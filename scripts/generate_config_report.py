import json
import os

# Load data
universal_json = set(json.load(open('utildata/universal_configs_analysis.json')).keys())
variable_json = set(json.load(open('utildata/variable_configs_analysis.json')).keys())
universal_md = {f.replace('_universal_config.md', '') for f in os.listdir('utildata/plugin_universal_configs') if f.endswith('_universal_config.md')}

# Generate report
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('# Plugin Configuration Status Report\n\n')
    f.write('**Generated**: November 13, 2025\n\n')
    
    f.write('## Summary\n\n')
    f.write(f'- **Total plugins with universal configs (JSON)**: {len(universal_json)}\n')
    f.write(f'- **Total plugins with variable configs (JSON)**: {len(variable_json)}\n')
    f.write(f'- **Total plugins with markdown baseline files**: {len(universal_md)}\n')
    f.write(f'- **Plugins with BOTH universal AND variable**: {len(universal_json.intersection(variable_json))}\n')
    f.write(f'- **Total unique plugins tracked**: {len(universal_json.union(variable_json))}\n\n')
    
    f.write('---\n\n')
    f.write('## Plugins with Universal Configs (82 total)\n\n')
    f.write('These plugins have baseline configs in `utildata/universal_configs_analysis.json`\n\n')
    for p in sorted(universal_json):
        has_md = '✓' if p in universal_md else '✗'
        has_var = ' + Variables' if p in variable_json else ''
        f.write(f'- {p} [MD: {has_md}]{has_var}\n')
    
    f.write('\n---\n\n')
    f.write('## Plugins with Variable Configs (18 total)\n\n')
    f.write('These plugins have per-server config variations in `utildata/variable_configs_analysis.json`\n')
    f.write('**All 18 should use SMP101 as master server**\n\n')
    for p in sorted(variable_json):
        f.write(f'- {p}\n')
    
    f.write('\n---\n\n')
    f.write('## Plugins with Markdown Baseline Files (57 total)\n\n')
    f.write('These plugins have `_universal_config.md` files in `utildata/plugin_universal_configs/`\n\n')
    for p in sorted(universal_md):
        has_var = ' + Variables' if p in variable_json else ''
        f.write(f'- {p}{has_var}\n')
    
    f.write('\n---\n\n')
    f.write('## Missing Markdown Files (25 plugins)\n\n')
    f.write('These plugins have configs in JSON but no markdown baseline file:\n\n')
    missing = universal_json - universal_md
    for p in sorted(missing):
        has_var = ' + Variables' if p in variable_json else ''
        f.write(f'- {p}{has_var}\n')

print('Report written to output.txt')
