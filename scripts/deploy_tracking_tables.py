#!/usr/bin/env python3
"""
Deploy tracking and history tables to production database

This script:
1. Connects to production MariaDB
2. Executes add_tracking_history_tables.sql
3. Verifies all 11 tables were created
4. Shows table sizes and row counts
"""

import mariadb
import sys
from pathlib import Path

# Database credentials
DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': '2024!SQLdb',
    'database': 'asmp_config'
}

EXPECTED_TABLES = [
    'config_key_migrations',
    'config_change_history',
    'deployment_history',
    'deployment_changes',
    'config_rule_history',
    'config_variance_history',
    'plugin_installation_history',
    'change_approval_requests',
    'notification_log',
    'scheduled_tasks',
    'system_health_metrics'
]


def deploy_sql():
    """Execute the SQL file"""
    print("=" * 80)
    print("DEPLOYING TRACKING & HISTORY TABLES")
    print("=" * 80)
    
    sql_file = Path(__file__).parent / 'add_tracking_history_tables.sql'
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    print(f"\n📄 Reading SQL from: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Connect to database
    print(f"\n🔌 Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✅ Connected successfully")
        
        # Execute SQL (split by semicolons)
        print("\n⚙️  Executing SQL statements...")
        
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements, 1):
            if statement.upper().startswith('USE'):
                continue  # Skip USE statements, we're already connected to the database
            
            try:
                cursor.execute(statement)
                if statement.upper().startswith('CREATE TABLE'):
                    table_name = statement.split('IF NOT EXISTS')[1].strip().split('(')[0].strip()
                    print(f"  ✅ Created table: {table_name}")
            except mariadb.Error as e:
                if 'already exists' in str(e):
                    print(f"  ℹ️  Table already exists (skipped)")
                else:
                    print(f"  ⚠️  Warning: {e}")
        
        conn.commit()
        print(f"\n✅ Executed {len(statements)} SQL statements")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mariadb.Error as e:
        print(f"❌ Database error: {e}")
        return False


def verify_tables():
    """Verify all tables were created"""
    print("\n" + "=" * 80)
    print("VERIFYING TABLES")
    print("=" * 80)
    
    try:
        conn = mariadb.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Check each expected table
        print("\n📋 Checking for expected tables...")
        
        all_found = True
        
        for table in EXPECTED_TABLES:
            cursor.execute(f"""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = 'asmp_config' 
                AND table_name = '{table}'
            """)
            result = cursor.fetchone()
            
            if result['count'] > 0:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - NOT FOUND")
                all_found = False
        
        if all_found:
            print(f"\n✅ All {len(EXPECTED_TABLES)} tables found!")
        else:
            print(f"\n⚠️  Some tables are missing")
            cursor.close()
            conn.close()
            return False
        
        # Get table statistics
        print("\n" + "=" * 80)
        print("TABLE STATISTICS")
        print("=" * 80)
        
        cursor.execute("""
            SELECT 
                table_name,
                table_rows,
                ROUND(data_length/1024/1024, 2) AS size_mb,
                ROUND(index_length/1024/1024, 2) AS index_mb
            FROM information_schema.tables
            WHERE table_schema = 'asmp_config'
            AND table_name IN (%s)
            ORDER BY table_name
        """ % ','.join([f"'{t}'" for t in EXPECTED_TABLES]))
        
        results = cursor.fetchall()
        
        print(f"\n{'Table Name':<35} {'Rows':>8} {'Data MB':>10} {'Index MB':>10}")
        print("-" * 80)
        
        total_rows = 0
        total_data = 0.0
        total_index = 0.0
        
        for row in results:
            print(f"{row['table_name']:<35} {row['table_rows']:>8} {row['size_mb']:>10.2f} {row['index_mb']:>10.2f}")
            total_rows += row['table_rows']
            total_data += row['size_mb']
            total_index += row['index_mb']
        
        print("-" * 80)
        print(f"{'TOTAL':<35} {total_rows:>8} {total_data:>10.2f} {total_index:>10.2f}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mariadb.Error as e:
        print(f"❌ Database error: {e}")
        return False


def main():
    """Main execution"""
    print("\n🚀 Starting deployment...\n")
    
    # Deploy SQL
    if not deploy_sql():
        print("\n❌ Deployment failed")
        sys.exit(1)
    
    # Verify tables
    if not verify_tables():
        print("\n⚠️  Verification failed")
        sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ DEPLOYMENT COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Run: python scripts/populate_known_migrations.py")
    print("2. Update config_updater.py to use database logging")
    print("3. Add history API endpoints to api.py")
    print("4. Test with: curl http://135.181.212.169:8000/api/history/changes")
    print()


if __name__ == '__main__':
    main()
