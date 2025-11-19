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
    
    def upsert_instance(self, instance_id: str, server_name: str, 
                       instance_name: Optional[str] = None, server_host: Optional[str] = None,
                       port: Optional[int] = None, amp_instance_id: Optional[str] = None,
                       platform: str = 'paper', minecraft_version: Optional[str] = None):
        """
        Register or update a discovered instance
        Uses ON DUPLICATE KEY UPDATE to handle existing instances
        """
        try:
            self.cursor.execute("""
                INSERT INTO instances 
                (instance_id, instance_name, server_name, server_host, port, 
                 amp_instance_id, platform, minecraft_version, last_seen)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    instance_name = COALESCE(VALUES(instance_name), instance_name),
                    server_host = COALESCE(VALUES(server_host), server_host),
                    port = COALESCE(VALUES(port), port),
                    amp_instance_id = COALESCE(VALUES(amp_instance_id), amp_instance_id),
                    platform = COALESCE(VALUES(platform), platform),
                    minecraft_version = COALESCE(VALUES(minecraft_version), minecraft_version),
                    last_seen = NOW()
            """, (instance_id, instance_name or instance_id, server_name, 
                  server_host, port, amp_instance_id, platform, minecraft_version))
            self.commit()
            logger.info(f"Registered instance: {instance_id} on {server_name}")
        except Error as e:
            logger.error(f"Failed to upsert instance {instance_id}: {e}")
            self.rollback()
            raise
    
    def get_instance_plugins(self, instance_id: str) -> List[Dict[str, Any]]:
        """
        Get all plugins currently installed on an instance from plugin_versions table
        
        Args:
            instance_id: Instance to query
            
        Returns:
            List of dicts with keys: plugin_name, installed_version, jar_filename, jar_hash
        """
        try:
            self.cursor.execute("""
                SELECT plugin_name, installed_version, jar_filename, jar_hash
                FROM plugin_versions
                WHERE instance_id = %s
            """, (instance_id,))
            return self.cursor.fetchall()
        except Error as e:
            logger.debug(f"Could not fetch plugins for {instance_id}: {e}")
            return []
    
    def get_instance_datapacks(self, instance_id: str) -> List[Dict[str, Any]]:
        """
        Get all datapacks currently installed on an instance
        
        Args:
            instance_id: Instance to query
            
        Returns:
            List of dicts with keys: datapack_name, version, world_name, file_name, file_hash
        """
        try:
            self.cursor.execute("""
                SELECT datapack_name, version, world_name, file_name, file_hash
                FROM instance_datapacks
                WHERE instance_id = %s
            """, (instance_id,))
            return self.cursor.fetchall()
        except Error as e:
            logger.debug(f"Could not fetch datapacks for {instance_id}: {e}")
            return []
    
    def upsert_datapack(self, instance_id: str, datapack_name: str, world_name: str,
                       version: Optional[str] = None, file_name: Optional[str] = None,
                       file_hash: Optional[str] = None, is_enabled: bool = True):
        """
        Register or update a datapack installation
        """
        try:
            self.cursor.execute("""
                INSERT INTO instance_datapacks
                (instance_id, datapack_name, world_name, version, file_name, file_hash, is_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    version = COALESCE(VALUES(version), version),
                    file_name = COALESCE(VALUES(file_name), file_name),
                    file_hash = VALUES(file_hash),
                    is_enabled = VALUES(is_enabled),
                    last_checked_at = CURRENT_TIMESTAMP
            """, (instance_id, datapack_name, world_name, version, file_name, file_hash, is_enabled))
            self.commit()
        except Error as e:
            logger.error(f"Failed to upsert datapack {datapack_name} for {instance_id}: {e}")
            self.rollback()
    
    def remove_datapack(self, instance_id: str, datapack_name: str, world_name: str):
        """Remove a datapack record (when uninstalled)"""
        try:
            self.cursor.execute("""
                DELETE FROM instance_datapacks
                WHERE instance_id = %s AND datapack_name = %s AND world_name = %s
            """, (instance_id, datapack_name, world_name))
            self.commit()
        except Error as e:
            logger.error(f"Failed to remove datapack {datapack_name}: {e}")
            self.rollback()
    
    def get_server_properties(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get server.properties data for an instance
        
        Returns:
            Dict with server property values or None
        """
        try:
            self.cursor.execute("""
                SELECT level_name, gamemode, difficulty, max_players, view_distance,
                       simulation_distance, pvp, spawn_protection, properties_json
                FROM instance_server_properties
                WHERE instance_id = %s
            """, (instance_id,))
            return self.cursor.fetchone()
        except Error as e:
            logger.debug(f"Could not fetch server properties for {instance_id}: {e}")
            return None
    
    def upsert_server_properties(self, instance_id: str, properties: Dict[str, Any]):
        """
        Update server.properties tracking for an instance
        
        Args:
            instance_id: Instance ID
            properties: Dict with keys: level_name, gamemode, difficulty, max_players, etc.
        """
        import json
        try:
            self.cursor.execute("""
                INSERT INTO instance_server_properties
                (instance_id, level_name, gamemode, difficulty, max_players, view_distance,
                 simulation_distance, pvp, spawn_protection, properties_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    level_name = VALUES(level_name),
                    gamemode = VALUES(gamemode),
                    difficulty = VALUES(difficulty),
                    max_players = VALUES(max_players),
                    view_distance = VALUES(view_distance),
                    simulation_distance = VALUES(simulation_distance),
                    pvp = VALUES(pvp),
                    spawn_protection = VALUES(spawn_protection),
                    properties_json = VALUES(properties_json),
                    last_updated_at = CURRENT_TIMESTAMP
            """, (
                instance_id,
                properties.get('level_name'),
                properties.get('gamemode'),
                properties.get('difficulty'),
                properties.get('max_players'),
                properties.get('view_distance'),
                properties.get('simulation_distance'),
                properties.get('pvp'),
                properties.get('spawn_protection'),
                json.dumps(properties)
            ))
            self.commit()
        except Error as e:
            logger.error(f"Failed to upsert server properties for {instance_id}: {e}")
            self.rollback()
    
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
    
    # ========================================================================
    # CHANGE HISTORY & TRACKING (NEW - Option C Implementation)
    # ========================================================================
    
    def log_config_change(self, 
                         instance_id: Optional[str],
                         plugin_name: str,
                         config_file: str,
                         config_key: str,
                         old_value: Any,
                         new_value: Any,
                         change_type: str = 'manual',
                         change_source: str = 'config_updater',
                         changed_by: Optional[str] = None,
                         change_reason: Optional[str] = None,
                         batch_id: Optional[str] = None,
                         deployment_id: Optional[int] = None) -> int:
        """
        Log a config change to database audit trail
        
        Args:
            instance_id: Instance ID (None for global changes)
            plugin_name: Plugin name
            config_file: Config file path
            config_key: Config key path (dot notation)
            old_value: Previous value (as JSON string)
            new_value: New value (as JSON string)
            change_type: Type of change (manual, automated, drift_fix, rule_based)
            change_source: Source of change (config_updater, web_ui, api, agent)
            changed_by: Username who made the change
            change_reason: Optional reason/description
            batch_id: Optional batch ID for grouping related changes
            deployment_id: Optional deployment ID if part of deployment
            
        Returns:
            change_id of inserted record
        """
        import json
        import os
        
        # Convert values to JSON strings if they're not already
        if not isinstance(old_value, str):
            old_value = json.dumps(old_value)
        if not isinstance(new_value, str):
            new_value = json.dumps(new_value)
        
        # Get username if not provided
        if changed_by is None:
            changed_by = os.getenv('USER', os.getenv('USERNAME', 'unknown'))
        
        self.cursor.execute("""
            INSERT INTO config_change_history
            (instance_id, plugin_name, config_file, config_key,
             old_value, new_value, change_type, change_source,
             changed_by, change_reason, batch_id, deployment_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            instance_id,
            plugin_name,
            config_file,
            config_key,
            old_value,
            new_value,
            change_type,
            change_source,
            changed_by,
            change_reason,
            batch_id,
            deployment_id
        ))
        
        self.commit()
        
        return self.cursor.lastrowid
    
    def get_change_history(self,
                          instance_id: Optional[str] = None,
                          plugin_name: Optional[str] = None,
                          changed_by: Optional[str] = None,
                          change_type: Optional[str] = None,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[Dict[str, Any]]:
        """
        Query config change history with filters
        
        Returns list of change records
        """
        query = "SELECT * FROM config_change_history WHERE 1=1"
        params = []
        
        if instance_id:
            query += " AND instance_id = %s"
            params.append(instance_id)
        
        if plugin_name:
            query += " AND plugin_name = %s"
            params.append(plugin_name)
        
        if changed_by:
            query += " AND changed_by = %s"
            params.append(changed_by)
        
        if change_type:
            query += " AND change_type = %s"
            params.append(change_type)
        
        if start_date:
            query += " AND changed_at >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND changed_at <= %s"
            params.append(end_date)
        
        query += " ORDER BY changed_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def get_plugin_migrations(self, plugin_name: str) -> List[Dict[str, Any]]:
        """Get known config key migrations for a plugin"""
        self.cursor.execute("""
            SELECT * FROM config_key_migrations
            WHERE plugin_name = %s
            ORDER BY from_version, to_version
        """, (plugin_name,))
        return self.cursor.fetchall()
    
    def create_deployment(self,
                         deployment_type: str,
                         scope: str,
                         target_instances: str,
                         deployed_by: str,
                         deployment_notes: Optional[str] = None) -> int:
        """
        Create new deployment record
        
        Returns deployment_id
        """
        self.cursor.execute("""
            INSERT INTO deployment_history
            (deployment_type, scope, target_instances, deployed_by, deployment_notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (deployment_type, scope, target_instances, deployed_by, deployment_notes))
        
        self.commit()
        
        return self.cursor.lastrowid
    
    def update_deployment_status(self,
                                 deployment_id: int,
                                 status: str,
                                 error_message: Optional[str] = None):
        """Update deployment status"""
        if status == 'completed':
            self.cursor.execute("""
                UPDATE deployment_history
                SET deployment_status = %s, completed_at = NOW()
                WHERE deployment_id = %s
            """, (status, deployment_id))
        elif status == 'failed':
            self.cursor.execute("""
                UPDATE deployment_history
                SET deployment_status = %s, completed_at = NOW(), error_message = %s
                WHERE deployment_id = %s
            """, (status, error_message, deployment_id))
        else:
            self.cursor.execute("""
                UPDATE deployment_history
                SET deployment_status = %s
                WHERE deployment_id = %s
            """, (status, deployment_id))
        
        self.commit()
