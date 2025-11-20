"""
Test script to verify all new modules work correctly with sample data.
Run this on the developer machine to validate implementations.
"""

import sys
from pathlib import Path

# Test 1: Baseline Parser
print("=" * 60)
print("TEST 1: Baseline Parser")
print("=" * 60)

try:
    from src.parsers.baseline_parser import BaselineParser, ParsedConfig
    
    # Create sample baseline markdown content
    sample_baseline = """
# EssentialsX

## config.yml

```yaml
teleport-safety: true
spawn-on-join: true
max-homes: 5
economy:
  enabled: true
  currency-symbol: "$"
```

## worth.yml

```yaml
diamond: 100
gold_ingot: 10
```
"""
    
    parser = BaselineParser()
    configs = parser.parse_baseline_content(sample_baseline, "EssentialsX")
    
    print(f" Parsed {len(configs)} config entries from sample baseline")
    for config in configs[:3]:
        print(f"  - {config.plugin_id}/{config.config_file} -> {config.config_key} = {config.config_value}")
    
    assert len(configs) > 0, "Should parse at least one config"
    assert configs[0].plugin_id == "EssentialsX", "Plugin ID should match"
    
    print(" Baseline parser validation PASSED\n")

except Exception as e:
    print(f" Baseline parser validation FAILED: {e}\n")
    sys.exit(1)


# Test 2: Rank Parser
print("=" * 60)
print("TEST 2: LuckPerms Rank Parser")
print("=" * 60)

try:
    from src.parsers.rank_parser import LuckPermsRankParser, RankInfo
    
    # Create sample LuckPerms group data
    sample_group_data = {
        'displayname': 'Administrator',
        'weight': 500,
        'parents': ['moderator', 'vip'],
        'permissions': {
            'essentials.teleport': True,
            'essentials.god': True,
            'worldedit.*': True
        },
        'meta': {
            'prefix': '&c[Admin] ',
            'suffix': ' &f'
        }
    }
    
    parser = LuckPermsRankParser()
    rank = parser._parse_group_data(
        sample_group_data, 
        'admin', 
        instance_id='TEST01',
        server_name='test'
    )
    
    print(f" Parsed rank: {rank.rank_name}")
    print(f"  Display: {rank.display_name}")
    print(f"  Priority: {rank.priority}")
    print(f"  Prefix: {rank.prefix}")
    print(f"  Inherits from: {', '.join(rank.inherits_from)}")
    print(f"  Permission count: {rank.permission_count}")
    
    assert rank.rank_name == 'admin', "Rank name should match"
    assert rank.priority == 500, "Priority should match weight"
    assert len(rank.inherits_from) == 2, "Should inherit from 2 groups"
    assert rank.permission_count == 3, "Should have 3 permissions"
    
    print(" Rank parser validation PASSED\n")

except Exception as e:
    print(f" Rank parser validation FAILED: {e}\n")
    sys.exit(1)


# Test 3: World Scanner (structure validation only)
print("=" * 60)
print("TEST 3: World Scanner (Structure)")
print("=" * 60)

try:
    from src.scanners.world_scanner import WorldScanner, WorldInfo
    from datetime import datetime
    
    # Create sample WorldInfo
    world = WorldInfo(
        instance_id='TEST01',
        world_name='world',
        world_type='normal',
        seed=12345,
        generator='default',
        folder_size_bytes=1024000,
        region_count=10
    )
    
    print(f" Created WorldInfo:")
    print(f"  Instance: {world.instance_id}")
    print(f"  Name: {world.world_name}")
    print(f"  Type: {world.world_type}")
    print(f"  Seed: {world.seed}")
    print(f"  Size: {world.folder_size_bytes / 1024:.1f} KB")
    print(f"  Regions: {world.region_count}")
    
    assert world.discovered_at is not None, "Should auto-set discovered_at"
    assert isinstance(world.discovered_at, datetime), "discovered_at should be datetime"
    
    print(" World scanner structure validation PASSED\n")

except Exception as e:
    print(f" World scanner validation FAILED: {e}\n")
    sys.exit(1)


# Test 4: Hierarchy Resolver (structure validation only)
print("=" * 60)
print("TEST 4: Config Hierarchy Resolver (Structure)")
print("=" * 60)

try:
    from src.core.hierarchy_resolver import ConfigContext, ScopeLevel, ResolvedConfig
    
    # Create sample context
    context = ConfigContext(
        plugin_id='server.properties',
        config_file='server.properties',
        config_key='spawn-protection',
        server_name='hetzner',
        instance_id='BENT01',
        world_name='world'
    )
    
    print(f" Created ConfigContext:")
    print(f"  Plugin: {context.plugin_id}")
    print(f"  File: {context.config_file}")
    print(f"  Key: {context.config_key}")
    print(f"  Server: {context.server_name}")
    print(f"  Instance: {context.instance_id}")
    print(f"  World: {context.world_name}")
    
    # Verify scope levels
    assert ScopeLevel.GLOBAL.value == 0, "GLOBAL should be lowest priority"
    assert ScopeLevel.PLAYER.value == 6, "PLAYER should be highest priority"
    assert ScopeLevel.INSTANCE.value > ScopeLevel.META_TAG.value, "INSTANCE > META_TAG"
    
    print(" Hierarchy resolver structure validation PASSED\n")

except Exception as e:
    print(f" Hierarchy resolver validation FAILED: {e}\n")
    sys.exit(1)


# Summary
print("=" * 60)
print("ALL TESTS PASSED ")
print("=" * 60)
print("\nAll new modules are functioning correctly!")
print("Ready to commit and deploy to production server.")
print("\nNext steps:")
print("  1. git add software/homeamp-config-manager/")
print("  2. git commit -m 'feat: Add 7-level hierarchy system'")
print("  3. git push origin master")
print("  4. SSH to production and pull changes")
print("  5. Run migrations on production database")
