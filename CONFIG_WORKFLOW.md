# Configuration Update Workflow

## The Complete Flow

### 1. Capture Current Configs as Baseline ("This is what we want")

```bash
# On production server (Hetzner or OVH)
cd /opt/archivesmp-config-manager

# Scan all instances, extract actual running configs
python scripts/extract_current_configs.py

# This creates:
# data/baselines/plugin_configs/
#   ├── QuickShop-Hikari/
#   │   ├── config.yml (from BENT01)
#   │   ├── messages.yml
#   │   └── ...
#   ├── EliteMobs/
#   │   ├── config.yml
#   │   └── ...
```

**What this does:**
- Reads actual running configs from all instances
- Extracts your custom values (prices, permissions, messages, etc.)
- Stores them as the "baseline" (expected state)
- These become your source of truth

### 2. Plugin Update Happens (New Version Released)

```bash
# Plugin automation already does this automatically!
# src/automation/plugin_automation.py runs hourly

# 1. Checks GitHub/Spigot/Hangar for updates
# 2. Downloads new version
# 3. Deploys to DEV01 for testing
# 4. Waits for approval
```

**DEV01 gets the new plugin with default configs** (not your custom ones yet)

### 3. Test New Plugin on DEV01

You check DEV01 and see:
- ❌ Plugin has default config (not your custom settings)
- ❌ New options you don't recognize
- ❌ Some old options missing

**This is expected!** DEV01 is for testing the plugin itself, not your config.

### 4. Extract New Config Template

```bash
# Get the new default config structure from DEV01
python scripts/extract_new_config_template.py --plugin QuickShop-Hikari --instance DEV01

# This creates:
# data/templates/QuickShop-Hikari/
#   ├── config.yml (new structure with defaults)
#   ├── messages.yml
```

### 5. Merge: Your Settings + New Structure = Updated Config

```bash
# Smart merge: keeps your values, adds new options, removes obsolete ones
python scripts/merge_config_baseline.py --plugin QuickShop-Hikari

# This does:
# 1. Load baseline (your custom settings)
# 2. Load template (new plugin structure)
# 3. Merge intelligently:
#    - Preserve your custom values
#    - Add new options with defaults
#    - Remove obsolete options
#    - Preserve comments where possible
# 4. Save to: data/baselines/plugin_configs/QuickShop-Hikari/config.yml (updated)
```

**Example merge:**

```yaml
# OLD BASELINE (your current settings):
shop:
  price: 100
  tax: 0.05
  old-option: true  # This was removed in new version

# NEW TEMPLATE (plugin v2.0 defaults):
shop:
  price: 50  # Default changed
  tax: 0.10  # Default changed
  new-feature: false  # New option added!

# MERGED RESULT (your settings + new structure):
shop:
  price: 100  # YOUR VALUE PRESERVED
  tax: 0.05  # YOUR VALUE PRESERVED
  new-feature: false  # NEW OPTION ADDED WITH DEFAULT
  # old-option removed (obsolete)
```

### 6. Deploy Merged Config to Production

```bash
# Now deploy the merged config to all instances
curl -X POST http://localhost:8000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "instance_names": ["BENT01", "EMAD01", "SMP201"],
    "plugin_name": "QuickShop-Hikari",
    "config_file": "config.yml"
  }'

# This deploys your merged config (custom values + new structure)
```

### 7. Restart Instances with New Plugin + New Config

```bash
# Web UI: Click "Restart Flagged Only"
# Or API:
curl -X POST http://localhost:8000/api/restart \
  -H "Content-Type: application/json" \
  -d '{
    "instance_names": ["BENT01", "EMAD01", "SMP201"],
    "restart_type": "instances"
  }'
```

**Now your servers have:**
- ✅ New plugin version
- ✅ Your custom settings preserved
- ✅ New features enabled with defaults
- ✅ No obsolete config breaking things

### 8. Verify with Drift Detection

```bash
# After restart, check if configs match expected
python scripts/run_drift_check.py --server BENT01

# Should show: ✅ No drift (config matches baseline)
```

## Full Production Workflow

### Scenario: EliteMobs v9.0.0 is released

**Step 1: Plugin auto-updates to DEV01**
```
[Plugin Automation]
- Detects EliteMobs v9.0.0 on GitHub
- Downloads new JAR
- Deploys to DEV01
- Flags DEV01 for restart
- Notifies: "EliteMobs v9.0.0 ready for testing on DEV01"
```

**Step 2: You test on DEV01**
```bash
# Restart DEV01 to load new plugin
curl -X POST http://localhost:8000/api/restart \
  -d '{"instance_names": ["DEV01"], "restart_type": "instances"}'

# Test the plugin
# - Check if it loads
# - Test basic features
# - Look for errors in logs
```

**Step 3: Extract new config template**
```bash
# Get the new config structure
python scripts/extract_new_config_template.py \
  --plugin EliteMobs \
  --instance DEV01 \
  --output data/templates/EliteMobs/

# Output:
# ✓ Extracted config.yml (new structure)
# ✓ Extracted powers.yml
# ✓ Extracted treasures.yml
# New options found:
#   - config.yml: new-feature.enabled
#   - config.yml: performance.async-spawning
# Obsolete options removed:
#   - config.yml: old-mob-system
```

**Step 4: Merge with your baseline**
```bash
# Smart merge preserving your settings
python scripts/merge_config_baseline.py \
  --plugin EliteMobs \
  --template data/templates/EliteMobs/ \
  --baseline data/baselines/plugin_configs/EliteMobs/ \
  --output data/baselines/plugin_configs/EliteMobs/ \
  --review

# Output:
# Merging config.yml...
#   ✓ Preserved: mob-spawn-rate: 0.3 (was 0.5 in default)
#   ✓ Preserved: boss-health-multiplier: 2.0
#   + Added: new-feature.enabled: false (new option)
#   + Added: performance.async-spawning: true (new option)
#   - Removed: old-mob-system (obsolete)
# 
# Review changes? [y/N]: y
# 
# [Opens diff viewer showing changes]
# 
# Accept merge? [Y/n]: Y
# ✓ Baseline updated: data/baselines/plugin_configs/EliteMobs/config.yml
```

