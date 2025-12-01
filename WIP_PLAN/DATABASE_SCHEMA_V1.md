# Complete Database Schema for Multi-Instance Config Management

**Version**: 1.0  
**Purpose**: Hierarchical configuration management with meta-tag logic, world-specific settings, and region support  
**Status**: Ready for review before database creation

---

## Design Principles

1. **Hierarchy**: 10-level priority system (PLAYER_OVERRIDE → REGION → REGION_GROUP → WORLD → WORLD_GROUP → INSTANCE → INSTANCE_GROUP → META_TAG → SERVER → GLOBAL)
2. **Tag Logic**: Support AND/EXCEPT operations (e.g., "survival AND economy-enabled EXCEPT creative")
3. **Meta-Grouping**: Arbitrary logical clustering at every tier (instance groups, world groups, region groups)
4. **Multi-Level Scoping**: Instance → World → Region → Player granularity
5. **Variance Tracking**: Detect expected vs unexpected configuration drift
6. **Rank-Aware**: Universal rank system for all gameplay features
7. **Player Overrides**: Ultra-granular control per player at any scope level

---

## Table Overview

**Total Tables**: 22

**Core Infrastructure** (3):
- `instances` - Physical deployments (SMP101, DEV01, etc.)
- `meta_tag_categories` - Tag classification (gameplay, modding, intensity, etc.)
- `meta_tags` - Classification tags (survival, creative, pvp-enabled, etc.)

**Meta-Grouping** (6):
- `instance_groups` + `instance_group_members` - Meta-server clustering (creative-servers, hetzner-cluster, etc.)
- `world_groups` + `world_group_members` - World clustering (resource-worlds, survival-worlds, etc.)
- `region_groups` + `region_group_members` - Region clustering (pvp-arenas, safe-zones, etc.)

**Tagging Assignments** (3):
- `instance_tags` - Tag assignments to instances
- `world_tags` - Tag assignments to worlds
- `region_tags` - Tag assignments to regions

**Multi-World/Region Support** (2):
- `worlds` - Multi-world per instance (world, world_nether, resource_world, etc.)
- `regions` - WorldGuard regions (spawn, shop_district, pvp_arena, etc.)

**Configuration System** (3):
- `config_rules` - Hierarchical config rules with scope filtering
- `config_variables` - Template substitution ({{SHORTNAME}}, {{SERVER_PORT}}, etc.)
- `config_variance_cache` - Performance cache for drift detection

**Player Progression** (2):
- `rank_definitions` - Universal rank system (20 primary + 30 prestige tiers)
- `player_ranks` - Player rank tracking and progression

**Player Classification** (3):
- `player_role_categories` - Role categories (staff, community, support, donor)
- `player_roles` - Specific roles (admin, moderator, patreon_tier1, etc.)
- `player_role_assignments` - Scoped role grants with expiry

**Player Overrides** (1):
- `player_config_overrides` - Per-player config exceptions with scope filtering

---

## Core Tables

### 1. Instances (Physical Deployments)

```sql
CREATE TABLE instances (
    instance_id VARCHAR(16) PRIMARY KEY,           -- SMP101, DEV01, CREA01, etc.
    instance_name VARCHAR(128) NOT NULL,           -- "Main SMP Server", "Creative World"
    
    -- Physical server assignment
    server_name VARCHAR(32) NOT NULL,              -- hetzner-xeon, ovh-ryzen
    server_host VARCHAR(64),                       -- 135.181.212.169, 37.187.143.41
    
    -- Instance details
    port INT,                                      -- 25565, 25566, etc.
    amp_instance_id VARCHAR(64),                   -- AMP internal instance ID
    platform VARCHAR(16) DEFAULT 'paper',          -- paper, fabric, velocity, etc.
    minecraft_version VARCHAR(16),                 -- 1.21.3, 1.21.4, etc.
    
    -- State
    is_active BOOLEAN DEFAULT true,
    is_production BOOLEAN DEFAULT true,            -- vs test/dev
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP,
    
    -- Notes
    description TEXT,
    admin_notes TEXT
);

CREATE INDEX idx_instances_server ON instances(server_name);
CREATE INDEX idx_instances_active ON instances(is_active, is_production);
```

**Example Data**:
```sql
INSERT INTO instances VALUES
    ('SMP101', 'Main SMP Server', 'hetzner-xeon', '135.181.212.169', 25565, 'amp-uuid-1', 'paper', '1.21.3', true, true, NOW(), NOW(), 'Primary survival server', NULL),
    ('DEV01', 'Development Server', 'hetzner-xeon', '135.181.212.169', 25566, 'amp-uuid-2', 'paper', '1.21.3', true, false, NOW(), NOW(), 'Testing environment', NULL),
    ('CREA01', 'Creative Server', 'ovh-ryzen', '37.187.143.41', 25565, 'amp-uuid-3', 'paper', '1.21.3', true, true, NOW(), NOW(), 'Creative building world', NULL);
```

---

### 2. Meta Tags (Classification System)

```sql
CREATE TABLE meta_tag_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(64) NOT NULL UNIQUE,     -- gameplay, modding, intensity, economy, combat, persistence
    description TEXT,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE meta_tags (
    tag_id SERIAL PRIMARY KEY,
    tag_name VARCHAR(64) NOT NULL UNIQUE,          -- survival, creative, economy-enabled, pvp-enabled, etc.
    category_id INT REFERENCES meta_tag_categories(category_id),
    
    -- Display
    display_name VARCHAR(128),                     -- "Survival Mode", "Economy Enabled"
    color_code VARCHAR(16),                        -- For GUI highlighting
    icon VARCHAR(64),                              -- Material or emoji for UI
    
    description TEXT,
    is_system_tag BOOLEAN DEFAULT false,           -- Built-in vs custom tags
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tags_category ON meta_tags(category_id);
CREATE INDEX idx_tags_active ON meta_tags(is_active);
```

**Example Data**:
```sql
-- Categories
INSERT INTO meta_tag_categories (category_name, description, display_order) VALUES
    ('gameplay', 'Primary gameplay mode', 1),
    ('modding', 'Level of modification from vanilla', 2),
    ('intensity', 'Difficulty/competitiveness', 3),
    ('economy', 'Economic system features', 4),
    ('combat', 'PvP/PvE configuration', 5),
    ('persistence', 'World reset behavior', 6);

-- Tags
INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag) VALUES
    -- Gameplay
    ('survival', 1, 'Survival Mode', 'Standard survival gameplay', true),
    ('creative', 1, 'Creative Mode', 'Creative building mode', true),
    ('minigame', 1, 'Minigame', 'Minigame/arena server', true),
    ('utility', 1, 'Utility', 'Hub/lobby/infrastructure', true),
    ('experimental', 1, 'Experimental', 'Testing/development', true),
    
    -- Modding
    ('pure-vanilla', 2, 'Pure Vanilla', 'No plugins, vanilla only', true),
    ('vanilla-ish', 2, 'Vanilla-ish', 'Minimal quality-of-life plugins', true),
    ('lightly-modded', 2, 'Lightly Modded', 'Standard plugin set', true),
    ('heavily-modded', 2, 'Heavily Modded', 'Fabric mods, Origins, Create', true),
    ('barely-minecraft', 2, 'Barely Minecraft', 'Heavily customized gameplay', true),
    
    -- Intensity
    ('casual', 3, 'Casual', 'Relaxed, teleports allowed, keep inventory', true),
    ('sweaty', 3, 'Sweaty', 'Competitive, strict rules', true),
    ('hardcore', 3, 'Hardcore', 'Permadeath or harsh penalties', true),
    
    -- Economy
    ('economy-enabled', 4, 'Economy Enabled', 'Full economy system active', true),
    ('economy-disabled', 4, 'Economy Disabled', 'No currency/shops', true),
    ('economy-creative', 4, 'Creative Economy', 'Limited economy in creative', true),
    
    -- Combat
    ('pvp-enabled', 5, 'PvP Enabled', 'Player vs Player allowed', true),
    ('pvp-disabled', 5, 'PvP Disabled', 'Peaceful, no PvP', true),
    ('pve-focused', 5, 'PvE Focused', 'EliteMobs, dungeons, bosses', true),
    
    -- Persistence
    ('persistent', 6, 'Persistent', 'World never resets', true),
    ('resetting', 6, 'Resetting', 'Periodic resets (weekly/monthly)', true),
    ('temporary', 6, 'Temporary', 'Event-only, deleted after', true);
```

