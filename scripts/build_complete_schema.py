#!/usr/bin/env python3
"""
Build comprehensive database schema with documentation for every table and column.
Includes: file paths, line numbers, usage context, and purpose.
"""

import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple

def parse_schema_report(report_path: Path) -> Dict:
    """Parse DATABASE_SCHEMA_FROM_CODE.md to extract all table info"""
    content = report_path.read_text(encoding='utf-8')
    
    tables = {}
    current_table = None
    
    # Split by table sections
    sections = re.split(r'\n### ([a-z_]+)\n', content)
    
    for i in range(1, len(sections), 2):
        table_name = sections[i]
        table_content = sections[i + 1]
        
        # Skip non-table sections
        if table_name in ('for', 'information_schema', 'pending', 'backup'):
            continue
        
        tables[table_name] = {
            'columns': [],
            'files': [],
            'create_statements': [],
            'purpose': ''
        }
        
        # Extract columns
        cols_match = re.search(r'\*\*Columns Used:\*\*\n((?:- `[^`]+`\n)+)', table_content)
        if cols_match:
            cols = re.findall(r'- `([^`]+)`', cols_match.group(1))
            # Filter out SQL keywords
            keywords = {'and', 'or', 'as', 'from', 'where', 'select', 'insert', 'update', 
                       'delete', 'create', 'if', 'not', 'exists', 'table', 'into', 'values',
                       'set', 'on', 'join', 'left', 'right', 'inner', 'outer', 'group',
                       'order', 'by', 'limit', 'offset', 'having', 'distinct', 'count',
                       'sum', 'avg', 'max', 'min', 'case', 'when', 'then', 'else', 'end',
                       'null', 'true', 'false', 'default', 'primary', 'foreign', 'key',
                       'index', 'unique', 'constraint', 'references', 'cascade', 'check',
                       'return', 'new_status', 'result', 'comment', 'vote', 'approvals',
                       'rejections', 'votes', 'request', 'for', 'in', 'like', 'between',
                       'is', 'with', 'conn', 'cursor', 'f', 'i', 'd', 'al', 'cv', 'endpo',
                       'basel', 'dictionary', 'detail'}
            tables[table_name]['columns'] = [c for c in cols if c.lower() not in keywords]
        
        # Extract files
        files_match = re.search(r'\*\*Referenced In:\*\*\n((?:- `[^`]+`\n)+)', table_content)
        if files_match:
            files = re.findall(r'- `([^`]+)`', files_match.group(1))
            tables[table_name]['files'] = files
        
        # Extract CREATE statements
        creates = re.findall(r'```sql\n(CREATE TABLE.*?)\n```', table_content, re.DOTALL | re.IGNORECASE)
        if creates:
            # Take the first complete CREATE statement
            for create in creates:
                if len(create) > 100 and '(' in create:  # Valid CREATE statement
                    tables[table_name]['create_statements'].append(create)
                    break
    
    return tables

