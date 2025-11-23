-- ============================================================================
-- ARCHIVESMP CONFIGURATION MANAGER - AUTHORITATIVE SCHEMA
-- Generated: 2025-11-23
-- This is the SINGLE SOURCE OF TRUTH for the database schema
-- Drop existing database and recreate from scratch
-- ============================================================================

DROP DATABASE IF EXISTS asmp_config;
CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asmp_config;

-- ============================================================================
-- CORE INFRASTRUCTURE TABLES
-- ============================================================================

-- Instances (Minecraft servers managed by AMP)
CREATE TABLE instances (
    instance_id VARCHAR(16) PRIMARY KEY COMMENT 'AMP instance ID',
    display_name VARCHAR(128) COMMENT 'Human-readable name',
    platform VARCHAR(32) COMMENT 'paper, velocity, fabric, etc',
    minecraft_version VARCHAR(32) COMMENT 'Minecraft version',
    server_name VARCHAR(64) COMMENT 'Physical server hostname',
    amp_instance_name VARCHAR(128) COMMENT 'Full AMP instance name',
    instance_path TEXT COMMENT 'Full filesystem path',
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_server (server_name),
    INDEX idx_platform (platform),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB COMMENT='AMP instances being managed';

-- Plugin Registry (global catalog of all known plugins)
CREATE TABLE plugins (
    plugin_id VARCHAR(64) PRIMARY KEY COMMENT 'Unique plugin identifier (lowercase)',
    plugin_name VARCHAR(128) NOT NULL COMMENT 'Plugin name from plugin.yml',
    display_name VARCHAR(128) COMMENT 'Human-friendly display name',
    platform VARCHAR(32) COMMENT 'paper, velocity, fabric, etc',
    current_stable_version VARCHAR(32) COMMENT 'Latest known stable version',
    author VARCHAR(256) COMMENT 'Plugin author',
    description TEXT COMMENT 'Plugin description',
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_platform (platform),
    INDEX idx_name (plugin_name)
) ENGINE=InnoDB COMMENT='Global plugin registry';

-- Instance Plugin Installations (which plugins are installed where)
CREATE TABLE instance_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(64) NOT NULL,
    installed_version VARCHAR(32) COMMENT 'Version currently installed',
    file_name VARCHAR(256) COMMENT 'JAR filename',
    file_path TEXT COMMENT 'Full path to JAR file',
    file_hash VARCHAR(64) COMMENT 'SHA256 hash of JAR',
    file_size BIGINT COMMENT 'File size in bytes',
    file_modified_at TIMESTAMP NULL COMMENT 'File mtime from filesystem',
    is_enabled BOOLEAN DEFAULT TRUE,
    first_discovered_at TIMESTAMP NULL COMMENT 'First time agent saw this',
    last_seen_at TIMESTAMP NULL COMMENT 'Last time agent saw this',
    installation_method VARCHAR(50) DEFAULT 'unknown' COMMENT 'How it was installed',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_plugin (instance_id, plugin_id),
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_file_hash (file_hash),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB COMMENT='Plugins installed on each instance';

-- Datapack Registry (global catalog of datapacks)
CREATE TABLE datapacks (
    datapack_id VARCHAR(128) PRIMARY KEY COMMENT 'Unique datapack identifier',
    datapack_name VARCHAR(128) NOT NULL COMMENT 'Datapack name',
    display_name VARCHAR(128) COMMENT 'Human-friendly name',
    version VARCHAR(32) COMMENT 'Datapack version',
    description TEXT,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (datapack_name)
) ENGINE=InnoDB COMMENT='Global datapack registry';

-- Instance Datapack Installations
CREATE TABLE instance_datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    datapack_id VARCHAR(128) NOT NULL COMMENT 'FK to datapacks table',
    world_name VARCHAR(64) NOT NULL COMMENT 'Which world has this datapack',
    version VARCHAR(32),
    file_name VARCHAR(256),
    file_path TEXT COMMENT 'Full path to datapack folder/zip',
    file_hash VARCHAR(64) COMMENT 'SHA256 if file, "folder" if directory',
    file_size BIGINT COMMENT 'Size in bytes, 0 for folders',
    is_enabled BOOLEAN DEFAULT TRUE,
    first_discovered_at TIMESTAMP NULL,
    last_seen_at TIMESTAMP NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_datapack_world (instance_id, datapack_id, world_name),
    INDEX idx_instance (instance_id),
    INDEX idx_datapack (datapack_id),
    INDEX idx_world (instance_id, world_name),
    INDEX idx_file_hash (file_hash),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB COMMENT='Datapacks installed per instance/world';

-- Server Properties
CREATE TABLE instance_server_properties (
    instance_id VARCHAR(16) PRIMARY KEY,
    level_name VARCHAR(64),
    gamemode VARCHAR(16),
    difficulty VARCHAR(16),
    max_players INT,
    view_distance INT,
    simulation_distance INT,
    pvp BOOLEAN,
    properties_json JSON COMMENT 'Full server.properties as JSON',
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- DISCOVERY & MONITORING TABLES
-- ============================================================================

-- Discovery Runs (summary of each agent scan)
CREATE TABLE discovery_runs (
    run_id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) NOT NULL COMMENT 'Which server ran the scan',
    run_type VARCHAR(32) COMMENT 'full_scan, incremental, etc',
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    status VARCHAR(32) COMMENT 'running, completed, failed',
    instances_discovered INT DEFAULT 0,
    plugins_discovered INT DEFAULT 0,
    datapacks_discovered INT DEFAULT 0,
    configs_scanned INT DEFAULT 0,
    new_items_found INT DEFAULT 0,
    changed_items INT DEFAULT 0,
    
    INDEX idx_server (server_name),
    INDEX idx_started (started_at),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='Summary of each discovery scan';

-- NOTE: discovery_items table REMOVED - was causing 153M record bloat
-- Agent now logs summary stats to discovery_runs only

-- ============================================================================
-- TAGGING & METADATA
-- ============================================================================

-- Meta Tag Categories
CREATE TABLE meta_tag_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(128),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Meta Tags
CREATE TABLE meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(64) UNIQUE NOT NULL,
    display_name VARCHAR(128),
    category_id INT,
    description TEXT,
    tag_color VARCHAR(7) COMMENT 'Hex color code',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES meta_tag_categories(category_id) ON DELETE SET NULL,
    INDEX idx_category (category_id)
) ENGINE=InnoDB;

-- Instance Meta Tags (many-to-many)
CREATE TABLE instance_meta_tags (
    instance_id VARCHAR(16),
    tag_id INT,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(64) COMMENT 'User or "system" for auto-tags',
    is_auto_detected BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3,2) COMMENT 'For auto-detected tags, 0-1',
    
    PRIMARY KEY (instance_id, tag_id),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    INDEX idx_tag (tag_id),
    INDEX idx_auto (is_auto_detected)
) ENGINE=InnoDB;

