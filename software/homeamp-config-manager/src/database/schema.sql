-- ArchiveSMP Configuration Database Schema
-- Central source of truth for all plugin configurations
-- Database: asmp_config_controller (SEPARATE from production asmp_SQL)

CREATE DATABASE IF NOT EXISTS asmp_config_controller;
USE asmp_config_controller;

-- Server/Instance Registry
CREATE TABLE IF NOT EXISTS servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(50) NOT NULL UNIQUE,  -- HETZNER, OVH
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_id INT NOT NULL,
    instance_shortname VARCHAR(20) NOT NULL,  -- SMP101, DEV01, etc.
    instance_fullname VARCHAR(100),
    instance_type ENUM('paper', 'velocity', 'geyser', 'ads') NOT NULL,
    paper_version VARCHAR(20),
    java_version VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(id),
    UNIQUE KEY unique_instance (server_id, instance_shortname)
);

-- Plugin Registry
CREATE TABLE IF NOT EXISTS plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(100) NOT NULL UNIQUE,
    platform ENUM('paper', 'velocity', 'geyser', 'universal') NOT NULL,
    current_version VARCHAR(50),
    jar_filename VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configuration Keys (The Heart of the System)
CREATE TABLE IF NOT EXISTS config_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id INT NOT NULL,
    config_filename VARCHAR(100) NOT NULL,  -- config.yml, messages.yml, etc.
    file_type ENUM('yaml', 'json', 'properties', 'toml') NOT NULL,
    key_path TEXT NOT NULL,  -- Full dotted path: shop.currency.default
    whitespace_prefix VARCHAR(50),  -- Indentation/spacing info for YAML reconstruction
    comment_pre TEXT,  -- Comment above this key
    comment_inline TEXT,  -- Inline comment
    plugin_default_value TEXT,  -- Plugin's original default (from docs/JAR)
    observed_value TEXT,  -- Value observed in production (from markdown snapshots)
    data_type ENUM('string', 'int', 'float', 'boolean', 'list', 'dict') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plugin_id) REFERENCES plugins(id),
    UNIQUE KEY unique_key (plugin_id, config_filename, key_path(500))
);

-- Our Network Defaults (What We Want Everywhere - MANUALLY APPROVED ONLY)
CREATE TABLE IF NOT EXISTS network_defaults (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key_id INT NOT NULL,
    our_value TEXT NOT NULL,  -- Our standardized value
    applies_to TEXT,  -- JSON array: ["SMP101", "DEV01"] or "ALL"
    reason TEXT,  -- Why we set this value
    set_by VARCHAR(50),  -- Who made this decision
    approved_at TIMESTAMP,  -- When this was approved as standard
    status ENUM('proposed', 'approved', 'deprecated') DEFAULT 'proposed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (config_key_id) REFERENCES config_keys(id)
);

-- Instance-Specific Overrides (Deviations We Accept)
CREATE TABLE IF NOT EXISTS instance_overrides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id INT NOT NULL,
    config_key_id INT NOT NULL,
    override_value TEXT NOT NULL,
    reason TEXT,  -- Why this instance is different
    approved_by VARCHAR(50),
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(id),
    FOREIGN KEY (config_key_id) REFERENCES config_keys(id),
    UNIQUE KEY unique_override (instance_id, config_key_id)
);

-- Live Instance State (What's Actually Deployed)
CREATE TABLE IF NOT EXISTS instance_config_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id INT NOT NULL,
    config_key_id INT NOT NULL,
    current_value TEXT NOT NULL,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(id),
    FOREIGN KEY (config_key_id) REFERENCES config_keys(id),
    UNIQUE KEY unique_state (instance_id, config_key_id)
);

-- Drift Detection Results (Calculated On-The-Fly)
CREATE TABLE IF NOT EXISTS drift_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id INT NOT NULL,
    config_key_id INT NOT NULL,
    expected_value TEXT NOT NULL,  -- From network_defaults or instance_overrides
    actual_value TEXT NOT NULL,  -- From instance_config_state
    drift_type ENUM('unauthorized_change', 'missing_override', 'value_mismatch') NOT NULL,
    severity ENUM('critical', 'warning', 'info') NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (instance_id) REFERENCES instances(id),
    FOREIGN KEY (config_key_id) REFERENCES config_keys(id),
    INDEX idx_unresolved (instance_id, resolved_at)
);

-- Change History (Audit Trail)
CREATE TABLE IF NOT EXISTS config_changes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id INT NOT NULL,
    config_key_id INT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type ENUM('deployment', 'manual', 'drift_fix', 'rollback') NOT NULL,
    changed_by VARCHAR(50) NOT NULL,
    change_reason TEXT,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(id),
    FOREIGN KEY (config_key_id) REFERENCES config_keys(id)
);

-- Indexes for Performance
CREATE INDEX idx_plugin_name ON plugins(plugin_name);
CREATE INDEX idx_instance_shortname ON instances(instance_shortname);
CREATE INDEX idx_config_key_path ON config_keys(key_path(500));
CREATE INDEX idx_drift_unresolved ON drift_log(resolved_at);
CREATE INDEX idx_last_seen ON instance_config_state(last_seen);
