#!/usr/bin/env python3
"""
Seed database with baseline configurations from universal_configs.zip

Extracts markdown baseline files and populates config_baselines table.
"""

import sys
import zipfile
from pathlib import Path
import mysql.connector
from mysql.connector import Error
import re
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent / "software" / "homeamp-config-manager"
sys.path.insert(0, str(project_root))

from src.analyzers.baseline_parser import BaselineParser


def get_db_connection():
    """Connect to production database"""
    try:
        conn = mysql.connector.connect(
            host='135.181.212.169',
            port=3369,
            user='root',
            password='2024!SQLdb',
            database='asmp_config'
        )
        if conn.is_connected():
            print("✓ Connected to database")
            return conn
    except Error as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)


def clear_existing_baselines(conn):
    """Clear existing baseline data"""
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM config_baselines")
        conn.commit()
        print(f"✓ Cleared existing baselines")
    except Error as e:
        print(f"✗ Failed to clear baselines: {e}")
    finally:
        cursor.close()


def seed_baselines(conn, baselines_dir: Path):
    """Seed baseline configurations from extracted markdown files"""
    parser = BaselineParser(str(baselines_dir))
    cursor = conn.cursor()
    
    inserted = 0
    failed = 0
    
    try:
        # Get all plugin baseline files
        for md_file in baselines_dir.glob("*.md"):
            plugin_name = md_file.stem
            print(f"\nProcessing {plugin_name}...")
            
            try:
                # Parse the baseline markdown file
                baseline_data = parser.parse_baseline_file(str(md_file))
                
                if not baseline_data:
                    print(f"  ⚠️  No data parsed from {md_file.name}")
                    failed += 1
                    continue
                
                # Insert each config file from the baseline
                for file_name, config_data in baseline_data.items():
                    if not config_data:
                        continue
                        
                    # Convert config_data dict to key-value pairs
                    for key_path, value in config_data.items():
                        try:
                            # Insert into config_baselines
                            cursor.execute("""
                                INSERT INTO config_baselines 
                                (plugin_name, file_name, key_path, expected_value, value_type, description)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                    expected_value = VALUES(expected_value),
                                    value_type = VALUES(value_type),
                                    description = VALUES(description)
                            """, (
                                plugin_name,
                                file_name,
                                key_path,
                                str(value),
                                type(value).__name__,
                                None  # description - could be extracted from markdown comments
                            ))
                            inserted += 1
                        except Error as e:
                            print(f"  ✗ Failed to insert {plugin_name}/{file_name}/{key_path}: {e}")
                            failed += 1
                
                conn.commit()
                print(f"  ✓ Inserted baseline for {plugin_name}")
                
            except Exception as e:
                print(f"  ✗ Failed to process {md_file.name}: {e}")
                failed += 1
                
    except Exception as e:
        print(f"✗ Seeding failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
    
    return inserted, failed


def main():
    """Main execution"""
    print("=== Baseline Database Seeding ===\n")
    
    # Paths
    zip_path = project_root / "data" / "baselines" / "universal_configs.zip"
    
    if not zip_path.exists():
        print(f"✗ Baseline zip not found: {zip_path}")
        sys.exit(1)
    
    print(f"📦 Found baseline zip: {zip_path}")
    
    # Extract zip to temp directory
    temp_dir = tempfile.mkdtemp(prefix="baselines_seed_")
    try:
        print(f"📂 Extracting to: {temp_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find the actual baselines directory (may be nested)
        baselines_dir = Path(temp_dir)
        universal_configs_dir = None
        
        # Look for universal_configs directory
        for item in baselines_dir.rglob("*"):
            if item.is_dir() and item.name == "universal_configs":
                universal_configs_dir = item
                break
        
        if not universal_configs_dir:
            # Try root of temp dir
            md_files = list(baselines_dir.glob("*.md"))
            if md_files:
                universal_configs_dir = baselines_dir
            else:
                print(f"✗ No universal_configs directory or .md files found in zip")
                sys.exit(1)
        
        print(f"📁 Found baselines in: {universal_configs_dir}")
        md_files = list(universal_configs_dir.glob("*.md"))
        print(f"📄 Found {len(md_files)} baseline files")
        
        # Connect to database
        conn = get_db_connection()
        
        # Clear existing data
        clear_existing_baselines(conn)
        
        # Seed baselines
        print("\n--- Seeding Baselines ---")
        inserted, failed = seed_baselines(conn, universal_configs_dir)
        
        print("\n=== Summary ===")
        print(f"✓ Inserted: {inserted} baseline entries")
        if failed > 0:
            print(f"✗ Failed: {failed} entries")
        
        conn.close()
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🧹 Cleaned up temp directory")


if __name__ == "__main__":
    main()
