# Database Schema Redundancy Analysis

**Purpose:** Identify duplicate/redundant tables that should be consolidated

---

## Table Categories

### Approval Workflow (2 tables)

- `approval_votes` (16 columns, 1 files)
- `change_approval_requests` (43 columns, 2 files)

### Config History (2 tables)

- `config_change_history` (58 columns, 4 files)
- `endpoint_config_change_history` (7 columns, 1 files)

### Config Management (2 tables)

- `config_key_migrations` (26 columns, 3 files)
- `config_locks` (21 columns, 1 files)

### Config Other (5 tables)

- `config_keys` (20 columns, 1 files)
- `config_variables` (14 columns, 3 files)
- `endpoint_config_backups` (27 columns, 2 files)
- `endpoint_config_files` (54 columns, 3 files)
- `player_config_overrides` (5 columns, 1 files)

### Config Rules (5 tables)

- `config_baselines` (4 columns, 1 files)
- `config_rules` (157 columns, 8 files)
- `config_templates` (40 columns, 2 files)
- `rank_config_rules` (5 columns, 1 files)
- `world_config_rules` (5 columns, 1 files)

### Config Variance Tracking (5 tables)

- `config_drift_log` (27 columns, 4 files)
- `config_variance_cache` (31 columns, 6 files)
- `config_variance_detected` (36 columns, 1 files)
- `config_variance_history` (25 columns, 1 files)
- `config_variances` (51 columns, 3 files)

### Core Data (5 tables)

- `datapacks` (80 columns, 3 files)
- `instances` (205 columns, 19 files)
- `plugins` (157 columns, 14 files)
- `ranks` (15 columns, 1 files)
- `worlds` (12 columns, 1 files)

### Deployment Updates (5 tables)

- `datapack_deployment_queue` (6 columns, 1 files)
- `deployment_history` (40 columns, 4 files)
- `deployment_logs` (21 columns, 3 files)
- `deployment_queue` (26 columns, 8 files)
- `plugin_update_queue` (20 columns, 2 files)

### Discovery Monitoring (4 tables)

- `agent_heartbeats` (4 columns, 2 files)
- `discovery_items` (11 columns, 1 files)
- `discovery_runs` (11 columns, 1 files)
- `system_health_metrics` (33 columns, 3 files)

### History Audit (2 tables)

- `audit_log` (40 columns, 3 files)
- `notification_log` (36 columns, 3 files)

### Junctions (5 tables)

- `instance_datapacks` (61 columns, 6 files)
- `instance_groups` (16 columns, 2 files)
- `instance_meta_tags` (44 columns, 3 files)
- `instance_plugins` (82 columns, 6 files)
- `instance_tags` (58 columns, 5 files)

### Metadata Tagging (8 tables)

- `meta_tag_categories` (44 columns, 2 files)
- `meta_tag_history` (12 columns, 1 files)
- `meta_tags` (87 columns, 6 files)
- `plugin_meta_tags` (9 columns, 1 files)
- `plugin_metadata` (8 columns, 1 files)
- `tag_conflicts` (16 columns, 1 files)
- `tag_dependencies` (17 columns, 1 files)
- `tag_hierarchy` (6 columns, 1 files)

### Uncategorized (10 tables)

- `baseline_snapshots` (9 columns, 1 files)
- `cicd_webhook_events` (9 columns, 2 files)
- `installed_plugins` (14 columns, 2 files)
- `instance_group_members` (10 columns, 1 files)
- `instance_server_properties` (35 columns, 3 files)
- `plugin_instances` (34 columns, 1 files)
- `plugin_versions` (80 columns, 6 files)
- `scheduled_tasks` (13 columns, 1 files)
- `server_properties_baselines` (42 columns, 2 files)
- `server_properties_variances` (40 columns, 2 files)

## 🚨 CRITICAL: Redundant Table Groups

These groups contain multiple tables doing the same job - major source of bloat!

### 1. Config Variance/Drift Tracking

**Tables:**
- `config_variance_detected` (36 columns)
- `config_variance_history` (25 columns)
- `config_variances` (51 columns)
- `config_variance_cache` (31 columns)
- `config_drift_log` (27 columns)

