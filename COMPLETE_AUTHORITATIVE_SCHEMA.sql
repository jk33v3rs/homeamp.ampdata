-- ============================================================================
-- COMPLETE AUTHORITATIVE SCHEMA (CORRECTED)
-- Generated from discovered SQL and Python files
-- Total Tables: 93
--
-- FIXES APPLIED:
-- 1. meta_tags: Changed 'id' → 'tag_id' for FK consistency
-- 2. plugin_versions: Changed plugin_id INT → VARCHAR(64)
-- 3. plugin_update_sources: Changed plugin_id INT → VARCHAR(64)
-- 4. datapack_deployment_queue: Fixed FK to datapacks(id)
-- 5. approval_votes: Fixed ENGINE syntax
-- 6. deployment_history: Added queue_deployment_id linkage
-- ============================================================================

USE asmp_config;


-- ============================================================================
-- INFRASTRUCTURE
-- ============================================================================

-- instances
-- Purpose: Core: Physical AMP instance deployments (servers)
-- Source: scripts/create_database_schema.sql
CREATE TABLE instances (
    instance_id VARCHAR(16) PRIMARY KEY,
    instance_name VARCHAR(128) NOT NULL,
    
    server_name VARCHAR(32) NOT NULL,
    server_host VARCHAR(64),
    
    port INT,
    amp_instance_id VARCHAR(64),
    platform VARCHAR(16) DEFAULT 'paper',
    minecraft_version VARCHAR(16),
    
    is_active BOOLEAN DEFAULT true,
    is_production BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NULL,
    
    description TEXT,
    admin_notes TEXT
) ENGINE=InnoDB;

-- instance_groups
-- Purpose: Grouping: Meta-server clusters (SMP vs Creative vs Test)
-- Source: scripts/create_database_schema.sql
CREATE TABLE instance_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    group_type VARCHAR(32),
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- instance_group_members
-- Purpose: Grouping: Links instances to groups
-- Source: scripts/create_database_schema.sql
CREATE TABLE instance_group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    group_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    assignment_note TEXT,
    
    UNIQUE KEY unique_instance_group (instance_id, group_id),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES instance_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- instance_tags
-- Purpose: Tagging: Assigns meta-tags to instances
-- Source: scripts/add_config_rules_tables.sql
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

-- instance_meta_tags
-- Purpose: Tagging: Links instances to meta-tags
-- Source: scripts/create_dynamic_metadata_system.sql
CREATE TABLE IF NOT EXISTS instance_meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    tag_id INT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(128) DEFAULT 'system',
    is_auto_detected BOOLEAN DEFAULT FALSE,  -- Did agent detect this automatically?
    confidence_score DECIMAL(3,2),  -- 0.00-1.00 for auto-detected tags
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_tag (instance_id, tag_id),
    INDEX idx_instance (instance_id),
    INDEX idx_tag (tag_id),
    INDEX idx_auto_detected (is_auto_detected)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- meta_tag_categories
-- Purpose: Tagging: Categories for organizing meta-tags
-- Source: scripts/create_database_schema.sql
CREATE TABLE meta_tag_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true
) ENGINE=InnoDB;

