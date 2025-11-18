-- Hierarchy Resolution Views
-- Purpose: SQL views for resolving config values across 7-level hierarchy
-- Author: AI Assistant
-- Date: 2025-01-04
-- Related Todos: #23, #24, #25

-- =============================================================================
-- View 1: v_config_hierarchy
-- Shows the full resolution chain for every config key across all scopes
-- =============================================================================
CREATE OR REPLACE VIEW v_config_hierarchy AS
SELECT 
    cr.rule_id,
    cr.plugin_id,
    cr.config_key,
    cr.scope_type,
    cr.scope_identifier,
    cr.config_value,
    cr.value_type,
    cr.is_active,
    cr.created_at,
    cr.priority,
    -- Add context for each scope type
    CASE cr.scope_type
        WHEN 'GLOBAL' THEN 'GLOBAL'
        WHEN 'SERVER' THEN CONCAT('SERVER:', cr.scope_identifier)
        WHEN 'META_TAG' THEN CONCAT('META_TAG:', mt.tag_name)
        WHEN 'INSTANCE' THEN CONCAT('INSTANCE:', i.instance_name)
        WHEN 'WORLD' THEN CONCAT('WORLD:', cr.scope_identifier)
        WHEN 'RANK' THEN CONCAT('RANK:', cr.scope_identifier)
        WHEN 'PLAYER' THEN CONCAT('PLAYER:', cr.scope_identifier)
    END AS scope_display,
    -- Join related entities
    p.plugin_name,
    p.plugin_version,
    i.instance_name,
    i.server_name,
    mt.tag_name AS meta_tag_name,
    mt.tag_category
FROM config_rules cr
LEFT JOIN plugins p ON cr.plugin_id = p.plugin_id
LEFT JOIN instances i ON cr.scope_identifier = i.instance_id AND cr.scope_type = 'INSTANCE'
LEFT JOIN meta_tags mt ON cr.scope_identifier = CAST(mt.tag_id AS CHAR) AND cr.scope_type = 'META_TAG'
WHERE cr.is_active = TRUE
ORDER BY cr.plugin_id, cr.config_key, 
    FIELD(cr.scope_type, 'GLOBAL', 'SERVER', 'META_TAG', 'INSTANCE', 'WORLD', 'RANK', 'PLAYER');

-- =============================================================================
-- View 2: v_instance_effective_configs
-- Resolves the final effective config value for each instance after hierarchy cascade
-- Uses GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER priority
-- =============================================================================
CREATE OR REPLACE VIEW v_instance_effective_configs AS
WITH ranked_configs AS (
    SELECT 
        i.instance_id,
        i.instance_name,
        i.server_name,
        cr.plugin_id,
        cr.config_key,
        cr.config_value,
        cr.value_type,
        cr.scope_type,
        cr.scope_identifier,
        -- Priority: PLAYER (highest) > RANK > WORLD > INSTANCE > META_TAG > SERVER > GLOBAL (lowest)
        ROW_NUMBER() OVER (
            PARTITION BY i.instance_id, cr.plugin_id, cr.config_key
            ORDER BY 
                FIELD(cr.scope_type, 'PLAYER', 'RANK', 'WORLD', 'INSTANCE', 'META_TAG', 'SERVER', 'GLOBAL') DESC,
                cr.priority DESC,
                cr.created_at DESC
        ) AS config_priority_rank
    FROM instances i
    CROSS JOIN config_rules cr
    LEFT JOIN instance_meta_tags imt ON i.instance_id = imt.instance_id
    WHERE cr.is_active = TRUE
      AND (
          -- GLOBAL: applies to all
          cr.scope_type = 'GLOBAL'
          -- SERVER: matches instance's server
          OR (cr.scope_type = 'SERVER' AND cr.scope_identifier = i.server_name)
          -- META_TAG: instance has this tag
          OR (cr.scope_type = 'META_TAG' AND cr.scope_identifier = CAST(imt.tag_id AS CHAR))
          -- INSTANCE: exact match
          OR (cr.scope_type = 'INSTANCE' AND cr.scope_identifier = i.instance_id)
          -- WORLD/RANK/PLAYER: require additional context, included for completeness
          OR cr.scope_type IN ('WORLD', 'RANK', 'PLAYER')
      )
)
SELECT 
    instance_id,
    instance_name,
    server_name,
    plugin_id,
    config_key,
    config_value AS effective_value,
    value_type,
    scope_type AS resolved_from_scope,
    scope_identifier AS resolved_from_identifier
