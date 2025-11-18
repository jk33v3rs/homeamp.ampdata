#!/usr/bin/env python3
"""
Populate known config key migrations from plugin analysis

This script adds documented breaking changes and version migrations
to the config_key_migrations table.

Based on findings from:
- PLUGIN_ANALYSIS_NOTES.md
- WIP_PLAN/PLUGIN_ANALYSIS_NOTES.md
- Various documentation files
"""

import mysql.connector
import sys
from datetime import datetime

# Database credentials
DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': '2024!SQLdb',
    'database': 'asmp_config'
}

# Known migrations from plugin analysis
KNOWN_MIGRATIONS = [
    {
        'plugin_name': 'ExcellentEnchants',
        'old_key_path': 'enchants.*.id',
        'new_key_path': 'enchantments.*.identifier',
        'from_version': '4.x',
        'to_version': '5.0.0',
        'migration_type': 'rename',
        'value_transform': None,
        'is_breaking': True,
        'is_automatic': False,  # Too risky - requires NBT data migration
        'notes': 'Enchant ID system changed in 5.0.0. Causes "Unknown Enchantment" errors on existing items. Requires NBT data migration for player items.',
        'documentation_url': 'https://github.com/nulli0n/ExcellentEnchants-spigot/wiki/Migration-Guide'
    },
    {
        'plugin_name': 'BentoBox',
        'old_key_path': 'challenges.*.challenge_id',
        'new_key_path': 'challenges.*.identifier',
        'from_version': '1.x',
        'to_version': '2.0.0',
        'migration_type': 'rename',
        'value_transform': None,
        'is_breaking': True,
        'is_automatic': False,  # Requires database migration
        'notes': 'Challenge ID format changed. Player progress lost if not migrated properly. Requires database update.',
        'documentation_url': None
    },
    {
        'plugin_name': 'HandsOffMyBook',
        'old_key_path': 'hotmb.protect',
        'new_key_path': 'handsoffmybook.protect',
        'from_version': '1.x',
        'to_version': '2.0.0',
        'migration_type': 'rename',
        'value_transform': None,
        'is_breaking': True,
        'is_automatic': True,  # Simple config rename
        'notes': 'Permission node format changed from hotmb.* to handsoffmybook.*',
        'documentation_url': None
    },
    {
        'plugin_name': 'ResurrectionChest',
        'old_key_path': 'expiry.timer',
        'new_key_path': 'expiry.duration_seconds',
        'from_version': '1.x',
        'to_version': '2.0.0',
        'migration_type': 'type_change',
        'value_transform': 'int(x) * 60',  # Convert minutes to seconds
        'is_breaking': True,
        'is_automatic': True,
        'notes': 'Timer format changed from minutes to seconds. Old configs will expire 60x faster without migration.',
        'documentation_url': None
    },
    {
        'plugin_name': 'JobListings',
        'old_key_path': 'storage.type',
        'new_key_path': 'database.enabled',
        'from_version': '1.x',
        'to_version': '2.0.0',
        'migration_type': 'remove',
        'value_transform': 'x == "file" -> False, x == "database" -> True',
        'is_breaking': True,
        'is_automatic': False,  # Requires data migration
        'notes': 'Storage migrated from config files to database. Old file-based jobs need manual import.',
        'documentation_url': None
    },
    {
        'plugin_name': 'LevelledMobs',
        'old_key_path': 'spawn-conditions.*.world',
        'new_key_path': 'spawn-conditions.*.worlds',
        'from_version': '3.x',
        'to_version': '4.0.0',
        'migration_type': 'rename',
        'value_transform': '[x] if isinstance(x, str) else x',  # String to list
        'is_breaking': False,
        'is_automatic': True,
        'notes': 'Single world string changed to list of worlds. Backward compatible but should migrate.',
        'documentation_url': None
    },
    {
        'plugin_name': 'EliteMobs',
        'old_key_path': 'ranks.*.min_level',
        'new_key_path': 'ranks.*.minimum_level',
        'from_version': '8.x',
        'to_version': '9.0.0',
        'migration_type': 'rename',
        'value_transform': None,
        'is_breaking': False,
        'is_automatic': True,
        'notes': 'Cosmetic key rename for consistency. Old key still works but deprecated.',
        'documentation_url': 'https://github.com/MagmaGuy/EliteMobs/wiki/Config-Migration'
    },
    {
        'plugin_name': 'Pl3xMap',
        'old_key_path': 'settings.zoom.default',
        'new_key_path': 'settings.default-zoom',
        'from_version': '1.x',
        'to_version': '2.0.0',
        'migration_type': 'move',
        'value_transform': None,
        'is_breaking': False,
        'is_automatic': True,
        'notes': 'Config restructuring for better organization. Old structure deprecated.',
        'documentation_url': 'https://github.com/pl3xgaming/Pl3xMap/wiki/Configuration'
    },
    {
        'plugin_name': 'SimpleVoiceChat',
        'old_key_path': 'port',
        'new_key_path': 'voice_chat.port',
        'from_version': '1.x',
        'to_version': '2.0.0',
        'migration_type': 'move',
        'value_transform': None,
        'is_breaking': True,
        'is_automatic': True,
        'notes': 'Port config moved to nested structure. Voice chat will fail to bind without migration.',
        'documentation_url': 'https://github.com/henkelmax/simple-voice-chat/wiki/Config-Migration'
    },
    {
        'plugin_name': 'DiscordSRV',
        'old_key_path': 'Experiment_WebhookChatMessageDelivery',
        'new_key_path': 'UseWebhooksForChat',
        'from_version': '1.x',
        'to_version': '2.0.0',
        'migration_type': 'rename',
        'value_transform': None,
        'is_breaking': False,
        'is_automatic': True,
        'notes': 'Experimental feature graduated to stable. Old key still works.',
        'documentation_url': None
    }
]


