-- Migration 004: Create worlds table
-- Purpose: Track all discovered worlds across instances
-- Author: AI Assistant
-- Date: 2025-11-18
-- Dependencies: existing instances table

-- =============================================================================
-- Table: worlds
-- Track all Minecraft worlds discovered in instances (world, world_nether, world_the_end, custom worlds)
-- =============================================================================
CREATE TABLE IF NOT EXISTS worlds (
    world_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL COMMENT 'FK to instances table',
    world_name VARCHAR(128) NOT NULL COMMENT 'Folder name (e.g., "world", "world_nether", "creative_plots")',
    world_type ENUM('normal', 'nether', 'end', 'custom') DEFAULT 'custom',
    
    -- World properties
    seed VARCHAR(64) NULL COMMENT 'World seed if available',
    generator VARCHAR(128) NULL COMMENT 'World generator (e.g., "VoidGen", "Terra")',
    environment VARCHAR(32) NULL COMMENT 'normal, nether, the_end (from Bukkit API)',
    
    -- Discovery metadata
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE COMMENT 'False if world folder no longer exists',
    
    -- Size tracking
    folder_size_bytes BIGINT NULL COMMENT 'Total world folder size in bytes',
    region_count INT NULL COMMENT 'Number of region files (.mca)',
    last_modified TIMESTAMP NULL COMMENT 'Most recent file modification in world folder',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_instance_world (instance_id, world_name),
    INDEX idx_instance (instance_id),
    INDEX idx_world_type (world_type),
    INDEX idx_active (is_active),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='All discovered Minecraft worlds across instances';

-- =============================================================================
-- Auto-discovery: Insert standard worlds for all instances
-- =============================================================================
-- This would typically be run by the world_discovery module
-- INSERT INTO worlds (instance_id, world_name, world_type, discovered_at)
-- SELECT instance_id, 'world', 'normal', NOW()
-- FROM instances
-- WHERE NOT EXISTS (
--     SELECT 1 FROM worlds w WHERE w.instance_id = instances.instance_id AND w.world_name = 'world'
-- );

-- =============================================================================
-- Verification queries
-- =============================================================================
-- Count worlds by type:
-- SELECT world_type, COUNT(*) as count FROM worlds GROUP BY world_type;

-- Worlds per instance:
-- SELECT i.instance_name, COUNT(w.world_id) as world_count
-- FROM instances i
-- LEFT JOIN worlds w ON i.instance_id = w.instance_id AND w.is_active = TRUE
-- GROUP BY i.instance_id, i.instance_name
-- ORDER BY world_count DESC;
