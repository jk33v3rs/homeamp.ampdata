-- ============================================================================
-- Comprehensive Config & Plugin Tracking Extension
-- Extends existing schema with granular key-level tracking, variance detection,
-- developer info, documentation, CI/CD builds, and meta-tags for everything
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- PLUGIN EXTENSIONS (Documentation, Developers, CI/CD Builds)
-- ============================================================================

-- Plugin developers/authors
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

-- Link plugins to developers (many-to-many)
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

-- CI/CD build history
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

-- Plugin documentation pages
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

-- Plugin version history
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

-- ============================================================================
-- GLOBAL CONFIG BASELINE (Key-level granular tracking)
-- ============================================================================

-- Global baseline config values (one row per key)
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

-- ============================================================================
-- INSTANCE-SPECIFIC CONFIG VALUES (Actual deployed values)
-- ============================================================================

-- Instance config actual values (what's actually in files)
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

-- ============================================================================
-- VARIANCE TRACKING (Differences from baseline)
-- ============================================================================

-- Detected variances (differences from global baseline)
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
-- DATAPACK EXTENSIONS
-- ============================================================================

-- Datapack version registry
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
-- META TAGS FOR EVERYTHING
-- ============================================================================

-- Server tags (for physical servers)
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

-- Group tags (for instance groups)
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

-- User/Player tags
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

-- Rank tags (meta-tags for rank definitions)
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

-- ============================================================================
-- RANK HIERARCHY (Subranks)
-- ============================================================================

-- Sub-ranks within main ranks
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

-- Player subrank progress
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

-- ============================================================================
-- CONFIG FILE METADATA
-- ============================================================================

-- Track config file versions and checksums
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

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

SELECT 'Comprehensive tracking schema extension created!' AS status;
SELECT TABLE_NAME, TABLE_ROWS 
FROM information_schema.tables 
WHERE table_schema = 'asmp_config' 
ORDER BY TABLE_NAME;
