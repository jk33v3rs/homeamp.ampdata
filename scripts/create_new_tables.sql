-- Create new tables for GUI features
-- Run with: mysql -u sqlworkerSMP -p'SQLdb2024!' -h 135.181.212.169 -P 3369 asmp_config < scripts/create_new_tables.sql

-- Deployment tracking tables
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

-- Plugin update management tables
CREATE TABLE IF NOT EXISTS plugin_update_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id INT NOT NULL,
    source_type ENUM('spigot', 'modrinth', 'hangar', 'github', 'jenkins') NOT NULL,
    source_url VARCHAR(512) NOT NULL,
    build_selector VARCHAR(255),
    download_url_pattern VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE,
    INDEX idx_plugin_id (plugin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS plugin_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id INT NOT NULL,
    current_version VARCHAR(50),
    latest_version VARCHAR(50),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_available BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE,
    INDEX idx_plugin_id (plugin_id),
    INDEX idx_update_available (update_available)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tag management tables
CREATE TABLE IF NOT EXISTS meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL,
    parent_tag_id INT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_tag_id) REFERENCES meta_tags(id) ON DELETE SET NULL,
    INDEX idx_parent_tag_id (parent_tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS tag_instances (
    tag_id INT NOT NULL,
    instance_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (tag_id, instance_id),
    FOREIGN KEY (tag_id) REFERENCES meta_tags(id) ON DELETE CASCADE,
    INDEX idx_instance_id (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS tag_hierarchy (
    parent_tag_id INT NOT NULL,
    child_tag_id INT NOT NULL,
    PRIMARY KEY (parent_tag_id, child_tag_id),
    FOREIGN KEY (parent_tag_id) REFERENCES meta_tags(id) ON DELETE CASCADE,
    FOREIGN KEY (child_tag_id) REFERENCES meta_tags(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Config variance tracking
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

-- Server properties management
CREATE TABLE IF NOT EXISTS server_properties_baselines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_key VARCHAR(255) NOT NULL UNIQUE,
    property_value TEXT,
    baseline_type ENUM('global', 'tag-specific') DEFAULT 'global',
    INDEX idx_baseline_type (baseline_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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

-- Datapack management
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

CREATE TABLE IF NOT EXISTS datapack_update_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    datapack_id INT NOT NULL,
    source_type ENUM('github', 'planetmc', 'custom') NOT NULL,
    source_url VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (datapack_id) REFERENCES datapacks(id) ON DELETE CASCADE,
    INDEX idx_datapack_id (datapack_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Config history for rollback
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

-- Audit log
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

-- Agent heartbeat monitoring
CREATE TABLE IF NOT EXISTS agent_heartbeats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL UNIQUE,
    server_name VARCHAR(255) NOT NULL,
    last_heartbeat DATETIME NOT NULL,
    status ENUM('online', 'offline') DEFAULT 'online',
    INDEX idx_server_name (server_name),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Display success message
SELECT 'All tables created successfully!' AS status;
