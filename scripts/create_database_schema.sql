-- ============================================================================
-- Complete Database Schema for Multi-Instance Config Management
-- Version: 1.0
-- Database: asmp_config (NEW)
-- Target: MariaDB 135.181.212.169:3369
-- User: sqlworkerSMP / 2024!SQLdb
-- ============================================================================

-- Connect to existing database first, then create new one
-- USE asmp_SQL;

-- Create new database for config management
CREATE DATABASE IF NOT EXISTS asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asmp_config;

-- ============================================================================
-- CORE INFRASTRUCTURE
-- ============================================================================

-- 1. Instances (Physical Deployments)
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
) ENGINE=InnoDB;

CREATE INDEX idx_instances_server ON instances(server_name);
CREATE INDEX idx_instances_active ON instances(is_active, is_production);

-- 2. Meta Tag Categories
CREATE TABLE meta_tag_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true
) ENGINE=InnoDB;

-- 3. Meta Tags
CREATE TABLE meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(64) NOT NULL UNIQUE,
    category_id INT,
    
    display_name VARCHAR(128),
    color_code VARCHAR(16),
    icon VARCHAR(64),
    
    description TEXT,
    is_system_tag BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES meta_tag_categories(category_id)
) ENGINE=InnoDB;

CREATE INDEX idx_tags_category ON meta_tags(category_id);
CREATE INDEX idx_tags_active ON meta_tags(is_active);

-- ============================================================================
-- META-GROUPING (Instance/World/Region Groups)
-- ============================================================================

-- 4. Instance Groups (Meta-Server Clustering)
CREATE TABLE instance_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    group_type VARCHAR(32),
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. Instance Group Members
CREATE TABLE instance_group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    group_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    assignment_note TEXT,
    
    UNIQUE KEY unique_instance_group (instance_id, group_id),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES instance_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_instance_group_members_instance ON instance_group_members(instance_id);
CREATE INDEX idx_instance_group_members_group ON instance_group_members(group_id);

-- 6. World Groups (Meta-World Clustering)
CREATE TABLE world_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 7. Region Groups (Meta-Region Clustering)
CREATE TABLE region_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(64) UNIQUE NOT NULL,
    description TEXT,
    color_code VARCHAR(16),
    is_system_group BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================================
-- TAGGING ASSIGNMENTS
-- ============================================================================