def populate_migrations():
    """Insert known migrations into database"""
    print("=" * 80)
    print("POPULATING KNOWN MIGRATIONS")
    print("=" * 80)
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print(f"\n✅ Connected to {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"\n📋 Inserting {len(KNOWN_MIGRATIONS)} migrations...\n")
        
        inserted = 0
        skipped = 0
        
        for mig in KNOWN_MIGRATIONS:
            try:
                cursor.execute("""
                    INSERT INTO config_key_migrations 
                    (plugin_name, old_key_path, new_key_path, from_version, to_version,
                     migration_type, value_transform, is_breaking, is_automatic, notes,
                     documentation_url, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    mig['plugin_name'],
                    mig['old_key_path'],
                    mig['new_key_path'],
                    mig['from_version'],
                    mig['to_version'],
                    mig['migration_type'],
                    mig['value_transform'],
                    mig['is_breaking'],
                    mig['is_automatic'],
                    mig['notes'],
                    mig['documentation_url'],
                    'initial_population'
                ))
                
                print(f"  ✅ {mig['plugin_name']}: {mig['old_key_path']} → {mig['new_key_path']}")
                if mig['is_breaking']:
                    print(f"     ⚠️  BREAKING CHANGE")
                
                inserted += 1
                
            except mysql.connector.IntegrityError as e:
                if 'Duplicate entry' in str(e):
                    print(f"  ⏭️  {mig['plugin_name']}: Already exists (skipped)")
                    skipped += 1
                else:
                    print(f"  ❌ {mig['plugin_name']}: Error - {e}")
        
        conn.commit()
        
        print("\n" + "=" * 80)
        print(f"✅ Inserted: {inserted}")
        print(f"⏭️  Skipped:  {skipped}")
        print(f"📊 Total:    {inserted + skipped}")
        print("=" * 80)
        
        # Show summary
        cursor.execute("""
            SELECT 
                migration_type,
                COUNT(*) as count,
                SUM(is_breaking) as breaking_count
            FROM config_key_migrations
            GROUP BY migration_type
            ORDER BY count DESC
        """)
        
        results = cursor.fetchall()
        
        if results:
            print("\n📈 MIGRATION SUMMARY BY TYPE:")
            print(f"\n{'Type':<15} {'Total':>8} {'Breaking':>10}")
            print("-" * 40)
            
            for row in results:
                print(f"{row[0]:<15} {row[1]:>8} {row[2]:>10}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"\n❌ Database error: {e}")
        return False


def main():
    """Main execution"""
    print("\n🚀 Starting migration population...\n")
    
    if not populate_migrations():
        print("\n❌ Population failed")
        sys.exit(1)
    
    print("\n✅ Migration data populated successfully")
    print("\nYou can now query migrations with:")
    print("  curl http://135.181.212.169:8000/api/migrations/ExcellentEnchants")
    print()


if __name__ == '__main__':
    main()