**Reason:** Multiple overlapping systems tracking config drift/variance

**✅ Recommendation:** Keep `config_variance_cache` (core working table - 6 files) + `config_drift_log` (event history - 4 files). Remove `config_variances` (old parallel system - 3 files), `config_variance_detected` (barely used - 1 file), `config_variance_history` (dead code - 1 file)

**Analysis:**
- `config_variance_cache`: Live snapshot of ALL config values, stores actual vs expected, used by dashboard
- `config_drift_log`: Time-series event log when drift is first detected (append-only audit trail)
- `config_variances`: Duplicate older variance tracking from variance_detector.py - REDUNDANT
- `config_variance_detected`: Only used for counts in plugin_configurator_endpoints.py - SAFE TO REMOVE
- `config_variance_history`: Only in comments/one SELECT, no INSERT statements found - DEAD CODE

**File Usage:**

- `config_drift_log`: 4 file(s)
  - scripts\drift_scanner_service.py
  - scripts\enforce_config.py
  - scripts\populate_config_cache.py
  - src\web\api.py
- `config_variance_cache`: 6 file(s)
  - scripts\drift_scanner_service.py
  - scripts\enforce_config.py
  - scripts\populate_config_cache.py
  - src\api\dashboard_endpoints.py
  - src\database\db_access.py
  - src\web\api.py
- `config_variance_detected`: 1 file(s)
  - src\api\plugin_configurator_endpoints.py
- `config_variance_history`: 1 file(s)
  - src\web\api.py
- `config_variances`: 3 file(s)
  - src\agent\variance_detector.py
  - src\api\enhanced_endpoints.py
  - src\api\variance_endpoints.py

---

### 2. Config Change History

**Tables:**
- `config_change_history` (58 columns)
- `endpoint_config_change_history` (7 columns)

**Reason:** Both track config changes over time

**✅ Recommendation:** Merge into config_change_history or remove if not deploying

**File Usage:**

- `config_change_history`: 4 file(s)
  - src\agent\conflict_detector.py
  - src\api\dashboard_endpoints.py
  - src\database\db_access.py
  - src\web\api.py
- `endpoint_config_change_history`: 1 file(s)
  - src\agent\database_methods_extension.py

---

### 3. Discovery Tracking

**Tables:**
- `discovery_runs` (11 columns)
- `discovery_items` (11 columns)

**Reason:** discovery_items caused 153M record bloat - REMOVE

**✅ Recommendation:** Keep discovery_runs ONLY (summary stats)

**File Usage:**

- `discovery_items`: 1 file(s)
  - src\agent\agent_database_methods.py
- `discovery_runs`: 1 file(s)
  - src\agent\agent_database_methods.py

---

### 4. Deployment Queues

**Tables:**
- `deployment_queue` (26 columns)
- `plugin_update_queue` (20 columns)
- `datapack_deployment_queue` (6 columns)

**Reason:** Multiple queues for same purpose

**✅ Recommendation:** Use deployment_queue with type field (plugin/datapack/config)

**File Usage:**

- `datapack_deployment_queue`: 1 file(s)
  - src\agent\agent_update_methods.py
- `deployment_queue`: 8 file(s)
  - src\agent\config_deployer.py
  - src\agent\conflict_detector.py
  - src\agent\performance_metrics.py
  - src\agent\scheduled_tasks.py
  - src\api\deployment_endpoints.py
  - src\api\enhanced_endpoints.py
  - src\api\plugin_configurator_endpoints.py
  - src\api\update_manager_endpoints.py
- `plugin_update_queue`: 2 file(s)
  - src\agent\agent_cicd_methods.py
  - src\agent\agent_update_methods.py

---

### 5. Config Baselines/Rules

**Tables:**
- `config_baselines` (4 columns)
- `config_rules` (157 columns)
- `config_templates` (40 columns)
- `baseline_snapshots` (9 columns)
- `server_properties_baselines` (42 columns)

**Reason:** Multiple tables for "expected" config values

**✅ Recommendation:** Consolidate to config_rules + server_properties_baselines

**File Usage:**

- `baseline_snapshots`: 1 file(s)
  - scripts\load_baselines.py