-- Meta Tag History
CREATE TABLE meta_tag_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    tag_id INT,
    action VARCHAR(16) COMMENT 'added, removed',
    performed_by VARCHAR(64),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    INDEX idx_instance (instance_id),
    INDEX idx_performed_at (performed_at)
) ENGINE=InnoDB;

-- Instance Tags (simple key-value tags)
CREATE TABLE instance_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    tag_name VARCHAR(64),
    tag_value VARCHAR(256),
    assigned_by VARCHAR(64),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_tag (instance_id, tag_name),
    INDEX idx_tag_name (tag_name)
) ENGINE=InnoDB;

-- ============================================================================
-- CONFIGURATION MANAGEMENT
-- ============================================================================

-- Config Rules (baseline expectations)
CREATE TABLE config_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64),
    config_file VARCHAR(128) COMMENT 'e.g., config.yml',
    config_key VARCHAR(256) COMMENT 'Dot-notation path',
    expected_value TEXT,
    value_type VARCHAR(32) COMMENT 'string, int, boolean, list, etc',
    applies_to_platform VARCHAR(32) COMMENT 'paper, velocity, etc',
    is_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_plugin_file (plugin_id, config_file),
    INDEX idx_platform (applies_to_platform)
) ENGINE=InnoDB COMMENT='Expected config values (baselines)';

-- Config Change History (ONLY for actual deployments, NOT drift detection)
CREATE TABLE config_change_history (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    plugin_name VARCHAR(128),
    config_file VARCHAR(128),
    config_key VARCHAR(256),
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(32) COMMENT 'manual, automated, migration, deployment',
    change_source VARCHAR(64) COMMENT 'web_ui, agent, api, script',
    changed_by VARCHAR(64),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    batch_id VARCHAR(64) COMMENT 'Group related changes',
    deployment_id INT COMMENT 'FK to deployments if applicable',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_name),
    INDEX idx_changed_at (changed_at),
    INDEX idx_batch (batch_id),
    INDEX idx_source (change_source)
) ENGINE=InnoDB COMMENT='Actual config changes deployed (NOT drift detection logs)';

-- Config Variance Detected (drift from baselines)
CREATE TABLE config_variance_detected (
    variance_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    plugin_id VARCHAR(64),
    config_file VARCHAR(128),
    config_key VARCHAR(256),
    expected_value TEXT,
    actual_value TEXT,
    variance_type VARCHAR(32) COMMENT 'missing, different, extra',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolution VARCHAR(32) COMMENT 'auto_fixed, manually_fixed, ignored, accepted',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE SET NULL,
    INDEX idx_instance (instance_id),
    INDEX idx_detected_at (detected_at),
    INDEX idx_resolved (resolved_at)
) ENGINE=InnoDB COMMENT='Detected config drift from baselines';

-- ============================================================================
-- DEPLOYMENT & UPDATES
-- ============================================================================

-- Plugin Update Queue
CREATE TABLE plugin_update_queue (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    plugin_id VARCHAR(64),
    current_version VARCHAR(32),
    target_version VARCHAR(32),
    update_priority VARCHAR(16) DEFAULT 'normal' COMMENT 'low, normal, high, critical',
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    queued_by VARCHAR(64),
    status VARCHAR(32) DEFAULT 'pending' COMMENT 'pending, in_progress, completed, failed',
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_priority (update_priority),
    INDEX idx_queued_at (queued_at)
) ENGINE=InnoDB;

