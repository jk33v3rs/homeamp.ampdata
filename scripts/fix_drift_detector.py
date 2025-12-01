#!/usr/bin/env python3
"""Fix drift_detector.py by adding type checks"""

fix_code = '''
# Read the file
with open('/opt/archivesmp-config-manager/src/analyzers/drift_detector.py', 'r') as f:
    lines = f.readlines()

# Find and fix the lines
output = []
i = 0
while i < len(lines):
    line = lines[i]
    output.append(line)
    
    # After "for plugin_name, baseline_plugin in baseline.items():"
    if 'for plugin_name, baseline_plugin in baseline.items():' in line:
        # Add type check if not already there
        if i + 1 < len(lines) and 'Skip if baseline_plugin is not a dict' not in lines[i + 1]:
            indent = ' ' * 16  # 4 spaces * 4 levels
            output.append(f'{indent}# Skip if baseline_plugin is not a dict (e.g., markdown parsing artifacts)\\n')
            output.append(f'{indent}if not isinstance(baseline_plugin, dict):\\n')
            output.append(f'{indent}    continue\\n')
            output.append(f'{indent}\\n')
    
    # After "for config_file, baseline_config in baseline_plugin.items():"
    elif 'for config_file, baseline_config in baseline_plugin.items():' in line:
        # Add type check if not already there
        if i + 1 < len(lines) and 'Skip if current_plugin is not a dict' not in lines[i + 1]:
            indent = ' ' * 20  # 4 spaces * 5 levels
            output.append(f'{indent}# Skip if current_plugin is not a dict\\n')
            output.append(f'{indent}if not isinstance(current_plugin, dict):\\n')
            output.append(f'{indent}    continue\\n')
    
    i += 1

# Write back
with open('/opt/archivesmp-config-manager/src/analyzers/drift_detector.py', 'w') as f:
    f.writelines(output)

print("Fixed drift_detector.py")
'''

print(fix_code)