---

### 3. Instance Tag Assignment (with AND/EXCEPT logic)

```sql
CREATE TABLE instance_tags (
    assignment_id SERIAL PRIMARY KEY,
    instance_id VARCHAR(16) REFERENCES instances(instance_id) ON DELETE CASCADE,
    tag_id INT REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    -- Assignment metadata
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by VARCHAR(64),                       -- Username who assigned
    assignment_note TEXT,                          -- Why this tag was assigned
    
    UNIQUE(instance_id, tag_id)
);

CREATE INDEX idx_instance_tags_instance ON instance_tags(instance_id);
CREATE INDEX idx_instance_tags_tag ON instance_tags(tag_id);
```

**Example Data**:
```sql
-- SMP101: survival, economy-enabled, pve-focused, sweaty, persistent
INSERT INTO instance_tags (instance_id, tag_id, assigned_by) 
SELECT 'SMP101', tag_id, 'system' FROM meta_tags WHERE tag_name IN ('survival', 'economy-enabled', 'pve-focused', 'sweaty', 'persistent', 'vanilla-ish');

-- DEV01: experimental, economy-disabled
INSERT INTO instance_tags (instance_id, tag_id, assigned_by)
SELECT 'DEV01', tag_id, 'system' FROM meta_tags WHERE tag_name IN ('experimental', 'economy-disabled', 'casual', 'vanilla-ish');

-- CREA01: creative, economy-creative, casual, persistent
INSERT INTO instance_tags (instance_id, tag_id, assigned_by)
SELECT 'CREA01', tag_id, 'system' FROM meta_tags WHERE tag_name IN ('creative', 'economy-creative', 'casual', 'persistent', 'vanilla-ish');
```

---

### 4. Worlds (Multi-World Support)

```sql
CREATE TABLE worlds (
    world_id SERIAL PRIMARY KEY,
    instance_id VARCHAR(16) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    -- World identification
    world_name VARCHAR(128) NOT NULL,              -- world, world_nether, world_the_end, creative, resource_world
    world_type VARCHAR(32),                        -- normal, nether, end, flat, custom
    
    -- World metadata
    seed BIGINT,
    generator VARCHAR(64),                         -- Default, TerraformGenerator, etc.
    difficulty VARCHAR(16),                        -- peaceful, easy, normal, hard
    
    -- State
    is_primary BOOLEAN DEFAULT false,              -- Main world for this instance
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(instance_id, world_name)
);

CREATE INDEX idx_worlds_instance ON worlds(instance_id);
CREATE INDEX idx_worlds_primary ON worlds(is_primary);
```

**Example Data**:
```sql
-- SMP101 worlds
INSERT INTO worlds (instance_id, world_name, world_type, is_primary, difficulty) VALUES
    ('SMP101', 'world', 'normal', true, 'normal'),
    ('SMP101', 'world_nether', 'nether', false, 'normal'),
    ('SMP101', 'world_the_end', 'end', false, 'normal'),
    ('SMP101', 'resource_world', 'normal', false, 'normal');

-- CREA01 worlds
INSERT INTO worlds (instance_id, world_name, world_type, is_primary, difficulty) VALUES
    ('CREA01', 'creative', 'flat', true, 'peaceful'),
    ('CREA01', 'plotworld', 'flat', false, 'peaceful');
```

---

### 5. World Tags (World-Level Meta Tags)

```sql
CREATE TABLE world_tags (
    world_tag_id SERIAL PRIMARY KEY,
    world_id INT REFERENCES worlds(world_id) ON DELETE CASCADE,
    tag_id INT REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by VARCHAR(64),
    
    UNIQUE(world_id, tag_id)
);

CREATE INDEX idx_world_tags_world ON world_tags(world_id);
CREATE INDEX idx_world_tags_tag ON world_tags(tag_id);
```

**Example**: Resource world is resetting, main world is persistent
```sql
-- Mark resource_world as resetting
INSERT INTO world_tags (world_id, tag_id, assigned_by)
SELECT w.world_id, t.tag_id, 'system'
FROM worlds w, meta_tags t
WHERE w.world_name = 'resource_world' AND t.tag_name = 'resetting';

-- Mark main world as persistent
INSERT INTO world_tags (world_id, tag_id, assigned_by)
SELECT w.world_id, t.tag_id, 'system'
FROM worlds w, meta_tags t
WHERE w.world_name = 'world' AND w.is_primary = true AND t.tag_name = 'persistent';
```

---

### 6. Regions (WorldGuard/Protection Regions)

```sql
CREATE TABLE regions (
    region_id SERIAL PRIMARY KEY,
    world_id INT REFERENCES worlds(world_id) ON DELETE CASCADE,
    
    -- Region identification
    region_name VARCHAR(128) NOT NULL,             -- spawn, shop_district, pvp_arena, etc.
    region_type VARCHAR(32),                       -- spawn, protected, pvp, shop, dungeon, etc.
    
    -- Coordinates (bounding box)
    min_x INT,
    min_y INT,
    min_z INT,
    max_x INT,
    max_y INT,
    max_z INT,
    
    -- Parent region (for nested regions)
    parent_region_id INT REFERENCES regions(region_id),
    
    -- Priority
    priority INT DEFAULT 0,
    
    -- State
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(world_id, region_name)
);

CREATE INDEX idx_regions_world ON regions(world_id);
CREATE INDEX idx_regions_type ON regions(region_type);
CREATE INDEX idx_regions_parent ON regions(parent_region_id);
```

**Example Data**:
```sql
-- SMP101 spawn region
INSERT INTO regions (world_id, region_name, region_type, min_x, min_y, min_z, max_x, max_y, max_z, priority)
SELECT world_id, 'spawn', 'spawn', -100, 0, -100, 100, 256, 100, 100
FROM worlds WHERE instance_id = 'SMP101' AND world_name = 'world';

-- SMP101 shop district
INSERT INTO regions (world_id, region_name, region_type, min_x, min_y, min_z, max_x, max_y, max_z, priority)
SELECT world_id, 'shop_district', 'shop', 200, 60, -50, 400, 120, 150, 50
FROM worlds WHERE instance_id = 'SMP101' AND world_name = 'world';
```

---

### 7. Region Tags (Region-Level Meta Tags)

```sql
CREATE TABLE region_tags (
    region_tag_id SERIAL PRIMARY KEY,
    region_id INT REFERENCES regions(region_id) ON DELETE CASCADE,
    tag_id INT REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by VARCHAR(64),
    
    UNIQUE(region_id, tag_id)
);

CREATE INDEX idx_region_tags_region ON region_tags(region_id);
CREATE INDEX idx_region_tags_tag ON region_tags(tag_id);
```

**Example**: PvP arena is pvp-enabled, spawn is pvp-disabled
```sql
-- Create pvp_arena region and tag it
INSERT INTO regions (world_id, region_name, region_type, min_x, min_y, min_z, max_x, max_y, max_z, priority)
SELECT world_id, 'pvp_arena', 'pvp', -500, 60, -500, -300, 90, -300, 75
FROM worlds WHERE instance_id = 'SMP101' AND world_name = 'world';

INSERT INTO region_tags (region_id, tag_id, assigned_by)
SELECT r.region_id, t.tag_id, 'system'
FROM regions r, meta_tags t
WHERE r.region_name = 'pvp_arena' AND t.tag_name = 'pvp-enabled';
```

---

### 8. Instance Groups (Meta-Server Clustering)

**Purpose**: Arbitrary logical grouping of instances beyond physical server assignment. Enables "meta-servers" based on ANY shared characteristic (physical location, gameplay mode, admin classification, etc.).

