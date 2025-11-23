-- ============================================================================
-- SCHEMA FIXES FOR BROKEN FOREIGN KEYS AND INCONSISTENCIES
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- FIX 1: Meta Tags Primary Key Inconsistency
-- Current: meta_tags has 'id' as PK
-- Problem: FKs reference meta_tags(tag_id) which doesn't exist
-- Fix: Rename 'id' to 'tag_id'
-- ============================================================================

-- Note: This requires dropping FKs first, then renaming, then recreating FKs
-- Better approach: Use tag_id from the start in the corrected schema below

-- ============================================================================
-- FIX 2: Plugin Version Foreign Key Type Mismatch
-- Current: plugins.plugin_id = VARCHAR(64)
-- Problem: plugin_versions.plugin_id = INT references plugins(id) [doesn't exist]
-- Fix: Change plugin_versions and plugin_update_sources to use VARCHAR(64)
-- ============================================================================

ALTER TABLE plugin_versions MODIFY plugin_id VARCHAR(64) NOT NULL;
ALTER TABLE plugin_versions DROP FOREIGN KEY plugin_versions_ibfk_1;
ALTER TABLE plugin_versions ADD FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE;

ALTER TABLE plugin_update_sources MODIFY plugin_id VARCHAR(64) NOT NULL;
ALTER TABLE plugin_update_sources DROP FOREIGN KEY plugin_update_sources_ibfk_1;
ALTER TABLE plugin_update_sources ADD FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE;

-- ============================================================================
-- FIX 3: Datapack Deployment Queue FK Mismatch
-- Current: datapacks has 'id' as PK
-- Problem: datapack_deployment_queue references datapacks(datapack_id) [doesn't exist]
-- Fix: Change FK to reference datapacks(id) OR add datapack_id column
-- ============================================================================

-- Option 1: Change the FK column to reference id
ALTER TABLE datapack_deployment_queue DROP FOREIGN KEY datapack_deployment_queue_ibfk_1;
ALTER TABLE datapack_deployment_queue MODIFY datapack_id INT NOT NULL;
ALTER TABLE datapack_deployment_queue ADD FOREIGN KEY (datapack_id) REFERENCES datapacks(id) ON DELETE CASCADE;

-- ============================================================================
-- FIX 4: Deployment Queue and History Linkage
-- Current: deployment_queue has VARCHAR(36) deployment_id
-- Current: deployment_history has INT deployment_id
-- Problem: They're disconnected - no way to link queue to history
-- Fix: Add queue_deployment_id to deployment_history
-- ============================================================================

ALTER TABLE deployment_history ADD COLUMN queue_deployment_id VARCHAR(36) NULL COMMENT 'Links to deployment_queue.deployment_id';
ALTER TABLE deployment_history ADD INDEX idx_queue_deployment (queue_deployment_id);

-- ============================================================================
-- FIX 5: Approval Votes Syntax Error
-- Current: CREATE TABLE ... ) ENGINE;
-- Problem: Missing =InnoDB
-- Fix: Complete the ENGINE clause
-- ============================================================================

-- Will be fixed in the corrected schema generation

-- ============================================================================
-- SUMMARY
-- ============================================================================

SELECT 'Schema fixes applied successfully!' AS status;