-- Deployment History
CREATE TABLE deployment_history (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_type VARCHAR(32) COMMENT 'plugin_update, config_change, bulk_update',
    target_instances TEXT COMMENT 'JSON array of instance_ids',
    initiated_by VARCHAR(64),
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status VARCHAR(32) DEFAULT 'pending' COMMENT 'pending, running, completed, failed',
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    deployment_notes TEXT,
    
    INDEX idx_status (status),
    INDEX idx_initiated_at (initiated_at)
) ENGINE=InnoDB;

-- Change Approval Requests
CREATE TABLE change_approval_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    change_type VARCHAR(32) COMMENT 'config, plugin_update, bulk_operation',
    change_description TEXT,
    affected_instances TEXT COMMENT 'JSON array',
    requested_by VARCHAR(64),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approval_status VARCHAR(32) DEFAULT 'pending' COMMENT 'pending, approved, rejected',
    reviewed_by VARCHAR(64),
    reviewed_at TIMESTAMP NULL,
    review_notes TEXT,
    
    INDEX idx_status (approval_status),
    INDEX idx_requested_at (requested_at)
) ENGINE=InnoDB;

-- ============================================================================
-- WORLDS & REGIONS
-- ============================================================================

-- Worlds
CREATE TABLE worlds (
    world_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    world_name VARCHAR(64),
    world_type VARCHAR(32) COMMENT 'normal, nether, end, custom',
    seed BIGINT,
    spawn_x INT,
    spawn_y INT,
    spawn_z INT,
    difficulty VARCHAR(16),
    hardcore BOOLEAN DEFAULT FALSE,
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_world (instance_id, world_name),
    INDEX idx_instance (instance_id)
) ENGINE=InnoDB;

-- ============================================================================
-- SYSTEM HEALTH & MONITORING
-- ============================================================================

-- System Health Metrics (DISABLED - was causing bloat, now just logs to journalctl)
-- CREATE TABLE system_health_metrics - REMOVED

-- Notification Log
CREATE TABLE notification_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notification_type VARCHAR(32),
    title VARCHAR(256),
    message TEXT,
    priority VARCHAR(16) DEFAULT 'normal',
    related_entity_type VARCHAR(32),
    related_entity_id VARCHAR(64),
    metadata JSON,
    channels VARCHAR(128) COMMENT 'Comma-separated: database,web_ui,email',
    status VARCHAR(32) DEFAULT 'pending' COMMENT 'pending, sent, read',
    sent_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    read_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB;

-- Scheduled Tasks
CREATE TABLE scheduled_tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(128) UNIQUE NOT NULL,
    task_type VARCHAR(32) COMMENT 'discovery, cleanup, health_check, etc',
    schedule_expression VARCHAR(64) COMMENT 'Cron-like expression',
    is_enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP NULL,
    last_run_status VARCHAR(32),
    next_run_at TIMESTAMP NULL,
    run_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_enabled (is_enabled),
    INDEX idx_next_run (next_run_at)
) ENGINE=InnoDB;

-- Audit Log
CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user VARCHAR(64),
    action VARCHAR(128),
    description TEXT,
    ip_address VARCHAR(45),
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_user (user),
    INDEX idx_action (action)
) ENGINE=InnoDB;

-- ============================================================================
-- SEED DEFAULT DATA
-- ============================================================================

-- Default Meta Tag Categories
INSERT INTO meta_tag_categories (category_name, display_name, description) VALUES
('server_type', 'Server Type', 'Type of Minecraft server'),
('player_count', 'Player Count', 'Expected player capacity'),
('game_mode', 'Game Mode', 'Primary game mode'),
('mod_level', 'Modification Level', 'How heavily modded the server is'),
('maintenance', 'Maintenance', 'Maintenance and operational status');

-- Default Meta Tags
INSERT INTO meta_tags (tag_name, display_name, category_id, tag_color) VALUES
('pure-vanilla', 'Pure Vanilla', (SELECT category_id FROM meta_tag_categories WHERE category_name='mod_level'), '#8B4513'),
('lightly-modded', 'Lightly Modded', (SELECT category_id FROM meta_tag_categories WHERE category_name='mod_level'), '#4682B4'),
('heavily-modded', 'Heavily Modded', (SELECT category_id FROM meta_tag_categories WHERE category_name='mod_level'), '#DC143C'),
('survival', 'Survival', (SELECT category_id FROM meta_tag_categories WHERE category_name='game_mode'), '#228B22'),
('creative', 'Creative', (SELECT category_id FROM meta_tag_categories WHERE category_name='game_mode'), '#FFD700'),
('minigame', 'Minigame', (SELECT category_id FROM meta_tag_categories WHERE category_name='game_mode'), '#FF69B4'),
('hub', 'Hub/Lobby', (SELECT category_id FROM meta_tag_categories WHERE category_name='server_type'), '#4169E1'),
('proxy', 'Proxy Server', (SELECT category_id FROM meta_tag_categories WHERE category_name='server_type'), '#8A2BE2');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
