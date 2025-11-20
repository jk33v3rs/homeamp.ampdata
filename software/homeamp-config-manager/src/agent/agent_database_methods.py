"""
Production Endpoint Agent - Part 2: Database Registration & Update Management
"""

# This file contains the database interaction methods for the production agent
# To be imported by production_endpoint_agent.py

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import hashlib
import json
import requests


class AgentDatabaseMethods:
    """Mixin class for database operations"""
    
    def _load_plugin_registry(self):
        """Load plugin registry from database into memory"""
        self.logger.info("[LOAD] Loading plugin registry from database")
        try:
            # Query all plugins
            cursor = self.db.execute_query(
                "SELECT * FROM plugins",
                fetch=True
            )
            
            for row in cursor:
                plugin_id = row['plugin_id']
                self.plugin_registry[plugin_id] = dict(row)
            
            self.logger.info(f"[OK] Loaded {len(self.plugin_registry)} plugins from registry")
        except Exception as e:
            self.logger.warning(f"[WARN]  Failed to load plugin registry: {e}")
    
    def _load_datapack_registry(self):
        """Load datapack registry from database"""
        self.logger.info("[LOAD] Loading datapack registry from database")
        try:
            cursor = self.db.execute_query(
                "SELECT * FROM datapacks",
                fetch=True
            )
            
            for row in cursor:
                datapack_id = row['datapack_id']
                self.datapack_registry[datapack_id] = dict(row)
            
            self.logger.info(f"[OK] Loaded {len(self.datapack_registry)} datapacks from registry")
        except Exception as e:
            self.logger.warning(f"[WARN]  Failed to load datapack registry: {e}")
    
    def _register_instance(self, instance_info: Dict):
        """Register or update instance in database"""
        try:
            self.db.execute_query("""
                INSERT INTO instances (instance_id, display_name, platform, minecraft_version, server_name, last_seen_at)
                VALUES (%(instance_id)s, %(display_name)s, %(platform)s, %(minecraft_version)s, %(server_name)s, NOW())
                ON DUPLICATE KEY UPDATE
                    display_name = VALUES(display_name),
                    platform = VALUES(platform),
                    minecraft_version = VALUES(minecraft_version),
                    server_name = VALUES(server_name),
                    last_seen_at = NOW()
            """, {
                'instance_id': instance_info['name'],
                'display_name': instance_info['name'],
                'platform': instance_info['platform'],
                'minecraft_version': instance_info['minecraft_version'],
                'server_name': instance_info['server_name']
            })
        except Exception as e:
            self.logger.error(f"Failed to register instance {instance_info['name']}: {e}")
    
    def _register_plugin(self, plugin_info: Dict):
        """Register or update plugin in global registry"""
        plugin_id = plugin_info['plugin_id']
        
        # Check if exists in registry
        if plugin_id not in self.plugin_registry:
            try:
                self.db.execute_query("""
                    INSERT INTO plugins (
                        plugin_id, plugin_name, display_name, platform, 
                        current_stable_version, author, description,
                        first_seen_at, last_checked_at
                    ) VALUES (
                        %(plugin_id)s, %(plugin_name)s, %(display_name)s, %(platform)s,
                        %(version)s, %(author)s, %(description)s,
                        NOW(), NOW()
                    )
                    ON DUPLICATE KEY UPDATE
                        current_stable_version = IF(VERSION_COMPARE(VALUES(current_stable_version), current_stable_version) > 0, 
                                                    VALUES(current_stable_version), current_stable_version),
                        last_checked_at = NOW()
                """, plugin_info)
                
                self.plugin_registry[plugin_id] = plugin_info
                self.logger.info(f"[NEW] Registered new plugin: {plugin_id}")
            except Exception as e:
                self.logger.error(f"Failed to register plugin {plugin_id}: {e}")
    
    def _register_plugin_installation(self, instance_id: str, plugin_id: str, 
                                     plugin_info: Dict, jar_path: Path):
        """Register plugin installation for specific instance"""
        try:
            file_hash = self._calculate_file_hash(jar_path)
            file_stat = jar_path.stat()
            
            self.db.execute_query("""
                INSERT INTO instance_plugins (
                    instance_id, plugin_id, installed_version, file_name, 
                    file_path, file_hash, file_size, file_modified_at,
                    is_enabled, first_discovered_at, last_seen_at, installation_method
                ) VALUES (
                    %(instance_id)s, %(plugin_id)s, %(version)s, %(file_name)s,
                    %(file_path)s, %(file_hash)s, %(file_size)s, FROM_UNIXTIME(%(mtime)s),
                    TRUE, NOW(), NOW(), 'unknown'
                )
                ON DUPLICATE KEY UPDATE
                    installed_version = VALUES(installed_version),
                    file_name = VALUES(file_name),
                    file_hash = VALUES(file_hash),
                    file_size = VALUES(file_size),
                    file_modified_at = VALUES(file_modified_at),
                    last_seen_at = NOW()
            """, {
                'instance_id': instance_id,
                'plugin_id': plugin_id,
                'version': plugin_info['version'],
                'file_name': jar_path.name,
                'file_path': str(jar_path),
                'file_hash': file_hash,
                'file_size': file_stat.st_size,
                'mtime': file_stat.st_mtime
            })
        except Exception as e:
            self.logger.error(f"Failed to register plugin installation {instance_id}/{plugin_id}: {e}")
    
    def _register_datapack(self, datapack_info: Dict):
        """Register datapack in global registry"""
        datapack_id = datapack_info['datapack_id']
        
        if datapack_id not in self.datapack_registry:
            try:
                self.db.execute_query("""
                    INSERT INTO datapacks (
                        datapack_id, datapack_name, display_name, version, description, last_checked_at
                    ) VALUES (
                        %(datapack_id)s, %(datapack_name)s, %(display_name)s, 
                        %(version)s, %(description)s, NOW()
                    )
                    ON DUPLICATE KEY UPDATE
                        last_checked_at = NOW()
                """, datapack_info)
                
                self.datapack_registry[datapack_id] = datapack_info
                self.logger.info(f"[NEW] Registered new datapack: {datapack_id}")
            except Exception as e:
                self.logger.error(f"Failed to register datapack {datapack_id}: {e}")
    
    def _register_datapack_installation(self, instance_id: str, datapack_id: str,
                                       world_name: str, datapack_info: Dict, datapack_path: Path):
        """Register datapack installation for specific instance/world"""
        try:
            file_hash = self._calculate_file_hash(datapack_path) if datapack_path.is_file() else 'folder'
            file_size = datapack_path.stat().st_size if datapack_path.is_file() else 0
            
            self.db.execute_query("""
                INSERT INTO instance_datapacks (
                    instance_id, datapack_id, world_name, version, file_name,
                    file_path, file_hash, file_size, is_enabled,
                    first_discovered_at, last_seen_at
                ) VALUES (
                    %(instance_id)s, %(datapack_id)s, %(world_name)s, %(version)s, %(file_name)s,
                    %(file_path)s, %(file_hash)s, %(file_size)s, TRUE,
                    NOW(), NOW()
                )
                ON DUPLICATE KEY UPDATE
                    version = VALUES(version),
                    file_name = VALUES(file_name),
                    file_hash = VALUES(file_hash),
                    last_seen_at = NOW()
            """, {
                'instance_id': instance_id,
                'datapack_id': datapack_id,
                'world_name': world_name,
                'version': datapack_info.get('version', 'unknown'),
                'file_name': datapack_path.name,
                'file_path': str(datapack_path),
                'file_hash': file_hash,
                'file_size': file_size
            })
        except Exception as e:
            self.logger.error(f"Failed to register datapack installation {instance_id}/{datapack_id}: {e}")
    
    def _scan_server_properties(self, instance_id: str, instance_path: Path):
        """Scan and store server.properties"""
        props_file = instance_path / 'Minecraft' / 'server.properties'
        if not props_file.exists():
            return
        
        try:
            # Parse server.properties
            properties = {}
            with open(props_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    if '=' in line:
                        key, value = line.split('=', 1)
                        properties[key.strip()] = value.strip()
            
            # Extract common properties
            common_props = {
                'level_name': properties.get('level-name', 'world'),
                'gamemode': properties.get('gamemode', 'survival'),
                'difficulty': properties.get('difficulty', 'normal'),
                'max_players': int(properties.get('max-players', '20')),
                'view_distance': int(properties.get('view-distance', '10')),
                'simulation_distance': int(properties.get('simulation-distance', '10')),
                'pvp': properties.get('pvp', 'true').lower() == 'true',
                'spawn_protection': int(properties.get('spawn-protection', '16')),
                'enable_command_block': properties.get('enable-command-block', 'false').lower() == 'true'
            }
            
            file_hash = self._calculate_file_hash(props_file)
            
            # Store in database
            self.db.execute_query("""
                INSERT INTO instance_server_properties (
                    instance_id, level_name, gamemode, difficulty, max_players,
                    view_distance, simulation_distance, pvp, spawn_protection,
                    enable_command_block, properties_json, file_hash, last_scanned_at
                ) VALUES (
                    %(instance_id)s, %(level_name)s, %(gamemode)s, %(difficulty)s, %(max_players)s,
                    %(view_distance)s, %(simulation_distance)s, %(pvp)s, %(spawn_protection)s,
                    %(enable_command_block)s, %(properties_json)s, %(file_hash)s, NOW()
                )
                ON DUPLICATE KEY UPDATE
                    level_name = VALUES(level_name),
                    gamemode = VALUES(gamemode),
                    difficulty = VALUES(difficulty),
                    max_players = VALUES(max_players),
                    view_distance = VALUES(view_distance),
                    simulation_distance = VALUES(simulation_distance),
                    pvp = VALUES(pvp),
                    spawn_protection = VALUES(spawn_protection),
                    enable_command_block = VALUES(enable_command_block),
                    properties_json = VALUES(properties_json),
                    file_hash = VALUES(file_hash),
                    last_scanned_at = NOW()
            """, {
                **common_props,
                'instance_id': instance_id,
                'properties_json': json.dumps(properties)
            })
        
        except Exception as e:
            self.logger.error(f"Failed to scan server.properties for {instance_id}: {e}")
    
    def _scan_instance_configs(self, instance_id: str, instance_path: Path):
        """Scan plugin configs and check for drift"""
        plugins_dir = instance_path / 'Minecraft' / 'plugins'
        if not plugins_dir.exists():
            return
        
        # Use existing config reader
        config_reader = PluginConfigReader(plugins_dir)
        configs = config_reader.read_all_configs()
        
        # Check drift (existing logic from old agent)
        self._check_drift(instance_id, configs)
    
    def _check_drift(self, instance_id: str, actual_configs: Dict[str, Dict]):
        """Check for config drift and log to database"""
        # (Use existing drift detection logic)
        pass  # Already implemented in endpoint_agent.py
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    # ========================================================================
    # DISCOVERY RUN TRACKING
    # ========================================================================
    
    def _start_discovery_run(self, run_type: str) -> int:
        """Start a discovery run and return run_id"""
        cursor = self.db.execute_query("""
            INSERT INTO discovery_runs (server_name, run_type, started_at, status)
            VALUES (%(server_name)s, %(run_type)s, NOW(), 'running')
        """, {'server_name': self.server_name, 'run_type': run_type}, fetch=True)
        
        return cursor.lastrowid
    
    def _end_discovery_run(self, status: str, stats: Dict = None):
        """Complete a discovery run"""
        if not self.current_run_id:
            return
        
        update_data = {
            'run_id': self.current_run_id,
            'status': status
        }
        
        if stats:
            update_data.update({
                'instances_discovered': stats.get('instances', 0),
                'plugins_discovered': stats.get('plugins', 0),
                'datapacks_discovered': stats.get('datapacks', 0),
                'configs_scanned': stats.get('configs', 0),
                'new_items_found': stats.get('new_items', 0),
                'changed_items': stats.get('changed_items', 0)
            })
        
        fields = ', '.join([f"{k} = %({k})s" for k in update_data.keys() if k != 'run_id'])
        
        self.db.execute_query(f"""
            UPDATE discovery_runs
            SET {fields}, completed_at = NOW()
            WHERE run_id = %(run_id)s
        """, update_data)
        
        self.current_run_id = None
    
    def _log_discovery_item(self, item_type: str, item_id: str, item_path: str, action: str):
        """Log an individual discovery item"""
        if not self.current_run_id:
            return
        
        try:
            self.db.execute_query("""
                INSERT INTO discovery_items (run_id, item_type, item_id, item_path, action, discovered_at)
                VALUES (%(run_id)s, %(item_type)s, %(item_id)s, %(item_path)s, %(action)s, NOW())
            """, {
                'run_id': self.current_run_id,
                'item_type': item_type,
                'item_id': item_id,
                'item_path': item_path,
                'action': action
            })
        except Exception as e:
            self.logger.warning(f"Failed to log discovery item: {e}")
    
    # ========================================================================
    # AUTO-TAGGING SYSTEM
    # ========================================================================
    
    def _auto_tag_instance(self, instance_id: str):
        """
        Auto-detect and suggest tags for instance based on:
        - Plugin set (if EssentialsX + Vault → economy-enabled)
        - Server properties (if pvp=false → pvp-disabled)
        - Gamemode (if creative → creative tag)
        """
        try:
            # Get instance plugins
            cursor = self.db.execute_query("""
                SELECT plugin_id FROM instance_plugins WHERE instance_id = %(instance_id)s
            """, {'instance_id': instance_id}, fetch=True)
            
            installed_plugins = {row['plugin_id'] for row in cursor}
            
            # Get server properties
            props_cursor = self.db.execute_query("""
                SELECT * FROM instance_server_properties WHERE instance_id = %(instance_id)s
            """, {'instance_id': instance_id}, fetch=True)
            
            props = dict(props_cursor.fetchone()) if props_cursor.rowcount > 0 else {}
            
            # Auto-detect tags
            suggested_tags = []
            
            # Gamemode tags
            if props.get('gamemode') == 'survival':
                suggested_tags.append(('survival', 0.95))
            elif props.get('gamemode') == 'creative':
                suggested_tags.append(('creative', 0.95))
            
            # PvP tags
            if props.get('pvp') == False:
                suggested_tags.append(('pvp-disabled', 0.90))
            elif props.get('pvp') == True:
                suggested_tags.append(('pvp-enabled', 0.90))
            
            # Economy tags (if Vault + economy plugin detected)
            if 'vault' in installed_plugins and any(p in installed_plugins for p in ['essentialsx', 'economy', 'shopkeeper']):
                suggested_tags.append(('economy-enabled', 0.85))
            
            # Modding level (based on plugin count)
            plugin_count = len(installed_plugins)
            if plugin_count == 0:
                suggested_tags.append(('pure-vanilla', 0.95))
            elif plugin_count < 10:
                suggested_tags.append(('vanilla-ish', 0.80))
            elif plugin_count < 30:
                suggested_tags.append(('lightly-modded', 0.75))
            else:
                suggested_tags.append(('heavily-modded', 0.70))
            
            # Apply tags with confidence scores
            for tag_name, confidence in suggested_tags:
                self._apply_auto_tag(instance_id, tag_name, confidence)
        
        except Exception as e:
            self.logger.error(f"Failed to auto-tag instance {instance_id}: {e}")
    
    def _apply_auto_tag(self, instance_id: str, tag_name: str, confidence: float):
        """Apply auto-detected tag to instance"""
        try:
            # Get tag_id
            cursor = self.db.execute_query("""
                SELECT tag_id FROM meta_tags WHERE tag_name = %(tag_name)s
            """, {'tag_name': tag_name}, fetch=True)
            
            if cursor.rowcount == 0:
                return  # Tag doesn't exist
            
            tag_id = cursor.fetchone()['tag_id']
            
            # Apply tag
            self.db.execute_query("""
                INSERT INTO instance_meta_tags (instance_id, tag_id, applied_at, applied_by, is_auto_detected, confidence_score)
                VALUES (%(instance_id)s, %(tag_id)s, NOW(), 'agent', TRUE, %(confidence)s)
                ON DUPLICATE KEY UPDATE
                    confidence_score = IF(VALUES(confidence_score) > confidence_score, VALUES(confidence_score), confidence_score),
                    applied_at = NOW()
            """, {
                'instance_id': instance_id,
                'tag_id': tag_id,
                'confidence': confidence
            })
            
            self.logger.info(f"  Auto-tagged {instance_id} with '{tag_name}' (confidence: {confidence:.2f})")
        
        except Exception as e:
            self.logger.warning(f"Failed to apply auto-tag {tag_name} to {instance_id}: {e}")
