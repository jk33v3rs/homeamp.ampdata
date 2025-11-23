#!/usr/bin/env python3
"""
Build COMPLETE_AUTHORITATIVE_SCHEMA.sql from discovered SQL files
Extracts all CREATE TABLE statements and merges them with purpose documentation
"""

import re
import os
from pathlib import Path

# SQL files discovered with CREATE TABLE statements
SQL_SOURCES = [
    'scripts/create_new_tables.sql',
    'scripts/add_config_rules_tables.sql', 
    'scripts/create_database_schema.sql',
    'scripts/add_tracking_history_tables.sql',
    'scripts/add_plugin_metadata_tables.sql',
    'software/homeamp-config-manager/scripts/create_multi_level_scope_tables.sql',
    'software/homeamp-config-manager/scripts/create_endpoint_config_tables.sql',
    'software/homeamp-config-manager/scripts/create_advanced_feature_tables.sql',
    'scripts/add_plugin_tracking_tables.sql',
    'scripts/add_comprehensive_tracking.sql',
    'scripts/create_dynamic_metadata_system.sql',
    'software/homeamp-config-manager/scripts/clear_duplicate_logs.sql'
]

# Python files with CREATE TABLE in code
PYTHON_SOURCES = [
    'software/homeamp-config-manager/src/agent/conflict_detector.py',  # config_locks
    'software/homeamp-config-manager/src/agent/approval_workflow.py'    # approval_votes
]