- `config_baselines`: 1 file(s)
  - src\agent\variance_detector.py
- `config_rules`: 8 file(s)
  - scripts\drift_scanner_service.py
  - scripts\load_baselines.py
  - scripts\populate_config_cache.py
  - src\core\hierarchy_resolver.py
  - src\database\db_access.py
  - src\engine\hierarchy_resolver.py
  - src\parsers\baseline_parser.py
  - src\web\api.py
- `config_templates`: 2 file(s)
  - src\agent\config_templates.py
  - src\web\api.py
- `server_properties_baselines`: 2 file(s)
  - src\agent\server_properties_scanner.py
  - src\api\enhanced_endpoints.py

---

### 6. Instance Tagging

**Tables:**
- `instance_tags` (58 columns)
- `instance_meta_tags` (44 columns)

**Reason:** Both assign tags to instances - one uses meta_tags FK, one is key-value

**✅ Recommendation:** Pick ONE approach: either instance_meta_tags (structured) OR instance_tags (flexible)

**File Usage:**

- `instance_meta_tags`: 3 file(s)
  - src\agent\agent_database_methods.py
  - src\api\tag_manager_endpoints.py
  - src\engine\hierarchy_resolver.py
- `instance_tags`: 5 file(s)
  - scripts\drift_scanner_service.py
  - scripts\populate_config_cache.py
  - src\api\dashboard_endpoints.py
  - src\database\db_access.py
  - src\web\api.py

---

## Similar Table Names

Tables with similar names that might be duplicates:

- `config_variables` ↔ `config_variances`
  - name similarity 88%
  - Columns: 14 vs 51
  - Files: 3 vs 3

- `server_properties_baselines` ↔ `server_properties_variances`
  - shared prefix 'server_'
  - Columns: 42 vs 40
  - Files: 2 vs 2

- `installed_plugins` ↔ `instance_plugins`
  - name similarity 85%
  - Columns: 14 vs 82
  - Files: 2 vs 6

- `instance_meta_tags` ↔ `instance_tags`
  - name similarity 84%
  - Columns: 44 vs 58
  - Files: 3 vs 5

- `plugin_meta_tags` ↔ `plugin_metadata`
  - name similarity 84%
  - Columns: 9 vs 8
  - Files: 1 vs 1

- `config_rules` ↔ `rank_config_rules`
  - name similarity 83%
  - Columns: 157 vs 5
  - Files: 8 vs 1

- `config_change_history` ↔ `endpoint_config_change_history`
  - both track history
  - Columns: 58 vs 7
  - Files: 4 vs 1

- `config_variance_history` ↔ `config_variances`
  - both track variance/drift
  - Columns: 25 vs 51
  - Files: 1 vs 3

- `config_change_history` ↔ `config_variance_history`
  - both track history
  - Columns: 58 vs 25
  - Files: 4 vs 1

- `instance_tags` ↔ `instances`
  - name similarity 82%
  - Columns: 58 vs 205
  - Files: 5 vs 19

- `config_variance_cache` ↔ `config_variances`
  - both track variance/drift
  - Columns: 31 vs 51
  - Files: 6 vs 3

- `instance_group_members` ↔ `instance_groups`
  - name similarity 81%
  - Columns: 10 vs 16
  - Files: 1 vs 2

- `config_rules` ↔ `world_config_rules`
  - name similarity 80%
  - Columns: 157 vs 5
  - Files: 8 vs 1

- `config_variance_cache` ↔ `config_variance_detected`
  - both track variance/drift
  - Columns: 31 vs 36
  - Files: 6 vs 1

- `rank_config_rules` ↔ `world_config_rules`
  - name similarity 80%
  - Columns: 5 vs 5
  - Files: 1 vs 1

- `config_rules` ↔ `config_variables`
  - name similarity 79%
  - Columns: 157 vs 14
  - Files: 8 vs 3

- `instance_groups` ↔ `instance_tags`
  - name similarity 79%
  - Columns: 16 vs 58
  - Files: 2 vs 5

- `config_keys` ↔ `config_locks`
  - name similarity 78%
  - Columns: 20 vs 21
  - Files: 1 vs 1

