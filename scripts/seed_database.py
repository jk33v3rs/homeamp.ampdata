#!/usr/bin/env python3
"""
Seed Initial Data to asmp_config Database
Populates meta tags, instances, groups, and parses baseline configs
"""

import mysql.connector
from pathlib import Path
import sys

DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_config',
    'autocommit': False
}

def execute_sql_file(cursor, filepath):
    """Execute SQL file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Split by semicolons and execute
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
    print(f"  Executing {len(statements)} statements...")
    
    for i, statement in enumerate(statements, 1):
        try:
            cursor.execute(statement)
            # Try to fetch results
            try:
                results = cursor.fetchall()
                if results:
                    for row in results:
                        print(f"  {row}")
            except:
                pass
        except mysql.connector.Error as e:
            if "Duplicate entry" not in str(e):
                print(f"  ✗ Error on statement {i}: {e}")
                print(f"  Statement: {statement[:200]}")
                raise

def main():
    print("=" * 80)
    print("Seeding Initial Data")
    print("=" * 80)
    
    # Connect
    print("\nConnecting to asmp_config...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("  ✓ Connected")
    except mysql.connector.Error as e:
        print(f"  ✗ Failed: {e}")
        return 1
    
    # Execute seed files
    SEED_FILES = [
        'seed_meta_tags.sql',
        'seed_instances.sql',
        'seed_instance_groups.sql',
        # Add more seed files here as needed
    ]
    
    scripts_dir = Path(__file__).parent
    
    for seed_file in SEED_FILES:
        filepath = scripts_dir / seed_file
        if not filepath.exists():
            print(f"\n✗ File not found: {filepath}")
            continue
            
        print(f"\nExecuting {seed_file}...")
        execute_sql_file(cursor, filepath)
        conn.commit()
        print(f"  ✓ Complete")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ SEEDING COMPLETE")
    print("=" * 80)
    return 0

if __name__ == '__main__':
    sys.exit(main())
