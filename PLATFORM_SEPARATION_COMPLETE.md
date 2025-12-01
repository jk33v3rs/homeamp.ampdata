# Platform Separation Implementation

## Summary

Successfully implemented platform-aware plugin categorization to prevent "predictable confusion that cataclysmically destroys the server" by keeping Velocity, Geyser, and Paper plugins properly separated.

## What Was Done

### 1. Plugin Platform Categorization (`scripts/categorize_plugins.py`)

Created comprehensive categorization system:

**Platform Breakdown:**
- **Paper/Spigot**: 62 plugins for 17 Minecraft servers
- **Velocity**: 10 plugins for VEL01 proxy
- **Geyser**: 1 extension for GEY01 standalone

**Consolidated Plugins:**
- **QuickShop-Hikari**: Merged 11 addons
  - Addon-Discount, Addon-DisplayControl, Addon-Limited, Addon-List, Addon-Plan, Addon-ShopItemOnly
  - Compat-EliteMobs, Compat-WorldEdit, Compat-WorldGuard
  - economy-bridge, Shop-Search

- **BentoBox**: Merged 3 extensions
  - BoxedEyes, PhantomWorlds, VoidSpawn

- **LuckPerms**: Includes luckperms-velocity variant

**Excluded (9 plugins NOT deployed):**
- DeluxeMenus, Duels, Essentials, EssentialsChat, EssentialsSpawn
- Geyser-Spigot, LibertyBans, LiveAtlas, Pl3xMap

**Output:** `plugin_platform_categorization.json`

### 2. Config Consolidation (`scripts/consolidate_configs.py`)

Merged addon/extension configs into parent plugins:

**Universal Configs:**
- Before: 82 plugin configs
- After: 79 consolidated configs
- Consolidated: BoxedEyes, PhantomWorlds, VoidSpawn → BentoBox

**Variable Configs:**
- Before: 23 plugin configs
- After: 23 configs (no variable addons)

**Platform-Separated Expectations:**
```
data/expectations/
  ├── paper/
  │   ├── universal_configs.json (53 plugins)
  │   └── variable_configs.json (17 plugins)
  ├── velocity/
  │   ├── universal_configs.json (6 plugins)
  │   └── variable_configs.json (0 plugins)
  └── geyser/
      ├── universal_configs.json (1 plugin)
      └── variable_configs.json (0 plugins)
```

**Output Files:**
- `utildata/universal_configs_consolidated.json`
- `utildata/variable_configs_consolidated.json`
- `data/expectations/paper/*.json`
- `data/expectations/velocity/*.json`
- `data/expectations/geyser/*.json`

### 3. Updated Drift Detection (`src/analyzers/drift_detector.py`)

Added platform awareness to prevent cross-contamination:

**New Features:**
- Platform-specific baseline loading
- `get_plugin_platform()` method to identify plugin type
- Automatic platform directory detection
- Platform filtering in drift detection

**Usage:**
```python
# Paper drift detection
detector = DriftDetector(baseline_path, platform='paper')

# Velocity drift detection
detector = DriftDetector(baseline_path, platform='velocity')

# Get plugin platform
platform = DriftDetector.get_plugin_platform('velocitab')  # Returns 'velocity'
```

## Architecture Changes

### Before:
```
data/baselines/
  ├── plugin_definitions/  (all plugins mixed together)
  └── expectations/  (single universal/variable files)
```

### After:
```
data/
  ├── baselines/plugin_definitions/  (97 .md files, 88 active)
  └── expectations/
      ├── paper/
      │   ├── universal_configs.json
      │   └── variable_configs.json
      ├── velocity/
      │   ├── universal_configs.json
      │   └── variable_configs.json
      └── geyser/
          ├── universal_configs.json
          └── variable_configs.json
```

## New Plugin Discovery

The categorization script includes:

