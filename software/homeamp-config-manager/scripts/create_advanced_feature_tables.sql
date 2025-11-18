-- Advanced Feature Management: Tag Dependencies, Conflicts, Feature Inventory
-- Purpose: Add tag dependency/conflict validation and instance feature tracking
-- Author: AI Assistant
-- Date: 2025-01-04
-- Related Todos: #18, #19, #20, #21, #22

-- =============================================================================
-- Table 1: tag_dependencies
-- Define that tag A requires tag B (e.g., "economy" requires "vault")
-- =============================================================================
CREATE TABLE IF NOT EXISTS tag_dependencies (
    dependency_id INT AUTO_INCREMENT PRIMARY KEY,
    dependent_tag_id INT NOT NULL COMMENT 'Tag that has the requirement',
    required_tag_id INT NOT NULL COMMENT 'Tag that must be present',
    dependency_type ENUM('required', 'recommended', 'optional') DEFAULT 'required',
    description TEXT NULL COMMENT 'Why this dependency exists',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (dependent_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (required_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_dependency (dependent_tag_id, required_tag_id),
    INDEX idx_dependent (dependent_tag_id),
    INDEX idx_required (required_tag_id),
    INDEX idx_type (dependency_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tag dependency relationships for validation';

-- =============================================================================
-- Table 2: tag_conflicts
-- Define that tag A conflicts with tag B (e.g., "creative" conflicts with "survival")
-- =============================================================================
CREATE TABLE IF NOT EXISTS tag_conflicts (
    conflict_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_a_id INT NOT NULL,
    tag_b_id INT NOT NULL,
    conflict_severity ENUM('error', 'warning', 'info') DEFAULT 'error',
    description TEXT NULL COMMENT 'Why these tags conflict',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (tag_a_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_b_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_conflict (tag_a_id, tag_b_id),
    INDEX idx_tag_a (tag_a_id),
    INDEX idx_tag_b (tag_b_id),
    INDEX idx_severity (conflict_severity),
    
    -- Ensure symmetric conflict (if A conflicts with B, B conflicts with A)
    CHECK (tag_a_id != tag_b_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Tag conflict definitions for validation';

-- =============================================================================
-- Table 3: instance_feature_inventory
-- Track what features each instance has (economy, permissions, PvP, custom items, etc.)
-- =============================================================================
CREATE TABLE IF NOT EXISTS instance_feature_inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    feature_name VARCHAR(128) NOT NULL COMMENT 'economy, permissions, pvp, custom-items, etc.',
    feature_category ENUM('gameplay', 'economy', 'permissions', 'protection', 'social', 'utility', 'cosmetic', 'admin', 'other') NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    detected_from VARCHAR(256) NULL COMMENT 'Which plugin/config provides this (e.g., Vault)',
    detection_method ENUM('plugin', 'config', 'manual') DEFAULT 'plugin',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_instance_feature (instance_id, feature_name),
    INDEX idx_instance (instance_id),
    INDEX idx_feature (feature_name),
    INDEX idx_category (feature_category),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Feature inventory per instance for capability tracking';

-- =============================================================================
-- Table 4: server_capabilities
-- Track what each server hardware supports (e.g., max RAM, CPU cores, storage)
-- =============================================================================
CREATE TABLE IF NOT EXISTS server_capabilities (
    capability_id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) NOT NULL COMMENT 'hetzner, ovh, etc.',
    capability_type VARCHAR(128) NOT NULL COMMENT 'max_ram_gb, cpu_cores, storage_tb, max_instances, etc.',
    capability_value VARCHAR(256) NOT NULL,
    unit VARCHAR(32) NULL COMMENT 'GB, cores, TB, count, etc.',
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(128) NULL,
    
    UNIQUE KEY unique_server_capability (server_name, capability_type),
    INDEX idx_server (server_name),
    INDEX idx_type (capability_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Server hardware capabilities and limits';

-- =============================================================================
-- Table 5: world_features
-- Track features enabled per-world (e.g., nether has mob_spawning, creative_plots has creative_mode)
-- =============================================================================
CREATE TABLE IF NOT EXISTS world_features (
    world_feature_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    feature_name VARCHAR(128) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    detected_from VARCHAR(256) NULL COMMENT 'Which config/plugin provides this',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_world_feature (instance_id, world_name, feature_name),
    INDEX idx_instance (instance_id),
    INDEX idx_world (world_name),
    INDEX idx_feature (feature_name),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Feature tracking per-world within instances';

-- =============================================================================
-- SAMPLE DATA for tag_dependencies
-- =============================================================================
-- These will be populated by the application based on plugin analysis
-- Examples:
-- INSERT INTO tag_dependencies (dependent_tag_id, required_tag_id, description) 
-- VALUES 
--   ((SELECT tag_id FROM meta_tags WHERE tag_name='economy'), (SELECT tag_id FROM meta_tags WHERE tag_name='vault'), 'Economy plugins require Vault API'),
--   ((SELECT tag_id FROM meta_tags WHERE tag_name='custom-ranks'), (SELECT tag_id FROM meta_tags WHERE tag_name='permissions'), 'Custom ranks require permission system');

-- =============================================================================
-- SAMPLE DATA for tag_conflicts
-- =============================================================================
-- Examples:
-- INSERT INTO tag_conflicts (tag_a_id, tag_b_id, conflict_severity, description)
-- VALUES
--   ((SELECT tag_id FROM meta_tags WHERE tag_name='creative'), (SELECT tag_id FROM meta_tags WHERE tag_name='survival'), 'error', 'Cannot be both creative and survival mode'),
--   ((SELECT tag_id FROM meta_tags WHERE tag_name='pvp-enabled'), (SELECT tag_id FROM meta_tags WHERE tag_name='pvp-disabled'), 'error', 'PvP cannot be both enabled and disabled');

-- =============================================================================
-- DEPLOYMENT INSTRUCTIONS
-- =============================================================================
-- 1. Test on development database first
-- 2. Verify tables created: SHOW TABLES LIKE 'tag_%'; SHOW TABLES LIKE '%feature%';
-- 3. Deploy to Hetzner: mysql -u root -p archivesmp_config < create_advanced_feature_tables.sql
-- 4. Deploy to OVH after Hetzner validation
-- 5. Populate sample tag dependencies and conflicts via API/admin UI
