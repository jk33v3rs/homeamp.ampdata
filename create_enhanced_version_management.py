#!/usr/bin/env python3
"""
Extract bulk plugin definitions from universal configs and organize into native file structure
"""

import json
import yaml
import shutil
from pathlib import Path
from collections import defaultdict

# Load universal configs
universal_file = Path('e:/homeamp.ampdata/utildata/universal_configs_analysis_UPDATED.json')
u = json.load(open(universal_file, encoding='utf-8'))

# Define which plugins have bulk definitions to extract
bulk_definition_plugins = {
    'Jobs': {
        'category': 'jobs',
        'subfolders': ['jobs'],  # jobs/*.yml files
        'source_instance': 'DEV01',  # Use DEV01 as the template
    },
    'Quests': {
        'category': 'quests',
        'subfolders': ['quests', 'actions', 'conditions'],
        'source_instance': 'DEV01',
    },
    'ExcellentQuests': {
        'category': 'quests',
        'subfolders': ['quests', 'objectives'],
        'source_instance': 'CLIP01',
    },
    'ExcellentChallenges': {
        'category': 'challenges',
        'subfolders': ['challenges', 'categories'],
        'source_instance': 'CLIP01',
    },
    'EliteMobs': {
        'category': 'mmo',
        'subfolders': ['custombosses', 'customitems', 'customquests', 'powers', 'events'],
        'source_instance': 'EVO01',
    },
    'Citizens': {
        'category': 'mmo',
        'subfolders': ['saves', 'templates'],
        'source_instance': 'EVO01',
    },
    'mcMMO': {
        'category': 'mmo',
        'subfolders': ['skills'],
        'source_instance': 'DEV01',
    },
    'CombatPets': {
        'category': 'mmo/pets',
        'subfolders': ['pets'],
        'source_instance': 'EVO01',
    },
}

# Base paths
utildata_hetzner = Path('e:/homeamp.ampdata/utildata/HETZNER')
utildata_ovh = Path('e:/homeamp.ampdata/utildata/OVH')
output_base = Path('e:/homeamp.ampdata/data/baselines/plugin_definitions')

print('=' * 80)
print('EXTRACTING BULK PLUGIN DEFINITIONS')
print('=' * 80)

# Create output directory
output_base.mkdir(parents=True, exist_ok=True)

total_removed_from_universal = 0
total_files_copied = 0

# Process each plugin
for plugin_name, config in bulk_definition_plugins.items():
    category = config['category']
    subfolders = config['subfolders']
    source_instance = config['source_instance']
    
    print(f'\n{plugin_name}:')
    print(f'  Category: {category}')
    print(f'  Source: {source_instance}')
    
    # Find source plugin directory
    source_path = None
    for base_path in [utildata_hetzner, utildata_ovh]:
        potential_path = base_path / source_instance / 'Minecraft' / 'plugins' / plugin_name
        if potential_path.exists():
            source_path = potential_path
            break
    
    if not source_path:
        print(f'  ❌ Source not found!')
        continue
    
    # Create output directory
    output_plugin_dir = output_base / category / plugin_name.lower()
    output_plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy subfolders
    files_copied = 0
    for subfolder in subfolders:
        source_subfolder = source_path / subfolder
        if source_subfolder.exists():
            dest_subfolder = output_plugin_dir / subfolder
            if dest_subfolder.exists():
                shutil.rmtree(dest_subfolder)
            shutil.copytree(source_subfolder, dest_subfolder)
            
            # Count files
            file_count = len(list(dest_subfolder.rglob('*.*')))
            files_copied += file_count
            print(f'  ✓ Copied {subfolder}/ ({file_count} files)')
    
    total_files_copied += files_copied
    
    # Remove bulk definitions from universal config
    if plugin_name in u:
        keys_to_remove = []
        for key in u[plugin_name].keys():
            # Remove keys that start with any of the subfolders
            if any(key.lower().startswith(f'{sf}/') or key.lower().startswith(f'{sf}.') 
                   for sf in subfolders):
                keys_to_remove.append(key)
        
        if keys_to_remove:
            for key in keys_to_remove:
                del u[plugin_name][key]
            print(f'  ✓ Removed {len(keys_to_remove)} definition keys from universal config')
            total_removed_from_universal += len(keys_to_remove)

# Save updated universal configs
print('\n' + '=' * 80)
print('UPDATING UNIVERSAL CONFIGS')
print('=' * 80)

with open(universal_file, 'w', encoding='utf-8') as f:
    json.dump(u, f, indent=2, sort_keys=True)

original_file = Path('e:/homeamp.ampdata/utildata/universal_configs_analysis.json')
with open(original_file, 'w', encoding='utf-8') as f:
    json.dump(u, f, indent=2, sort_keys=True)

print(f'\n✓ Removed {total_removed_from_universal} bulk definition entries from universal configs')
print(f'✓ Copied {total_files_copied} native definition files to plugin_definitions/')

# Show final plugin counts
print('\n' + '=' * 80)
print('UPDATED PLUGIN SETTINGS COUNTS')
print('=' * 80)
for plugin in sorted(u.keys()):
    if plugin in bulk_definition_plugins:
        print(f'{plugin:30s}: {len(u[plugin]):6d} settings (bulk definitions removed)')

print('\n' + '=' * 80)
print('PLUGIN DEFINITIONS DIRECTORY STRUCTURE')
print('=' * 80)
print(f'\n{output_base}/')
for category_dir in sorted(output_base.iterdir()):
    if category_dir.is_dir():
        print(f'  {category_dir.name}/')
        for plugin_dir in sorted(category_dir.rglob('*')):
            if plugin_dir.is_dir():
                rel_path = plugin_dir.relative_to(output_base)
                indent = '    ' * len(rel_path.parts)
                file_count = len(list(plugin_dir.glob('*.*')))
                if file_count > 0:
                    print(f'{indent}{plugin_dir.name}/ ({file_count} files)')
                else:
                    print(f'{indent}{plugin_dir.name}/')
