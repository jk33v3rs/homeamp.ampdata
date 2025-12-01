#!/usr/bin/env python3
"""Deploy instance groups directly"""
import mysql.connector

DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_config'
}

groups = [
    # Physical
    ('hetzner-cluster', 'physical', 'All instances on Hetzner Xeon server'),
    ('ovh-cluster', 'physical', 'All instances on OVH Ryzen server'),
    # Logical
    ('survival-servers', 'logical', 'Survival gameplay mode servers'),
    ('creative-servers', 'logical', 'Creative building mode servers'),
    ('minigame-servers', 'logical', 'Minigame and event servers'),
    ('utility-servers', 'logical', 'Hub, proxy, and infrastructure servers'),
    # Administrative
    ('production', 'administrative', 'Live production servers'),
    ('development', 'administrative', 'Development and testing servers'),
]

members = {
    'hetzner-cluster': ['TOWER01', 'EVO01', 'DEV01', 'MINI01', 'BIGG01', 'FORT01', 'PRIV01', 'SMP101'],
    'ovh-cluster': ['CLIP01', 'CSMC01', 'EMAD01', 'BENT01', 'HCRE01', 'SMP201', 'HUB01', 'MINT01', 'CREA01', 'GEY01', 'VEL01'],
    'survival-servers': ['SMP101', 'SMP201', 'CLIP01', 'HCRE01', 'EMAD01', 'BENT01', 'EVO01'],
    'creative-servers': ['CREA01', 'PRIV01'],
    'minigame-servers': ['MINI01', 'BIGG01', 'FORT01', 'TOWER01', 'CSMC01', 'MINT01'],
    'utility-servers': ['HUB01', 'VEL01', 'GEY01'],
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

print("Creating groups...")
for group in groups:
    cursor.execute(
        "INSERT INTO instance_groups (group_name, group_type, description) VALUES (%s, %s, %s)",
        group
    )
    print(f"  ✓ {group[0]}")

# Get production/development members from instances table
cursor.execute("SELECT instance_id FROM instances WHERE is_production = true")
members['production'] = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT instance_id FROM instances WHERE is_production = false")
members['development'] = [row[0] for row in cursor.fetchall()]

print("\nAdding members...")
for group_name, instance_ids in members.items():
    cursor.execute("SELECT group_id FROM instance_groups WHERE group_name = %s", (group_name,))
    group_id = cursor.fetchone()[0]
    
    for instance_id in instance_ids:
        cursor.execute(
            "INSERT INTO instance_group_members (group_id, instance_id) VALUES (%s, %s)",
            (group_id, instance_id)
        )
    print(f"  ✓ {group_name}: {len(instance_ids)} members")

conn.commit()

print("\n" + "="*60)
cursor.execute("""
    SELECT group_name, group_type, COUNT(igm.instance_id) AS members
    FROM instance_groups ig
    LEFT JOIN instance_group_members igm ON ig.group_id = igm.group_id
    GROUP BY ig.group_id, group_name, group_type
    ORDER BY group_type, group_name
""")

print("Instance Groups:")
for row in cursor.fetchall():
    print(f"  {row[0]:20} ({row[1]:15}): {row[2]:2} members")

cursor.close()
conn.close()