```sql
CREATE TABLE instance_groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,        -- "creative-servers", "hetzner-cluster", "production"
    group_type VARCHAR(32),                        -- "physical", "logical", "administrative"
    description TEXT,
    color_code VARCHAR(16),                        -- For GUI highlighting
    is_system_group BOOLEAN DEFAULT false,         -- Built-in vs custom
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE instance_group_members (
    member_id SERIAL PRIMARY KEY,
    instance_id VARCHAR(16) REFERENCES instances(instance_id) ON DELETE CASCADE,
    group_id INT REFERENCES instance_groups(group_id) ON DELETE CASCADE,
    
    -- Assignment metadata
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by VARCHAR(64),
    assignment_note TEXT,
    
    UNIQUE(instance_id, group_id)
);

CREATE INDEX idx_instance_group_members_instance ON instance_group_members(instance_id);
CREATE INDEX idx_instance_group_members_group ON instance_group_members(group_id);
```

**Example Data**:
```sql
-- Physical grouping (hardware-based meta-servers)
INSERT INTO instance_groups (group_name, group_type, description, is_system_group) VALUES
    ('hetzner-cluster', 'physical', 'All instances on Hetzner Xeon server (135.181.212.169)', true),
    ('ovh-cluster', 'physical', 'All instances on OVH Ryzen server (37.187.143.41)', true);

-- Logical grouping (gameplay-based meta-servers)
INSERT INTO instance_groups (group_name, group_type, description, is_system_group) VALUES
    ('creative-servers', 'logical', 'All instances allowing creative mode instance-wide', false),
    ('survival-servers', 'logical', 'All survival-focused instances', false),
    ('economy-servers', 'logical', 'All instances with economy system enabled', false),
    ('pvp-servers', 'logical', 'All instances with PvP enabled', false);

-- Administrative grouping (operational classification)
INSERT INTO instance_groups (group_name, group_type, description, is_system_group) VALUES
    ('production', 'administrative', 'Production instances available to players', true),
    ('development', 'administrative', 'Dev/test instances for staff only', true),
    ('experimental', 'administrative', 'Experimental feature testing grounds', true);

-- Assign instances to groups
INSERT INTO instance_group_members (instance_id, group_id, assigned_by)
SELECT 'SMP101', group_id, 'system' FROM instance_groups 
WHERE group_name IN ('hetzner-cluster', 'survival-servers', 'economy-servers', 'production');

INSERT INTO instance_group_members (instance_id, group_id, assigned_by)
SELECT 'DEV01', group_id, 'system' FROM instance_groups 
WHERE group_name IN ('hetzner-cluster', 'development');

INSERT INTO instance_group_members (instance_id, group_id, assigned_by)
SELECT 'CREA01', group_id, 'system' FROM instance_groups 
WHERE group_name IN ('ovh-cluster', 'creative-servers', 'production');
```

---

### 9. World Groups (Meta-World Clustering)

**Purpose**: Logical grouping of worlds across instances. Enables rules like "all resource-worlds reset weekly" or "all survival-worlds have keep-inventory disabled".

```sql
CREATE TABLE world_groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,        -- "resource-worlds", "survival-worlds", "spawn-worlds"
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE world_group_members (
    member_id SERIAL PRIMARY KEY,
    world_id INT REFERENCES worlds(world_id) ON DELETE CASCADE,
    group_id INT REFERENCES world_groups(group_id) ON DELETE CASCADE,
    
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by VARCHAR(64),
    
    UNIQUE(world_id, group_id)
);

CREATE INDEX idx_world_group_members_world ON world_group_members(world_id);
CREATE INDEX idx_world_group_members_group ON world_group_members(group_id);
```

**Example Data**:
```sql
INSERT INTO world_groups (group_name, description, is_system_group) VALUES
    ('resource-worlds', 'Resource gathering worlds that reset periodically', false),
    ('survival-worlds', 'Main persistent survival worlds', false),
    ('spawn-worlds', 'Hub/spawn/lobby worlds', false),
    ('creative-worlds', 'Creative building worlds', false),
    ('end-worlds', 'The End dimensions across all instances', true),
    ('nether-worlds', 'Nether dimensions across all instances', true);

-- Assign worlds to groups
INSERT INTO world_group_members (world_id, group_id, assigned_by)
SELECT w.world_id, g.group_id, 'system'
FROM worlds w, world_groups g
WHERE w.world_name = 'resource_world' AND g.group_name = 'resource-worlds';

INSERT INTO world_group_members (world_id, group_id, assigned_by)
SELECT w.world_id, g.group_id, 'system'
FROM worlds w, world_groups g
WHERE w.world_name = 'world' AND w.is_primary = true AND g.group_name = 'survival-worlds';

INSERT INTO world_group_members (world_id, group_id, assigned_by)
SELECT w.world_id, g.group_id, 'system'
FROM worlds w, world_groups g
WHERE w.world_type = 'end' AND g.group_name = 'end-worlds';
```

---

### 10. Region Groups (Meta-Region Clustering)

**Purpose**: Logical grouping of regions across worlds and instances. Enables rules like "all pvp-arenas disable teleportation" or "all safe-zones have keep-inventory enabled".

```sql
CREATE TABLE region_groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,        -- "pvp-arenas", "safe-zones", "admin-areas"
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE region_group_members (
    member_id SERIAL PRIMARY KEY,
    region_id INT REFERENCES regions(region_id) ON DELETE CASCADE,
    group_id INT REFERENCES region_groups(group_id) ON DELETE CASCADE,
    
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by VARCHAR(64),
    
    UNIQUE(region_id, group_id)
);

CREATE INDEX idx_region_group_members_region ON region_group_members(region_id);
CREATE INDEX idx_region_group_members_group ON region_group_members(group_id);
```

**Example Data**:
```sql
INSERT INTO region_groups (group_name, description, is_system_group) VALUES
    ('pvp-arenas', 'All PvP combat zones across all servers', false),
    ('safe-zones', 'Protected areas where PvP/damage is disabled', false),
    ('spawn-areas', 'Server spawn regions', true),
    ('admin-areas', 'Staff-only restricted zones', false),
    ('shop-districts', 'Player shop/trade areas', false),
    ('event-zones', 'Temporary event regions', false);

-- Assign regions to groups
INSERT INTO region_group_members (region_id, group_id, assigned_by)
SELECT r.region_id, g.group_id, 'system'
FROM regions r, region_groups g
WHERE r.region_type = 'pvp' AND g.group_name = 'pvp-arenas';

INSERT INTO region_group_members (region_id, group_id, assigned_by)
SELECT r.region_id, g.group_id, 'system'
FROM regions r, region_groups g
WHERE r.region_type = 'spawn' AND g.group_name = 'spawn-areas';

INSERT INTO region_group_members (region_id, group_id, assigned_by)
SELECT r.region_id, g.group_id, 'system'
FROM regions r, region_groups g
WHERE r.region_type = 'shop' AND g.group_name = 'shop-districts';
```

---

### 11. Configuration Rules (Hierarchical Settings)

