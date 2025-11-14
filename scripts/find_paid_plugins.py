import os
import re

paid = []
path = 'data/plugin_definitions'

for f in os.listdir(path):
    if f.endswith('.md'):
        filepath = os.path.join(path, f)
        with open(filepath, encoding='utf-8') as file:
            content = file.read()
            lines = content.split('\n')
            
            # Check notes field around line 10 for paid/premium
            notes_section = '\n'.join(lines[8:12]) if len(lines) > 12 else content
            
            # Skip if explicitly marked as FREE
            if 'FREE base plugin' in notes_section or 'Free to download' in notes_section:
                continue
                
            # Check for paid indicators
            if re.search(r'notes:.*["\'].*Paid', notes_section, re.IGNORECASE):
                paid.append(f.replace('.md', ''))

print(f'Paid plugins found: {len(paid)}')
for p in sorted(paid):
    print(f'  {p}')
