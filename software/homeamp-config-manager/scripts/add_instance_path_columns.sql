-- Add Instance Folder and Path Tracking Columns
-- Purpose: Track AMP instance folder names and paths for accurate config file location
-- Author: AI Assistant
-- Date: 2025-01-04
-- Related Todos: #4, #5, #6, #7

-- Add column to store the actual folder name under /home/amp/.ampdata/instances/
-- This may differ from instance_id (e.g., "SMP201-Season2" vs "SMP201")
ALTER TABLE instances 
ADD COLUMN instance_folder_name VARCHAR(128) COMMENT 'Actual folder name under AMP instances directory';

-- Add column to store the full base path to the instance
-- Example: /home/amp/.ampdata/instances/SMP201-Season2
ALTER TABLE instances 
ADD COLUMN instance_base_path VARCHAR(512) COMMENT 'Full path to instance root directory';

-- Add index for efficient folder name lookups
ALTER TABLE instances 
ADD INDEX idx_folder_name (instance_folder_name);

-- NOTE: amp_instance_id column already exists but may be unpopulated
-- This column should store the AMP internal UUID from Instance.conf
-- Example: a1b2c3d4-e5f6-7890-abcd-ef1234567890

-- DEPLOYMENT INSTRUCTIONS:
-- 1. Run this on development database first
-- 2. Verify columns added successfully: DESC instances;
-- 3. Deploy to Hetzner: mysql -u root -p archivesmp_config < add_instance_path_columns.sql
-- 4. Deploy to OVH after Hetzner validation
-- 5. Agent will populate these columns on next discovery scan