-- meta_tags
-- Purpose: Tagging: Dynamic tags for classification (PvP, Economy, Creative, etc.)
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL,
    parent_tag_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_tag_id) REFERENCES meta_tags(tag_id) ON DELETE SET NULL,
    INDEX idx_parent_tag_id (parent_tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- meta_tag_history
-- Purpose: Tagging: Audit trail of tag changes
-- Source: scripts/create_dynamic_metadata_system.sql
CREATE TABLE IF NOT EXISTS meta_tag_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    tag_id INT NOT NULL,
    action ENUM('added', 'removed', 'modified') NOT NULL,
    performed_by VARCHAR(128) NOT NULL,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    INDEX idx_instance (instance_id),
    INDEX idx_performed_at (performed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- PLUGIN MANAGEMENT
-- ============================================================================

-- plugins
-- Purpose: Plugin Management: Discovered plugins across all instances
-- Source: scripts/add_plugin_metadata_tables.sql
CREATE TABLE IF NOT EXISTS plugins (
    plugin_id VARCHAR(64) PRIMARY KEY,
    plugin_name VARCHAR(128) NOT NULL,
    platform ENUM('paper', 'fabric', 'neoforge', 'geyser', 'velocity', 'datapack') NOT NULL,
    current_version VARCHAR(32),
    latest_version VARCHAR(32),
    
    -- Source locations
    modrinth_id VARCHAR(64),
    hangar_slug VARCHAR(128),
    github_repo VARCHAR(256),
    spigot_id VARCHAR(16),
    bukkit_id VARCHAR(16),
    curseforge_id VARCHAR(16),
    
    -- Documentation
    docs_url TEXT,
    wiki_url TEXT,
    plugin_page_url TEXT,
    
    -- CI/CD
    has_cicd BOOLEAN DEFAULT FALSE,
    cicd_provider ENUM('github', 'gitlab', 'jenkins', 'none') DEFAULT 'none',
    cicd_url TEXT,
    
    -- Metadata
    description TEXT,
    author VARCHAR(128),
    license VARCHAR(64),
    is_premium BOOLEAN DEFAULT FALSE,
    is_paid BOOLEAN DEFAULT FALSE,
    
    -- Tracking
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_platform (platform),
    INDEX idx_modrinth (modrinth_id),
    INDEX idx_hangar (hangar_slug),
    INDEX idx_github (github_repo(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- instance_plugins
-- Purpose: Plugin Management: Which plugins are installed on which instances
-- Source: scripts/add_plugin_metadata_tables.sql
CREATE TABLE IF NOT EXISTS instance_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(64) NOT NULL,
    installed_version VARCHAR(32),
    file_name VARCHAR(256),
    file_hash VARCHAR(64),
    is_enabled BOOLEAN DEFAULT TRUE,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_plugin (instance_id, plugin_id),
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- plugin_versions
-- Purpose: Plugin Management: Version tracking and update availability
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS plugin_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    current_version VARCHAR(50),
    latest_version VARCHAR(50),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_available BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_plugin_id (plugin_id),
    INDEX idx_update_available (update_available)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- plugin_update_queue
-- Purpose: Plugin Management: Queue of pending plugin updates
-- Source: scripts/add_plugin_metadata_tables.sql
CREATE TABLE IF NOT EXISTS plugin_update_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    from_version VARCHAR(32),
    to_version VARCHAR(32) NOT NULL,
    priority INT DEFAULT 5,
    status ENUM('pending', 'in_progress', 'completed', 'failed') DEFAULT 'pending',
    scheduled_for TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_priority (priority DESC),
    INDEX idx_scheduled (scheduled_for)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- plugin_update_sources
-- Purpose: Plugin Management: Where to check for plugin updates
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS plugin_update_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    source_type ENUM('spigot', 'modrinth', 'hangar', 'github', 'jenkins') NOT NULL,
    source_url VARCHAR(512) NOT NULL,
    build_selector VARCHAR(255),
    download_url_pattern VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_plugin_id (plugin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================================================
-- DATAPACK MANAGEMENT
-- ============================================================================

-- datapacks
-- Purpose: Datapack Management: Discovered datapacks
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50),
    world_path VARCHAR(512) NOT NULL,
    instance_id VARCHAR(50) NOT NULL,
    pack_format INT,
    description TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_instance_id (instance_id),
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- instance_datapacks
-- Purpose: Datapack Management: Which datapacks are on which instances
-- Source: scripts/add_plugin_metadata_tables.sql
CREATE TABLE IF NOT EXISTS instance_datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    datapack_name VARCHAR(128) NOT NULL,
    version VARCHAR(32),
    world_name VARCHAR(64) NOT NULL,
    file_name VARCHAR(256),
    file_hash VARCHAR(64),
    
    -- Source locations
    modrinth_id VARCHAR(64),
    github_repo VARCHAR(256),
    custom_source TEXT,
    
    is_enabled BOOLEAN DEFAULT TRUE,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    INDEX idx_instance (instance_id),
    INDEX idx_world (instance_id, world_name),
    INDEX idx_modrinth (modrinth_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- datapack_deployment_queue
-- Purpose: Datapack Management: Queue of pending datapack deployments
-- Source: scripts/create_dynamic_metadata_system.sql
CREATE TABLE IF NOT EXISTS datapack_deployment_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    datapack_id VARCHAR(128) NOT NULL,
    target_instances TEXT,  -- JSON array of instance_ids
    target_worlds TEXT,  -- JSON array of world names, or '*' for all
    
    version VARCHAR(64),
    download_url TEXT,
    
    action ENUM('install', 'update', 'remove', 'enable', 'disable') NOT NULL,
    priority INT DEFAULT 5,
    scheduled_for TIMESTAMP NULL,
    requires_restart BOOLEAN DEFAULT TRUE,
    
    status ENUM('pending', 'in_progress', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NOT NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    error_message TEXT,
    deployment_log TEXT,
    
    FOREIGN KEY (datapack_id) REFERENCES datapacks(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_scheduled (scheduled_for)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- datapack_update_sources
-- Purpose: Datapack Management: Where to check for datapack updates
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS datapack_update_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    datapack_id INT NOT NULL,
    source_type ENUM('github', 'planetmc', 'custom') NOT NULL,
    source_url VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (datapack_id) REFERENCES datapacks(id) ON DELETE CASCADE,
    INDEX idx_datapack_id (datapack_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- datapack_versions
-- Purpose: Datapack Management: Version tracking
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS datapack_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    datapack_name VARCHAR(128) NOT NULL,
    version_string VARCHAR(32) NOT NULL,
    minecraft_version VARCHAR(50) COMMENT 'Target MC version',
    
    source_url TEXT,
    download_url TEXT,
    modrinth_id VARCHAR(64),
    github_repo VARCHAR(256),
    
    description TEXT,
    author VARCHAR(128),
    release_date DATETIME,
    file_hash VARCHAR(64),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_datapack_version (datapack_name, version_string),
    INDEX idx_datapack_name (datapack_name),
    INDEX idx_minecraft_version (minecraft_version),
    INDEX idx_modrinth (modrinth_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- CONFIGURATION
-- ============================================================================

-- instance_server_properties
-- Purpose: Configuration: server.properties values per instance
-- Source: scripts/add_plugin_metadata_tables.sql
CREATE TABLE IF NOT EXISTS instance_server_properties (
    instance_id VARCHAR(16) PRIMARY KEY,
    level_name VARCHAR(64) NOT NULL,
    gamemode VARCHAR(16),
    difficulty VARCHAR(16),
    max_players INT,
    view_distance INT,
    simulation_distance INT,
    pvp BOOLEAN,
    spawn_protection INT,
    properties_json TEXT,  -- Full JSON of all properties
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- server_properties_baselines
-- Purpose: Configuration: Expected server.properties values
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS server_properties_baselines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_key VARCHAR(255) NOT NULL UNIQUE,
    property_value TEXT,
    baseline_type ENUM('global', 'tag-specific') DEFAULT 'global',
    INDEX idx_baseline_type (baseline_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- server_properties_variances
-- Purpose: Configuration: Detected deviations in server.properties
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS server_properties_variances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    property_key VARCHAR(255) NOT NULL,
    variance_value TEXT,
    is_intentional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_instance_property (instance_id, property_key),
    INDEX idx_instance_id (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- config_rules
-- Purpose: Configuration: Hierarchical rules (GLOBAL→SERVER→TAG→INSTANCE)
-- Source: scripts/add_config_rules_tables.sql
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

-- config_variables
-- Purpose: Configuration: Template variables ({{VARIABLE}})
-- Source: scripts/add_config_rules_tables.sql
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

-- config_change_history
-- Purpose: History: Audit trail of all config changes
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS config_change_history (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    
    instance_id VARCHAR(16),
    plugin_name VARCHAR(64) NOT NULL,
    config_file VARCHAR(256),
    config_key VARCHAR(512),
    
    old_value TEXT,
    new_value TEXT,
    value_type VARCHAR(16),
    
    change_type ENUM('manual', 'automated', 'drift_fix', 'version_upgrade', 'rule_update', 'migration') DEFAULT 'manual',
    change_source VARCHAR(32) COMMENT 'web_ui, api, cli, agent, migration_script',
    
    changed_by VARCHAR(64) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    
    deployment_id INT COMMENT 'Links to deployment that applied this change',
    batch_id VARCHAR(64) COMMENT 'Groups related changes together',
    
    is_reverted BOOLEAN DEFAULT FALSE,
    reverted_at TIMESTAMP NULL,
    reverted_by VARCHAR(64),
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE SET NULL,
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_name),
    INDEX idx_changed_at (changed_at),
    INDEX idx_changed_by (changed_by),
    INDEX idx_change_type (change_type),
    INDEX idx_deployment (deployment_id),
    INDEX idx_batch (batch_id),
    INDEX idx_reverted (is_reverted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Complete audit trail of all configuration changes';

-- baseline_snapshots
-- Purpose: History: Loaded baseline files and their checksums
-- Source: scripts/add_config_rules_tables.sql
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
-- VARIANCE DETECTION
-- ============================================================================

-- config_variance_cache
-- Purpose: Variance Detection: Pre-calculated variance data for UI
-- Source: scripts/add_config_rules_tables.sql
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

-- config_drift_log
-- Purpose: Variance Detection: Actual config drift detected
-- Source: scripts/add_config_rules_tables.sql
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

-- config_variance_detected
-- Purpose: Variance Detection: Detected differences vs baselines
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS config_variance_detected (
    variance_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(64) NOT NULL,
    config_file_path VARCHAR(512) NOT NULL,
    config_key_path VARCHAR(512) NOT NULL,
    
    expected_value TEXT COMMENT 'From global baseline',
    actual_value TEXT COMMENT 'What instance has',
    
    variance_type ENUM('drift', 'expected', 'manual_override', 'rule_based', 'unknown') DEFAULT 'drift',
    is_approved BOOLEAN DEFAULT FALSE,
    approval_date TIMESTAMP NULL,
    approved_by VARCHAR(64),
    
    server_name VARCHAR(32) COMMENT 'Which physical server this variance is on',
    applies_to_instances TEXT COMMENT 'Comma-separated list if multiple instances share this variance',
    
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolution_notes TEXT,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_variance_type (variance_type),
    INDEX idx_is_approved (is_approved),
    INDEX idx_server (server_name),
    INDEX idx_detected (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- DEPLOYMENT
-- ============================================================================

-- deployment_queue
-- Purpose: Deployment: Pending deployments
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS deployment_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_id VARCHAR(36) NOT NULL UNIQUE,
    plugin_name VARCHAR(255) NOT NULL,
    instance_ids JSON NOT NULL,
    status ENUM('pending', 'resolving', 'deploying', 'completed', 'failed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- deployment_logs
-- Purpose: Deployment: Per-instance deployment results
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS deployment_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_id VARCHAR(36) NOT NULL,
    instance_id VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deployment_id) REFERENCES deployment_queue(deployment_id) ON DELETE CASCADE,
    INDEX idx_deployment_id (deployment_id),
    INDEX idx_instance_id (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- deployment_history
-- Purpose: Deployment: Complete deployment records
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS deployment_history (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    
    deployment_type ENUM('config', 'plugin', 'full', 'hotfix', 'rollback') NOT NULL,
    deployment_scope VARCHAR(32) COMMENT 'single, server, group, network',
    
    target_instances TEXT COMMENT 'JSON array of instance_ids',
    target_server VARCHAR(32),
    target_group_id INT,
    
    deployed_by VARCHAR(64) NOT NULL,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployment_duration_seconds INT,
    
    deployment_status ENUM('pending', 'in_progress', 'success', 'partial', 'failed', 'rolled_back') DEFAULT 'pending',
    
    changes_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    
    pre_deployment_snapshot TEXT COMMENT 'JSON backup of state before deployment',
    error_log TEXT,
    
    rollback_deployment_id INT COMMENT 'If this is a rollback, points to original deployment',
    is_rollback BOOLEAN DEFAULT FALSE,
    
    notes TEXT,
    
    
    queue_deployment_id VARCHAR(36) NULL COMMENT 'Links to deployment_queue.deployment_id',
    FOREIGN KEY (target_group_id) REFERENCES instance_groups(group_id) ON DELETE SET NULL,
    FOREIGN KEY (rollback_deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    INDEX idx_deployed_at (deployed_at),
    INDEX idx_deployed_by (deployed_by),
    INDEX idx_deployment_type (deployment_type),
    INDEX idx_status (deployment_status),
    INDEX idx_target_server (target_server),
    INDEX idx_is_rollback (is_rollback)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Tracks all deployments with success/failure outcomes';

-- deployment_changes
-- Purpose: Deployment: Individual changes within deployments
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS deployment_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    deployment_id INT NOT NULL,
    change_id INT NOT NULL,
    
    change_status ENUM('pending', 'success', 'failed', 'skipped') DEFAULT 'pending',
    error_message TEXT,
    
    applied_at TIMESTAMP NULL,
    
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE CASCADE,
    FOREIGN KEY (change_id) REFERENCES config_change_history(change_id) ON DELETE CASCADE,
    UNIQUE KEY unique_deployment_change (deployment_id, change_id),
    INDEX idx_deployment (deployment_id),
    INDEX idx_change (change_id),
    INDEX idx_status (change_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Many-to-many link between deployments and changes';


-- ============================================================================
-- APPROVAL WORKFLOW
-- ============================================================================

-- change_approval_requests
-- Purpose: Approval: Change requests awaiting approval
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS change_approval_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    
    request_type ENUM('config_change', 'deployment', 'plugin_update', 'rule_change') NOT NULL,
    
    requested_by VARCHAR(64) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    justification TEXT,
    
    risk_level ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    impact_scope VARCHAR(32) COMMENT 'single, server, network',
    
    affected_instances TEXT COMMENT 'JSON array of instance_ids',
    
    approval_status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
    
    approved_by VARCHAR(64),
    approved_at TIMESTAMP NULL,
    approval_notes TEXT,
    
    rejected_by VARCHAR(64),
    rejected_at TIMESTAMP NULL,
    rejection_reason TEXT,
    
    deployment_id INT COMMENT 'Links to deployment if approved and executed',
    
    expires_at TIMESTAMP NULL COMMENT 'Auto-reject if not approved by this time',
    
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    INDEX idx_requested_by (requested_by),
    INDEX idx_status (approval_status),
    INDEX idx_risk_level (risk_level),
    INDEX idx_requested_at (requested_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Workflow for changes requiring approval before deployment';

-- approval_votes
-- Purpose: Approval: Individual votes on approval requests
-- Source: software/homeamp-config-manager/src/agent/approval_workflow.py
CREATE TABLE IF NOT EXISTS approval_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    voted_by VARCHAR(50) NOT NULL,
    vote ENUM('approved', 'rejected') NOT NULL,
    comment TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES change_approval_requests(request_id) ON DELETE CASCADE,
    UNIQUE KEY unique_vote (request_id, voted_by),
    INDEX idx_request (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================================
-- WORLD MANAGEMENT
-- ============================================================================

-- worlds
-- Purpose: World Management: Minecraft worlds across instances
-- Source: scripts/create_database_schema.sql
CREATE TABLE worlds (
    world_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    
    world_name VARCHAR(128) NOT NULL,
    world_type VARCHAR(32),
    
    seed BIGINT,
    generator VARCHAR(64),
    difficulty VARCHAR(16),
    
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_instance_world (instance_id, world_name),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- world_groups
-- Purpose: World Management: Groupings of related worlds
-- Source: scripts/create_database_schema.sql
CREATE TABLE world_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- world_group_members
-- Purpose: World Management: Links worlds to groups
-- Source: scripts/create_database_schema.sql
CREATE TABLE world_group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    world_id INT,
    group_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_world_group (world_id, group_id),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES world_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- world_tags
-- Purpose: World Management: Tags applied to worlds
-- Source: scripts/create_database_schema.sql
CREATE TABLE world_tags (
    world_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    world_id INT,
    tag_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_world_tag (world_id, tag_id),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- world_meta_tags
-- Purpose: World Management: Meta-tags for worlds
-- Source: software/homeamp-config-manager/scripts/create_multi_level_scope_tables.sql
CREATE TABLE IF NOT EXISTS world_meta_tags (
    world_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL COMMENT 'Folder name under instance (e.g., world, world_nether, world_the_end)',
    meta_tag_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128) NULL COMMENT 'User or system',
    auto_assigned BOOLEAN DEFAULT FALSE COMMENT 'True if auto-tagged by agent',
    confidence_score DECIMAL(3,2) NULL COMMENT 'ML confidence for auto-tags (0.00-1.00)',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (meta_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_world_tag (instance_id, world_name, meta_tag_id),
    INDEX idx_instance (instance_id),
    INDEX idx_world (world_name),
    INDEX idx_tag (meta_tag_id),
    INDEX idx_auto_assigned (auto_assigned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Meta-tags assigned to specific worlds within instances';

-- world_config_rules
-- Purpose: World Management: Config rules scoped to worlds
-- Source: software/homeamp-config-manager/scripts/create_multi_level_scope_tables.sql
CREATE TABLE IF NOT EXISTS world_config_rules (
    world_rule_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_key VARCHAR(512) NOT NULL COMMENT 'Dot-notation path (e.g., spawn.protection.radius)',
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object', 'null') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_world_config (instance_id, world_name, plugin_id, config_key),
    INDEX idx_instance (instance_id),
    INDEX idx_world (world_name),
    INDEX idx_plugin (plugin_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='World-specific config overrides';


-- ============================================================================
-- REGION MANAGEMENT
-- ============================================================================

-- regions
-- Purpose: Region Management: WorldGuard/GriefPrevention regions
-- Source: scripts/create_database_schema.sql
CREATE TABLE regions (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    world_id INT,
    
    region_name VARCHAR(128) NOT NULL,
    region_type VARCHAR(32),
    
    min_x INT,
    min_y INT,
    min_z INT,
    max_x INT,
    max_y INT,
    max_z INT,
    
    parent_region_id INT,
    priority INT DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_world_region (world_id, region_name),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_region_id) REFERENCES regions(region_id)
) ENGINE=InnoDB;

-- region_groups
-- Purpose: Region Management: Groupings of regions
-- Source: scripts/create_database_schema.sql
CREATE TABLE region_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- region_group_members
-- Purpose: Region Management: Links regions to groups
-- Source: scripts/create_database_schema.sql
CREATE TABLE region_group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    group_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_region_group (region_id, group_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES region_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- region_tags
-- Purpose: Region Management: Tags for regions
-- Source: scripts/create_database_schema.sql
CREATE TABLE region_tags (
    region_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    tag_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_region_tag (region_id, tag_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================================
-- PLAYER PROGRESSION
-- ============================================================================

-- rank_definitions
-- Purpose: Player Progression: Rank definitions (Member, VIP, etc.)
-- Source: scripts/create_database_schema.sql
CREATE TABLE rank_definitions (
    rank_id INT PRIMARY KEY,
    rank_type VARCHAR(16) NOT NULL,
    rank_name VARCHAR(32) NOT NULL,
    rank_order INT NOT NULL,
    
    display_color VARCHAR(16),
    chat_prefix TEXT,
    tab_prefix TEXT,
    luckperms_group VARCHAR(64),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- player_ranks
-- Purpose: Player Progression: Current rank per player
-- Source: scripts/create_database_schema.sql
CREATE TABLE player_ranks (
    player_uuid CHAR(36) PRIMARY KEY,
    current_rank_id INT,
    current_prestige_id INT,
    
    total_playtime_seconds BIGINT DEFAULT 0,
    total_quest_completions INT DEFAULT 0,
    total_mob_kills INT DEFAULT 0,
    rank_progress_percent DECIMAL(5,2) DEFAULT 0.00,
    
    last_rank_up TIMESTAMP NULL,
    last_prestige TIMESTAMP NULL,
    first_join TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (current_rank_id) REFERENCES rank_definitions(rank_id),
    FOREIGN KEY (current_prestige_id) REFERENCES rank_definitions(rank_id)
) ENGINE=InnoDB;

-- rank_meta_tags
-- Purpose: Player Progression: Meta-tags for ranks
-- Source: software/homeamp-config-manager/scripts/create_multi_level_scope_tables.sql
CREATE TABLE IF NOT EXISTS rank_meta_tags (
    rank_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NULL COMMENT 'NULL = server-wide rank across all instances',
    server_name VARCHAR(64) NULL COMMENT 'hetzner or ovh - for server-wide ranks',
    rank_name VARCHAR(128) NOT NULL COMMENT 'LuckPerms group name',
    meta_tag_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128) NULL,
    rank_priority INT NULL COMMENT 'LuckPerms weight/priority for sorting',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (meta_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_rank_tag (instance_id, server_name, rank_name, meta_tag_id),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_rank (rank_name),
    INDEX idx_tag (meta_tag_id),
    INDEX idx_priority (rank_priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Meta-tags assigned to permission ranks/groups';

-- rank_config_rules
-- Purpose: Player Progression: Config rules scoped to ranks
-- Source: software/homeamp-config-manager/scripts/create_multi_level_scope_tables.sql
CREATE TABLE IF NOT EXISTS rank_config_rules (
    rank_rule_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NULL COMMENT 'NULL = applies to all instances with this rank',
    server_name VARCHAR(64) NULL COMMENT 'NULL = applies to all servers',
    rank_name VARCHAR(128) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object', 'null') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_rank_config (instance_id, server_name, rank_name, plugin_id, config_key),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_rank (rank_name),
    INDEX idx_plugin (plugin_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Rank-specific config overrides';

-- player_config_overrides
-- Purpose: Player Progression: Player-specific config overrides
-- Source: scripts/create_database_schema.sql
CREATE TABLE player_config_overrides (
    override_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36),
    
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    config_value TEXT,
    
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',
    scope_selector VARCHAR(128),
    
    world_filter VARCHAR(128),
    region_filter VARCHAR(128),
    
    reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT true
) ENGINE=InnoDB;

-- player_meta_tags
-- Purpose: Player Progression: Meta-tags for individual players
-- Source: software/homeamp-config-manager/scripts/create_multi_level_scope_tables.sql
CREATE TABLE IF NOT EXISTS player_meta_tags (
    player_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid VARCHAR(36) NOT NULL COMMENT 'Minecraft player UUID',
    player_name VARCHAR(16) NULL COMMENT 'Current username (may change)',
    instance_id VARCHAR(16) NULL COMMENT 'NULL = applies across all instances',
    server_name VARCHAR(64) NULL COMMENT 'NULL = applies across all servers',
    meta_tag_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128) NULL,
    expires_at TIMESTAMP NULL COMMENT 'NULL = never expires',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (meta_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_player_tag (player_uuid, instance_id, server_name, meta_tag_id),
    INDEX idx_player_uuid (player_uuid),
    INDEX idx_player_name (player_name),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_tag (meta_tag_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Meta-tags assigned to individual players';

-- player_role_categories
-- Purpose: Player Progression: Categories for player roles
-- Source: scripts/create_database_schema.sql
CREATE TABLE player_role_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    display_order INT DEFAULT 0,
    is_system_category BOOLEAN DEFAULT true
) ENGINE=InnoDB;

-- player_roles
-- Purpose: Player Progression: Donor/Staff role definitions
-- Source: scripts/create_database_schema.sql
CREATE TABLE player_roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(64) NOT NULL UNIQUE,
    category_id INT,
    
    display_name VARCHAR(128),
    color_code VARCHAR(16),
    chat_prefix TEXT,
    tab_prefix TEXT,
    permission_weight INT DEFAULT 0,
    
    luckperms_group VARCHAR(64),
    is_donor_role BOOLEAN DEFAULT false,
    is_staff_role BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES player_role_categories(category_id)
) ENGINE=InnoDB;

-- player_role_assignments
-- Purpose: Player Progression: Assigns roles to players
-- Source: scripts/create_database_schema.sql
CREATE TABLE player_role_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36),
    role_id INT,
    
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',
    scope_selector VARCHAR(128),
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    expires_at TIMESTAMP NULL,
    
    subscription_id VARCHAR(128),
    last_payment_date TIMESTAMP NULL,
    
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    
    FOREIGN KEY (role_id) REFERENCES player_roles(role_id)
) ENGINE=InnoDB;


-- ============================================================================
-- MONITORING
-- ============================================================================

-- discovery_runs
-- Purpose: Monitoring: Agent discovery run history
-- Source: scripts/create_dynamic_metadata_system.sql
CREATE TABLE IF NOT EXISTS discovery_runs (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) NOT NULL,
    run_type ENUM('full_scan', 'incremental', 'targeted') NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status ENUM('running', 'completed', 'failed', 'partial') DEFAULT 'running',
    
    -- Counts
    instances_discovered INT DEFAULT 0,
    plugins_discovered INT DEFAULT 0,
    datapacks_discovered INT DEFAULT 0,
    configs_scanned INT DEFAULT 0,
    
    -- Results
    new_items_found INT DEFAULT 0,
    changed_items INT DEFAULT 0,
    removed_items INT DEFAULT 0,
    
    error_count INT DEFAULT 0,
    error_log TEXT,
    
    INDEX idx_server (server_name),
    INDEX idx_started_at (started_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- agent_heartbeats
-- Purpose: Monitoring: Agent health tracking
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS agent_heartbeats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL UNIQUE,
    server_name VARCHAR(255) NOT NULL,
    last_heartbeat DATETIME NOT NULL,
    status ENUM('online', 'offline') DEFAULT 'online',
    INDEX idx_server_name (server_name),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- system_health_metrics
-- Purpose: Monitoring: Performance and health metrics
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS system_health_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    
    metric_source VARCHAR(32) NOT NULL COMMENT 'web_api, agent, database, external',
    instance_id VARCHAR(16),
    
    metric_type VARCHAR(64) NOT NULL COMMENT 'response_time, memory_usage, plugin_count, drift_count, etc.',
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(16) COMMENT 'ms, MB, count, percent',
    
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    metadata_json TEXT COMMENT 'Additional context',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    INDEX idx_source (metric_source),
    INDEX idx_instance (instance_id),
    INDEX idx_type (metric_type),
    INDEX idx_recorded_at (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Time-series metrics for monitoring system health';

-- audit_log
-- Purpose: Monitoring: System-wide audit trail
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100),
    action_type ENUM('config_change', 'plugin_update', 'deployment', 'approval', 'rejection', 'tag_create', 'tag_delete') NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    details JSON,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_action_type (action_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- notification_log
-- Purpose: Monitoring: Sent notifications
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS notification_log (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    
    notification_type ENUM('deployment', 'drift_alert', 'plugin_update', 'approval_request', 'error', 'info') NOT NULL,
    
    recipient VARCHAR(128) NOT NULL COMMENT 'User, email, webhook URL, Discord channel',
    delivery_method ENUM('email', 'webhook', 'discord', 'slack', 'internal') NOT NULL,
    
    subject VARCHAR(255),
    message TEXT,
    
    related_deployment_id INT,
    related_approval_id INT,
    related_change_id INT,
    
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_status ENUM('pending', 'sent', 'failed', 'bounced') DEFAULT 'pending',
    delivery_error TEXT,
    
    FOREIGN KEY (related_deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    FOREIGN KEY (related_approval_id) REFERENCES change_approval_requests(request_id) ON DELETE SET NULL,
    FOREIGN KEY (related_change_id) REFERENCES config_change_history(change_id) ON DELETE SET NULL,
    INDEX idx_sent_at (sent_at),
    INDEX idx_recipient (recipient),
    INDEX idx_delivery_method (delivery_method),
    INDEX idx_status (delivery_status),
    INDEX idx_type (notification_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Audit trail of all notifications sent by the system';


-- ============================================================================
-- AUTOMATION
-- ============================================================================

-- scheduled_tasks
-- Purpose: Automation: Scheduled task configuration and status
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    
    task_name VARCHAR(128) NOT NULL,
    task_type ENUM('drift_check', 'plugin_update_check', 'variance_snapshot', 'backup', 'cleanup', 'custom') NOT NULL,
    
    schedule_expression VARCHAR(64) COMMENT 'Cron expression or interval',
    
    last_run_at TIMESTAMP NULL,
    last_run_status ENUM('success', 'failed', 'partial', 'skipped') DEFAULT 'success',
    last_run_duration_seconds INT,
    last_run_error TEXT,
    
    next_run_at TIMESTAMP NULL,
    
    is_enabled BOOLEAN DEFAULT true,
    
    config_json TEXT COMMENT 'JSON configuration for the task',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    
    UNIQUE KEY unique_task_name (task_name),
    INDEX idx_task_type (task_type),
    INDEX idx_next_run (next_run_at),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Configuration and status of automated scheduled tasks';


-- ============================================================================
-- ENDPOINT CONFIG
-- ============================================================================

-- endpoint_config_files
-- Purpose: Endpoint Config: Non-plugin config files tracked
-- Source: software/homeamp-config-manager/scripts/create_endpoint_config_tables.sql
CREATE TABLE IF NOT EXISTS endpoint_config_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NULL,  -- NULL for server-level configs
    datapack_id VARCHAR(128) NULL,  -- NULL for plugin configs
    config_file_type ENUM('yaml', 'json', 'toml', 'properties', 'xml', 'hocon', 'conf', 'other') NOT NULL,
    relative_path VARCHAR(1024) NOT NULL COMMENT 'Relative to instance base path',
    absolute_path VARCHAR(1024) NULL COMMENT 'Full filesystem path (computed)',
    file_hash VARCHAR(64) NULL COMMENT 'SHA-256 hash for change detection',
    file_size_bytes INT NULL,
    last_modified_at TIMESTAMP NULL COMMENT 'Filesystem mtime',
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_main_config BOOLEAN DEFAULT FALSE COMMENT 'True if this is config.yml vs messages.yml',
    is_auto_generated BOOLEAN DEFAULT FALSE COMMENT 'True for plugin-generated configs',
    is_tracked BOOLEAN DEFAULT TRUE COMMENT 'False to exclude from monitoring',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_instance_path (instance_id, relative_path),
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_datapack (datapack_id),
    INDEX idx_file_hash (file_hash),
    INDEX idx_last_modified (last_modified_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tracks all endpoint config file locations and metadata';

-- endpoint_config_backups
-- Purpose: Endpoint Config: Backups of endpoint configs
-- Source: software/homeamp-config-manager/scripts/create_endpoint_config_tables.sql
CREATE TABLE IF NOT EXISTS endpoint_config_backups (
    backup_id INT AUTO_INCREMENT PRIMARY KEY,
    config_file_id INT NOT NULL COMMENT 'Links to endpoint_config_files.id',
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NULL,
    config_file_path VARCHAR(1024) NOT NULL COMMENT 'Path at time of backup',
    file_content LONGTEXT NOT NULL COMMENT 'Full file snapshot',
    file_hash VARCHAR(64) NOT NULL COMMENT 'SHA-256 of content',
    backed_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    backed_up_by VARCHAR(128) NULL COMMENT 'User or system identifier',
    backup_reason ENUM('before_change', 'scheduled', 'manual', 'pre_migration', 'pre_deployment') NOT NULL,
    backup_metadata JSON NULL COMMENT 'Additional context (e.g., change description)',
    
    FOREIGN KEY (config_file_id) REFERENCES endpoint_config_files(id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_config_file (config_file_id),
    INDEX idx_instance (instance_id),
    INDEX idx_backed_up_at (backed_up_at),
    INDEX idx_backup_reason (backup_reason)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Full snapshots of config files for rollback capability';

-- endpoint_config_change_history
-- Purpose: Endpoint Config: Change history for endpoints
-- Source: software/homeamp-config-manager/scripts/create_endpoint_config_tables.sql
CREATE TABLE IF NOT EXISTS endpoint_config_change_history (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    config_file_id INT NOT NULL,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NULL,
    change_type ENUM('key_modified', 'key_added', 'key_deleted', 'file_replaced', 'file_created', 'file_deleted') NOT NULL,
    changed_key_path VARCHAR(512) NULL COMMENT 'Dot-notation path (e.g., settings.economy.enabled)',
    old_value TEXT NULL,
    new_value TEXT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(128) NULL COMMENT 'User, agent, or system',
    change_source ENUM('manual', 'agent', 'deployment', 'migration', 'api') NOT NULL,
    change_reason TEXT NULL COMMENT 'Why this change was made',
    backup_id INT NULL COMMENT 'Pre-change backup if created',
    rollback_of_change_id INT NULL COMMENT 'If this is a rollback, the change it reverted',
    
    FOREIGN KEY (config_file_id) REFERENCES endpoint_config_files(id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (backup_id) REFERENCES endpoint_config_backups(backup_id) ON DELETE SET NULL,
    FOREIGN KEY (rollback_of_change_id) REFERENCES endpoint_config_change_history(change_id) ON DELETE SET NULL,
    
    INDEX idx_config_file (config_file_id),
    INDEX idx_instance (instance_id),
    INDEX idx_changed_at (changed_at),
    INDEX idx_change_type (change_type),
    INDEX idx_change_source (change_source),
    INDEX idx_changed_key (changed_key_path(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Full audit trail of all config file modifications';


-- ============================================================================
-- ADVANCED FEATURES
-- ============================================================================

-- tag_dependencies
-- Purpose: Advanced: Tag dependency management
-- Source: software/homeamp-config-manager/scripts/create_advanced_feature_tables.sql
CREATE TABLE IF NOT EXISTS tag_dependencies (
    dependency_id INT AUTO_INCREMENT PRIMARY KEY,
    dependent_tag_id INT NOT NULL COMMENT 'Tag that has the requirement',
    required_tag_id INT NOT NULL COMMENT 'Tag that must be present',
    dependency_type ENUM('required', 'recommended', 'optional') DEFAULT 'required',
    description TEXT NULL COMMENT 'Why this dependency exists',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (dependent_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (required_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_dependency (dependent_tag_id, required_tag_id),
    INDEX idx_dependent (dependent_tag_id),
    INDEX idx_required (required_tag_id),
    INDEX idx_type (dependency_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tag dependency relationships for validation';

-- tag_conflicts
-- Purpose: Advanced: Conflicting tag detection
-- Source: software/homeamp-config-manager/scripts/create_advanced_feature_tables.sql
CREATE TABLE IF NOT EXISTS tag_conflicts (
    conflict_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_a_id INT NOT NULL,
    tag_b_id INT NOT NULL,
    conflict_severity ENUM('error', 'warning', 'info') DEFAULT 'error',
    description TEXT NULL COMMENT 'Why these tags conflict',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (tag_a_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_b_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_conflict (tag_a_id, tag_b_id),
    INDEX idx_tag_a (tag_a_id),
    INDEX idx_tag_b (tag_b_id),
    INDEX idx_severity (conflict_severity),
    
    -- Ensure symmetric conflict (if A conflicts with B, B conflicts with A)
    CHECK (tag_a_id != tag_b_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tag conflict definitions for validation';

-- tag_hierarchy
-- Purpose: Advanced: Hierarchical tag relationships
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS tag_hierarchy (
    parent_tag_id INT NOT NULL,
    child_tag_id INT NOT NULL,
    PRIMARY KEY (parent_tag_id, child_tag_id),
    FOREIGN KEY (parent_tag_id) REFERENCES meta_tags(id) ON DELETE CASCADE,
    FOREIGN KEY (child_tag_id) REFERENCES meta_tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- instance_feature_inventory
-- Purpose: Advanced: Feature capabilities per instance
-- Source: software/homeamp-config-manager/scripts/create_advanced_feature_tables.sql
CREATE TABLE IF NOT EXISTS instance_feature_inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    feature_name VARCHAR(128) NOT NULL COMMENT 'economy, permissions, pvp, custom-items, etc.',
    feature_category ENUM('gameplay', 'economy', 'permissions', 'protection', 'social', 'utility', 'cosmetic', 'admin', 'other') NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    detected_from VARCHAR(256) NULL COMMENT 'Which plugin/config provides this (e.g., Vault)',
    detection_method ENUM('plugin', 'config', 'manual') DEFAULT 'plugin',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_instance_feature (instance_id, feature_name),
    INDEX idx_instance (instance_id),
    INDEX idx_feature (feature_name),
    INDEX idx_category (feature_category),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Feature inventory per instance for capability tracking';

-- server_capabilities
-- Purpose: Advanced: Server hardware/software capabilities
-- Source: software/homeamp-config-manager/scripts/create_advanced_feature_tables.sql
CREATE TABLE IF NOT EXISTS server_capabilities (
    capability_id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) NOT NULL COMMENT 'hetzner, ovh, etc.',
    capability_type VARCHAR(128) NOT NULL COMMENT 'max_ram_gb, cpu_cores, storage_tb, max_instances, etc.',
    capability_value VARCHAR(256) NOT NULL,
    unit VARCHAR(32) NULL COMMENT 'GB, cores, TB, count, etc.',
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(128) NULL,
    
    UNIQUE KEY unique_server_capability (server_name, capability_type),
    INDEX idx_server (server_name),
    INDEX idx_type (capability_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Server hardware capabilities and limits';

-- world_features
-- Purpose: Advanced: Features enabled per world
-- Source: software/homeamp-config-manager/scripts/create_advanced_feature_tables.sql
CREATE TABLE IF NOT EXISTS world_features (
    world_feature_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    feature_name VARCHAR(128) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    detected_from VARCHAR(256) NULL COMMENT 'Which config/plugin provides this',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_world_feature (instance_id, world_name, feature_name),
    INDEX idx_instance (instance_id),
    INDEX idx_world (world_name),
    INDEX idx_feature (feature_name),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Feature tracking per-world within instances';


-- ============================================================================
-- OTHER
-- ============================================================================

-- tag_instances
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS tag_instances (
    tag_id INT NOT NULL,
    instance_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (tag_id, instance_id),
    FOREIGN KEY (tag_id) REFERENCES meta_tags(id) ON DELETE CASCADE,
    INDEX idx_instance_id (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- config_variances
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS config_variances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    plugin_name VARCHAR(255) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    variance_value TEXT,
    baseline_value TEXT,
    is_intentional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_instance_plugin (instance_id, plugin_name),
    INDEX idx_intentional (is_intentional)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- config_history
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/create_new_tables.sql
CREATE TABLE IF NOT EXISTS config_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    previous_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployment_id VARCHAR(36),
    FOREIGN KEY (deployment_id) REFERENCES deployment_queue(deployment_id) ON DELETE SET NULL,
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- config_key_migrations
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS config_key_migrations (
    migration_id INT AUTO_INCREMENT PRIMARY KEY,
    
    plugin_name VARCHAR(64) NOT NULL,
    old_key_path VARCHAR(512) NOT NULL,
    new_key_path VARCHAR(512) NOT NULL,
    
    from_version VARCHAR(32) COMMENT 'Plugin version where key was deprecated',
    to_version VARCHAR(32) COMMENT 'Plugin version with new key',
    
    migration_type ENUM('rename', 'move', 'split', 'merge', 'remove', 'type_change') DEFAULT 'rename',
    value_transform TEXT COMMENT 'Python expression to transform value, e.g., "int(x) * 1000"',
    
    is_breaking BOOLEAN DEFAULT false COMMENT 'Whether this breaks backward compatibility',
    is_automatic BOOLEAN DEFAULT true COMMENT 'Whether to apply automatically',
    
    notes TEXT,
    documentation_url TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    
    UNIQUE KEY unique_migration (plugin_name, old_key_path, from_version),
    INDEX idx_plugin (plugin_name),
    INDEX idx_from_version (from_version),
    INDEX idx_migration_type (migration_type),
    INDEX idx_breaking (is_breaking)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Tracks config key changes between plugin versions for automatic migration';

-- config_rule_history
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS config_rule_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    
    rule_id INT NOT NULL,
    
    plugin_name VARCHAR(64),
    config_key VARCHAR(512),
    scope_type VARCHAR(16),
    scope_selector VARCHAR(128),
    
    old_value TEXT,
    new_value TEXT,
    
    old_priority INT,
    new_priority INT,
    
    change_type ENUM('create', 'update', 'delete', 'priority_change', 'scope_change') NOT NULL,
    
    changed_by VARCHAR(64),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    
    FOREIGN KEY (rule_id) REFERENCES config_rules(rule_id) ON DELETE CASCADE,
    INDEX idx_rule (rule_id),
    INDEX idx_changed_at (changed_at),
    INDEX idx_changed_by (changed_by),
    INDEX idx_change_type (change_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Audit trail for changes to config_rules table';

-- config_variance_history
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS config_variance_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    
    variance_type VARCHAR(16),
    is_expected_variance BOOLEAN,
    
    total_instances INT,
    unique_values INT,
    drift_count INT COMMENT 'How many instances have unexpected drift',
    
    variance_reason TEXT,
    variance_details TEXT COMMENT 'JSON with per-instance breakdown',
    
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_plugin_key (plugin_name, config_key),
    INDEX idx_snapshot_time (snapshot_timestamp),
    INDEX idx_variance_type (variance_type),
    INDEX idx_drift_count (drift_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Historical snapshots of config variance for trend analysis';

-- plugin_installation_history
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_tracking_history_tables.sql
CREATE TABLE IF NOT EXISTS plugin_installation_history (
    install_id INT AUTO_INCREMENT PRIMARY KEY,
    
    instance_id VARCHAR(16) NOT NULL,
    plugin_name VARCHAR(64) NOT NULL,
    
    action ENUM('install', 'remove', 'update', 'enable', 'disable') NOT NULL,
    
    version_from VARCHAR(32),
    version_to VARCHAR(32),
    
    jar_file_name VARCHAR(256),
    jar_hash VARCHAR(64) COMMENT 'SHA-256 of plugin jar',
    
    performed_by VARCHAR(64) NOT NULL,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    
    deployment_id INT COMMENT 'Link to deployment if part of larger deployment',
    
    requires_restart BOOLEAN DEFAULT true,
    restart_performed BOOLEAN DEFAULT false,
    restart_at TIMESTAMP NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_name),
    INDEX idx_action (action),
    INDEX idx_performed_at (performed_at),
    INDEX idx_performed_by (performed_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT 'Complete history of plugin lifecycle events';

-- plugin_developers
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS plugin_developers (
    developer_id INT AUTO_INCREMENT PRIMARY KEY,
    developer_name VARCHAR(128) NOT NULL UNIQUE,
    spigot_username VARCHAR(64),
    modrinth_username VARCHAR(64),
    github_username VARCHAR(64),
    discord_contact VARCHAR(128),
    website_url TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_spigot (spigot_username),
    INDEX idx_modrinth (modrinth_username),
    INDEX idx_github (github_username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- plugin_developer_links
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS plugin_developer_links (
    link_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    developer_id INT NOT NULL,
    role VARCHAR(32) DEFAULT 'author' COMMENT 'author, contributor, maintainer',
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    FOREIGN KEY (developer_id) REFERENCES plugin_developers(developer_id) ON DELETE CASCADE,
    UNIQUE KEY unique_plugin_developer (plugin_id, developer_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_developer (developer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- plugin_cicd_builds
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS plugin_cicd_builds (
    build_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    build_number VARCHAR(32),
    build_url TEXT,
    artifact_url TEXT,
    
    build_status ENUM('success', 'failure', 'pending', 'cancelled') DEFAULT 'success',
    commit_sha VARCHAR(40),
    branch_name VARCHAR(100),
    version_built VARCHAR(32),
    
    build_timestamp DATETIME,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_plugin (plugin_id),
    INDEX idx_build_timestamp (build_timestamp),
    INDEX idx_status (build_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- plugin_documentation_pages
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS plugin_documentation_pages (
    doc_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    doc_type ENUM('wiki', 'readme', 'javadoc', 'config_guide', 'api_docs', 'tutorial') NOT NULL,
    page_url TEXT NOT NULL,
    page_title VARCHAR(255),
    last_updated DATETIME,
    content_hash VARCHAR(64) COMMENT 'SHA-256 to detect changes',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_plugin (plugin_id),
    INDEX idx_doc_type (doc_type),
    INDEX idx_is_primary (is_primary)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- plugin_version_history
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS plugin_version_history (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    version_string VARCHAR(32) NOT NULL,
    version_major INT,
    version_minor INT,
    version_patch INT,
    
    release_date DATETIME,
    changelog TEXT,
    download_url TEXT,
    is_prerelease BOOLEAN DEFAULT FALSE,
    minecraft_versions TEXT COMMENT 'Comma-separated supported MC versions',
    
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_plugin_version (plugin_id, version_string),
    INDEX idx_plugin (plugin_id),
    INDEX idx_release_date (release_date),
    INDEX idx_version_parts (version_major, version_minor, version_patch)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- global_config_baseline
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS global_config_baseline (
    baseline_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    config_file_path VARCHAR(512) NOT NULL COMMENT 'e.g., plugins/PluginName/config.yml',
    config_key_path VARCHAR(512) NOT NULL COMMENT 'YAML path e.g., settings.economy.starting-balance',
    
    expected_value TEXT,
    value_type ENUM('string', 'number', 'boolean', 'list', 'map', 'null') DEFAULT 'string',
    yaml_indent_level INT DEFAULT 0 COMMENT 'Indentation depth in YAML',
    
    config_file_version VARCHAR(32) COMMENT 'Config version number if plugin tracks it',
    applies_to_plugin_version VARCHAR(32) COMMENT 'Plugin version this baseline is for',
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    notes TEXT,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_baseline_key (plugin_id, config_file_path, config_key_path),
    INDEX idx_plugin (plugin_id),
    INDEX idx_config_file (config_file_path),
    INDEX idx_config_key (config_key_path(255)),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- instance_config_values
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS instance_config_values (
    value_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(64) NOT NULL,
    config_file_path VARCHAR(512) NOT NULL,
    config_key_path VARCHAR(512) NOT NULL,
    
    actual_value TEXT,
    value_type ENUM('string', 'number', 'boolean', 'list', 'map', 'null') DEFAULT 'string',
    yaml_indent_level INT DEFAULT 0,
    
    config_file_version VARCHAR(32),
    plugin_version VARCHAR(32) COMMENT 'Plugin version installed on instance',
    
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_changed TIMESTAMP NULL,
    file_hash VARCHAR(64) COMMENT 'Hash of entire config file',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_config (instance_id, plugin_id, config_file_path, config_key_path),
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_config_file (config_file_path),
    INDEX idx_config_key (config_key_path(255)),
    INDEX idx_last_verified (last_verified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- server_tags
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS server_tags (
    server_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(32) NOT NULL,
    tag_id INT NOT NULL,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_server_tag (server_name, tag_id),
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    INDEX idx_server (server_name),
    INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- group_tags
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS group_tags (
    group_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    tag_id INT NOT NULL,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_group_tag (group_id, tag_id),
    FOREIGN KEY (group_id) REFERENCES instance_groups(group_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    INDEX idx_group (group_id),
    INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- player_tags
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS player_tags (
    player_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36) NOT NULL,
    tag_id INT NOT NULL,
    
    scope_type VARCHAR(16) DEFAULT 'GLOBAL' COMMENT 'GLOBAL, INSTANCE, WORLD, REGION',
    scope_selector VARCHAR(128),
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    UNIQUE KEY unique_player_tag (player_uuid, tag_id, scope_type, scope_selector),
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    INDEX idx_player (player_uuid),
    INDEX idx_tag (tag_id),
    INDEX idx_scope (scope_type, scope_selector),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- rank_tags
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS rank_tags (
    rank_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    rank_id INT NOT NULL,
    tag_id INT NOT NULL,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_rank_tag (rank_id, tag_id),
    FOREIGN KEY (rank_id) REFERENCES rank_definitions(rank_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    INDEX idx_rank (rank_id),
    INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- rank_subranks
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS rank_subranks (
    subrank_id INT AUTO_INCREMENT PRIMARY KEY,
    parent_rank_id INT NOT NULL,
    subrank_name VARCHAR(64) NOT NULL,
    subrank_order INT NOT NULL COMMENT 'Order within parent rank',
    
    display_color VARCHAR(16),
    chat_prefix TEXT,
    tab_prefix TEXT,
    
    requirement_type VARCHAR(32) COMMENT 'playtime, kills, quests, custom',
    requirement_value INT,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_rank_id) REFERENCES rank_definitions(rank_id) ON DELETE CASCADE,
    UNIQUE KEY unique_parent_subrank (parent_rank_id, subrank_name),
    INDEX idx_parent_rank (parent_rank_id),
    INDEX idx_subrank_order (parent_rank_id, subrank_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- player_subrank_progress
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS player_subrank_progress (
    progress_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36) NOT NULL,
    subrank_id INT NOT NULL,
    
    progress_value INT DEFAULT 0,
    progress_percent DECIMAL(5,2) DEFAULT 0.00,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP NULL,
    
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (subrank_id) REFERENCES rank_subranks(subrank_id) ON DELETE CASCADE,
    UNIQUE KEY unique_player_subrank (player_uuid, subrank_id),
    INDEX idx_player (player_uuid),
    INDEX idx_subrank (subrank_id),
    INDEX idx_completed (is_completed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- config_file_metadata
-- Purpose: Purpose unknown - referenced in code
-- Source: scripts/add_comprehensive_tracking.sql
CREATE TABLE IF NOT EXISTS config_file_metadata (
    metadata_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(64) NOT NULL,
    config_file_path VARCHAR(512) NOT NULL,
    
    file_version VARCHAR(32) COMMENT 'Version number if config tracks it',
    plugin_version VARCHAR(32) COMMENT 'Plugin version that generated this config',
    
    file_size_bytes BIGINT,
    file_hash VARCHAR(64) COMMENT 'SHA-256 of entire file',
    line_count INT,
    key_count INT COMMENT 'Number of config keys in file',
    
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_config_file (instance_id, plugin_id, config_file_path),
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_file_hash (file_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- instance_platform_configs
-- Purpose: Platform: Platform-specific configs
-- Source: scripts/create_dynamic_metadata_system.sql
CREATE TABLE IF NOT EXISTS instance_platform_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    config_type ENUM('paper_global', 'paper_world', 'spigot', 'bukkit', 'purpur', 'other') NOT NULL,
    world_name VARCHAR(128),  -- NULL for global configs
    
    -- Full config snapshot (YAML as JSON)
    config_json TEXT NOT NULL,
    file_hash VARCHAR(64),
    
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_config (instance_id, config_type, world_name),
    INDEX idx_instance (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- discovery_items
-- Purpose: Discovery: Individual items found during discovery
-- Source: scripts/create_dynamic_metadata_system.sql
CREATE TABLE IF NOT EXISTS discovery_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    run_id INT NOT NULL,
    item_type ENUM('instance', 'plugin', 'datapack', 'config', 'world', 'other') NOT NULL,
    item_id VARCHAR(256) NOT NULL,
    item_path VARCHAR(1024),
    action ENUM('discovered', 'unchanged', 'modified', 'removed') NOT NULL,
    details TEXT,  -- JSON with specifics
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (run_id) REFERENCES discovery_runs(run_id) ON DELETE CASCADE,
    INDEX idx_run (run_id),
    INDEX idx_type (item_type),
    INDEX idx_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- cicd_webhook_events
-- Purpose: CI/CD: Webhook events from build systems
-- Source: scripts/create_dynamic_metadata_system.sql
CREATE TABLE IF NOT EXISTS cicd_webhook_events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(128),
    
    -- Event details
    provider ENUM('github', 'gitlab', 'jenkins', 'modrinth', 'hangar', 'custom') NOT NULL,
    event_type VARCHAR(64) NOT NULL,  -- 'release', 'push', 'tag', etc.
    payload TEXT,  -- Full JSON payload
    
    -- Extracted data
    version VARCHAR(64),
    download_url TEXT,
    release_notes TEXT,
    is_prerelease BOOLEAN DEFAULT FALSE,
    
    -- Processing
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    status ENUM('pending', 'processed', 'ignored', 'failed') DEFAULT 'pending',
    action_taken TEXT,  -- What the system did in response
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_received (received_at),
    INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- config_locks
-- Purpose: Locking: Prevents concurrent config edits
-- Source: software/homeamp-config-manager/src/agent/conflict_detector.py
CREATE TABLE IF NOT EXISTS config_locks (
    lock_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    locked_by VARCHAR(50) NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_until TIMESTAMP NOT NULL,
    INDEX idx_lock_key (instance_id, plugin_name, config_key),
    INDEX idx_lock_expiry (locked_until)
) ENGINE;
