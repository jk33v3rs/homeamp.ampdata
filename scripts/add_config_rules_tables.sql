-- ============================================================================
-- Configuration Rules and Variance Tracking Schema Addition
-- Adds hierarchical config rules system with drift detection
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- CONFIGURATION RULES SYSTEM
-- ============================================================================

-- Config rules with priority hierarchy (GLOBAL → SERVER → META_TAG → INSTANCE)
-- Handles PLUGINS, STANDARD CONFIGS (server.properties, bukkit.yml), and DATAPACKS
CREATE TABLE IF NOT EXISTS config_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- What type of config is this?
    config_type VARCHAR(16) NOT NULL DEFAULT 'plugin',  -- plugin, standard, datapack
    
    -- What config is this rule for?
    plugin_name VARCHAR(128),          -- For plugin configs (EliteMobs, HuskSync) or NULL for standard
    config_file VARCHAR(255) NOT NULL, -- config.yml, server.properties, bukkit.yml, etc.
    config_key VARCHAR(512) NOT NULL,  -- Key path (can be dot notation)
    
    -- For datapacks (only used when config_type='datapack')
    datapack_name VARCHAR(128),        -- Name of required datapack
    world_name VARCHAR(64),            -- Which world (or NULL for all worlds)
    
    -- Scope definition (what instances does this apply to?)
    scope_type VARCHAR(16) NOT NULL,  -- GLOBAL, SERVER, META_TAG, INSTANCE
    scope_selector VARCHAR(128),       -- NULL for GLOBAL, 'Hetzner' for SERVER, 'creative' for META_TAG, 'SMP101' for INSTANCE
    
    -- Value
    config_value TEXT,
    value_type VARCHAR(16) DEFAULT 'string',  -- string, int, float, boolean, json, list, required, optional
    
    -- Priority (auto-calculated: 1=INSTANCE, 2=META_TAG, 3=SERVER, 4=GLOBAL)
    priority INT NOT NULL DEFAULT 4,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(128),
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    
    -- Indexes
    INDEX idx_rules_type (config_type),
    INDEX idx_rules_plugin (plugin_name),
    INDEX idx_rules_file (config_file),
    INDEX idx_rules_scope (scope_type, scope_selector),
    INDEX idx_rules_priority (priority),
    INDEX idx_rules_lookup (config_type, config_file, config_key),
    INDEX idx_rules_datapack (datapack_name, world_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instance tag assignments (for meta-tag based rules)
CREATE TABLE IF NOT EXISTS instance_tags (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    tag_id INT NOT NULL,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128),
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_instance_tag (instance_id, tag_id),
    INDEX idx_instance_tags_instance (instance_id),
    INDEX idx_instance_tags_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Config variables (for {{VARIABLE}} substitution)
CREATE TABLE IF NOT EXISTS config_variables (
    variable_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Scope (where is this variable defined?)
    scope_type VARCHAR(16) NOT NULL,  -- GLOBAL, SERVER, INSTANCE
    scope_identifier VARCHAR(128),     -- NULL for GLOBAL, server name or instance ID
    
    -- Variable
    variable_name VARCHAR(128) NOT NULL,
    variable_value TEXT,
    value_type VARCHAR(16) DEFAULT 'string',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    description TEXT,
    
    UNIQUE KEY unique_var_scope (scope_type, scope_identifier, variable_name),
    INDEX idx_variables_name (variable_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DRIFT DETECTION & VARIANCE TRACKING
-- ============================================================================

-- Variance cache (pre-calculated for UI performance)
-- Tracks variance for PLUGINS, STANDARD CONFIGS, and DATAPACKS
CREATE TABLE IF NOT EXISTS config_variance_cache (
    cache_id INT AUTO_INCREMENT PRIMARY KEY,
    
    config_type VARCHAR(16) NOT NULL DEFAULT 'plugin',  -- plugin, standard, datapack
    plugin_name VARCHAR(128),          -- For plugins, NULL for standard configs
    config_file VARCHAR(255) NOT NULL, -- config.yml, server.properties, etc.
    config_key VARCHAR(512) NOT NULL,  -- Key path
    
    -- For datapacks
    datapack_name VARCHAR(128),
    world_name VARCHAR(64),
    
    -- Variance classification
    variance_classification VARCHAR(16),  -- NONE, VARIABLE, META_TAG, INSTANCE, DRIFT
    instance_count INT DEFAULT 0,         -- How many instances have this config
    unique_value_count INT DEFAULT 0,     -- How many different values exist
    
    -- Expected vs unexpected variance
    is_expected_variance BOOLEAN DEFAULT true,  -- Green vs Red flag
    
    -- Sample values (for quick display)
    most_common_value TEXT,
    sample_values JSON,                   -- Array of {value, count, instances[]}
    
    -- Last updated
    last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_version INT DEFAULT 1,
    
    UNIQUE KEY unique_config_key (config_type, COALESCE(plugin_name, ''), config_file, config_key, COALESCE(datapack_name, ''), COALESCE(world_name, '')),
    INDEX idx_variance_type (config_type),
    INDEX idx_variance_classification (variance_classification),
    INDEX idx_variance_drift (is_expected_variance)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Detected drift entries (actual differences found)
-- Handles PLUGINS, STANDARD CONFIGS, and DATAPACKS
CREATE TABLE IF NOT EXISTS config_drift_log (
    drift_id INT AUTO_INCREMENT PRIMARY KEY,
    
    instance_id VARCHAR(16) NOT NULL,
    config_type VARCHAR(16) NOT NULL DEFAULT 'plugin',  -- plugin, standard, datapack
    plugin_name VARCHAR(128),          -- For plugins, NULL for standard
    config_file VARCHAR(255),
    config_key VARCHAR(512),
    
    -- For datapacks
    datapack_name VARCHAR(128),
    world_name VARCHAR(64),
    
    -- Values
    baseline_value TEXT,          -- Expected value from rule/baseline
    actual_value TEXT,            -- Actual value found
    
    -- Classification
    drift_type VARCHAR(16),       -- missing, different, extra, variable
    severity VARCHAR(16),         -- info, warning, error
    
    -- Resolution
    status VARCHAR(16) DEFAULT 'pending',  -- pending, reviewed, fixed, ignored
    reviewed_by VARCHAR(128),
    reviewed_at TIMESTAMP NULL,
    resolution_notes TEXT,
    
    -- Detection
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_id VARCHAR(64),
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_drift_instance (instance_id),
    INDEX idx_drift_type (config_type),
    INDEX idx_drift_plugin (plugin_name),
    INDEX idx_drift_status (status),
    INDEX idx_drift_severity (severity),
    INDEX idx_drift_detected (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- BASELINE TRACKING (for audit trail)
-- ============================================================================

-- Track which baselines have been loaded
CREATE TABLE IF NOT EXISTS baseline_snapshots (
    snapshot_id INT AUTO_INCREMENT PRIMARY KEY,
    
    plugin_name VARCHAR(128) NOT NULL,
    baseline_source VARCHAR(255),  -- File path or source identifier
    
    config_count INT DEFAULT 0,
    config_data JSON,              -- Full baseline config as JSON
    
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    loaded_by VARCHAR(128),
    checksum VARCHAR(64),          -- MD5/SHA hash of baseline file
    
    INDEX idx_baseline_plugin (plugin_name),
    INDEX idx_baseline_loaded (loaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- INITIAL DATA SEEDING
-- ============================================================================

-- Seed standard meta tag categories
INSERT IGNORE INTO meta_tag_categories (category_name, description, display_order) VALUES
    ('server', 'Physical server location', 1),
    ('gameplay', 'Game mode type', 2),
    ('modding', 'Modding/plugin level', 3),
    ('intensity', 'Difficulty/competitiveness', 4),
    ('economy', 'Economic system', 5),
    ('combat', 'Combat/PvP settings', 6),
    ('persistence', 'World reset behavior', 7),
    ('custom', 'Custom/special tags', 99);

-- Seed standard meta tags
INSERT IGNORE INTO meta_tags (tag_name, category_id, display_name, color_code, is_system_tag) VALUES
    -- Server tags
    ('hetzner', (SELECT category_id FROM meta_tag_categories WHERE category_name='server'), 'Hetzner Xeon', '#ff6b6b', true),
    ('ovh', (SELECT category_id FROM meta_tag_categories WHERE category_name='server'), 'OVH Ryzen', '#4ecdc4', true),
    
    -- Gameplay tags
    ('survival', (SELECT category_id FROM meta_tag_categories WHERE category_name='gameplay'), 'Survival', '#2ecc71', true),
    ('creative', (SELECT category_id FROM meta_tag_categories WHERE category_name='gameplay'), 'Creative', '#3498db', true),
    ('minigame', (SELECT category_id FROM meta_tag_categories WHERE category_name='gameplay'), 'Minigame', '#9b59b6', true),
    ('utility', (SELECT category_id FROM meta_tag_categories WHERE category_name='gameplay'), 'Utility/Hub', '#95a5a6', true),
    ('experimental', (SELECT category_id FROM meta_tag_categories WHERE category_name='gameplay'), 'Experimental/Dev', '#e67e22', true),
    
    -- Modding level tags
    ('vanilla', (SELECT category_id FROM meta_tag_categories WHERE category_name='modding'), 'Vanilla-ish', '#ffffff', false),
    ('paper', (SELECT category_id FROM meta_tag_categories WHERE category_name='modding'), 'Paper Plugins', '#00aa00', true),
    ('fabric', (SELECT category_id FROM meta_tag_categories WHERE category_name='modding'), 'Fabric Mods', '#aa5500', false),
    
    -- Economy tags
    ('economy-enabled', (SELECT category_id FROM meta_tag_categories WHERE category_name='economy'), 'Economy Enabled', '#f1c40f', false),
    ('economy-disabled', (SELECT category_id FROM meta_tag_categories WHERE category_name='economy'), 'No Economy', '#7f8c8d', false),
    
    -- Combat tags
    ('pvp-enabled', (SELECT category_id FROM meta_tag_categories WHERE category_name='combat'), 'PvP Enabled', '#e74c3c', false),
    ('pve-focused', (SELECT category_id FROM meta_tag_categories WHERE category_name='combat'), 'PvE/EliteMobs', '#27ae60', false),
    
    -- Persistence tags
    ('persistent', (SELECT category_id FROM meta_tag_categories WHERE category_name='persistence'), 'Never Resets', '#1abc9c', false),
    ('resetting', (SELECT category_id FROM meta_tag_categories WHERE category_name='persistence'), 'Periodic Resets', '#e67e22', false);

-- Seed default variables for all instances (will be populated by agent)
-- Common variables: SHORTNAME, SERVER_PORT, DATABASE_NAME, WORLD_NAME, CLUSTER_ID

-- ============================================================================
-- SAMPLE RULES - Examples of all three config types
-- ============================================================================

-- PLUGIN CONFIG RULES
INSERT IGNORE INTO config_rules (config_type, plugin_name, config_file, config_key, scope_type, scope_selector, config_value, value_type, priority, created_by, notes) VALUES
    -- Plugin: Global defaults
    ('plugin', 'EliteMobs', 'config.yml', 'language', 'GLOBAL', NULL, 'english', 'string', 4, 'system', 'Universal language setting'),
    ('plugin', 'EliteMobs', 'config.yml', 'setupDoneV4', 'GLOBAL', NULL, 'true', 'boolean', 4, 'system', 'Setup completion flag'),
    
    -- Plugin: Server-specific (database hosts differ by physical server)
    ('plugin', 'HuskSync', 'config.yml', 'database.host', 'SERVER', 'Hetzner', '135.181.212.169', 'string', 3, 'system', 'Hetzner DB host'),
    ('plugin', 'HuskSync', 'config.yml', 'database.host', 'SERVER', 'OVH', '37.187.143.41', 'string', 3, 'system', 'OVH DB host'),
    
    -- Plugin: Meta-tag rules (economy disabled in creative)
    ('plugin', 'Vault', 'config.yml', 'economy.enabled', 'META_TAG', 'creative', 'false', 'boolean', 2, 'system', 'No economy in creative worlds'),
    ('plugin', 'EssentialsX', 'config.yml', 'economy-enabled', 'META_TAG', 'economy-disabled', 'false', 'boolean', 2, 'system', 'Economy disabled tag');

-- STANDARD CONFIG RULES (server.properties, bukkit.yml, spigot.yml, paper-global.yml)
INSERT IGNORE INTO config_rules (config_type, plugin_name, config_file, config_key, scope_type, scope_selector, config_value, value_type, priority, created_by, notes) VALUES
    -- server.properties: Global defaults
    ('standard', NULL, 'server.properties', 'max-players', 'GLOBAL', NULL, '100', 'int', 4, 'system', 'Default max players'),
    ('standard', NULL, 'server.properties', 'difficulty', 'GLOBAL', NULL, 'hard', 'string', 4, 'system', 'Default difficulty'),
    ('standard', NULL, 'server.properties', 'pvp', 'GLOBAL', NULL, 'false', 'boolean', 4, 'system', 'PvP disabled by default'),
    
    -- server.properties: Meta-tag overrides
    ('standard', NULL, 'server.properties', 'gamemode', 'META_TAG', 'creative', 'creative', 'string', 2, 'system', 'Creative worlds force creative mode'),
    ('standard', NULL, 'server.properties', 'gamemode', 'META_TAG', 'survival', 'survival', 'string', 2, 'system', 'Survival worlds force survival mode'),
    ('standard', NULL, 'server.properties', 'pvp', 'META_TAG', 'pvp-enabled', 'true', 'boolean', 2, 'system', 'Enable PvP for tagged instances'),
    ('standard', NULL, 'server.properties', 'difficulty', 'META_TAG', 'creative', 'peaceful', 'string', 2, 'system', 'Creative worlds are peaceful'),
    
    -- bukkit.yml: Global and meta-tag
    ('standard', NULL, 'bukkit.yml', 'spawn-protection', 'GLOBAL', NULL, '16', 'int', 4, 'system', 'Default spawn protection'),
    ('standard', NULL, 'bukkit.yml', 'spawn-protection', 'META_TAG', 'creative', '0', 'int', 2, 'system', 'No spawn protection in creative'),
    
    -- spigot.yml: Global settings
    ('standard', NULL, 'spigot.yml', 'world-settings.default.view-distance', 'GLOBAL', NULL, '10', 'int', 4, 'system', 'Default view distance'),
    ('standard', NULL, 'spigot.yml', 'world-settings.default.mob-spawn-range', 'GLOBAL', NULL, '8', 'int', 4, 'system', 'Default mob spawn range'),
    
    -- paper-global.yml: Performance settings
    ('standard', NULL, 'config/paper-global.yml', 'chunk-loading.async-chunks', 'GLOBAL', NULL, 'true', 'boolean', 4, 'system', 'Enable async chunk loading'),
    ('standard', NULL, 'config/paper-global.yml', 'timings.enabled', 'GLOBAL', NULL, 'true', 'boolean', 4, 'system', 'Enable timings'),
    
    -- Instance-specific overrides
    ('standard', NULL, 'server.properties', 'spawn-protection', 'INSTANCE', 'SMP101', '32', 'int', 1, 'admin', 'SMP101 has larger spawn protection');

-- DATAPACK RULES (required/optional datapacks per world/instance)
INSERT IGNORE INTO config_rules (config_type, datapack_name, world_name, scope_type, scope_selector, config_value, value_type, priority, created_by, notes) VALUES
    -- Global: Required datapacks for all survival worlds
    ('datapack', 'VanillaTweaks-AFK', 'world', 'META_TAG', 'survival', 'required', 'required', 2, 'system', 'AFK display for survival worlds'),
    ('datapack', 'VanillaTweaks-PlayerHeadDrops', 'world', 'META_TAG', 'survival', 'required', 'required', 2, 'system', 'Player head drops for survival'),
    
    -- Creative-specific datapacks
    ('datapack', 'WorldEdit', NULL, 'META_TAG', 'creative', 'required', 'required', 2, 'system', 'WorldEdit datapack for creative'),
    
    -- Instance-specific datapack requirements
    ('datapack', 'CustomDungeon-TowerDefense', 'TOWER_WORLD', 'INSTANCE', 'TOWER01', 'required', 'required', 1, 'admin', 'Tower Defense custom datapack'),
    ('datapack', 'Terralith', 'world', 'INSTANCE', 'SMP101', 'required', 'required', 1, 'admin', 'Terralith terrain gen for SMP101'),
    
    -- Optional datapacks
    ('datapack', 'VanillaTweaks-ArmorStandEditor', NULL, 'GLOBAL', NULL, 'optional', 'optional', 4, 'system', 'Optional armor stand editor');

COMMIT;
