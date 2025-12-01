"""
Database Access Layer for Configuration Management

Provides data access methods for the asmp_config MariaDB database.
"""

import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfigDatabase:
    """Database connection and query interface"""
    
    def __init__(self, host: str, port: int, user: str, password: str, database: str = 'asmp_config'):
        """
        Initialize database connection
        
        Args:
            host: Database host (e.g., '135.181.212.169')
            port: Database port (e.g., 3369)
            user: Database user
            password: Database password
            database: Database name
        """
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'autocommit': False
        }
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = mysql.connector.connect(**self.config)
            self.cursor = self.conn.cursor(dictionary=True)
            logger.info(f"Connected to database {self.config['database']} at {self.config['host']}")
        except Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def commit(self):
        """Commit transaction"""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """Rollback transaction"""
        if self.conn:
            self.conn.rollback()
    
    # ========================================================================
    # INSTANCE QUERIES
    # ========================================================================
    
    def get_all_instances(self) -> List[Dict[str, Any]]:
        """Get all instances"""
        self.cursor.execute("""
            SELECT instance_id, instance_name, server_name, server_host, port,
                   platform, minecraft_version, is_active, is_production, description
            FROM instances
            WHERE is_active = true
            ORDER BY server_name, instance_id
        """)
        return self.cursor.fetchall()
    
    def get_instances_by_server(self, server_name: str) -> List[Dict[str, Any]]:
        """Get instances for a specific physical server"""
        self.cursor.execute("""
            SELECT instance_id, instance_name, server_host, port,
                   platform, minecraft_version, is_production
            FROM instances
            WHERE server_name = %s AND is_active = true
            ORDER BY instance_id
        """, (server_name,))
        return self.cursor.fetchall()
    
    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get single instance by ID"""
        self.cursor.execute("""
            SELECT * FROM instances WHERE instance_id = %s
        """, (instance_id,))
        return self.cursor.fetchone()
    
    # ========================================================================
    # INSTANCE GROUP QUERIES
    # ========================================================================
    
    def get_instance_groups_for_instance(self, instance_id: str) -> List[str]:
        """Get all group names an instance belongs to"""
        self.cursor.execute("""
            SELECT ig.group_name
            FROM instance_groups ig
            JOIN instance_group_members igm ON ig.group_id = igm.group_id
            WHERE igm.instance_id = %s
        """, (instance_id,))
        return [row['group_name'] for row in self.cursor.fetchall()]
    
    def get_instances_in_group(self, group_name: str) -> List[str]:
        """Get all instance IDs in a group"""
        self.cursor.execute("""
            SELECT igm.instance_id
            FROM instance_group_members igm
            JOIN instance_groups ig ON igm.group_id = ig.group_id
            WHERE ig.group_name = %s
        """, (group_name,))
        return [row['instance_id'] for row in self.cursor.fetchall()]
    
    # ========================================================================
    # CONFIG RULE QUERIES (Hierarchy Resolution)
    # ========================================================================
    
    def resolve_config_value(self, instance_id: str, plugin_name: str, 
                            config_file: str, config_key: str) -> Tuple[Any, int, str]:
        """
        Resolve config value for an instance using priority hierarchy
        
        Args:
            instance_id: Target instance
            plugin_name: Plugin name
            config_file: Config filename
            config_key: Config key path
        
        Returns:
            Tuple of (config_value, priority, scope_description)
        """
        # Get instance details and groups
        instance = self.get_instance(instance_id)
        if not instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        server_name = instance['server_name']
        groups = self.get_instance_groups_for_instance(instance_id)
        
        # Query all applicable rules in priority order (0=highest)
        self.cursor.execute("""
            SELECT config_value, priority, scope_type, scope_selector
            FROM config_rules
            WHERE plugin_name = %s
              AND config_file = %s
              AND config_key = %s
              AND is_active = true
              AND (
                  (scope_type = 'GLOBAL')
                  OR (scope_type = 'SERVER' AND scope_selector = %s)
                  OR (scope_type = 'INSTANCE_GROUP' AND scope_selector IN (%s))
                  OR (scope_type = 'INSTANCE' AND scope_selector = %s)
              )
            ORDER BY priority ASC
            LIMIT 1
        """, (plugin_name, config_file, config_key, server_name, 
              ','.join(groups) if groups else '', instance_id))
        
        result = self.cursor.fetchone()
        if result:
            scope_desc = f"{result['scope_type']}:{result['scope_selector']}"
            return (result['config_value'], result['priority'], scope_desc)
        
        return (None, None, 'NOT_CONFIGURED')
    
    def get_all_config_rules(self, plugin_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all config rules, optionally filtered by plugin"""
        if plugin_name:
            self.cursor.execute("""
                SELECT * FROM config_rules
                WHERE plugin_name = %s AND is_active = true
                ORDER BY priority, plugin_name, config_file, config_key
            """, (plugin_name,))
        else:
            self.cursor.execute("""
                SELECT * FROM config_rules
                WHERE is_active = true
                ORDER BY priority, plugin_name, config_file, config_key
            """)
        return self.cursor.fetchall()
    
    # ========================================================================
    # CONFIG VARIABLE QUERIES
    # ========================================================================
    
    def get_variable_value(self, variable_name: str, scope_type: str, 
                          scope_identifier: str) -> Optional[str]:
        """Get variable value for a specific scope"""
        self.cursor.execute("""
            SELECT variable_value
            FROM config_variables
            WHERE variable_name = %s
              AND scope_type = %s
              AND scope_identifier = %s
        """, (variable_name, scope_type, scope_identifier))
        
        result = self.cursor.fetchone()
        return result['variable_value'] if result else None
    
    def substitute_variables(self, config_value: str, instance_id: str) -> str:
        """
        Substitute {{VARIABLE_NAME}} placeholders in config value
        
        Checks scopes in order: INSTANCE → SERVER → GLOBAL
        """
        if not isinstance(config_value, str) or '{{' not in config_value:
            return config_value
        
        instance = self.get_instance(instance_id)
        server_name = instance['server_name']
        
        # Extract variables from config value
        import re
        variables = re.findall(r'\{\{([A-Z_]+)\}\}', config_value)
        
        result = config_value
        for var_name in variables:
            # Try instance scope first
            value = self.get_variable_value(var_name, 'INSTANCE', instance_id)
            
            # Fall back to server scope
            if value is None:
                value = self.get_variable_value(var_name, 'SERVER', server_name)
            
            # Fall back to global scope
            if value is None:
                value = self.get_variable_value(var_name, 'GLOBAL', 'default')
            
            if value is not None:
                result = result.replace(f'{{{{{var_name}}}}}', value)
        
        return result
    
    # ========================================================================
    # VARIANCE CACHE QUERIES
    # ========================================================================
    
    def get_variance_report(self, classification: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get variance report from cache
        
        Args:
            classification: Filter by variance_classification (NONE, VARIABLE, META_TAG, INSTANCE, DRIFT)
        """
        if classification:
            self.cursor.execute("""
                SELECT * FROM config_variance_cache
                WHERE variance_classification = %s
                ORDER BY plugin_name, config_key
            """, (classification,))
        else:
            self.cursor.execute("""
                SELECT * FROM config_variance_cache
                ORDER BY variance_classification, plugin_name, config_key
            """)
        return self.cursor.fetchall()
    
    # ========================================================================
    # META TAG QUERIES
    # ========================================================================
    
    def get_instance_tags(self, instance_id: str) -> List[str]:
        """Get all meta tag names for an instance"""
        self.cursor.execute("""
            SELECT mt.tag_name
            FROM meta_tags mt
            JOIN instance_tags it ON mt.tag_id = it.tag_id
            WHERE it.instance_id = %s
        """, (instance_id,))
        return [row['tag_name'] for row in self.cursor.fetchall()]
    
    def get_instances_with_tag(self, tag_name: str) -> List[str]:
        """Get all instance IDs with a specific tag"""
        self.cursor.execute("""
            SELECT it.instance_id
            FROM instance_tags it
            JOIN meta_tags mt ON it.tag_id = mt.tag_id
            WHERE mt.tag_name = %s
        """, (tag_name,))
        return [row['instance_id'] for row in self.cursor.fetchall()]
