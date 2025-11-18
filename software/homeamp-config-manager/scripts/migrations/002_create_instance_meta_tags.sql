-- Migration 002: Create instance_meta_tags junction table
-- Purpose: Many-to-many relationship between instances and meta tags
-- Author: AI Assistant
-- Date: 2025-11-18
-- Dependencies: 001_create_meta_tags.sql, existing instances table

-- =============================================================================
-- Table: instance_meta_tags
-- Junction table for assigning tags to instances
-- =============================================================================
CREATE TABLE IF NOT EXISTS instance_meta_tags (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL COMMENT 'FK to instances table',
    tag_id INT NOT NULL COMMENT 'FK to meta_tags table',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by VARCHAR(128) NULL COMMENT 'User or system that assigned the tag',
    auto_assigned BOOLEAN DEFAULT FALSE COMMENT 'True if auto-tagged by agent/ML',
    confidence_score DECIMAL(4,3) NULL COMMENT 'ML confidence for auto-tags (0.000-1.000)',
    notes TEXT NULL COMMENT 'Optional notes about why this tag was assigned',
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_instance_tag (instance_id, tag_id),
    INDEX idx_instance (instance_id),
    INDEX idx_tag (tag_id),
    INDEX idx_auto_assigned (auto_assigned),
    INDEX idx_assigned_at (assigned_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Many-to-many relationship between instances and meta tags';

-- =============================================================================
-- Sample assignments (comment out in production, seed separately)
-- =============================================================================
-- Example: Tag all instances with 'production' tag initially
-- INSERT INTO instance_meta_tags (instance_id, tag_id, assigned_by, auto_assigned)
-- SELECT i.instance_id, mt.tag_id, 'system', TRUE
-- FROM instances i
-- CROSS JOIN meta_tags mt
-- WHERE mt.tag_name = 'production'
-- ON DUPLICATE KEY UPDATE assigned_at = CURRENT_TIMESTAMP;

-- =============================================================================
-- Verification query
-- =============================================================================
-- SELECT i.instance_name, GROUP_CONCAT(mt.tag_name) as tags
-- FROM instances i
-- LEFT JOIN instance_meta_tags imt ON i.instance_id = imt.instance_id
-- LEFT JOIN meta_tags mt ON imt.tag_id = mt.tag_id
-- GROUP BY i.instance_id, i.instance_name
-- ORDER BY i.instance_name;
