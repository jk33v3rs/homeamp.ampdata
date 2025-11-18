#!/usr/bin/env python3
"""
Seed Baseline Configs from Global Config Rules
Deploys placeholder/baseline configs from developer machine to production database.

This script reads the existing config_rules table and ensures all baseline
configurations are properly seeded for all instances.

Usage:
    python3 seed_baseline_configs.py [--dry-run] [--instance BENT01]
"""

import os
import sys
import argparse
import mysql.connector
from datetime import datetime
from typing import List, Dict, Any

# Database connection details
DB_CONFIG = {
    'host': os.getenv('ASMP_DB_HOST', '135.181.212.169'),
    'port': int(os.getenv('ASMP_DB_PORT', '3369')),
    'user': os.getenv('ASMP_DB_USER', 'sqlworkerSMP'),
    'password': os.getenv('ASMP_DB_PASSWORD', '2024!SQLdb'),
    'database': 'asmp_config'
}


class BaselineConfigSeeder:
    """Seeds baseline configs from config_rules to production instances."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.conn = None
        self.cursor = None
        self.stats = {
            'rules_loaded': 0,
            'instances_found': 0,
            'configs_created': 0,
            'configs_updated': 0,
            'configs_skipped': 0,
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
    
    def get_global_config_rules(self) -> List[Dict[str, Any]]:
        """Fetch all GLOBAL scope config rules."""
        query = """
            SELECT rule_id, plugin_name, config_key, config_value, 
                   description, priority, is_active
            FROM config_rules
            WHERE scope_type = 'GLOBAL' AND is_active = 1
            ORDER BY plugin_name, config_key
        """
        self.cursor.execute(query)
        rules = self.cursor.fetchall()
        self.stats['rules_loaded'] = len(rules)
        return rules
    
    def get_all_instances(self, instance_filter: str = None) -> List[Dict[str, Any]]:
        """Fetch all active instances (or specific instance)."""
        if instance_filter:
            query = """
                SELECT instance_id, instance_name, server_id, amp_instance_id
                FROM instances
                WHERE instance_name = %s AND is_active = 1
            """
            self.cursor.execute(query, (instance_filter,))
        else:
            query = """
                SELECT instance_id, instance_name, server_id, amp_instance_id
                FROM instances
                WHERE is_active = 1
                ORDER BY instance_name
            """
            self.cursor.execute(query)
        
        instances = self.cursor.fetchall()
        self.stats['instances_found'] = len(instances)
        return instances
    
    def get_plugin_configs(self, instance_id: int, plugin_name: str) -> List[Dict[str, Any]]:
        """Get existing plugin configs for an instance."""
        query = """
            SELECT config_id, config_key, config_value
            FROM instance_plugin_configs
            WHERE instance_id = %s AND plugin_name = %s
        """
        self.cursor.execute(query, (instance_id, plugin_name))
        return self.cursor.fetchall()
    
    def apply_baseline_to_instance(self, instance: Dict[str, Any], rule: Dict[str, Any]):
        """Apply a single baseline config rule to an instance."""
        instance_id = instance['instance_id']
        instance_name = instance['instance_name']
        plugin_name = rule['plugin_name']
        config_key = rule['config_key']
        config_value = rule['config_value']
        
        # Check if config already exists
        existing_configs = self.get_plugin_configs(instance_id, plugin_name)
        existing = next((c for c in existing_configs if c['config_key'] == config_key), None)
        
        if existing:
            # Config exists - check if value matches
            if existing['config_value'] == config_value:
                print(f"  ⏭️  {instance_name}/{plugin_name}/{config_key}: Already set to '{config_value}'")
                self.stats['configs_skipped'] += 1
            else:
                # Value differs - update if not dry-run
                print(f"  🔄 {instance_name}/{plugin_name}/{config_key}: '{existing['config_value']}' → '{config_value}'")
                if not self.dry_run:
                    update_query = """
                        UPDATE instance_plugin_configs
                        SET config_value = %s, last_updated = NOW()
                        WHERE config_id = %s
                    """
                    self.cursor.execute(update_query, (config_value, existing['config_id']))
                    self.stats['configs_updated'] += 1
                else:
                    self.stats['configs_updated'] += 1
        else:
            # Config doesn't exist - create it
            print(f"  ✨ {instance_name}/{plugin_name}/{config_key}: Creating with '{config_value}'")
            if not self.dry_run:
                insert_query = """
                    INSERT INTO instance_plugin_configs 
                    (instance_id, plugin_name, config_key, config_value, last_updated)
                    VALUES (%s, %s, %s, %s, NOW())
                """
                self.cursor.execute(insert_query, (instance_id, plugin_name, config_key, config_value))
                self.stats['configs_created'] += 1
            else:
                self.stats['configs_created'] += 1
    
    def seed_all_baselines(self, instance_filter: str = None):
        """Seed all baseline configs to all instances."""
        print("\n" + "="*80)
        print("SEEDING BASELINE CONFIGS FROM GLOBAL RULES")
        print("="*80 + "\n")
        
        if self.dry_run:
            print("🔍 DRY-RUN MODE - No changes will be made\n")
        
        # Get global rules
        print("📋 Loading global config rules...")
        rules = self.get_global_config_rules()
        print(f"✅ Loaded {len(rules)} global config rules\n")
        
        if not rules:
            print("⚠️  No global config rules found!")
            return
        
        # Get instances
        print("🎮 Loading instances...")
        instances = self.get_all_instances(instance_filter)
        if instance_filter:
            print(f"✅ Loaded 1 instance: {instance_filter}\n")
        else:
            print(f"✅ Loaded {len(instances)} instances\n")
        
        if not instances:
            print("⚠️  No instances found!")
            return
        
        # Apply each rule to each instance
        print("🚀 Applying baseline configs...\n")
        for rule in rules:
            plugin_name = rule['plugin_name']
            config_key = rule['config_key']
            print(f"📦 {plugin_name}/{config_key}:")
            
            for instance in instances:
                try:
                    self.apply_baseline_to_instance(instance, rule)
                except mysql.connector.Error as e:
                    print(f"  ❌ {instance['instance_name']}: Database error - {e}")
                    self.stats['errors'] += 1
                except Exception as e:
                    print(f"  ❌ {instance['instance_name']}: {e}")
                    self.stats['errors'] += 1
            
            print()  # Blank line between rules
        
        # Commit changes
        if not self.dry_run:
            self.conn.commit()
            print("✅ Changes committed to database\n")
        
        # Print summary
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"  Global Rules Loaded: {self.stats['rules_loaded']}")
        print(f"  Instances Processed: {self.stats['instances_found']}")
        print(f"  Configs Created:     {self.stats['configs_created']}")
        print(f"  Configs Updated:     {self.stats['configs_updated']}")
        print(f"  Configs Skipped:     {self.stats['configs_skipped']}")
        print(f"  Errors:              {self.stats['errors']}")
        print("="*80 + "\n")
        
        if self.dry_run:
            print("ℹ️  This was a dry-run. Re-run without --dry-run to apply changes.\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Seed baseline configs from global rules to production instances',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run to see what would change
  python3 seed_baseline_configs.py --dry-run
  
  # Apply to all instances
  python3 seed_baseline_configs.py
  
  # Apply to single instance
  python3 seed_baseline_configs.py --instance BENT01
  
  # Dry-run for single instance
  python3 seed_baseline_configs.py --dry-run --instance BENT01
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )
    
    parser.add_argument(
        '--instance',
        type=str,
        help='Apply to specific instance only (e.g., BENT01)'
    )
    
    args = parser.parse_args()
    
    # Create seeder and run
    seeder = BaselineConfigSeeder(dry_run=args.dry_run)
    
    try:
        seeder.connect()
        seeder.seed_all_baselines(instance_filter=args.instance)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        seeder.disconnect()


if __name__ == '__main__':
    main()