**Step 5: Deploy to production staging group**
```bash
# Deploy to a few servers first (canary deployment)
curl -X POST http://localhost:8000/api/deploy \
  -d '{
    "instance_names": ["DEV01", "BENT01"],
    "plugin_name": "EliteMobs",
    "config_file": "config.yml"
  }'

# Restart those instances
curl -X POST http://localhost:8000/api/restart \
  -d '{"instance_names": ["DEV01", "BENT01"], "restart_type": "instances"}'
```

**Step 6: Verify no issues**
```bash
# Check logs
journalctl -u archivesmp-agent -n 50 --follow

# Check drift (should be zero)
python scripts/run_drift_check.py --server BENT01

# Output:
# ✓ EliteMobs: No drift detected
```

**Step 7: Roll out to all production**
```bash
# Deploy to all EliteMobs instances
curl -X POST http://localhost:8000/api/deploy \
  -d '{
    "instance_names": ["EMAD01", "HARD01", "ROY01", "SMP201"],
    "plugin_name": "EliteMobs"
  }'

# Restart all
curl -X POST http://localhost:8000/api/restart \
  -d '{
    "instance_names": ["EMAD01", "HARD01", "ROY01", "SMP201"],
    "restart_type": "instances"
  }'
```

## What This Solves

### Without this system:
```
Plugin update → Use new default config → Lose all custom settings
Plugin update → Keep old config → Plugin breaks (obsolete options)
Plugin update → Manually edit config → Error-prone, time-consuming
```

### With this system:
```
Plugin update → Extract template → Merge with baseline → Deploy → WORKS!
✓ Your settings preserved
✓ New features enabled
✓ No obsolete options
✓ Automatic and reproducible
```

## Key Scripts Needed (TO BE CREATED)

### 1. `scripts/extract_current_configs.py`
**Purpose:** Capture current running configs as baseline
```python
# Scans all instances
# Extracts plugin configs
# Saves to data/baselines/plugin_configs/
```

### 2. `scripts/extract_new_config_template.py`
**Purpose:** Get new plugin's default config structure
```python
# Reads config from DEV01 (or any instance with new plugin)
# Saves to data/templates/PLUGIN_NAME/
```

### 3. `scripts/merge_config_baseline.py`
**Purpose:** Smart merge of your settings + new structure
```python
# Loads baseline (your custom values)
# Loads template (new structure)
# Merges intelligently:
#   - Keep your custom values
#   - Add new options with defaults
#   - Remove obsolete options
# Saves updated baseline
```

### 4. `scripts/run_drift_check.py`
**Purpose:** Verify deployed configs match baseline
```python
# Uses existing DriftDetector
# Reports any differences
# Helps catch deployment issues
```

## Platform-Aware Config Management

**Important:** Configs are platform-specific!

```
data/baselines/plugin_configs/
  ├── paper/
  │   ├── QuickShop-Hikari/
  │   ├── EliteMobs/
  │   └── ...
  ├── velocity/
  │   ├── velocitab/
  │   ├── viaversion-velocity/
  │   └── ...
  └── geyser/
      └── Geyser-Recipe-Fix/
```

**Why?** Because Velocity plugins shouldn't have configs deployed to Paper servers (prevents catastrophic confusion).

## Audit Trail

Every config change is logged:

```json
{
  "timestamp": "2025-11-13T10:30:00Z",
  "action": "config_merge",
  "plugin": "EliteMobs",
  "version_old": "8.9.5",
  "version_new": "9.0.0",
  "changes": [
    {
      "file": "config.yml",
      "key": "new-feature.enabled",
      "action": "added",
      "value": false
    },
    {
      "file": "config.yml", 
      "key": "old-mob-system",
      "action": "removed",
      "old_value": true
    }
  ],
  "deployed_to": ["DEV01", "BENT01"],
  "deployed_by": "admin",
  "status": "success"
}
```

## Rollback Strategy

If something breaks after plugin update:

```bash
# Option 1: Rollback config only
curl -X POST http://localhost:8000/api/rollback-config \
  -d '{
    "instance_name": "BENT01",
    "plugin_name": "EliteMobs",
    "config_file": "config.yml"
  }'

# Option 2: Rollback plugin version (via AMP)
ampinstmgr stop BENT01
# Manually replace JAR with old version
ampinstmgr start BENT01

# Option 3: Restore from backup
# Configs are automatically backed up before deployment
# See: /home/amp/.ampdata/instances/BENT01/plugins/EliteMobs/config.yml.backup.20251113_103000
```

## Benefits

✅ **Preserve custom settings** during plugin updates
✅ **Automatic config migration** to new plugin versions
✅ **Staging workflow**: DEV01 → Test → Production
✅ **Platform-aware**: Won't deploy Velocity configs to Paper
✅ **Drift detection**: Verify configs match expected state
✅ **Audit trail**: Track all config changes
✅ **Rollback capability**: Restore if something breaks
✅ **No manual editing**: Reduces human error

## Next Steps

Want me to create these scripts?

1. **extract_current_configs.py** - Capture your current settings
2. **extract_new_config_template.py** - Get new plugin structure
3. **merge_config_baseline.py** - Smart merge tool
4. **run_drift_check.py** - Verify deployments

This will complete the "real → baseline → update → deploy" workflow you described.
