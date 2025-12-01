# Deviation Mistake Detection Heuristics

**Context**: We have universal configs (settings shared by ALL instances with a plugin) and variable configs (per-instance deviations). The question is: **which deviations are mistakes vs intentional customizations?**

## Data Structure Review
- **Universal Config**: `{plugin: {setting: value}}` - Settings identical across ALL INSTANCES THAT HAVE THE PLUGIN
- **Variable Config**: `{plugin: {setting: {instance: value}}}` - Per-instance deviations (only for instances with the plugin)
- **Plugin Deployment**: Not all plugins on all instances (tracked in deployment_matrix.csv)
- **Key Point**: If a plugin is only on 5 instances, universal config is "what those 5 share", variable config is "how those 5 differ"

## 20 Heuristics for Detecting Mistake Deviations

### Statistical Outlier Detection (Frequency-Based)

#### 1. **Single Odd One Out**
- **Rule**: If 1 instance differs from N-1 others (where N = total instances WITH THIS PLUGIN, N >= 3), flag it
- **Example**: DEV01 has `CMI.ReSpawn.Enabled=true`, but 6 others WITH CMI have `false`
- **Confidence**: HIGH if N >= 10, MEDIUM if N >= 5, LOW if N < 5
- **Why Mistake**: Humans tend to copy-paste configs; one outlier suggests oversight
- **Important**: Only compare instances that actually have the plugin deployed

#### 2. **Minority Deviation (< 20% of instances)**
- **Rule**: If setting X has 2-3 instances with value A, but 15+ instances with value B
- **Example**: 2 servers have `max-players=50`, 15 have `max-players=100`
- **Confidence**: MEDIUM (could be intentional for special servers)
- **Why Mistake**: Small clusters suggest partial config update that missed some servers

#### 3. **Expected Value Distribution Violation**
- **Rule**: Setting should follow a pattern (e.g., serverUuid = unique per instance), but has duplicates
- **Example**: `serverUuid` is identical across BENT01, BIG01, CSMC01, MIN01, ROY01, TOW01 (all `b194daaf-...`)
- **Confidence**: VERY HIGH - this is clearly a mistake
- **Why Mistake**: UUIDs MUST be unique; duplicates indicate copy-paste error

### Type/Format Consistency

#### 4. **Type Mismatch Across Instances**
- **Rule**: Same setting has different data types across instances
- **Example**: `port` is `8080` (int) on 10 servers, `"8080"` (string) on 2 servers
- **Confidence**: HIGH
- **Why Mistake**: Inconsistent types suggest manual editing errors

#### 5. **Format Inconsistency**
- **Rule**: Same setting uses different formats (e.g., IP addresses, dates, paths)
- **Example**: `database-url` is `localhost:3306` on 8 servers, `127.0.0.1:3306` on 2 servers
- **Confidence**: MEDIUM (both may work, but inconsistency is suspicious)
- **Why Mistake**: Copy-paste from different sources without standardization

#### 6. **Boolean Typo Detection**
- **Rule**: Boolean setting has value like `treu`, `flase`, `1`, `0`, `yes`, `no` instead of `true`/`false`
- **Example**: `enabled: yes` instead of `enabled: true`
- **Confidence**: MEDIUM (YAML accepts yes/no, but inconsistency is suspect)
- **Why Mistake**: Typos or misunderstanding of config format

### Semantic Analysis

#### 7. **Known Default Value Reversion**
- **Rule**: Instance has a setting = plugin's default value, while others have a customized value
- **Example**: 1 server has `spawn-protection=16` (Minecraft default), 18 have `spawn-protection=0`
- **Confidence**: MEDIUM (could be intentional reset)
- **Why Mistake**: Suggests config file was replaced/reset and customizations lost

#### 8. **Complementary Setting Mismatch**
- **Rule**: Related settings are inconsistent (e.g., `database.enabled=true` but `database.host` is empty)
- **Example**: `auto-update=true` but `update-check-url=""` on 1 server
- **Confidence**: HIGH
- **Why Mistake**: Logical inconsistency indicates incomplete configuration

