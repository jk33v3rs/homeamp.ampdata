#!/usr/bin/env python3
import mysql.connector

DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_config'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

with open('scripts/seed_instance_groups.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
print(f"Executing {len(statements)} statements...")

for i, stmt in enumerate(statements, 1):
    cursor.execute(stmt)
    try:
        results = cursor.fetchall()
        if results:
            for row in results:
                print(f"  {row}")
    except:
        pass

conn.commit()
print("\n✓ Deployed instance groups\n")

cursor.execute("""
    SELECT group_name, group_type, COUNT(igm.instance_id) AS members
    FROM instance_groups ig
    LEFT JOIN instance_group_members igm ON ig.group_id = igm.group_id
    GROUP BY ig.group_id, group_name, group_type
    ORDER BY group_type, group_name
""")

print("Groups:")
for row in cursor.fetchall():
    print(f"  {row[0]} ({row[1]}): {row[2]} members")

cursor.close()
conn.close()
