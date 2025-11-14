#!/usr/bin/env python3
"""
Extract universal configs for the 29 missing plugins
"""

import json
import yaml
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, Set

# Plugins to extract (excluding .paper-remapped and spark)
PLUGINS_TO_EXTRACT = [
    'autoviaupdater', 'BattleRoyale', 'BentoBox', 'BoxedEyes', 'CreativeSuite', 
    'CSMC', 'Duels', 'EternalTD', 'ExcellentQuests', 'floodgate', 'GregoRail', 
    'Hurricane', 'HuskTowns', 'Jobs', 'LevelledMobs', 'LibsDisguises', 'Minetorio', 
    'PAPIProxyBridge', 'PhantomWorlds', 'qscompat-worldedit', 'vcustombrand', 
    'velocitab', 'viarewind', 'VoidSpawn', 'vserverinfo', 'vwhitelist'
]

# Server directories
HETZNER_PATH = Path('e:/homeamp.ampdata/utildata/HETZNER')
OVH_PATH = Path('e:/homeamp.ampdata/utildata/OVH')

def load_config_file(file_path):
    """Load a configuration file (YAML, JSON, or properties)."""
    # Convert Path to string
    file_path_str = str(file_path)
    
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            if file_path_str.endswith('.json'):
                try:
                    return json.load(f)
                except:
                    return {}
            elif file_path_str.endswith('.properties') or file_path_str.endswith('.conf'):
                props = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        props[key.strip()] = value.strip()
                return props
            else:  # YAML
                try:
                    return yaml.safe_load(f) or {}
                except:
                    # Silently skip malformed YAML (BentoBox, ExcellentQuests, etc.)
                    return {}
    except KeyboardInterrupt:
        raise
    except:
        pass
    return {}

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary with dot notation"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def extract_plugin_configs(plugin_name: str) -> tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Extract universal configs and deviations for a plugin
    
    Returns:
        (universal_config, variable_config)
    """
    # Collect all configs from all instances
    instance_configs = {}
    
    instances_found = 0
    for server_base in [HETZNER_PATH, OVH_PATH]:
        for server_dir in server_base.iterdir():
            if not server_dir.is_dir():
                continue
                
            plugin_path = server_dir / 'Minecraft' / 'plugins' / plugin_name
            if not plugin_path.exists():
                continue
            
            instance_name = server_dir.name
            instance_configs[instance_name] = {}
            instances_found += 1
            
            # Find all config files
            for config_file in plugin_path.rglob('*.yml'):
                relative_path = config_file.relative_to(plugin_path)
                config_key = str(relative_path).replace('\\', '/').replace('.yml', '')
                
                config_data = load_config_file(config_file)
                if config_data:
                    flattened = flatten_dict(config_data)
                    instance_configs[instance_name][config_key] = flattened
            
            # Also check for .yaml, .json, .properties
            for ext in ['.yaml', '.json', '.properties', '.conf']:
                for config_file in plugin_path.rglob(f'*{ext}'):
                    relative_path = config_file.relative_to(plugin_path)
                    config_key = str(relative_path).replace('\\', '/').replace(ext, '')
                    
                    if config_key not in instance_configs[instance_name]:
                        config_data = load_config_file(config_file)
                        if config_data:
                            flattened = flatten_dict(config_data)
                            instance_configs[instance_name][config_key] = flattened
    
    # Remove empty instances
    instance_configs = {k: v for k, v in instance_configs.items() if v}
    
    if not instance_configs:
        return {}, {}
    
    # For single instance, everything is universal
    if len(instance_configs) == 1:
        instance_name = list(instance_configs.keys())[0]
        return instance_configs[instance_name], {}
    
    # For multiple instances, find universal settings
    universal_config = {}
    variable_config = defaultdict(lambda: defaultdict(dict))
    
    # Collect all config file keys across all instances
    all_config_keys = set()
    for instance_data in instance_configs.values():
        all_config_keys.update(instance_data.keys())
    
    for config_key in all_config_keys:
        # Collect all setting keys for this config file
        all_setting_keys = set()
        for instance_data in instance_configs.values():
            if config_key in instance_data:
                all_setting_keys.update(instance_data[config_key].keys())
        
        for setting_key in all_setting_keys:
            values_by_instance = {}
            
            for instance_name, instance_data in instance_configs.items():
                if config_key in instance_data and setting_key in instance_data[config_key]:
                    values_by_instance[instance_name] = instance_data[config_key][setting_key]
            
            # Check if all instances have the same value
            unique_values = set(str(v) for v in values_by_instance.values())
            
            if len(unique_values) == 1:
                # Universal setting
                full_key = f"{config_key}.{setting_key}" if config_key else setting_key
                universal_config[full_key] = list(values_by_instance.values())[0]
            else:
                # Variable setting
                full_key = f"{config_key}.{setting_key}" if config_key else setting_key
                variable_config[plugin_name][full_key] = values_by_instance
    
    return universal_config, dict(variable_config)

def main():
    print("Extracting configs for 27 missing plugins...")
    
    universal_configs = {}
    variable_configs = {}
    
    for plugin_name in sorted(PLUGINS_TO_EXTRACT):
        print(f"\nProcessing {plugin_name}...")
        
        universal, variable = extract_plugin_configs(plugin_name)
        
        if universal:
            universal_configs[plugin_name] = universal
            print(f"[OK] Found {len(universal)} universal settings")
        
        if variable:
            variable_configs.update(variable)
            total_deviations = sum(len(v) for v in variable.get(plugin_name, {}).values())
            print(f"[WARN] Found {total_deviations} variable settings")
        
        if not universal and not variable:
            print(f"so [SKIP] No config files found")
    
    # Save to files
    print("\n\nSaving results...")
    
    # Merge with existing universal configs
    existing_universal_path = Path('e:/homeamp.ampdata/utildata/universal_configs_analysis.json')
    if existing_universal_path.exists():
        with open(existing_universal_path, 'r', encoding='utf-8') as f:
            existing_universal = json.load(f)
        existing_universal.update(universal_configs)
        universal_configs = existing_universal
    
    # Merge with existing variable configs
    existing_variable_path = Path('e:/homeamp.ampdata/utildata/variable_configs_analysis.json')
    if existing_variable_path.exists():
        with open(existing_variable_path, 'r', encoding='utf-8') as f:
            existing_variable = json.load(f)
        existing_variable.update(variable_configs)
        variable_configs = existing_variable
    
    # Write updated files
    with open('e:/homeamp.ampdata/utildata/universal_configs_analysis_UPDATED.json', 'w', encoding='utf-8') as f:
        json.dump(universal_configs, f, indent=2, sort_keys=True)
    
    with open('e:/homeamp.ampdata/utildata/variable_configs_analysis_UPDATED.json', 'w', encoding='utf-8') as f:
        json.dump(variable_configs, f, indent=2, sort_keys=True)
    
    print(f"\n[OK] Total plugins with universal configs: {len(universal_configs)}")
    print(f"[OK] Total plugins with variable configs: {len(variable_configs)}")
    print(f"\nSaved to:")
    print(f"  - universal_configs_analysis_UPDATED.json")
    print(f"  - variable_configs_analysis_UPDATED.json")

if __name__ == '__main__':
    main()
