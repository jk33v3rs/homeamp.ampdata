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
        self.plugin_cache: Dict[str, Dict[str, str]] = {}  # {instance_id: {plugin: version}}
        self.drift_cache: Dict[str, set] = {}  # {instance_id: set of drift signatures}
        
        self.running = False
    
    def start(self):
        """Start agent main loop"""
        self.logger.info(f"🚀 Starting endpoint agent for {self.server_name}")
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
            self.logger.info(f"📡 Discovered {len(discovered)} instances")
            
            # 2. Get expected instances from database
            expected_instances = self.db.get_instances_by_server(self.server_name)
            expected_ids = {inst['instance_id'] for inst in expected_instances}
            
            # 3. Check for missing instances
            discovered_ids = {inst['name'] for inst in discovered}
            missing = expected_ids - discovered_ids
            unexpected = discovered_ids - expected_ids
            
            if missing:
                self.logger.warning(f"⚠️  Missing instances: {missing}")
            if unexpected:
                self.logger.info(f"🆕 Unexpected instances: {unexpected}")
            
            # 4. Scan each instance
            for instance in discovered:
                if instance['name'] in expected_ids:
                    self._scan_instance_full(instance)
        
        except Exception as e:
            self.logger.error(f"❌ Error in agent cycle: {e}", exc_info=True)
    
    def _scan_instance_full(self, instance: Dict[str, Any]):
        """Full instance scan: configs, plugins, drift detection"""
        instance_id = instance['name']
        instance_path = Path(instance['path'])
        
        try:
            # 1. Scan plugins and detect changes
            self._scan_plugin_changes(instance_id, instance_path)
            
            # 2. Scan configs and check drift
            self._scan_instance_configs(instance_id, instance_path)
            
        except Exception as e:
            self.logger.error(f"❌ Error scanning {instance_id}: {e}", exc_info=True)
    
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
        
        # Compare with cache to detect changes
        cached = self.plugin_cache.get(instance_id, {})
        
        # Detect new plugins
        for plugin_name, info in current_plugins.items():
            if plugin_name not in cached:
                self.logger.info(f"🆕 Plugin installed: {instance_id}/{plugin_name} v{info['version']}")
                self._log_plugin_event(
                    instance_id, plugin_name, 'install',
                    version_to=info['version'],
                    jar_file=info['jar_file'],
                    jar_hash=info['jar_hash']
                )
            elif cached[plugin_name]['jar_hash'] != info['jar_hash']:
                old_ver = cached[plugin_name]['version']
                self.logger.info(f"🔄 Plugin updated: {instance_id}/{plugin_name} {old_ver} → {info['version']}")
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
                self.logger.info(f"🗑️  Plugin removed: {instance_id}/{plugin_name}")
                self._log_plugin_event(
                    instance_id, plugin_name, 'remove',
                    version_from=cached[plugin_name]['version']
                )
        
        # Update cache
        self.plugin_cache[instance_id] = current_plugins
    
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
                                f"🔔 NEW DRIFT {instance_id}/{plugin_name}/{config_file}:{config_key} "
                                f"- Expected: {expected_normalized} (from {scope}), "
                                f"Got: {actual_normalized}"
                            )
                            
                            # Log drift to config_change_history
                            try:
                                self.db.log_config_change(
                                    instance_id=instance_id,
                                    plugin_name=plugin_name,
                                    config_key=f"{config_file}:{config_key}",
                                    old_value=str(expected_normalized),
                                    new_value=str(actual_normalized),
                                    change_type='automated',  # Agent detected
                                    changed_by=f'agent-{self.server_name}',
                                    reason=f'Drift from {scope} expectation detected during scan'
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
                          version_from: str = None, version_to: str = None,
                          jar_file: str = None, jar_hash: str = None):
        """
        Log to plugin_installation_history table
        Note: Would need new db_access.py method - using config_change_history for now
        """
        try:
            self.db.log_config_change(
                instance_id=instance_id,
                plugin_name=plugin_name,
                config_key='plugin_lifecycle',
                old_value=version_from or '',
                new_value=version_to or '',
                change_type='automated',
                changed_by=f'agent-{self.server_name}',
                reason=f'Plugin {action}: {jar_file or plugin_name} (hash: {jar_hash[:8] if jar_hash else "unknown"})'
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
                    f"🔄 Found {len(applicable)} auto-migrations for {plugin_name} "
                    f"{from_version} → {to_version}"
                )
                
                for migration in applicable:
                    if migration['is_breaking']:
                        self.logger.warning(
                            f"⚠️  BREAKING CHANGE: {migration['old_key_path']} → "
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
                config_key=migration['new_key_path'],
                old_value=f"migrated from {migration['old_key_path']}",
                new_value=migration['new_key_path'],
                change_type='automated',
                changed_by=f'agent-{self.server_name}',
                reason=f"Auto-migration: {migration['notes']}"
            )
            self.logger.info(f"✅ Applied migration: {migration['old_key_path']} → {migration['new_key_path']}")
        except Exception as e:
            self.logger.error(f"Failed to apply migration: {e}")
    
    def _log_variance_snapshot(self, instance_id: str, drift_info: List[Dict]):
        """
        Log to config_variance_history for trend analysis
        Would need new db_access.py method
        """
        self.logger.info(f"📊 Variance snapshot: {instance_id} has {len(drift_info)} drift items")
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
        Extract version from plugin jar filename (simplified)
        Real implementation would read plugin.yml from jar
        """
        import re
        name = jar_file.stem
        
        # Common patterns: PluginName-1.2.3.jar, PluginName_v1.2.3.jar
        version_match = re.search(r'[-_]v?(\d+\.\d+(?:\.\d+)?)', name)
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