-- 8. Instance Tags
CREATE TABLE instance_tags (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    tag_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    assignment_note TEXT,
    
    UNIQUE KEY unique_instance_tag (instance_id, tag_id),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_instance_tags_instance ON instance_tags(instance_id);
CREATE INDEX idx_instance_tags_tag ON instance_tags(tag_id);

-- ============================================================================
-- MULTI-WORLD/REGION SUPPORT
-- ============================================================================

-- 9. Worlds
CREATE TABLE worlds (
    world_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    
    world_name VARCHAR(128) NOT NULL,
    world_type VARCHAR(32),
    
    seed BIGINT,
    generator VARCHAR(64),
    difficulty VARCHAR(16),
    
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_instance_world (instance_id, world_name),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_worlds_instance ON worlds(instance_id);
CREATE INDEX idx_worlds_primary ON worlds(is_primary);

-- 10. World Tags
CREATE TABLE world_tags (
    world_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    world_id INT,
    tag_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_world_tag (world_id, tag_id),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_world_tags_world ON world_tags(world_id);
CREATE INDEX idx_world_tags_tag ON world_tags(tag_id);

-- 11. World Group Members
CREATE TABLE world_group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    world_id INT,
    group_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_world_group (world_id, group_id),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES world_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_world_group_members_world ON world_group_members(world_id);
CREATE INDEX idx_world_group_members_group ON world_group_members(group_id);

-- 12. Regions
CREATE TABLE regions (
    region_id INT AUTO_INCREMENT PRIMARY KEY,
    world_id INT,
    
    region_name VARCHAR(128) NOT NULL,
    region_type VARCHAR(32),
    
    min_x INT,
    min_y INT,
    min_z INT,
    max_x INT,
    max_y INT,
    max_z INT,
    
    parent_region_id INT,
    priority INT DEFAULT 0,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_world_region (world_id, region_name),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    FOREIGN KEY (parent_region_id) REFERENCES regions(region_id)
) ENGINE=InnoDB;

CREATE INDEX idx_regions_world ON regions(world_id);
CREATE INDEX idx_regions_type ON regions(region_type);
CREATE INDEX idx_regions_parent ON regions(parent_region_id);

-- 13. Region Tags
CREATE TABLE region_tags (
    region_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    tag_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_region_tag (region_id, tag_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_region_tags_region ON region_tags(region_id);
CREATE INDEX idx_region_tags_tag ON region_tags(tag_id);

-- 14. Region Group Members
CREATE TABLE region_group_members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    region_id INT,
    group_id INT,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    
    UNIQUE KEY unique_region_group (region_id, group_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES region_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE INDEX idx_region_group_members_region ON region_group_members(region_id);
CREATE INDEX idx_region_group_members_group ON region_group_members(group_id);

-- ============================================================================
-- CONFIGURATION SYSTEM
-- ============================================================================

-- 15. Configuration Rules
CREATE TABLE config_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    config_file VARCHAR(256),
    
    scope_type VARCHAR(16) NOT NULL,
    scope_selector VARCHAR(128),
    
    tag_logic_type VARCHAR(16) DEFAULT 'AND',
    tag_logic_expression TEXT,
    
    world_filter VARCHAR(128),
    region_filter VARCHAR(128),
    
    config_value TEXT,
    value_type VARCHAR(16),
    
    priority INT NOT NULL,
    
    is_expected_variance BOOLEAN DEFAULT true,
    validation_regex VARCHAR(256),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_modified_by VARCHAR(64),
    is_active BOOLEAN DEFAULT true,
    notes TEXT
) ENGINE=InnoDB;

CREATE INDEX idx_config_rules_plugin ON config_rules(plugin_name);
CREATE INDEX idx_config_rules_key ON config_rules(config_key);
CREATE INDEX idx_config_rules_scope ON config_rules(scope_type, scope_selector);
CREATE INDEX idx_config_rules_priority ON config_rules(priority);
CREATE INDEX idx_config_rules_active ON config_rules(is_active);
CREATE INDEX idx_config_rules_lookup ON config_rules(plugin_name, config_key, is_active, priority);

-- Trigger to auto-calculate priority
DELIMITER //
CREATE TRIGGER config_rule_priority_trigger
BEFORE INSERT ON config_rules
FOR EACH ROW
BEGIN
    SET NEW.priority = CASE NEW.scope_type
        WHEN 'PLAYER_OVERRIDE' THEN 0
        WHEN 'REGION' THEN 1
        WHEN 'REGION_GROUP' THEN 2
        WHEN 'WORLD' THEN 3
        WHEN 'WORLD_GROUP' THEN 4
        WHEN 'INSTANCE' THEN 5
        WHEN 'INSTANCE_GROUP' THEN 6
        WHEN 'META_TAG' THEN 7
        WHEN 'SERVER' THEN 8
        WHEN 'GLOBAL' THEN 9
        ELSE 999
    END;
END//
DELIMITER ;

-- 16. Configuration Variables
CREATE TABLE config_variables (
    variable_id INT AUTO_INCREMENT PRIMARY KEY,
    
    scope_type VARCHAR(16) NOT NULL,
    scope_selector VARCHAR(128),
    
    variable_name VARCHAR(64) NOT NULL,
    variable_value TEXT,
    
    is_system_variable BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_var_scope (scope_type, scope_selector, variable_name)
) ENGINE=InnoDB;

CREATE INDEX idx_config_vars_scope ON config_variables(scope_type, scope_selector);
CREATE INDEX idx_config_vars_name ON config_variables(variable_name);

-- 17. Variance Cache
CREATE TABLE config_variance_cache (
    cache_id INT AUTO_INCREMENT PRIMARY KEY,
    
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    
    total_instances INT,
    unique_values INT,
    variance_type VARCHAR(16),
    
    is_expected_variance BOOLEAN DEFAULT true,
    variance_reason TEXT,
    
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_variance (plugin_name, config_key)
) ENGINE=InnoDB;

CREATE INDEX idx_variance_cache_plugin ON config_variance_cache(plugin_name);
CREATE INDEX idx_variance_cache_type ON config_variance_cache(variance_type);
CREATE INDEX idx_variance_cache_drift ON config_variance_cache(is_expected_variance);

-- ============================================================================
-- PLAYER PROGRESSION
-- ============================================================================

-- 18. Rank Definitions
CREATE TABLE rank_definitions (
    rank_id INT PRIMARY KEY,
    rank_type VARCHAR(16) NOT NULL,
    rank_name VARCHAR(32) NOT NULL,
    rank_order INT NOT NULL,
    
    display_color VARCHAR(16),
    chat_prefix TEXT,
    tab_prefix TEXT,
    luckperms_group VARCHAR(64),
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 19. Player Ranks
CREATE TABLE player_ranks (
    player_uuid CHAR(36) PRIMARY KEY,
    current_rank_id INT,
    current_prestige_id INT,
    
    total_playtime_seconds BIGINT DEFAULT 0,
    total_quest_completions INT DEFAULT 0,
    total_mob_kills INT DEFAULT 0,
    rank_progress_percent DECIMAL(5,2) DEFAULT 0.00,
    
    last_rank_up TIMESTAMP NULL,
    last_prestige TIMESTAMP NULL,
    first_join TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (current_rank_id) REFERENCES rank_definitions(rank_id),
    FOREIGN KEY (current_prestige_id) REFERENCES rank_definitions(rank_id)
) ENGINE=InnoDB;

CREATE INDEX idx_player_ranks_rank ON player_ranks(current_rank_id);
CREATE INDEX idx_player_ranks_prestige ON player_ranks(current_prestige_id);

-- ============================================================================
-- PLAYER CLASSIFICATION
-- ============================================================================

-- 20. Player Role Categories
CREATE TABLE player_role_categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    display_order INT DEFAULT 0,
    is_system_category BOOLEAN DEFAULT true
) ENGINE=InnoDB;

-- 21. Player Roles
CREATE TABLE player_roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(64) NOT NULL UNIQUE,
    category_id INT,
    
    display_name VARCHAR(128),
    color_code VARCHAR(16),
    chat_prefix TEXT,
    tab_prefix TEXT,
    permission_weight INT DEFAULT 0,
    
    luckperms_group VARCHAR(64),
    is_donor_role BOOLEAN DEFAULT false,
    is_staff_role BOOLEAN DEFAULT false,
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES player_role_categories(category_id)
) ENGINE=InnoDB;

CREATE INDEX idx_player_roles_category ON player_roles(category_id);
CREATE INDEX idx_player_roles_donor ON player_roles(is_donor_role);
CREATE INDEX idx_player_roles_staff ON player_roles(is_staff_role);

-- 22. Player Role Assignments
CREATE TABLE player_role_assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36),
    role_id INT,
    
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',
    scope_selector VARCHAR(128),
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(64),
    expires_at TIMESTAMP NULL,
    
    subscription_id VARCHAR(128),
    last_payment_date TIMESTAMP NULL,
    
    is_active BOOLEAN DEFAULT true,
    notes TEXT,
    
    FOREIGN KEY (role_id) REFERENCES player_roles(role_id)
) ENGINE=InnoDB;

CREATE INDEX idx_player_role_assign_player ON player_role_assignments(player_uuid);
CREATE INDEX idx_player_role_assign_role ON player_role_assignments(role_id);
CREATE INDEX idx_player_role_assign_scope ON player_role_assignments(scope_type, scope_selector);
CREATE INDEX idx_player_role_assign_active ON player_role_assignments(is_active);
CREATE INDEX idx_player_role_assign_expires ON player_role_assignments(expires_at);

-- 23. Player Config Overrides
CREATE TABLE player_config_overrides (
    override_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36),
    
    plugin_name VARCHAR(64) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    config_value TEXT,
    
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',
    scope_selector VARCHAR(128),
    
    world_filter VARCHAR(128),
    region_filter VARCHAR(128),
    
    reason TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT true
) ENGINE=InnoDB;

CREATE INDEX idx_player_overrides_player ON player_config_overrides(player_uuid);
CREATE INDEX idx_player_overrides_plugin ON player_config_overrides(plugin_name);
CREATE INDEX idx_player_overrides_key ON player_config_overrides(config_key);
CREATE INDEX idx_player_overrides_scope ON player_config_overrides(scope_type, scope_selector);
CREATE INDEX idx_player_overrides_active ON player_config_overrides(is_active);

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================

SELECT 'Database schema created successfully!' AS status;
SELECT COUNT(*) AS total_tables FROM information_schema.tables WHERE table_schema = 'asmp_config';
