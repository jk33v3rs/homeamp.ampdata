-- ============================================================================
-- Clear Duplicate/Spam Logs from Agent Logging Loop
-- Run this to clean up tens of thousands of duplicate records before deploying fix
-- Usage: mysql -h <HOST> -P <PORT> -u <USER> -p <DATABASE> < scripts/clear_duplicate_logs.sql
-- ============================================================================

-- Show counts before cleanup
SELECT 'Before cleanup:' as status;
SELECT 
    'config_change_history' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT instance_id) as unique_instances,
    MIN(changed_at) as oldest_record,
    MAX(changed_at) as newest_record
FROM config_change_history
WHERE change_source = 'agent-hetzner-xeon'
  AND plugin_name IN ('plugins', 'datapacks', 'server');

-- Backup table (optional - comment out if not needed)
-- CREATE TABLE config_change_history_backup_20251120 AS SELECT * FROM config_change_history;

-- ============================================================================
-- Keep only the FIRST occurrence of each plugin installation per instance
-- Delete all subsequent duplicates
-- ============================================================================

-- For plugin installations (keeps oldest record, deletes newer duplicates)
DELETE cch FROM config_change_history cch
INNER JOIN (
    SELECT 
        instance_id,
        plugin_name,
        config_key,
        new_value,
        MIN(change_id) as keep_id
    FROM config_change_history
    WHERE change_source LIKE 'agent-%'
      AND config_file = 'plugins'
      AND config_key = 'plugin_lifecycle'
      AND change_reason LIKE 'Plugin install:%'
    GROUP BY instance_id, plugin_name, new_value
) as keeper ON cch.instance_id = keeper.instance_id
    AND cch.plugin_name = keeper.plugin_name
    AND cch.new_value = keeper.new_value
    AND cch.config_file = 'plugins'
    AND cch.config_key = 'plugin_lifecycle'
WHERE cch.change_id != keeper.keep_id
  AND cch.change_reason LIKE 'Plugin install:%';

-- For datapack installations
DELETE cch FROM config_change_history cch
INNER JOIN (
    SELECT 
        instance_id,
        plugin_name,
        config_file,
        new_value,
        MIN(change_id) as keep_id
    FROM config_change_history
    WHERE change_source LIKE 'agent-%'
      AND plugin_name = 'datapacks'
      AND config_key = 'datapack_lifecycle'
      AND change_reason LIKE 'Datapack installed:%'
    GROUP BY instance_id, config_file, new_value
) as keeper ON cch.instance_id = keeper.instance_id
    AND cch.config_file = keeper.config_file
    AND cch.new_value = keeper.new_value
    AND cch.plugin_name = 'datapacks'
WHERE cch.change_id != keeper.keep_id
  AND cch.change_reason LIKE 'Datapack installed:%';

-- For server property changes (keep only distinct changes)
DELETE cch FROM config_change_history cch
INNER JOIN (
    SELECT 
        instance_id,
        config_key,
        old_value,
        new_value,
        MIN(change_id) as keep_id
    FROM config_change_history
    WHERE change_source LIKE 'agent-%'
      AND plugin_name = 'server'
      AND config_file = 'server.properties'
    GROUP BY instance_id, config_key, old_value, new_value
) as keeper ON cch.instance_id = keeper.instance_id
    AND cch.config_key = keeper.config_key
    AND cch.old_value = keeper.old_value
    AND cch.new_value = keeper.new_value
    AND cch.plugin_name = 'server'
WHERE cch.change_id != keeper.keep_id;

-- ============================================================================
-- Show counts after cleanup
-- ============================================================================

SELECT 'After cleanup:' as status;
SELECT 
    'config_change_history' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT instance_id) as unique_instances,
    MIN(changed_at) as oldest_record,
    MAX(changed_at) as newest_record
FROM config_change_history
WHERE change_source = 'agent-hetzner-xeon'
  AND plugin_name IN ('plugins', 'datapacks', 'server');

-- Show remaining records by type
SELECT 
    plugin_name,
    config_file,
    COUNT(*) as count
FROM config_change_history
WHERE change_source LIKE 'agent-%'
GROUP BY plugin_name, config_file
ORDER BY plugin_name, config_file;

SELECT CONCAT('Cleanup complete. Safe to deploy agent fix now.') as message;
