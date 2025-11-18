#!/usr/bin/env python3
"""
Load Global Config Rules from Markdown Baselines
Reads baseline configs from utildata and populates config_rules table.

This script parses markdown baseline files and creates GLOBAL scope config_rules
for each plugin's default configuration.

Usage:
    python3 load_global_rules_from_baselines.py [--dry-run] [--plugin ExcellentEnchants]
"""

import os
import sys
import re
import yaml
import argparse
import mysql.connector
from pathlib import Path
from typing import List, Dict, Any, Optional

# Database connection details
DB_CONFIG = {
    'host': os.getenv('ASMP_DB_HOST', '135.181.212.169'),
    'port': int(os.getenv('ASMP_DB_PORT', '3369')),
    'user': os.getenv('ASMP_DB_USER', 'sqlworkerSMP'),
    'password': os.getenv('ASMP_DB_PASSWORD', '2024!SQLdb'),
    'database': 'asmp_config'
}

# Baseline directory
BASELINE_DIR = Path(r'd:\homeamp.ampdata\homeamp.ampdata\utildata\baselines')


class BaselineConfigLoader:
    """Loads baseline configs from markdown files into config_rules table."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.stats = {
            'files_processed': 0,
            'rules_created': 0,
            'rules_updated': 0,
            'rules_skipped': 0,
            'errors': 0
        }
    
    def connect(self):
        """Connect to database."""
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(dictionary=True)
            print(f"✅ Connected to {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        except mysql.connector.Error as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def parse_baseline_markdown(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a baseline markdown file to extract YAML config.
        
        Expected format:
        ```yaml
        config:
          key: value
        ```
        
        Returns dict with plugin_name and config dict, or None if parsing fails.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract plugin name from filename (e.g., "ExcellentEnchants_config.yml.md")
            plugin_name = file_path.stem.replace('_config.yml', '')
            
            # Find YAML code blocks
            yaml_blocks = re.findall(r'```ya?ml\n(.*?)\n```', content, re.DOTALL)
            
            if not yaml_blocks:
                print(f"  ⚠️  No YAML blocks found in {file_path.name}")
                return None
            
            # Parse first YAML block
            config_data = yaml.safe_load(yaml_blocks[0])
            
            return {
                'plugin_name': plugin_name,
                'config': config_data,
                'file_path': str(file_path)
            }
        
        except Exception as e:
            print(f"  ❌ Error parsing {file_path.name}: {e}")
            self.stats['errors'] += 1
            return None
    
    def flatten_config(self, config: Dict[str, Any], prefix: str = '') -> List[Dict[str, Any]]:
        """
        Flatten nested config dict into list of key-value pairs.
        
        Example:
            {'settings': {'enabled': true, 'level': 5}}
        Becomes:
            [
                {'key': 'settings.enabled', 'value': 'true'},
                {'key': 'settings.level', 'value': '5'}
            ]
        """
        rules = []
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recurse into nested dicts
                rules.extend(self.flatten_config(value, full_key))
            elif isinstance(value, list):
                # Convert lists to YAML string
                rules.append({
                    'key': full_key,
                    'value': yaml.dump(value, default_flow_style=True).strip()
                })
            else:
                # Leaf value
                rules.append({
                    'key': full_key,
                    'value': str(value)
                })
        
        return rules
    
    def get_existing_rule(self, plugin_name: str, config_key: str) -> Optional[Dict[str, Any]]:
        """Check if a rule already exists for this plugin/key."""
        query = """
            SELECT rule_id, config_value, is_active
            FROM config_rules
            WHERE plugin_name = %s 
              AND config_key = %s
              AND scope_type = 'GLOBAL'
        """
        self.cursor.execute(query, (plugin_name, config_key))
        return self.cursor.fetchone()
    
    def create_or_update_rule(self, plugin_name: str, config_key: str, config_value: str):
        """Create or update a global config rule."""
        existing = self.get_existing_rule(plugin_name, config_key)
        
        if existing:
            # Rule exists - check if value changed
            if existing['config_value'] == config_value:
                print(f"    ⏭️  {config_key}: Already set to '{config_value}'")
                self.stats['rules_skipped'] += 1
            else:
                print(f"    🔄 {config_key}: '{existing['config_value']}' → '{config_value}'")
                if not self.dry_run:
                    update_query = """
                        UPDATE config_rules
                        SET config_value = %s, last_updated = NOW()
                        WHERE rule_id = %s
                    """
                    self.cursor.execute(update_query, (config_value, existing['rule_id']))
                self.stats['rules_updated'] += 1
        else:
            # Rule doesn't exist - create it
            print(f"    ✨ {config_key}: Creating with '{config_value}'")
            if not self.dry_run:
                insert_query = """
                    INSERT INTO config_rules
                    (plugin_name, config_key, config_value, scope_type, scope_value, 
                     description, priority, is_active, created_by)
                    VALUES (%s, %s, %s, 'GLOBAL', '', 
                            'Auto-imported from baseline', 50, 1, 'baseline_import')
                """
                self.cursor.execute(insert_query, (plugin_name, config_key, config_value))
            self.stats['rules_created'] += 1
    
    def process_baseline_file(self, file_path: Path):
        """Process a single baseline markdown file."""
        print(f"\n📄 Processing: {file_path.name}")
        
        # Parse markdown
        baseline = self.parse_baseline_markdown(file_path)
        if not baseline:
            return
        
        plugin_name = baseline['plugin_name']
        config = baseline['config']
        
        print(f"  Plugin: {plugin_name}")
        
        # Flatten config to key-value pairs
        flat_rules = self.flatten_config(config)
        print(f"  Found {len(flat_rules)} config keys")
        
        # Create/update each rule
        for rule in flat_rules:
            try:
                self.create_or_update_rule(plugin_name, rule['key'], rule['value'])
            except Exception as e:
                print(f"    ❌ Error creating rule {rule['key']}: {e}")
                self.stats['errors'] += 1
        
        self.stats['files_processed'] += 1
    
    def load_all_baselines(self, plugin_filter: Optional[str] = None):
        """Load all baseline configs from utildata."""
        print("\n" + "="*80)
        print("LOADING BASELINE CONFIGS TO GLOBAL RULES")
        print("="*80 + "\n")
        
        if self.dry_run:
            print("🔍 DRY-RUN MODE - No changes will be made\n")
        
        # Find baseline files
        if not BASELINE_DIR.exists():
            print(f"❌ Baseline directory not found: {BASELINE_DIR}")
            return
        
        pattern = f"{plugin_filter}_*.md" if plugin_filter else "*_config.yml.md"
        baseline_files = list(BASELINE_DIR.glob(pattern))
        
        if not baseline_files:
            print(f"⚠️  No baseline files found matching: {pattern}")
            return
        
        print(f"📂 Found {len(baseline_files)} baseline files in {BASELINE_DIR}\n")
        
        # Process each file
        for file_path in sorted(baseline_files):
            self.process_baseline_file(file_path)
        
        # Commit changes
        if not self.dry_run:
            self.conn.commit()
            print("\n✅ Changes committed to database")
        
        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Files Processed:  {self.stats['files_processed']}")
        print(f"  Rules Created:    {self.stats['rules_created']}")
        print(f"  Rules Updated:    {self.stats['rules_updated']}")
        print(f"  Rules Skipped:    {self.stats['rules_skipped']}")
        print(f"  Errors:           {self.stats['errors']}")
        print("="*80 + "\n")
        
        if self.dry_run:
            print("ℹ️  This was a dry-run. Re-run without --dry-run to apply changes.\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Load baseline configs from markdown files into config_rules table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run to see what would be imported
  python3 load_global_rules_from_baselines.py --dry-run
  
  # Import all baselines
  python3 load_global_rules_from_baselines.py
  
  # Import single plugin
  python3 load_global_rules_from_baselines.py --plugin ExcellentEnchants
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )
    
    parser.add_argument(
        '--plugin',
        type=str,
        help='Process specific plugin only (e.g., ExcellentEnchants)'
    )
    
    args = parser.parse_args()
    
    # Create loader and run
    loader = BaselineConfigLoader(dry_run=args.dry_run)
    
    try:
        loader.connect()
        loader.load_all_baselines(plugin_filter=args.plugin)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        loader.disconnect()


if __name__ == '__main__':
    main()
