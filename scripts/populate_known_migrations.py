#!/usr/bin/env python3
"""Populate known config key migrations from plugin analysis"""

import mariadb
from datetime import datetime

# Connect to database
conn = mariadb.connect(
    host='135.181.212.169',
    port=3369,
    user='sqlworkerSMP',
    password='2024!SQLdb',
    database='asmp_config'
)
cursor = conn.cursor()

# Known migrations from plugin analysis
migrations = [
    {
        'plugin_name': 'ExcellentEnchants',
        'old_key_path': 'enchants.elite_damage.id',
        'new_key_path': 'enchantments.elite_damage.identifier',
        'from_version': '4.x',
        'to_version': '5.0.0',
        'migration_type': 'rename',
        'is_breaking': True,
        'notes': 'Enchant ID system changed in 5.0.0, causes "Unknown Enchantment" errors on items'
    },
    {
        'plugin_name': 'BentoBox',
        'old_key_path': 'challenges.challenge_id',
        'new_key_path': 'challenges.identifier',
        'from_version': '1.x',
        'to_version': '2.x',
        'migration_type': 'rename',
        'is_breaking': True,
        'notes': 'Challenge ID changes cause player progress loss'
    },
    {
        'plugin_name': 'HandsOffMyBook',
        'old_key_path': 'hotmb.protect',
        'new_key_path': 'handsoffmybook.protect',
        'from_version': '1.x',
        'to_version': '2.x',
        'migration_type': 'rename',
        'is_breaking': True,
        'notes': 'Permission node format changed'
    },
    {
        'plugin_name': 'ResurrectionChest',
        'old_key_path': 'expiry.timer',
        'new_key_path': 'expiry.duration_seconds',
        'from_version': '1.x',
        'to_version': '2.x',
        'migration_type': 'type_change',
        'value_transform': 'int(x) * 60',  # Convert minutes to seconds
        'is_breaking': True,
        'notes': 'Timer format changed from minutes to seconds'
    },
    {
        'plugin_name': 'JobListings',
        'old_key_path': 'storage.type',
        'new_key_path': 'database.enabled',
        'from_version': '1.x',
        'to_version': '2.x',
        'migration_type': 'remove',
        'is_breaking': True,
        'notes': 'Storage migrated from config files to database'
    }
]

for mig in migrations:
    cursor.execute("""
        INSERT INTO config_key_migrations 
        (plugin_name, old_key_path, new_key_path, from_version, to_version, 
         migration_type, value_transform, is_breaking, notes, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        mig['plugin_name'],
        mig['old_key_path'],
        mig['new_key_path'],
        mig['from_version'],
        mig['to_version'],
        mig['migration_type'],
        mig.get('value_transform'),
        mig['is_breaking'],
        mig['notes'],
        'initial_population'
    ))

conn.commit()
print(f"[OK] Inserted {len(migrations)} known migrations")

# Verify
cursor.execute("SELECT COUNT(*) FROM config_key_migrations")
count = cursor.fetchone()[0]
print(f"[OK] Total migrations in database: {count}")

conn.close()
