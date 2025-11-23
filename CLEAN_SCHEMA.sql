-- ============================================================================
-- ARCHIVESMP CONFIGURATION MANAGER - AUTHORITATIVE SCHEMA
-- ============================================================================
-- Complete schema with all working features
-- Based on: scripts/create_database_schema.sql + active code requirements
-- ============================================================================

DROP DATABASE IF EXISTS asmp_config;
CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asmp_config;

-- ============================================================================
-- CORE: SERVERS & INSTANCES
-- ============================================================================

CREATE TABLE instances (
    instance_id VARCHAR(16) PRIMARY KEY COMMENT 'AMP instance name (e.g., SMP101, HUB01)',
    display_name VARCHAR(128) COMMENT 'Human-readable name',
    platform VARCHAR(16) NOT NULL COMMENT 'paper, velocity, fabric, etc',
    minecraft_version VARCHAR(16) COMMENT 'MC version (e.g., 1.21.1)',
    server_name VARCHAR(64) NOT NULL COMMENT 'Physical server (hetzner-xeon, ovh-ryzen)',
    instance_path TEXT COMMENT 'Full filesystem path to instance',
    
    -- Auto-tracking timestamps
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'First discovered',
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last scan that saw this instance',
    
    INDEX idx_server (server_name),
    INDEX idx_platform (platform),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB COMMENT='Minecraft server instances';

-- ============================================================================
-- CORE: PLUGINS & DATAPACKS REGISTRY
-- ============================================================================

CREATE TABLE plugins (
    plugin_id VARCHAR(64) PRIMARY KEY COMMENT 'Plugin identifier (lowercase, e.g., luckperms)',
    display_name VARCHAR(128) COMMENT 'Human-readable name',
    current_version VARCHAR(32) COMMENT 'Latest known version',
    
    -- Source tracking
    modrinth_id VARCHAR(64) COMMENT 'Modrinth project ID',
    github_repo VARCHAR(256) COMMENT 'GitHub repo (owner/name)',
    spigot_id INT COMMENT 'Spigot resource ID',
    
    -- Metadata
    is_paid BOOLEAN DEFAULT FALSE COMMENT 'Requires payment',
    
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_modrinth (modrinth_id),
    INDEX idx_github (github_repo)
) ENGINE=InnoDB COMMENT='Plugin registry';

CREATE TABLE datapacks (
    datapack_id VARCHAR(128) PRIMARY KEY COMMENT 'Datapack identifier',
    display_name VARCHAR(128),
    current_version VARCHAR(32),
    
    -- Source tracking
    modrinth_id VARCHAR(64),
    github_repo VARCHAR(256),
    
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_modrinth (modrinth_id)
) ENGINE=InnoDB COMMENT='Datapack registry';

-- ============================================================================
-- CORE: INSTALLATION TRACKING (JUNCTION TABLES)
-- ============================================================================

CREATE TABLE instance_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(64) NOT NULL,
    
    -- Installation details
    installed_version VARCHAR(32),
    file_name VARCHAR(256),
    file_path TEXT,
    file_hash VARCHAR(64) COMMENT 'SHA256 hash',
    file_size BIGINT,
    file_modified_at TIMESTAMP NULL COMMENT 'Filesystem mtime',
    is_enabled BOOLEAN DEFAULT TRUE,
    
    -- Auto-tracking
    first_discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_plugin (instance_id, plugin_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB COMMENT='Which plugins are installed where';

CREATE TABLE instance_datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    datapack_id VARCHAR(128) NOT NULL,
    world_name VARCHAR(64) NOT NULL,
    
    -- Installation details
    version VARCHAR(32),
    file_name VARCHAR(256),
    file_path TEXT,
    file_hash VARCHAR(64),
    file_size BIGINT,
    is_enabled BOOLEAN DEFAULT TRUE,
    
    -- Auto-tracking
    first_discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_datapack (instance_id, datapack_id, world_name),
    INDEX idx_datapack (datapack_id),
    INDEX idx_world (instance_id, world_name)
) ENGINE=InnoDB COMMENT='Which datapacks are installed where';

-- ============================================================================
-- CONFIGURATION: VALUES & BASELINES
-- ============================================================================

CREATE TABLE config_values (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_name VARCHAR(64) NOT NULL,
    config_file VARCHAR(256) NOT NULL,
    config_key VARCHAR(512) NOT NULL COMMENT 'Dot-notation path (e.g., database.host)',
    config_value TEXT COMMENT 'Current value (JSON if complex)',
    
    -- Auto-tracking
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Value changed',
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last scanned',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY unique_config (instance_id, plugin_name, config_file, config_key),
    INDEX idx_plugin (plugin_name),
    INDEX idx_file (config_file),
    INDEX idx_changed (last_changed_at)
) ENGINE=InnoDB COMMENT='Actual config values from instances';

CREATE TABLE config_baseline (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(64) NOT NULL,
    config_file VARCHAR(256) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    expected_value TEXT COMMENT 'Expected value (JSON if complex)',
    value_type VARCHAR(32) COMMENT 'string, integer, boolean, json',
    is_required BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_baseline (plugin_name, config_file, config_key),
    INDEX idx_plugin (plugin_name)
) ENGINE=InnoDB COMMENT='Expected config values (baselines)';

-- ============================================================================
-- CONFIGURATION: DRIFT DETECTION
-- ============================================================================

CREATE TABLE config_variance_detected (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_name VARCHAR(64) NOT NULL,
    config_file VARCHAR(256) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    
    -- Variance details
    actual_value TEXT COMMENT 'What we found',
    expected_value TEXT COMMENT 'What should be',
    variance_type VARCHAR(32) COMMENT 'missing, wrong_value, extra, type_mismatch',
    
    -- Auto-tracking (updates on every scan where variance still exists)
    first_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY unique_variance (instance_id, plugin_name, config_file, config_key),
    INDEX idx_unresolved (is_resolved, last_detected_at),
    INDEX idx_plugin (plugin_name)
) ENGINE=InnoDB COMMENT='Config drift/variance detected by scans';

-- ============================================================================
-- DEPLOYMENT: ACTUAL CHANGES MADE
-- ============================================================================

CREATE TABLE deployment_changes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_name VARCHAR(64),
    config_file VARCHAR(256),
    config_key VARCHAR(512),
    
    -- Change details
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(32) COMMENT 'manual_edit, drift_fix, baseline_update, deployment',
    
    -- Audit
    changed_by VARCHAR(64) COMMENT 'Username or agent name',
    change_reason TEXT,
    deployment_id VARCHAR(64) COMMENT 'Batch deployment ID',
    
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    INDEX idx_instance (instance_id),
    INDEX idx_deployment (deployment_id),
    INDEX idx_changed_at (changed_at)
) ENGINE=InnoDB COMMENT='Audit log of actual config changes deployed';

