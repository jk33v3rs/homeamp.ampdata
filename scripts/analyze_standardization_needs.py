#!/usr/bin/env python3
"""
Identify plugins that need better standardization
"""

import json
from pathlib import Path

# Load config data
universal = json.load(open('e:/homeamp.ampdata/utildata/universal_configs_analysis_UPDATED.json'))
variable = json.load(open('e:/homeamp.ampdata/utildata/variable_configs_analysis_UPDATED.json'))

# Analyze each plugin with variables
plugins_needing_work = []

for plugin in sorted(variable.keys()):
    var_count = sum(len(settings) for settings in variable[plugin].values())
    uni_count = len(universal.get(plugin, {}))
    ratio = var_count / uni_count if uni_count > 0 else float('inf')
    
    # Get instance count from variable config
    instances = set()
    for setting_variations in variable[plugin].values():
        instances.update(setting_variations.keys())
    instance_count = len(instances)
    
    plugins_needing_work.append({
        'plugin': plugin,
        'universal': uni_count,
        'variable': var_count,
        'ratio': ratio,
        'instances': instance_count
    })

# Sort by ratio (highest first = most variation relative to universal)
plugins_needing_work.sort(key=lambda x: x['ratio'], reverse=True)

print("=" * 80)
print("PLUGINS NEEDING STANDARDIZATION (sorted by variable/universal ratio)")
print("=" * 80)
print(f"\n{'Plugin':<25} {'Instances':<10} {'Universal':<10} {'Variable':<10} {'Ratio':<10} {'Priority'}")
print("-" * 80)

for p in plugins_needing_work:
    if p['ratio'] > 1.0:
        priority = "🔴 HIGH"
    elif p['ratio'] > 0.5:
        priority = "🟡 MED"
    else:
        priority = "🟢 LOW"
    
    print(f"{p['plugin']:<25} {p['instances']:<10} {p['universal']:<10} {p['variable']:<10} {p['ratio']:<10.3f} {priority}")

# Detailed analysis of high-priority plugins
print("\n" + "=" * 80)
print("HIGH PRIORITY PLUGINS (ratio > 1.0) - Need Immediate Standardization")
print("=" * 80)

for p in plugins_needing_work:
    if p['ratio'] > 1.0:
        plugin_name = p['plugin']
        print(f"\n{plugin_name} ({p['instances']} instances):")
        print(f"  - {p['universal']} universal settings")
        print(f"  - {p['variable']} variable settings")
        print(f"  - {p['ratio']:.1f}x more variables than universal (should be mostly universal!)")
        
        # Show which settings vary
        print(f"\n  Variable settings breakdown:")
        for setting_key, instances_dict in sorted(variable[plugin_name].items())[:10]:  # Show first 10
            unique_values = len(set(str(v) for v in instances_dict.values()))
            print(f"    - {setting_key}: {unique_values} different values across {len(instances_dict)} instances")
        
        if len(variable[plugin_name]) > 10:
            print(f"    ... and {len(variable[plugin_name]) - 10} more variable settings")

print("\n" + "=" * 80)
print("RECOMMENDATION: Create standardization plan for plugins with ratio > 0.5")
print("=" * 80)
