"""
Performance Metrics Collection for ArchiveSMP Config Manager

Tracks:
- API response times
- Database query performance
- Agent scan durations
- Deployment times
- Resource usage
"""

import mariadb
import time
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
import logging
import os

# Optional dependency - gracefully degrade if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logging.warning("psutil not available - system metrics will be limited")

logger = logging.getLogger("performance_metrics")


class PerformanceMetrics:
    """Collects and stores performance metrics"""
    
    def __init__(self, db_connection):
        """
        Initialize performance metrics collector
        
        Args:
            db_connection: MariaDB connection
        """
        self.db = db_connection
        self.cursor = db_connection.cursor(dictionary=True)
        if HAS_PSUTIL:
            self.process = psutil.Process(os.getpid())
        else:
            self.process = None
    
    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str = 'ms',
        component: Optional[str] = None,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a performance metric
        
        Args:
            metric_name: Name of metric (e.g., 'api_response_time')
            metric_value: Numeric value
            metric_unit: Unit of measurement (ms, seconds, bytes, count, percent)
            component: System component (api, agent, database, etc.)
            operation: Specific operation (query, scan, deploy, etc.)
            metadata: Additional structured data
        """
        import json
        
        query = """
            INSERT INTO system_health_metrics (
                metric_name,
                metric_value,
                metric_unit,
                component,
                operation,
                metadata,
                recorded_at
            ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        self.cursor.execute(query, (
            metric_name,
            metric_value,
            metric_unit,
            component,
            operation,
            metadata_json
        ))
        
        self.db.commit()
    
    @contextmanager
    def measure_time(
        self,
        metric_name: str,
        component: str,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager to measure execution time
        
        Usage:
            with metrics.measure_time('api_request', 'api', 'get_instances'):
                # ... code to measure
                pass
        
        Args:
            metric_name: Name of metric
            component: System component
            operation: Operation being measured
            metadata: Additional data to store
        """
        start_time = time.time()
        
        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_metric(
                metric_name=metric_name,
                metric_value=duration_ms,
                metric_unit='ms',
                component=component,
                operation=operation,
                metadata=metadata
            )
    
    def collect_system_metrics(self):
        """Collect current system resource usage metrics"""
        
        # CPU usage
        cpu_percent = self.process.cpu_percent(interval=1)
        self.record_metric(
            metric_name='cpu_usage',
            metric_value=cpu_percent,
            metric_unit='percent',
            component='system',
            operation='resource_monitor'
        )
        
        # Memory usage
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        self.record_metric(
            metric_name='memory_usage',
            metric_value=memory_mb,
            metric_unit='MB',
            component='system',
            operation='resource_monitor'
        )
        
        # Database connection pool
        self.cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        result = self.cursor.fetchone()
        if result:
            connections = int(result['Value'])
            self.record_metric(
                metric_name='db_connections',
                metric_value=connections,
                metric_unit='count',
                component='database',
                operation='connection_pool'
            )
        
        logger.debug(f"System metrics: CPU={cpu_percent}%, Memory={memory_mb:.2f}MB")
    
    def collect_database_metrics(self):
        """Collect database performance metrics"""
        
        # Query count
        self.cursor.execute("SHOW STATUS LIKE 'Queries'")
        result = self.cursor.fetchone()
        if result:
            queries = int(result['Value'])
            self.record_metric(
                metric_name='db_query_count',
                metric_value=queries,
                metric_unit='count',
                component='database',
                operation='query_stats'
            )
        
        # Slow queries
        self.cursor.execute("SHOW STATUS LIKE 'Slow_queries'")
        result = self.cursor.fetchone()
        if result:
            slow_queries = int(result['Value'])
            self.record_metric(
                metric_name='db_slow_queries',
                metric_value=slow_queries,
                metric_unit='count',
                component='database',
                operation='query_stats'
            )
        
        # Table sizes
        self.cursor.execute("""
            SELECT 
                table_name,
                ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
            FROM information_schema.TABLES
            WHERE table_schema = DATABASE()
            ORDER BY (data_length + index_length) DESC
            LIMIT 10
        """)
        
        tables = self.cursor.fetchall()
        for table in tables:
            self.record_metric(
                metric_name='table_size',
                metric_value=table['size_mb'],
                metric_unit='MB',
                component='database',
                operation='storage',
                metadata={'table_name': table['table_name']}
            )
    
    def collect_api_metrics(self):
        """Collect API performance metrics from recent history"""
        
        # Average API response times by endpoint (last hour)
        query = """
            SELECT 
                operation,
                AVG(metric_value) as avg_ms,
                MIN(metric_value) as min_ms,
                MAX(metric_value) as max_ms,
                COUNT(*) as request_count
            FROM system_health_metrics
            WHERE 
                component = 'api' 
                AND recorded_at > DATE_SUB(NOW(), INTERVAL 1 HOUR)
            GROUP BY operation
        """
        
        self.cursor.execute(query)
        endpoint_stats = self.cursor.fetchall()
        
        for stats in endpoint_stats:
            logger.info(
                f"API {stats['operation']}: "
                f"avg={stats['avg_ms']:.2f}ms, "
                f"min={stats['min_ms']:.2f}ms, "
                f"max={stats['max_ms']:.2f}ms, "
                f"count={stats['request_count']}"
            )
    
    def collect_agent_metrics(self):
        """Collect agent performance metrics"""
        
        # Instance count
        self.cursor.execute("SELECT COUNT(*) as count FROM instances WHERE is_active = 1")
        result = self.cursor.fetchone()
        if result:
            self.record_metric(
                metric_name='active_instances',
                metric_value=result['count'],
                metric_unit='count',
                component='agent',
                operation='discovery'
            )
        
        # Plugin count
        self.cursor.execute("SELECT COUNT(DISTINCT plugin_name) as count FROM installed_plugins")
        result = self.cursor.fetchone()
        if result:
            self.record_metric(
                metric_name='unique_plugins',
                metric_value=result['count'],
                metric_unit='count',
                component='agent',
                operation='plugin_registry'
            )
        
        # Pending deployments
        self.cursor.execute("SELECT COUNT(*) as count FROM deployment_queue WHERE status = 'pending'")
        result = self.cursor.fetchone()
        if result:
            self.record_metric(
                metric_name='pending_deployments',
                metric_value=result['count'],
                metric_unit='count',
                component='agent',
                operation='deployment_queue'
            )
        
        # Recent deployment success rate (last 24 hours)
        query = """
            SELECT 
                COUNT(CASE WHEN deployment_status = 'success' THEN 1 END) as success_count,
                COUNT(CASE WHEN deployment_status = 'failed' THEN 1 END) as failed_count,
                COUNT(*) as total_count
            FROM deployment_history
            WHERE deployed_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
        """
        
        self.cursor.execute(query)
        result = self.cursor.fetchone()
        if result and result['total_count'] > 0:
            success_rate = (result['success_count'] / result['total_count']) * 100
            self.record_metric(
                metric_name='deployment_success_rate',
                metric_value=success_rate,
                metric_unit='percent',
                component='agent',
                operation='deployment',
                metadata={
                    'success_count': result['success_count'],
                    'failed_count': result['failed_count'],
                    'total_count': result['total_count']
                }
            )
    
    def get_metric_summary(
        self,
        metric_name: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Get statistical summary of a metric over time
        
        Args:
            metric_name: Name of metric to summarize
            hours: Number of hours to look back
        
        Returns:
            Dict with avg, min, max, count
        """
        query = """
            SELECT 
                AVG(metric_value) as avg_value,
                MIN(metric_value) as min_value,
                MAX(metric_value) as max_value,
                COUNT(*) as sample_count,
                MAX(recorded_at) as last_recorded
            FROM system_health_metrics
            WHERE 
                metric_name = %s
                AND recorded_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        
        self.cursor.execute(query, (metric_name, hours))
        result = self.cursor.fetchone()
        
        return result if result else {}
    
    def get_slow_operations(
        self,
        component: Optional[str] = None,
        threshold_ms: float = 1000,
        limit: int = 10
    ) -> list:
        """
        Get slowest operations
        
        Args:
            component: Filter by component (api, agent, database)
            threshold_ms: Minimum duration in milliseconds
            limit: Max results to return
        
        Returns:
            List of slow operations
        """
        query = """
            SELECT 
                component,
                operation,
                metric_value as duration_ms,
                recorded_at,
                metadata
            FROM system_health_metrics
            WHERE 
                metric_unit = 'ms'
                AND metric_value >= %s
        """
        
        params = [threshold_ms]
        
        if component:
            query += " AND component = %s"
            params.append(component)  # type: ignore
        
        query += " ORDER BY metric_value DESC LIMIT %s"
        params.append(limit)
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def collect_all_metrics(self):
        """Collect all available metrics"""
        logger.info("Collecting comprehensive metrics...")
        
        try:
            self.collect_system_metrics()
            self.collect_database_metrics()
            self.collect_agent_metrics()
            self.collect_api_metrics()
            logger.info("Metrics collection complete")
        
        except Exception as e:
            logger.error(f"Metrics collection failed: {e}")


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_metrics_collector(db_connection) -> PerformanceMetrics:
    """
    Factory function to create metrics collector
    
    Args:
        db_connection: MariaDB connection
    
    Returns:
        PerformanceMetrics instance
    """
    return PerformanceMetrics(db_connection)
