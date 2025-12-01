#!/usr/bin/env python3
"""
Config Enforcement Agent

Applies config rule changes to live instances.
Creates backups before modification and supports rollback.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import yaml
import json
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_access import ConfigDatabase
from core.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigEnforcer:
    """Enforces config rules on live instances"""
    
    def __init__(self, db: ConfigDatabase, amp_base_dir: Path, backup_dir: Path):
        self.db = db
        self.amp_base_dir = amp_base_dir
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def enforce_instance(self, instance_id: str, auto_apply: bool = False):
        """
        Enforce all rules for an instance
        
        Args:
            instance_id: Instance to enforce
            auto_apply: If False, only report what would change (dry run)
        """
        logger.info(f"Enforcing rules for {instance_id} (dry_run={not auto_apply})")
        
        # Get instance details
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM instances WHERE instance_id = %s", (instance_id,))
        instance = cursor.fetchone()
        
        if not instance:
            logger.error(f"Instance {instance_id} not found")
            return
        
        server_name = instance['server_name']
        instance_path = Path(self.amp_base_dir) / instance_id
        
        if not instance_path.exists():
            logger.error(f"Instance path not found: {instance_path}")
            return
        
        # Get all drift entries for this instance
        cursor.execute("""
            SELECT * FROM config_variance_cache
            WHERE instance_id = %s AND is_drift = TRUE
        """, (instance_id,))
        
        drifts = cursor.fetchall()
        
        if not drifts:
            logger.info(f"No drift detected for {instance_id}")
            return
        
        logger.info(f"Found {len(drifts)} drift entries to fix")
        
        # Group by config file
        files_to_fix = {}
        for drift in drifts:
            config_type = drift['config_type']
            plugin_name = drift['plugin_name']
            config_file = drift['config_file']
            
            key = (config_type, plugin_name, config_file)
            if key not in files_to_fix:
                files_to_fix[key] = []
            
            files_to_fix[key].append(drift)
        
        # Create backup if applying changes
        if auto_apply:
            backup_id = self._create_backup(instance_id, instance_path, files_to_fix.keys())
            logger.info(f"Created backup: {backup_id}")
        
        # Apply fixes
        for (config_type, plugin_name, config_file), drift_entries in files_to_fix.items():
            try:
                self._fix_config_file(
                    instance_path, config_type, plugin_name, config_file,
                    drift_entries, auto_apply
                )
            except Exception as e:
                logger.error(f"Failed to fix {config_file}: {e}", exc_info=True)
                if auto_apply:
                    logger.error("Rolling back changes...")
                    self._rollback(backup_id, instance_path)
                    return
        
        if auto_apply:
            logger.info(f"Successfully enforced rules for {instance_id}")
            
            # Mark drift as resolved
            for drift in drifts:
                cursor.execute("""
                    UPDATE config_variance_cache
                    SET is_drift = FALSE,
                        actual_value = expected_value,
                        last_scanned = %s
                    WHERE cache_id = %s
                """, (datetime.now(), drift['cache_id']))
                
                # Update drift log
                cursor.execute("""
                    UPDATE config_drift_log
                    SET status = 'RESOLVED',
                        resolved_at = %s
                    WHERE instance_id = %s
                      AND config_type = %s
                      AND plugin_name <=> %s
                      AND config_file <=> %s
                      AND config_key <=> %s
                      AND status = 'PENDING'
                """, (datetime.now(), instance_id, drift['config_type'],
                      drift['plugin_name'], drift['config_file'], drift['config_key']))
            
            self.db.conn.commit()
    
    def _create_backup(self, instance_id: str, instance_path: Path, files_to_backup):
        """Create backup of config files"""
        backup_id = f"{instance_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        for config_type, plugin_name, config_file in files_to_backup:
            if config_type == 'plugin':
                source = instance_path / 'Minecraft' / 'plugins' / plugin_name / config_file
            elif config_type == 'standard':
                source = instance_path / 'Minecraft' / config_file
            elif config_type == 'datapack':
                # Datapacks are folders/zips
                source = instance_path / 'Minecraft' / 'world' / 'datapacks' / plugin_name
            
            if source.exists():
                dest = backup_path / config_type / (plugin_name or 'standard') / config_file
                dest.parent.mkdir(parents=True, exist_ok=True)
                
                if source.is_dir():
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
                
                logger.info(f"Backed up: {source.relative_to(instance_path)}")
        
        # Save backup manifest
        manifest = {
            'backup_id': backup_id,
            'instance_id': instance_id,
            'created_at': datetime.now().isoformat(),
            'files': [f"{ct}/{pn}/{cf}" for ct, pn, cf in files_to_backup]
        }
        
        with open(backup_path / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return backup_id
    
    def _rollback(self, backup_id: str, instance_path: Path):
        """Rollback to backup"""
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_id}")
            return
        
        # Read manifest
        with open(backup_path / 'manifest.json', 'r') as f:
            manifest = json.load(f)
        
        # Restore files
        for file_spec in manifest['files']:
            parts = file_spec.split('/')
            config_type = parts[0]
            plugin_name = parts[1] if parts[1] != 'standard' else None
            config_file = parts[2]
            
            source = backup_path / file_spec
            
            if config_type == 'plugin':
                dest = instance_path / 'Minecraft' / 'plugins' / plugin_name / config_file
            elif config_type == 'standard':
                dest = instance_path / 'Minecraft' / config_file
            
            if source.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.rmtree(dest, ignore_errors=True)
                    shutil.copytree(source, dest)
                else:
                    shutil.copy2(source, dest)
                
                logger.info(f"Restored: {dest.relative_to(instance_path)}")
        
        logger.info(f"Rollback complete: {backup_id}")
    
    def _fix_config_file(self, instance_path: Path, config_type: str, plugin_name: str,
                         config_file: str, drift_entries: list, auto_apply: bool):
        """Fix drift in a single config file"""
        
        # Determine file path
        if config_type == 'plugin':
            file_path = instance_path / 'Minecraft' / 'plugins' / plugin_name / config_file
        elif config_type == 'standard':
            file_path = instance_path / 'Minecraft' / config_file
        elif config_type == 'datapack':
            # Datapacks are presence-based, not value-based
            logger.info(f"Skipping datapack enforcement: {plugin_name}")
            return
        
        if not file_path.exists():
            logger.warning(f"Config file not found: {file_path}")
            return
        
        # Read current config
        if file_path.suffix == '.properties':
            config_data = self._read_properties(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        
        if not config_data:
            config_data = {}
        
        # Apply fixes
        changes_made = []
        for drift in drift_entries:
            config_key = drift['config_key']
            expected_value = drift['expected_value']
            actual_value = drift['actual_value']
            
            # Parse expected value to correct type
            expected_parsed = self._parse_value(expected_value, drift['value_type'])
            
            # Apply change
            if auto_apply:
                self._set_nested_key(config_data, config_key, expected_parsed)
                changes_made.append(f"{config_key}: {actual_value} -> {expected_value}")
            else:
                logger.info(f"WOULD FIX: {config_key}: {actual_value} -> {expected_value}")
        
        # Write config if changes applied
        if auto_apply and changes_made:
            if file_path.suffix == '.properties':
                self._write_properties(file_path, config_data)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Applied {len(changes_made)} fixes to {file_path.name}")
            for change in changes_made:
                logger.info(f"  - {change}")
    
    def _read_properties(self, file_path: Path) -> dict:
        """Read .properties file"""
        config = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    
    def _write_properties(self, file_path: Path, config: dict):
        """Write .properties file"""
        lines = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#') and '=' in stripped:
                    key = stripped.split('=', 1)[0].strip()
                    if key in config:
                        lines.append(f"{key}={config[key]}\n")
                        del config[key]
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
        
        # Add any new keys
        for key, value in config.items():
            lines.append(f"{key}={value}\n")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def _set_nested_key(self, config: dict, key_path: str, value):
        """Set nested key in config dict (e.g., 'parent.child.key')"""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _parse_value(self, value_str: str, value_type: str):
        """Parse string value to correct type"""
        if value_type == 'boolean':
            return value_str.lower() in ('true', '1', 'yes')
        elif value_type == 'integer':
            return int(value_str)
        elif value_type == 'float':
            return float(value_str)
        elif value_type == 'null':
            return None
        elif value_type == 'list':
            try:
                return json.loads(value_str)
            except:
                return value_str.split(',')
        else:
            return value_str


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Config enforcement agent')
    parser.add_argument('instance_id', help='Instance ID to enforce')
    parser.add_argument('--apply', action='store_true',
                       help='Apply changes (default: dry run)')
    parser.add_argument('--amp-dir', default='/home/amp/.ampdata/instances',
                       help='AMP instances directory')
    parser.add_argument('--backup-dir', default='/var/lib/archivesmp/backups',
                       help='Backup directory')
    
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
        enforcer = ConfigEnforcer(db, Path(args.amp_dir), Path(args.backup_dir))
        enforcer.enforce_instance(args.instance_id, auto_apply=args.apply)
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
