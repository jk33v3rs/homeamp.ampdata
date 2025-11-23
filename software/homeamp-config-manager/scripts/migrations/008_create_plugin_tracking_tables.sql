-- Add Missing Columns to Plugin and Datapack Tracking Tables
-- Purpose: Add file_path, file_hash, file_size, etc. to instance_plugins and instance_datapacks
-- Date: 2025-11-23
-- Fixes: Agent errors "Unknown column 'file_path' in 'INSERT INTO'"
-- Usage: mysql -h <HOST> -P <PORT> -u <USER> -p <DATABASE> < 008_create_plugin_tracking_tables.sql

-- Add missing columns to instance_plugins table
ALTER TABLE instance_plugins 
ADD COLUMN IF NOT EXISTS file_path TEXT COMMENT 'Full path to plugin JAR file',
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64) COMMENT 'SHA256 hash of JAR file',
ADD COLUMN IF NOT EXISTS file_size BIGINT COMMENT 'File size in bytes',
ADD COLUMN IF NOT EXISTS file_modified_at TIMESTAMP NULL COMMENT 'Last modified timestamp from filesystem',
ADD COLUMN IF NOT EXISTS installation_method VARCHAR(50) DEFAULT 'unknown' COMMENT 'How plugin was installed';

-- Add missing columns to instance_datapacks table  
ALTER TABLE instance_datapacks
ADD COLUMN IF NOT EXISTS file_path TEXT COMMENT 'Full path to datapack folder/zip',
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64) COMMENT 'SHA256 hash if file, else "folder"',
ADD COLUMN IF NOT EXISTS file_size BIGINT COMMENT 'File size in bytes, 0 for folders';

-- Add indexes for performance
ALTER TABLE instance_plugins 
ADD INDEX IF NOT EXISTS idx_file_hash (file_hash),
ADD INDEX IF NOT EXISTS idx_modified (file_modified_at);

ALTER TABLE instance_datapacks
ADD INDEX IF NOT EXISTS idx_file_hash (file_hash);

-- Deployment Instructions:
-- Run on production (Hetzner):
-- mysql -h <DB_HOST> -P <DB_PORT> -u <DB_USER> -p <DB_NAME> < scripts/migrations/008_create_plugin_tracking_tables.sql