```sql
CREATE TABLE config_rules (
    rule_id SERIAL PRIMARY KEY,
    
    -- What is being configured
    plugin_name VARCHAR(64) NOT NULL,              -- EliteMobs, HuskSync, LuckPerms, etc.
    config_key VARCHAR(512) NOT NULL,              -- damage.lightning-elite, database.host, etc.
    config_file VARCHAR(256),                      -- config.yml, settings.conf, etc.
    
    -- Scope definition
    scope_type VARCHAR(16) NOT NULL,               -- GLOBAL, SERVER, INSTANCE_GROUP, META_TAG, INSTANCE, WORLD_GROUP, WORLD, REGION_GROUP, REGION
    scope_selector VARCHAR(128),                   -- NULL for GLOBAL, server name, group name, instance ID, world name, region name
    
    -- Tag logic (for META_TAG scope only)
    tag_logic_type VARCHAR(16) DEFAULT 'AND',     -- AND, OR, EXCEPT
    tag_logic_expression TEXT,                     -- JSON: ["survival", "economy-enabled"] AND NOT ["creative"]
    
    -- World/Region specificity (optional)
    world_filter VARCHAR(128),                     -- world, world_nether, resource_world, NULL = all worlds
    region_filter VARCHAR(128),                    -- spawn, shop_district, NULL = all regions
    
    -- Value
    config_value TEXT,                             -- Actual value or {{VARIABLE}}
    value_type VARCHAR(16),                        -- string, int, float, boolean, json, yaml
    
    -- Priority (auto-calculated from scope_type)
    priority INT NOT NULL,                         -- 0=PLAYER_OVERRIDE, 1=REGION, 2=REGION_GROUP, 3=WORLD, 4=WORLD_GROUP, 5=INSTANCE, 6=INSTANCE_GROUP, 7=META_TAG, 8=SERVER, 9=GLOBAL
    
    -- Validation
    is_expected_variance BOOLEAN DEFAULT true,     -- false = red flag (drift)
    validation_regex VARCHAR(256),                 -- Optional validation pattern
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(64),
    last_modified_at TIMESTAMP DEFAULT NOW(),
    last_modified_by VARCHAR(64),
    is_active BOOLEAN DEFAULT true,
    notes TEXT
);

CREATE INDEX idx_config_rules_plugin ON config_rules(plugin_name);
CREATE INDEX idx_config_rules_key ON config_rules(config_key);
CREATE INDEX idx_config_rules_scope ON config_rules(scope_type, scope_selector);
CREATE INDEX idx_config_rules_priority ON config_rules(priority);
CREATE INDEX idx_config_rules_active ON config_rules(is_active);

-- Composite index for resolution queries
CREATE INDEX idx_config_rules_lookup ON config_rules(plugin_name, config_key, is_active, priority);
```

**Priority Assignment**:
```sql
-- Trigger to auto-calculate priority based on scope_type
CREATE OR REPLACE FUNCTION set_config_rule_priority()
RETURNS TRIGGER AS $$
BEGIN
    NEW.priority := CASE NEW.scope_type
        WHEN 'PLAYER_OVERRIDE' THEN 0
        WHEN 'REGION' THEN 1
        WHEN 'REGION_GROUP' THEN 2
        WHEN 'WORLD' THEN 3
        WHEN 'WORLD_GROUP' THEN 4
        WHEN 'INSTANCE' THEN 5
        WHEN 'INSTANCE_GROUP' THEN 6
        WHEN 'META_TAG' THEN 7
        WHEN 'SERVER' THEN 8
        WHEN 'GLOBAL' THEN 9
        ELSE 999
    END;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER config_rule_priority_trigger
    BEFORE INSERT OR UPDATE ON config_rules
    FOR EACH ROW
    EXECUTE FUNCTION set_config_rule_priority();
```

**Example Data**:
```sql
-- GLOBAL: EliteMobs version (all instances)
INSERT INTO config_rules (plugin_name, config_key, scope_type, config_value, value_type, created_by) VALUES
    ('EliteMobs', 'version', 'GLOBAL', '9.2.9', 'string', 'system');

-- SERVER: Database host (per physical server)
INSERT INTO config_rules (plugin_name, config_key, scope_type, scope_selector, config_value, value_type, created_by) VALUES
    ('CoreProtect', 'mysql-host', 'SERVER', 'hetzner-xeon', '135.181.212.169', 'string', 'system'),
    ('CoreProtect', 'mysql-host', 'SERVER', 'ovh-ryzen', '37.187.143.41', 'string', 'system');

-- INSTANCE_GROUP: Creative servers all have keep-inventory enabled
INSERT INTO config_rules (plugin_name, config_key, scope_type, scope_selector, config_value, value_type, created_by) VALUES
    ('server', 'keep-inventory', 'INSTANCE_GROUP', 'creative-servers', 'true', 'boolean', 'admin'),
    ('server', 'spawn-monsters', 'INSTANCE_GROUP', 'creative-servers', 'false', 'boolean', 'admin');

-- META_TAG: Elite spawn rate (survival servers only)
INSERT INTO config_rules (plugin_name, config_key, scope_type, tag_logic_type, tag_logic_expression, config_value, value_type, created_by) VALUES
    ('EliteMobs', 'spawn-elite-rate', 'META_TAG', 'AND', '["survival", "pve-focused"]', '0.05', 'float', 'system'),
    ('EliteMobs', 'spawn-elite-rate', 'META_TAG', 'AND', '["creative"]', '0.0', 'float', 'system');

-- INSTANCE: Spawn protection (unique per instance)
INSERT INTO config_rules (plugin_name, config_key, scope_type, scope_selector, config_value, value_type, created_by) VALUES
    ('server', 'spawn-protection', 'INSTANCE', 'SMP101', '32', 'int', 'admin'),
    ('server', 'spawn-protection', 'INSTANCE', 'DEV01', '0', 'int', 'admin');

-- WORLD_GROUP: All resource worlds reset weekly
INSERT INTO config_rules (plugin_name, config_key, scope_type, scope_selector, config_value, value_type, created_by) VALUES
    ('MultiVerse', 'auto-reset-days', 'WORLD_GROUP', 'resource-worlds', '7', 'int', 'admin'),
    ('MultiVerse', 'announce-reset', 'WORLD_GROUP', 'resource-worlds', 'true', 'boolean', 'admin');

-- WORLD: PvP enabled (per world)
INSERT INTO config_rules (plugin_name, config_key, scope_type, scope_selector, world_filter, config_value, value_type, created_by) VALUES
    ('server', 'pvp', 'WORLD', 'SMP101', 'world', 'true', 'boolean', 'admin'),
    ('server', 'pvp', 'WORLD', 'SMP101', 'resource_world', 'true', 'boolean', 'admin'),
    ('server', 'pvp', 'WORLD', 'CREA01', 'creative', 'false', 'boolean', 'admin');

-- REGION_GROUP: All PvP arenas disable teleportation
INSERT INTO config_rules (plugin_name, config_key, scope_type, scope_selector, config_value, value_type, created_by) VALUES
    ('EssentialsX', 'allow-teleport', 'REGION_GROUP', 'pvp-arenas', 'false', 'boolean', 'admin'),
    ('EssentialsX', 'allow-home', 'REGION_GROUP', 'pvp-arenas', 'false', 'boolean', 'admin');

-- REGION: Build permissions (region-specific)
INSERT INTO config_rules (plugin_name, config_key, scope_type, scope_selector, region_filter, config_value, value_type, created_by) VALUES
    ('WorldGuard', 'flags.build', 'REGION', 'SMP101', 'spawn', 'deny', 'string', 'admin'),
    ('WorldGuard', 'flags.build', 'REGION', 'SMP101', 'shop_district', 'allow', 'string', 'admin');
```

---

### 9. Configuration Variables (Template Substitution)

```sql
CREATE TABLE config_variables (
    variable_id SERIAL PRIMARY KEY,
    
    -- Scope (where this variable applies)
    scope_type VARCHAR(16) NOT NULL,               -- GLOBAL, SERVER, INSTANCE, WORLD
    scope_selector VARCHAR(128),                   -- NULL for GLOBAL, instance_id, server_name, etc.
    
    -- Variable definition
    variable_name VARCHAR(64) NOT NULL,            -- SHORTNAME, SERVER_PORT, DATABASE_NAME, etc.
    variable_value TEXT NOT NULL,
    value_type VARCHAR(16) DEFAULT 'string',
    
    -- Metadata
    description TEXT,
    is_system_variable BOOLEAN DEFAULT true,       -- Built-in vs custom
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(scope_type, scope_selector, variable_name)
);

CREATE INDEX idx_variables_scope ON config_variables(scope_type, scope_selector);
CREATE INDEX idx_variables_name ON config_variables(variable_name);
```

