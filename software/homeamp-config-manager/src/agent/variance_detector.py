"""
Config Variance Detector - Identifies differences between instance configs and baselines
"""
import mysql.connector
import yaml
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfigVariance:
    """Represents a configuration variance between baseline and instance"""
    instance_id: str
    plugin_name: str
    file_path: str
    config_key: str
    baseline_value: Any
    actual_value: Any
    is_intentional: bool = False


class VarianceDetector:
    """Detects configuration variances across instances"""
    
    def __init__(self, db_config: Dict[str, str] = None):
        self.db_config = db_config or get_db_config()
    
    def _get_db_connection(self):
        """Create database connection"""
        return get_db_connection()
    
    def _get_baseline_config(self, plugin_name: str) -> Dict[str, Any]:
        """Fetch baseline configuration for a plugin from database"""
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT file_path, config_key, config_value
                FROM config_baselines
                WHERE plugin_name = %s
            """, (plugin_name,))
            
            baseline = {}
            for row in cursor.fetchall():
                file_path = row['file_path']
                if file_path not in baseline:
                    baseline[file_path] = {}
                baseline[file_path][row['config_key']] = row['config_value']
            
            return baseline
        finally:
            cursor.close()
            conn.close()
    
    def _read_instance_config(self, instance_path: str, plugin_name: str, file_path: str) -> Dict[str, Any]:
        """Read configuration file from instance directory"""
        full_path = os.path.join(instance_path, 'plugins', plugin_name, file_path)
        
        if not os.path.exists(full_path):
            logger.warning(f"Config file not found: {full_path}")
            return {}
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.yml') or file_path.endswith('.yaml'):
                    return yaml.safe_load(f) or {}
                else:
                    # Handle other config formats as needed
                    return {}
        except Exception as e:
            logger.error(f"Error reading config file {full_path}: {e}")
            return {}
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary into dot-notation keys"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def scan_instance_configs(self, instance_id: str, instance_path: str, plugin_list: List[str]) -> List[ConfigVariance]:
        """Scan instance configs and compare with baselines"""
        variances = []
        
        for plugin_name in plugin_list:
            baseline = self._get_baseline_config(plugin_name)
            
            for file_path, baseline_keys in baseline.items():
                # Read actual config from instance
                instance_config = self._read_instance_config(instance_path, plugin_name, file_path)
                flattened_instance = self._flatten_dict(instance_config)
                
                # Compare each baseline key
                for config_key, baseline_value in baseline_keys.items():
                    actual_value = flattened_instance.get(config_key)
                    
                    # Check if values differ
                    if actual_value != baseline_value:
                        variance = ConfigVariance(
                            instance_id=instance_id,
                            plugin_name=plugin_name,
                            file_path=file_path,
                            config_key=config_key,
                            baseline_value=baseline_value,
                            actual_value=actual_value
                        )
                        variances.append(variance)
                        logger.info(f"Variance detected: {instance_id}/{plugin_name}/{config_key}: {actual_value} vs {baseline_value}")
        
        return variances
    
    def register_variance(self, instance_id: str, plugin_name: str, config_key: str, 
                         baseline_value: Any, actual_value: Any) -> int:
        """Register a variance in the database"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if variance already exists
            cursor.execute("""
                SELECT id FROM config_variances
                WHERE instance_id = %s AND plugin_name = %s AND config_key = %s
            """, (instance_id, plugin_name, config_key))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing variance
                cursor.execute("""
                    UPDATE config_variances
                    SET variance_value = %s, baseline_value = %s
                    WHERE id = %s
                """, (str(actual_value), str(baseline_value), existing[0]))
                variance_id = existing[0]
            else:
                # Insert new variance
                cursor.execute("""
                    INSERT INTO config_variances 
                    (instance_id, plugin_name, config_key, variance_value, baseline_value, is_intentional)
                    VALUES (%s, %s, %s, %s, %s, FALSE)
                """, (instance_id, plugin_name, config_key, str(actual_value), str(baseline_value)))
                variance_id = cursor.lastrowid
            
            conn.commit()
            logger.info(f"Registered variance ID {variance_id} for {instance_id}/{plugin_name}/{config_key}")
            return variance_id
        finally:
            cursor.close()
            conn.close()
    
    def scan_and_register_all(self, instances: List[Dict[str, str]], plugin_list: List[str]) -> int:
        """Scan all instances and register variances"""
        total_variances = 0
        
        for instance in instances:
            instance_id = instance['instance_id']
            instance_path = instance['instance_path']
            
            logger.info(f"Scanning instance {instance_id} for variances...")
            variances = self.scan_instance_configs(instance_id, instance_path, plugin_list)
            
            for variance in variances:
                self.register_variance(
                    variance.instance_id,
                    variance.plugin_name,
                    variance.config_key,
                    variance.baseline_value,
                    variance.actual_value
                )
                total_variances += 1
        
        logger.info(f"Total variances registered: {total_variances}")
        return total_variances
