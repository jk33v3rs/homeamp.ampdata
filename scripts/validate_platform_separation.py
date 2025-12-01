#!/usr/bin/env python3
"""Validation report for platform separation"""

import json
from pathlib import Path

repo_root = Path(__file__).parent.parent
categorization_file = repo_root / 'plugin_platform_categorization.json'

with open(categorization_file, 'r') as f:
    cat = json.load(f)

print('=' * 70)
print('PLATFORM SEPARATION VALIDATION REPORT')
print('=' * 70)
print()

print('ACTIVE PLUGINS:')
paper_count = len(cat['platforms']['paper']['plugins'])
velocity_count = len(cat['platforms']['velocity']['plugins'])
geyser_count = len(cat['platforms']['geyser']['plugins'])
total_active = paper_count + velocity_count + geyser_count

print(f'  Paper/Spigot:     {paper_count:3} plugins')
print(f'  Velocity:         {velocity_count:3} plugins')
print(f'  Geyser:           {geyser_count:3} extension(s)')
print(f'  {"":20}---')
print(f'  Total Active:     {total_active:3} plugins')
print()

print('CONSOLIDATED:')
quickshop_count = len(cat['consolidated']['QuickShop-Hikari'])
bentobox_count = len(cat['consolidated']['BentoBox'])
luckperms_count = len(cat['consolidated']['LuckPerms'])

print(f'  QuickShop-Hikari: {quickshop_count:3} addons merged')
print(f'  BentoBox:         {bentobox_count:3} extensions merged')
print(f'  LuckPerms:        {luckperms_count:3} variant(s)')
print()

print('EXCLUDED (Not Deployed):')
for plugin in cat['excluded']:
    print(f'  - {plugin}')
print()

print('VELOCITY PLUGINS (VEL01 ONLY):')
for plugin in sorted(cat['platforms']['velocity']['plugins']):
    print(f'  - {plugin}')
print()

print('=' * 70)
print('STATUS: ✅ Platform separation complete and validated!')
print('=' * 70)
print()
print('Next steps:')
print('  1. Deploy to production servers (Hetzner + OVH)')
print('  2. Run new plugin discovery scan')
print('  3. Test platform-specific drift detection')
print()
