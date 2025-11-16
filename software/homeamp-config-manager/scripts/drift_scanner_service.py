#!/usr/bin/env python3
"""
Periodic Drift Scanner Service

Runs as a systemd service to periodically scan for config drift.
Populates variance cache and logs drift events.
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import logging
import signal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_access import ConfigDatabase
from core.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DriftScanner:
    """Periodic drift scanner service"""
    
    def __init__(self, db: ConfigDatabase, scan_interval: int = 300):
        """
        Initialize drift scanner
        
        Args:
            db: Database connection
            scan_interval: Scan interval in seconds (default 5 minutes)
        """
        self.db = db
        self.scan_interval = scan_interval
        self.running = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def start(self):
        """Start scanner service"""
        logger.info(f"Starting drift scanner (interval: {self.scan_interval}s)")
        self.running = True
        
        while self.running:
            try:
                self._run_scan_cycle()
                
                # Sleep until next scan
                if self.running:
                    logger.info(f"Next scan in {self.scan_interval}s")
                    time.sleep(self.scan_interval)
            
            except Exception as e:
                logger.error(f"Error in scan cycle: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retry
        
        logger.info("Drift scanner stopped")
    
    def _run_scan_cycle(self):
        """Execute one scan cycle"""
        logger.info("=== Starting drift scan cycle ===")
        start_time = datetime.now()
        
        # Get all active instances
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("SELECT instance_id, server_name FROM instances WHERE is_active = TRUE")
        instances = cursor.fetchall()
        
        logger.info(f"Scanning {len(instances)} instances")
        
        drift_count = 0
        
        for instance in instances:
            try:
                drifts = self._scan_instance_drift(instance['instance_id'], instance['server_name'])
                drift_count += drifts
            except Exception as e:
                logger.error(f"Failed to scan {instance['instance_id']}: {e}")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Scan complete: {drift_count} drift events detected in {elapsed:.2f}s")
    
    def _scan_instance_drift(self, instance_id: str, server_name: str) -> int:
        """
        Scan for drift in a single instance
        
        Returns:
            Number of drift events detected
        """
        cursor = self.db.conn.cursor(dictionary=True)
        
        # Get all cached configs for this instance
        cursor.execute("""
            SELECT cache_id, config_type, plugin_name, config_file, config_key,
                   actual_value, expected_value, variance_type, is_drift
            FROM config_variance_cache
            WHERE instance_id = %s
        """, (instance_id,))
        
        cached_configs = cursor.fetchall()
        drift_count = 0
        
        for config in cached_configs:
            # Re-resolve expected value (rules may have changed)
            expected_value, variance_type = self._resolve_expected_value(
                instance_id, server_name,
                config['config_type'],
                config['plugin_name'],
                config['config_file'],
                config['config_key']
            )
            
            # Check if value drifted from expected
            actual_value = config['actual_value']
            is_drift = False
            
            if expected_value is not None and actual_value != expected_value:
                is_drift = True
                variance_type = 'DRIFT'
                
                # Check if this is a new drift (wasn't drift before)
                if not config['is_drift']:
                    drift_count += 1
                    self._log_new_drift(
                        instance_id, server_name,
                        config['config_type'],
                        config['plugin_name'],
                        config['config_file'],
                        config['config_key'],
                        expected_value, actual_value
                    )
            
            # Update cache
            cursor.execute("""
                UPDATE config_variance_cache
                SET expected_value = %s,
                    variance_type = %s,
                    is_drift = %s,
                    last_scanned = %s
                WHERE cache_id = %s
            """, (expected_value, variance_type, is_drift, datetime.now(), config['cache_id']))
        
        self.db.conn.commit()
        
        if drift_count > 0:
            logger.warning(f"{instance_id}: {drift_count} new drift events detected")
        
        return drift_count
    
    def _resolve_expected_value(self, instance_id: str, server_name: str, config_type: str,
                               plugin_name: str, config_file: str, config_key: str):
        """
        Resolve expected value using rule hierarchy
        
        Returns: (expected_value, variance_type)
        """
        cursor = self.db.conn.cursor(dictionary=True)
        
        # Query rules in priority order (INSTANCE > META_TAG > SERVER > GLOBAL)
        cursor.execute("""
            SELECT expected_value, scope, priority, is_variable
            FROM config_rules
            WHERE config_type = %s
              AND (plugin_name = %s OR plugin_name IS NULL)
              AND (config_file = %s OR config_file IS NULL)
              AND (config_key = %s OR config_key IS NULL)
              AND (
                  scope = 'GLOBAL'
                  OR (scope = 'SERVER' AND server_name = %s)
                  OR (scope = 'INSTANCE' AND instance_id = %s)
                  OR (scope = 'META_TAG' AND meta_tag_id IN (
                      SELECT meta_tag_id FROM instance_tags WHERE instance_id = %s
                  ))
              )
            ORDER BY priority ASC
            LIMIT 1
        """, (config_type, plugin_name, config_file, config_key,
              server_name, instance_id, instance_id))
        
        rule = cursor.fetchone()
        
        if not rule:
            return None, 'NONE'
        
        expected_value = rule['expected_value']
        
        # Substitute variables if needed
        if rule['is_variable']:
            expected_value = self._substitute_variables(instance_id, expected_value)
        
        # Determine variance type from scope
        variance_map = {
            'INSTANCE': 'INSTANCE',
            'META_TAG': 'META_TAG',
            'SERVER': 'GLOBAL',
            'GLOBAL': 'GLOBAL'
        }
        
        variance_type = variance_map.get(rule['scope'], 'NONE')
        if rule['is_variable']:
            variance_type = 'VARIABLE'
        
        return expected_value, variance_type
    
    def _substitute_variables(self, instance_id: str, value: str) -> str:
        """Substitute {{VARIABLE}} placeholders"""
        
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT variable_name, variable_value
            FROM config_variables
            WHERE instance_id = %s
        """, (instance_id,))
        
        variables = {row['variable_name']: row['variable_value'] for row in cursor.fetchall()}
        
        # Also get instance-specific values
        cursor.execute("""
            SELECT instance_id, server_name
            FROM instances
            WHERE instance_id = %s
        """, (instance_id,))
        
        inst = cursor.fetchone()
        if inst:
            variables['INSTANCE_ID'] = inst['instance_id']
            variables['SERVER_NAME'] = inst['server_name']
            variables['SHORTNAME'] = inst['instance_id']
        
        # Substitute
        result = value
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        return result
    
    def _log_new_drift(self, instance_id: str, server_name: str, config_type: str,
                      plugin_name: str, config_file: str, config_key: str,
                      expected_value: str, actual_value: str):
        """Log newly detected drift"""
        
        cursor = self.db.conn.cursor()
        
        # Check if drift already logged recently (last 24 hours)
        cursor.execute("""
            SELECT drift_id FROM config_drift_log
            WHERE instance_id = %s
              AND config_type = %s
              AND plugin_name <=> %s
              AND config_file <=> %s
              AND config_key <=> %s
              AND detected_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY detected_at DESC
            LIMIT 1
        """, (instance_id, config_type, plugin_name, config_file, config_key))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing drift log
            cursor.execute("""
                UPDATE config_drift_log
                SET actual_value = %s,
                    expected_value = %s,
                    detected_at = %s
                WHERE drift_id = %s
            """, (actual_value, expected_value, datetime.now(), existing[0]))
        else:
            # Insert new drift log
            cursor.execute("""
                INSERT INTO config_drift_log
                (instance_id, server_name, config_type, plugin_name, config_file,
                 config_key, expected_value, actual_value, severity, detected_at, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                instance_id, server_name, config_type, plugin_name, config_file,
                config_key, expected_value, actual_value, 'MEDIUM', datetime.now(), 'PENDING'
            ))
        
        self.db.conn.commit()
        
        logger.warning(
            f"NEW DRIFT: {instance_id}/{config_type}/{plugin_name or 'standard'}/"
            f"{config_file}:{config_key} = {actual_value} (expected {expected_value})"
        )


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Drift scanner service')
    parser.add_argument('--interval', type=int, default=300,
                       help='Scan interval in seconds (default: 300)')
    
    args = parser.parse_args()
    
    # Connect to database
    db = ConfigDatabase(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    db.connect()
    
    try:
        scanner = DriftScanner(db, scan_interval=args.interval)
        scanner.start()
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
