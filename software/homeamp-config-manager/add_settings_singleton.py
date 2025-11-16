#!/usr/bin/env python3
"""Quick fix to add settings singleton"""

with open('src/core/settings.py', 'r') as f:
    content = f.read()

if 'settings = get_settings()' not in content:
    content += '\n\n# Global settings instance\nsettings = get_settings()\n'
    
    with open('src/core/settings.py', 'w') as f:
        f.write(content)
    
    print("Added settings singleton")
else:
    print("Already has settings singleton")
