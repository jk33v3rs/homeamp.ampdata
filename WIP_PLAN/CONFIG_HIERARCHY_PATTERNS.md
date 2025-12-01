# Configuration Hierarchy & State Management Patterns

**Purpose**: Define the data management model for multi-instance config synchronization with variance handling.

**Core Insight**: Most settings are GLOBAL by default. Variance is the exception, not the rule. GUI should show the unified view with variance highlighted.

---

## Rule Priority Hierarchy (Highest to Lowest)

```
1. INSTANCE_SPECIFIC    (e.g., SMP101 has custom spawn-protection: 32)
2. META_TAG_SPECIFIC    (e.g., all creative worlds: gamemode enforcement)
3. SERVER_SPECIFIC      (e.g., all Hetzner instances: different DB host)
4. GLOBAL_DEFAULT       (e.g., all instances: same plugin version)
```

**Conflict Resolution**: Higher priority ALWAYS wins. Instance-specific overrides meta-tags, meta-tags override server-level, server-level overrides global.

---

## State Scopes

### 1. GLOBAL (Default Assumption)
**What**: Settings identical across ALL instances unless explicitly overridden.

**Examples**:
- Plugin versions (EliteMobs 9.2.9 everywhere)
- Core gameplay mechanics (damage calculations, enchantment formulas)
- Permission group inheritance (LuckPerms default groups)
- Universal plugin configs (57 baseline files)

**Visual**: No highlighting - this is the baseline

**Edit Behavior**: "Push to All" button prominent, changes apply network-wide

---

### 2. SERVER-LEVEL (Physical Hardware)
**What**: Settings that differ between bare metal servers (Hetzner vs OVH).

**Examples**:
- Database connection strings (different hosts)
- Redis endpoints (135.181.212.169 vs 37.187.143.41)
- MinIO endpoints (different message bus instances)
- File paths (if storage differs)

**Visual**: Light yellow highlighting - infrastructure variance

**Edit Behavior**: "Push to Hetzner Instances" or "Push to OVH Instances" bulk action

**Tags**:
- `server:hetzner-xeon`
- `server:ovh-ryzen`

---

### 3. META-TAG BASED (Gameplay Category)
**What**: Settings determined by instance's gameplay mode/category.

**Tag Categories**:

#### Gameplay Style:
- `vanilla-ish` - Minimal plugins, mostly vanilla experience
- `pure-vanilla` - Literally vanilla, just syncing player data
- `lightly-modded` - Paper plugins, no game-changing stuff
- `heavily-modded` - Fabric mods, Origins, Create, tech mods
- `barely-minecraft` - Fully custom, unrecognizable from vanilla

#### Game Mode:
- `creative` - Creative mode worlds (CREA01, freebuild areas)
- `survival` - Standard survival (SMP101, SMP201, most instances)
- `minigame` - Minigame servers (parkour, PvP arenas)
- `utility` - Hub, lobby, network infrastructure (HUB01)
- `experimental` - Dev/test instances (DEV01)

#### Difficulty/Intensity:
- `casual` - Relaxed gameplay, teleports allowed, no death penalties
- `sweaty` - Hardcore, competitive, strict rules
- `hardcore` - Permadeath or harsh penalties

#### Economy:
- `economy-enabled` - Full economy (shops, currency, trading)
- `economy-disabled` - No money systems
- `economy-creative` - Creative mode with economic restrictions

#### Combat:
- `pvp-enabled` - PvP allowed globally or in zones
- `pvp-disabled` - Peaceful, no PvP
- `pve-focused` - EliteMobs, dungeons, boss fights

#### World Persistence:
- `persistent` - Worlds never reset (SMP101 main world)
- `resetting` - Weekly/monthly resets (resource worlds)
- `temporary` - Event-only, deleted after

**Visual**: Light blue highlighting - "this varies by category"

**Edit Behavior**: 
- Dropdown: "Apply to all [creative] instances"
- Rule builder: "IF meta-tag:creative THEN gamemode: CREATIVE"

**Examples**:
```yaml
# Creative worlds get different spawn protection
spawn-protection:
  GLOBAL: 16
  meta-tag:creative: 0  # No spawn protection in creative
  
# Economy disabled in creative
economy-enabled:
  GLOBAL: true
  meta-tag:creative: false
  meta-tag:utility: false  # No economy in HUB either
  
# PvP rules by category
pvp-enabled:
  GLOBAL: false
  meta-tag:pvp-enabled: true
  instance:SMP101: false  # SMP101 is PvE-focused, overrides tag
```

