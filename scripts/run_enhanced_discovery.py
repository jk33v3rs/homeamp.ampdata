#!/usr/bin/env python3
"""
Enhanced Discovery Script - Runs full discovery with new agent features
"""
import sys
import os
import logging

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'software', 'homeamp-config-manager', 'src'))

from agent.variance_detector import VarianceDetector
from agent.server_properties_scanner import ServerPropertiesScanner
from agent.datapack_discovery import DatapackDiscovery
import mysql.connector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': '135.181.212.169',
    'port': 3369,
    'user': 'sqlworkerSMP',
    'password': 'SQLdb2024!',
    'database': 'asmp_config'
}


def get_instances() -> list:
    """Fetch all instances from database"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT instance_id, instance_path, server_name, online_status
            FROM instances
            WHERE online_status = TRUE
            ORDER BY instance_id
        """)
        instances = cursor.fetchall()
        logger.info(f"Found {len(instances)} online instances")
        return instances
    finally:
        cursor.close()
        conn.close()


def get_plugin_list() -> list:
    """Fetch list of discovered plugins"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT name FROM plugins ORDER BY name")
        plugins = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(plugins)} plugins")
        return plugins
    finally:
        cursor.close()
        conn.close()


def run_variance_detection(instances: list, plugins: list):
    """Run config variance detection"""
    logger.info("=" * 60)
    logger.info("PHASE 1: Config Variance Detection")
    logger.info("=" * 60)
    
    detector = VarianceDetector(DB_CONFIG)
    total_variances = detector.scan_and_register_all(instances, plugins)
    
    logger.info(f"✓ Config variance detection complete: {total_variances} variances found")
    return total_variances


def run_server_properties_scan(instances: list):
    """Run server.properties scanning"""
    logger.info("=" * 60)
    logger.info("PHASE 2: Server Properties Scanning")
    logger.info("=" * 60)
    
    scanner = ServerPropertiesScanner(DB_CONFIG)
    
    # First, create baseline from PRI01 (primary instance)
    pri01 = next((i for i in instances if i['instance_id'] == 'PRI01'), None)
    if pri01:
        logger.info("Creating global baseline from PRI01...")
        scanner.create_baseline_from_instance('PRI01', pri01['instance_path'])
    else:
        logger.warning("PRI01 not found, skipping baseline creation")
    
    # Scan all instances
    total_variances = scanner.scan_all_instances(instances)
    
    logger.info(f"✓ Server properties scan complete: {total_variances} variances found")
    return total_variances


def run_datapack_discovery(instances: list):
    """Run datapack discovery"""
    logger.info("=" * 60)
    logger.info("PHASE 3: Datapack Discovery")
    logger.info("=" * 60)
    
    discovery = DatapackDiscovery(DB_CONFIG)
    total_datapacks = discovery.scan_and_register_all(instances)
    
    logger.info(f"✓ Datapack discovery complete: {total_datapacks} datapacks found")
    return total_datapacks


def verify_data_populated():
    """Verify that tables have been populated"""
    logger.info("=" * 60)
    logger.info("VERIFICATION: Checking Data Population")
    logger.info("=" * 60)
    
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    tables_to_check = [
        ('config_variances', 10),
        ('server_properties_variances', 5),
        ('datapacks', 3)
    ]
    
    all_passed = True
    
    for table_name, expected_min in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        if count >= expected_min:
            logger.info(f"✓ {table_name}: {count} rows (expected >= {expected_min})")
        else:
            logger.warning(f"⚠ {table_name}: {count} rows (expected >= {expected_min})")
            all_passed = False
    
    cursor.close()
    conn.close()
    
    return all_passed


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("ENHANCED DISCOVERY - STARTING")
    logger.info("=" * 60)
    
    try:
        # Fetch instances and plugins
        instances = get_instances()
        if not instances:
            logger.error("No instances found! Ensure bootstrap_discovery.py has run.")
            return 1
        
        plugins = get_plugin_list()
        if not plugins:
            logger.error("No plugins found! Ensure bootstrap_discovery.py has run.")
            return 1
        
        # Run all discovery phases
        variance_count = run_variance_detection(instances, plugins)
        property_variance_count = run_server_properties_scan(instances)
        datapack_count = run_datapack_discovery(instances)
        
        # Verify results
        logger.info("")
        verification_passed = verify_data_populated()
        
        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("ENHANCED DISCOVERY - SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Instances scanned: {len(instances)}")
        logger.info(f"Config variances: {variance_count}")
        logger.info(f"Server property variances: {property_variance_count}")
        logger.info(f"Datapacks discovered: {datapack_count}")
        logger.info(f"Verification: {'PASSED' if verification_passed else 'FAILED'}")
        logger.info("=" * 60)
        
        return 0 if verification_passed else 1
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
