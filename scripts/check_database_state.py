#!/usr/bin/env python3
"""
Quick database state check - what tables exist and what data is populated
"""

import mysql.connector
from pathlib import Path

DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_config',
    'autocommit': False
}

def main():
    print("=" * 80)
    print("DATABASE STATE CHECK")
    print("=" * 80)
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    # 1. List all tables
    print("\n1. ALL TABLES IN asmp_config:")
    print("-" * 80)
    cursor.execute("SHOW TABLES")
    tables = [list(row.values())[0] for row in cursor.fetchall()]
    for i, table in enumerate(tables, 1):
        print(f"  {i:2d}. {table}")
    print(f"\nTotal: {len(tables)} tables")
    
    # 2. Core instance data
    print("\n2. INSTANCES:")
    print("-" * 80)
    cursor.execute("SELECT COUNT(*) as count FROM instances")
    count = cursor.fetchone()['count']
    print(f"  Total instances: {count}")
    
    cursor.execute("""
        SELECT instance_id, instance_name, server_name, is_active, is_production 
        FROM instances 
        ORDER BY server_name, instance_id
        LIMIT 15
    """)
    for row in cursor.fetchall():
        status = "PROD" if row['is_production'] else "DEV"
        active = "✓" if row['is_active'] else "✗"
        print(f"  {active} {row['instance_id']:8s} {row['instance_name']:30s} {row['server_name']:15s} [{status}]")
    
    # 3. Check if plugins table exists and has data
    print("\n3. PLUGINS:")
    print("-" * 80)
    if 'plugins' in tables:
        cursor.execute("SELECT COUNT(*) as count FROM plugins")
        count = cursor.fetchone()['count']
        print(f"  Total plugins: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT plugin_id, plugin_name, platform, current_version, has_cicd, cicd_provider
                FROM plugins
                LIMIT 10
            """)
            for row in cursor.fetchall():
                cicd = f"[{row['cicd_provider']}]" if row['has_cicd'] else ""
                print(f"  - {row['plugin_name']:25s} v{row['current_version']:10s} ({row['platform']}) {cicd}")
    else:
        print("  ✗ 'plugins' table does NOT exist")
    
    # 4. Check instance_plugins
    print("\n4. INSTANCE_PLUGINS:")
    print("-" * 80)
    if 'instance_plugins' in tables:
        cursor.execute("SELECT COUNT(*) as count FROM instance_plugins")
        count = cursor.fetchone()['count']
        print(f"  Total instance-plugin mappings: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT ip.instance_id, p.plugin_name, ip.installed_version
                FROM instance_plugins ip
                JOIN plugins p ON ip.plugin_id = p.plugin_id
                LIMIT 10
            """)
            for row in cursor.fetchall():
                print(f"  {row['instance_id']:8s} -> {row['plugin_name']:25s} v{row['installed_version']}")
    else:
        print("  ✗ 'instance_plugins' table does NOT exist")
    
    # 5. Check config_rules (the global config)
    print("\n5. CONFIG_RULES (Global Config Baseline):")
    print("-" * 80)
    if 'config_rules' in tables:
        cursor.execute("SELECT COUNT(*) as count FROM config_rules")
        count = cursor.fetchone()['count']
        print(f"  Total config rules: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT plugin_name, config_key, scope_type, scope_selector, config_value, priority
                FROM config_rules
                ORDER BY priority
                LIMIT 10
            """)
            for row in cursor.fetchall():
                scope = f"{row['scope_type']}"
                if row['scope_selector']:
                    scope += f":{row['scope_selector']}"
                value = row['config_value'][:30] if row['config_value'] else 'NULL'
                print(f"  [{row['priority']}] {row['plugin_name']:20s} {row['config_key']:30s} = {value:30s} ({scope})")
    else:
        print("  ✗ 'config_rules' table does NOT exist")
    
    # 6. Check config_variance_cache
    print("\n6. CONFIG_VARIANCE_CACHE:")
    print("-" * 80)
    if 'config_variance_cache' in tables:
        cursor.execute("SELECT COUNT(*) as count FROM config_variance_cache")
        count = cursor.fetchone()['count']
        print(f"  Total variance entries: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT plugin_name, config_key, variance_type, unique_values, is_expected_variance
                FROM config_variance_cache
                LIMIT 10
            """)
            for row in cursor.fetchall():
                expected = "✓ expected" if row['is_expected_variance'] else "✗ DRIFT"
                print(f"  {row['plugin_name']:20s} {row['config_key']:30s} [{row['variance_type']:10s}] {row['unique_values']} values ({expected})")
    else:
        print("  ✗ 'config_variance_cache' table does NOT exist")
    
    # 7. Check for comprehensive tracking tables
    print("\n7. COMPREHENSIVE TRACKING TABLES (from add_comprehensive_tracking.sql):")
    print("-" * 80)
    comprehensive_tables = [
        'global_config_baseline',
        'instance_config_values',
        'config_variance_detected',
        'plugin_developers',
        'plugin_cicd_builds',
        'plugin_documentation_pages',
        'plugin_version_history'
    ]
    
    for table_name in comprehensive_tables:
        if table_name in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"  ✓ {table_name:35s} ({count} rows)")
        else:
            print(f"  ✗ {table_name:35s} (NOT EXISTS)")
    
    # 8. Check instance groups
    print("\n8. INSTANCE_GROUPS:")
    print("-" * 80)
    if 'instance_groups' in tables:
        cursor.execute("SELECT COUNT(*) as count FROM instance_groups")
        count = cursor.fetchone()['count']
        print(f"  Total groups: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT group_name, group_type, description
                FROM instance_groups
                LIMIT 10
            """)
            for row in cursor.fetchall():
                print(f"  - {row['group_name']:20s} ({row['group_type']:10s}) {row['description']}")
    else:
        print("  ✗ 'instance_groups' table does NOT exist")
    
    # 9. Check meta_tags
    print("\n9. META_TAGS:")
    print("-" * 80)
    if 'meta_tags' in tables:
        cursor.execute("SELECT COUNT(*) as count FROM meta_tags")
        count = cursor.fetchone()['count']
        print(f"  Total meta tags: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT tag_name, description
                FROM meta_tags
                LIMIT 10
            """)
            for row in cursor.fetchall():
                desc = row['description'][:50] if row['description'] else ''
                print(f"  - {row['tag_name']:20s} {desc}")
    else:
        print("  ✗ 'meta_tags' table does NOT exist")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("✓ DATABASE CHECK COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