---

### 4. INSTANCE-SPECIFIC (Unique Per-Instance)
**What**: Settings that are unique to ONE instance, overriding all other rules.

**Examples**:
- Server ports (each instance has unique port)
- Instance names/shortnames (SMP101, DEV01, CREA01)
- World names (different world folders per instance)
- Database table prefixes (smp101_, dev01_, etc.)
- Cluster IDs (SMPNET vs DEVnet vs standalone)

**Visual**: Pink highlighting - "unique override, highest priority"

**Edit Behavior**: 
- Editable inline, no "push to" option
- Warning: "This will only affect SMP101"

**Variable Patterns** (from Master_Variable_Configurations.xlsx):
```
{{SERVER_PORT}}        → instance:SMP101 = 25565, instance:DEV01 = 25566
{{SHORTNAME}}          → instance:SMP101 = "SMP101", instance:DEV01 = "DEV01"
{{DATABASE_NAME}}      → instance:SMP101 = "asmp_SQL", instance:DEV01 = "asmp_DEV"
{{WORLD_NAME}}         → instance:SMP101 = "world", instance:CREA01 = "creative"
{{CLUSTER_ID}}         → instance:SMP101 = "SMPNET", instance:DEV01 = "DEVnet"
```

---

## Variance Detection & Highlighting

### Color Coding in GUI

#### **No Highlight** (White/Default)
- Setting is GLOBAL with no variance
- All instances have identical value
- Example: `plugin.elitemobs.version = "9.2.9"` everywhere

#### **Light Green** (Expected Variance)
- Setting uses variable substitution (e.g., `{{SHORTNAME}}`)
- Variance is intentional and structural
- Example: `database.table-prefix = "{{SHORTNAME}}_"` → `smp101_`, `dev01_`, etc.

#### **Light Blue** (Meta-Tag Variance)
- Setting differs by category (creative vs survival)
- Multiple instances share same override
- Example: `gamemode-enforcement: CREATIVE` for all creative-tagged instances

#### **Pink** (Instance-Specific Variance)
- Setting has unique value for ONE instance
- May indicate drift or intentional customization
- Example: `spawn-protection: 32` only on SMP101, everywhere else is `16`

#### **Red** (Unexpected Drift)
- Setting should be global but has unexplained variance
- Possible configuration drift/mistake
- Example: `elitemobs.lightning-damage: 5.0` on most servers, `4.0` on one instance (why?)

---

## GUI Layout Concept

### Main Config Editor Panel

```
┌─────────────────────────────────────────────────────────────────┐
│ Plugin: EliteMobs                                    [Edit Mode] │
├─────────────────────────────────────────────────────────────────┤
│ Viewing: GLOBAL (11 instances)          [Filter: All Variances] │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ Key                          Value           Variance  Action    │
│ ─────────────────────────────────────────────────────────────── │
│ version                      9.2.9           ✓ Global  [Edit]   │
│                                                                   │
│ damage.base-multiplier       1.0             ✓ Global  [Edit]   │
│                                                                   │
│ damage.lightning-elite       5.0             ⚠ Drift   [View]   │  ← RED: unexpected
│   └─ SMP101: 5.0 (10 instances)                                 │
│   └─ DEV01:  4.0 (1 instance)  ← Why different?                 │
│                                                                   │
│ database.table-prefix        {{SHORTNAME}}_  ✓ Variable [View]  │  ← GREEN: expected
│   └─ SMP101: smp101_                                            │
│   └─ DEV01:  dev01_                                             │
│   └─ ... (9 more)                                               │
│                                                                   │
│ spawn-elite-rate             0.05            ⚠ Meta-Tag [View]  │  ← BLUE: category
│   └─ survival (10): 0.05                                        │
│   └─ creative (1):  0.0  (tag:creative disables elites)        │
│                                                                   │
│ custom-spawn-protection      16              ⚠ Instance [View]  │  ← PINK: unique
│   └─ GLOBAL:  16 (10 instances)                                │
│   └─ SMP101:  32 (instance override)                           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

[Push to All] [Push to Tagged...] [Push to Server...] [Validate]
```

---

## Rule Definition System

### Creating Conditional Rules