-- ============================================================================
-- METADATA: TAGS & GROUPING
-- ============================================================================

CREATE TABLE meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(128),
    description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_name (tag_name)
) ENGINE=InnoDB COMMENT='Tags for organizing instances/plugins';

CREATE TABLE instance_tags (
    instance_id VARCHAR(16) NOT NULL,
    tag_id INT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(64),
    
    PRIMARY KEY (instance_id, tag_id),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Tags applied to instances';

CREATE TABLE instance_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Instance groups for batch operations';

CREATE TABLE instance_group_members (
    group_id INT NOT NULL,
    instance_id VARCHAR(16) NOT NULL,
    
    PRIMARY KEY (group_id, instance_id),
    FOREIGN KEY (group_id) REFERENCES instance_groups(group_id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='Group membership';

-- ============================================================================
-- WORLDS (for multi-world instances)
-- ============================================================================

CREATE TABLE worlds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(64) NOT NULL,
    world_type VARCHAR(32) COMMENT 'normal, nether, end, custom',
    
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY unique_world (instance_id, world_name)
) ENGINE=InnoDB COMMENT='Worlds in multi-world instances';

-- ============================================================================
-- DONE - MINIMAL, CLEAN, TIMESTAMP-DRIVEN SCHEMA
-- ============================================================================
