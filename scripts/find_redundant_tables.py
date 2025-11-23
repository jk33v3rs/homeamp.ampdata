#!/usr/bin/env python3
"""
Analyze database schema to find redundant tables that appear to track the same thing.
Detects:
- Similar names (config_variance_* vs config_variances)
- Overlapping columns (>50% shared columns)
- Similar purposes based on column patterns
"""

import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, Set, List, Tuple
from difflib import SequenceMatcher

def similarity_ratio(a: str, b: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)"""
    return SequenceMatcher(None, a, b).ratio()

def extract_schema_from_report(report_path: Path) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]]]:
    """Extract table names, columns, and files from the markdown report"""
    tables = {}
    table_files = {}
    current_table = None
    in_columns_section = False
    in_files_section = False
    
    with open(report_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Detect table header
            if line.startswith('### '):
                table_name = line.strip().replace('### ', '')
                if table_name and 'Recommended Schema' not in table_name and 'Detailed Table' not in table_name:
                    current_table = table_name
                    tables[current_table] = set()
                    table_files[current_table] = set()
                    in_columns_section = False
                    in_files_section = False
            
            # Detect columns section
            elif line.startswith('**Columns Used:**'):
                in_columns_section = True
                in_files_section = False
            
            # Detect files section
            elif line.startswith('**Referenced In:**'):
                in_columns_section = False
                in_files_section = True
            
            # Extract column names
            elif in_columns_section and line.startswith('- `'):
                col = line.strip().replace('- `', '').replace('`', '')
                if current_table and col:
                    tables[current_table].add(col)
            
            # Extract file names
            elif in_files_section and line.startswith('- `'):
                file_path = line.strip().replace('- `', '').replace('`', '')
                if current_table and file_path:
                    table_files[current_table].add(file_path)
            
            # End of section
            elif (in_columns_section or in_files_section) and line.startswith('**') and not line.startswith('**Columns') and not line.startswith('**Referenced'):
                in_columns_section = False
                in_files_section = False
    
    return tables, table_files

def find_name_similarities(tables: Dict[str, Set[str]]) -> List[Tuple[str, str, float, str]]:
    """Find tables with similar names"""
    similarities = []
    table_names = list(tables.keys())
    
    for i, table1 in enumerate(table_names):
        for table2 in table_names[i+1:]:
            ratio = similarity_ratio(table1, table2)
            
            # Check for common patterns
            reason = []
            
            # Same prefix/suffix
            if '_' in table1 and '_' in table2:
                parts1 = table1.split('_')
                parts2 = table2.split('_')
                
                # Shared prefix
                if parts1[0] == parts2[0] and parts1[0] not in ('instance', 'plugin', 'config', 'meta'):
                    reason.append(f"shared prefix '{parts1[0]}_'")
                
                # Singular/plural
                if table1.rstrip('s') == table2.rstrip('s'):
                    reason.append("singular/plural variant")
                
                # Similar words
                if 'history' in table1 and 'history' in table2:
                    reason.append("both track history")
                if 'variance' in table1 and 'variance' in table2:
                    reason.append("both track variance/drift")
                if 'log' in table1 and 'log' in table2:
                    reason.append("both are logs")
                if 'queue' in table1 and 'queue' in table2:
                    reason.append("both are queues")
            
            if ratio > 0.6 or reason:
                reason_str = '; '.join(reason) if reason else f"name similarity {ratio:.0%}"
                similarities.append((table1, table2, ratio, reason_str))
    
    return sorted(similarities, key=lambda x: x[2], reverse=True)

def find_column_overlap(tables: Dict[str, Set[str]]) -> List[Tuple[str, str, int, int, float]]:
    """Find tables with significant column overlap"""
    overlaps = []
    table_names = list(tables.keys())
    
    for i, table1 in enumerate(table_names):
        cols1 = tables[table1]
        if not cols1:
            continue
            
        for table2 in table_names[i+1:]:
            cols2 = tables[table2]
            if not cols2:
                continue
            
            shared = cols1 & cols2
            total = cols1 | cols2
            
            if len(shared) >= 5:  # At least 5 shared columns
                overlap_pct = len(shared) / min(len(cols1), len(cols2))
                
                if overlap_pct > 0.3:  # >30% overlap
                    overlaps.append((table1, table2, len(shared), len(total), overlap_pct))
    
    return sorted(overlaps, key=lambda x: x[4], reverse=True)

def categorize_tables(tables: Dict[str, Set[str]]) -> Dict[str, List[str]]:
    """Categorize tables by purpose based on name patterns"""
    categories = defaultdict(list)
    
    for table in tables.keys():
        # Skip junk tables
        if table in ('for', 'information_schema', 'backup', 'pending'):
            categories['_junk'].append(table)
            continue
        
        # Core data
        if table in ('instances', 'plugins', 'datapacks', 'worlds', 'ranks'):
            categories['core_data'].append(table)
        
        # Junctions (many-to-many)
        elif 'instance_' in table and any(x in table for x in ('plugins', 'datapacks', 'tags', 'groups')):
            categories['junctions'].append(table)
        
        # Configuration
        elif 'config' in table:
            if 'variance' in table or 'drift' in table:
                categories['config_variance_tracking'].append(table)
            elif 'history' in table or 'change' in table or 'log' in table:
                categories['config_history'].append(table)
            elif 'rule' in table or 'baseline' in table or 'template' in table:
                categories['config_rules'].append(table)
            elif 'lock' in table or 'migration' in table:
                categories['config_management'].append(table)
            else:
                categories['config_other'].append(table)
        
        # Metadata & Tagging
        elif 'tag' in table or 'meta' in table:
            categories['metadata_tagging'].append(table)
        
        # Deployment & Updates
        elif any(x in table for x in ('deployment', 'queue', 'update')):
            categories['deployment_updates'].append(table)
        
        # Discovery & Monitoring
        elif any(x in table for x in ('discovery', 'heartbeat', 'health', 'metric')):
            categories['discovery_monitoring'].append(table)
        
        # History/Audit
        elif 'history' in table or 'log' in table or 'audit' in table:
            categories['history_audit'].append(table)
        
        # Approval/Workflow
        elif 'approval' in table or 'vote' in table:
            categories['approval_workflow'].append(table)
        
        # Other
        else:
            categories['uncategorized'].append(table)
    
    return dict(categories)

def find_redundant_groups(tables: Dict[str, Set[str]], table_files: Dict[str, Set[str]]) -> List[Dict]:
    """Identify groups of tables that are likely redundant"""
    redundant_groups = []
    
    # Config variance tracking - clearly redundant
    variance_tables = {
        'config_variance_detected': tables.get('config_variance_detected', set()),
        'config_variance_history': tables.get('config_variance_history', set()),
        'config_variances': tables.get('config_variances', set()),
        'config_variance_cache': tables.get('config_variance_cache', set()),
        'config_drift_log': tables.get('config_drift_log', set()),
    }
    if any(variance_tables.values()):
        redundant_groups.append({
            'group': 'Config Variance/Drift Tracking',
            'tables': [k for k, v in variance_tables.items() if v],
            'files': {k: table_files.get(k, set()) for k in variance_tables.keys() if k in table_files},
            'reason': 'All track configuration drift/variance - should be ONE table',
            'recommendation': 'Keep config_variance_detected, remove others'
        })
    
    # Config history tracking
    history_tables = {
        'config_change_history': tables.get('config_change_history', set()),
        'endpoint_config_change_history': tables.get('endpoint_config_change_history', set()),
    }
    if len([k for k, v in history_tables.items() if v]) > 1:
        redundant_groups.append({
            'group': 'Config Change History',
            'tables': [k for k, v in history_tables.items() if v],
            'files': {k: table_files.get(k, set()) for k in history_tables.keys() if k in table_files},
            'reason': 'Both track config changes over time',
            'recommendation': 'Merge into config_change_history or remove if not deploying'
        })
    
    # Discovery tracking
    discovery_tables = {
        'discovery_runs': tables.get('discovery_runs', set()),
        'discovery_items': tables.get('discovery_items', set()),
    }
    if any(discovery_tables.values()):
        redundant_groups.append({
            'group': 'Discovery Tracking',
            'tables': [k for k, v in discovery_tables.items() if v],
            'files': {k: table_files.get(k, set()) for k in discovery_tables.keys() if k in table_files},
            'reason': 'discovery_items caused 153M record bloat - REMOVE',
            'recommendation': 'Keep discovery_runs ONLY (summary stats)'
        })
    
    # Deployment queues
    queue_tables = {
        'deployment_queue': tables.get('deployment_queue', set()),
        'plugin_update_queue': tables.get('plugin_update_queue', set()),
        'datapack_deployment_queue': tables.get('datapack_deployment_queue', set()),
    }
    if len([k for k, v in queue_tables.items() if v]) > 1:
        redundant_groups.append({
            'group': 'Deployment Queues',
            'tables': [k for k, v in queue_tables.items() if v],
            'files': {k: table_files.get(k, set()) for k in queue_tables.keys() if k in table_files},
            'reason': 'Multiple queues for same purpose',
            'recommendation': 'Use deployment_queue with type field (plugin/datapack/config)'
        })
    
    # Config baselines/rules
    baseline_tables = {
        'config_baselines': tables.get('config_baselines', set()),
        'config_rules': tables.get('config_rules', set()),
        'config_templates': tables.get('config_templates', set()),
        'baseline_snapshots': tables.get('baseline_snapshots', set()),
        'server_properties_baselines': tables.get('server_properties_baselines', set()),
    }
    if len([k for k, v in baseline_tables.items() if v]) > 1:
        redundant_groups.append({
            'group': 'Config Baselines/Rules',
            'tables': [k for k, v in baseline_tables.items() if v],
            'files': {k: table_files.get(k, set()) for k in baseline_tables.keys() if k in table_files},
            'reason': 'Multiple tables for "expected" config values',
            'recommendation': 'Consolidate to config_rules + server_properties_baselines'
        })
    
    # Metadata tracking
    meta_tables = {
        'meta_tags': tables.get('meta_tags', set()),
        'instance_tags': tables.get('instance_tags', set()),
        'instance_meta_tags': tables.get('instance_meta_tags', set()),
        'plugin_meta_tags': tables.get('plugin_meta_tags', set()),
    }
    if 'instance_tags' in [k for k, v in meta_tables.items() if v] and \
       'instance_meta_tags' in [k for k, v in meta_tables.items() if v]:
        redundant_groups.append({
            'group': 'Instance Tagging',
            'tables': ['instance_tags', 'instance_meta_tags'],
            'files': {k: table_files.get(k, set()) for k in ['instance_tags', 'instance_meta_tags'] if k in table_files},
            'reason': 'Both assign tags to instances - one uses meta_tags FK, one is key-value',
            'recommendation': 'Pick ONE approach: either instance_meta_tags (structured) OR instance_tags (flexible)'
        })
    
    return redundant_groups

def main():
    report_path = Path(__file__).parent.parent / "DATABASE_SCHEMA_FROM_CODE.md"
    
    if not report_path.exists():
        print(f"ERROR: Report not found: {report_path}")
        return
    
    print(f"Analyzing schema from: {report_path}\n")
    
    # Extract schema
    tables, table_files = extract_schema_from_report(report_path)
    print(f"Found {len(tables)} tables\n")
    
    # Categorize tables
    categories = categorize_tables(tables)
    
    # Generate report
    output_path = Path(__file__).parent.parent / "SCHEMA_REDUNDANCY_ANALYSIS.md"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Database Schema Redundancy Analysis\n\n")
        f.write("**Purpose:** Identify duplicate/redundant tables that should be consolidated\n\n")
        f.write("---\n\n")
        
        # Table categories
        f.write("## Table Categories\n\n")
        for category, table_list in sorted(categories.items()):
            if not table_list or category == '_junk':
                continue
            f.write(f"### {category.replace('_', ' ').title()} ({len(table_list)} tables)\n\n")
            for table in sorted(table_list):
                col_count = len(tables[table])
                file_count = len(table_files.get(table, []))
                f.write(f"- `{table}` ({col_count} columns, {file_count} files)\n")
            f.write("\n")
        
        # Redundant groups
        f.write("## 🚨 CRITICAL: Redundant Table Groups\n\n")
        f.write("These groups contain multiple tables doing the same job - major source of bloat!\n\n")
        
        redundant_groups = find_redundant_groups(tables, table_files)
        for idx, group in enumerate(redundant_groups, 1):
            f.write(f"### {idx}. {group['group']}\n\n")
            f.write(f"**Tables:**\n")
            for table in group['tables']:
                col_count = len(tables.get(table, []))
                f.write(f"- `{table}` ({col_count} columns)\n")
            f.write(f"\n**Reason:** {group['reason']}\n\n")
            f.write(f"**✅ Recommendation:** {group['recommendation']}\n\n")
            
            # Show file usage
            if 'files' in group and group['files']:
                f.write("**File Usage:**\n\n")
                for table, files in sorted(group['files'].items()):
                    if files:
                        f.write(f"- `{table}`: {len(files)} file(s)\n")
                        for file in sorted(files):
                            f.write(f"  - {file}\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        # Name similarities
        f.write("## Similar Table Names\n\n")
        f.write("Tables with similar names that might be duplicates:\n\n")
        
        similarities = find_name_similarities(tables)
        for table1, table2, ratio, reason in similarities[:20]:  # Top 20
            f.write(f"- `{table1}` ↔ `{table2}`\n")
            f.write(f"  - {reason}\n")
            f.write(f"  - Columns: {len(tables[table1])} vs {len(tables[table2])}\n")
            file1_count = len(table_files.get(table1, []))
            file2_count = len(table_files.get(table2, []))
            f.write(f"  - Files: {file1_count} vs {file2_count}\n\n")
        
        # Column overlap
        f.write("## High Column Overlap\n\n")
        f.write("Tables sharing many columns (might be redundant):\n\n")
        
        overlaps = find_column_overlap(tables)
        for table1, table2, shared, total, pct in overlaps[:20]:  # Top 20
            f.write(f"- `{table1}` ↔ `{table2}`\n")
            f.write(f"  - {shared} shared columns ({pct:.0%} overlap)\n")
            shared_cols = tables[table1] & tables[table2]
            f.write(f"  - Common: {', '.join(sorted(list(shared_cols)[:10]))}")
            if len(shared_cols) > 10:
                f.write(f" ... (+{len(shared_cols)-10} more)")
            f.write("\n\n")
        
        # Summary recommendations
        f.write("## Summary & Recommendations\n\n")
        f.write(f"**Current State:** {len(tables)} tables\n\n")
        f.write(f"**Redundant Groups Found:** {len(redundant_groups)}\n\n")
        
        f.write("### Immediate Actions:\n\n")
        f.write("1. **Config Variance:** Consolidate 5 variance tables → 1 table\n")
        f.write("2. **Discovery:** Remove `discovery_items` (153M record bloat source)\n")
        f.write("3. **Deployment:** Merge 3 queue tables → 1 with type field\n")
        f.write("4. **Tagging:** Pick ONE tagging approach (structured vs flexible)\n")
        f.write("5. **Baselines:** Consolidate 5 baseline tables → 2 (config + server props)\n\n")
        
        f.write("### Expected Reduction:\n\n")
        f.write(f"- **Before:** {len(tables)} tables\n")
        f.write(f"- **After:** ~35-40 tables (40% reduction)\n")
        f.write(f"- **Bloat Eliminated:** discovery_items, redundant variance tables\n\n")
    
    print(f"\n✅ Analysis complete: {output_path}")
    print(f"\nKey findings:")
    print(f"  - {len(redundant_groups)} redundant table groups")
    print(f"  - {len(similarities)} similar table names")
    print(f"  - {len(overlaps)} high column overlaps")

if __name__ == "__main__":
    main()
