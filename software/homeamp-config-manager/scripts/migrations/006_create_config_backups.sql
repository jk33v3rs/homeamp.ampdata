-- Migration 006: Create config_backups table
-- Purpose: Track all configuration file backups with hash verification
-- Author: AI Assistant
-- Date: 2025-11-18
-- Dependencies: existing config_files table

-- =============================================================================
-- Table: config_backups
-- Store backup history for all config files with integrity verification
-- =============================================================================
CREATE TABLE IF NOT EXISTS config_backups (
    backup_id INT AUTO_INCREMENT PRIMARY KEY,
    config_file_id INT NOT NULL COMMENT 'FK to config_files table',
    
    -- Backup metadata
    backup_reason ENUM('manual', 'auto_before_modify', 'scheduled', 'drift_detected', 'deployment') DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(128) NULL COMMENT 'User or system that created backup',
    
    -- File integrity
    file_hash VARCHAR(64) NOT NULL COMMENT 'SHA-256 hash of backed-up content',
    file_size INT NOT NULL COMMENT 'File size in bytes',
    
    -- Backup storage
    backup_path VARCHAR(512) NOT NULL COMMENT 'Full path to backup file on disk',
    compressed BOOLEAN DEFAULT FALSE COMMENT 'True if backup is gzip compressed',
    
    -- Restoration tracking
    restored_at TIMESTAMP NULL COMMENT 'When this backup was restored (NULL = never)',
    restored_by VARCHAR(128) NULL COMMENT 'User who restored this backup',
    restore_successful BOOLEAN NULL COMMENT 'True if restore succeeded, False if failed, NULL if never restored',
    
    -- Retention policy
    expires_at TIMESTAMP NULL COMMENT 'When backup is eligible for deletion (NULL = keep forever)',
    is_retained BOOLEAN DEFAULT TRUE COMMENT 'False = marked for deletion',
    retention_reason VARCHAR(255) NULL COMMENT 'Why this backup is retained (e.g., "pre-deployment snapshot")',
    
    FOREIGN KEY (config_file_id) REFERENCES config_files(config_file_id) ON DELETE CASCADE,
    
    INDEX idx_config_file (config_file_id),
    INDEX idx_created_at (created_at DESC),
    INDEX idx_backup_reason (backup_reason),
    INDEX idx_file_hash (file_hash),
    INDEX idx_expires_at (expires_at),
    INDEX idx_retained (is_retained),
    INDEX idx_restored (restored_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Configuration file backup history with integrity verification';

-- =============================================================================
-- Retention policy: Auto-expire old backups (configurable)
-- =============================================================================
-- Default: Keep manual backups for 90 days, auto backups for 30 days
-- This would be run by a scheduled job

-- Mark expired backups:
-- UPDATE config_backups 
-- SET is_retained = FALSE
-- WHERE backup_reason = 'auto_before_modify' 
--   AND created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
--   AND is_retained = TRUE;

-- DELETE old backups (after marking):
-- DELETE FROM config_backups 
-- WHERE is_retained = FALSE 
--   AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);  -- Grace period

-- =============================================================================
-- Verification queries
-- =============================================================================
-- Backup count by reason:
-- SELECT backup_reason, COUNT(*) as count, 
--        ROUND(SUM(file_size)/1024/1024, 2) as total_mb
-- FROM config_backups
-- WHERE is_retained = TRUE
-- GROUP BY backup_reason;

-- Recent backups:
-- SELECT cf.plugin_id, cf.file_path, cb.backup_reason, cb.created_at, cb.file_size
-- FROM config_backups cb
-- JOIN config_files cf ON cb.config_file_id = cf.config_file_id
-- ORDER BY cb.created_at DESC
-- LIMIT 20;

-- Backups eligible for cleanup:
-- SELECT COUNT(*) as expired_backups, 
--        ROUND(SUM(file_size)/1024/1024, 2) as total_mb
-- FROM config_backups
-- WHERE expires_at < NOW() AND is_retained = TRUE;
