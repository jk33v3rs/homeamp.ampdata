# Expectations Data Format

## Overview

"Expectations" are the baseline configurations that define what plugin configs **SHOULD** look like across the ArchiveSMP network. The drift detection system compares these expectations against "reality" (actual configs on production servers) to identify configuration drift.

## File Structure

```
data/expectations/
├── universal_configs.json         # 82 plugins - identical everywhere
├── variable_configs.json          # 23 plugins - documented variances
└── metadata.json                  # Metadata about the expectations
```

## Universal Configs

**File:** `universal_configs.json`

**Format:**
```json
{
  "PluginName": {
    "config.key.path": "expected_value",
    "another.key": "expected_value"
  }
}
```

**Example:**
```json
{
  "CoreProtect": {
    "verbose": true,
    "api-enabled": false,
    "rollback-items": true
  },
  "LuckPerms": {
    "server": "global",
    "use-server-uuid-cache": true,
    "auto-op": false
  }
}
```

**Rules:**
- These configs should be **identical** across all 23 instances
- If reality differs from expectations, it's flagged as **unexpected drift**
- Covers 82 plugins including 6 paid plugins

## Variable Configs

**File:** `variable_configs.json`

**Format:**
```json
{
  "PluginName": {
    "config.key.path": {
      "INSTANCE1": "allowed_value_1",
      "INSTANCE2": "allowed_value_2"
    }
  }
}
```

**Example:**
```json
{
  "CoreProtect": {
    "table-prefix": {
      "BENT01": "co_bent01_",
      "CLIP01": "co_clip01_",
      "SMP101": "co_smp101_"
    }
  },
  "bStats": {
    "serverUuid": {
      "BENT01": "550e8400-e29b-41d4-a716-446655440000",
      "CLIP01": "550e8400-e29b-41d4-a716-446655440001"
    }
  },
  "LevelledMobs": {
    "use-custom-mobs.enabled": {
      "BENT01": true,
      "BIG01": false,
      "CLIP01": false
    }
  }
}
```

**Rules:**
- These configs are **allowed to differ** between instances
- If reality matches a documented variance, it's flagged as **documented variance** (warning, not error)
- If reality differs AND it's not a documented variance, it's flagged as **unexpected drift**
- Covers 23 plugins (all are subset of the 82 universal plugins)

## Documented Variances Explained

Some plugins need instance-specific values:

### Server Identity
- `bStats.serverUuid` - Unique ID per instance for metrics
- `CoreProtect.table-prefix` - Unique DB table prefix per instance
- `ImageFrame.WebServer.Port` - Unique port per instance

### Instance-Specific Features
- `LevelledMobs` settings - BENT01 uses advanced levelling, others use vanilla
- `CMI` economy settings - Per-server balances
- `Quests` data - Different quest progression per server

## Drift Detection Logic

```python
for each plugin in instance:
    for each config_key in plugin:
        # Get expected value
        if plugin in universal_configs:
            expected = universal_configs[plugin][config_key]
        
        # Check if variance is documented
        if plugin in variable_configs:
            if config_key in variable_configs[plugin]:
                if instance_name in variable_configs[plugin][config_key]:
                    expected = variable_configs[plugin][config_key][instance_name]
                    is_documented_variance = True
        
        # Compare
        actual = read_config_from_disk(instance, plugin, config_key)
        
        if actual != expected:
            report_drift(
                plugin=plugin,
                key=config_key,
                expected=expected,
                actual=actual,
                is_documented_variance=is_documented_variance
            )
```

## Example Drift Scenarios

### Scenario 1: Unexpected Drift (RED FLAG 🔴)
```
Plugin: CoreProtect
Key: rollback-items
Expected: true (from universal_configs.json)
Actual: false (on BENT01)
Status: UNEXPECTED DRIFT
Action: Fix required
```

### Scenario 2: Documented Variance (YELLOW FLAG 🟡)
```
Plugin: CoreProtect
Key: table-prefix
Expected: "co_bent01_" (from variable_configs.json for BENT01)
Actual: "co_bent01_" (on BENT01)
Status: OK - Documented Variance
Action: None needed
```

### Scenario 3: Unexpected Variance (RED FLAG 🔴)
```
Plugin: CoreProtect
Key: table-prefix
Expected: "co_bent01_" (from variable_configs.json for BENT01)
Actual: "co_wrong_" (on BENT01)
Status: UNEXPECTED DRIFT (wrong variance value)
Action: Fix required
```

### Scenario 4: Perfect Match (GREEN FLAG 🟢)
```
Plugin: LuckPerms
Key: server
Expected: "global" (from universal_configs.json)
Actual: "global" (on all instances)
Status: OK
Action: None needed
```

## Updating Expectations

### When to Update Universal Configs
- Plugin updated and changed default configs
- New plugin added to all servers
- Standard config change rolled out network-wide

### When to Update Variable Configs
- New instance added (add its variances)
- Instance-specific feature enabled/disabled
- Port/ID/prefix assignments changed

### How to Update
1. Edit source files:
   - `E:\homeamp.ampdata\utildata\universal_configs_analysis.json`
   - `E:\homeamp.ampdata\utildata\variable_configs_analysis_UPDATED.json`

2. Run packaging script:
   ```cmd
   python E:\homeamp.ampdata\scripts\package_expectations.py
   ```

3. Deploy to production:
   ```bash
   scp -r software/homeamp-config-manager/data/expectations/ webadmin@135.181.212.169:/home/webadmin/archivesmp-config-manager/data/
   scp -r software/homeamp-config-manager/data/expectations/ webadmin@37.187.143.41:/home/webadmin/archivesmp-config-manager/data/
   ```

4. Restart agents:
   ```bash
   sudo systemctl restart archivesmp-agent
   ```

## Validation

The agent validates expectations data on startup:

```
✓ Loaded 82 universal plugin configs
✓ Loaded 23 variable plugin configs
✓ Found 23 instances in 11 Hetzner + 12 OVH
✓ Expectations data valid
```

## Related Files

- **Baseline Documentation:** `E:\homeamp.ampdata\utildata\plugin_universal_configs\*.md`
- **Plugin Definitions:** `E:\homeamp.ampdata\data\plugin_definitions\*.md`
- **Production Configs:** `/home/amp/.ampdata/instances/*/Minecraft/plugins/*/config.yml`
