-- Migration 001: Create meta_tags table
-- Purpose: Core meta-tagging system for grouping instances
-- Author: AI Assistant
-- Date: 2025-11-18
-- Related: 7-level hierarchy system (GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER)

-- =============================================================================
-- Table: meta_tags
-- Store reusable tags for grouping instances (e.g., "survival-servers", "creative-servers", "modded")
-- =============================================================================
CREATE TABLE IF NOT EXISTS meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(64) NOT NULL UNIQUE COMMENT 'Unique tag identifier (e.g., "survival-servers")',
    tag_description TEXT NULL COMMENT 'Human-readable description of tag purpose',
    tag_color VARCHAR(7) NULL COMMENT 'Hex color for UI display (e.g., "#00d4ff")',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL COMMENT 'User who created the tag',
    is_system_tag BOOLEAN DEFAULT FALSE COMMENT 'True if created by system (not deletable)',
    priority INT DEFAULT 100 COMMENT 'Priority for conflict resolution (higher = higher priority)',
    
    INDEX idx_tag_name (tag_name),
    INDEX idx_system_tag (is_system_tag),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Reusable tags for grouping and organizing instances';

-- =============================================================================
-- Initial system tags (common use cases)
-- =============================================================================
INSERT INTO meta_tags (tag_name, tag_description, tag_color, is_system_tag, priority) VALUES
    ('survival', 'Standard survival game mode servers', '#10b981', TRUE, 100),
    ('creative', 'Creative mode servers', '#f59e0b', TRUE, 100),
    ('skyblock', 'Skyblock-themed servers', '#06b6d4', TRUE, 100),
    ('modded', 'Servers with mods/datapacks', '#8b5cf6', TRUE, 100),
    ('minigames', 'Minigame servers', '#ec4899', TRUE, 100),
    ('public', 'Public-facing servers', '#3b82f6', TRUE, 150),
    ('private', 'Private/testing servers', '#64748b', TRUE, 150),
    ('production', 'Production servers (live)', '#ef4444', TRUE, 200),
    ('staging', 'Staging/testing environment', '#f59e0b', TRUE, 150),
    ('development', 'Development servers', '#06b6d4', TRUE, 100)
ON DUPLICATE KEY UPDATE tag_description = VALUES(tag_description);

-- =============================================================================
-- Verification query
-- =============================================================================
-- SELECT COUNT(*) as meta_tags_count FROM meta_tags;
-- Expected: At least 10 system tags
