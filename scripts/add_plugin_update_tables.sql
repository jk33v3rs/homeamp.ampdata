-- Plugin Update Tracking Schema
-- Adds tables for plugin versions, CI/CD sources, documentation tracking, and datapacks

-- ============================================================================
-- Plugin Versions & Sources
-- ============================================================================

CREATE TABLE IF NOT EXISTS plugin_sources (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    source_type ENUM('github', 'spigot', 'modrinth', 'hangar', 'jenkins', 'github_actions', 'direct_url') NOT NULL,
    source_identifier VARCHAR(500) NOT NULL COMMENT 'Repo slug, resource ID, or URL',
    priority INT DEFAULT 10 COMMENT 'Lower = higher priority when multiple sources exist',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_plugin_source (plugin_name, source_type, source_identifier),
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_source_type (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Plugin distribution sources';

CREATE TABLE IF NOT EXISTS plugin_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    version_string VARCHAR(100) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    download_url TEXT,
    release_date DATETIME,
    changelog TEXT,
    is_prerelease BOOLEAN DEFAULT FALSE,
    version_major INT,
    version_minor INT,
    version_patch INT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_plugin_version (plugin_name, version_string, source_type),
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_release_date (release_date),
    INDEX idx_version_parts (version_major, version_minor, version_patch)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='All discovered plugin versions';

CREATE TABLE IF NOT EXISTS installed_plugins (
    installation_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_name VARCHAR(100) NOT NULL,
    plugin_name VARCHAR(255) NOT NULL,
    version_string VARCHAR(100),
    jar_filename VARCHAR(255),
    file_size_bytes BIGINT,
    file_hash VARCHAR(64) COMMENT 'SHA-256 hash',
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_name) REFERENCES instances(instance_name) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_plugin (instance_name, plugin_name),
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_instance (instance_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Currently installed plugins per instance';

CREATE TABLE IF NOT EXISTS plugin_update_status (
    status_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    latest_version VARCHAR(100),
    latest_source VARCHAR(50),
    latest_download_url TEXT,
    latest_changelog TEXT,
    update_available_count INT DEFAULT 0 COMMENT 'How many instances need this update',
    risk_level ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_plugin (plugin_name),
    INDEX idx_update_available (update_available_count),
    INDEX idx_last_checked (last_checked)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Latest version and update status per plugin';

-- ============================================================================
-- CI/CD Integration
-- ============================================================================

CREATE TABLE IF NOT EXISTS ci_cd_endpoints (
    endpoint_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    ci_type ENUM('github_actions', 'jenkins', 'gitlab_ci', 'circle_ci', 'travis_ci') NOT NULL,
    endpoint_url VARCHAR(500) NOT NULL,
    artifact_pattern VARCHAR(255) COMMENT 'Regex or glob pattern for artifact matching',
    auth_required BOOLEAN DEFAULT FALSE,
    auth_token_key VARCHAR(100) COMMENT 'Reference to credential storage',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_ci_endpoint (plugin_name, ci_type, endpoint_url),
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_ci_type (ci_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CI/CD endpoints for plugin builds';

CREATE TABLE IF NOT EXISTS ci_cd_builds (
    build_id INT AUTO_INCREMENT PRIMARY KEY,
    endpoint_id INT NOT NULL,
    plugin_name VARCHAR(255) NOT NULL,
    build_number VARCHAR(100),
    build_url VARCHAR(500),
    artifact_url TEXT,
    build_status ENUM('success', 'failure', 'pending', 'cancelled') DEFAULT 'success',
    commit_sha VARCHAR(40),
    branch_name VARCHAR(100),
    build_timestamp DATETIME,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (endpoint_id) REFERENCES ci_cd_endpoints(endpoint_id) ON DELETE CASCADE,
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_build_timestamp (build_timestamp),
    INDEX idx_build_status (build_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CI/CD build history';

-- ============================================================================
-- Documentation Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS plugin_documentation (
    doc_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    doc_type ENUM('wiki', 'readme', 'official_docs', 'javadoc', 'config_guide', 'api_docs') NOT NULL,
    doc_url VARCHAR(500) NOT NULL,
    title VARCHAR(255),
    last_updated DATETIME,
    content_hash VARCHAR(64) COMMENT 'SHA-256 hash to detect changes',
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_plugin_doc (plugin_name, doc_type, doc_url),
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_doc_type (doc_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Plugin documentation sources';

CREATE TABLE IF NOT EXISTS plugin_pages_tracked (
    page_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    page_url VARCHAR(500) NOT NULL,
    page_type ENUM('spigot_resource', 'modrinth_project', 'github_repo', 'hangar_project', 'custom') NOT NULL,
    page_title VARCHAR(255),
    description TEXT,
    author VARCHAR(255),
    download_count INT,
    rating DECIMAL(3, 2),
    last_scraped TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    scrape_interval_hours INT DEFAULT 24,
    UNIQUE KEY unique_page (plugin_name, page_url),
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_page_type (page_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Plugin project pages being monitored';

-- ============================================================================
-- Datapack Management
-- ============================================================================

CREATE TABLE IF NOT EXISTS datapacks (
    datapack_id INT AUTO_INCREMENT PRIMARY KEY,
    datapack_name VARCHAR(255) NOT NULL,
    version_string VARCHAR(100),
    minecraft_version VARCHAR(50) COMMENT 'Target MC version (e.g., 1.20.1)',
    source_url VARCHAR(500),
    description TEXT,
    author VARCHAR(255),
    file_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_datapack_version (datapack_name, version_string),
    INDEX idx_datapack_name (datapack_name),
    INDEX idx_minecraft_version (minecraft_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Available datapacks';

CREATE TABLE IF NOT EXISTS installed_datapacks (
    installation_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_name VARCHAR(100) NOT NULL,
    datapack_name VARCHAR(255) NOT NULL,
    version_string VARCHAR(100),
    world_name VARCHAR(100) DEFAULT 'world' COMMENT 'Which world has this datapack',
    file_hash VARCHAR(64),
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_name) REFERENCES instances(instance_name) ON DELETE CASCADE,
    INDEX idx_instance (instance_name),
    INDEX idx_datapack (datapack_name),
    INDEX idx_world (world_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Datapacks installed per instance';

-- ============================================================================
-- Update Deployment Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS plugin_deployments (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(255) NOT NULL,
    from_version VARCHAR(100),
    to_version VARCHAR(100) NOT NULL,
    target_instances JSON COMMENT 'Array of instance names',
    deployment_status ENUM('pending', 'in_progress', 'completed', 'failed', 'rolled_back') DEFAULT 'pending',
    initiated_by VARCHAR(100),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    error_message TEXT,
    rollback_available BOOLEAN DEFAULT FALSE,
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_status (deployment_status),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Plugin update deployment history';

-- ============================================================================
-- Seed Data
-- ============================================================================

-- Add some common plugin sources
INSERT IGNORE INTO plugin_sources (plugin_name, source_type, source_identifier, priority) VALUES
('WorldEdit', 'github', 'EngineHub/WorldEdit', 1),
('WorldGuard', 'github', 'EngineHub/WorldGuard', 1),
('Pl3xMap', 'github', 'pl3xgaming/Pl3xMap', 1),
('LuckPerms', 'github', 'LuckPerms/LuckPerms', 1),
('Vault', 'github', 'MilkBowl/Vault', 1),
('PlaceholderAPI', 'spigot', '6245', 1),
('EssentialsX', 'github', 'EssentialsX/Essentials', 1),
('CoreProtect', 'spigot', '8631', 1),
('GriefPrevention', 'spigot', '1884', 1),
('Plan', 'github', 'plan-player-analytics/Plan', 1),
('Citizens', 'spigot', '13811', 1),
('Denizen', 'spigot', '21039', 1),
('Sentinel', 'spigot', '22017', 1),
('LibsDisguises', 'spigot', '81', 1),
('ProtocolLib', 'spigot', '1997', 1),
('Shopkeepers', 'github', 'Shopkeepers/Shopkeepers', 1),
('ViaVersion', 'hangar', 'ViaVersion', 1),
('ViaBackwards', 'hangar', 'ViaBackwards', 1),
('Geyser', 'modrinth', 'geyser', 1),
('Floodgate', 'modrinth', 'floodgate', 1);
