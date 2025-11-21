#!/usr/bin/env python3
"""
Fix config_variances → config_variance_detected table name in production
Run this on the YunoHost server to apply the database table name fix
"""

import sys
import re

def fix_table_name(file_path):
    """Replace all occurrences of config_variances with config_variance_detected"""
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Store original for comparison
        original_content = content
        
        # Replace all occurrences
        # Use word boundaries to avoid partial matches
        content = re.sub(r'\bconfig_variances\b', 'config_variance_detected', content)
        
        # Count changes
        changes = len(re.findall(r'\bconfig_variance_detected\b', content))
        
        if content == original_content:
            print("No changes needed - file already correct")
            return 0
        
        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Successfully updated {changes} occurrences of table name")
        print(f"   Changed: config_variances -> config_variance_detected")
        return 0
        
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"Error: Permission denied: {file_path}", file=sys.stderr)
        print("   Try running with sudo", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    # Production path
    file_path = "/opt/archivesmp-config-manager/software/homeamp-config-manager/src/api/plugin_configurator_endpoints.py"
    
    print(f"Fixing table name in: {file_path}")
    print("-" * 60)
    
    sys.exit(fix_table_name(file_path))