**GUI Flow**:
1. Click "Add Rule" on any setting
2. Define condition:
   - Scope: Global / Server / Meta-Tag / Instance
   - Selector: (if meta-tag) which tag(s)
   - Value: what to set
3. Priority auto-assigned based on scope
4. Conflicts highlighted if any

**Example Rule Builder**:
```
┌──────────────────────────────────────────────────┐
│ Rule for: gamemode-enforcement                   │
├──────────────────────────────────────────────────┤
│                                                   │
│ [✓] Global Default                               │
│     Value: SURVIVAL                              │
│                                                   │
│ [✓] Override for meta-tag: creative             │
│     Value: CREATIVE                              │
│                                                   │
│ [✓] Override for instance: DEV01                │
│     Value: CREATIVE                              │
│                                                   │
│ [Add Override...]                                │
│                                                   │
│ Priority Order:                                  │
│   1. Instance:DEV01 → CREATIVE                  │
│   2. Meta-tag:creative → CREATIVE               │
│   3. Global → SURVIVAL                          │
│                                                   │
│ [Save Rules] [Test Resolution] [Cancel]         │
└──────────────────────────────────────────────────┘
```

---

## Meta-Tag Assignment Interface

### Instance Tagging Panel

```
┌──────────────────────────────────────────────────────────┐
│ Instance: SMP101                              [Edit Tags] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Server:        [x] hetzner-xeon  [ ] ovh-ryzen           │
│                                                           │
│ Gameplay:      [x] survival      [ ] creative            │
│                [ ] minigame      [ ] utility             │
│                [ ] experimental                          │
│                                                           │
│ Modding Level: [ ] pure-vanilla  [x] vanilla-ish        │
│                [ ] lightly-modded                        │
│                [ ] heavily-modded                        │
│                [ ] barely-minecraft                      │
│                                                           │
│ Intensity:     [ ] casual        [x] sweaty             │
│                [ ] hardcore                              │
│                                                           │
│ Economy:       [x] economy-enabled                       │
│                                                           │
│ Combat:        [ ] pvp-enabled   [x] pve-focused        │
│                                                           │
│ Persistence:   [x] persistent    [ ] resetting          │
│                                                           │
│ Custom Tags:   [elitemobs-enabled] [mcmmo-enabled]      │
│                [+Add Custom Tag]                         │
│                                                           │
│ [Save Tags] [View Affected Rules] [Cancel]              │
└──────────────────────────────────────────────────────────┘
```

---

## Bulk Operations

### "Edit Once, Push to Affected"

**Workflow**:
1. Select setting in global view
2. Edit value
3. Choose push scope:
   - **All Instances** (global override)
   - **All in Server: Hetzner** (server-level)
   - **All with Tag: creative** (meta-tag level)
   - **Only: SMP101, SMP201** (multi-instance select)
4. Preview affected instances
5. Confirm push
6. Agent deploys changes

**Preview Example**:
```
┌──────────────────────────────────────────────────────────┐
│ Confirm Change Push                                      │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ Setting:  elitemobs.spawn-elite-rate                    │
│ New Value: 0.10                                         │
│                                                           │
│ Scope: All instances with tag:survival                  │
│                                                           │
│ Affected Instances (10):                                │
│   ✓ SMP101      (current: 0.05 → will be: 0.10)        │
│   ✓ SMP201      (current: 0.05 → will be: 0.10)        │
│   ✓ EMAD01      (current: 0.05 → will be: 0.10)        │
│   ... (7 more)                                          │
│                                                           │
│ NOT Affected (1):                                       │
│   ✗ CREA01      (tag:creative has override: 0.0)       │
│                                                           │
│ [Confirm Push] [Cancel]                                 │
└──────────────────────────────────────────────────────────┘
```

---

## Data Model for Rules

### Database Schema for Rule Storage

