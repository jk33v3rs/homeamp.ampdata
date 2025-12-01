#!/usr/bin/env python3
"""
Plugin Platform Categorization and Discovery

Categorizes plugins by platform and detects new installations:
- Paper/Spigot plugins (Minecraft servers)
- Velocity plugins (proxy VEL01)
- Geyser extensions (Bedrock bridge GEY01)

Also consolidates related plugins (QuickShop addons, BentoBox extensions)
"""

import json
from pathlib import Path
from typing import Dict, List, Set
import yaml

# Pl3xMap instance classification for public vs private maps
PAPER_MAP_CONFIGS = {
    'public': [
        'BENT01', 'CLIP01', 'CREA01', 'DEV01', 'EMAD01',
        'EVO01', 'HARD01', 'MINE01', 'MIN01', 'SMP101', 'SMP201', 'TOW01'
    ],
    'private': [
        'ROY01',   # Battle Royale - hide player positions
        'CSMC01',  # Counter-Strike MC - anti screen camping
        'PRI01',   # Minigames - admin monitoring
        'BIG01'    # BiggerGames - admin monitoring
    ]
}

# Platform detection mappings
VELOCITY_PLUGINS = {
    'autoviaupdater', 'luckperms-velocity', 'papiproxybridge-velocity',
    'plan-velocity', 'vcustombrand', 'velocitab', 'viabackwards-velocity',
    'viaversion-velocity', 'viarewind', 'vserverinfo', 'vwhitelist'
}

GEYSER_EXTENSIONS = {
    'Geyser-Recipe-Fix',  # Geyser extension
    # GEY01 is standalone, not a plugin
}

BENTOBOX_ADDONS = {
    'BoxedEyes', 'VoidSpawn', 'PhantomWorlds'  # BentoBox extensions
}

QUICKSHOP_ADDONS = {
    'Addon-Discount', 'Addon-DisplayControl', 'Addon-Limited', 
    'Addon-List', 'Addon-Plan', 'Addon-ShopItemOnly',
    'Compat-EliteMobs', 'Compat-WorldEdit', 'Compat-WorldGuard',
    'Shop-Search', 'economy-bridge'
}

# Plugins that are NOT deployed (hallucinated or legacy)
NOT_DEPLOYED = {
    'DeluxeMenus',
    'Duels',
    'Essentials',
    'EssentialsChat',
    'EssentialsSpawn',
    'Geyser-Spigot',
    'LibertyBans',
    'LiveAtlas'
    # Pl3xMap now active - see PAPER_MAP_CONFIGS for public/private split
}

# Consolidation mapping
CONSOLIDATE_INTO = {
    # QuickShop addons → QuickShop-Hikari
    'Addon-Discount': 'QuickShop-Hikari',
    'Addon-DisplayControl': 'QuickShop-Hikari',
    'Addon-Limited': 'QuickShop-Hikari',
    'Addon-List': 'QuickShop-Hikari',
    'Addon-Plan': 'QuickShop-Hikari',
    'Addon-ShopItemOnly': 'QuickShop-Hikari',
    'Compat-EliteMobs': 'QuickShop-Hikari',
    'Compat-WorldEdit': 'QuickShop-Hikari',
    'Compat-WorldGuard': 'QuickShop-Hikari',
    'Shop-Search': 'QuickShop-Hikari',
    'economy-bridge': 'QuickShop-Hikari',
    
    # BentoBox extensions → BentoBox
    'BoxedEyes': 'BentoBox',
    'VoidSpawn': 'BentoBox',
    'PhantomWorlds': 'BentoBox',
    
    # LuckPerms variants
    'luckperms-velocity': 'LuckPerms',  # Same plugin, different platforms
}


def load_plugin_definitions(definitions_dir: Path) -> Dict[str, dict]:
    """Load all plugin definition markdown files"""
    plugins = {}
    
    for md_file in definitions_dir.glob('*.md'):
        plugin_name = md_file.stem
        
        # Skip non-deployed plugins
        if plugin_name in NOT_DEPLOYED:
            continue
        
        try:
            # Read YAML frontmatter
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract frontmatter between ---
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    plugins[plugin_name] = frontmatter
        except Exception as e:
            print(f"Warning: Could not load {md_file}: {e}")
    
    return plugins