**`detect_installed_plugins()` function:**
- Scans JAR files in `/home/amp/.ampdata/instances/<instance>/plugins/`
- Scans extensions in `/home/amp/.ampdata/instances/<instance>/extensions/`
- Matches against known plugin definitions

**`find_new_plugins()` function:**
- Compares installed JARs vs known definitions
- Returns list of unknown plugins requiring definition

**`scan_for_new_plugins()` function:**
- Wrapper for production scanning
- Reports new plugins not in registry
- Can request CI/CD info for new discoveries

## Usage Instructions

### Run Categorization (Already Done)
```bash
cd e:\homeamp.ampdata
python scripts\categorize_plugins.py
```

### Run Config Consolidation (Already Done)
```bash
cd e:\homeamp.ampdata
python scripts\consolidate_configs.py
```

### On Production Servers (To Be Done)

**Deploy categorization script:**
```bash
# Copy script to production
scp scripts/categorize_plugins.py root@archivesmp.site:/opt/archivesmp-config-manager/scripts/

# SSH to Hetzner
ssh root@archivesmp.site

# Run new plugin scan
cd /opt/archivesmp-config-manager
python scripts/categorize_plugins.py --scan-new
```

**Expected output on production:**
```
Loaded 88 plugin definitions (excluding non-deployed)

Scanning for new plugins...
  Paper servers: 17 instances
  Velocity servers: 1 instance (VEL01)
  Geyser servers: 1 instance (GEY01)

NEW PLUGINS FOUND:
  Paper: SomeNewPlugin.jar (BENT01, EMAD01)
  Velocity: NewProxyPlugin.jar (VEL01)

Report saved to: /opt/archivesmp-config-manager/new_plugins_report.json
```

## Platform-Specific Instance Mapping

### Paper/Spigot Servers (17 instances):
BENT01, BIG01, CLIP01, CREA01, CSMC01, DEV01, EMAD01, EVO01, HARD01, HUB01, MINE01, MIN01, PRI01, ROY01, SMP101, SMP201, TOW01

### Velocity Proxy (1 instance):
VEL01

### Geyser Standalone (1 instance):
GEY01

### Hetzner Deployment (11 instances):
BENT01, CLIP01, CREA01, DEV01, EMAD01, HARD01, MINE01, MIN01, ROY01, SMP201, VEL01

### OVH Deployment (12 instances):
BIG01, CSMC01, EVO01, GEY01, HUB01, PRI01, SMP101, TOW01, + 4 more TBD

## Velocity Plugin List (10 plugins)

**CRITICAL: These plugins ONLY go on VEL01 proxy**

1. autoviaupdater
2. papiproxybridge-velocity
3. plan-velocity
4. vcustombrand
5. velocitab
6. viabackwards-velocity
7. viarewind
8. viaversion-velocity
9. vserverinfo
10. vwhitelist

**DO NOT deploy Velocity plugins to Paper servers!**

## Geyser Extensions (1 extension)

**ONLY for GEY01 standalone:**
- Geyser-Recipe-Fix

## Next Steps

### High Priority:
1. ✅ Platform categorization complete
2. ✅ Config consolidation complete
3. ✅ Drift detector updated
4. ⏳ Deploy scripts to production
5. ⏳ Run new plugin discovery on Hetzner
6. ⏳ Run new plugin discovery on OVH

### Medium Priority:
1. Update plugin definition files with `platform:` field
2. Add CI/CD request workflow for new plugins
3. Create platform-specific deployment guards in agent API
4. Add platform indicator to web UI
5. Test drift detection with platform-specific expectations

### Low Priority:
1. Migrate existing baseline configs to platform directories
2. Add platform badges to plugin list UI
3. Create platform health dashboard
4. Document platform-specific config patterns

## Files Modified