```sql
-- Instance metadata
CREATE TABLE instances (
    instance_id VARCHAR(16) PRIMARY KEY,  -- SMP101, DEV01, etc.
    server_name VARCHAR(32),              -- hetzner-xeon, ovh-ryzen
    is_active BOOLEAN DEFAULT true
);

-- Tag assignments
CREATE TABLE instance_tags (
    instance_id VARCHAR(16) REFERENCES instances(instance_id),
    tag_name VARCHAR(64),                 -- creative, survival, pvp-enabled, etc.
    tag_category VARCHAR(32),             -- gameplay, modding, intensity, economy, combat
    PRIMARY KEY (instance_id, tag_name)
);

-- Config rules (multi-level hierarchy)
CREATE TABLE config_rules (
    rule_id SERIAL PRIMARY KEY,
    plugin_name VARCHAR(64),              -- EliteMobs, HuskSync, etc.
    config_key VARCHAR(256),              -- damage.lightning-elite, database.host, etc.
    
    -- Scope definition
    scope_type VARCHAR(16),               -- GLOBAL, SERVER, META_TAG, INSTANCE
    scope_selector VARCHAR(64),           -- NULL for GLOBAL, 'hetzner-xeon', 'creative', 'SMP101'
    
    -- Value
    config_value TEXT,                    -- Actual value or {{VARIABLE}}
    value_type VARCHAR(16),               -- string, int, float, boolean, json
    
    -- Priority (auto-calculated from scope_type)
    priority INT,                         -- 1=INSTANCE, 2=META_TAG, 3=SERVER, 4=GLOBAL
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(64),               -- Staff member who created rule
    is_active BOOLEAN DEFAULT true
);

-- Variance detection (cached for performance)
CREATE TABLE config_variance_cache (
    plugin_name VARCHAR(64),
    config_key VARCHAR(256),
    
    variance_type VARCHAR(16),            -- NONE, VARIABLE, META_TAG, INSTANCE, DRIFT
    instance_count INT,                   -- How many instances affected
    unique_values INT,                    -- How many different values exist
    
    -- Drift detection
    is_expected_variance BOOLEAN,         -- Green (variable) vs Red (drift)
    
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (plugin_name, config_key)
);

-- Variable definitions (for {{SHORTNAME}} etc.)
CREATE TABLE config_variables (
    instance_id VARCHAR(16) REFERENCES instances(instance_id),
    variable_name VARCHAR(64),            -- SHORTNAME, SERVER_PORT, DATABASE_NAME
    variable_value TEXT,
    PRIMARY KEY (instance_id, variable_name)
);
```

---

## Resolution Algorithm

### How to Determine Final Value for Instance

```python
def resolve_config_value(plugin_name: str, config_key: str, instance_id: str) -> str:
    """
    Resolve final config value for an instance using priority hierarchy.
    """
    # Get instance metadata
    instance = get_instance(instance_id)
    tags = get_instance_tags(instance_id)
    
    # Fetch all applicable rules, ordered by priority
    rules = db.query("""
        SELECT scope_type, scope_selector, config_value, priority
        FROM config_rules
        WHERE plugin_name = ? AND config_key = ?
        AND is_active = true
        ORDER BY priority ASC  -- Lower number = higher priority
    """, plugin_name, config_key)
    
    final_value = None
    
    for rule in rules:
        if rule.scope_type == 'GLOBAL':
            final_value = rule.config_value  # Set baseline
            
        elif rule.scope_type == 'SERVER':
            if instance.server_name == rule.scope_selector:
                final_value = rule.config_value  # Override global
                
        elif rule.scope_type == 'META_TAG':
            if rule.scope_selector in tags:
                final_value = rule.config_value  # Override server-level
                
        elif rule.scope_type == 'INSTANCE':
            if instance_id == rule.scope_selector:
                final_value = rule.config_value  # Highest priority, final override
                break  # No need to check further
    
    # Substitute variables
    if final_value and '{{' in final_value:
        final_value = substitute_variables(final_value, instance_id)
    
    return final_value


def substitute_variables(value: str, instance_id: str) -> str:
    """
    Replace {{VARIABLE}} placeholders with instance-specific values.
    """
    variables = get_instance_variables(instance_id)
    
    for var_name, var_value in variables.items():
        value = value.replace(f"{{{{{var_name}}}}}", var_value)
    
    return value
```

---

## Next Steps

1. **Implement rule storage** - Create config_rules and instance_tags tables
2. **Build tag assignment UI** - Let staff tag instances with gameplay categories
3. **Create variance detector** - Scan all instances, populate variance_cache
4. **Build unified config editor** - Main GUI with color-coded variance display
5. **Test rule resolution** - Verify priority hierarchy works correctly
6. **Add bulk push operations** - "Edit once, push to tagged instances"

This gives you the **data management foundation** for "edit once, apply intelligently based on tags and priorities".