def categorize_by_platform(plugins: Dict[str, dict]) -> Dict[str, List[str]]:
    """Categorize plugins by platform"""
    categorized = {
        'paper': [],      # Paper/Spigot servers (BENT01, BIG01, etc.)
        'velocity': [],   # Velocity proxy (VEL01)
        'geyser': [],     # Geyser standalone (GEY01)
        'consolidated': {},  # Parent plugin → [children]
        'unknown': []
    }
    
    for plugin_name, definition in plugins.items():
        # Check if should be consolidated
        if plugin_name in CONSOLIDATE_INTO:
            parent = CONSOLIDATE_INTO[plugin_name]
            if parent not in categorized['consolidated']:
                categorized['consolidated'][parent] = []
            categorized['consolidated'][parent].append(plugin_name)
            continue
        
        # Categorize by platform
        if plugin_name in VELOCITY_PLUGINS:
            categorized['velocity'].append(plugin_name)
        elif plugin_name in GEYSER_EXTENSIONS:
            categorized['geyser'].append(plugin_name)
        else:
            # Default to Paper
            categorized['paper'].append(plugin_name)
    
    return categorized


def detect_installed_plugins(server_path: Path, platform: str) -> Set[str]:
    """
    Detect installed plugins on a server by scanning the plugins directory.
    
    Args:
        server_path: Path to server (e.g., /home/amp/.ampdata/instances/BENT01)
        platform: 'paper', 'velocity', or 'geyser'
    
    Returns:
        Set of plugin names found on disk
    """
    if platform == 'paper':
        plugins_dir = server_path / 'Minecraft' / 'plugins'
    elif platform == 'velocity':
        plugins_dir = server_path / 'plugins'
    elif platform == 'geyser':
        plugins_dir = server_path / 'extensions'
    else:
        return set()
    
    if not plugins_dir.exists():
        return set()
    
    installed = set()
    
    # Scan for .jar files
    for jar_file in plugins_dir.glob('*.jar'):
        # Extract plugin name from JAR filename
        # Examples:
        # - QuickShop-Hikari-6.2.0.8.jar → QuickShop-Hikari
        # - LuckPerms-Bukkit-5.4.jar → LuckPerms
        # - Addon-DisplayControl-1.0.jar → Addon-DisplayControl
        
        name = jar_file.stem
        
        # Remove version numbers
        # Remove common suffixes
        for suffix in ['-Bukkit', '-Spigot', '-Paper', '-Velocity', '-velocity']:
            if suffix in name:
                name = name.split(suffix)[0]
                break
        
        # Remove version patterns (numbers, dots, dashes at end)
        import re
        name = re.sub(r'-?\d+(\.\d+)*(-[a-zA-Z0-9]+)?$', '', name)
        
        installed.add(name)
    
    return installed


def find_new_plugins(known_plugins: Set[str], installed_plugins: Set[str]) -> Set[str]:
    """Find plugins that are installed but not in definitions"""
    return installed_plugins - known_plugins


