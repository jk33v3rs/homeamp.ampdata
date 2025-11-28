-- Schema without foreign keys for initial creation
USE homeamp_v2;

SET FOREIGN_KEY_CHECKS = 0;

-- Drop all tables if they exist
DROP TABLE IF EXISTS instance_meta_tags;
DROP TABLE IF EXISTS instance_tags;
DROP TABLE IF EXISTS instance_group_members;
DROP TABLE IF EXISTS instance_groups;
DROP TABLE IF EXISTS instances;
DROP TABLE IF EXISTS meta_tags;
DROP TABLE IF EXISTS servers;
DROP TABLE IF EXISTS plugins;
DROP TABLE IF EXISTS plugin_installations;
DROP TABLE IF EXISTS plugin_versions;
DROP TABLE IF EXISTS plugin_update_sources;
DROP TABLE IF EXISTS plugin_configs;
DROP TABLE IF EXISTS plugin_config_keys;
DROP TABLE IF EXISTS datapacks;
DROP TABLE IF EXISTS datapack_installations;
DROP TABLE IF EXISTS datapack_versions;
DROP TABLE IF EXISTS datapack_metadata;
DROP TABLE IF EXISTS worlds;
DROP TABLE IF EXISTS config_files;
DROP TABLE IF EXISTS config_keys;
DROP TABLE IF EXISTS config_values;
DROP TABLE IF EXISTS config_hierarchy;
DROP TABLE IF EXISTS config_rules;
DROP TABLE IF EXISTS config_variances;
DROP TABLE IF EXISTS deployments;
DROP TABLE IF EXISTS deployment_queue;
DROP TABLE IF EXISTS deployment_history;
DROP TABLE IF EXISTS deployment_steps;
DROP TABLE IF EXISTS datapack_deployment_queue;
DROP TABLE IF EXISTS update_checks;
DROP TABLE IF EXISTS plugin_updates;
DROP TABLE IF EXISTS approval_requests;
DROP TABLE IF EXISTS approval_votes;
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS change_history;
DROP TABLE IF EXISTS backup_snapshots;

SET FOREIGN_KEY_CHECKS = 1;

-- Core tables
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE instance_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    group_type VARCHAR(32),
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE instance_group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    group_id INT,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    assignment_note TEXT,
    UNIQUE KEY unique_instance_group (instance_id, group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(64) UNIQUE NOT NULL,
    category VARCHAR(32),
    description TEXT,
    color_code VARCHAR(16),
    icon VARCHAR(64),
    is_system_tag BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE instance_tags (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    tag_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128),
    UNIQUE KEY unique_instance_tag (instance_id, tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE servers (
    server_id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) UNIQUE NOT NULL,
    hostname VARCHAR(255),
    ip_address VARCHAR(45),
    ssh_port INT DEFAULT 22,
    location VARCHAR(128),
    provider VARCHAR(64),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE plugins (
    plugin_id VARCHAR(64) PRIMARY KEY,
    plugin_name VARCHAR(128) NOT NULL,
    version VARCHAR(32),
    author VARCHAR(128),
    description TEXT,
    homepage VARCHAR(255),
    platform VARCHAR(16) DEFAULT 'paper',
    api_version VARCHAR(16),
    main_class VARCHAR(255),
    is_premium BOOLEAN DEFAULT false,
    update_source VARCHAR(32),
    update_id VARCHAR(128),
    last_update_check TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE plugin_installations (
    installation_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(64) NOT NULL,
    installed_version VARCHAR(32),
    jar_path VARCHAR(512),
    file_hash VARCHAR(64),
    is_enabled BOOLEAN DEFAULT true,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NULL,
    UNIQUE KEY unique_instance_plugin (instance_id, plugin_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE plugin_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL,
    release_date DATE,
    minecraft_version VARCHAR(32),
    download_url VARCHAR(512),
    changelog TEXT,
    is_latest BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE plugin_update_sources (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    source_id_value VARCHAR(128),
    api_url VARCHAR(512),
    check_interval INT DEFAULT 3600,
    last_check TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT true
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    version VARCHAR(32),
    description TEXT,
    author VARCHAR(128),
    pack_format INT,
    namespace VARCHAR(64),
    file_path VARCHAR(512),
    file_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE datapack_installations (
    installation_id INT AUTO_INCREMENT PRIMARY KEY,
    world_id INT,
    datapack_id INT,
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_enabled BOOLEAN DEFAULT true
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE worlds (
    world_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    world_type VARCHAR(32),
    environment VARCHAR(32) DEFAULT 'normal',
    seed VARCHAR(64),
    generator VARCHAR(64),
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE config_files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    plugin_id VARCHAR(64),
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(512),
    file_type VARCHAR(32) DEFAULT 'yaml',
    file_hash VARCHAR(64),
    last_modified TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE config_keys (
    key_id INT AUTO_INCREMENT PRIMARY KEY,
    file_id INT,
    key_path VARCHAR(512) NOT NULL,
    key_name VARCHAR(255),
    data_type VARCHAR(32),
    default_value TEXT,
    description TEXT,
    is_required BOOLEAN DEFAULT false
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE config_values (
    value_id INT AUTO_INCREMENT PRIMARY KEY,
    key_id INT,
    instance_id VARCHAR(16),
    value TEXT,
    value_type VARCHAR(32),
    last_modified TIMESTAMP NULL,
    modified_by VARCHAR(128)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE deployments (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_name VARCHAR(128),
    deployment_type VARCHAR(32) NOT NULL,
    target_instances TEXT,
    created_by VARCHAR(128),
    status VARCHAR(32) DEFAULT 'pending',
    scheduled_at TIMESTAMP NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE deployment_queue (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_id INT,
    instance_id VARCHAR(16),
    plugin_id VARCHAR(64),
    target_version VARCHAR(32),
    priority INT DEFAULT 0,
    status VARCHAR(32) DEFAULT 'pending',
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    error_message TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE update_checks (
    check_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64),
    current_version VARCHAR(32),
    latest_version VARCHAR(32),
    update_available BOOLEAN DEFAULT false,
    source VARCHAR(32),
    check_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    release_notes TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE approval_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    request_type VARCHAR(32) NOT NULL,
    entity_type VARCHAR(32),
    entity_id VARCHAR(128),
    requested_by VARCHAR(128),
    status VARCHAR(32) DEFAULT 'pending',
    required_approvals INT DEFAULT 1,
    current_approvals INT DEFAULT 0,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    details JSON
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE approval_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT,
    voter VARCHAR(128),
    approved BOOLEAN,
    vote_reason TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user VARCHAR(128),
    action VARCHAR(64) NOT NULL,
    entity_type VARCHAR(32),
    entity_id VARCHAR(128),
    details JSON,
    ip_address VARCHAR(45),
    user_agent TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE backup_snapshots (
    snapshot_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    snapshot_type VARCHAR(32) DEFAULT 'full',
    file_path VARCHAR(512),
    file_size BIGINT,
    compression_type VARCHAR(32),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    notes TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Indexes
CREATE INDEX idx_instance_tags_instance ON instance_tags(instance_id);
CREATE INDEX idx_instance_tags_tag ON instance_tags(tag_id);
CREATE INDEX idx_plugin_installations_instance ON plugin_installations(instance_id);
CREATE INDEX idx_plugin_installations_plugin ON plugin_installations(plugin_id);
CREATE INDEX idx_config_files_instance ON config_files(instance_id);
CREATE INDEX idx_config_files_plugin ON config_files(plugin_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user ON audit_log(user);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
