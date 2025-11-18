-- Migration 003: Create config_rules table
-- Purpose: Store configuration rules at all 7 scope levels
-- Author: AI Assistant
-- Date: 2025-11-18
-- Dependencies: 001_create_meta_tags.sql, existing instances/plugins tables

-- =============================================================================
-- Table: config_rules
-- Universal table for config rules at GLOBAL, SERVER, META_TAG, INSTANCE, WORLD, RANK, PLAYER scopes
-- =============================================================================
CREATE TABLE IF NOT EXISTS config_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Scope definition (only ONE should be set per rule)
    scope_level ENUM('GLOBAL', 'SERVER', 'META_TAG', 'INSTANCE', 'WORLD', 'RANK', 'PLAYER') NOT NULL,
    
    -- Scope identifiers (NULL for non-applicable scopes)
    server_name VARCHAR(64) NULL COMMENT 'hetzner or ovh (for SERVER scope)',
    meta_tag_id INT NULL COMMENT 'FK to meta_tags (for META_TAG scope)',
    instance_id VARCHAR(16) NULL COMMENT 'FK to instances (for INSTANCE, WORLD, RANK, PLAYER scopes)',
    world_name VARCHAR(128) NULL COMMENT 'World folder name (for WORLD scope)',
    rank_name VARCHAR(128) NULL COMMENT 'LuckPerms rank name (for RANK scope)',
    player_uuid CHAR(36) NULL COMMENT 'Player UUID (for PLAYER scope)',
    
    -- Configuration details
    plugin_id VARCHAR(64) NOT NULL COMMENT 'Plugin identifier (e.g., "EssentialsX")',
    config_file VARCHAR(255) NOT NULL COMMENT 'Config file name (e.g., "config.yml")',
    config_key VARCHAR(512) NOT NULL COMMENT 'Dot-notation key path (e.g., "spawn.world")',
    config_value TEXT NOT NULL COMMENT 'JSON-encoded value (supports all types)',
    value_type ENUM('string', 'integer', 'float', 'boolean', 'list', 'dict') DEFAULT 'string',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL COMMENT 'User who created the rule',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    updated_by VARCHAR(128) NULL,
    is_active BOOLEAN DEFAULT TRUE COMMENT 'False = disabled rule (ignored in resolution)',
    priority INT DEFAULT 0 COMMENT 'Tie-breaker within same scope level',
    notes TEXT NULL COMMENT 'Documentation about why this rule exists',
    
    -- Foreign keys
    FOREIGN KEY (meta_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    -- Indexes for fast hierarchy resolution
    INDEX idx_scope_level (scope_level),
    INDEX idx_server (server_name),
    INDEX idx_meta_tag (meta_tag_id),
    INDEX idx_instance (instance_id),
    INDEX idx_world (world_name),
    INDEX idx_rank (rank_name),
    INDEX idx_player (player_uuid),
    INDEX idx_plugin_file_key (plugin_id, config_file, config_key),
    INDEX idx_active (is_active),
    INDEX idx_priority (priority),
    
    -- Composite indexes for common queries
    INDEX idx_global_lookup (scope_level, plugin_id, config_file, config_key),
    INDEX idx_server_lookup (scope_level, server_name, plugin_id, config_file, config_key),
    INDEX idx_tag_lookup (scope_level, meta_tag_id, plugin_id, config_file, config_key),
    INDEX idx_instance_lookup (scope_level, instance_id, plugin_id, config_file, config_key),
    
    -- Constraints: Ensure scope identifiers match scope level
    CONSTRAINT chk_global_scope CHECK (
        (scope_level = 'GLOBAL' AND server_name IS NULL AND meta_tag_id IS NULL AND instance_id IS NULL AND world_name IS NULL AND rank_name IS NULL AND player_uuid IS NULL) OR
        scope_level != 'GLOBAL'
    ),
    CONSTRAINT chk_server_scope CHECK (
        (scope_level = 'SERVER' AND server_name IS NOT NULL AND meta_tag_id IS NULL AND instance_id IS NULL AND world_name IS NULL AND rank_name IS NULL AND player_uuid IS NULL) OR
        scope_level != 'SERVER'
    ),
    CONSTRAINT chk_meta_tag_scope CHECK (
        (scope_level = 'META_TAG' AND meta_tag_id IS NOT NULL AND instance_id IS NULL AND world_name IS NULL AND rank_name IS NULL AND player_uuid IS NULL) OR
        scope_level != 'META_TAG'
    ),
    CONSTRAINT chk_instance_scope CHECK (
        (scope_level = 'INSTANCE' AND instance_id IS NOT NULL AND world_name IS NULL AND rank_name IS NULL AND player_uuid IS NULL) OR
        scope_level != 'INSTANCE'
    ),
    CONSTRAINT chk_world_scope CHECK (
        (scope_level = 'WORLD' AND instance_id IS NOT NULL AND world_name IS NOT NULL AND rank_name IS NULL AND player_uuid IS NULL) OR
        scope_level != 'WORLD'
    ),
    CONSTRAINT chk_rank_scope CHECK (
        (scope_level = 'RANK' AND instance_id IS NOT NULL AND rank_name IS NOT NULL AND player_uuid IS NULL) OR
        scope_level != 'RANK'
    ),
    CONSTRAINT chk_player_scope CHECK (
        (scope_level = 'PLAYER' AND instance_id IS NOT NULL AND player_uuid IS NOT NULL) OR
        scope_level != 'PLAYER'
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Configuration rules at all 7 scope levels with priority-based resolution';

-- =============================================================================
-- Sample data (for testing hierarchy resolution)
-- =============================================================================
-- GLOBAL: Default spawn protection radius
INSERT INTO config_rules (scope_level, plugin_id, config_file, config_key, config_value, value_type, created_by, notes) VALUES
    ('GLOBAL', 'minecraft', 'server.properties', 'spawn-protection', '16', 'integer', 'system', 'Default spawn protection radius')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);

-- SERVER: Hetzner-specific setting
-- INSERT INTO config_rules (scope_level, server_name, plugin_id, config_file, config_key, config_value, value_type, created_by) VALUES
--     ('SERVER', 'hetzner', 'minecraft', 'server.properties', 'max-players', '100', 'integer', 'system');

-- =============================================================================
-- Verification queries
-- =============================================================================
-- Count rules by scope level:
-- SELECT scope_level, COUNT(*) as count FROM config_rules GROUP BY scope_level ORDER BY scope_level;

-- View hierarchy for a specific config key:
-- SELECT scope_level, server_name, meta_tag_id, instance_id, world_name, rank_name, player_uuid, config_value
-- FROM config_rules
-- WHERE plugin_id = 'minecraft' AND config_file = 'server.properties' AND config_key = 'spawn-protection'
-- ORDER BY FIELD(scope_level, 'GLOBAL', 'SERVER', 'META_TAG', 'INSTANCE', 'WORLD', 'RANK', 'PLAYER');
