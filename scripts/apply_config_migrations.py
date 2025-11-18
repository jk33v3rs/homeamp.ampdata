#!/usr/bin/env python3
"""
Config Migration Applier

Applies config key migrations when updating plugin versions.
Handles key renames, value transformations, and structural changes.

Usage:
    # Dry run (preview only)
    python apply_config_migrations.py --plugin EliteMobs --from-version 8.9.5 --to-version 9.0.0 --instance BENT01 --dry-run
    
    # Apply migrations
    python apply_config_migrations.py --plugin EliteMobs --from-version 8.9.5 --to-version 9.0.0 --instance BENT01
    
    # Apply to all instances
    python apply_config_migrations.py --plugin EliteMobs --from-version 8.9.5 --to-version 9.0.0 --all-instances
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import json
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'software' / 'homeamp-config-manager' / 'src'))

from database.db_access import ConfigDatabase


class ConfigMigrationApplier:
    """Applies config key migrations based on version upgrades"""
    
    def __init__(self, db: ConfigDatabase, utildata_path: Path, dry_run: bool = True):
        """
        Initialize migration applier
        
        Args:
            db: Database connection
            utildata_path: Path to utildata directory
            dry_run: If True, only preview changes
        """
        self.db = db
        self.utildata_path = utildata_path
        self.dry_run = dry_run
        self.applied_count = 0
        self.skipped_count = 0
        self.failed_count = 0
    
    def get_applicable_migrations(self, 
                                 plugin_name: str, 
                                 from_version: str, 
                                 to_version: str) -> List[Dict]:
        """
        Get migrations applicable for version upgrade
        
        Args:
            plugin_name: Plugin name
            from_version: Current version
            to_version: Target version
            
        Returns:
            List of migration dictionaries
        """
        self.db.cursor.execute("""
            SELECT * FROM config_key_migrations
            WHERE plugin_name = %s
            AND (
                (from_version = %s OR from_version = %s)
                OR (to_version = %s OR to_version = %s)
            )
            ORDER BY migration_id
        """, (plugin_name, from_version, from_version.split('.')[0] + '.x', 
              to_version, to_version.split('.')[0] + '.x'))
        
        return self.db.cursor.fetchall()
    
    def apply_migration(self, 
                       config: Dict[str, Any], 
                       migration: Dict,
                       config_file_path: Path) -> tuple[Dict[str, Any], bool]:
        """
        Apply single migration to config dict
        
        Args:
            config: Config dictionary
            migration: Migration definition
            config_file_path: Path to config file
            
        Returns:
            (modified_config, was_applied)
        """
        old_path = migration['old_key_path'].split('.')
        new_path = migration['new_key_path'].split('.')
        
        # Handle wildcard paths (e.g., "enchants.*.id")
        if '*' in old_path:
            return self._apply_wildcard_migration(config, migration, old_path, new_path)
        
        # Get old value
        old_value = self._get_nested_value(config, old_path)
        
        if old_value is None:
            print(f"  ⏭️  Key not found: {migration['old_key_path']} (skipping)")
            self.skipped_count += 1
            return config, False
        
        # Transform value if needed
        new_value = old_value
        if migration['value_transform']:
            try:
                # Safe eval with limited scope
                new_value = eval(
                    migration['value_transform'], 
                    {
                        'x': old_value, 
                        'int': int, 
                        'str': str, 
                        'float': float,
                        'list': list,
                        'isinstance': isinstance
                    }
                )
                print(f"  🔄 Transformed: {old_value} → {new_value}")
            except Exception as e:
                print(f"  ⚠️  Value transform failed: {e}")
                self.failed_count += 1
                return config, False
        
        # Set new value
        config = self._set_nested_value(config, new_path, new_value)
        print(f"  ✅ {migration['old_key_path']} → {migration['new_key_path']} = {new_value}")
        
        # Remove old key if migration type requires it
        if migration['migration_type'] in ['move', 'remove', 'rename']:
            config = self._delete_nested_key(config, old_path)
            print(f"  🗑️  Removed old key: {migration['old_key_path']}")
        
        self.applied_count += 1
        return config, True
    
    def _apply_wildcard_migration(self,
                                  config: Dict[str, Any],
                                  migration: Dict,
                                  old_path: List[str],
                                  new_path: List[str]) -> tuple[Dict[str, Any], bool]:
        """Apply migration with wildcard paths"""
        # Find wildcard position
        wildcard_idx = old_path.index('*')
        prefix = old_path[:wildcard_idx]
        suffix = old_path[wildcard_idx+1:]
        
        # Get container
        container = self._get_nested_value(config, prefix)
        
        if not isinstance(container, dict):
            print(f"  ⏭️  Wildcard container not found or not a dict")
            self.skipped_count += 1
            return config, False
        
        # Apply to each item
        applied = False
        for key in list(container.keys()):
            item_old_path = prefix + [key] + suffix
            item_new_path = new_path[:wildcard_idx] + [key] + new_path[wildcard_idx+1:]
            
            old_value = self._get_nested_value(config, item_old_path)
            if old_value is not None:
                config = self._set_nested_value(config, item_new_path, old_value)
                if migration['migration_type'] in ['move', 'remove', 'rename']:
                    config = self._delete_nested_key(config, item_old_path)
                print(f"  ✅ {'.'.join(item_old_path)} → {'.'.join(item_new_path)}")
                applied = True
        
        if applied:
            self.applied_count += 1
        else:
            self.skipped_count += 1
        
        return config, applied
    
    def _get_nested_value(self, d: Dict, path: List[str]) -> Any:
        """Get value from nested dict using path"""
        current = d
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _set_nested_value(self, d: Dict, path: List[str], value: Any) -> Dict:
        """Set value in nested dict using path"""
        current = d
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value
        return d
    
    def _delete_nested_key(self, d: Dict, path: List[str]) -> Dict:
        """Delete key from nested dict using path"""
        current = d
        for key in path[:-1]:
            if key not in current:
                return d
            current = current[key]
        if path[-1] in current:
            del current[path[-1]]
        return d
    
    def apply_to_instance(self,
                         instance_id: str,
                         plugin_name: str,
                         migrations: List[Dict],
                         config_filename: str = 'config.yml') -> bool:
        """
        Apply migrations to a single instance
        
        Returns:
            True if successful
        """
        # Find config file
        config_path = self.utildata_path / instance_id / plugin_name / config_filename
        
        if not config_path.exists():
            print(f"\n⚠️  Config file not found: {config_path}")
            return False
        
        print(f"\n📂 Processing: {instance_id}/{plugin_name}/{config_filename}")
        
        # Load config
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            print(f"  ❌ Failed to load config: {e}")
            self.failed_count += 1
            return False
        
        if config is None:
            config = {}
        
        # Apply each migration
        original_config = json.dumps(config, sort_keys=True)
        
        for migration in migrations:
            print(f"\n  🔄 Migration: {migration['old_key_path']} → {migration['new_key_path']}")
            if migration['is_breaking']:
                print(f"     ⚠️  BREAKING: {migration['notes']}")
            
            config, applied = self.apply_migration(config, migration, config_path)
        
        # Check if anything changed
        if json.dumps(config, sort_keys=True) == original_config:
            print(f"\n  ℹ️  No changes needed for {instance_id}")
            return True
        
        # Save or preview
        if self.dry_run:
            print(f"\n  📄 DRY RUN - Would save changes to {config_path}")
            print("\n  Preview (first 50 lines):")
            preview = yaml.dump(config, default_flow_style=False)
            for i, line in enumerate(preview.split('\n')[:50], 1):
                print(f"    {i:3d} | {line}")
            if len(preview.split('\n')) > 50:
                print("    ... (truncated)")
        else:
            # Backup original
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = config_path.with_suffix(f'.{timestamp}.backup')
            config_path.rename(backup_path)
            
            # Write new config
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                
                print(f"\n  ✅ Saved to {config_path}")
                print(f"  📦 Backup: {backup_path}")
                
            except Exception as e:
                # Restore backup if save fails
                backup_path.rename(config_path)
                print(f"  ❌ Failed to save: {e}")
                print(f"  🔄 Restored original from backup")
                self.failed_count += 1
                return False
        
        return True


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Apply config key migrations for plugin version upgrades',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migrations for single instance
  python apply_config_migrations.py --plugin EliteMobs --from-version 8.9.5 --to-version 9.0.0 --instance BENT01 --dry-run
  
  # Apply migrations to single instance
  python apply_config_migrations.py --plugin EliteMobs --from-version 8.9.5 --to-version 9.0.0 --instance BENT01
  
  # Apply to all instances
  python apply_config_migrations.py --plugin ExcellentEnchants --from-version 4.x --to-version 5.0.0 --all-instances --dry-run
        """
    )
    
    parser.add_argument('--plugin', required=True, help='Plugin name')
    parser.add_argument('--from-version', required=True, help='Current plugin version')
    parser.add_argument('--to-version', required=True, help='Target plugin version')
    parser.add_argument('--instance', help='Instance ID (e.g., BENT01)')
    parser.add_argument('--all-instances', action='store_true', help='Apply to all instances')
    parser.add_argument('--dry-run', action='store_true', help='Preview only, do not save changes')
    parser.add_argument('--config-file', default='config.yml', help='Config filename (default: config.yml)')
    parser.add_argument('--utildata', default='e:/homeamp.ampdata/utildata', help='Path to utildata directory')
    
    args = parser.parse_args()
    
    if not args.instance and not args.all_instances:
        parser.error("Must specify either --instance or --all-instances")
    
    utildata_path = Path(args.utildata)
    if not utildata_path.exists():
        print(f"❌ Utildata path not found: {utildata_path}")
        sys.exit(1)
    
    # Connect to database
    print("🔌 Connecting to database...")
    db = ConfigDatabase(
        host='135.181.212.169',
        port=3369,
        user='sqlworkerSMP',
        password='2024!SQLdb'
    )
    
    try:
        db.connect()
        print("✅ Connected\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Create applier
    applier = ConfigMigrationApplier(db, utildata_path, dry_run=args.dry_run)
    
    # Get migrations
    print(f"🔍 Finding migrations for {args.plugin} {args.from_version} → {args.to_version}...")
    migrations = applier.get_applicable_migrations(args.plugin, args.from_version, args.to_version)
    
    if not migrations:
        print(f"\nℹ️  No migrations found for {args.plugin} {args.from_version} → {args.to_version}")
        print("This version upgrade may not require config changes.")
        db.disconnect()
        sys.exit(0)
    
    print(f"\n📋 Found {len(migrations)} migration(s):\n")
    for i, mig in enumerate(migrations, 1):
        print(f"{i}. {mig['old_key_path']} → {mig['new_key_path']}")
        print(f"   Type: {mig['migration_type']}")
        if mig['is_breaking']:
            print(f"   ⚠️  BREAKING CHANGE")
        if mig['notes']:
            print(f"   Note: {mig['notes']}")
        print()
    
    # Get instances to process
    if args.all_instances:
        instances = db.get_all_instances()
        instance_ids = [inst['instance_id'] for inst in instances]
        print(f"📦 Applying to {len(instance_ids)} instances")
    else:
        instance_ids = [args.instance]
        print(f"📦 Applying to instance: {args.instance}")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be saved\n")
    
    print("=" * 80)
    
    # Apply to each instance
    success_count = 0
    for instance_id in instance_ids:
        if applier.apply_to_instance(instance_id, args.plugin, migrations, args.config_file):
            success_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Instances processed: {len(instance_ids)}")
    print(f"Successful:          {success_count}")
    print(f"Failed:              {len(instance_ids) - success_count}")
    print(f"Migrations applied:  {applier.applied_count}")
    print(f"Migrations skipped:  {applier.skipped_count}")
    print(f"Migrations failed:   {applier.failed_count}")
    
    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")
    else:
        print("\n✅ Migrations complete")
        print("📦 Backups created with timestamp suffix")
        print("\n⚠️  Remember to restart affected servers for changes to take effect")
    
    db.disconnect()


if __name__ == '__main__':
    main()