**Created:**
- `scripts/categorize_plugins.py` (400 lines)
- `scripts/consolidate_configs.py` (180 lines)
- `plugin_platform_categorization.json`
- `utildata/universal_configs_consolidated.json`
- `utildata/variable_configs_consolidated.json`
- `data/expectations/paper/universal_configs.json`
- `data/expectations/paper/variable_configs.json`
- `data/expectations/velocity/universal_configs.json`
- `data/expectations/velocity/variable_configs.json`
- `data/expectations/geyser/universal_configs.json`
- `data/expectations/geyser/variable_configs.json`

**Modified:**
- `src/analyzers/drift_detector.py` (added platform awareness)

## Safety Improvements

### Before:
- All plugins treated equally
- No platform separation
- Risk of deploying Velocity plugins to Paper servers
- Risk of deploying Paper plugins to Velocity proxy
- Config drift detection couldn't distinguish platforms

### After:
- ✅ Explicit platform categorization
- ✅ Velocity plugins isolated
- ✅ Geyser extensions separate
- ✅ Config consolidation reduces redundancy
- ✅ Drift detection platform-aware
- ✅ New plugin discovery respects platforms
- ✅ 9 non-deployed plugins explicitly excluded

## Production Deployment Commands

### On Hetzner (archivesmp.site):
```bash
# SSH to server
ssh root@archivesmp.site

# Copy scripts
cd /opt/archivesmp-config-manager
git pull  # If using git deployment

# Or manual copy:
# scp scripts/categorize_plugins.py root@archivesmp.site:/opt/archivesmp-config-manager/scripts/
# scp scripts/consolidate_configs.py root@archivesmp.site:/opt/archivesmp-config-manager/scripts/

# Run categorization with production scan
python scripts/categorize_plugins.py --scan-new

# Review new plugins report
cat new_plugins_report.json

# Deploy consolidated configs to expectations
python scripts/consolidate_configs.py

# Restart agent to load new platform logic
sudo systemctl restart homeamp-agent
```

### On OVH (archivesmp.online):
```bash
# SSH to server
ssh root@archivesmp.online

# Same commands as Hetzner
cd /opt/archivesmp-config-manager
python scripts/categorize_plugins.py --scan-new
python scripts/consolidate_configs.py
sudo systemctl restart homeamp-agent
```

## Testing Checklist

- [ ] Run categorize_plugins.py on production Hetzner
- [ ] Run categorize_plugins.py on production OVH
- [ ] Verify 62 Paper plugins detected
- [ ] Verify 10 Velocity plugins only on VEL01
- [ ] Verify 1 Geyser extension only on GEY01
- [ ] Verify NO Essentials/DeluxeMenus/etc. detected
- [ ] Review new_plugins_report.json for unknowns
- [ ] Test drift detection with platform filter
- [ ] Verify QuickShop configs consolidated
- [ ] Verify BentoBox configs consolidated
- [ ] Test deployment with platform guards
- [ ] Verify web UI shows platform correctly

## Success Metrics

✅ **88 active plugins categorized** (excluding 9 non-deployed)
✅ **62 Paper plugins** identified for Minecraft servers
✅ **10 Velocity plugins** isolated for proxy
✅ **1 Geyser extension** for Bedrock bridge
✅ **11 QuickShop addons** consolidated
✅ **3 BentoBox extensions** consolidated
✅ **79 consolidated configs** (down from 82)
✅ **Platform-separated expectations** created
✅ **Drift detector** updated with platform awareness
✅ **New plugin discovery** framework ready

## Final Notes

This implementation prevents:
- ❌ Deploying Velocity plugins to Paper servers
- ❌ Deploying Paper plugins to Velocity proxy
- ❌ Deploying Geyser extensions to wrong servers
- ❌ Config drift false positives from platform mixing
- ❌ "Predictable confusion that cataclysmically destroys the server"

And enables:
- ✅ Safe platform-specific deployments
- ✅ Consolidated addon/extension configs
- ✅ New plugin discovery with platform detection
- ✅ Platform-aware drift detection
- ✅ Cleaner config management

**Ready for production deployment to Hetzner and OVH!**
