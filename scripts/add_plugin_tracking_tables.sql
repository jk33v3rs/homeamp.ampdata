-- ============================================================================
-- Plugin Tracking Tables
-- Adds plugin version management, change history, and deployment tracking
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- PLUGIN MANAGEMENT
-- ============================================================================

-- Plugins table
CREATE TABLE IF NOT EXISTS plugins (
    plugin_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(128) NOT NULL UNIQUE,
    display_name VARCHAR(256),
    description TEXT,
    source_url VARCHAR(512),
    documentation_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE INDEX idx_plugins_name ON plugins(plugin_name);

-- Plugin versions installed per instance
CREATE TABLE IF NOT EXISTS plugin_versions (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_name VARCHAR(128) NOT NULL,
    
    installed_version VARCHAR(64),
    jar_filename VARCHAR(256),
    jar_hash VARCHAR(64),
    
    latest_version VARCHAR(64),
    update_available BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP NULL,
    
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_instance_plugin (instance_id, plugin_name),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_plugin_versions_instance ON plugin_versions(instance_id);
CREATE INDEX idx_plugin_versions_plugin ON plugin_versions(plugin_name);
CREATE INDEX idx_plugin_versions_update ON plugin_versions(update_available);

-- ============================================================================
-- CHANGE TRACKING
-- ============================================================================

-- Config change history (already referenced by agent code)
CREATE TABLE IF NOT EXISTS config_change_history (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    
    instance_id VARCHAR(16),
    plugin_name VARCHAR(128),
    config_file VARCHAR(256),
    config_key VARCHAR(512),
    
    old_value TEXT,
    new_value TEXT,
    
    change_type ENUM('manual', 'automated', 'migration', 'drift_fix') DEFAULT 'manual',
    change_reason TEXT,
    
    changed_by VARCHAR(128),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    deployment_id INT NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE INDEX idx_change_history_instance ON config_change_history(instance_id);
CREATE INDEX idx_change_history_plugin ON config_change_history(plugin_name);
CREATE INDEX idx_change_history_time ON config_change_history(changed_at);
CREATE INDEX idx_change_history_type ON config_change_history(change_type);

-- ============================================================================
-- DEPLOYMENT TRACKING
-- ============================================================================

-- Deployment queue/history
CREATE TABLE IF NOT EXISTS deployment_history (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    
    deployment_type ENUM('config', 'plugin', 'full_sync') DEFAULT 'config',
    scope VARCHAR(32),
    target_instances TEXT,
    
    deployment_status ENUM('pending', 'in_progress', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    
    deployed_by VARCHAR(128),
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    
    deployment_notes TEXT,
    error_message TEXT,
    
    affected_instances INT DEFAULT 0,
    successful_instances INT DEFAULT 0,
    failed_instances INT DEFAULT 0
) ENGINE=InnoDB;

CREATE INDEX idx_deployment_status ON deployment_history(deployment_status);
CREATE INDEX idx_deployment_time ON deployment_history(deployed_at);
CREATE INDEX idx_deployment_type ON deployment_history(deployment_type);

-- ============================================================================
-- AUDIT LOG
-- ============================================================================

-- Audit log for all system actions
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INT AUTO_INCREMENT PRIMARY KEY,
    
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(64) NOT NULL,
    resource_type VARCHAR(64),
    resource_id VARCHAR(128),
    
    user_id VARCHAR(128),
    ip_address VARCHAR(45),
    
    action_details TEXT,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
) ENGINE=InnoDB;

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action ON audit_log(action_type);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_resource ON audit_log(resource_type, resource_id);

-- ============================================================================
-- VERIFY TABLES
-- ============================================================================

SELECT 'Plugin tracking tables created!' AS status;
SELECT TABLE_NAME FROM information_schema.tables 
WHERE table_schema = 'asmp_config' 
AND TABLE_NAME IN ('plugins', 'plugin_versions', 'config_change_history', 'deployment_history', 'audit_log')
ORDER BY TABLE_NAME;