**Example Data**:
```sql
-- GLOBAL variables
INSERT INTO config_variables (scope_type, variable_name, variable_value, description, is_system_variable) VALUES
    ('GLOBAL', 'NETWORK_NAME', 'ArchiveSMP', 'Network display name', true),
    ('GLOBAL', 'MYSQL_USER', 'sqlworkerSMP', 'Database username', true),
    ('GLOBAL', 'MYSQL_PASSWORD', 'SQLdb2024!', 'Database password', true);

-- SERVER variables
INSERT INTO config_variables (scope_type, scope_selector, variable_name, variable_value, is_system_variable) VALUES
    ('SERVER', 'hetzner-xeon', 'MYSQL_HOST', '135.181.212.169', true),
    ('SERVER', 'hetzner-xeon', 'MYSQL_PORT', '3369', true),
    ('SERVER', 'ovh-ryzen', 'MYSQL_HOST', '37.187.143.41', true),
    ('SERVER', 'ovh-ryzen', 'MYSQL_PORT', '3369', true);

-- INSTANCE variables
INSERT INTO config_variables (scope_type, scope_selector, variable_name, variable_value, is_system_variable) VALUES
    ('INSTANCE', 'SMP101', 'SHORTNAME', 'SMP101', true),
    ('INSTANCE', 'SMP101', 'SERVER_PORT', '25565', true),
    ('INSTANCE', 'SMP101', 'DATABASE_NAME', 'asmp_SQL', true),
    ('INSTANCE', 'SMP101', 'CLUSTER_ID', 'SMPNET', true),
    
    ('INSTANCE', 'DEV01', 'SHORTNAME', 'DEV01', true),
    ('INSTANCE', 'DEV01', 'SERVER_PORT', '25566', true),
    ('INSTANCE', 'DEV01', 'DATABASE_NAME', 'asmp_DEV', true),
    ('INSTANCE', 'DEV01', 'CLUSTER_ID', 'DEVnet', true),
    
    ('INSTANCE', 'CREA01', 'SHORTNAME', 'CREA01', true),
    ('INSTANCE', 'CREA01', 'SERVER_PORT', '25565', true),
    ('INSTANCE', 'CREA01', 'DATABASE_NAME', 'asmp_CREA', true),
    ('INSTANCE', 'CREA01', 'CLUSTER_ID', 'SMPNET', true);

-- WORLD variables (example: different seeds per world)
INSERT INTO config_variables (scope_type, scope_selector, variable_name, variable_value, is_system_variable) VALUES
    ('WORLD', 'SMP101:world', 'WORLD_SEED', '1234567890', true),
    ('WORLD', 'SMP101:resource_world', 'WORLD_SEED', '9876543210', true);
```

---

### 10. Variance Detection Cache (Performance)

```sql
CREATE TABLE config_variance_cache (
    cache_id SERIAL PRIMARY KEY,
    
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    
    -- Variance statistics
    total_instances INT,                           -- How many instances have this key
    unique_values INT,                             -- How many different values exist
    variance_type VARCHAR(16),                     -- NONE, VARIABLE, META_TAG, INSTANCE, WORLD, REGION, DRIFT
    
    -- Expected vs unexpected
    is_expected_variance BOOLEAN DEFAULT true,     -- Green (expected) vs Red (drift)
    variance_reason TEXT,                          -- "Uses {{SHORTNAME}} variable", "Tagged by survival/creative"
    
    -- Cache metadata
    last_calculated TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(plugin_name, config_key)
);

CREATE INDEX idx_variance_cache_plugin ON config_variance_cache(plugin_name);
CREATE INDEX idx_variance_cache_type ON config_variance_cache(variance_type);
CREATE INDEX idx_variance_cache_drift ON config_variance_cache(is_expected_variance);
```

---

### 11. Tag Logic Expressions (AND/EXCEPT Support)

```sql
CREATE TABLE tag_logic_operators (
    operator_id SERIAL PRIMARY KEY,
    operator_name VARCHAR(16) UNIQUE NOT NULL,     -- AND, OR, NOT, EXCEPT
    description TEXT,
    precedence INT DEFAULT 0                       -- For parsing order
);

INSERT INTO tag_logic_operators (operator_name, description, precedence) VALUES
    ('AND', 'All tags must match', 3),
    ('OR', 'Any tag can match', 2),
    ('NOT', 'Exclude these tags', 4),
    ('EXCEPT', 'Alias for NOT', 4);
```

**Tag Logic Expression Format** (stored in `config_rules.tag_logic_expression` as JSON):

```json
{
  "include": ["survival", "economy-enabled"],
  "exclude": ["creative", "experimental"]
}
```

**Interpreted as**: `(survival AND economy-enabled) EXCEPT (creative OR experimental)`

---

## Supporting Tables (from previous schemas)

### 12. Rank System (Progression)

```sql
CREATE TABLE rank_definitions (
    rank_id INT PRIMARY KEY,
    rank_type VARCHAR(16) NOT NULL,                -- 'primary' or 'prestige'
    rank_name VARCHAR(32) NOT NULL,
    rank_order INT NOT NULL,
    
    display_color VARCHAR(16),
    chat_prefix TEXT,
    tab_prefix TEXT,
    luckperms_group VARCHAR(64),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE player_ranks (
    player_uuid CHAR(36) PRIMARY KEY,
    current_rank_id INT REFERENCES rank_definitions(rank_id),
    current_prestige_id INT REFERENCES rank_definitions(rank_id),
    
    total_playtime_seconds BIGINT DEFAULT 0,
    total_quest_completions INT DEFAULT 0,
    total_mob_kills INT DEFAULT 0,
    rank_progress_percent DECIMAL(5,2) DEFAULT 0.00,
    
    last_rank_up TIMESTAMP,
    last_prestige TIMESTAMP,
    first_join TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_player_ranks_rank ON player_ranks(current_rank_id);
CREATE INDEX idx_player_ranks_prestige ON player_ranks(current_prestige_id);
```

---

### 13. Player Role System (Staff/Support/Donor Classifications)

```sql
CREATE TABLE player_role_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(64) NOT NULL UNIQUE,     -- staff, community, support, donor
    description TEXT,
    display_order INT DEFAULT 0,
    is_system_category BOOLEAN DEFAULT true
);

CREATE TABLE player_roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(64) NOT NULL UNIQUE,         -- admin, moderator, helper, patreon_tier1, etc.
    category_id INT REFERENCES player_role_categories(category_id),
    
    -- Display
    display_name VARCHAR(128),                     -- "Administrator", "Patreon Supporter"
    color_code VARCHAR(16),                        -- &c for admin, &6 for donor, etc.
    chat_prefix TEXT,                              -- [ADMIN], [MOD], [VIP], etc.
    tab_prefix TEXT,
    permission_weight INT DEFAULT 0,               -- Higher = more permissions
    
    -- LuckPerms integration
    luckperms_group VARCHAR(64),                   -- Map to LuckPerms group
    
    -- Metadata
    description TEXT,
    is_staff_role BOOLEAN DEFAULT false,           -- For staff-only features
    is_donor_role BOOLEAN DEFAULT false,           -- For donor perks
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_player_roles_category ON player_roles(category_id);
CREATE INDEX idx_player_roles_staff ON player_roles(is_staff_role);
CREATE INDEX idx_player_roles_donor ON player_roles(is_donor_role);
```

**Example Data**:
```sql
-- Categories
INSERT INTO player_role_categories (category_name, description, display_order) VALUES
    ('staff', 'Server staff and administrators', 1),
    ('community', 'Community helpers and moderators', 2),
    ('support', 'Support roles (builders, testers, etc.)', 3),
    ('donor', 'Financial supporters and patrons', 4);

-- Roles
INSERT INTO player_roles (role_name, category_id, display_name, color_code, chat_prefix, permission_weight, luckperms_group, is_staff_role) VALUES
    -- Staff
    ('owner', 1, 'Server Owner', '&4', '[OWNER]', 1000, 'owner', true),
    ('admin', 1, 'Administrator', '&c', '[ADMIN]', 900, 'admin', true),
    ('manager', 1, 'Manager', '&c', '[MANAGER]', 850, 'manager', true),
    
    -- Community
    ('moderator', 2, 'Moderator', '&2', '[MOD]', 700, 'moderator', true),
    ('helper', 2, 'Helper', '&a', '[HELPER]', 500, 'helper', false),
    ('trial_mod', 2, 'Trial Moderator', '&2', '[T-MOD]', 600, 'trial_mod', true),
    
    -- Support
    ('builder', 3, 'Builder', '&e', '[BUILDER]', 300, 'builder', false),
    ('developer', 3, 'Developer', '&b', '[DEV]', 400, 'developer', false),
    ('tester', 3, 'Tester', '&7', '[TESTER]', 200, 'tester', false),
    
    -- Donors
    ('patreon_deity', 4, 'Patreon Deity', '&d', '[DEITY]', 150, 'patreon_deity', false, true),
    ('patreon_legend', 4, 'Patreon Legend', '&d', '[LEGEND]', 140, 'patreon_legend', false, true),
    ('patreon_hero', 4, 'Patreon Hero', '&d', '[HERO]', 130, 'patreon_hero', false, true),
    ('patreon_supporter', 4, 'Patreon Supporter', '&d', '[VIP]', 120, 'patreon_supporter', false, true),
    ('lifetime_donor', 4, 'Lifetime Supporter', '&6', '[LIFETIME]', 110, 'lifetime_donor', false, true),
    ('monthly_donor', 4, 'Monthly Supporter', '&6', '[DONOR]', 100, 'monthly_donor', false, true);
```

