#!/usr/bin/env python3
"""
Build COMPLETE schema by merging AUTHORITATIVE_SCHEMA.sql with missing tables from code analysis.
Documents purpose and file usage for every table.
"""

import re
from pathlib import Path
from typing import Dict, List

def extract_tables_from_authoritative() -> Dict[str, str]:
    """Extract existing table definitions from AUTHORITATIVE_SCHEMA.sql"""
    auth_path = Path(__file__).parent.parent / "AUTHORITATIVE_SCHEMA.sql"
    content = auth_path.read_text(encoding='utf-8')
    
    tables = {}
    # Find all CREATE TABLE statements
    pattern = r'CREATE TABLE\s+([a-z_]+)\s*\((.*?)\)\s*ENGINE=InnoDB'
    matches = re.finditer(pattern, content, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        table_name = match.group(1)
        full_create = match.group(0)
        tables[table_name] = full_create
    
    return tables

def get_table_usage_from_report() -> Dict[str, Dict]:
    """Get file usage and purpose from DATABASE_SCHEMA_FROM_CODE.md"""
    report_path = Path(__file__).parent.parent / "DATABASE_SCHEMA_FROM_CODE.md"
    content = report_path.read_text(encoding='utf-8')
    
    usage = {}
    sections = re.split(r'\n### ([a-z_]+)\n', content)
    
    for i in range(1, len(sections), 2):
        table_name = sections[i]
        table_content = sections[i + 1]
        
        files = []
        files_match = re.search(r'\*\*Referenced In:\*\*\n((?:- `[^`]+`\n)+)', table_content)
        if files_match:
            files = re.findall(r'- `([^`]+)`', files_match.group(1))
        
        usage[table_name] = {'files': files}
    
    return usage

def infer_purpose(table_name: str) -> str:
    """Get purpose description for each table"""
    purposes = {
        # Core Infrastructure
        'instances': 'Minecraft server instances managed by AMP - core registry of all servers',
        'plugins': 'Global plugin registry - catalog of all known plugins across all instances',
        'instance_plugins': 'Plugin installations tracking - which plugins are installed where with version info',
        'datapacks': 'Global datapack registry - catalog of all known datapacks',
        'instance_datapacks': 'Datapack installations per world - tracks which datapacks are active in which worlds',
        'instance_server_properties': 'Server.properties file tracking - monitors server.properties per instance',
        'discovery_runs': 'Agent discovery execution history - logs each discovery scan run',
        'discovery_items': 'Individual discovery items - granular items found during discovery',
        'worlds': 'Minecraft world tracking - all worlds across all instances',
        
        # Plugin Management  
        'plugin_versions': 'Plugin version tracking - available versions and update detection',
        'plugin_metadata': 'Extended plugin metadata - additional info beyond basic registry',
        'plugin_instances': 'Alternative plugin-instance mapping - redundant with instance_plugins',
        'installed_plugins': 'Simplified plugin installation list - legacy tracking',
        'plugin_update_queue': 'Pending plugin updates - queue of plugins awaiting update approval',
        'plugin_meta_tags': 'Tags assigned to plugins - categorization of plugins',
        
        # Tagging System
        'meta_tag_categories': 'Tag categories - organizational buckets for tags (server_type, game_mode, etc)',
        'meta_tags': 'Available tags - all tags that can be assigned to instances/plugins',
        'instance_meta_tags': 'Instance tag assignments - which tags are applied to which instances',
        'meta_tag_history': 'Tag change audit trail - historical record of tag changes',
        'instance_tags': 'Alternative instance tagging - redundant with instance_meta_tags',
        'tag_hierarchy': 'Tag parent-child relationships - hierarchical tag structure',
        'tag_dependencies': 'Required tag dependencies - if tag A then must have tag B',
        'tag_conflicts': 'Conflicting tag rules - tag A excludes tag B',
        
        # Configuration Management
        'config_rules': 'Baseline configuration rules - expected values for all config keys',
        'config_variables': 'Variable definitions - template variables for config substitution',
        'config_templates': 'Reusable config templates - pre-defined config patterns',
        'config_baselines': 'Baseline configuration snapshots - saved baseline states',
        'baseline_snapshots': 'Loaded baseline tracking - tracks which baseline files have been loaded',
        'config_change_history': 'Config change audit trail - all configuration changes logged',
        'config_locks': 'Pessimistic locking - prevents concurrent config edits',
        'config_key_migrations': 'Config key renaming tracking - handles config key migrations',
        'config_keys': 'Config key registry - legacy registry of all known config keys',
        
        # Variance & Drift Detection
        'config_variance_cache': 'Pre-calculated variance data - cached for UI performance, tracks expected vs actual',
        'config_variance_detected': 'Detected configuration variances - differences from expected values',
        'config_variances': 'Variance analysis results - comprehensive variance data',
        'config_variance_history': 'Historical variance tracking - variance trends over time',
        'config_drift_log': 'Configuration drift events - log of drift detection events',
        'server_properties_baselines': 'Expected server.properties values - baseline for server.properties',
        'server_properties_variances': 'Server.properties drift detection - detected variances in server.properties',
        
        # Deployment & Updates
        'deployment_queue': 'Pending deployment operations - queue of changes awaiting deployment',
        'deployment_history': 'Deployment audit trail - completed deployments log',
        'deployment_logs': 'Detailed deployment operation logs - granular deployment step logging',
        'datapack_deployment_queue': 'Datapack deployment queue - datapack-specific deployments',
        
        # Approval Workflow
        'change_approval_requests': 'Change approval requests - workflow for change approval',
        'approval_votes': 'Individual approval votes - votes on approval requests',
        
        # Grouping & Hierarchy
        'instance_groups': 'Logical instance grouping - groups of related instances',
        'instance_group_members': 'Instance group membership - which instances belong to which groups',
        'world_config_rules': 'World-specific config rules - config rules that apply to specific worlds',
        'ranks': 'Player rank definitions - permission tiers/ranks',
        'rank_config_rules': 'Rank-specific config rules - config rules per rank',
        'player_config_overrides': 'Player-specific config overrides - per-player config customizations',
        
        # Endpoint Management
        'endpoint_config_files': 'External endpoint configuration files - configs for external endpoints',
        'endpoint_config_backups': 'Endpoint config backups - backup copies of endpoint configs',
        'endpoint_config_change_history': 'Endpoint config change audit - change history for endpoints',
        
        # Monitoring & Operations
        'notification_log': 'System notifications - alerts and notification history',
        'scheduled_tasks': 'Scheduled background tasks - cron-like task definitions',
        'audit_log': 'System-wide audit trail - comprehensive audit logging',
        'agent_heartbeats': 'Agent health monitoring - tracks agent last-seen and status',
        'system_health_metrics': 'System performance metrics - CPU, memory, disk, etc monitoring',
        'cicd_webhook_events': 'CI/CD webhook events - GitHub/GitLab webhook integration log'
    }
    
    return purposes.get(table_name, f'Table referenced in code - purpose needs documentation')

def build_complete_schema():
    """Build complete schema merging existing and missing tables"""
    
    print("Loading existing tables from AUTHORITATIVE_SCHEMA.sql...")
    existing_tables = extract_tables_from_authoritative()
    print(f"  Found {len(existing_tables)} existing table definitions")
    
    print("\nLoading usage data from DATABASE_SCHEMA_FROM_CODE.md...")
    usage_data = get_table_usage_from_report()
    print(f"  Found {len(usage_data)} tables referenced in code")
    
    # Find missing tables
    missing = set(usage_data.keys()) - set(existing_tables.keys())
    print(f"\n  Missing tables: {len(missing)}")
    
    output_path = Path(__file__).parent.parent / "COMPLETE_AUTHORITATIVE_SCHEMA.sql"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("""-- ============================================================================
-- ARCHIVESMP CONFIGURATION MANAGER - COMPLETE AUTHORITATIVE SCHEMA
-- Generated: November 24, 2025
-- Source: Merged from AUTHORITATIVE_SCHEMA.sql + code analysis
-- 
-- This schema includes ALL tables referenced in the codebase with:
--   - Purpose documentation
--   - File usage information
--   - Complete table definitions where available
-- 
-- Tables are marked as:
--   [CORE] - From original AUTHORITATIVE_SCHEMA, fully defined
--   [TODO] - Referenced in code but needs definition
-- ============================================================================

DROP DATABASE IF EXISTS asmp_config;
CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asmp_config;

""")
        
        # Write tables by category
        categories = {
            'CORE INFRASTRUCTURE': [
                'instances', 'plugins', 'instance_plugins', 'datapacks',
                'instance_datapacks', 'instance_server_properties', 
                'discovery_runs', 'discovery_items', 'worlds'
            ],
            'PLUGIN MANAGEMENT': [
                'plugin_versions', 'plugin_metadata', 'plugin_instances',
                'installed_plugins', 'plugin_update_queue', 'plugin_meta_tags'
            ],
            'TAGGING SYSTEM': [
                'meta_tag_categories', 'meta_tags', 'instance_meta_tags',
                'meta_tag_history', 'instance_tags', 'tag_hierarchy',
                'tag_dependencies', 'tag_conflicts'
            ],
            'CONFIGURATION MANAGEMENT': [
                'config_rules', 'config_variables', 'config_templates',
                'config_baselines', 'baseline_snapshots', 'config_change_history',
                'config_locks', 'config_key_migrations', 'config_keys'
            ],
            'VARIANCE & DRIFT DETECTION': [
                'config_variance_cache', 'config_variance_detected', 'config_variances',
                'config_variance_history', 'config_drift_log',
                'server_properties_baselines', 'server_properties_variances'
            ],
            'DEPLOYMENT & UPDATES': [
                'deployment_queue', 'deployment_history', 'deployment_logs',
                'datapack_deployment_queue'
            ],
            'APPROVAL WORKFLOW': [
                'change_approval_requests', 'approval_votes'
            ],
            'GROUPING & HIERARCHY': [
                'instance_groups', 'instance_group_members', 'world_config_rules',
                'ranks', 'rank_config_rules', 'player_config_overrides'
            ],
            'ENDPOINT MANAGEMENT': [
                'endpoint_config_files', 'endpoint_config_backups',
                'endpoint_config_change_history'
            ],
            'MONITORING & OPERATIONS': [
                'notification_log', 'scheduled_tasks', 'audit_log',
                'agent_heartbeats', 'system_health_metrics', 'cicd_webhook_events'
            ]
        }
        
        for category, table_list in categories.items():
            f.write(f"-- ============================================================================\n")
            f.write(f"-- {category}\n")
            f.write(f"-- ============================================================================\n\n")
            
            for table_name in table_list:
                purpose = infer_purpose(table_name)
                files = usage_data.get(table_name, {}).get('files', [])
                
                if table_name in existing_tables:
                    status = "[CORE]"
                else:
                    status = "[TODO]"
                
                f.write(f"-- {status} {table_name}\n")
                f.write(f"-- Purpose: {purpose}\n")
                if files:
                    file_list = ', '.join(files[:3])
                    if len(files) > 3:
                        file_list += f" (+{len(files)-3} more)"
                    f.write(f"-- Used in: {file_list}\n")
                f.write(f"--\n")
                
                if table_name in existing_tables:
                    f.write(existing_tables[table_name])
                    f.write(";\n\n")
                else:
                    f.write(f"-- CREATE TABLE {table_name} (\n")
                    f.write(f"--     -- TODO: Define schema based on code usage\n")
                    f.write(f"--     -- See DATABASE_SCHEMA_FROM_CODE.md for column details\n")
                    f.write(f"-- ) ENGINE=InnoDB;\n\n")
        
        # Add seed data
        f.write("""
-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Default Meta Tag Categories
INSERT INTO meta_tag_categories (category_name, display_name, description) VALUES
('server_type', 'Server Type', 'Type of Minecraft server'),
('player_count', 'Player Count', 'Expected player capacity'),
('game_mode', 'Game Mode', 'Primary game mode'),
('mod_level', 'Modification Level', 'How heavily modded the server is'),
('maintenance', 'Maintenance', 'Maintenance and operational status');

-- Default Meta Tags
INSERT INTO meta_tags (tag_name, display_name, category_id, tag_color) VALUES
('pure-vanilla', 'Pure Vanilla', (SELECT category_id FROM meta_tag_categories WHERE category_name='mod_level'), '#8B4513'),
('lightly-modded', 'Lightly Modded', (SELECT category_id FROM meta_tag_categories WHERE category_name='mod_level'), '#4682B4'),
('heavily-modded', 'Heavily Modded', (SELECT category_id FROM meta_tag_categories WHERE category_name='mod_level'), '#DC143C'),
('survival', 'Survival', (SELECT category_id FROM meta_tag_categories WHERE category_name='game_mode'), '#228B22'),
('creative', 'Creative', (SELECT category_id FROM meta_tag_categories WHERE category_name='game_mode'), '#FFD700'),
('minigame', 'Minigame', (SELECT category_id FROM meta_tag_categories WHERE category_name='game_mode'), '#FF69B4'),
('hub', 'Hub/Lobby', (SELECT category_id FROM meta_tag_categories WHERE category_name='server_type'), '#4169E1'),
('proxy', 'Proxy Server', (SELECT category_id FROM meta_tag_categories WHERE category_name='server_type'), '#8A2BE2');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
""")
    
    print(f"\n✅ Complete schema generated: {output_path}")
    print(f"\n   Summary:")
    print(f"   - Total tables in codebase: {len(usage_data)}")
    print(f"   - Tables with definitions [CORE]: {len(existing_tables)}")
    print(f"   - Tables needing definition [TODO]: {len(missing)}")
    
    print(f"\n   Next steps:")
    print(f"   1. Review COMPLETE_AUTHORITATIVE_SCHEMA.sql")
    print(f"   2. Define [TODO] tables based on usage in DATABASE_SCHEMA_FROM_CODE.md")
    print(f"   3. Test on development database")
    print(f"   4. Deploy to production")

if __name__ == "__main__":
    build_complete_schema()
