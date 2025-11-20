-- Fix Recent Activity Log Issues
-- Run on production database: asmp_config

USE asmp_config;

-- Step 1: Update enum to include 'plugin_lifecycle'
ALTER TABLE config_change_history 
MODIFY COLUMN change_type ENUM('manual', 'automated', 'migration', 'drift_fix', 'plugin_lifecycle', 'plugin_install', 'plugin_update', 'plugin_remove') 
DEFAULT 'manual';

-- Step 2: Clear all plugin_lifecycle entries (they're polluting the log)
DELETE FROM config_change_history 
WHERE change_type = 'plugin_lifecycle';

-- Step 3: Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_change_history_recent 
ON config_change_history(changed_at DESC, change_type);

-- Verify the changes
SELECT 
    change_type,
    COUNT(*) as count,
    MAX(changed_at) as most_recent
FROM config_change_history
GROUP BY change_type
ORDER BY most_recent DESC;