---

### 14. Player Role Assignments

```sql
CREATE TABLE player_role_assignments (
    assignment_id SERIAL PRIMARY KEY,
    player_uuid CHAR(36) NOT NULL,
    role_id INT REFERENCES player_roles(role_id) ON DELETE CASCADE,
    
    -- Assignment scope (can be network-wide or specific)
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',       -- GLOBAL, SERVER, INSTANCE, WORLD, REGION
    scope_selector VARCHAR(128),                   -- NULL for global, instance_id, etc.
    
    -- Temporal
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by VARCHAR(64),                       -- Who granted this role
    expires_at TIMESTAMP,                          -- NULL = permanent, otherwise temp role
    
    -- Donor tracking
    subscription_id VARCHAR(128),                  -- Patreon/PayPal subscription ID
    last_payment_date TIMESTAMP,                   -- For donor role expiry tracking
    
    -- Metadata
    assignment_reason TEXT,                        -- "Promoted for excellent moderation"
    is_active BOOLEAN DEFAULT true,
    
    UNIQUE(player_uuid, role_id, scope_type, scope_selector)
);

CREATE INDEX idx_player_role_assign_player ON player_role_assignments(player_uuid);
CREATE INDEX idx_player_role_assign_role ON player_role_assignments(role_id);
CREATE INDEX idx_player_role_assign_scope ON player_role_assignments(scope_type, scope_selector);
CREATE INDEX idx_player_role_assign_active ON player_role_assignments(is_active);
CREATE INDEX idx_player_role_assign_expires ON player_role_assignments(expires_at) WHERE expires_at IS NOT NULL;
```

**Example Data**:
```sql
-- Player A is admin globally
INSERT INTO player_role_assignments (player_uuid, role_id, scope_type, assigned_by, assignment_reason) 
SELECT 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', role_id, 'GLOBAL', 'system', 'Server owner'
FROM player_roles WHERE role_name = 'owner';

-- Player B is moderator only on SMP101
INSERT INTO player_role_assignments (player_uuid, role_id, scope_type, scope_selector, assigned_by)
SELECT 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', role_id, 'INSTANCE', 'SMP101', 'admin_user'
FROM player_roles WHERE role_name = 'moderator';

-- Player C is helper in creative worlds only
INSERT INTO player_role_assignments (player_uuid, role_id, scope_type, scope_selector, assigned_by)
SELECT 'cccccccc-cccc-cccc-cccc-cccccccccccc', role_id, 'META_TAG', 'creative', 'admin_user'
FROM player_roles WHERE role_name = 'helper';

-- Player D is patreon supporter (expires in 30 days)
INSERT INTO player_role_assignments (player_uuid, role_id, scope_type, assigned_by, expires_at, subscription_id)
SELECT 'dddddddd-dddd-dddd-dddd-dddddddddddd', role_id, 'GLOBAL', 'patreon_webhook', 
       NOW() + INTERVAL '30 days', 'patreon_sub_12345'
FROM player_roles WHERE role_name = 'patreon_supporter';
```

---

### 15. Player-Specific Config Overrides

```sql
CREATE TABLE player_config_overrides (
    override_id SERIAL PRIMARY KEY,
    
    -- Player identification
    player_uuid CHAR(36) NOT NULL,
    
    -- What config is overridden
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    
    -- Scope (where this override applies)
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',       -- GLOBAL, SERVER, INSTANCE, WORLD, REGION
    scope_selector VARCHAR(128),
    world_filter VARCHAR(128),
    region_filter VARCHAR(128),
    
    -- Override value
    override_value TEXT NOT NULL,
    value_type VARCHAR(16) DEFAULT 'string',
    
    -- Why this override exists
    override_reason TEXT,                          -- "Admin bypass for testing", "VIP perk", etc.
    granted_by VARCHAR(64),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,                          -- NULL = permanent
    
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_player_overrides_player ON player_config_overrides(player_uuid);
CREATE INDEX idx_player_overrides_plugin ON player_config_overrides(plugin_name, config_key);
CREATE INDEX idx_player_overrides_scope ON player_config_overrides(scope_type, scope_selector);
CREATE INDEX idx_player_overrides_active ON player_config_overrides(is_active);
```

**Example Use Cases**:
```sql
-- Admin has no spawn protection cooldown
INSERT INTO player_config_overrides (player_uuid, plugin_name, config_key, override_value, override_reason, granted_by)
VALUES ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'Essentials', 'spawn-cooldown', '0', 'Admin bypass', 'system');

-- VIP donor gets increased homes
INSERT INTO player_config_overrides (player_uuid, plugin_name, config_key, override_value, override_reason, granted_by)
VALUES ('dddddddd-dddd-dddd-dddd-dddddddddddd', 'Essentials', 'max-homes', '10', 'Patreon VIP perk', 'donor_system');

-- Builder has worldedit in creative world only
INSERT INTO player_config_overrides (player_uuid, plugin_name, config_key, scope_type, scope_selector, override_value, granted_by)
VALUES ('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee', 'WorldEdit', 'max-blocks', 'INSTANCE', 'CREA01', '1000000', 'admin_user');

-- Tester can bypass region restrictions in test regions
INSERT INTO player_config_overrides (player_uuid, plugin_name, config_key, scope_type, region_filter, override_value, granted_by)
SELECT 'ffffffff-ffff-ffff-ffff-ffffffffffff', 'WorldGuard', 'build-permission', 'REGION', 'test_zone', 'allow', 'system'
FROM regions WHERE region_name = 'test_zone';
```

---

## Resolution Algorithm Pseudocode

