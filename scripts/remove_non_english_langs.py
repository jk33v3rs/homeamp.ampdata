t#!/usr/bin/env python3
"""Remove all locale/language entries from universal configs completely"""

import json
from pathlib import Path

# Load current universal configs
input_file = Path('e:/homeamp.ampdata/utildata/universal_configs_analysis_UPDATED.json')
u = json.load(open(input_file, encoding='utf-8'))

total_removed = 0
plugin_stats = {}

# Patterns that indicate locale/language/translation content
locale_patterns = [
    'locale',       # Matches locale/, locales/, /locale/, /locales/
    'translatable',
    'lang',
    'language',
    'translation',
    'message',
    'words_',  # Jobs plugin uses Words_en.yml, Words_zh.yml etc
]

# Process each plugin
for plugin_name, settings in u.items():
    keys_to_remove = []
    
    for key in settings.keys():
        key_lower = key.lower()
        
        # Check if this key is locale/language related
        if any(pattern in key_lower for pattern in locale_patterns):
            keys_to_remove.append(key)
    
    # Remove the keys
    if keys_to_remove:
        plugin_stats[plugin_name] = len(keys_to_remove)
        for key in keys_to_remove:
            del settings[key]
            total_removed += 1

# Report
print('=' * 80)
print('REMOVED ALL LOCALE/LANGUAGE ENTRIES')
print('=' * 80)
for plugin, count in sorted(plugin_stats.items(), key=lambda x: x[1], reverse=True):
    print(f'{plugin:30s}: {count:6d} entries removed')

print(f'\nTotal removed: {total_removed:,} locale/language entries')

# Save cleaned version
output_file = Path('e:/homeamp.ampdata/utildata/universal_configs_analysis_UPDATED.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(u, f, indent=2, sort_keys=True)

print(f'\nSaved cleaned configs to: {output_file}')

# Also update the non-UPDATED version
original_file = Path('e:/homeamp.ampdata/utildata/universal_configs_analysis.json')
if original_file.exists():
    with open(original_file, 'w', encoding='utf-8') as f:
        json.dump(u, f, indent=2, sort_keys=True)
    print(f'Also updated: {original_file}')

# Show final plugin counts
print('\n' + '=' * 80)
print('FINAL PLUGIN SETTINGS COUNTS (after locale removal)')
print('=' * 80)
for plugin, settings in sorted(u.items(), key=lambda x: len(x[1]), reverse=True)[:20]:
    print(f'{plugin:30s}: {len(settings):6d} settings')