- `config_keys` ↔ `config_rules`
  - name similarity 78%
  - Columns: 20 vs 157
  - Files: 1 vs 8

- `datapack_deployment_queue` ↔ `deployment_queue`
  - both are queues
  - Columns: 6 vs 26
  - Files: 1 vs 8

## High Column Overlap

Tables sharing many columns (might be redundant):

- `change_approval_requests` ↔ `config_variance_history`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_change_history` ↔ `config_variance_history`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_key_migrations` ↔ `config_variance_history`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_rules` ↔ `player_config_overrides`
  - 5 shared columns (100% overlap)
  - Common: config_key, config_value, player_uuid, plugin_id, stance_id

- `config_rules` ↔ `rank_config_rules`
  - 5 shared columns (100% overlap)
  - Common: config_key, config_value, plugin_id, rank_name, stance_id

- `config_rules` ↔ `world_config_rules`
  - 5 shared columns (100% overlap)
  - Common: config_key, config_value, plugin_id, stance_id, world_name

- `config_templates` ↔ `config_variance_history`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_variance_history` ↔ `deployment_history`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_variance_history` ↔ `for`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_variance_history` ↔ `notification_log`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_variance_history` ↔ `pending`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `config_variance_history` ↔ `system_health_metrics`
  - 25 shared columns (100% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

- `datapack_deployment_queue` ↔ `plugin_update_queue`
  - 6 shared columns (100% overlap)
  - Common: created_at, limit, pend, priority, scheduled_for, status

- `for` ↔ `server_properties_variances`
  - 40 shared columns (100% overlap)
  - Common: detail, dictionary, insert, instance_id, jo, properties, property_key, query, ra, timestamp ... (+30 more)

- `datapacks` ↔ `instances`
  - 79 shared columns (99% overlap)
  - Common: dictionary, display_name, endpo, is_enabled, jo, name, timestamp, total_datapacks, track, view_d ... (+69 more)

- `for` ↔ `server_properties_baselines`
  - 41 shared columns (98% overlap)
  - Common: created_at, detail, dictionary, insert, jo, properties, property_key, query, ra, timestamp ... (+31 more)

- `datapacks` ↔ `for`
  - 78 shared columns (98% overlap)
  - Common: an, dictionary, endpo, is_enabled, jo, name, timestamp, total_datapacks, track, view_d ... (+68 more)

- `server_properties_baselines` ↔ `server_properties_variances`
  - 39 shared columns (98% overlap)
  - Common: detail, dictionary, insert, instance_id, jo, properties, property_key, query, ra, timestamp ... (+29 more)

- `instances` ↔ `plugin_instances`
  - 33 shared columns (97% overlap)
  - Common: detail, dictionary, instance_id, instance_name, jo, plugin, ra, read, result, target ... (+23 more)

- `change_approval_requests` ↔ `config_key_migrations`
  - 25 shared columns (96% overlap)
  - Common: change_type, changed_by, created_at, deployed_at, deployed_by, limit, notification_type, params, query, to_version ... (+15 more)

## Summary & Recommendations

**Current State:** 64 tables

**Redundant Groups Found:** 6

### Immediate Actions:

1. **Config Variance:** Keep `config_variance_cache` + `config_drift_log` (different purposes). Remove 3 redundant tables: `config_variances`, `config_variance_detected`, `config_variance_history`
2. **Discovery:** Remove `discovery_items` (153M record bloat source), keep `discovery_runs` for summary stats
3. **Deployment:** Merge 3 queue tables → 1 `deployment_queue` with type field (plugin/datapack/config)
4. **Tagging:** Pick ONE approach: `instance_meta_tags` (structured, 3 files) OR `instance_tags` (flexible key-value, 5 files)
5. **Baselines:** Consolidate to `config_rules` (heavily used, 8 files) + `server_properties_baselines` (specialized, 2 files). Remove `config_baselines`, `config_templates`, `baseline_snapshots`
6. **Config History:** Merge `endpoint_config_change_history` (1 file) → `config_change_history` (4 files)

### Expected Reduction:

- **Before:** 64 tables
- **After:** ~35-40 tables (40% reduction)
- **Bloat Eliminated:** discovery_items, redundant variance tables

