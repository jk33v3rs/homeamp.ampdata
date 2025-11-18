-- Multi-Level Scope System: World, Rank, Player Meta-Tagging
-- Purpose: Extend meta-tag system to support 7 scope levels (GLOBAL, SERVER, META_TAG, INSTANCE, WORLD, RANK, PLAYER)
-- Author: AI Assistant
-- Date: 2025-01-04
-- Related Todos: #11, #12, #13, #14, #15, #16, #17

-- =============================================================================
-- Table 1: world_meta_tags
-- Assign meta-tags to specific worlds (e.g., "world", "world_nether", "creative_plots")
-- =============================================================================
CREATE TABLE IF NOT EXISTS world_meta_tags (
    world_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL COMMENT 'Folder name under instance (e.g., world, world_nether, world_the_end)',
    meta_tag_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128) NULL COMMENT 'User or system',
    auto_assigned BOOLEAN DEFAULT FALSE COMMENT 'True if auto-tagged by agent',
    confidence_score DECIMAL(3,2) NULL COMMENT 'ML confidence for auto-tags (0.00-1.00)',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (meta_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_world_tag (instance_id, world_name, meta_tag_id),
    INDEX idx_instance (instance_id),
    INDEX idx_world (world_name),
    INDEX idx_tag (meta_tag_id),
    INDEX idx_auto_assigned (auto_assigned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Meta-tags assigned to specific worlds within instances';

-- =============================================================================
-- Table 2: rank_meta_tags  
-- Assign meta-tags to LuckPerms ranks/groups (e.g., "default", "vip", "moderator", "admin")
-- =============================================================================
CREATE TABLE IF NOT EXISTS rank_meta_tags (
    rank_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NULL COMMENT 'NULL = server-wide rank across all instances',
    server_name VARCHAR(64) NULL COMMENT 'hetzner or ovh - for server-wide ranks',
    rank_name VARCHAR(128) NOT NULL COMMENT 'LuckPerms group name',
    meta_tag_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128) NULL,
    rank_priority INT NULL COMMENT 'LuckPerms weight/priority for sorting',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (meta_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_rank_tag (instance_id, server_name, rank_name, meta_tag_id),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_rank (rank_name),
    INDEX idx_tag (meta_tag_id),
    INDEX idx_priority (rank_priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Meta-tags assigned to permission ranks/groups';

-- =============================================================================
-- Table 3: player_meta_tags
-- Assign meta-tags to individual players (e.g., "builder", "tester", "trusted")
-- =============================================================================
CREATE TABLE IF NOT EXISTS player_meta_tags (
    player_tag_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid VARCHAR(36) NOT NULL COMMENT 'Minecraft player UUID',
    player_name VARCHAR(16) NULL COMMENT 'Current username (may change)',
    instance_id VARCHAR(16) NULL COMMENT 'NULL = applies across all instances',
    server_name VARCHAR(64) NULL COMMENT 'NULL = applies across all servers',
    meta_tag_id INT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128) NULL,
    expires_at TIMESTAMP NULL COMMENT 'NULL = never expires',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (meta_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_player_tag (player_uuid, instance_id, server_name, meta_tag_id),
    INDEX idx_player_uuid (player_uuid),
    INDEX idx_player_name (player_name),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_tag (meta_tag_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Meta-tags assigned to individual players';

-- =============================================================================
-- ALTER: Extend config_rules scope_type to support 7 levels
-- =============================================================================
ALTER TABLE config_rules 
MODIFY COLUMN scope_type ENUM('GLOBAL', 'SERVER', 'META_TAG', 'INSTANCE', 'WORLD', 'RANK', 'PLAYER') NOT NULL
COMMENT 'Hierarchy level where rule applies (GLOBAL highest, PLAYER lowest priority)';

-- Add indexes for new scope types
ALTER TABLE config_rules 
ADD INDEX idx_scope_type (scope_type),
ADD INDEX idx_scope_world (scope_type, scope_identifier(128)),
ADD INDEX idx_scope_rank (scope_type, scope_identifier(128)),
ADD INDEX idx_scope_player (scope_type, scope_identifier(128));

-- =============================================================================
-- Table 4: world_config_rules
-- Per-world config overrides (e.g., world_nether has different spawn protection)
-- =============================================================================
CREATE TABLE IF NOT EXISTS world_config_rules (
    world_rule_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_key VARCHAR(512) NOT NULL COMMENT 'Dot-notation path (e.g., spawn.protection.radius)',
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object', 'null') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_world_config (instance_id, world_name, plugin_id, config_key),
    INDEX idx_instance (instance_id),
    INDEX idx_world (world_name),
    INDEX idx_plugin (plugin_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='World-specific config overrides';

-- =============================================================================
-- Table 5: rank_config_rules
-- Per-rank config overrides (e.g., VIPs have different economy starting balance)
-- =============================================================================
CREATE TABLE IF NOT EXISTS rank_config_rules (
    rank_rule_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NULL COMMENT 'NULL = applies to all instances with this rank',
    server_name VARCHAR(64) NULL COMMENT 'NULL = applies to all servers',
    rank_name VARCHAR(128) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object', 'null') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_rank_config (instance_id, server_name, rank_name, plugin_id, config_key),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_rank (rank_name),
    INDEX idx_plugin (plugin_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Rank-specific config overrides';

-- =============================================================================
-- Table 6: player_config_overrides
-- Per-player config overrides (e.g., specific player has custom spawn location)
-- =============================================================================
CREATE TABLE IF NOT EXISTS player_config_overrides (
    player_override_id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid VARCHAR(36) NOT NULL,
    player_name VARCHAR(16) NULL,
    instance_id VARCHAR(16) NULL COMMENT 'NULL = applies across all instances',
    server_name VARCHAR(64) NULL COMMENT 'NULL = applies across all servers',
    plugin_id VARCHAR(128) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object', 'null') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL,
    expires_at TIMESTAMP NULL COMMENT 'NULL = never expires',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_player_override (player_uuid, instance_id, server_name, plugin_id, config_key),
    INDEX idx_player_uuid (player_uuid),
    INDEX idx_player_name (player_name),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_plugin (plugin_id),
    INDEX idx_active (is_active),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Player-specific config overrides';

-- =============================================================================
-- DEPLOYMENT INSTRUCTIONS
-- =============================================================================
-- 1. Test on development database first
-- 2. Verify tables created: SHOW TABLES LIKE '%meta_tags'; SHOW TABLES LIKE '%config_rules%';
-- 3. Check config_rules ENUM: SHOW COLUMNS FROM config_rules LIKE 'scope_type';
-- 4. Deploy to Hetzner: mysql -u root -p archivesmp_config < create_multi_level_scope_tables.sql
-- 5. Deploy to OVH after Hetzner validation
-- 6. Update API and agent code to use new scope levels