```python
def resolve_config_value(plugin_name: str, config_key: str, 
                         instance_id: str, world_name: str = None, 
                         region_name: str = None, 
                         player_uuid: str = None) -> str:
    """
    Resolve final config value using hierarchical priority:
    PLAYER_OVERRIDE (0) > REGION (1) > WORLD (2) > INSTANCE (3) > META_TAG (4) > SERVER (5) > GLOBAL (6)
    
    Supports player-specific overrides for granular control like:
    "Player X (admin role) can do Y (build) in Z region (spawn) 
     of AA world (world) on BB instance (SMP101) on CC server (hetzner-xeon)"
    """
    
    # Get instance metadata
    instance = get_instance(instance_id)
    instance_tags = get_instance_tags(instance_id)
    
    # Get world metadata (if specified)
    world = None
    world_tags = []
    if world_name:
        world = get_world(instance_id, world_name)
        world_tags = get_world_tags(world.world_id)
    
    # Get region metadata (if specified)
    region = None
    region_tags = []
    if region_name and world:
        region = get_region(world.world_id, region_name)
        region_tags = get_region_tags(region.region_id)
    
    # Get player metadata (if specified)
    player_roles = []
    player_rank = None
    player_prestige = None
    if player_uuid:
        player_roles = get_player_roles(player_uuid, instance_id, world_name, region_name)
        player_rank = get_player_rank(player_uuid)
        player_prestige = get_player_prestige(player_uuid)
        
        # CHECK PLAYER-SPECIFIC OVERRIDES FIRST (highest priority)
        player_override = db.query_one("""
            SELECT override_value
            FROM player_config_overrides
            WHERE player_uuid = ?
            AND plugin_name = ?
            AND config_key = ?
            AND is_active = true
            AND (expires_at IS NULL OR expires_at > NOW())
            AND (scope_type = 'GLOBAL' 
                 OR (scope_type = 'SERVER' AND scope_selector = ?)
                 OR (scope_type = 'INSTANCE' AND scope_selector = ?)
                 OR (scope_type = 'WORLD' AND world_filter = ?)
                 OR (scope_type = 'REGION' AND region_filter = ?))
            ORDER BY CASE scope_type
                WHEN 'REGION' THEN 1
                WHEN 'WORLD' THEN 2
                WHEN 'INSTANCE' THEN 3
                WHEN 'SERVER' THEN 4
                WHEN 'GLOBAL' THEN 5
            END
            LIMIT 1
        """, player_uuid, plugin_name, config_key, 
             instance.server_name, instance_id, world_name, region_name)
        
        if player_override:
            return substitute_variables(player_override.override_value, instance_id, world_name)
    
    # Fetch all applicable rules, ordered by priority (lower = higher priority)
    rules = db.query("""
        SELECT scope_type, scope_selector, tag_logic_expression, 
               world_filter, region_filter, config_value, priority
        FROM config_rules
        WHERE plugin_name = ? 
        AND config_key = ?
        AND is_active = true
        ORDER BY priority ASC
    """, plugin_name, config_key)
    
    final_value = None
    
    for rule in rules:
        # GLOBAL: Always applies
        if rule.scope_type == 'GLOBAL':
            final_value = rule.config_value
            
        # SERVER: Check if instance is on this server
        elif rule.scope_type == 'SERVER':
            if instance.server_name == rule.scope_selector:
                final_value = rule.config_value
                
        # META_TAG: Check tag logic
        elif rule.scope_type == 'META_TAG':
            if evaluate_tag_logic(rule.tag_logic_expression, instance_tags):
                final_value = rule.config_value
                
        # INSTANCE: Check exact match
        elif rule.scope_type == 'INSTANCE':
            if instance_id == rule.scope_selector:
                # Check world filter
                if rule.world_filter:
                    if world_name != rule.world_filter:
                        continue
                # Check region filter
                if rule.region_filter:
                    if region_name != rule.region_filter:
                        continue
                final_value = rule.config_value
                
        # WORLD: Check world match and world tags
        elif rule.scope_type == 'WORLD':
            if world and (rule.scope_selector == instance_id or not rule.scope_selector):
                if rule.world_filter == world_name or not rule.world_filter:
                    # Check world tags if specified
                    if rule.tag_logic_expression:
                        if evaluate_tag_logic(rule.tag_logic_expression, world_tags):
                            final_value = rule.config_value
                    else:
                        final_value = rule.config_value
                        
        # REGION: Check region match and region tags
        elif rule.scope_type == 'REGION':
            if region and rule.region_filter == region_name:
                # Check region tags if specified
                if rule.tag_logic_expression:
                    if evaluate_tag_logic(rule.tag_logic_expression, region_tags):
                        final_value = rule.config_value
                        break  # Highest priority, stop here
                else:
                    final_value = rule.config_value
                    break  # Highest priority, stop here
    
    # Substitute variables
    if final_value and '{{' in final_value:
        final_value = substitute_variables(final_value, instance_id, world_name, player_uuid)
    
    return final_value


def get_player_roles(player_uuid: str, instance_id: str = None, 
                     world_name: str = None, region_name: str = None) -> List[str]:
    """
    Get all active roles for a player in the current context.
    Returns role names that apply in this scope.
    """
    query = """
        SELECT pr.role_name
        FROM player_role_assignments pra
        JOIN player_roles pr ON pra.role_id = pr.role_id
        WHERE pra.player_uuid = ?
        AND pra.is_active = true
        AND (pra.expires_at IS NULL OR pra.expires_at > NOW())
        AND (
            pra.scope_type = 'GLOBAL'
            OR (pra.scope_type = 'INSTANCE' AND pra.scope_selector = ?)
            OR (pra.scope_type = 'WORLD' AND pra.scope_selector LIKE ?)
            OR (pra.scope_type = 'REGION' AND pra.scope_selector LIKE ?)
        )
    """
    
    world_pattern = f"{instance_id}:{world_name}" if world_name else "%"
    region_pattern = f"{instance_id}:{world_name}:{region_name}" if region_name else "%"
    
    roles = db.query(query, player_uuid, instance_id, world_pattern, region_pattern)
    return [r.role_name for r in roles]


def check_player_permission(player_uuid: str, permission: str, 
                            instance_id: str, world_name: str = None, 
                            region_name: str = None) -> bool:
    """
    Check if player has a specific permission based on their roles.
    Example: check_player_permission(uuid, "worldedit.use", "SMP101", "world", "spawn")
    """
    roles = get_player_roles(player_uuid, instance_id, world_name, region_name)
    
    # Check if any role grants this permission
    # This would integrate with LuckPerms or custom permission system
    for role_name in roles:
        role_perms = get_role_permissions(role_name)
        if permission in role_perms or has_wildcard_permission(role_perms, permission):
            return True
    
    return False


def evaluate_tag_logic(expression_json: str, assigned_tags: List[str]) -> bool:
    """
    Evaluate tag logic expression.
    Format: {"include": ["tag1", "tag2"], "exclude": ["tag3"]}
    Returns: (tag1 AND tag2) AND NOT (tag3)
    """
    if not expression_json:
        return True
    
    expr = json.loads(expression_json)
    
    # Check include (AND logic)
    if 'include' in expr:
        for required_tag in expr['include']:
            if required_tag not in assigned_tags:
                return False  # Missing required tag
    
    # Check exclude (NOT logic)
    if 'exclude' in expr:
        for excluded_tag in expr['exclude']:
            if excluded_tag in assigned_tags:
                return False  # Has excluded tag
    
    return True  # All conditions met


def substitute_variables(value: str, instance_id: str, world_name: str = None, 
                        player_uuid: str = None) -> str:
    """
    Replace {{VARIABLE}} with actual values.
    Priority: PLAYER > WORLD > INSTANCE > SERVER > GLOBAL
    
    Player variables: {{PLAYER_NAME}}, {{PLAYER_RANK}}, {{PLAYER_ROLE}}
    """
    # Get all applicable variables
    variables = {}
    
    # GLOBAL variables
    global_vars = get_variables('GLOBAL', None)
    variables.update(global_vars)
    
    # SERVER variables
    instance = get_instance(instance_id)
    server_vars = get_variables('SERVER', instance.server_name)
    variables.update(server_vars)
    
    # INSTANCE variables
    instance_vars = get_variables('INSTANCE', instance_id)
    variables.update(instance_vars)
    
    # WORLD variables (if world specified)
    if world_name:
        world_vars = get_variables('WORLD', f"{instance_id}:{world_name}")
        variables.update(world_vars)
    
    # PLAYER variables (if player specified)
    if player_uuid:
        player_name = get_player_name(player_uuid)
        player_rank = get_player_rank(player_uuid)
        player_roles = get_player_roles(player_uuid, instance_id, world_name)
        
        variables.update({
            'PLAYER_UUID': player_uuid,
            'PLAYER_NAME': player_name,
            'PLAYER_RANK': player_rank.rank_name if player_rank else 'None',
            'PLAYER_PRESTIGE': get_player_prestige(player_uuid).rank_name if get_player_prestige(player_uuid) else 'None',
            'PLAYER_PRIMARY_ROLE': player_roles[0] if player_roles else 'player',
            'PLAYER_ROLES': ','.join(player_roles) if player_roles else 'player'
        })
    
    # Substitute
    for var_name, var_value in variables.items():
        value = value.replace(f"{{{{{var_name}}}}}", str(var_value))
    
    return value
```

---

## Real-World Example: Ultra-Granular Permission

**Scenario**: "Admin player can bypass spawn protection in the spawn region of the main world on SMP101 server on Hetzner"

