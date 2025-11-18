-- Migration 005: Create ranks table
-- Purpose: Track LuckPerms ranks/groups across instances
-- Author: AI Assistant
-- Date: 2025-11-18
-- Dependencies: existing instances table

-- =============================================================================
-- Table: ranks
-- Track all LuckPerms ranks/groups discovered in instances
-- =============================================================================
CREATE TABLE IF NOT EXISTS ranks (
    rank_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NULL COMMENT 'FK to instances (NULL = server-wide rank)',
    server_name VARCHAR(64) NULL COMMENT 'hetzner or ovh (for server-wide ranks)',
    rank_name VARCHAR(128) NOT NULL COMMENT 'LuckPerms group name (e.g., "default", "vip", "admin")',
    
    -- Rank properties (from LuckPerms config)
    priority INT DEFAULT 0 COMMENT 'LuckPerms weight/priority (higher = more permissions)',
    display_name VARCHAR(128) NULL COMMENT 'Human-readable display name',
    prefix VARCHAR(64) NULL COMMENT 'Chat prefix (e.g., "[VIP]")',
    suffix VARCHAR(64) NULL COMMENT 'Chat suffix',
    color_code VARCHAR(16) NULL COMMENT 'Color code for rank (e.g., "&6" for gold)',
    
    -- Permissions summary
    permission_count INT DEFAULT 0 COMMENT 'Total permissions granted by this rank',
    inherits_from TEXT NULL COMMENT 'JSON array of parent ranks',
    
    -- Discovery metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE COMMENT 'False if rank no longer exists in LuckPerms',
    
    -- Player tracking
    player_count INT DEFAULT 0 COMMENT 'Number of players with this rank (updated periodically)',
    is_default BOOLEAN DEFAULT FALSE COMMENT 'True if this is the default rank for new players',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_instance_rank (instance_id, server_name, rank_name),
    INDEX idx_instance (instance_id),
    INDEX idx_server (server_name),
    INDEX idx_rank_name (rank_name),
    INDEX idx_priority (priority DESC),
    INDEX idx_active (is_active),
    INDEX idx_default (is_default)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='LuckPerms ranks/groups across instances with priority and metadata';

-- =============================================================================
-- Common ranks seed data (typical LuckPerms setup)
-- =============================================================================
-- These would typically be discovered automatically, but we can seed common ones
INSERT INTO ranks (server_name, rank_name, priority, display_name, is_default) VALUES
    ('hetzner', 'default', 0, 'Player', TRUE),
    ('hetzner', 'vip', 50, 'VIP', FALSE),
    ('hetzner', 'vip+', 75, 'VIP+', FALSE),
    ('hetzner', 'mvp', 100, 'MVP', FALSE),
    ('hetzner', 'helper', 200, 'Helper', FALSE),
    ('hetzner', 'moderator', 300, 'Moderator', FALSE),
    ('hetzner', 'admin', 500, 'Admin', FALSE),
    ('hetzner', 'owner', 1000, 'Owner', FALSE)
ON DUPLICATE KEY UPDATE 
    priority = VALUES(priority),
    display_name = VALUES(display_name);

-- =============================================================================
-- Verification queries
-- =============================================================================
-- Ranks by priority:
-- SELECT rank_name, priority, display_name, player_count
-- FROM ranks
-- WHERE is_active = TRUE
-- ORDER BY priority DESC;

-- Ranks per instance:
-- SELECT i.instance_name, COUNT(r.rank_id) as rank_count
-- FROM instances i
-- LEFT JOIN ranks r ON i.instance_id = r.instance_id AND r.is_active = TRUE
-- GROUP BY i.instance_id, i.instance_name
-- ORDER BY rank_count DESC;
