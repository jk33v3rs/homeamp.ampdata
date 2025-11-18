-- ============================================================================
-- Tracking & History Extension - OPTION C IMPLEMENTATION
-- Adds change tracking, deployment history, and audit capabilities
-- WITHOUT duplicating existing config_rules functionality
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- 1. CONFIG KEY MIGRATIONS (Version Upgrade Support)
-- ============================================================================

CREATE TABLE IF NOT EXISTS config_key_migrations (
    migration_id INT AUTO_INCREMENT PRIMARY KEY,
    
    plugin_name VARCHAR(64) NOT NULL,
    old_key_path VARCHAR(512) NOT NULL,
    new_key_path VARCHAR(512) NOT NULL,
    
    from_version VARCHAR(32) COMMENT 'Plugin version where key was deprecated',
    to_version VARCHAR(32) COMMENT 'Plugin version with new key',
    
    migration_type ENUM('rename', 'move', 'split', 'merge', 'remove', 'type_change') DEFAULT 'rename',
    value_transform TEXT COMMENT 'Python expression to transform value, e.g., "int(x) * 1000"',
    
    is_breaking BOOLEAN DEFAULT false COMMENT 'Whether this breaks backward compatibility',
    is_automatic BOOLEAN DEFAULT true COMMENT 'Whether to apply automatically',
    
    notes TEXT,
    documentation_url TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    
    UNIQUE KEY unique_migration (plugin_name, old_key_path, from_version),
    INDEX idx_plugin (plugin_name),
    INDEX idx_from_version (from_version),
    INDEX idx_migration_type (migration_type),
    INDEX idx_breaking (is_breaking)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE config_key_migrations IS 'Tracks config key changes between plugin versions for automatic migration';

-- ============================================================================
-- 2. CONFIG CHANGE HISTORY (Replaces file-based audit logs)
-- ============================================================================

CREATE TABLE IF NOT EXISTS config_change_history (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    
    instance_id VARCHAR(16),
    plugin_name VARCHAR(64) NOT NULL,
    config_file VARCHAR(256),
    config_key VARCHAR(512),
    
    old_value TEXT,
    new_value TEXT,
    value_type VARCHAR(16),
    
    change_type ENUM('manual', 'automated', 'drift_fix', 'version_upgrade', 'rule_update', 'migration') DEFAULT 'manual',
    change_source VARCHAR(32) COMMENT 'web_ui, api, cli, agent, migration_script',
    
    changed_by VARCHAR(64) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    
    deployment_id INT COMMENT 'Links to deployment that applied this change',
    batch_id VARCHAR(64) COMMENT 'Groups related changes together',
    
    is_reverted BOOLEAN DEFAULT FALSE,
    reverted_at TIMESTAMP NULL,
    reverted_by VARCHAR(64),
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE SET NULL,
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_name),
    INDEX idx_changed_at (changed_at),
    INDEX idx_changed_by (changed_by),
    INDEX idx_change_type (change_type),
    INDEX idx_deployment (deployment_id),
    INDEX idx_batch (batch_id),
    INDEX idx_reverted (is_reverted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE config_change_history IS 'Complete audit trail of all configuration changes';

-- ============================================================================
-- 3. DEPLOYMENT HISTORY (Track deployments and their outcomes)
-- ============================================================================

CREATE TABLE IF NOT EXISTS deployment_history (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    
    deployment_type ENUM('config', 'plugin', 'full', 'hotfix', 'rollback') NOT NULL,
    deployment_scope VARCHAR(32) COMMENT 'single, server, group, network',
    
    target_instances TEXT COMMENT 'JSON array of instance_ids',
    target_server VARCHAR(32),
    target_group_id INT,
    
    deployed_by VARCHAR(64) NOT NULL,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployment_duration_seconds INT,
    
    deployment_status ENUM('pending', 'in_progress', 'success', 'partial', 'failed', 'rolled_back') DEFAULT 'pending',
    
    changes_count INT DEFAULT 0,
    success_count INT DEFAULT 0,
    failure_count INT DEFAULT 0,
    
    pre_deployment_snapshot TEXT COMMENT 'JSON backup of state before deployment',
    error_log TEXT,
    
    rollback_deployment_id INT COMMENT 'If this is a rollback, points to original deployment',
    is_rollback BOOLEAN DEFAULT FALSE,
    
    notes TEXT,
    
    FOREIGN KEY (target_group_id) REFERENCES instance_groups(group_id) ON DELETE SET NULL,
    FOREIGN KEY (rollback_deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    INDEX idx_deployed_at (deployed_at),
    INDEX idx_deployed_by (deployed_by),
    INDEX idx_deployment_type (deployment_type),
    INDEX idx_status (deployment_status),
    INDEX idx_target_server (target_server),
    INDEX idx_is_rollback (is_rollback)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE deployment_history IS 'Tracks all deployments with success/failure outcomes';

-- ============================================================================
-- 4. DEPLOYMENT CHANGES (Links changes to deployments)
-- ============================================================================

CREATE TABLE IF NOT EXISTS deployment_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    deployment_id INT NOT NULL,
    change_id INT NOT NULL,
    
    change_status ENUM('pending', 'success', 'failed', 'skipped') DEFAULT 'pending',
    error_message TEXT,
    
    applied_at TIMESTAMP NULL,
    
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE CASCADE,
    FOREIGN KEY (change_id) REFERENCES config_change_history(change_id) ON DELETE CASCADE,
    UNIQUE KEY unique_deployment_change (deployment_id, change_id),
    INDEX idx_deployment (deployment_id),
    INDEX idx_change (change_id),
    INDEX idx_status (change_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE deployment_changes IS 'Many-to-many link between deployments and changes';

-- ============================================================================
-- 5. CONFIG RULE HISTORY (Track changes to config rules themselves)
-- ============================================================================

CREATE TABLE IF NOT EXISTS config_rule_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    
    rule_id INT NOT NULL,
    
    plugin_name VARCHAR(64),
    config_key VARCHAR(512),
    scope_type VARCHAR(16),
    scope_selector VARCHAR(128),
    
    old_value TEXT,
    new_value TEXT,
    
    old_priority INT,
    new_priority INT,
    
    change_type ENUM('create', 'update', 'delete', 'priority_change', 'scope_change') NOT NULL,
    
    changed_by VARCHAR(64),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    
    FOREIGN KEY (rule_id) REFERENCES config_rules(rule_id) ON DELETE CASCADE,
    INDEX idx_rule (rule_id),
    INDEX idx_changed_at (changed_at),
    INDEX idx_changed_by (changed_by),
    INDEX idx_change_type (change_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE config_rule_history IS 'Audit trail for changes to config_rules table';

-- Create trigger to auto-populate config_rule_history on UPDATE
DELIMITER //
CREATE TRIGGER config_rule_update_history
AFTER UPDATE ON config_rules
FOR EACH ROW
BEGIN
    DECLARE change_type_val ENUM('create', 'update', 'delete', 'priority_change', 'scope_change');
    
    -- Determine change type
    IF OLD.scope_type != NEW.scope_type OR OLD.scope_selector != NEW.scope_selector THEN
        SET change_type_val = 'scope_change';
    ELSEIF OLD.priority != NEW.priority THEN
        SET change_type_val = 'priority_change';
    ELSEIF NEW.is_active = FALSE AND OLD.is_active = TRUE THEN
        SET change_type_val = 'delete';
    ELSE
        SET change_type_val = 'update';
    END IF;
    
    INSERT INTO config_rule_history (
        rule_id, plugin_name, config_key, scope_type, scope_selector,
        old_value, new_value, old_priority, new_priority,
        change_type, changed_by, change_reason
    ) VALUES (
        OLD.rule_id, OLD.plugin_name, OLD.config_key, OLD.scope_type, OLD.scope_selector,
        OLD.config_value, NEW.config_value, OLD.priority, NEW.priority,
        change_type_val, NEW.last_modified_by, NEW.notes
    );
END//
DELIMITER ;

-- Create trigger for INSERT (create events)
DELIMITER //
CREATE TRIGGER config_rule_create_history
AFTER INSERT ON config_rules
FOR EACH ROW
BEGIN
    INSERT INTO config_rule_history (
        rule_id, plugin_name, config_key, scope_type, scope_selector,
        old_value, new_value, old_priority, new_priority,
        change_type, changed_by, change_reason
    ) VALUES (
        NEW.rule_id, NEW.plugin_name, NEW.config_key, NEW.scope_type, NEW.scope_selector,
        NULL, NEW.config_value, NULL, NEW.priority,
        'create', NEW.created_by, NEW.notes
    );
END//
DELIMITER ;

-- ============================================================================
-- 6. VARIANCE HISTORY (Track how variance changes over time)
-- ============================================================================

CREATE TABLE IF NOT EXISTS config_variance_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    
    variance_type VARCHAR(16),
    is_expected_variance BOOLEAN,
    
    total_instances INT,
    unique_values INT,
    drift_count INT COMMENT 'How many instances have unexpected drift',
    
    variance_reason TEXT,
    variance_details TEXT COMMENT 'JSON with per-instance breakdown',
    
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_plugin_key (plugin_name, config_key),
    INDEX idx_snapshot_time (snapshot_timestamp),
    INDEX idx_variance_type (variance_type),
    INDEX idx_drift_count (drift_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE config_variance_history IS 'Historical snapshots of config variance for trend analysis';

-- ============================================================================
-- 7. PLUGIN INSTALLATION HISTORY (Track plugin adds/removes/updates)
-- ============================================================================

CREATE TABLE IF NOT EXISTS plugin_installation_history (
    install_id INT AUTO_INCREMENT PRIMARY KEY,
    
    instance_id VARCHAR(16) NOT NULL,
    plugin_name VARCHAR(64) NOT NULL,
    
    action ENUM('install', 'remove', 'update', 'enable', 'disable') NOT NULL,
    
    version_from VARCHAR(32),
    version_to VARCHAR(32),
    
    jar_file_name VARCHAR(256),
    jar_hash VARCHAR(64) COMMENT 'SHA-256 of plugin jar',
    
    performed_by VARCHAR(64) NOT NULL,
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    
    deployment_id INT COMMENT 'Link to deployment if part of larger deployment',
    
    requires_restart BOOLEAN DEFAULT true,
    restart_performed BOOLEAN DEFAULT false,
    restart_at TIMESTAMP NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_name),
    INDEX idx_action (action),
    INDEX idx_performed_at (performed_at),
    INDEX idx_performed_by (performed_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE plugin_installation_history IS 'Complete history of plugin lifecycle events';

-- ============================================================================
-- 8. APPROVAL WORKFLOW (For change requests requiring review)
-- ============================================================================

CREATE TABLE IF NOT EXISTS change_approval_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    
    request_type ENUM('config_change', 'deployment', 'plugin_update', 'rule_change') NOT NULL,
    
    requested_by VARCHAR(64) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    justification TEXT,
    
    risk_level ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    impact_scope VARCHAR(32) COMMENT 'single, server, network',
    
    affected_instances TEXT COMMENT 'JSON array of instance_ids',
    
    approval_status ENUM('pending', 'approved', 'rejected', 'cancelled') DEFAULT 'pending',
    
    approved_by VARCHAR(64),
    approved_at TIMESTAMP NULL,
    approval_notes TEXT,
    
    rejected_by VARCHAR(64),
    rejected_at TIMESTAMP NULL,
    rejection_reason TEXT,
    
    deployment_id INT COMMENT 'Links to deployment if approved and executed',
    
    expires_at TIMESTAMP NULL COMMENT 'Auto-reject if not approved by this time',
    
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    INDEX idx_requested_by (requested_by),
    INDEX idx_status (approval_status),
    INDEX idx_risk_level (risk_level),
    INDEX idx_requested_at (requested_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE change_approval_requests IS 'Workflow for changes requiring approval before deployment';

-- ============================================================================
-- 9. NOTIFICATION LOG (Track all notifications sent)
-- ============================================================================

CREATE TABLE IF NOT EXISTS notification_log (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    
    notification_type ENUM('deployment', 'drift_alert', 'plugin_update', 'approval_request', 'error', 'info') NOT NULL,
    
    recipient VARCHAR(128) NOT NULL COMMENT 'User, email, webhook URL, Discord channel',
    delivery_method ENUM('email', 'webhook', 'discord', 'slack', 'internal') NOT NULL,
    
    subject VARCHAR(255),
    message TEXT,
    
    related_deployment_id INT,
    related_approval_id INT,
    related_change_id INT,
    
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivery_status ENUM('pending', 'sent', 'failed', 'bounced') DEFAULT 'pending',
    delivery_error TEXT,
    
    FOREIGN KEY (related_deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE SET NULL,
    FOREIGN KEY (related_approval_id) REFERENCES change_approval_requests(request_id) ON DELETE SET NULL,
    FOREIGN KEY (related_change_id) REFERENCES config_change_history(change_id) ON DELETE SET NULL,
    INDEX idx_sent_at (sent_at),
    INDEX idx_recipient (recipient),
    INDEX idx_delivery_method (delivery_method),
    INDEX idx_status (delivery_status),
    INDEX idx_type (notification_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE notification_log IS 'Audit trail of all notifications sent by the system';

-- ============================================================================
-- 10. SCHEDULED TASKS (Track automated operations)
-- ============================================================================

CREATE TABLE IF NOT EXISTS scheduled_tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    
    task_name VARCHAR(128) NOT NULL,
    task_type ENUM('drift_check', 'plugin_update_check', 'variance_snapshot', 'backup', 'cleanup', 'custom') NOT NULL,
    
    schedule_expression VARCHAR(64) COMMENT 'Cron expression or interval',
    
    last_run_at TIMESTAMP NULL,
    last_run_status ENUM('success', 'failed', 'partial', 'skipped') DEFAULT 'success',
    last_run_duration_seconds INT,
    last_run_error TEXT,
    
    next_run_at TIMESTAMP NULL,
    
    is_enabled BOOLEAN DEFAULT true,
    
    config_json TEXT COMMENT 'JSON configuration for the task',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    
    UNIQUE KEY unique_task_name (task_name),
    INDEX idx_task_type (task_type),
    INDEX idx_next_run (next_run_at),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE scheduled_tasks IS 'Configuration and status of automated scheduled tasks';

-- ============================================================================
-- 11. SYSTEM HEALTH METRICS (Performance and health tracking)
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_health_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    
    metric_source VARCHAR(32) NOT NULL COMMENT 'web_api, agent, database, external',
    instance_id VARCHAR(16),
    
    metric_type VARCHAR(64) NOT NULL COMMENT 'response_time, memory_usage, plugin_count, drift_count, etc.',
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(16) COMMENT 'ms, MB, count, percent',
    
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    metadata_json TEXT COMMENT 'Additional context',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    INDEX idx_source (metric_source),
    INDEX idx_instance (instance_id),
    INDEX idx_type (metric_type),
    INDEX idx_recorded_at (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

COMMENT ON TABLE system_health_metrics IS 'Time-series metrics for monitoring system health';

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

SELECT 'Tracking & History tables created successfully!' AS status;
SELECT COUNT(*) AS new_tables_created FROM information_schema.tables 
WHERE table_schema = 'asmp_config' 
AND table_name IN (
    'config_key_migrations',
    'config_change_history',
    'deployment_history',
    'deployment_changes',
    'config_rule_history',
    'config_variance_history',
    'plugin_installation_history',
    'change_approval_requests',
    'notification_log',
    'scheduled_tasks',
    'system_health_metrics'
);