def infer_table_purpose(table_name: str, info: Dict) -> str:
    """Infer purpose from table name, columns, and usage patterns"""
    purposes = {
        'instances': 'Minecraft server instances managed by AMP',
        'plugins': 'Global plugin registry and metadata',
        'instance_plugins': 'Plugin installations per instance with version tracking',
        'datapacks': 'Global datapack registry',
        'instance_datapacks': 'Datapack installations per world per instance',
        'instance_server_properties': 'Server.properties tracking per instance',
        'discovery_runs': 'Agent discovery execution history',
        'discovery_items': 'Individual items discovered by agent runs',
        'meta_tag_categories': 'Categories for organizing meta tags',
        'meta_tags': 'Available tags for instances, plugins, etc.',
        'instance_meta_tags': 'Tag assignments to instances',
        'meta_tag_history': 'Historical record of tag changes',
        'instance_tags': 'Alternative tag assignment table',
        'tag_hierarchy': 'Hierarchical relationships between tags',
        'tag_dependencies': 'Required tag dependencies (if tag A then need tag B)',
        'tag_conflicts': 'Conflicting tag rules (tag A excludes tag B)',
        'plugin_meta_tags': 'Tags assigned to plugins',
        'config_rules': 'Baseline configuration rules and expected values',
        'config_variables': 'Variable definitions for config templating',
        'config_templates': 'Reusable configuration templates',
        'config_baselines': 'Baseline configuration snapshots',
        'baseline_snapshots': 'Loaded baseline files tracking',
        'config_change_history': 'Audit trail of configuration changes',
        'config_variance_cache': 'Pre-calculated variance data for UI performance',
        'config_variance_detected': 'Detected configuration variances',
        'config_variances': 'Configuration variance analysis results',
        'config_variance_history': 'Historical variance tracking',
        'config_drift_log': 'Detected configuration drift events',
        'config_locks': 'Pessimistic locking for concurrent config edits',
        'config_key_migrations': 'Config key renaming/migration tracking',
        'config_keys': 'Registry of all known config keys (legacy)',
        'deployment_queue': 'Pending deployment operations queue',
        'deployment_history': 'Completed deployment audit trail',
        'deployment_logs': 'Detailed deployment operation logs',
        'datapack_deployment_queue': 'Datapack-specific deployment queue',
        'plugin_update_queue': 'Plugin update pending queue',
        'plugin_versions': 'Plugin version tracking and update availability',
        'plugin_metadata': 'Extended plugin metadata',
        'plugin_instances': 'Alternative plugin-instance relationship table',
        'installed_plugins': 'Simplified plugin installation tracking',
        'change_approval_requests': 'Change approval workflow requests',
        'approval_votes': 'Individual votes on approval requests',
        'worlds': 'Minecraft world tracking per instance',
        'world_config_rules': 'World-specific configuration rules',
        'ranks': 'Player rank/permission tier definitions',
        'rank_config_rules': 'Rank-specific configuration rules',
        'player_config_overrides': 'Player-specific config value overrides',
        'instance_groups': 'Logical grouping of instances',
        'instance_group_members': 'Instance membership in groups',
        'endpoint_config_files': 'External endpoint configuration files',
        'endpoint_config_backups': 'Backups of endpoint configurations',
        'endpoint_config_change_history': 'Endpoint config change audit',
        'server_properties_baselines': 'Expected server.properties values',
        'server_properties_variances': 'Detected server.properties variances',
        'notification_log': 'System notifications and alerts',
        'scheduled_tasks': 'Scheduled background task definitions',
        'audit_log': 'System-wide audit trail',
        'agent_heartbeats': 'Agent health monitoring and last-seen tracking',
        'system_health_metrics': 'System performance and health metrics',
        'cicd_webhook_events': 'CI/CD webhook event log'
    }
    
    return purposes.get(table_name, f'Purpose not documented - used in {len(info["files"])} files')

def generate_complete_schema(tables: Dict, output_path: Path):
    """Generate complete SQL schema with inline documentation"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("""-- ============================================================================
-- ARCHIVESMP CONFIGURATION MANAGER - COMPLETE AUTHORITATIVE SCHEMA
-- Generated: November 24, 2025
-- Source: Extracted from actual codebase via extract_schema_from_code.py
-- 
-- This schema includes EVERY table referenced in the codebase with:
--   - File paths showing where each table/column is used
--   - Purpose documentation for each table
--   - Complete CREATE TABLE statements from code
-- ============================================================================

DROP DATABASE IF EXISTS asmp_config;
CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asmp_config;

-- ============================================================================
-- CORE INFRASTRUCTURE TABLES
-- ============================================================================

