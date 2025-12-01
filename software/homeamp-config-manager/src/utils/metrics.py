"""
Prometheus Metrics Exporter

Exports metrics for monitoring via Prometheus/Grafana
"""

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry
from typing import Dict
from datetime import datetime


class MetricsExporter:
    """Prometheus metrics exporter for HomeAMP agents"""
    
    def __init__(self):
        """Initialize metrics"""
        self.registry = CollectorRegistry()
        
        # Agent health metrics
        self.agent_up = Gauge(
            'homeamp_agent_up',
            'Agent is running (1) or down (0)',
            ['server'],
            registry=self.registry
        )
        
        self.last_poll_timestamp = Gauge(
            'homeamp_agent_last_poll_timestamp',
            'Unix timestamp of last MinIO poll',
            ['server'],
            registry=self.registry
        )
        
        # Configuration drift metrics
        self.drift_detected_count = Gauge(
            'homeamp_drift_detected_total',
            'Number of configuration drifts detected',
            ['server', 'plugin'],
            registry=self.registry
        )
        
        self.last_drift_check_timestamp = Gauge(
            'homeamp_last_drift_check_timestamp',
            'Unix timestamp of last drift check',
            ['server'],
            registry=self.registry
        )
        
        # Change application metrics
        self.changes_applied_total = Counter(
            'homeamp_changes_applied_total',
            'Total number of configuration changes applied',
            ['server', 'status'],
            registry=self.registry
        )
        
        self.change_application_duration = Histogram(
            'homeamp_change_application_duration_seconds',
            'Time taken to apply configuration changes',
            ['server'],
            registry=self.registry
        )
        
        # Plugin version metrics
        self.plugin_version = Gauge(
            'homeamp_plugin_version_info',
            'Plugin version information',
            ['server', 'plugin', 'version'],
            registry=self.registry
        )
        
        self.plugins_outdated_count = Gauge(
            'homeamp_plugins_outdated_total',
            'Number of plugins with available updates',
            ['server'],
            registry=self.registry
        )
        
        # Deviation metrics
        self.deviations_pending = Gauge(
            'homeamp_deviations_pending',
            'Number of deviations pending review',
            ['server'],
            registry=self.registry
        )
        
        self.deviations_flagged_bad = Gauge(
            'homeamp_deviations_flagged_bad',
            'Number of deviations flagged as bad',
            ['server'],
            registry=self.registry
        )
    
    def update_agent_health(self, server: str, is_up: bool):
        """Update agent health status"""
        self.agent_up.labels(server=server).set(1 if is_up else 0)
        self.last_poll_timestamp.labels(server=server).set(datetime.now().timestamp())
    
    def update_drift_count(self, server: str, plugin: str, count: int):
        """Update drift detection count"""
        self.drift_detected_count.labels(server=server, plugin=plugin).set(count)
    
    def record_drift_check(self, server: str):
        """Record drift check timestamp"""
        self.last_drift_check_timestamp.labels(server=server).set(datetime.now().timestamp())
    
    def record_change_applied(self, server: str, success: bool, duration: float):
        """Record a configuration change application"""
        status = "success" if success else "failure"
        self.changes_applied_total.labels(server=server, status=status).inc()
        self.change_application_duration.labels(server=server).observe(duration)
    
    def update_plugin_version(self, server: str, plugin: str, version: str):
        """Update plugin version info"""
        self.plugin_version.labels(server=server, plugin=plugin, version=version).set(1)
    
    def update_outdated_plugins(self, server: str, count: int):
        """Update count of outdated plugins"""
        self.plugins_outdated_count.labels(server=server).set(count)
    
    def update_deviations(self, server: str, pending: int, flagged_bad: int):
        """Update deviation counts"""
        self.deviations_pending.labels(server=server).set(pending)
        self.deviations_flagged_bad.labels(server=server).set(flagged_bad)
    
    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest(self.registry)


# Global metrics instance
metrics = MetricsExporter()
