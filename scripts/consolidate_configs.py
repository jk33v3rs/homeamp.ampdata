#!/usr/bin/env python3
"""
Consolidate Plugin Configurations

Merges configs from addon/compat plugins into their parent plugin:
- QuickShop addons → QuickShop-Hikari
- BentoBox extensions → BentoBox

This prevents predictable confusion and makes configs easier to manage.
"""

import json
from pathlib import Path
from typing import Dict, Any

# Load categorization
repo_root = Path(__file__).parent.parent
categorization_file = repo_root / 'plugin_platform_categorization.json'

with open(categorization_file, 'r') as f:
    categorization = json.load(f)

CONSOLIDATED = categorization['consolidated']

def consolidate_universal_configs():
    """Consolidate universal configs into parent plugins"""
    
    universal_file = repo_root / 'utildata' / 'universal_configs_analysis.json'
    
    with open(universal_file, 'r') as f:
        universal = json.load(f)
    
    print("Consolidating Universal Configs...")
    print()
    
    consolidated_universal = {}
    
    for plugin_name, config in universal.items():
        # Check if this plugin should be consolidated
        parent = None
        for parent_plugin, children in CONSOLIDATED.items():
            if plugin_name in children:
                parent = parent_plugin
                break
        
        if parent:
            # Merge into parent
            if parent not in consolidated_universal:
                consolidated_universal[parent] = {}
            
            # Prefix keys with addon name to avoid conflicts
            for key, value in config.items():
                prefixed_key = f"{plugin_name}.{key}"
                consolidated_universal[parent][prefixed_key] = value
            
            print(f"  {plugin_name} → {parent}")
        else:
            # Keep as-is
            consolidated_universal[plugin_name] = config
    
    # Save
    output_file = repo_root / 'utildata' / 'universal_configs_consolidated.json'
    with open(output_file, 'w') as f:
        json.dump(consolidated_universal, f, indent=2)
    
    print()
    print(f"Saved to: {output_file}")
    print(f"Original: {len(universal)} plugins")
    print(f"Consolidated: {len(consolidated_universal)} plugins")
    print()


def consolidate_variable_configs():
    """Consolidate variable configs into parent plugins"""
    
    variable_file = repo_root / 'utildata' / 'variable_configs_analysis_UPDATED.json'
    
    with open(variable_file, 'r') as f:
        variable = json.load(f)
    
    print("Consolidating Variable Configs...")
    print()
    
    consolidated_variable = {}
    
    for plugin_name, config_keys in variable.items():
        # Check if this plugin should be consolidated
        parent = None
        for parent_plugin, children in CONSOLIDATED.items():
            if plugin_name in children:
                parent = parent_plugin
                break
        
        if parent:
            # Merge into parent
            if parent not in consolidated_variable:
                consolidated_variable[parent] = {}
            
            # Prefix keys with addon name
            for key, instances in config_keys.items():
                prefixed_key = f"{plugin_name}.{key}"
                consolidated_variable[parent][prefixed_key] = instances
            
            print(f"  {plugin_name} → {parent}")
        else:
            # Keep as-is
            consolidated_variable[plugin_name] = config_keys
    
    # Save
    output_file = repo_root / 'utildata' / 'variable_configs_consolidated.json'
    with open(output_file, 'w') as f:
        json.dump(consolidated_variable, f, indent=2)
    
    print()
    print(f"Saved to: {output_file}")
    print(f"Original: {len(variable)} plugins")
    print(f"Consolidated: {len(consolidated_variable)} plugins")
    print()


def update_expectations_structure():
    """
    Update expectations directory structure to separate by platform:
    
    data/expectations/
      ├── paper/
      │   ├── universal_configs.json
      │   └── variable_configs.json
      ├── velocity/
      │   ├── universal_configs.json
      │   └── variable_configs.json
      └── geyser/
          ├── universal_configs.json
          └── variable_configs.json
    """
    
    print("Creating Platform-Separated Expectations Structure...")
    print()
    
    expectations_dir = repo_root / 'software' / 'homeamp-config-manager' / 'data' / 'expectations'
    
    # Create platform directories
    for platform in ['paper', 'velocity', 'geyser']:
        platform_dir = expectations_dir / platform
        platform_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {platform_dir}")
    
    # Load consolidated configs
    with open(repo_root / 'utildata' / 'universal_configs_consolidated.json', 'r') as f:
        universal = json.load(f)
    
    with open(repo_root / 'utildata' / 'variable_configs_consolidated.json', 'r') as f:
        variable = json.load(f)
    
    # Split by platform
    platforms = categorization['platforms']
    
    for platform_name in ['paper', 'velocity', 'geyser']:
        platform_plugins = set(platforms[platform_name]['plugins'])
        
        # Filter configs for this platform
        platform_universal = {
            plugin: config 
            for plugin, config in universal.items() 
            if plugin in platform_plugins
        }
        
        platform_variable = {
            plugin: config 
            for plugin, config in variable.items() 
            if plugin in platform_plugins
        }
        
        # Save
        platform_dir = expectations_dir / platform_name
        
        with open(platform_dir / 'universal_configs.json', 'w') as f:
            json.dump(platform_universal, f, indent=2)
        
        with open(platform_dir / 'variable_configs.json', 'w') as f:
            json.dump(platform_variable, f, indent=2)
        
        print(f"  {platform_name}: {len(platform_universal)} universal, {len(platform_variable)} variable")
    
    print()
    print("Platform-separated expectations created!")
    print()


if __name__ == '__main__':
    print("=" * 80)
    print("Plugin Configuration Consolidation")
    print("=" * 80)
    print()
    
    consolidate_universal_configs()
    consolidate_variable_configs()
    update_expectations_structure()
    
    print("=" * 80)
    print("DONE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review consolidated configs in utildata/*_consolidated.json")
    print("  2. Update drift detection to use platform-specific expectations")
    print("  3. Update config deployment to check plugin platform")
    print()
