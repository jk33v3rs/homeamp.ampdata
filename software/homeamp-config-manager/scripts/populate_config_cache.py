#!/usr/bin/env python3
"""
Config Cache Populator

Scans live instance configs and populates config_variance_cache table.
Compares against rules to determine variance type.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import yaml
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_access import ConfigDatabase
from core.settings import settings
from amp_integration.instance_scanner import AMPInstanceScanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigCachePopulator:
    """Populates variance cache from live configs"""
    
    def __init__(self, db: ConfigDatabase, amp_base_dir: Path):
        self.db = db
        self.amp_base_dir = amp_base_dir
        self.scanner = AMPInstanceScanner(amp_base_dir)
    
    def populate_all_instances(self):
        """Scan all instances and populate cache"""
        
        # Discover instances
        instances = self.scanner.discover_instances()
        logger.info(f"Found {len(instances)} instances to scan")
        
        for instance in instances:
            try:
                self.populate_instance(instance)
            except Exception as e:
                logger.error(f"Failed to scan {instance['name']}: {e}", exc_info=True)
    
    def populate_instance(self, instance: dict):
        """Populate cache for a single instance"""
        instance_id = instance['name']
        logger.info(f"Scanning {instance_id}...")
        
        # Get instance details from database
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM instances WHERE instance_id = %s", (instance_id,))
        db_instance = cursor.fetchone()
        
        if not db_instance:
            logger.warning(f"Instance {instance_id} not in database, skipping")
            return
        
        server_name = db_instance['server_name']
        
        # Scan plugin configs
        plugins_dir = Path(instance['path']) / 'Minecraft' / 'plugins'
        if plugins_dir.exists():
            self._scan_plugin_configs(instance_id, server_name, plugins_dir)
        
        # Scan standard configs
        minecraft_dir = Path(instance['path']) / 'Minecraft'
        if minecraft_dir.exists():
            self._scan_standard_configs(instance_id, server_name, minecraft_dir)
        
        # Scan datapacks
        datapacks_dir = minecraft_dir / 'world' / 'datapacks'
        if datapacks_dir.exists():
            self._scan_datapacks(instance_id, server_name, datapacks_dir)
    
    def _scan_plugin_configs(self, instance_id: str, server_name: str, plugins_dir: Path):
        """Scan plugin configuration files"""
        
        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            plugin_name = plugin_dir.name
            
            # Scan YAML config files
            for config_file in list(plugin_dir.glob("*.yml")) + list(plugin_dir.glob("*.yaml")):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                    
                    if not config_data:
                        continue
                    
                    # Flatten config and store in cache
                    self._process_config_dict(
                        instance_id, server_name, 'plugin',
                        plugin_name, config_file.name, config_data
                    )
                
                except Exception as e:
                    logger.warning(f"Failed to read {config_file}: {e}")
    
    def _scan_standard_configs(self, instance_id: str, server_name: str, minecraft_dir: Path):
        """Scan standard Minecraft server configs"""
        
        standard_files = [
            'server.properties',
            'bukkit.yml',
            'spigot.yml',
            'paper-global.yml',
            'paper-world-defaults.yml',
            'pufferfish.yml',
            'purpur.yml'
        ]
        
        for filename in standard_files:
            config_file = minecraft_dir / filename
            if not config_file.exists():
                continue
            
            try:
                if filename.endswith('.properties'):
                    config_data = self._parse_properties_file(config_file)
                else:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                
                if config_data:
                    self._process_config_dict(
                        instance_id, server_name, 'standard',
                        None, filename, config_data
                    )
            
            except Exception as e:
                logger.warning(f"Failed to read {config_file}: {e}")
    
    def _scan_datapacks(self, instance_id: str, server_name: str, datapacks_dir: Path):
        """Scan installed datapacks"""
        
        for datapack in datapacks_dir.iterdir():
            if datapack.is_dir() or datapack.suffix == '.zip':
                datapack_name = datapack.stem
                
                # Record datapack presence
                self._store_cache_entry(
                    instance_id, server_name, 'datapack',
                    datapack_name, None, None, 'true', 'boolean'
                )
    
    def _parse_properties_file(self, file_path: Path) -> dict:
        """Parse Java .properties file"""
        config = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    
    def _process_config_dict(self, instance_id: str, server_name: str, config_type: str,
                            plugin_name: Optional[str], config_file: str, config_data: dict,
                            prefix: str = ""):
        """Process config dictionary recursively"""
        
        for key, value in config_data.items():
            full_key = f"{prefix}{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recurse into nested dicts
                self._process_config_dict(
                    instance_id, server_name, config_type,
                    plugin_name, config_file, value, f"{full_key}."
                )
            else:
                # Store leaf values
                value_str = str(value) if value is not None else None
                value_type = self._get_value_type(value)
                
                self._store_cache_entry(
                    instance_id, server_name, config_type,
                    plugin_name, config_file, full_key, value_str, value_type
                )
    
    def _get_value_type(self, value) -> str:
        """Determine value type"""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, list):
            return 'list'
        else:
            return 'string'
    
    def _store_cache_entry(self, instance_id: str, server_name: str, config_type: str,
                          plugin_name: Optional[str], config_file: Optional[str],
                          config_key: Optional[str], actual_value: Optional[str],
                          value_type: str):
        """Store config entry in variance cache"""
        
        # Resolve expected value from rules
        expected_value, variance_type = self._resolve_expected_value(
            instance_id, server_name, config_type, plugin_name, config_file, config_key
        )
        
        # Determine if drift (value differs from expected)
        is_drift = False
        if expected_value is not None and actual_value != expected_value:
            is_drift = True
            variance_type = 'DRIFT'
        
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO config_variance_cache
            (instance_id, server_name, config_type, plugin_name, config_file,
             config_key, actual_value, expected_value, variance_type, value_type,
             is_drift, last_scanned)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                actual_value = VALUES(actual_value),
                expected_value = VALUES(expected_value),
                variance_type = VALUES(variance_type),
                value_type = VALUES(value_type),
                is_drift = VALUES(is_drift),
                last_scanned = VALUES(last_scanned)
        """, (
            instance_id, server_name, config_type, plugin_name, config_file,
            config_key, actual_value, expected_value, variance_type, value_type,
            is_drift, datetime.now()
        ))
        
        self.db.conn.commit()
        
        # Log drift if detected
        if is_drift:
            self._log_drift(
                instance_id, server_name, config_type, plugin_name,
                config_file, config_key, expected_value, actual_value
            )
    
    def _resolve_expected_value(self, instance_id: str, server_name: str, config_type: str,
                               plugin_name: Optional[str], config_file: Optional[str],
                               config_key: Optional[str]) -> Tuple[Optional[str], str]:
        """
        Resolve expected value using rule hierarchy
        
        Returns: (expected_value, variance_type)
        """
        cursor = self.db.conn.cursor(dictionary=True)
        
        # Query rules in priority order
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
        
        # Also get instance-specific values from instances table
        cursor.execute("""
            SELECT instance_id, server_name, instance_type
            FROM instances
            WHERE instance_id = %s
        """, (instance_id,))
        
        inst = cursor.fetchone()
        if inst:
            variables['INSTANCE_ID'] = inst['instance_id']
            variables['SERVER_NAME'] = inst['server_name']
            variables['SHORTNAME'] = inst['instance_id']  # e.g., BENT01
        
        # Substitute
        result = value
        for var_name, var_value in variables.items():
            result = result.replace(f"{{{{{var_name}}}}}", str(var_value))
        
        return result
    
    def _log_drift(self, instance_id: str, server_name: str, config_type: str,
                   plugin_name: Optional[str], config_file: Optional[str],
                   config_key: Optional[str], expected_value: str, actual_value: str):
        """Log detected drift"""
        
        cursor = self.db.conn.cursor()
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
            f"DRIFT: {instance_id}/{config_type}/{plugin_name or 'standard'}/{config_file}:"
            f"{config_key} = {actual_value} (expected {expected_value})"
        )


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate config variance cache')
    parser.add_argument('--amp-dir', default='/home/amp/.ampdata/instances',
                       help='AMP instances directory')
    
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
        populator = ConfigCachePopulator(db, Path(args.amp_dir))
        populator.populate_all_instances()
        logger.info("Config cache population complete")
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
