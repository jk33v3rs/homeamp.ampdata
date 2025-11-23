-- Add Missing Columns to Plugin and Datapack Tracking Tables
-- Purpose: Add file_path, file_hash, file_size, etc. to instance_plugins and instance_datapacks
-- Date: 2025-11-23
-- Fixes: Agent errors "Unknown column 'file_path' in 'INSERT INTO'"
-- Usage: mysql -h <HOST> -P <PORT> -u <USER> -p <DATABASE> < 008_create_plugin_tracking_tables.sql

-- Add missing columns to instance_plugins table
ALTER TABLE instance_plugins 
ADD COLUMN IF NOT EXISTS file_path TEXT COMMENT 'Full path to plugin JAR file',
ADD COLUMN IF NOT EXISTS file_size BIGINT COMMENT 'File size in bytes',
ADD COLUMN IF NOT EXISTS file_modified_at TIMESTAMP NULL COMMENT 'Last modified timestamp from filesystem',
ADD COLUMN IF NOT EXISTS first_discovered_at TIMESTAMP NULL COMMENT 'First time this plugin was discovered',
ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP NULL COMMENT 'Last time this plugin was seen during discovery',
ADD COLUMN IF NOT EXISTS installation_method VARCHAR(50) DEFAULT 'unknown' COMMENT 'How plugin was installed';

-- Add missing columns to instance_datapacks table
-- Note: Handle both datapack_name and datapack_id (idempotent)
-- First, check if we need to rename datapack_name to datapack_id
SET @col_exists = (SELECT COUNT(*) FROM information_schema.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'instance_datapacks' 
    AND COLUMN_NAME = 'datapack_name');

SET @sql_rename = IF(@col_exists > 0, 
    'ALTER TABLE instance_datapacks CHANGE COLUMN datapack_name datapack_id VARCHAR(128) NOT NULL COMMENT "Datapack identifier"',
    'SELECT "Column datapack_name does not exist, skipping rename" AS Info');

PREPARE stmt FROM @sql_rename;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Now add the missing columns
ALTER TABLE instance_datapacks
ADD COLUMN IF NOT EXISTS file_path TEXT COMMENT 'Full path to datapack folder/zip',
ADD COLUMN IF NOT EXISTS file_size BIGINT COMMENT 'File size in bytes, 0 for folders',
ADD COLUMN IF NOT EXISTS first_discovered_at TIMESTAMP NULL COMMENT 'First time this datapack was discovered',
ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP NULL COMMENT 'Last time this datapack was seen during discovery';

-- Add indexes for performance
ALTER TABLE instance_plugins 
ADD INDEX IF NOT EXISTS idx_file_hash (file_hash),
ADD INDEX IF NOT EXISTS idx_modified (file_modified_at),
ADD INDEX IF NOT EXISTS idx_last_seen (last_seen_at);

ALTER TABLE instance_datapacks
ADD INDEX IF NOT EXISTS idx_file_hash (file_hash),
ADD INDEX IF NOT EXISTS idx_last_seen (last_seen_at);

-- Deployment Instructions:
-- Run on production (Hetzner):
-- mysql -h <DB_HOST> -P <DB_PORT> -u <DB_USER> -p <DB_NAME> < scripts/migrations/008_create_plugin_tracking_tables.sql
