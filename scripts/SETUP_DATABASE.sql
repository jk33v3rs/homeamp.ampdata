-- ============================================================================
-- COMPLETE DATABASE SETUP - Run this to create all required tables
-- ============================================================================
-- This combines:
-- - create_database_schema.sql (base tables)
-- - add_tracking_history_tables.sql (change tracking)
-- - add_plugin_tracking_tables.sql (plugin management)
-- ============================================================================

USE asmp_config;

-- Source the existing schema files in order
SOURCE create_database_schema.sql;
SOURCE add_tracking_history_tables.sql;
SOURCE add_plugin_tracking_tables.sql;

-- Verify all tables exist
SELECT 'Checking core tables...' AS status;
SELECT TABLE_NAME FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'asmp_config' 
AND TABLE_NAME IN ('instances', 'config_rules', 'config_variables')
ORDER BY TABLE_NAME;

SELECT 'Checking plugin tables...' AS status;
SELECT TABLE_NAME FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'asmp_config' 
AND TABLE_NAME LIKE 'plugin%'
ORDER BY TABLE_NAME;

SELECT 'Checking tracking tables...' AS status;
SELECT TABLE_NAME FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'asmp_config' 
AND TABLE_NAME IN ('config_change_history', 'deployment_history', 'audit_log')
ORDER BY TABLE_NAME;

SELECT 'All tables created!' AS status;
SELECT COUNT(*) AS total_tables FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'asmp_config';
