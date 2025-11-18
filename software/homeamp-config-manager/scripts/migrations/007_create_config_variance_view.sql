-- Migration 007: Create config_variance view
-- Purpose: Materialized view for detecting configuration variance across instances
-- Author: AI Assistant
-- Date: 2025-11-18
-- Dependencies: config_files, config_rules, instances, meta_tags

-- =============================================================================
-- View: config_variance
-- Detect configuration differences across instances and classify variance
-- =============================================================================
-- Note: This is a regular view. For better performance with large datasets,
-- consider creating a materialized view (requires triggers or scheduled refresh)

CREATE OR REPLACE VIEW config_variance AS
SELECT 
    -- Grouping keys
    cf.plugin_id,
    cf.file_path,
    cf.config_key,
    
    -- Variance metrics
    COUNT(DISTINCT cf.instance_id) as instance_count,
    COUNT(DISTINCT cf.config_value_hash) as unique_values_count,
    
    -- Value distribution (JSON object with instance -> value mapping)
    JSON_OBJECTAGG(i.instance_name, cf.config_value) as value_by_instance,
    
    -- Classification logic
    CASE
        -- NONE: All instances have identical values
        WHEN COUNT(DISTINCT cf.config_value_hash) = 1 THEN 'NONE'
        
        -- META_TAG: Values align with meta-tag groups
        WHEN EXISTS (
            SELECT 1 
            FROM config_rules cr
            WHERE cr.scope_level = 'META_TAG'
              AND cr.plugin_id = cf.plugin_id
              AND cr.config_key = cf.config_key
        ) THEN 'META_TAG'
        
        -- INSTANCE: Intentional per-instance configuration
        WHEN EXISTS (
            SELECT 1
            FROM config_rules cr
            WHERE cr.scope_level = 'INSTANCE'
              AND cr.plugin_id = cf.plugin_id
              AND cr.config_key = cf.config_key
        ) THEN 'INSTANCE'
        
        -- VARIABLE: Expected variation (e.g., server-port, max-players)
        WHEN cf.config_key IN ('server-port', 'max-players', 'server-ip', 'server-name') THEN 'VARIABLE'
        
        -- DRIFT: Unintentional configuration drift (needs attention)
        ELSE 'DRIFT'
    END as variance_classification,
    
    -- Metadata
    MIN(cf.last_modified_at) as earliest_modification,
    MAX(cf.last_modified_at) as latest_modification,
    
    -- Instance groups (for drill-down analysis)
    GROUP_CONCAT(DISTINCT i.server_name) as servers,
    GROUP_CONCAT(DISTINCT mt.tag_name) as meta_tags

FROM config_files cf
JOIN instances i ON cf.instance_id = i.instance_id
LEFT JOIN instance_meta_tags imt ON i.instance_id = imt.instance_id
LEFT JOIN meta_tags mt ON imt.tag_id = mt.tag_id

GROUP BY cf.plugin_id, cf.file_path, cf.config_key

-- Only include keys that actually have variance
HAVING unique_values_count > 1

ORDER BY 
    variance_classification DESC,  -- Show DRIFT first
    instance_count DESC,            -- Then widespread issues
    plugin_id, 
    config_key;

-- =============================================================================
-- Alternative: Materialized view (better performance for large datasets)
-- =============================================================================
-- Uncomment this section to create a materialized view instead
-- Requires manual refresh or trigger-based updates

/*
CREATE TABLE IF NOT EXISTS config_variance_materialized (
    variance_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64),
    file_path VARCHAR(512),
    config_key VARCHAR(512),
    instance_count INT,
    unique_values_count INT,
    value_by_instance JSON,
    variance_classification ENUM('NONE', 'VARIABLE', 'META_TAG', 'INSTANCE', 'DRIFT'),
    earliest_modification TIMESTAMP,
    latest_modification TIMESTAMP,
    servers TEXT,
    meta_tags TEXT,
    last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_classification (variance_classification),
    INDEX idx_plugin (plugin_id),
    INDEX idx_unique_values (unique_values_count),
    INDEX idx_last_refreshed (last_refreshed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Materialized view of config variance for performance';

-- Refresh procedure (run periodically)
DELIMITER $$
CREATE PROCEDURE refresh_config_variance()
BEGIN
    TRUNCATE TABLE config_variance_materialized;
    
    INSERT INTO config_variance_materialized (
        plugin_id, file_path, config_key, instance_count, unique_values_count,
        value_by_instance, variance_classification, earliest_modification,
        latest_modification, servers, meta_tags
    )
    SELECT * FROM config_variance;
END$$
DELIMITER ;
*/

-- =============================================================================
-- Verification queries
-- =============================================================================
-- Variance by classification:
-- SELECT variance_classification, COUNT(*) as count
-- FROM config_variance
-- GROUP BY variance_classification;

-- Top drift issues (needs immediate attention):
-- SELECT plugin_id, config_key, instance_count, unique_values_count
-- FROM config_variance
-- WHERE variance_classification = 'DRIFT'
-- ORDER BY instance_count DESC, unique_values_count DESC
-- LIMIT 20;

-- Variance for specific plugin:
-- SELECT config_key, variance_classification, unique_values_count, value_by_instance
-- FROM config_variance
-- WHERE plugin_id = 'EssentialsX'
-- ORDER BY variance_classification DESC;