def extract_create_tables_from_sql(filepath):
    """Extract CREATE TABLE statements from SQL file"""
    tables = {}
    
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return tables
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Pattern to match CREATE TABLE ... ENGINE=InnoDB;
    pattern = r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-zA-Z0-9_]+)\s*\('
    
    for match in re.finditer(pattern, content, re.IGNORECASE):
        table_name = match.group(1).strip()
        start_pos = match.start()
        
        # Find the end of the CREATE statement (ENGINE=... or just semicolon)
        remaining = content[start_pos:]
        
        # Try to find ENGINE clause
        engine_match = re.search(r';', remaining)
        if engine_match:
            end_pos = start_pos + engine_match.end()
            full_def = content[start_pos:end_pos]
            
            # Don't normalize whitespace - preserve formatting
            full_def = full_def.strip()
            
            if table_name not in tables:
                tables[table_name] = {
                    'definition': full_def,
                    'source': filepath
                }
    
    return tables

def extract_create_tables_from_python(filepath):
    """Extract CREATE TABLE statements from Python code"""
    tables = {}
    
    if not os.path.exists(filepath):
        return tables
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Look for CREATE TABLE in Python strings
    pattern = r'CREATE TABLE(?:\s+IF NOT EXISTS)?\s+([a-zA-Z0-9_]+)\s*\('
    
    for match in re.finditer(pattern, content, re.IGNORECASE):
        table_name = match.group(1).strip()
        start_pos = match.start()
        
        # Find the end (triple quote or closing paren + quote)
        remaining = content[start_pos:]
        
        # Try to find the end of the SQL statement
        end_match = re.search(r'\)\s*ENGINE', remaining, re.IGNORECASE)
        if not end_match:
            end_match = re.search(r'\)', remaining)
            
        if end_match:
            end_pos = start_pos + end_match.end()
            
            # Look for ENGINE clause
            engine_match = re.search(r'ENGINE\s*=\s*\w+', content[end_pos:end_pos+100], re.IGNORECASE)
            if engine_match:
                end_pos += engine_match.end()
            
            full_def = content[start_pos:end_pos]
            
            # Don't normalize whitespace - preserve formatting
            full_def = full_def.strip()
            
            # Ensure it ends with semicolon
            if not full_def.endswith(';'):
                full_def += ';'
            
            if table_name not in tables:
                tables[table_name] = {
                    'definition': full_def,
                    'source': filepath
                }
    
    return tables

def infer_purpose(table_name):
    """Infer the purpose of a table from its name"""
    purposes = {
        # Infrastructure
        'instances': 'Core: Physical AMP instance deployments (servers)',
        'instance_groups': 'Grouping: Meta-server clusters (SMP vs Creative vs Test)',
        'instance_group_members': 'Grouping: Links instances to groups',
        'instance_tags': 'Tagging: Assigns meta-tags to instances',
        'instance_meta_tags': 'Tagging: Links instances to meta-tags',
        'meta_tag_categories': 'Tagging: Categories for organizing meta-tags',
        'meta_tags': 'Tagging: Dynamic tags for classification (PvP, Economy, Creative, etc.)',
        'meta_tag_history': 'Tagging: Audit trail of tag changes',
        
        # Plugins
        'plugins': 'Plugin Management: Discovered plugins across all instances',
        'instance_plugins': 'Plugin Management: Which plugins are installed on which instances',
        'plugin_versions': 'Plugin Management: Version tracking and update availability',
        'plugin_update_queue': 'Plugin Management: Queue of pending plugin updates',
        'plugin_update_sources': 'Plugin Management: Where to check for plugin updates',
        
        # Datapacks
        'datapacks': 'Datapack Management: Discovered datapacks',
        'instance_datapacks': 'Datapack Management: Which datapacks are on which instances',
        'datapack_deployment_queue': 'Datapack Management: Queue of pending datapack deployments',
        'datapack_update_sources': 'Datapack Management: Where to check for datapack updates',
        'datapack_versions': 'Datapack Management: Version tracking',
        
        # Server Properties
        'instance_server_properties': 'Configuration: server.properties values per instance',
        'server_properties_baselines': 'Configuration: Expected server.properties values',
        'server_properties_variances': 'Configuration: Detected deviations in server.properties',
        
        # Config Rules
        'config_rules': 'Configuration: Hierarchical rules (GLOBAL→SERVER→TAG→INSTANCE)',
        'config_variables': 'Configuration: Template variables ({{VARIABLE}})',
        'config_variance_cache': 'Variance Detection: Pre-calculated variance data for UI',
        'config_drift_log': 'Variance Detection: Actual config drift detected',
        'config_variance_detected': 'Variance Detection: Detected differences vs baselines',
        'config_change_history': 'History: Audit trail of all config changes',
        'baseline_snapshots': 'History: Loaded baseline files and their checksums',
        
        # Deployment
        'deployment_queue': 'Deployment: Pending deployments',
        'deployment_logs': 'Deployment: Per-instance deployment results',
        'deployment_history': 'Deployment: Complete deployment records',
        'deployment_changes': 'Deployment: Individual changes within deployments',
        
        # Approval Workflow
        'change_approval_requests': 'Approval: Change requests awaiting approval',
        'approval_votes': 'Approval: Individual votes on approval requests',
        
        # Worlds
        'worlds': 'World Management: Minecraft worlds across instances',
        'world_groups': 'World Management: Groupings of related worlds',
        'world_group_members': 'World Management: Links worlds to groups',
        'world_tags': 'World Management: Tags applied to worlds',
        'world_meta_tags': 'World Management: Meta-tags for worlds',
        'world_config_rules': 'World Management: Config rules scoped to worlds',
        
        # Regions
        'regions': 'Region Management: WorldGuard/GriefPrevention regions',
        'region_groups': 'Region Management: Groupings of regions',
        'region_group_members': 'Region Management: Links regions to groups',
        'region_tags': 'Region Management: Tags for regions',
        
        # Ranks & Players
        'rank_definitions': 'Player Progression: Rank definitions (Member, VIP, etc.)',
        'player_ranks': 'Player Progression: Current rank per player',
        'rank_meta_tags': 'Player Progression: Meta-tags for ranks',
        'rank_config_rules': 'Player Progression: Config rules scoped to ranks',
        'player_config_overrides': 'Player Progression: Player-specific config overrides',
        'player_meta_tags': 'Player Progression: Meta-tags for individual players',
        'player_role_categories': 'Player Progression: Categories for player roles',
        'player_roles': 'Player Progression: Donor/Staff role definitions',
        'player_role_assignments': 'Player Progression: Assigns roles to players',
        
        # Monitoring
        'discovery_runs': 'Monitoring: Agent discovery run history',
        'agent_heartbeats': 'Monitoring: Agent health tracking',
        'system_health_metrics': 'Monitoring: Performance and health metrics',
        'audit_log': 'Monitoring: System-wide audit trail',
        'notification_log': 'Monitoring: Sent notifications',
        
        # Scheduling
        'scheduled_tasks': 'Automation: Scheduled task configuration and status',
        
        # Endpoints
        'endpoint_config_files': 'Endpoint Config: Non-plugin config files tracked',
        'endpoint_config_backups': 'Endpoint Config: Backups of endpoint configs',
        'endpoint_config_change_history': 'Endpoint Config: Change history for endpoints',
        
        # Advanced Features
        'tag_dependencies': 'Advanced: Tag dependency management',
        'tag_conflicts': 'Advanced: Conflicting tag detection',
        'tag_hierarchy': 'Advanced: Hierarchical tag relationships',
        'instance_feature_inventory': 'Advanced: Feature capabilities per instance',
        'server_capabilities': 'Advanced: Server hardware/software capabilities',
        'world_features': 'Advanced: Features enabled per world',
        
        # Other
        'config_locks': 'Locking: Prevents concurrent config edits',
        'cicd_webhook_events': 'CI/CD: Webhook events from build systems',
        'instance_platform_configs': 'Platform: Platform-specific configs',
        'discovery_items': 'Discovery: Individual items found during discovery',
    }
    
    return purposes.get(table_name, f'Purpose unknown - referenced in code')

def apply_schema_fixes(definition, table_name):
    """Apply fixes to table definitions"""
    
    # Fix 1: Meta tags - change 'id' to 'tag_id' for consistency
    if table_name == 'meta_tags':
        definition = definition.replace('id INT AUTO_INCREMENT PRIMARY KEY', 'tag_id INT AUTO_INCREMENT PRIMARY KEY')
        definition = definition.replace('parent_tag_id INT', 'parent_tag_id INT')
        definition = definition.replace('REFERENCES meta_tags(id)', 'REFERENCES meta_tags(tag_id)')
    
    # Fix 2: Plugin versions - change plugin_id from INT to VARCHAR(64)
    if table_name == 'plugin_versions':
        definition = definition.replace('plugin_id INT NOT NULL', 'plugin_id VARCHAR(64) NOT NULL')
        definition = definition.replace('REFERENCES plugins(id)', 'REFERENCES plugins(plugin_id)')
    
    # Fix 3: Plugin update sources - change plugin_id from INT to VARCHAR(64)
    if table_name == 'plugin_update_sources':
        definition = definition.replace('plugin_id INT NOT NULL', 'plugin_id VARCHAR(64) NOT NULL')
        definition = definition.replace('REFERENCES plugins(id)', 'REFERENCES plugins(plugin_id)')
    
    # Fix 4: Datapack deployment queue - fix FK reference
    if table_name == 'datapack_deployment_queue':
        definition = definition.replace('REFERENCES datapacks(datapack_id)', 'REFERENCES datapacks(id)')
    
    # Fix 5: Approval votes - fix ENGINE syntax
    if table_name == 'approval_votes':
        definition = definition.replace(') ENGINE;', ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;')
    
    # Fix 6: Add queue linkage to deployment_history
    if table_name == 'deployment_history':
        # Add queue_deployment_id column if not present
        if 'queue_deployment_id' not in definition:
            # Insert before the FKs
            insert_pos = definition.find('FOREIGN KEY')
            if insert_pos > 0:
                new_col = "\n    queue_deployment_id VARCHAR(36) NULL COMMENT 'Links to deployment_queue.deployment_id',\n    "
                definition = definition[:insert_pos] + new_col + definition[insert_pos:]
    
    # Fix all FK references to meta_tags to use tag_id
    if 'REFERENCES meta_tags(' in definition:
        definition = definition.replace('REFERENCES meta_tags(tag_id)', 'REFERENCES meta_tags(tag_id)')
    
    return definition

def main():
    all_tables = {}
    
    print("🔍 Extracting CREATE TABLE statements from SQL files...\n")
    
    # Extract from SQL files
    for sql_file in SQL_SOURCES:
        tables = extract_create_tables_from_sql(sql_file)
        for name, data in tables.items():
            if name not in all_tables:
                all_tables[name] = data
                print(f"  ✓ {name:<40} from {sql_file}")
    
    print(f"\n🐍 Extracting CREATE TABLE statements from Python files...\n")
    
    # Extract from Python files
    for py_file in PYTHON_SOURCES:
        tables = extract_create_tables_from_python(py_file)
        for name, data in tables.items():
            if name not in all_tables:
                all_tables[name] = data
                print(f"  ✓ {name:<40} from {py_file}")
    
    print(f"\n🔧 Applying schema fixes...")
    
    # Apply fixes to all tables
    for table_name, table_data in all_tables.items():
        table_data['definition'] = apply_schema_fixes(table_data['definition'], table_name)
    
    print(f"\n📊 Total tables extracted: {len(all_tables)}")
    
    # Build the complete schema
    output = []
    output.append("-- ============================================================================")
    output.append("-- COMPLETE AUTHORITATIVE SCHEMA (CORRECTED)")
    output.append("-- Generated from discovered SQL and Python files")
    output.append(f"-- Total Tables: {len(all_tables)}")
    output.append("--")
    output.append("-- FIXES APPLIED:")
    output.append("-- 1. meta_tags: Changed 'id' → 'tag_id' for FK consistency")
    output.append("-- 2. plugin_versions: Changed plugin_id INT → VARCHAR(64)")
    output.append("-- 3. plugin_update_sources: Changed plugin_id INT → VARCHAR(64)")
    output.append("-- 4. datapack_deployment_queue: Fixed FK to datapacks(id)")
    output.append("-- 5. approval_votes: Fixed ENGINE syntax")
    output.append("-- 6. deployment_history: Added queue_deployment_id linkage")
    output.append("-- ============================================================================\n")
    output.append("USE asmp_config;\n")
    
    # Group tables by category
    categories = {
        'Infrastructure': ['instances', 'instance_groups', 'instance_group_members', 'instance_tags', 'instance_meta_tags', 
                          'meta_tag_categories', 'meta_tags', 'meta_tag_history'],
        'Plugin Management': ['plugins', 'instance_plugins', 'plugin_versions', 'plugin_update_queue', 'plugin_update_sources'],
        'Datapack Management': ['datapacks', 'instance_datapacks', 'datapack_deployment_queue', 'datapack_update_sources', 'datapack_versions'],
        'Configuration': ['instance_server_properties', 'server_properties_baselines', 'server_properties_variances',
                         'config_rules', 'config_variables', 'config_change_history', 'baseline_snapshots'],
        'Variance Detection': ['config_variance_cache', 'config_drift_log', 'config_variance_detected'],
        'Deployment': ['deployment_queue', 'deployment_logs', 'deployment_history', 'deployment_changes'],
        'Approval Workflow': ['change_approval_requests', 'approval_votes'],
        'World Management': ['worlds', 'world_groups', 'world_group_members', 'world_tags', 'world_meta_tags', 'world_config_rules'],
        'Region Management': ['regions', 'region_groups', 'region_group_members', 'region_tags'],
        'Player Progression': ['rank_definitions', 'player_ranks', 'rank_meta_tags', 'rank_config_rules', 
                              'player_config_overrides', 'player_meta_tags', 'player_role_categories', 
                              'player_roles', 'player_role_assignments'],
        'Monitoring': ['discovery_runs', 'agent_heartbeats', 'system_health_metrics', 'audit_log', 'notification_log'],
        'Automation': ['scheduled_tasks'],
        'Endpoint Config': ['endpoint_config_files', 'endpoint_config_backups', 'endpoint_config_change_history'],
        'Advanced Features': ['tag_dependencies', 'tag_conflicts', 'tag_hierarchy', 'instance_feature_inventory', 
                             'server_capabilities', 'world_features'],
        'Other': []  # Catch-all for uncategorized
    }
    
    # Add tables to categories
    categorized = set()
    for category, table_list in categories.items():
        for table in table_list:
            if table in all_tables:
                categorized.add(table)
    
    # Add uncategorized to Other
    for table in all_tables:
        if table not in categorized:
            categories['Other'].append(table)
    
    # Generate schema by category
    for category, table_list in categories.items():
        tables_in_category = [t for t in table_list if t in all_tables]
        if not tables_in_category:
            continue
            
        output.append(f"\n-- ============================================================================")
        output.append(f"-- {category.upper()}")
        output.append(f"-- ============================================================================\n")
        
        for table_name in tables_in_category:
            table_data = all_tables[table_name]
            purpose = infer_purpose(table_name)
            source = table_data['source']
            
            output.append(f"-- {table_name}")
            output.append(f"-- Purpose: {purpose}")
            output.append(f"-- Source: {source}")
            output.append(table_data['definition'])
            output.append("")
    
    # Write to file
    output_file = 'COMPLETE_AUTHORITATIVE_SCHEMA.sql'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print(f"\n✅ Generated {output_file}")
    print(f"   📄 {len(output)} lines")
    print(f"   📊 {len(all_tables)} tables")

if __name__ == '__main__':
    main()
