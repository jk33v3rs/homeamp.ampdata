-- Endpoint Config File Tracking System
-- Purpose: Track all config files for plugins/datapacks, with backup and change history
-- Author: AI Assistant
-- Date: 2025-01-04
-- Related Todos: #8, #9, #10

-- =============================================================================
-- Table 1: endpoint_config_files
-- Tracks location and metadata for all config files
-- =============================================================================
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

-- =============================================================================
-- Table 2: endpoint_config_backups
-- Stores full content snapshots before modifications
-- =============================================================================
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

-- =============================================================================
-- Table 3: endpoint_config_change_history
-- Audit log of every modification to config files
-- =============================================================================
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

-- =============================================================================
-- DEPLOYMENT INSTRUCTIONS
-- =============================================================================
-- 1. Test on development database first
-- 2. Verify tables created: SHOW TABLES LIKE 'endpoint_config%';
-- 3. Check structure: DESC endpoint_config_files;
-- 4. Deploy to Hetzner: mysql -u root -p archivesmp_config < create_endpoint_config_tables.sql
-- 5. Deploy to OVH after Hetzner validation
-- 6. Agent will populate on next discovery scan
