-- Plugin Metadata Tables for CI/CD and Documentation Tracking
-- Run this to add plugin tracking to asmp_config database

USE asmp_config;

-- Plugin registry with metadata
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

-- Instance-specific plugin installations
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

-- Datapacks tracking
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

-- Server properties tracking
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

-- Plugin update queue
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