#### 9. **Performance Setting Anomaly**
- **Rule**: Performance-critical setting is drastically different on 1 instance without justification
- **Example**: `max-threads=1` on 1 server, `max-threads=8` on others (same hardware)
- **Confidence**: MEDIUM (depends on hardware/role)
- **Why Mistake**: Performance settings should match hardware specs

#### 10. **Security Setting Downgrade**
- **Rule**: Security-related setting is weaker on 1 instance
- **Example**: `require-auth=false` on 1 server, `true` on others
- **Confidence**: HIGH
- **Why Mistake**: Security should be consistent; downgrades are usually mistakes

### Temporal Analysis (Requires Metadata)

#### 11. **Recent Change Divergence**
- **Rule**: Setting was recently changed on N-1 instances but not on 1 instance
- **Example**: `plugin-version` updated to 1.5.0 on 18 servers last week, still 1.4.0 on 1 server
- **Confidence**: HIGH
- **Why Mistake**: Batch update that missed one server

#### 12. **Stale Configuration**
- **Rule**: Instance config hasn't been modified in months while others were updated recently
- **Example**: Config last modified 6 months ago, others modified last week
- **Confidence**: MEDIUM
- **Why Mistake**: Server may have been forgotten during maintenance

### Context-Aware Detection

#### 13. **Server Role Violation**
- **Rule**: Setting deviates from expected value for server role (creative/survival/hub/etc)
- **Example**: CREA01 (creative server) has `allow-flight=false`
- **Confidence**: HIGH if role is known
- **Why Mistake**: Role-specific settings should be consistent with server type

#### 14. **Cross-Plugin Inconsistency**
- **Rule**: Setting in Plugin A contradicts related setting in Plugin B on same instance
- **Example**: `world-border.size=5000` in WorldBorder, but `max-distance=10000` in Dynmap
- **Confidence**: MEDIUM
- **Why Mistake**: Plugins should have compatible configurations

#### 15. **Network Topology Violation**
- **Rule**: Network-related settings are inconsistent with known server topology
- **Example**: Proxy mode enabled on non-proxy server, or disabled on proxy server
- **Confidence**: HIGH if topology is known
- **Why Mistake**: Network configs must match actual infrastructure

### Value Range Analysis

#### 16. **Out-of-Range Value**
- **Rule**: Numeric setting exceeds reasonable/documented limits
- **Example**: `view-distance=64` when max is 32
- **Confidence**: HIGH
- **Why Mistake**: Either typo or misunderstanding of valid range

#### 17. **Zero/Null Where Unexpected**
- **Rule**: Critical setting has value 0, null, empty string on 1 instance but not others
- **Example**: `max-players=0` on 1 server, `100` on others
- **Confidence**: MEDIUM (could be intentional disable)
- **Why Mistake**: Often indicates incomplete config or placeholder not replaced

#### 18. **Excessive Value Anomaly**
- **Rule**: Value is orders of magnitude different (10x, 100x) from others
- **Example**: `chunk-gc-period=600000` (10min) on 1 server, `600` (10sec) on others
- **Confidence**: MEDIUM (could be intentional tuning)
- **Why Mistake**: Decimal point error or unit confusion (seconds vs milliseconds)

### Pattern Recognition

#### 19. **Instance Name Pattern Mismatch**
- **Rule**: Setting should correlate with instance name but doesn't
- **Example**: `server-name=SMP201` on DEV01 instance
- **Confidence**: VERY HIGH
- **Why Mistake**: Copy-paste from wrong server config

#### 20. **Cluster Consistency Violation**
- **Rule**: Servers in same logical cluster (e.g., all "SMP*" or all "CREA*") should have similar configs
- **Example**: SMP101 and SMP201 have `difficulty=hard`, but SMP301 has `difficulty=peaceful`
- **Confidence**: MEDIUM (depends on cluster definition)
- **Why Mistake**: Cluster configs should be synchronized

## Implementation Priority

