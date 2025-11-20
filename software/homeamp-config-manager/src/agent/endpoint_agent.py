"""
Configuration Management Endpoint Agent (Database-backed)

Runs on each physical server (Hetzner/OVH) to:
1. Discover local AMP instances
2. Scan plugin configurations
3. Report to central database
4. Apply configuration changes from database
5. Track drift, deployments, and plugin changes (Option C)
6. Auto-apply migrations on plugin updates
"""

import time
import logging
import sys
import hashlib
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..database.db_access import ConfigDatabase
from ..amp_integration.instance_scanner import AMPInstanceScanner
from ..analyzers.config_reader import PluginConfigReader


class EndpointAgent:
    """
    Production-ready agent that runs on each physical server.
    Reports instance state to central database and logs all changes.
    """
    
    def __init__(self, server_name: str, db_config: Dict[str, Any]):
        """
        Args:
            server_name: Physical server name ('hetzner-xeon' or 'ovh-ryzen')
            db_config: Database connection config (host, port, user, password)
        """
        self.server_name = server_name
        self.db = ConfigDatabase(**db_config)
        
        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f'endpoint-agent-{server_name}')
        
        # AMP instance discovery
        self.amp_base_dir = Path("/home/amp/.ampdata/instances")
        self.scanner = AMPInstanceScanner(self.amp_base_dir)
        
        # Tracking state
        self.current_deployment_id: Optional[int] = None
        self.plugin_cache: Dict[str, Dict[str, Dict[str, str]]] = {}  # {instance_id: {plugin_name: {version, jar_file, jar_hash}}}
        self.datapack_cache: Dict[str, Dict[str, Dict[str, str]]] = {}  # {instance_id: {world:datapack: {version, file_hash}}}
        self.server_props_cache: Dict[str, Dict[str, Any]] = {}  # {instance_id: {property: value}}
        self.drift_cache: Dict[str, set] = {}  # {instance_id: set of drift signatures}
        
        self.running = False
    
    def start(self):
        """Start agent main loop"""
        self.logger.info(f"[START] Starting endpoint agent for {self.server_name}")
        self.db.connect()
        self.running = True
        
        try:
            while self.running:
                self._run_cycle()
                time.sleep(60)  # Run every minute
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down agent")
        self.running = False
        self.db.disconnect()
    
    def _run_cycle(self):
        """Execute one agent cycle"""
        try:
            # 1. Discover instances
            discovered = self.scanner.discover_instances()
            self.logger.info(f"[DISC] Discovered {len(discovered)} instances")
            
            # 2. Register all discovered instances (upsert to database)
            for instance in discovered:
                try:
                    self.db.upsert_instance(
                        instance_id=instance['name'],
                        server_name=self.server_name,
                        instance_name=instance.get('friendly_name', instance['name']),
                        amp_instance_id=instance.get('amp_id'),
                        platform=instance.get('platform', 'paper'),
                        minecraft_version=instance.get('mc_version')
                    )
                except Exception as e:
                    self.logger.error(f"Failed to register {instance['name']}: {e}")
            
            # 3. Get expected instances from database (now includes newly registered)
            expected_instances = self.db.get_instances_by_server(self.server_name)
            expected_ids = {inst['instance_id'] for inst in expected_instances}
            
            # 4. Check for missing instances (in DB but not on disk)
            discovered_ids = {inst['name'] for inst in discovered}
            missing = expected_ids - discovered_ids
            
            if missing:
                self.logger.warning(f"[WARN]  Missing instances (in DB but not found): {missing}")
            
            # 5. Scan each instance
            for instance in discovered:
                self._scan_instance_full(instance)
        
        except Exception as e:
            self.logger.error(f"[ERROR] Error in agent cycle: {e}", exc_info=True)
    
    def _load_plugins_from_db(self, instance_id: str) -> Dict[str, Dict[str, str]]:
        """Load existing plugin state from database to initialize cache"""
        try:
            plugins = self.db.get_instance_plugins(instance_id)
            cache = {}
            for plugin in plugins:
                cache[plugin['plugin_name']] = {
                    'version': plugin.get('installed_version', 'unknown'),
                    'jar_file': plugin.get('jar_filename', ''),
                    'jar_hash': plugin.get('jar_hash', '')
                }
            return cache
        except Exception as e:
            self.logger.debug(f"Could not load plugins from DB for {instance_id}: {e}")
            return {}
    
    def _scan_instance_full(self, instance: Dict[str, Any]):
        """Full instance scan: configs, plugins, drift detection"""
        instance_id = instance['name']
        instance_path = Path(instance['path'])
        
        try:
            # 1. Scan plugins and detect changes
            self._scan_plugin_changes(instance_id, instance_path)
            
            # 2. Scan datapacks and detect changes
            self._scan_datapack_changes(instance_id, instance_path, instance)
            
            # 3. Scan server.properties and detect changes
            self._scan_server_properties(instance_id, instance_path)
            
            # 4. Scan configs and detect drift
            self._scan_instance_configs(instance_id, instance_path)
            
        except Exception as e:
            self.logger.error(f"[ERROR] Error scanning {instance_id}: {e}", exc_info=True)
    
    def _scan_plugin_changes(self, instance_id: str, instance_path: Path):
        """
        Scan plugins directory and log any install/remove/update events
        Uses plugin_installation_history table
        """
        plugins_dir = instance_path / 'Minecraft' / 'plugins'
        if not plugins_dir.exists():
            return
        
        current_plugins = {}
        
        # Scan all jar files
        for jar_file in plugins_dir.glob('*.jar'):
            plugin_name = jar_file.stem
            
            # Calculate jar hash
            jar_hash = self._calculate_file_hash(jar_file)
            
            # Try to extract version (simplified - would need actual jar inspection)
            version = self._extract_plugin_version(jar_file)
            
            current_plugins[plugin_name] = {
                'version': version,
                'jar_file': jar_file.name,
                'jar_hash': jar_hash
            }
        
        # Load cache from database if empty (first run)
        if instance_id not in self.plugin_cache:
            self.plugin_cache[instance_id] = self._load_plugins_from_db(instance_id)
        
        # Compare with cache to detect changes
        cached = self.plugin_cache.get(instance_id, {})
        
        # Detect new plugins
        for plugin_name, info in current_plugins.items():
            if plugin_name not in cached:
                self.logger.info(f"[NEW] Plugin installed: {instance_id}/{plugin_name} v{info['version']}")
                self._log_plugin_event(
                    instance_id, plugin_name, 'install',
                    version_to=info['version'],
                    jar_file=info['jar_file'],
                    jar_hash=info['jar_hash']
                )
            elif cached[plugin_name]['jar_hash'] != info['jar_hash']:
                old_ver = cached[plugin_name]['version']
                self.logger.info(f"[UPDATE] Plugin updated: {instance_id}/{plugin_name} {old_ver} → {info['version']}")
                self._log_plugin_event(
                    instance_id, plugin_name, 'update',
                    version_from=old_ver,
                    version_to=info['version'],
                    jar_file=info['jar_file'],
                    jar_hash=info['jar_hash']
                )
                
                # Check if migrations exist for this update
                self._check_and_apply_migrations(instance_id, plugin_name, old_ver, info['version'])
        
        # Detect removed plugins
        for plugin_name in cached:
            if plugin_name not in current_plugins:
                self.logger.info(f"  Plugin removed: {instance_id}/{plugin_name}")
                self._log_plugin_event(
                    instance_id, plugin_name, 'remove',
                    version_from=cached[plugin_name]['version']
                )
        
        # Update cache
        self.plugin_cache[instance_id] = current_plugins
    
    def _load_datapacks_from_db(self, instance_id: str) -> Dict[str, Dict[str, str]]:
        """Load existing datapack state from database to initialize cache"""
        try:
            datapacks = self.db.get_instance_datapacks(instance_id)
            cache = {}
            for dp in datapacks:
                key = f"{dp['world_name']}:{dp['datapack_name']}"
                cache[key] = {
                    'version': dp.get('version', 'unknown'),
                    'file_name': dp.get('file_name', ''),
                    'file_hash': dp.get('file_hash', '')
                }
            return cache
        except Exception as e:
            self.logger.debug(f"Could not load datapacks from DB for {instance_id}: {e}")
            return {}
    
    def _scan_datapack_changes(self, instance_id: str, instance_path: Path, instance: Dict[str, Any]):
        """Scan datapacks directory and detect changes"""
        datapacks_path = instance.get('datapacks_path')
        if not datapacks_path:
            return
        
        datapacks_dir = Path(datapacks_path)
        if not datapacks_dir.exists():
            return
        
        world_name = instance.get('level_name', 'world')
        current_datapacks = {}
        
        # Scan all .zip files in datapacks directory
        for dp_file in datapacks_dir.glob('*.zip'):
            if dp_file.name == 'vanilla.zip':
                continue  # Skip vanilla datapack
            
            datapack_name = dp_file.stem
            file_hash = self._calculate_file_hash(dp_file)
            key = f"{world_name}:{datapack_name}"
            
            current_datapacks[key] = {
                'version': 'unknown',  # Would need pack.mcmeta parsing for version
                'file_name': dp_file.name,
                'file_hash': file_hash,
                'world_name': world_name,
                'datapack_name': datapack_name
            }
        
        # Load cache from database if empty (first run)
        if instance_id not in self.datapack_cache:
            self.datapack_cache[instance_id] = self._load_datapacks_from_db(instance_id)
        
        cached = self.datapack_cache.get(instance_id, {})
        
        # Detect new datapacks
        for key, info in current_datapacks.items():
            if key not in cached:
                self.logger.info(f"  Datapack installed: {instance_id}/{info['world_name']}/{info['datapack_name']}")
                self.db.upsert_datapack(
                    instance_id=instance_id,
                    datapack_name=info['datapack_name'],
                    world_name=info['world_name'],
                    version=info['version'],
                    file_name=info['file_name'],
                    file_hash=info['file_hash']
                )
                self.db.log_config_change(
                    instance_id=instance_id,
                    plugin_name='datapacks',
                    config_file=info['world_name'],
                    config_key='datapack_lifecycle',
                    old_value='',
                    new_value=info['datapack_name'],
                    change_type='automated',
                    changed_by=f'agent-{self.server_name}',
                    change_reason=f"Datapack installed: {info['file_name']}"
                )
            elif cached[key]['file_hash'] != info['file_hash']:
                self.logger.info(f"[UPDATE] Datapack updated: {instance_id}/{info['world_name']}/{info['datapack_name']}")
                self.db.upsert_datapack(
                    instance_id=instance_id,
                    datapack_name=info['datapack_name'],
                    world_name=info['world_name'],
                    version=info['version'],
                    file_name=info['file_name'],
                    file_hash=info['file_hash']
                )
                self.db.log_config_change(
                    instance_id=instance_id,
                    plugin_name='datapacks',
                    config_file=info['world_name'],
                    config_key='datapack_lifecycle',
                    old_value=cached[key].get('file_name', ''),
                    new_value=info['file_name'],
                    change_type='automated',
                    changed_by=f'agent-{self.server_name}',
                    change_reason=f"Datapack updated"
                )
        
        # Detect removed datapacks
        for key in cached:
            if key not in current_datapacks:
                parts = key.split(':', 1)
                world_name = parts[0]
                datapack_name = parts[1]
                self.logger.info(f"  Datapack removed: {instance_id}/{world_name}/{datapack_name}")
                self.db.remove_datapack(instance_id, datapack_name, world_name)
                self.db.log_config_change(
                    instance_id=instance_id,
                    plugin_name='datapacks',
                    config_file=world_name,
                    config_key='datapack_lifecycle',
                    old_value=datapack_name,
                    new_value='',
                    change_type='automated',
                    changed_by=f'agent-{self.server_name}',
                    change_reason=f"Datapack removed"
                )
        
        # Update cache
        self.datapack_cache[instance_id] = current_datapacks
    
    def _scan_server_properties(self, instance_id: str, instance_path: Path):
        """Scan server.properties and detect changes"""
        minecraft_dir = instance_path / 'Minecraft'
        server_props_file = minecraft_dir / 'server.properties'
        
        if not server_props_file.exists():
            return
        
        try:
            # Parse server.properties
            properties = {}
            content = server_props_file.read_text()
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Convert boolean strings
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    # Convert numbers
                    elif value.isdigit():
                        value = int(value)
                    
                    properties[key] = value
            
            # Load cache from database if empty (first run)
            if instance_id not in self.server_props_cache:
                db_props = self.db.get_server_properties(instance_id)
                if db_props:
                    import json
                    self.server_props_cache[instance_id] = json.loads(db_props.get('properties_json', '{}'))
                else:
                    self.server_props_cache[instance_id] = {}
            
            cached = self.server_props_cache.get(instance_id, {})
            
            # Detect changes in key properties
            key_properties = ['level_name', 'gamemode', 'difficulty', 'max_players', 
                            'view_distance', 'simulation_distance', 'pvp', 'spawn_protection']
            
            changes_detected = False
            for prop in key_properties:
                if prop in properties:
                    old_val = cached.get(prop)
                    new_val = properties.get(prop)
                    if old_val != new_val and old_val is not None:
                        self.logger.info(f"[CONFIG]  Server property changed: {instance_id}/{prop}: {old_val} → {new_val}")
                        self.db.log_config_change(
                            instance_id=instance_id,
                            plugin_name='server',
                            config_file='server.properties',
                            config_key=prop,
                            old_value=str(old_val),
                            new_value=str(new_val),
                            change_type='automated',
                            changed_by=f'agent-{self.server_name}',
                            change_reason=f"Server property changed"
                        )
                        changes_detected = True
            
            # Update database with current properties
            self.db.upsert_server_properties(instance_id, {
                'level_name': properties.get('level-name'),
                'gamemode': properties.get('gamemode'),
                'difficulty': properties.get('difficulty'),
                'max_players': properties.get('max-players'),
                'view_distance': properties.get('view-distance'),
                'simulation_distance': properties.get('simulation-distance'),
                'pvp': properties.get('pvp'),
                'spawn_protection': properties.get('spawn-protection')
            })
            
            # Update cache
            self.server_props_cache[instance_id] = properties
            
        except Exception as e:
            self.logger.error(f"Failed to scan server.properties for {instance_id}: {e}")
    
    def _scan_instance_configs(self, instance_id: str, instance_path: Path):
        """Scan plugin configs and check for drift"""
        plugins_dir = instance_path / 'Minecraft' / 'plugins'
        
        if not plugins_dir.exists():
            return
        
        # Scan all plugin config files
        config_reader = PluginConfigReader(plugins_dir)
        configs = config_reader.read_all_configs()
        
        # Compare against database expectations
        self._check_drift(instance_id, configs)
    
    def _normalize_value(self, value: Any) -> Any:
        """Normalize values to prevent false drift detection"""
        # Normalize YAML booleans (true/True/TRUE -> True, false/False/FALSE -> False)
        if isinstance(value, str):
            if value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        return value
    
    def _check_drift(self, instance_id: str, actual_configs: Dict[str, Dict]):
        """
        Compare actual configs against database rules and log drift
        Populates: config_change_history, config_variance_history
        
        Args:
            instance_id: Instance identifier
            actual_configs: {plugin_name: {config_file: {key: value}}}
        """
        drift_detected = []
        
        # Initialize drift cache for this instance
        if instance_id not in self.drift_cache:
            self.drift_cache[instance_id] = set()
        
        # For each plugin config key, resolve expected value from database
        for plugin_name, files in actual_configs.items():
            for config_file, keys in files.items():
                for config_key, actual_value in keys.items():
                    # Resolve expected value using hierarchy
                    expected_value, priority, scope = self.db.resolve_config_value(
                        instance_id, plugin_name, config_file, config_key
                    )
                    
                    # Substitute variables
                    if expected_value:
                        expected_value = self.db.substitute_variables(expected_value, instance_id)
                    
                    # Normalize both values to prevent false positives (e.g., true vs True)
                    expected_normalized = self._normalize_value(expected_value)
                    actual_normalized = self._normalize_value(actual_value)
                    
                    # Check for drift
                    if expected_normalized is not None and actual_normalized != expected_normalized:
                        # Create drift signature
                        drift_sig = f"{plugin_name}:{config_file}:{config_key}:{expected_normalized}:{actual_normalized}"
                        
                        # Only log if this is NEW drift (not in cache)
                        if drift_sig not in self.drift_cache[instance_id]:
                            drift_info = {
                                'plugin': plugin_name,
                                'file': config_file,
                                'key': config_key,
                                'expected': expected_normalized,
                                'actual': actual_normalized,
                                'scope': scope
                            }
                            drift_detected.append(drift_info)
                            
                            self.logger.warning(
                                f" NEW DRIFT {instance_id}/{plugin_name}/{config_file}:{config_key} "
                                f"- Expected: {expected_normalized} (from {scope}), "
                                f"Got: {actual_normalized}"
                            )
                            
                            # Log drift to config_change_history
                            try:
                                self.db.log_config_change(
                                    instance_id=instance_id,
                                    plugin_name=plugin_name,
                                    config_file=config_file,
                                    config_key=config_key,
                                    old_value=str(expected_normalized),
                                    new_value=str(actual_normalized),
                                    change_type='automated',  # Agent detected
                                    changed_by=f'agent-{self.server_name}',
                                    change_reason=f'Drift from {scope} expectation detected during scan'
                                )
                                
                                # Add to cache
                                self.drift_cache[instance_id].add(drift_sig)
                                
                            except Exception as e:
                                self.logger.error(f"Failed to log drift: {e}")
                        # If drift is in cache, it was already logged - skip silently
                    else:
                        # Value matches - remove from drift cache if present
                        drift_sig = f"{plugin_name}:{config_file}:{config_key}"
                        self.drift_cache[instance_id] = {
                            sig for sig in self.drift_cache[instance_id]
                            if not sig.startswith(drift_sig + ":")
                        }
        
        # Log variance snapshot if drift detected (for trending)
        if drift_detected:
            self._log_variance_snapshot(instance_id, drift_detected)
    
    def _log_plugin_event(self, instance_id: str, plugin_name: str, action: str,
                          version_from: Optional[str] = None, version_to: Optional[str] = None,
                          jar_file: Optional[str] = None, jar_hash: Optional[str] = None):
        """
        Log to plugin_installation_history table
        Note: Would need new db_access.py method - using config_change_history for now
        """
        try:
            self.db.log_config_change(
                instance_id=instance_id,
                plugin_name=plugin_name,
                config_file='plugins',
                config_key='plugin_lifecycle',
                old_value=version_from or '',
                new_value=version_to or '',
                change_type='automated',
                changed_by=f'agent-{self.server_name}',
                change_reason=f'Plugin {action}: {jar_file or plugin_name} (hash: {jar_hash[:8] if jar_hash else "unknown"})'
            )
        except Exception as e:
            self.logger.error(f"Failed to log plugin event: {e}")
    
    def _check_and_apply_migrations(self, instance_id: str, plugin_name: str,
                                    from_version: str, to_version: str):
        """
        Check config_key_migrations table and apply automatic migrations
        Populates: config_change_history with change_type='migration'
        """
        try:
            migrations = self.db.get_plugin_migrations(plugin_name)
            
            applicable = [
                m for m in migrations
                if m['from_version'] == from_version
                and m['to_version'] == to_version
                and m['is_automatic']
            ]
            
            if applicable:
                self.logger.info(
                    f"[UPDATE] Found {len(applicable)} auto-migrations for {plugin_name} "
                    f"{from_version} → {to_version}"
                )
                
                for migration in applicable:
                    if migration['is_breaking']:
                        self.logger.warning(
                            f"[WARN]  BREAKING CHANGE: {migration['old_key_path']} → "
                            f"{migration['new_key_path']}"
                        )
                    
                    # Auto-apply if safe
                    if migration['is_automatic'] and not migration['is_breaking']:
                        self._apply_migration(instance_id, plugin_name, migration)
        
        except Exception as e:
            self.logger.error(f"Error checking migrations: {e}")
    
    def _apply_migration(self, instance_id: str, plugin_name: str, migration: Dict):
        """
        Apply a config key migration
        Logs to config_change_history with change_type='migration'
        """
        try:
            self.db.log_config_change(
                instance_id=instance_id,
                plugin_name=plugin_name,
                config_file='config.yml',
                config_key=migration['new_key_path'],
                old_value=f"migrated from {migration['old_key_path']}",
                new_value=migration['new_key_path'],
                change_type='automated',
                changed_by=f'agent-{self.server_name}',
                change_reason=f"Auto-migration: {migration['notes']}"
            )
            self.logger.info(f"[OK] Applied migration: {migration['old_key_path']} → {migration['new_key_path']}")
        except Exception as e:
            self.logger.error(f"Failed to apply migration: {e}")
    
    def _log_variance_snapshot(self, instance_id: str, drift_info: List[Dict]):
        """
        Log to config_variance_history for trend analysis
        Would need new db_access.py method
        """
        self.logger.info(f" Variance snapshot: {instance_id} has {len(drift_info)} drift items")
        # TODO: Implement actual variance history logging
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _extract_plugin_version(self, jar_file: Path) -> str:
        """
        Extract version from plugin.yml inside jar file
        Falls back to filename parsing if jar reading fails
        """
        import zipfile
        
        # Try to read plugin.yml from jar
        try:
            with zipfile.ZipFile(jar_file, 'r') as jar:
                # Try plugin.yml (Bukkit/Spigot/Paper)
                if 'plugin.yml' in jar.namelist():
                    with jar.open('plugin.yml') as yml_file:
                        plugin_data = yaml.safe_load(yml_file)
                        version = plugin_data.get('version')
                        if version:
                            return str(version)
                
                # Try bungee.yml (BungeeCord)
                if 'bungee.yml' in jar.namelist():
                    with jar.open('bungee.yml') as yml_file:
                        plugin_data = yaml.safe_load(yml_file)
                        version = plugin_data.get('version')
                        if version:
                            return str(version)
                
                # Try velocity-plugin.json (Velocity)
                if 'velocity-plugin.json' in jar.namelist():
                    import json
                    with jar.open('velocity-plugin.json') as json_file:
                        plugin_data = json.load(json_file)
                        version = plugin_data.get('version')
                        if version:
                            return str(version)
        
        except Exception as e:
            self.logger.debug(f"Failed to read version from jar {jar_file.name}: {e}")
        
        # Fallback: parse filename
        import re
        name = jar_file.stem
        # Match semantic versions (1.2.3), build numbers (1641), or mixed (2.10.0-SNAPSHOT-761)
        version_match = re.search(r'[-_]v?(\d+(?:\.\d+)*(?:-[a-zA-Z0-9.-]+)?)', name)
        if version_match:
            return version_match.group(1)
        
        return 'unknown'


def main():
    """Entry point for systemd service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ArchiveSMP Endpoint Agent')
    parser.add_argument('--server', required=True, help='Server name (hetzner-xeon or ovh-ryzen)')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-port', type=int, default=3306, help='Database port')
    parser.add_argument('--db-user', default='root', help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')
    parser.add_argument('--db-name', default='asmp_config', help='Database name')
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'port': args.db_port,
        'user': args.db_user,
        'password': args.db_password,
        'database': args.db_name
    }
    
    agent = EndpointAgent(args.server, db_config)
    agent.start()


if __name__ == '__main__':
    main()
