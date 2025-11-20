#!/usr/bin/env python4
"""
Fix drift detector type errors
Adds isinstance() checks to prevent list/dict comparison errors
"""

import sys
from pathlib import Path

def fix_drift_detector():
    """Add type checks to drift detector"""
    
    file_path = Path('/opt/archivesmp-config-manager/src/analyzers/drift_detector.py')
    
    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return 1
    
    print(f"Reading {file_path}...")
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if already fixed
    if 'isinstance(baseline_plugin, dict)' in content:
        print(" drift_detector.py already has type checks - no changes needed")
        return 0
    
    # Apply fixes
    lines = content.split('\n')
    output = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        output.append(line)
        
        # Fix 1: After "for plugin_name, baseline_plugin in baseline.items():"
        if 'for plugin_name, baseline_plugin in baseline.items():' in line:
            # Get indentation
            indent = len(line) - len(line.lstrip())
            next_indent = ' ' * (indent + 4)
            
            # Add type check
            output.append(f'{next_indent}# Skip if baseline_plugin is not a dict (e.g., markdown parsing artifacts)')
            output.append(f'{next_indent}if not isinstance(baseline_plugin, dict):')
            output.append(f'{next_indent}    continue')
            output.append('')
        
        # Fix 2: After "for config_file, baseline_config in baseline_plugin.items():"
        elif 'for config_file, baseline_config in baseline_plugin.items():' in line:
            # Get indentation
            indent = len(line) - len(line.lstrip())
            next_indent = ' ' * (indent + 4)
            
            # Add type check for current_plugin
            output.append(f'{next_indent}# Skip if current_plugin is not a dict')
            output.append(f'{next_indent}if plugin_name not in current or not isinstance(current.get(plugin_name), dict):')
            output.append(f'{next_indent}    continue')
            output.append('')
        
        i += 1
    
    # Write back
    print(f"Writing fixes to {file_path}...")
    with open(file_path, 'w') as f:
        f.write('\n'.join(output))
    
    print(" Fixed drift_detector.py")
    print("\nRestart the agent:")
    print("  sudo systemctl restart homeamp-agent")
    return 0

if __name__ == '__main__':
    sys.exit(fix_drift_detector())
