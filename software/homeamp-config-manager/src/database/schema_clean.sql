-- ArchiveSMP Configuration Manager Database Schema
-- CORRECT database name: asmp_config
-- DO NOT USE: asmp_SQL (that's AMP's production database)

-- Servers
CREATE TABLE IF NOT EXISTS servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(50) NOT NULL UNIQUE,
    ip_address VARCHAR(45),
    hostname VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instances
CREATE TABLE IF NOT EXISTS instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(20) NOT NULL UNIQUE,
    instance_name VARCHAR(100),
    server_name VARCHAR(50),
    instance_type VARCHAR(20),
    minecraft_version VARCHAR(20),
    platform_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Plugins Registry
CREATE TABLE IF NOT EXISTS plugins (
    plugin_id VARCHAR(100) PRIMARY KEY,
    plugin_name VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    current_version VARCHAR(50),
    latest_version VARCHAR(50),
    github_repo VARCHAR(200),
    modrinth_id VARCHAR(100),
    hangar_slug VARCHAR(100),
    spigot_id VARCHAR(50),
    bukkit_id VARCHAR(100),
    curseforge_id VARCHAR(100),
    docs_url TEXT,
    wiki_url TEXT,
    plugin_page_url TEXT,
    has_cicd BOOLEAN DEFAULT FALSE,
    cicd_provider VARCHAR(50) DEFAULT 'none',
    cicd_url TEXT,
    description TEXT,
    author VARCHAR(200),
    license VARCHAR(100),
    last_checked_at TIMESTAMP NULL,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instance Plugins (what's installed where)
CREATE TABLE IF NOT EXISTS instance_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(20) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    installed_version VARCHAR(50),
    file_name VARCHAR(255),
    file_hash VARCHAR(64),
    is_enabled BOOLEAN DEFAULT TRUE,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_instance_plugin (instance_id, plugin_id),
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instance Datapacks
CREATE TABLE IF NOT EXISTS instance_datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(20) NOT NULL,
    datapack_name VARCHAR(100) NOT NULL,
    world_name VARCHAR(100) DEFAULT 'world',
    file_name VARCHAR(255),
    file_hash VARCHAR(64),
    modrinth_id VARCHAR(100),
    github_repo VARCHAR(200),
    custom_source TEXT,
    is_enabled BOOLEAN DEFAULT TRUE,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_instance_datapack (instance_id, datapack_name, world_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Instance Server Properties
CREATE TABLE IF NOT EXISTS instance_server_properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(20) NOT NULL UNIQUE,
    level_name VARCHAR(100),
    gamemode VARCHAR(20),
    difficulty VARCHAR(20),
    max_players INT,
    view_distance INT,
    simulation_distance INT,
    pvp BOOLEAN,
    spawn_protection INT,
    properties_json JSON,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Baseline Snapshots (expected configs from universal baselines)
CREATE TABLE IF NOT EXISTS baseline_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    snapshot_id VARCHAR(50) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    config_data JSON NOT NULL,
    priority ENUM('GLOBAL', 'SERVER', 'INSTANCE') DEFAULT 'GLOBAL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_snapshot_plugin (snapshot_id, plugin_id),
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Config Rules (transformation rules)
CREATE TABLE IF NOT EXISTS config_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(100) NOT NULL,
    config_key VARCHAR(500) NOT NULL,
    expected_value TEXT,
    applies_to VARCHAR(100) DEFAULT 'ALL',
    priority ENUM('GLOBAL', 'SERVER', 'INSTANCE') DEFAULT 'GLOBAL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_rule (plugin_id, config_key(255), applies_to),
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Drift Detection Results
CREATE TABLE IF NOT EXISTS drift_detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(20) NOT NULL,
    plugin_id VARCHAR(100) NOT NULL,
    config_key VARCHAR(500) NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    drift_type VARCHAR(50),
    severity ENUM('critical', 'warning', 'info') DEFAULT 'warning',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_unresolved (instance_id, resolved_at),
    INDEX idx_plugin (plugin_id),
    INDEX idx_detected (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Change History
CREATE TABLE IF NOT EXISTS config_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(20) NOT NULL,
    plugin_id VARCHAR(100),
    config_key VARCHAR(500),
    old_value TEXT,
    new_value TEXT,
    change_type VARCHAR(50),
    changed_by VARCHAR(100),
    change_reason TEXT,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE SET NULL,
    INDEX idx_instance (instance_id),
    INDEX idx_deployed (deployed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Performance indexes (no duplicates)
CREATE INDEX idx_instance_type ON instances(instance_type);
CREATE INDEX idx_plugin_platform ON plugins(platform);
CREATE INDEX idx_instance_plugin_instance ON instance_plugins(instance_id);
CREATE INDEX idx_instance_plugin_plugin ON instance_plugins(plugin_id);
CREATE INDEX idx_baseline_snapshot ON baseline_snapshots(snapshot_id);
CREATE INDEX idx_rules_priority ON config_rules(priority);
