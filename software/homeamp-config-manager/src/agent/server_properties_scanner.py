"""
Server Properties Scanner - Discovers server.properties configurations
"""
import mysql.connector
import os
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ServerPropertiesScanner:
    """Scans and tracks server.properties files across instances"""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
    
    def _get_db_connection(self):
        """Create database connection"""
        return mysql.connector.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database']
        )
    
    def scan_instance_properties(self, instance_path: str) -> Dict[str, Any]:
        """Read and parse server.properties file from instance"""
        properties_path = os.path.join(instance_path, 'server.properties')
        
        if not os.path.exists(properties_path):
            logger.warning(f"server.properties not found at {properties_path}")
            return {}
        
        properties = {}
        try:
            with open(properties_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        properties[key.strip()] = value.strip()
            
            logger.info(f"Parsed {len(properties)} properties from {properties_path}")
            return properties
        except Exception as e:
            logger.error(f"Error reading server.properties at {properties_path}: {e}")
            return {}
    
    def _get_baseline_properties(self) -> Dict[str, str]:
        """Fetch baseline server properties from database"""
        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT property_key, property_value
                FROM server_properties_baselines
                WHERE baseline_type = 'global'
            """)
            
            baselines = {}
            for row in cursor.fetchall():
                baselines[row['property_key']] = row['property_value']
            
            return baselines
        finally:
            cursor.close()
            conn.close()
    
    def detect_property_variances(self, instance_id: str, properties: Dict[str, str]) -> int:
        """Compare instance properties with baselines and register variances"""
        baselines = self._get_baseline_properties()
        
        if not baselines:
            logger.warning("No baseline properties defined, skipping variance detection")
            return 0
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        variances_count = 0
        
        try:
            for property_key, baseline_value in baselines.items():
                actual_value = properties.get(property_key)
                
                # Check if values differ
                if actual_value and actual_value != baseline_value:
                    # Check if variance already exists
                    cursor.execute("""
                        SELECT id FROM server_properties_variances
                        WHERE instance_id = %s AND property_key = %s
                    """, (instance_id, property_key))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # Update existing variance
                        cursor.execute("""
                            UPDATE server_properties_variances
                            SET variance_value = %s
                            WHERE id = %s
                        """, (actual_value, existing[0]))
                    else:
                        # Insert new variance
                        cursor.execute("""
                            INSERT INTO server_properties_variances
                            (instance_id, property_key, variance_value, is_intentional)
                            VALUES (%s, %s, %s, FALSE)
                        """, (instance_id, property_key, actual_value))
                    
                    variances_count += 1
                    logger.info(f"Property variance: {instance_id}/{property_key}: {actual_value} vs {baseline_value}")
            
            conn.commit()
            logger.info(f"Registered {variances_count} property variances for {instance_id}")
            return variances_count
        finally:
            cursor.close()
            conn.close()
    
    def create_baseline_from_instance(self, instance_id: str, instance_path: str):
        """Create global baselines from a reference instance (e.g., PRI01)"""
        properties = self.scan_instance_properties(instance_path)
        
        if not properties:
            logger.error(f"No properties found for instance {instance_id}, cannot create baseline")
            return
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            for property_key, property_value in properties.items():
                cursor.execute("""
                    INSERT INTO server_properties_baselines
                    (property_key, property_value, baseline_type)
                    VALUES (%s, %s, 'global')
                    ON DUPLICATE KEY UPDATE property_value = %s
                """, (property_key, property_value, property_value))
            
            conn.commit()
            logger.info(f"Created baseline from {instance_id} with {len(properties)} properties")
        finally:
            cursor.close()
            conn.close()
    
    def scan_all_instances(self, instances: List[Dict[str, str]]) -> int:
        """Scan all instances for server.properties variances"""
        total_variances = 0
        
        for instance in instances:
            instance_id = instance['instance_id']
            instance_path = instance['instance_path']
            
            logger.info(f"Scanning server.properties for {instance_id}...")
            properties = self.scan_instance_properties(instance_path)
            
            if properties:
                variances = self.detect_property_variances(instance_id, properties)
                total_variances += variances
        
        logger.info(f"Total server.properties variances: {total_variances}")
        return total_variances
