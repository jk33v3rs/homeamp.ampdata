#!/usr/bin/env python3
"""
Baseline Loader Script

Loads universal baseline configs from markdown files into the database.
Populates baseline_snapshots and creates initial GLOBAL rules in config_rules.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analyzers.baseline_parser import BaselineParser
from database.db_access import ConfigDatabase
from core.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_baselines_to_db():
    """Load all baseline configs into database"""
    
    # Initialize parser
    baselines_dir = Path(__file__).parent.parent / "data" / "baselines" / "universal_configs"
    parser = BaselineParser(str(baselines_dir))
    
    # Connect to database
    db = ConfigDatabase(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    db.connect()
    
    try:
        # Get list of all plugins with baselines
        plugins = parser.list_plugins()
        logger.info(f"Found {len(plugins)} plugins with baseline configs")
        
        snapshot_id = f"baseline-load-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        for plugin_name in plugins:
            logger.info(f"Processing {plugin_name}...")
            
            # Parse baseline
            baseline_config = parser.parse_plugin_baseline(plugin_name)
            
            if not baseline_config:
                logger.warning(f"No config values found for {plugin_name}")
                continue
            
            # Insert into baseline_snapshots
            insert_baseline_snapshot(db, snapshot_id, plugin_name, baseline_config)
            
            # Create GLOBAL rules for each config key
            create_global_rules(db, plugin_name, baseline_config)
            
            logger.info(f"Loaded {len(baseline_config)} config keys for {plugin_name}")
        
        logger.info(f"Successfully loaded {len(plugins)} baselines")
        
    finally:
        db.disconnect()


def insert_baseline_snapshot(db, snapshot_id: str, plugin_name: str, config: dict):
    """Insert baseline snapshot into database"""
    
    cursor = db.connection.cursor()
    
    for config_key, value in config.items():
        # Assume config.yml as default file (can be enhanced later)
        config_file = "config.yml"
        
        # Convert value to string for storage
        value_str = str(value) if value is not None else None
        
        # Determine value type
        value_type = type(value).__name__
        if value is None:
            value_type = 'null'
        elif isinstance(value, bool):
            value_type = 'boolean'
        elif isinstance(value, int):
            value_type = 'integer'
        elif isinstance(value, float):
            value_type = 'float'
        elif isinstance(value, str):
            value_type = 'string'
        elif isinstance(value, list):
            value_type = 'list'
        elif isinstance(value, dict):
            value_type = 'dict'
        
        cursor.execute("""
            INSERT INTO baseline_snapshots 
            (snapshot_id, plugin_name, config_file, config_key, expected_value, 
             value_type, created_at, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                expected_value = VALUES(expected_value),
                value_type = VALUES(value_type),
                created_at = VALUES(created_at)
        """, (
            snapshot_id,
            plugin_name,
            config_file,
            config_key,
            value_str,
            value_type,
            datetime.now(),
            f"Loaded from {plugin_name}_universal_config.md"
        ))
    
    db.connection.commit()


def create_global_rules(db, plugin_name: str, config: dict):
    """Create GLOBAL priority rules for baseline configs"""
    
    cursor = db.connection.cursor()
    
    for config_key, value in config.items():
        config_file = "config.yml"
        
        # Check if rule already exists
        cursor.execute("""
            SELECT rule_id FROM config_rules
            WHERE config_type = 'plugin'
              AND plugin_name = %s
              AND config_file = %s
              AND config_key = %s
              AND scope = 'GLOBAL'
        """, (plugin_name, config_file, config_key))
        
        if cursor.fetchone():
            # Rule already exists, skip
            continue
        
        # Convert value to string
        value_str = str(value) if value is not None else None
        
        # Determine if this is a variable placeholder
        is_variable = False
        if isinstance(value, str) and '{{' in value and '}}' in value:
            is_variable = True
        
        # Create GLOBAL rule
        cursor.execute("""
            INSERT INTO config_rules
            (config_type, plugin_name, config_file, config_key, expected_value,
             scope, priority, is_variable, created_at, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'plugin',
            plugin_name,
            config_file,
            config_key,
            value_str,
            'GLOBAL',
            4,  # GLOBAL = priority 4
            is_variable,
            datetime.now(),
            f"Auto-created from baseline: {plugin_name}_universal_config.md"
        ))
    
    db.connection.commit()


if __name__ == '__main__':
    load_baselines_to_db()
