#!/usr/bin/env python3
"""
Deploy instances directly to database
"""

import mysql.connector

DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_config'
}

# OVH Instances
ovh_instances = [
    ('CLIP01', 'ClippyCore Enhanced Hardcore', 'ovh-ryzen', '37.187.143.41', 1179, 'paper', '1.21.8', True, True, 'ClippyCore enhanced hardcore mode'),
    ('CSMC01', 'CounterStrike: Minecraft', 'ovh-ryzen', '37.187.143.41', 1180, 'paper', '1.21.8', True, True, 'CounterStrike-style minigame'),
    ('EMAD01', 'EMadventure Server', 'ovh-ryzen', '37.187.143.41', 1181, 'paper', '1.21.8', True, True, 'Adventure-focused gameplay'),
    ('BENT01', 'BentoBox Ecosystem', 'ovh-ryzen', '37.187.143.41', 1182, 'paper', '1.21.8', True, True, 'Skyblock/OneBlock/Worlds suite'),
    ('HCRE01', 'Hardcore Survival', 'ovh-ryzen', '37.187.143.41', 1183, 'paper', '1.21.8', True, True, 'Hardcore survival server'),
    ('SMP201', 'Archive SMP Season 2', 'ovh-ryzen', '37.187.143.41', 1184, 'paper', '1.21.8', True, True, 'Primary SMP server'),
    ('HUB01', 'Network Hub', 'ovh-ryzen', '37.187.143.41', 1185, 'paper', '1.21.8', True, True, 'Central server hub'),
    ('MINT01', 'Minetorio', 'ovh-ryzen', '37.187.143.41', 1186, 'paper', '1.21.8', True, True, 'Factorio-inspired automation'),
    ('CREA01', 'Creative Server', 'ovh-ryzen', '37.187.143.41', 1187, 'paper', '1.21.8', True, True, 'Creative building mode'),
    ('GEY01', 'Geyser Standalone', 'ovh-ryzen', '37.187.143.41', 19132, 'geyser', '1.21.8', True, True, 'Bedrock Edition support'),
    ('VEL01', 'Velocity Proxy', 'ovh-ryzen', '37.187.143.41', 25565, 'velocity', '1.21.8', True, True, 'Network backbone proxy'),
]

# Hetzner Instances
hetzner_instances = [
    ('TOWER01', 'Eternal Tower Defense', 'hetzner-xeon', '135.181.212.169', 2171, 'paper', '1.21.8', True, True, 'Tower defense minigame'),
    ('EVO01', 'Evolution SMP', 'hetzner-xeon', '135.181.212.169', 2172, 'paper', '1.21.8', True, True, 'Modded server development'),
    ('DEV01', 'Development Server', 'hetzner-xeon', '135.181.212.169', 2173, 'paper', '1.21.8', True, False, 'Testing environment'),
    ('MINI01', 'Minigames Server', 'hetzner-xeon', '135.181.212.169', 2174, 'paper', '1.21.8', True, True, 'General minigames'),
    ('BIGG01', 'BiggerGAMES', 'hetzner-xeon', '135.181.212.169', 2175, 'paper', '1.21.8', True, True, 'Extended minigames collection'),
    ('FORT01', 'Battle Royale', 'hetzner-xeon', '135.181.212.169', 2176, 'paper', '1.21.8', True, True, 'Fortnite-style battle royale'),
    ('PRIV01', 'Private Worlds', 'hetzner-xeon', '135.181.212.169', 2177, 'paper', '1.21.8', True, True, 'Private server worlds'),
    ('SMP101', 'Archive SMP Season 1', 'hetzner-xeon', '135.181.212.169', 2178, 'paper', '1.21.8', True, True, 'SMP Season 1 instance'),
]

all_instances = ovh_instances + hetzner_instances

print("Connecting to database...")
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Clear test data
print("Clearing test data...")
cursor.execute("DELETE FROM instances WHERE instance_id = 'TEST01'")

print(f"Inserting {len(all_instances)} instances...")
insert_sql = """
INSERT INTO instances 
(instance_id, instance_name, server_name, server_host, port, platform, minecraft_version, is_active, is_production, description) 
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for instance in all_instances:
    try:
        cursor.execute(insert_sql, instance)
        print(f"  ✓ {instance[0]}")
    except mysql.connector.Error as e:
        print(f"  ✗ {instance[0]}: {e}")

conn.commit()
print(f"\n✓ Inserted {cursor.rowcount} instances")

# Verify
cursor.execute("SELECT COUNT(*) FROM instances")
total = cursor.fetchone()[0]
print(f"Total instances in database: {total}")

cursor.execute("SELECT server_name, COUNT(*) FROM instances GROUP BY server_name")
print("\nBy server:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.close()
conn.close()