### Tier 1: Implement First (High Confidence, Easy to Detect)
1. Single Odd One Out (#1)
2. Expected Value Distribution Violation (#3) - e.g., duplicate UUIDs
3. Boolean Typo Detection (#6)
4. Instance Name Pattern Mismatch (#19)
5. Out-of-Range Value (#16)

### Tier 2: High Value (Requires Some Context)
6. Type Mismatch (#4)
7. Security Setting Downgrade (#10)
8. Complementary Setting Mismatch (#8)
9. Server Role Violation (#13)
10. Network Topology Violation (#15)

### Tier 3: Advanced (Requires Historical Data or Complex Analysis)
11. Minority Deviation (#2)
12. Recent Change Divergence (#11)
13. Stale Configuration (#12)
14. Known Default Value Reversion (#7)
15. Cross-Plugin Inconsistency (#14)

### Tier 4: Nice to Have (May Have False Positives)
16. Format Inconsistency (#5)
17. Performance Setting Anomaly (#9)
18. Zero/Null Where Unexpected (#17)
19. Excessive Value Anomaly (#18)
20. Cluster Consistency Violation (#20)

## Example Implementation Flow

```python
from pathlib import Path
from collections import Counter
import re

def parse_universal_config_markdown(md_file: Path) -> dict:
    """
    Parse universal config markdown file to extract settings
    
    Format: `Setting.Path` = value
    
    Returns:
        dict {setting_path: value}
    """
    config = {}
    with open(md_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Match lines like: `Alert.Timer` = 1440
            match = re.match(r'^`([^`]+)`\s*=\s*(.+)$', line.strip())
            if match:
                setting_path = match.group(1)
                value_str = match.group(2).strip()
                
                # Parse value (handle lists, bools, numbers, strings)
                if value_str == '[]':
                    value = []
                elif value_str.lower() == 'true':
                    value = True
                elif value_str.lower() == 'false':
                    value = False
                elif value_str.startswith('"') and value_str.endswith('"'):
                    value = value_str[1:-1]
                else:
                    try:
                        value = int(value_str)
                    except ValueError:
                        try:
                            value = float(value_str)
                        except ValueError:
                            value = value_str
                
                config[setting_path] = value
    
    return config

def load_baselines_from_markdown(baseline_dir: Path) -> dict:
    """
    Load all universal config markdown files
    
    Returns:
        dict {plugin_name: {setting: value}}
    """
    baselines = {}
    
    for md_file in baseline_dir.glob("*_universal_config.md"):
        plugin_name = md_file.stem.replace('_universal_config', '')
        baselines[plugin_name] = parse_universal_config_markdown(md_file)
    
    return baselines

def detect_deviation_mistakes(baseline_dir: Path, variable_config: dict, deployment_matrix: dict):
    """
    Analyze variable_config to find likely mistakes
    
    Args:
        baseline_dir: Path to data/baselines/universal_configs/ with .md files
        variable_config: dict {plugin: {setting: {instance: value}}} from utildata/variable_configs_analysis.json
        deployment_matrix: dict {plugin: [instances]} - instances that HAVE the plugin
    
    Returns:
        List of suspected mistakes with confidence scores
    """
    mistakes = []
    
    # Load universal configs from markdown files
    universal_configs = load_baselines_from_markdown(baseline_dir)
    
    for plugin, settings in variable_config.items():
        # CRITICAL: Only analyze instances that actually have this plugin deployed
        instances_with_plugin = deployment_matrix.get(plugin, [])
        
        for setting, instance_values in settings.items():
            # Heuristic #1: Single Odd One Out
            value_counts = Counter(instance_values.values())
            if len(value_counts) == 2:  # Only 2 distinct values
                minority_value, minority_count = min(value_counts.items(), key=lambda x: x[1])
                majority_value, majority_count = max(value_counts.items(), key=lambda x: x[1])
                
                if minority_count == 1 and majority_count >= 5:
                    outlier_instance = [k for k, v in instance_values.items() if v == minority_value][0]
                    mistakes.append({
                        'plugin': plugin,
                        'setting': setting,
                        'instance': outlier_instance,
                        'actual_value': minority_value,
                        'expected_value': majority_value,
                        'heuristic': 'single_odd_one_out',
                        'confidence': 'HIGH' if majority_count >= 10 else 'MEDIUM',
                        'other_instances_count': majority_count
                    })
            
            # Heuristic #3: Duplicate UUIDs
            if 'uuid' in setting.lower() or 'guid' in setting.lower():
                value_counts = Counter(instance_values.values())
                for value, count in value_counts.items():
                    if count > 1:  # UUID should be unique
                        duplicates = [k for k, v in instance_values.items() if v == value]
                        mistakes.append({
                            'plugin': plugin,
                            'setting': setting,
                            'instances': duplicates,
                            'duplicate_value': value,
                            'heuristic': 'duplicate_uuid',
                            'confidence': 'VERY_HIGH',
                            'duplicate_count': count
                        })
            
            # Heuristic #4: Type Mismatch
            types = {type(v).__name__ for v in instance_values.values()}
            if len(types) > 1:
                type_distribution = Counter(type(v).__name__ for v in instance_values.values())
                minority_type, minority_count = min(type_distribution.items(), key=lambda x: x[1])
                minority_instances = [k for k, v in instance_values.items() if type(v).__name__ == minority_type]
                mistakes.append({
                    'plugin': plugin,
                    'setting': setting,
                    'instances': minority_instances,
                    'heuristic': 'type_mismatch',
                    'confidence': 'HIGH',
                    'minority_type': minority_type,
                    'expected_type': max(type_distribution.items(), key=lambda x: x[1])[0]
                })
    
    return mistakes

# Example usage:
# baseline_dir = Path("data/baselines/universal_configs")
# variable_config = json.load(open("utildata/variable_configs_analysis.json"))
# deployment_matrix = load_deployment_matrix("data/reference_data/deployment_matrix.csv")
# mistakes = detect_deviation_mistakes(baseline_dir, variable_config, deployment_matrix)
```

## Real-World Example from Your Data

From `variable_configs_analysis.json`:

```json
"bStats": {
  "serverUuid": {
    "BENT01": "b194daaf-4672-45b1-a849-450067692bbc",
    "BIG01": "b194daaf-4672-45b1-a849-450067692bbc",
    "CSMC01": "b194daaf-4672-45b1-a849-450067692bbc",
    "MIN01": "b194daaf-4672-45b1-a849-450067692bbc",
    "ROY01": "b194daaf-4672-45b1-a849-450067692bbc",
    "TOW01": "b194daaf-4672-45b1-a849-450067692bbc",
    ...
  }
}
```

**DETECTED MISTAKE**: 
- **Heuristic**: #3 (Expected Value Distribution Violation)
- **Confidence**: VERY HIGH
- **Issue**: 6 instances share the same serverUuid `b194daaf-4672-45b1-a849-450067692bbc`
- **Why Mistake**: UUIDs must be unique per instance for bStats tracking
- **Fix**: Generate unique UUID for each instance

---

And from the CMI example:

```json
"CMI": {
  "ReSpawn.Enabled": {
    "BENT01": false, "BIG01": false, "CSMC01": false, "HARD01": false,
    "MIN01": false, "ROY01": false, "TOW01": false,  // 7 false
    "CLIP01": true, "CREA01": true, "DEV01": true, "EMAD01": true,
    "EVO01": true, "HUB01": true, "MINE01": true, "PRI01": true,
    "SMP101": true, "SMP201": true  // 10 true
  }
}
```

**DETECTED PATTERN**: 
- **Heuristic**: #20 (Cluster Consistency Violation) + #13 (Server Role Violation)
- **Confidence**: MEDIUM
- **Pattern**: All "towny-style" servers (BENT, BIG, CSMC, HARD, MIN, ROY, TOW) have `ReSpawn.Enabled=false`, while SMP/creative servers have `true`
- **Assessment**: This is likely INTENTIONAL, not a mistake - different server types have different respawn mechanics

This demonstrates the need for **context-aware analysis**: not all deviations are mistakes!