def generate_plugin_report(definitions_dir: Path, output_file: Path):
    """Generate comprehensive plugin categorization report"""
    
    print("=" * 80)
    print("ArchiveSMP Plugin Platform Categorization")
    print("=" * 80)
    print()
    
    # Load definitions
    plugins = load_plugin_definitions(definitions_dir)
    print(f"Loaded {len(plugins)} plugin definitions (excluding non-deployed)")
    print()
    
    # Categorize
    categorized = categorize_by_platform(plugins)
    
    # Generate report
    report = {
        'timestamp': str(Path(__file__).stat().st_mtime),
        'total_plugins': len(plugins),
        'platforms': {
            'paper': {
                'count': len(categorized['paper']),
                'plugins': sorted(categorized['paper'])
            },
            'velocity': {
                'count': len(categorized['velocity']),
                'plugins': sorted(categorized['velocity'])
            },
            'geyser': {
                'count': len(categorized['geyser']),
                'plugins': sorted(categorized['geyser'])
            }
        },
        'consolidated': categorized['consolidated'],
        'excluded': sorted(NOT_DEPLOYED)
    }
    
    # Print summary
    print("PAPER/SPIGOT PLUGINS (for BENT01, BIG01, CLIP01, etc.):")
    print(f"  Count: {report['platforms']['paper']['count']}")
    for plugin in report['platforms']['paper']['plugins'][:10]:
        print(f"    - {plugin}")
    if report['platforms']['paper']['count'] > 10:
        print(f"    ... and {report['platforms']['paper']['count'] - 10} more")
    print()
    
    print("VELOCITY PLUGINS (for VEL01 proxy):")
    print(f"  Count: {report['platforms']['velocity']['count']}")
    for plugin in report['platforms']['velocity']['plugins']:
        print(f"    - {plugin}")
    print()
    
    print("GEYSER EXTENSIONS (for GEY01 standalone):")
    print(f"  Count: {report['platforms']['geyser']['count']}")
    for plugin in report['platforms']['geyser']['plugins']:
        print(f"    - {plugin}")
    print()
    
    print("CONSOLIDATED PLUGINS:")
    for parent, children in sorted(report['consolidated'].items()):
        print(f"  {parent}:")
        for child in children:
            print(f"    - {child}")
    print()
    
    print("EXCLUDED (not deployed):")
    for plugin in report['excluded']:
        print(f"    - {plugin}")
    print()
    
    # Save report
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report saved to: {output_file}")
    print()


def scan_for_new_plugins(instances_base: Path, definitions_dir: Path):
    """Scan all instances for plugins not in definitions"""
    
    print("=" * 80)
    print("Scanning for New/Unknown Plugins")
    print("=" * 80)
    print()
    
    # Load known plugins
    plugins = load_plugin_definitions(definitions_dir)
    known = set(plugins.keys())
    
    # Add consolidated children as "known"
    for plugin_name in CONSOLIDATE_INTO.keys():
        known.add(plugin_name)
    
    # Scan each instance
    new_plugins_found = {}
    
    if not instances_base.exists():
        print(f"Instances directory not found: {instances_base}")
        print("(This is OK on development machine)")
        return
    
    for instance_dir in instances_base.iterdir():
        if not instance_dir.is_dir():
            continue
        
        instance_name = instance_dir.name
        
        # Determine platform
        if instance_name == 'VEL01':
            platform = 'velocity'
        elif instance_name == 'GEY01':
            platform = 'geyser'
        else:
            platform = 'paper'
        
        # Scan for installed plugins
        installed = detect_installed_plugins(instance_dir, platform)
        
        # Find new plugins
        new = find_new_plugins(known, installed)
        
        if new:
            new_plugins_found[instance_name] = {
                'platform': platform,
                'new_plugins': sorted(new)
            }
    
    if new_plugins_found:
        print("NEW PLUGINS DETECTED (not in definitions):")
        print()
        for instance, data in sorted(new_plugins_found.items()):
            print(f"{instance} ({data['platform']}):")
            for plugin in data['new_plugins']:
                print(f"  - {plugin}")
        print()
        print("ACTION REQUIRED: Add these plugins to plugin_definitions/")
        print("  1. Create <PluginName>.md file")
        print("  2. Add YAML frontmatter with servers, update_source, ci_cd")
        print("  3. Document configuration requirements")
    else:
        print("✓ No new plugins detected - all plugins have definitions")
    
    print()


if __name__ == '__main__':
    # Paths
    repo_root = Path(__file__).parent.parent
    definitions_dir = repo_root / 'data' / 'plugin_definitions'
    output_file = repo_root / 'plugin_platform_categorization.json'
    
    # Generate categorization report
    generate_plugin_report(definitions_dir, output_file)
    
    # Scan for new plugins (will fail gracefully on dev machine)
    instances_base = Path('/home/amp/.ampdata/instances')
    scan_for_new_plugins(instances_base, definitions_dir)
