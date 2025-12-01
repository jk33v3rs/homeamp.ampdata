#!/usr/bin/env python3
"""
Deploy Database Schema to MariaDB
Executes create_database_schema.sql on remote MariaDB server
"""

import mysql.connector
from pathlib import Path
import sys

# Database connection config
DB_CONFIG = {
    'host': '135.181.212.169',  # Direct connection (requires remote access grant)
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_SQL',  # Connect to existing DB first
    'allow_local_infile': True,
    'autocommit': False
}

def read_sql_file(filepath):
    """Read SQL file and return content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_script(cursor, sql_content):
    """Execute SQL script with multiple statements"""
    # Split by delimiter changes and regular statements
    statements = []
    current_stmt = []
    delimiter = ';'
    in_delimiter_block = False
    
    for line in sql_content.split('\n'):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('--'):
            continue
            
        # Handle DELIMITER changes
        if line.upper().startswith('DELIMITER'):
            if 'DELIMITER ;' in line.upper():
                delimiter = ';'
                in_delimiter_block = False
            else:
                delimiter = '//'
                in_delimiter_block = True
            continue
        
        # Add line to current statement
        current_stmt.append(line)
        
        # Check if statement is complete
        if line.endswith(delimiter):
            stmt = ' '.join(current_stmt)
            if delimiter == '//':
                stmt = stmt[:-2]  # Remove //
            else:
                stmt = stmt[:-1]  # Remove ;
            
            if stmt.strip():
                statements.append(stmt)
            current_stmt = []
    
    # Execute each statement
    total = len(statements)
    for i, stmt in enumerate(statements, 1):
        try:
            print(f"[{i}/{total}] Executing: {stmt[:80]}...")
            cursor.execute(stmt)
            
            # Try to fetch results if any
            try:
                results = cursor.fetchall()
                if results:
                    for row in results:
                        print(f"  → {row}")
            except:
                pass  # No results to fetch
                
        except mysql.connector.Error as e:
            print(f"  ✗ ERROR: {e}")
            if "already exists" not in str(e):
                raise

def main():
    sql_file = Path(__file__).parent / 'create_database_schema.sql'
    
    if not sql_file.exists():
        print(f"✗ SQL file not found: {sql_file}")
        return 1
    
    print("=" * 80)
    print("Database Schema Deployment")
    print("=" * 80)
    print(f"Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"User: {DB_CONFIG['user']}")
    print(f"Target Database: asmp_config (will create)")
    print("=" * 80)
    
    # Read SQL file
    print(f"\nReading SQL file: {sql_file}")
    sql_content = read_sql_file(sql_file)
    print(f"  ✓ Loaded {len(sql_content)} characters")
    
    # Connect to database
    print(f"\nConnecting to MariaDB...")
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("  ✓ Connected successfully")
    except mysql.connector.Error as e:
        print(f"  ✗ Connection failed: {e}")
        return 1
    
    # Execute SQL script
    print(f"\nExecuting SQL script...")
    try:
        execute_sql_script(cursor, sql_content)
        conn.commit()
        print("\n  ✓ All statements executed successfully")
    except Exception as e:
        print(f"\n  ✗ Execution failed: {e}")
        conn.rollback()
        return 1
    finally:
        cursor.close()
        conn.close()
    
    # Verify database creation
    print(f"\nVerifying database creation...")
    try:
        verify_config = DB_CONFIG.copy()
        verify_config['database'] = 'asmp_config'
        conn = mysql.connector.connect(**verify_config)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print(f"\n  ✓ Database 'asmp_config' created successfully")
        print(f"  ✓ {len(tables)} tables created:")
        for (table,) in sorted(tables):
            print(f"    - {table}")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        print(f"  ✗ Verification failed: {e}")
        return 1
    
    print("\n" + "=" * 80)
    print("✓ DEPLOYMENT COMPLETE")
    print("=" * 80)
    return 0

if __name__ == '__main__':
    sys.exit(main())