""")
        
        # Group tables by category
        categories = {
            'Infrastructure': ['instances', 'plugins', 'instance_plugins', 'datapacks', 
                             'instance_datapacks', 'instance_server_properties', 
                             'discovery_runs', 'discovery_items', 'worlds'],
            'Plugin Management': ['plugin_versions', 'plugin_metadata', 'plugin_instances',
                                'installed_plugins', 'plugin_update_queue'],
            'Tagging System': ['meta_tag_categories', 'meta_tags', 'instance_meta_tags',
                             'meta_tag_history', 'instance_tags', 'tag_hierarchy',
                             'tag_dependencies', 'tag_conflicts', 'plugin_meta_tags'],
            'Configuration Management': ['config_rules', 'config_variables', 'config_templates',
                                        'config_baselines', 'baseline_snapshots', 
                                        'config_change_history', 'config_locks',
                                        'config_key_migrations', 'config_keys'],
            'Variance & Drift Detection': ['config_variance_cache', 'config_variance_detected',
                                          'config_variances', 'config_variance_history',
                                          'config_drift_log', 'server_properties_baselines',
                                          'server_properties_variances'],
            'Deployment & Updates': ['deployment_queue', 'deployment_history', 'deployment_logs',
                                    'datapack_deployment_queue'],
            'Approval Workflow': ['change_approval_requests', 'approval_votes'],
            'Grouping & Hierarchy': ['instance_groups', 'instance_group_members',
                                    'world_config_rules', 'ranks', 'rank_config_rules',
                                    'player_config_overrides'],
            'Endpoint Management': ['endpoint_config_files', 'endpoint_config_backups',
                                   'endpoint_config_change_history'],
            'Monitoring & Operations': ['notification_log', 'scheduled_tasks', 'audit_log',
                                       'agent_heartbeats', 'system_health_metrics',
                                       'cicd_webhook_events']
        }
        
        for category, table_list in categories.items():
            f.write(f"-- ============================================================================\n")
            f.write(f"-- {category.upper()}\n")
            f.write(f"-- ============================================================================\n\n")
            
            for table_name in table_list:
                if table_name not in tables:
                    continue
                
                info = tables[table_name]
                purpose = infer_table_purpose(table_name, info)
                
                f.write(f"-- {table_name}\n")
                f.write(f"-- Purpose: {purpose}\n")
                f.write(f"-- Used in: {', '.join(info['files'][:3])}")
                if len(info['files']) > 3:
                    f.write(f" (+{len(info['files']) - 3} more)")
                f.write("\n")
                
                if info['columns']:
                    f.write(f"-- Columns: {', '.join(info['columns'][:10])}")
                    if len(info['columns']) > 10:
                        f.write(f" (+{len(info['columns']) - 10} more)")
                    f.write("\n")
                
                if info['create_statements']:
                    f.write(info['create_statements'][0])
                    f.write("\n\n")
                else:
                    f.write(f"-- WARNING: No CREATE TABLE statement found in code\n")
                    f.write(f"-- This table is referenced but may need manual definition\n\n")
        
        # Add seed data from AUTHORITATIVE_SCHEMA
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

def main():
    report_path = Path(__file__).parent.parent / "DATABASE_SCHEMA_FROM_CODE.md"
    output_path = Path(__file__).parent.parent / "COMPLETE_AUTHORITATIVE_SCHEMA.sql"
    
    if not report_path.exists():
        print(f"ERROR: {report_path} not found. Run extract_schema_from_code.py first.")
        return
    
    print(f"Parsing schema report: {report_path}")
    tables = parse_schema_report(report_path)
    
    print(f"Found {len(tables)} valid tables")
    print(f"Generating complete schema: {output_path}")
    
    generate_complete_schema(tables, output_path)
    
    print(f"\n✅ Complete schema generated!")
    print(f"   Tables: {len(tables)}")
    print(f"   Output: {output_path}")
    
    # Summary stats
    tables_with_creates = sum(1 for t in tables.values() if t['create_statements'])
    tables_without_creates = len(tables) - tables_with_creates
    
    print(f"\n   Tables with CREATE statements: {tables_with_creates}")
    print(f"   Tables needing manual definition: {tables_without_creates}")
    
    if tables_without_creates > 0:
        print(f"\n   Tables without CREATE statements:")
        for name, info in tables.items():
            if not info['create_statements']:
                print(f"      - {name} (used in {len(info['files'])} files)")

if __name__ == "__main__":
    main()