FROM ranked_configs
WHERE config_priority_rank = 1
ORDER BY instance_id, plugin_id, config_key;

-- =============================================================================
-- View 3: v_variance_by_scope
-- Shows config variance (differences) at each scope level
-- =============================================================================
CREATE OR REPLACE VIEW v_variance_by_scope AS
WITH scope_values AS (
    SELECT 
        cr.plugin_id,
        cr.config_key,
        cr.scope_type,
        COUNT(DISTINCT cr.config_value) AS distinct_value_count,
        COUNT(*) AS total_rules,
        GROUP_CONCAT(DISTINCT cr.config_value ORDER BY cr.config_value SEPARATOR ' | ') AS all_values,
        MIN(cr.config_value) AS min_value,
        MAX(cr.config_value) AS max_value
    FROM config_rules cr
    WHERE cr.is_active = TRUE
    GROUP BY cr.plugin_id, cr.config_key, cr.scope_type
),
total_variance AS (
    SELECT
        plugin_id,
        config_key,
        COUNT(DISTINCT config_value) AS total_distinct_values,
        SUM(total_rules) AS total_rules_all_scopes
    FROM config_rules
    WHERE is_active = TRUE
    GROUP BY plugin_id, config_key
)
SELECT 
    sv.plugin_id,
    p.plugin_name,
    sv.config_key,
    sv.scope_type,
    sv.distinct_value_count,
    sv.total_rules,
    sv.all_values,
    tv.total_distinct_values AS total_variance_across_scopes,
    tv.total_rules_all_scopes,
    -- Variance indicator
    CASE 
        WHEN sv.distinct_value_count = 1 THEN 'UNIFORM'
        WHEN sv.distinct_value_count <= 3 THEN 'LOW_VARIANCE'
        WHEN sv.distinct_value_count <= 10 THEN 'MEDIUM_VARIANCE'
        ELSE 'HIGH_VARIANCE'
    END AS variance_level,
    -- Percentage of total variance
    ROUND((sv.distinct_value_count / tv.total_distinct_values) * 100, 2) AS pct_of_total_variance
FROM scope_values sv
JOIN total_variance tv ON sv.plugin_id = tv.plugin_id AND sv.config_key = tv.config_key
LEFT JOIN plugins p ON sv.plugin_id = p.plugin_id
WHERE sv.distinct_value_count > 1  -- Only show configs with variance
ORDER BY total_variance_across_scopes DESC, sv.plugin_id, sv.config_key, sv.scope_type;

-- =============================================================================
-- USAGE EXAMPLES
-- =============================================================================

-- Get effective configs for a specific instance:
-- SELECT * FROM v_instance_effective_configs WHERE instance_id = 'BENT01';

-- See full hierarchy for a plugin's config key:
-- SELECT * FROM v_config_hierarchy WHERE plugin_id = 'LuckPerms' AND config_key LIKE 'storage%';

-- Find high-variance config keys across all scopes:
-- SELECT * FROM v_variance_by_scope WHERE variance_level IN ('HIGH_VARIANCE', 'MEDIUM_VARIANCE');

-- Find configs that differ at INSTANCE level (customization):
-- SELECT * FROM v_variance_by_scope WHERE scope_type = 'INSTANCE' AND distinct_value_count > 1;

-- =============================================================================
-- DEPLOYMENT INSTRUCTIONS
-- =============================================================================
-- 1. Test on development database first
-- 2. Verify views created: SHOW FULL TABLES WHERE Table_type = 'VIEW';
-- 3. Test queries: SELECT COUNT(*) FROM v_config_hierarchy;
-- 4. Deploy to Hetzner: mysql -u root -p archivesmp_config < create_hierarchy_views.sql
-- 5. Deploy to OVH after Hetzner validation
-- 6. Use in API endpoints for config resolution and variance analysis
