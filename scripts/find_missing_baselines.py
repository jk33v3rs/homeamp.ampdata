#!/usr/bin/env python3
"""Find plugins in deployment matrix that don't have universal config files"""

import csv
from pathlib import Path

# Load deployment matrix plugins
matrix_file = Path(r'e:\homeamp.ampdata\utildata\ActualDBs\deployment_matrix.csv')
with open(matrix_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    matrix_plugins = {row['plugin_name'].strip() for row in reader}

# Load universal config files
configs_dir = Path(r'e:\homeamp.ampdata\utildata\plugin_universal_configs')
config_files = list(configs_dir.glob('*_universal_config.md'))
config_plugins = {f.stem.replace('_universal_config', '') for f in config_files}

# Find missing
missing = matrix_plugins - config_plugins
has_config = matrix_plugins & config_plugins

print(f"=== BASELINE STATUS ===")
print(f"Total plugins in deployment matrix: {len(matrix_plugins)}")
print(f"Plugins with universal configs: {len(has_config)}")
print(f"Plugins MISSING configs: {len(missing)}")
print()

print(f"=== PLUGINS WITH CONFIGS ({len(has_config)}) ===")
for plugin in sorted(has_config):
    print(f"  ✅ {plugin}")

print()
print(f"=== MISSING CONFIGS ({len(missing)}) ===")
for plugin in sorted(missing):
    print(f"  ❌ {plugin}")
