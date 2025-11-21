-- ============================================================================
-- Dynamic Metadata and Auto-Discovery System
-- Comprehensive schema for self-discovering, tag-driven config management
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- DYNAMIC META-TAGGING SYSTEM (User-extensible)
-- ============================================================================

-- Tag categories (user can add/modify at any time)
CREATE TABLE IF NOT EXISTS meta_tag_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(64) NOT NULL UNIQUE,
    display_name VARCHAR(128) NOT NULL,
    description TEXT,
    is_multiselect BOOLEAN DEFAULT TRUE,  -- Allow multiple tags from this category?
    is_required BOOLEAN DEFAULT FALSE,    -- Must instance have at least one tag from this category?
    display_order INT DEFAULT 999,
    icon VARCHAR(64),
    color VARCHAR(16),  -- Hex color for UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_display_order (display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tags (user can add/modify/deprecate)
CREATE TABLE IF NOT EXISTS meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    tag_name VARCHAR(64) NOT NULL,  -- Slug/identifier
    display_name VARCHAR(128) NOT NULL,
    description TEXT,
    icon VARCHAR(64),
    color VARCHAR(16),
    is_system_tag BOOLEAN DEFAULT FALSE,  -- True = core system tag, False = user-defined
    is_deprecated BOOLEAN DEFAULT FALSE,
    replacement_tag_id INT,  -- If deprecated, what replaces it?
    metadata_json TEXT,  -- Flexible JSON for any extra properties
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES meta_tag_categories(category_id) ON DELETE RESTRICT,
    FOREIGN KEY (replacement_tag_id) REFERENCES meta_tags(tag_id) ON DELETE SET NULL,
    UNIQUE KEY unique_tag (category_id, tag_name),
    INDEX idx_category (category_id),
    INDEX idx_deprecated (is_deprecated)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instance tags (many-to-many with history)
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

-- Tag change history (audit trail for tag modifications)
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
-- PLUGIN REGISTRY (Fully Dynamic, CI/CD-Integrated)
-- ============================================================================

-- Comprehensive plugin registry
CREATE TABLE IF NOT EXISTS plugins (
    plugin_id VARCHAR(128) PRIMARY KEY,  -- Normalized slug
    plugin_name VARCHAR(256) NOT NULL,
    display_name VARCHAR(256),
    platform ENUM('paper', 'fabric', 'neoforge', 'geyser', 'velocity', 'datapack', 'unknown') NOT NULL,
    
    -- Versioning
    current_stable_version VARCHAR(64),
    latest_version VARCHAR(64),
    min_minecraft_version VARCHAR(16),
    max_minecraft_version VARCHAR(16),
    
    -- Source/Distribution Locations (multi-platform support)
    modrinth_id VARCHAR(128),
    modrinth_slug VARCHAR(128),
    hangar_slug VARCHAR(256),
    github_repo VARCHAR(512),
    github_release_pattern VARCHAR(256),  -- Regex for release asset matching
    spigot_id VARCHAR(32),
    bukkit_id VARCHAR(32),
    curseforge_id VARCHAR(32),
    jenkins_url TEXT,
    custom_download_url TEXT,
    
    -- Documentation & Info
    docs_url TEXT,
    wiki_url TEXT,
    plugin_page_url TEXT,
    changelog_url TEXT,
    support_discord TEXT,
    
    -- CI/CD Integration
    has_cicd BOOLEAN DEFAULT FALSE,
    cicd_provider ENUM('github_actions', 'github_releases', 'gitlab_ci', 'jenkins', 'modrinth_api', 'hangar_api', 'none') DEFAULT 'none',
    cicd_webhook_url TEXT,
    cicd_api_key_ref VARCHAR(128),  -- Reference to secrets store
    auto_update_enabled BOOLEAN DEFAULT FALSE,
    update_strategy ENUM('manual', 'notify_only', 'auto_stable', 'auto_latest') DEFAULT 'manual',
    
    -- Classification
    category VARCHAR(64),  -- e.g., 'combat', 'economy', 'admin', 'worldgen'
    tags TEXT,  -- JSON array of tags
    description TEXT,
    author VARCHAR(256),
    license VARCHAR(128),
    is_premium BOOLEAN DEFAULT FALSE,
    is_paid BOOLEAN DEFAULT FALSE,
    requires_license_key BOOLEAN DEFAULT FALSE,
    
    -- Dependencies
    dependencies TEXT,  -- JSON array: [{plugin_id, version_constraint, optional}]
    incompatibilities TEXT,  -- JSON array of incompatible plugins
    
    -- Tracking
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_update_check_at TIMESTAMP,
    last_available_version_at TIMESTAMP,
    
    -- Metadata
    metadata_json TEXT,  -- Flexible JSON for any extra properties
    
    INDEX idx_platform (platform),
    INDEX idx_modrinth_id (modrinth_id),
    INDEX idx_modrinth_slug (modrinth_slug),
    INDEX idx_hangar (hangar_slug(255)),
    INDEX idx_github (github_repo(255)),
    INDEX idx_category (category),
    INDEX idx_auto_update (auto_update_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instance-specific plugin installations (discovered dynamically)
CREATE TABLE IF NOT EXISTS instance_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    
    -- File details
    installed_version VARCHAR(64),
    file_name VARCHAR(512),
    file_path VARCHAR(1024),
    file_hash VARCHAR(64),  -- SHA-256
    file_size BIGINT,
    file_modified_at TIMESTAMP,
    
    -- State
    is_enabled BOOLEAN DEFAULT TRUE,
    is_outdated BOOLEAN DEFAULT FALSE,
    available_version VARCHAR(64),
    
    -- Discovery
    first_discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    installed_by VARCHAR(128),
    installation_method ENUM('manual', 'agent', 'cicd', 'amp', 'unknown') DEFAULT 'unknown',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_plugin (instance_id, plugin_id),
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_outdated (is_outdated),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DATAPACK REGISTRY (Auto-Discovery + Deployment)
-- ============================================================================

-- Datapack catalog
CREATE TABLE IF NOT EXISTS datapacks (
    datapack_id VARCHAR(128) PRIMARY KEY,
    datapack_name VARCHAR(256) NOT NULL,
    display_name VARCHAR(256),
    version VARCHAR(64),
    
    -- Source locations
    modrinth_id VARCHAR(128),
    github_repo VARCHAR(512),
    planetminecraft_url TEXT,
    custom_source_url TEXT,
    
    -- Documentation
    description TEXT,
    docs_url TEXT,
    changelog_url TEXT,
    
    -- Classification
    category VARCHAR(64),
    tags TEXT,  -- JSON array
    minecraft_version VARCHAR(16),
    
    -- Update tracking
    has_auto_update BOOLEAN DEFAULT FALSE,
    update_check_url TEXT,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    metadata_json TEXT,
    
    INDEX idx_modrinth (modrinth_id),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instance datapacks (per-world, auto-discovered)
CREATE TABLE IF NOT EXISTS instance_datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    datapack_id VARCHAR(128) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    
    -- File details
    version VARCHAR(64),
    file_name VARCHAR(512),
    file_path VARCHAR(1024),
    file_hash VARCHAR(64),
    file_size BIGINT,
    
    -- State
    is_enabled BOOLEAN DEFAULT TRUE,
    load_order INT,  -- Determined from world/datapacks folder
    
    -- Discovery
    first_discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_datapack_world (instance_id, datapack_id, world_name),
    INDEX idx_instance (instance_id),
    INDEX idx_datapack (datapack_id),
    INDEX idx_world (instance_id, world_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SERVER PROPERTIES & SETTINGS (Auto-Discovered)
-- ============================================================================

-- server.properties tracking
CREATE TABLE IF NOT EXISTS instance_server_properties (
    instance_id VARCHAR(16) PRIMARY KEY,
    
    -- Common properties
    level_name VARCHAR(128),
    gamemode VARCHAR(32),
    difficulty VARCHAR(32),
    max_players INT,
    view_distance INT,
    simulation_distance INT,
    pvp BOOLEAN,
    spawn_protection INT,
    enable_command_block BOOLEAN,
    
    -- Full snapshot (JSON of ALL properties for future-proofing)
    properties_json TEXT,
    
    -- Discovery
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    file_hash VARCHAR(64),
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Paper/Spigot/Bukkit configuration tracking
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

-- ============================================================================
-- AUTO-DISCOVERY TRACKING
-- ============================================================================

-- Track what the agent has discovered
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

-- Detailed discovery items
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

-- ============================================================================
-- PLUGIN UPDATE MANAGEMENT
-- ============================================================================

-- Update queue (user-triggered or auto)
CREATE TABLE IF NOT EXISTS plugin_update_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(128) NOT NULL,
    target_instances TEXT,  -- JSON array of instance_ids, or '*' for all
    
    from_version VARCHAR(64),
    to_version VARCHAR(64) NOT NULL,
    download_url TEXT,
    
    -- Scheduling
    priority INT DEFAULT 5,  -- 1-10, higher = more urgent
    scheduled_for TIMESTAMP NULL,
    requires_restart BOOLEAN DEFAULT TRUE,
    auto_restart BOOLEAN DEFAULT FALSE,
    
    -- Status
    status ENUM('pending', 'downloading', 'deploying', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NOT NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    
    -- Results
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    error_message TEXT,
    deployment_log TEXT,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_priority (priority DESC),
    INDEX idx_scheduled (scheduled_for),
    INDEX idx_plugin (plugin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Datapack deployment queue
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
    
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_scheduled (scheduled_for)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- CI/CD WEBHOOK EVENTS
-- ============================================================================

-- Incoming webhook events from CI/CD systems
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

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Active plugin installations with update status
CREATE OR REPLACE VIEW v_plugin_status AS
SELECT 
    ip.instance_id,
    i.instance_name AS instance_name,
    ip.plugin_id,
    p.display_name AS plugin_name,
    ip.installed_version,
    p.latest_version,
    ip.is_outdated,
    ip.is_enabled,
    p.platform,
    p.auto_update_enabled,
    ip.last_seen_at,
    p.last_checked_at AS plugin_last_checked
FROM instance_plugins ip
JOIN plugins p ON ip.plugin_id = p.plugin_id
JOIN instances i ON ip.instance_id = i.instance_id
ORDER BY ip.instance_id, p.display_name;

-- Instance summary with tags
CREATE OR REPLACE VIEW v_instance_summary AS
SELECT 
    i.instance_id,
    i.display_name,
    i.platform,
    i.minecraft_version,
    i.server_name,
    GROUP_CONCAT(DISTINCT mt.display_name ORDER BY mtc.display_order SEPARATOR ', ') AS tags,
    COUNT(DISTINCT ip.plugin_id) AS plugin_count,
    COUNT(DISTINCT id.datapack_id) AS datapack_count,
    i.last_seen_at
FROM instances i
LEFT JOIN instance_meta_tags imt ON i.instance_id = imt.instance_id
LEFT JOIN meta_tags mt ON imt.tag_id = mt.tag_id
LEFT JOIN meta_tag_categories mtc ON mt.category_id = mtc.category_id
LEFT JOIN instance_plugins ip ON i.instance_id = ip.instance_id
LEFT JOIN instance_datapacks id ON i.instance_id = id.instance_id
GROUP BY i.instance_id;

-- Pending updates
CREATE OR REPLACE VIEW v_pending_updates AS
SELECT 
    ip.instance_id,
    i.display_name AS instance_name,
    ip.plugin_id,
    p.display_name AS plugin_name,
    ip.installed_version AS current_version,
    p.latest_version AS available_version,
    p.changelog_url,
    p.auto_update_enabled
FROM instance_plugins ip
JOIN plugins p ON ip.plugin_id = p.plugin_id
JOIN instances i ON ip.instance_id = i.instance_id
WHERE ip.is_outdated = TRUE
ORDER BY p.auto_update_enabled DESC, i.instance_id;