```sql
-- Step 1: Ensure player has admin role globally
INSERT INTO player_role_assignments (player_uuid, role_id, scope_type, assigned_by)
SELECT 'admin-uuid-1234', role_id, 'GLOBAL', 'owner'
FROM player_roles WHERE role_name = 'admin';

-- Step 2: Create player-specific override for spawn protection bypass
INSERT INTO player_config_overrides 
    (player_uuid, plugin_name, config_key, 
     scope_type, scope_selector, world_filter, region_filter, 
     override_value, override_reason, granted_by)
VALUES 
    ('admin-uuid-1234', 'WorldGuard', 'spawn-protection-bypass', 
     'REGION', 'SMP101', 'world', 'spawn',
     'true', 'Admin testing needs', 'owner');

-- Step 3: Query resolution
SELECT resolve_config_value(
    plugin_name := 'WorldGuard',
    config_key := 'spawn-protection-bypass',
    instance_id := 'SMP101',
    world_name := 'world',
    region_name := 'spawn',
    player_uuid := 'admin-uuid-1234'
);
-- Returns: 'true' (from player override, priority 0)

-- Step 4: Same query for regular player
SELECT resolve_config_value(
    plugin_name := 'WorldGuard',
    config_key := 'spawn-protection-bypass',
    instance_id := 'SMP101',
    world_name := 'world',
    region_name := 'spawn',
    player_uuid := 'regular-player-uuid'
);
-- Returns: 'false' (from global/region rule, no player override exists)
```

**Another Example**: "Patreon VIP gets increased home limit only on survival instances"

```sql
-- Player has patreon_hero role
INSERT INTO player_role_assignments (player_uuid, role_id, scope_type, scope_selector, assigned_by, subscription_id)
SELECT 'vip-uuid-5678', role_id, 'META_TAG', 'survival', 'patreon_webhook', 'sub_abc123'
FROM player_roles WHERE role_name = 'patreon_hero';

-- Override max homes for VIP on survival servers
INSERT INTO player_config_overrides 
    (player_uuid, plugin_name, config_key, scope_type, scope_selector, 
     override_value, override_reason, granted_by)
VALUES 
    ('vip-uuid-5678', 'Essentials', 'max-homes', 'META_TAG', 'survival',
     '10', 'Patreon Hero tier perk', 'donor_system');

-- On SMP101 (survival tagged):
resolve_config_value('Essentials', 'max-homes', 'SMP101', player_uuid='vip-uuid-5678')
-- Returns: '10' (player override)

-- On CREA01 (creative tagged):
resolve_config_value('Essentials', 'max-homes', 'CREA01', player_uuid='vip-uuid-5678')
-- Returns: '5' (global default, no survival tag so override doesn't apply)
```

---

## Index Summary

**Total Indexes**: 54

**Purpose**:
- Foreign key lookups (instance_id, tag_id, world_id, region_id, player_uuid, role_id, group_id)
- Config rule resolution (plugin + key + priority)
- Tag filtering (category, active status)
- Group membership lookups (instance_groups, world_groups, region_groups)
- Variance detection (drift analysis)
- Player role lookups (role assignments, expiry tracking)
- Player override resolution (scoped permission overrides)
- Performance optimization (composite indexes for common queries)

**Key Composite Indexes**:
- `idx_config_rules_lookup`: Fast config resolution (plugin + key + active + priority)
- `idx_instance_group_members_instance`: Instance group membership
- `idx_world_group_members_world`: World group membership
- `idx_region_group_members_region`: Region group membership
- `idx_player_role_assign_scope`: Role assignment scope filtering
- `idx_player_overrides_player`: Player-specific override lookups
- `idx_player_role_assign_expires`: Automatic donor role expiry checks

---

## Size Estimates

**Assumptions**:
- 20 instances
- **10 instance groups** (physical, logical, administrative)
- 50 meta tags (system + custom)
- 100 worlds (5 per instance avg)
- **10 world groups** (resource-worlds, survival-worlds, etc.)
- 500 regions
- **10 region groups** (pvp-arenas, safe-zones, etc.)
- 10,000 config rules
- 500 variables
- 1,000 variance cache entries
- **30 player roles** (staff + donor tiers)
- **5,000 active players** (with rank tracking)
- **500 role assignments** (admins, mods, donors)
- **200 player-specific overrides** (VIP perks, admin bypasses)

**Estimated Database Size**: ~80-160 MB

**Query Performance** (with indexes):
- Config resolution: <5ms (indexed lookups)
- Player override check: <3ms (indexed player_uuid + scope)
- Tag logic evaluation: <1ms (in-memory)
- Variance detection: <10ms (cached results)
- Role assignment lookup: <2ms (indexed player + scope)
- Donor expiry check: <5ms (indexed expires_at)

---

## Priority Hierarchy Summary

**Final Resolution Order** (0 = highest priority):

```
0. PLAYER_OVERRIDE     - Specific player bypass/perk
   ↓
1. REGION              - Region-specific rules (spawn, pvp_arena, etc.)
   ↓
2. REGION_GROUP        - Region group rules (all pvp-arenas, all safe-zones)
   ↓
3. WORLD               - World-specific rules (main world vs resource world)
   ↓
4. WORLD_GROUP         - World group rules (all resource-worlds, all survival-worlds)
   ↓
5. INSTANCE            - Instance-specific rules (SMP101 custom settings)
   ↓
6. INSTANCE_GROUP      - Instance group rules (all creative-servers, hetzner-cluster)
   ↓
7. META_TAG            - Tag-based rules (survival vs creative)
   ↓
8. SERVER              - Physical server rules (Hetzner vs OVH)
   ↓
9. GLOBAL              - Network-wide baseline
```

**Example Resolution Path**:

Query: `resolve_config_value('WorldGuard', 'pvp-enabled', 'SMP101', 'world', 'spawn', 'admin-uuid')`

1. Check: Player override for admin-uuid in spawn region? → **YES: false** (admin testing, return immediately)
2. (Skip remaining checks, player override wins)

Query: `resolve_config_value('EliteMobs', 'spawn-rate', 'SMP101', 'resource_world', null, 'regular-player')`

1. Check: Player override? → No
2. Check: Region rule? → No (no region specified)
3. Check: World rule for resource_world? → **YES: 0.10** (higher spawn rate in resource world)
4. (Return world-specific value, don't check lower priorities)

Query: `resolve_config_value('Essentials', 'max-homes', 'SMP101', null, null, 'vip-uuid')`

1. Check: Player override for vip-uuid? → **YES: 10** (Patreon VIP perk)
2. (Return immediately, bypass all other rules)

Query: `resolve_config_value('CoreProtect', 'mysql-host', 'SMP101', null, null, null)`

1. Check: Player override? → No
2. Check: Region? → No
3. Check: World? → No
4. Check: Instance? → No
5. Check: Meta-tag (survival)? → No (not defined at tag level)
6. Check: Server (hetzner-xeon)? → **YES: '135.181.212.169'**
7. (Return server-level value)

---

## Size Estimates

**Assumptions**:
- 20 instances
- 50 meta tags
- 100 worlds (5 per instance avg)
- 500 regions
- 10,000 config rules
- 500 variables
- 1,000 variance cache entries

**Estimated Database Size**: ~50-100 MB

**Query Performance**:
- Config resolution: <5ms (indexed lookups)
- Tag logic evaluation: <1ms (in-memory)
- Variance detection: <10ms (cached results)

---

## Next Steps for Review

1. **Validate Scope Hierarchy**: REGION > WORLD > INSTANCE > META_TAG > SERVER > GLOBAL correct?
2. **Tag Logic Syntax**: JSON format `{"include": [], "exclude": []}` acceptable?
3. **World Naming**: Should world_name include instance prefix or be unique per instance?
4. **Region Priority**: Should regions have numeric priority or just parent/child relationships?
5. **Missing Fields**: Any additional metadata needed for your use cases?

**Once approved, I will**:
1. Generate SQL migration script
2. Create initial seed data (tags, variables, sample rules)
3. Build Python data access layer with resolution algorithm
4. Deploy to MariaDB on Hetzner
