#!/usr/bin/env python3
"""Analyze JobListings variable configs to identify customization patterns"""

import json

v = json.load(open('e:/homeamp.ampdata/utildata/variable_configs_analysis_UPDATED.json'))
jl = v['JobListings']

print('=' * 80)
print('JobListings Variable Settings Analysis')
print('=' * 80)

# Analyze all settings
for setting, instances in sorted(jl.items()):
    unique_vals = set(str(val) for val in instances.values())
    
    print(f'\n{setting}:')
    for val in sorted(unique_vals):
        inst_list = [inst for inst, v in instances.items() if str(v) == val]
        print(f'  "{val}" → {len(inst_list)} instances: {", ".join(sorted(inst_list))}')

# Look for the "odd one out" pattern
print('\n' + '=' * 80)
print('PATTERN ANALYSIS: Looking for "one different, rest same"')
print('=' * 80)

customized_instance = None
generic_instances = None

for setting, instances in jl.items():
    values_count = {}
    for inst, val in instances.items():
        val_str = str(val)
        if val_str not in values_count:
            values_count[val_str] = []
        values_count[val_str].append(inst)
    
    # Check if there's a 9-1 split (one customized, 9 generic)
    if len(values_count) == 2:
        counts = [len(insts) for insts in values_count.values()]
        if 1 in counts and 9 in counts:
            # Found a potential customization
            for val, insts in values_count.items():
                if len(insts) == 1:
                    if customized_instance is None:
                        customized_instance = insts[0]
                    elif customized_instance == insts[0]:
                        print(f'✓ {setting}: {customized_instance} is different from the other 9')
                elif len(insts) == 9:
                    if generic_instances is None:
                        generic_instances = set(insts)

if customized_instance:
    print(f'\n{"=" * 80}')
    print(f'CONCLUSION: {customized_instance} appears to be CUSTOMIZED')
    print(f'The other 9 instances appear to have DEFAULT/GENERIC configs')
    print(f'{"=" * 80}')
else:
    print('\nNo clear 1-vs-9 pattern found. Checking for other splits...')
    
    # Check for 2-vs-8 split
    for setting, instances in jl.items():
        values_count = {}
        for inst, val in instances.items():
            val_str = str(val)
            if val_str not in values_count:
                values_count[val_str] = []
            values_count[val_str].append(inst)
        
        if len(values_count) == 2:
            counts = sorted([len(insts) for insts in values_count.values()])
            if counts == [2, 8]:
                print(f'\n{setting}:')
                for val, insts in values_count.items():
                    print(f'  {len(insts)} instances ({", ".join(sorted(insts))}): {val}')
