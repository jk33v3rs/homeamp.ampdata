# Database Schema Requirements (Extracted from Code)

**Generated:** D:\homeamp.ampdata\homeamp.ampdata

**Total Tables Found:** 64

---

## Table Summary

| # | Table Name | Columns Found | Files Referencing |
|---|------------|---------------|-------------------|
| 1 | `agent_heartbeats` | 4 | 2 |
| 2 | `approval_votes` | 16 | 1 |
| 3 | `audit_log` | 40 | 3 |
| 4 | `backup` | 47 | 1 |
| 5 | `baseline_snapshots` | 9 | 1 |
| 6 | `change_approval_requests` | 43 | 2 |
| 7 | `cicd_webhook_events` | 9 | 2 |
| 8 | `config_baselines` | 4 | 1 |
| 9 | `config_change_history` | 58 | 4 |
| 10 | `config_drift_log` | 27 | 4 |
| 11 | `config_key_migrations` | 26 | 3 |
| 12 | `config_keys` | 20 | 1 |
| 13 | `config_locks` | 21 | 1 |
| 14 | `config_rules` | 157 | 8 |
| 15 | `config_templates` | 40 | 2 |
| 16 | `config_variables` | 14 | 3 |
| 17 | `config_variance_cache` | 31 | 6 |
| 18 | `config_variance_detected` | 36 | 1 |
| 19 | `config_variance_history` | 25 | 1 |
| 20 | `config_variances` | 51 | 3 |
| 21 | `datapack_deployment_queue` | 6 | 1 |
| 22 | `datapacks` | 80 | 3 |
| 23 | `deployment_history` | 40 | 4 |
| 24 | `deployment_logs` | 21 | 3 |
| 25 | `deployment_queue` | 26 | 8 |
| 26 | `discovery_items` | 11 | 1 |
| 27 | `discovery_runs` | 11 | 1 |
| 28 | `endpoint_config_backups` | 27 | 2 |
| 29 | `endpoint_config_change_history` | 7 | 1 |
| 30 | `endpoint_config_files` | 54 | 3 |
| 31 | `for` | 217 | 1 |
| 32 | `information_schema` | 6 | 1 |
| 33 | `installed_plugins` | 14 | 2 |
| 34 | `instance_datapacks` | 61 | 6 |
| 35 | `instance_group_members` | 10 | 1 |
| 36 | `instance_groups` | 16 | 2 |
| 37 | `instance_meta_tags` | 44 | 3 |
| 38 | `instance_plugins` | 82 | 6 |
| 39 | `instance_server_properties` | 35 | 3 |
| 40 | `instance_tags` | 58 | 5 |
| 41 | `instances` | 205 | 19 |
| 42 | `meta_tag_categories` | 44 | 2 |
| 43 | `meta_tag_history` | 12 | 1 |
| 44 | `meta_tags` | 87 | 6 |
| 45 | `notification_log` | 36 | 3 |
| 46 | `pending` | 31 | 1 |
| 47 | `player_config_overrides` | 5 | 1 |
| 48 | `plugin_instances` | 34 | 1 |
| 49 | `plugin_meta_tags` | 9 | 1 |
| 50 | `plugin_metadata` | 8 | 1 |
| 51 | `plugin_update_queue` | 20 | 2 |
| 52 | `plugin_versions` | 80 | 6 |
| 53 | `plugins` | 157 | 14 |
| 54 | `rank_config_rules` | 5 | 1 |
| 55 | `ranks` | 15 | 1 |
| 56 | `scheduled_tasks` | 13 | 1 |
| 57 | `server_properties_baselines` | 42 | 2 |
| 58 | `server_properties_variances` | 40 | 2 |
| 59 | `system_health_metrics` | 33 | 3 |
| 60 | `tag_conflicts` | 16 | 1 |
| 61 | `tag_dependencies` | 17 | 1 |
| 62 | `tag_hierarchy` | 6 | 1 |
| 63 | `world_config_rules` | 5 | 1 |
| 64 | `worlds` | 12 | 1 |

---

## Detailed Table Analysis

### agent_heartbeats

**Columns Used:**
- `agent_id`
- `last_heartbeat`
- `server_name`
- `status`

**Referenced In:**
- `src\agent\enhanced_discovery.py`
- `src\api\enhanced_endpoints.py`

**INSERT Operations:** 5 found

**SELECT Operations:** 5 found

---

### approval_votes

**Columns Used:**
- `and`
- `approvals`
- `comment`
- `create`
- `if`
- `new_status`
- `rejections`
- `request`
- `request_id`
- `result`
- `return`
- `vote`
- `vote_id`
- `voted_at`
- `voted_by`
- `votes`

**Referenced In:**
- `src\agent\approval_workflow.py`

**CREATE TABLE Statements:**
```sql
CREATE TABLE IF NOT EXISTS approval_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    voted_by VARCHAR(50) NOT NULL,
    vote ENUM('approved', 'rejected') NOT NULL,
    comment TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES change_approval_requests(request_id) ON DELETE CASCADE,
    UNIQUE KEY unique_vote (request_id, voted_by),
    INDEX idx_request (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

```sql
CREATE TABLE IF NOT EXISTS approval_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    voted_by VARCHAR(50) NOT NULL,
    vote ENUM('approved', 'rejected') NOT NULL,
    comment TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES change_approval_requests(request_id) ON DELETE CASCADE,
    UNIQUE KEY unique_vote (request_id, voted_by),
    INDEX idx_request (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

```sql
AND requested_by = %s
        """
        
        self.cursor.execute(query, (request_id, cancelled_by))
        self.db.commit()
        
        if self.cursor.rowcount > 0:
            logger.info(f"Approval request {request_id} cancelled by {cancelled_by}")
            return True
        
        return False


# Create votes table
CREATE_VOTES_TABLE = """
CREATE TABLE IF NOT EXISTS approval_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    voted_by VARCH
... (truncated)
```

**INSERT Operations:** 3 found

**SELECT Operations:** 8 found

---

### audit_log

**Columns Used:**
- `action`
- `al`
- `as`
- `basel`
- `conn`
- `cursor`
- `cv`
- `d`
- `description`
- `detail`
- `details`
- `dictionary`
- `endpo`
- `event_id`
- `event_type`
- `f`
- `i`
- `id`
- `if`
- `instance_id`
- `instance_name`
- `is_`
- `jo`
- `join`
- `limit`
- `match`
- `params`
- `property_key`
- `query`
- `ra`
- `rowcount`
- `server_properties_basel`
- `spv`
- `stance_id`
- `status_code`
- `t`
- `timestamp`
- `user`
- `where_clause`
- `where_conditions`

**Referenced In:**
- `src\api\audit_log_endpoints.py`
- `src\api\enhanced_endpoints.py`
- `src\api\plugin_configurator_endpoints.py`

**INSERT Operations:** 9 found

**SELECT Operations:** 12 found

---

### backup

**Columns Used:**
- `_restore_config_from_backup`
- `backed_up_at`
- `backup`
- `backup_id`
- `bool`
- `config`
- `config_file_id`
- `create`
- `created`
- `created_at`
- `def`
- `determ`
- `e`
- `endpo`
- `error`
- `except`
- `exception`
- `f`
- `failed`
- `fetch`
- `file`
- `file_path`
- `for`
- `id`
- `if`
- `info`
- `int`
- `last_id`
- `last_insert_id`
- `limit`
- `logger`
- `none`
- `ok`
- `otherw`
- `params`
- `plug`
- `plugin_id`
- `restore`
- `restore_to_path`
- `result`
- `return`
- `self`
- `stance_id`
- `str`
- `target_path`
- `to`
- `true`

**Referenced In:**
- `src\agent\database_methods_extension.py`

**SELECT Operations:** 1 found

---

### baseline_snapshots

**Columns Used:**
- `config_file`
- `config_key`
- `config_type`
- `created_at`
- `expected_value`
- `notes`
- `plugin_name`
- `snapshot_id`
- `value_type`

**Referenced In:**
- `scripts\load_baselines.py`

**INSERT Operations:** 3 found

---

### change_approval_requests

**Columns Used:**
- `approval_count`
- `auto_approve_after_hours`
- `change_data`
- `change_description`
- `change_type`
- `changed_at`
- `changed_by`
- `config_key`
- `created_at`
- `deployed_at`
- `deployed_by`
- `deployment_status`
- `deployment_type`
- `elapsed`
- `from_version`
- `hour`
- `hours_elapsed`
- `id`
- `if`
- `limit`
- `metric_name`
- `notification_type`
- `now`
- `params`
- `pend`
- `plug`
- `plugin_name`
- `priority`
- `query`
- `recorded_at`
- `rejection_count`
- `request`
- `request_id`
- `requested_by`
- `required_approvals`
- `resolved_at`
- `snapshot_at`
- `stance_id`
- `status`
- `str`
- `timestampdiff`
- `to_version`
- `voted_at`

**Referenced In:**
- `src\agent\approval_workflow.py`
- `src\web\api.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 10 found

**UPDATE Operations:** 6 found

---

### cicd_webhook_events

**Columns Used:**
- `action_taken`
- `created_at`
- `event_id`
- `limit`
- `pend`
- `priority`
- `processed_at`
- `received_at`
- `status`

**Referenced In:**
- `src\agent\agent_cicd_methods.py`
- `src\agent\agent_update_methods.py`

**SELECT Operations:** 6 found

**UPDATE Operations:** 17 found

---

### config_baselines

**Columns Used:**
- `config_key`
- `config_value`
- `file_path`
- `plugin_name`

**Referenced In:**
- `src\agent\variance_detector.py`

**SELECT Operations:** 2 found

---

### config_change_history

**Columns Used:**
- `batch_id`
- `change`
- `change_id`
- `change_reason`
- `change_source`
- `change_type`
- `changed_at`
- `changed_by`
- `concat`
- `config_change_h`
- `config_file`
- `config_key`
- `count`
- `created_at`
- `d`
- `date`
- `deployed_at`
- `deployed_by`
- `deployment_id`
- `deployment_status`
- `deployment_type`
- `description`
- `detail`
- `event`
- `event_type`
- `from_version`
- `get_change_stat`
- `i`
- `id`
- `if`
- `instance_id`
- `is`
- `lifecycle`
- `limit`
- `m`
- `metric_name`
- `new_value`
- `not`
- `notification_type`
- `null`
- `old_value`
- `params`
- `plug`
- `plugin_lifecycle`
- `plugin_name`
- `query`
- `ra`
- `recorded_at`
- `snapshot_at`
- `stance_id`
- `stat`
- `status`
- `status_code`
- `str`
- `timestamp`
- `to_version`
- `total`
- `user`

**Referenced In:**
- `src\agent\conflict_detector.py`
- `src\api\dashboard_endpoints.py`
- `src\database\db_access.py`
- `src\web\api.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 23 found

---

### config_drift_log

**Columns Used:**
- `_active`
- `actual_value`
- `config_file`
- `config_key`
- `config_type`
- `d`
- `detected_at`
- `drift_id`
- `endpo`
- `exist`
- `expected_value`
- `get_plug`
- `insert`
- `instance_id`
- `limit`
- `pend`
- `plug`
- `plugin_name`
- `priority`
- `resolution_notes`
- `resolved_at`
- `reviewed_at`
- `reviewed_by`
- `server_name`
- `severity`
- `status`
- `tags`

**Referenced In:**
- `scripts\drift_scanner_service.py`
- `scripts\enforce_config.py`
- `scripts\populate_config_cache.py`
- `src\web\api.py`

**INSERT Operations:** 6 found

**SELECT Operations:** 9 found

**UPDATE Operations:** 9 found

---

### config_key_migrations

**Columns Used:**
- `_breaking`
- `change_type`
- `changed_at`
- `changed_by`
- `config_key`
- `created_at`
- `deployed_at`
- `deployed_by`
- `deployment_status`
- `deployment_type`
- `from_version`
- `id`
- `if`
- `limit`
- `metric_name`
- `notification_type`
- `params`
- `plug`
- `plugin_name`
- `query`
- `recorded_at`
- `snapshot_at`
- `stance_id`
- `status`
- `str`
- `to_version`

**Referenced In:**
- `src\agent\compatibility_checker.py`
- `src\database\db_access.py`
- `src\web\api.py`

**SELECT Operations:** 12 found

---

### config_keys

**Columns Used:**
- `_active`
- `comment_inline`
- `comment_pre`
- `config_file`
- `config_filename`
- `config_key`
- `cont`
- `created_at`
- `data_type`
- `determ`
- `ex`
- `file_type`
- `id`
- `key_path`
- `observed_value`
- `plug`
- `plugin_default_value`
- `plugin_id`
- `priority`
- `whitespace_prefix`

**Referenced In:**
- `scripts\parse_markdown_to_sql.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 3 found

---

### config_locks

**Columns Used:**
- `by`
- `config_key`
- `count`
- `create`
- `created_at`
- `exist`
- `existing_lock`
- `if`
- `instance_id`
- `l`
- `lock_duration_m`
- `lock_id`
- `locked_at`
- `locked_by`
- `locked_until`
- `params`
- `plug`
- `plugin_name`
- `query`
- `rowcount`
- `stance_id`

**Referenced In:**
- `src\agent\conflict_detector.py`

**CREATE TABLE Statements:**
```sql
CREATE TABLE IF NOT EXISTS config_locks (
    lock_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    locked_by VARCHAR(50) NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_until TIMESTAMP NOT NULL,
    INDEX idx_lock_key (instance_id, plugin_name, config_key),
    INDEX idx_lock_expiry (locked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

```sql
CREATE TABLE IF NOT EXISTS config_locks (
    lock_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    locked_by VARCHAR(50) NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_until TIMESTAMP NOT NULL,
    INDEX idx_lock_key (instance_id, plugin_name, config_key),
    INDEX idx_lock_expiry (locked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**INSERT Operations:** 3 found

**SELECT Operations:** 5 found

**UPDATE Operations:** 3 found

**DELETE Operations:** 4 found

---

### config_rules

**Columns Used:**
- `_active`
- `_calculate_scope_score`
- `_enabled`
- `_get_available_keys`
- `a`
- `add`
- `all`
- `any`
- `append`
- `args`
- `at`
- `available`
- `available_keys`
- `base`
- `based`
- `best`
- `best_rule`
- `bonus`
- `by`
- `calculate`
- `config`
- `config_file`
- `config_key`
- `config_keys`
- `config_type`
- `config_value`
- `configcontext`
- `context`
- `cr`
- `created_at`
- `created_by`
- `ctx`
- `cursor`
- `db`
- `debug`
- `def`
- `desc`
- `dict`
- `display_order`
- `drift_id`
- `each`
- `endpo`
- `exist`
- `expected_value`
- `f`
- `file`
- `filename`
- `first`
- `for`
- `get`
- `get_plug`
- `global`
- `hierarchy`
- `higher`
- `identifier`
- `if`
- `ig`
- `in`
- `instance`
- `instance_count`
- `instance_id`
- `int`
- `is_active`
- `is_variable`
- `jo`
- `key`
- `keys`
- `lambda`
- `least`
- `len`
- `level`
- `limit`
- `list`
- `logger`
- `mapping`
- `matches`
- `matching`
- `meta`
- `meta_tag`
- `meta_tag_id`
- `meta_tag_ids`
- `more`
- `most`
- `mtc`
- `multiple`
- `none`
- `not`
- `notes`
- `of`
- `on`
- `once`
- `optional`
- `other`
- `over`
- `p`
- `player`
- `player_uuid`
- `plug`
- `plugin`
- `plugin_id`
- `plugin_name`
- `primary`
- `priority`
- `pv`
- `query`
- `rank`
- `rank_name`
- `resolve`
- `resolve_all_configs`
- `resolve_config`
- `resolved`
- `resolvedconfig`
- `result`
- `return`
- `returns`
- `reverse`
- `rule`
- `rule_id`
- `rules`
- `s`
- `same`
- `scope`
- `scope_identifier`
- `scope_level`
- `scope_score`
- `scope_scores`
- `scope_selector`
- `scope_type`
- `score`
- `scored_rules`
- `scores`
- `selected`
- `self`
- `server`
- `server_name`
- `set`
- `sort`
- `specific`
- `specificity`
- `stance_id`
- `str`
- `tag`
- `tags`
- `the`
- `this`
- `to`
- `true`
- `update_available`
- `updated_at`
- `value_type`
- `variable_name`
- `wins`
- `within`
- `without`
- `world`
- `world_name`
- `x`

**Referenced In:**
- `scripts\drift_scanner_service.py`
- `scripts\load_baselines.py`
- `scripts\populate_config_cache.py`
- `src\core\hierarchy_resolver.py`
- `src\database\db_access.py`
- `src\engine\hierarchy_resolver.py`
- `src\parsers\baseline_parser.py`
- `src\web\api.py`

**INSERT Operations:** 13 found

**SELECT Operations:** 46 found

**UPDATE Operations:** 7 found

---

### config_templates

**Columns Used:**
- `change_type`
- `changed_at`
- `changed_by`
- `clone_from_`
- `config_key`
- `created_at`
- `created_by`
- `deployed_at`
- `deployed_by`
- `deployment_status`
- `deployment_type`
- `description`
- `existing`
- `from_version`
- `id`
- `if`
- `last_used_at`
- `limit`
- `metric_name`
- `notification_type`
- `params`
- `plug`
- `plugin_name`
- `query`
- `recorded_at`
- `result`
- `rowcount`
- `snapshot_at`
- `source`
- `stalled_plug`
- `stance_id`
- `status`
- `str`
- `tag`
- `tags`
- `template_data`
- `template_id`
- `template_name`
- `to_version`
- `usage_count`

**Referenced In:**
- `src\agent\config_templates.py`
- `src\web\api.py`

**INSERT Operations:** 2 found

**SELECT Operations:** 6 found

**UPDATE Operations:** 4 found

**DELETE Operations:** 2 found

---

### config_variables

**Columns Used:**
- `_active`
- `config_file`
- `config_key`
- `instance_id`
- `is_active`
- `limit`
- `plugin_name`
- `priority`
- `result`
- `scope_identifier`
- `scope_type`
- `variable_name`
- `variable_value`
- `variables`

**Referenced In:**
- `scripts\drift_scanner_service.py`
- `scripts\populate_config_cache.py`
- `src\database\db_access.py`

**SELECT Operations:** 8 found

---

### config_variance_cache

**Columns Used:**
- `_drift`
- `_enabled`
- `actual_value`
- `cache_id`
- `cached_configs`
- `changed_at`
- `config`
- `config_drifts`
- `config_file`
- `config_key`
- `config_type`
- `drift_count`
- `drifts`
- `expected_value`
- `ig`
- `instance_id`
- `is_active`
- `is_baseline`
- `is_drift`
- `last_scanned`
- `limit`
- `mtc`
- `plug`
- `plugin_id`
- `plugin_name`
- `result`
- `scope`
- `server_name`
- `value_type`
- `variance_classification`
- `variance_type`

**Referenced In:**
- `scripts\drift_scanner_service.py`
- `scripts\enforce_config.py`
- `scripts\populate_config_cache.py`
- `src\api\dashboard_endpoints.py`
- `src\database\db_access.py`
- `src\web\api.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 25 found

**UPDATE Operations:** 6 found

---

### config_variance_detected

**Columns Used:**
- `actual_value`
- `as`
- `basel`
- `baseline_path`
- `config_key`
- `conn`
- `cursor`
- `cv`
- `detail`
- `dictionary`
- `expected_value`
- `has_plug`
- `i`
- `if`
- `instance_id`
- `instance_name`
- `is_intentional`
- `jo`
- `last_updated`
- `params`
- `plug`
- `plugin`
- `plugin_`
- `plugin_id`
- `ra`
- `reason`
- `result`
- `row`
- `server_name`
- `status_code`
- `substring_`
- `tags`
- `target`
- `tentional_only`
- `update_available`
- `variance_id`

**Referenced In:**
- `src\api\plugin_configurator_endpoints.py`

**SELECT Operations:** 7 found

**UPDATE Operations:** 2 found

---

### config_variance_history

**Columns Used:**
- `change_type`
- `changed_at`
- `changed_by`
- `config_key`
- `created_at`
- `deployed_at`
- `deployed_by`
- `deployment_status`
- `deployment_type`
- `from_version`
- `id`
- `if`
- `limit`
- `metric_name`
- `notification_type`
- `params`
- `plug`
- `plugin_name`
- `query`
- `recorded_at`
- `snapshot_at`
- `stance_id`
- `status`
- `str`
- `to_version`

**Referenced In:**
- `src\web\api.py`

**SELECT Operations:** 1 found

---

### config_variances

**Columns Used:**
- `actual_value`
- `all`
- `as`
- `basel`
- `baseline_value`
- `config_key`
- `conn`
- `cursor`
- `cv`
- `d`
- `deleted_count`
- `detail`
- `detected_at`
- `dictionary`
- `endpo`
- `exist`
- `existing`
- `f`
- `for`
- `i`
- `id`
- `if`
- `insert`
- `instance_id`
- `instance_name`
- `is_`
- `is_intentional`
- `jo`
- `join`
- `l`
- `limit`
- `plug`
- `plugin_l`
- `plugin_name`
- `property_key`
- `query`
- `ra`
- `reg`
- `rowcount`
- `scan_and_reg`
- `server_name`
- `server_properties_basel`
- `spv`
- `stance`
- `stance_id`
- `status_code`
- `t`
- `timestamp`
- `total_variances`
- `variance_id`
- `variance_value`

**Referenced In:**
- `src\agent\variance_detector.py`
- `src\api\enhanced_endpoints.py`
- `src\api\variance_endpoints.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 7 found

**UPDATE Operations:** 6 found

**DELETE Operations:** 3 found

---

### datapack_deployment_queue

**Columns Used:**
- `created_at`
- `limit`
- `pend`
- `priority`
- `scheduled_for`
- `status`

**Referenced In:**
- `src\agent\agent_update_methods.py`

**SELECT Operations:** 3 found

---

### datapacks

**Columns Used:**
- `all`
- `an`
- `as`
- `basel`
- `bool`
- `change_type`
- `changed_by`
- `conn`
- `created_at`
- `currently`
- `cursor`
- `cv`
- `d`
- `datapack`
- `datapack_id`
- `datapack_name`
- `description`
- `detail`
- `dictionary`
- `difficulty`
- `display_name`
- `endpo`
- `exist`
- `existing`
- `f`
- `file_hash`
- `file_name`
- `for`
- `gamemode`
- `get_`
- `i`
- `id`
- `if`
- `insert`
- `instance_id`
- `is_`
- `is_enabled`
- `jo`
- `join`
- `l`
- `last_checked_at`
- `last_updated_at`
- `level_name`
- `limit`
- `max_players`
- `name`
- `pack_format`
- `params`
- `plug`
- `plugin_name`
- `priority`
- `properties_json`
- `property_key`
- `pvp`
- `query`
- `ra`
- `reg`
- `rowcount`
- `scan_and_reg`
- `server_properties_basel`
- `simulation_d`
- `simulation_distance`
- `spawn_protection`
- `spv`
- `stance`
- `stance_id`
- `status`
- `status_code`
- `t`
- `timestamp`
- `to`
- `total`
- `total_datapacks`
- `track`
- `un`
- `version`
- `view_d`
- `view_distance`
- `world_name`
- `world_path`

**Referenced In:**
- `src\agent\agent_database_methods.py`
- `src\agent\datapack_discovery.py`
- `src\api\enhanced_endpoints.py`

**INSERT Operations:** 6 found

**SELECT Operations:** 9 found

**UPDATE Operations:** 3 found

---

### deployment_history

**Columns Used:**
- `change_type`
- `changed_at`
- `changed_by`
- `completed_at`
- `config_key`
- `created_at`
- `current_version`
- `deployed_at`
- `deployed_by`
- `deployment`
- `deployment_id`
- `deployment_notes`
- `deployment_status`
- `deployment_type`
- `error_message`
- `from_version`
- `id`
- `if`
- `instances_json`
- `limit`
- `metric_name`
- `new_version`
- `notification_type`
- `null`
- `params`
- `pend`
- `plug`
- `plugin_name`
- `query`
- `recorded_at`
- `result`
- `scope`
- `snapshot_at`
- `stance_id`
- `status`
- `str`
- `target_instances`
- `timestamp`
- `to_version`
- `type`

**Referenced In:**
- `src\agent\performance_metrics.py`
- `src\api\dashboard_endpoints.py`
- `src\database\db_access.py`
- `src\web\api.py`

**INSERT Operations:** 2 found

**SELECT Operations:** 6 found

**UPDATE Operations:** 7 found

---

### deployment_logs

**Columns Used:**
- `created_at`
- `deployment_id`
- `detail`
- `dl`
- `dq`
- `f`
- `i`
- `id`
- `instance_id`
- `instance_name`
- `limit`
- `message`
- `params`
- `plugin_name`
- `queue_entry`
- `ra`
- `stat`
- `stats`
- `status`
- `status_code`
- `timestamp`

**Referenced In:**
- `src\agent\config_deployer.py`
- `src\api\deployment_endpoints.py`
- `src\api\update_manager_endpoints.py`

**INSERT Operations:** 2 found

**SELECT Operations:** 6 found

---

### deployment_queue

**Columns Used:**
- `config_content`
- `created_at`
- `deployment_id`
- `deployment_notes`
- `detail`
- `dl`
- `dq`
- `f`
- `id`
- `instance_count`
- `instance_id`
- `instance_ids`
- `json_length`
- `limit`
- `params`
- `pend`
- `plugin_id`
- `plugin_name`
- `queue_entry`
- `ra`
- `requested_by`
- `stat`
- `stats`
- `status`
- `status_code`
- `updated_at`

**Referenced In:**
- `src\agent\config_deployer.py`
- `src\agent\conflict_detector.py`
- `src\agent\performance_metrics.py`
- `src\agent\scheduled_tasks.py`
- `src\api\deployment_endpoints.py`
- `src\api\enhanced_endpoints.py`
- `src\api\plugin_configurator_endpoints.py`
- `src\api\update_manager_endpoints.py`

**INSERT Operations:** 14 found

**SELECT Operations:** 20 found

**UPDATE Operations:** 3 found

---

### discovery_items

**Columns Used:**
- `_log_d`
- `action`
- `an`
- `current_run_id`
- `d`
- `discovered_at`
- `insert`
- `item_id`
- `item_path`
- `item_type`
- `run_id`

**Referenced In:**
- `src\agent\agent_database_methods.py`

**INSERT Operations:** 3 found

---

### discovery_runs

**Columns Used:**
- `_log_d`
- `an`
- `completed_at`
- `current_run_id`
- `d`
- `insert`
- `run_id`
- `run_type`
- `server_name`
- `started_at`
- `status`

**Referenced In:**
- `src\agent\agent_database_methods.py`

**INSERT Operations:** 3 found

**UPDATE Operations:** 3 found

---

### endpoint_config_backups

**Columns Used:**
- `backed_up_at`
- `backed_up_by`
- `backup`
- `backup_content`
- `backup_id`
- `backup_metadata`
- `backup_reason`
- `config_file_id`
- `config_file_path`
- `content_hash`
- `created_at`
- `determ`
- `endpo`
- `file_content`
- `file_hash`
- `file_size_bytes`
- `if`
- `instance_id`
- `length`
- `limit`
- `otherw`
- `params`
- `plug`
- `plugin_id`
- `result`
- `stance_id`
- `target_path`

**Referenced In:**
- `src\agent\database_methods_extension.py`
- `src\utils\config_backup.py`

**INSERT Operations:** 6 found

**SELECT Operations:** 17 found

**DELETE Operations:** 3 found

---

### endpoint_config_change_history

**Columns Used:**
- `backup_id`
- `change_details`
- `change_type`
- `changed_at`
- `changed_by`
- `config_file_id`
- `instance_id`

**Referenced In:**
- `src\agent\database_methods_extension.py`

**INSERT Operations:** 3 found

---

### endpoint_config_files

**Columns Used:**
- `_create_config_backup`
- `args`
- `backup`
- `cf`
- `config`
- `config_file_id`
- `create`
- `current_hash`
- `database`
- `def`
- `display_name`
- `e`
- `error`
- `except`
- `exception`
- `f`
- `failed`
- `fetch`
- `file`
- `file_path`
- `file_size`
- `file_type`
- `first_discovered`
- `i`
- `id`
- `if`
- `in`
- `instance_base_path`
- `instance_folder_name`
- `instance_id`
- `instance_name`
- `int`
- `last_discovered`
- `last_id`
- `last_insert_id`
- `logger`
- `manual`
- `none`
- `of`
- `operations`
- `optional`
- `p`
- `plug`
- `plugin_display_name`
- `plugin_id`
- `plugin_name`
- `reason`
- `register`
- `result`
- `return`
- `self`
- `str`
- `to`
- `true`

**Referenced In:**
- `src\agent\agent_extensions.py`
- `src\agent\database_methods_extension.py`
- `src\utils\config_backup.py`

**INSERT Operations:** 6 found

**SELECT Operations:** 13 found

**UPDATE Operations:** 6 found

---

### for

**Columns Used:**
- `__name__`
- `_active`
- `_enabled`
- `active_instances`
- `affected_`
- `all`
- `amp_`
- `an`
- `as`
- `backed_up_at`
- `backup`
- `backup_id`
- `basel`
- `baseline_path`
- `baseline_value`
- `bool`
- `by`
- `category_name`
- `cha`
- `chain`
- `change`
- `change_id`
- `change_type`
- `changed_at`
- `changed_by`
- `changes`
- `check_all_plug`
- `check_plug`
- `component`
- `config_change_h`
- `config_file`
- `config_file_id`
- `config_key`
- `config_type`
- `conn`
- `cont`
- `count`
- `cr`
- `create_baseline_from_`
- `created_at`
- `currently`
- `cursor`
- `cv`
- `d`
- `data`
- `datapack`
- `datapack_id`
- `datapack_name`
- `date`
- `deployed_at`
- `deployed_by`
- `deployment_id`
- `deployment_scope`
- `deployment_status`
- `deployment_type`
- `description`
- `detail`
- `determ`
- `dictionary`
- `difficulty`
- `dism`
- `display_order`
- `dist`
- `dl`
- `dq`
- `drift_id`
- `endpo`
- `exist`
- `existing`
- `existing_lock`
- `f`
- `fetch`
- `file_hash`
- `file_name`
- `file_path`
- `for`
- `from_version`
- `gamemode`
- `get`
- `get_`
- `get_change_stat`
- `get_plug`
- `getting`
- `group_name`
- `h`
- `has_plug`
- `i`
- `id`
- `if`
- `ig`
- `insert`
- `instance`
- `instance_count`
- `instance_id`
- `instance_info`
- `instance_name`
- `int`
- `is_`
- `is_active`
- `is_deprecated`
- `is_enabled`
- `is_intentional`
- `jo`
- `join`
- `key`
- `l`
- `last_checked_at`
- `last_heartbeat`
- `last_seen`
- `last_updated_at`
- `latest_version`
- `level_name`
- `limit`
- `locked_at`
- `locked_by`
- `locked_until`
- `mark`
- `matrix`
- `max_players`
- `meta_tag_h`
- `metric_name`
- `mtc`
- `name`
- `next_run`
- `notification_type`
- `otherw`
- `outdated_plugins`
- `p`
- `pack_format`
- `params`
- `parent_tag_id`
- `plug`
- `plugin`
- `plugin_`
- `plugin_id`
- `plugin_l`
- `plugin_name`
- `plugin_row`
- `plugins`
- `priority`
- `properties`
- `properties_json`
- `property_key`
- `property_value`
- `pv`
- `pvp`
- `query`
- `queue_entry`
- `ra`
- `recorded_at`
- `reference`
- `reg`
- `result`
- `row`
- `rowcount`
- `rule_id`
- `scan_`
- `scan_and_reg`
- `schedule_value`
- `scope_identifier`
- `scope_type`
- `server_name`
- `server_properties_basel`
- `set`
- `simulation_d`
- `simulation_distance`
- `snapshot_at`
- `source_type`
- `spawn_protection`
- `spv`
- `stance`
- `stance_`
- `stance_id`
- `stance_plug`
- `stat`
- `stats`
- `status`
- `status_code`
- `str`
- `substring_`
- `t`
- `t1`
- `table_schema`
- `tag_id`
- `tag_name`
- `tags`
- `target`
- `target_instances`
- `target_path`
- `task_name`
- `tc`
- `tentional_only`
- `th`
- `timestamp`
- `to`
- `to_version`
- `total_datapacks`
- `total_plugins`
- `total_variances`
- `track`
- `un`
- `update_available`
- `updated_at`
- `updates_found`
- `upsert_`
- `usage_count`
- `value`
- `variable_name`
- `variables`
- `variance_classification`
- `variance_id`
- `variance_value`
- `version`
- `view_d`
- `view_distance`
- `world_name`
- `world_path`

**Referenced In:**
- `src\agent\conflict_detector.py`

**CREATE TABLE Statements:**
```sql
# Create table for locks if not exists
CREATE_LOCKS_TABLE =
```

---

### information_schema

**Columns Used:**
- `data_length`
- `index_length`
- `round`
- `size_mb`
- `table_name`
- `table_schema`

**Referenced In:**
- `src\agent\performance_metrics.py`

**SELECT Operations:** 3 found

---

### installed_plugins

**Columns Used:**
- `clone_from_`
- `config_data`
- `existing`
- `instance_id`
- `plug`
- `plugin_name`
- `query`
- `result`
- `rowcount`
- `source`
- `stalled_plug`
- `stance_id`
- `str`
- `template_id`

**Referenced In:**
- `src\agent\config_templates.py`
- `src\agent\performance_metrics.py`

**SELECT Operations:** 5 found

---

### instance_datapacks

**Columns Used:**
- `an`
- `bool`
- `change_type`
- `changed_by`
- `currently`
- `custom_source`
- `d`
- `datapack`
- `datapack_id`
- `datapack_name`
- `description`
- `difficulty`
- `discovered_at`
- `file_hash`
- `file_name`
- `file_path`
- `file_size`
- `first_discovered_at`
- `gamemode`
- `get_`
- `github_repo`
- `i`
- `id`
- `if`
- `insert`
- `installed_at`
- `instance_id`
- `instance_name`
- `is_enabled`
- `l`
- `last_checked_at`
- `last_seen_at`
- `last_updated_at`
- `level_name`
- `ma`
- `max_players`
- `modr`
- `modrinth_id`
- `name`
- `params`
- `parser`
- `plug`
- `plugin_name`
- `po`
- `properties_json`
- `pvp`
- `reg`
- `result`
- `simulation_d`
- `simulation_distance`
- `spawn_protection`
- `stance_id`
- `to`
- `total`
- `track`
- `un`
- `version`
- `view_d`
- `view_distance`
- `world_name`
- `world_path`

**Referenced In:**
- `scripts\modrinth_sync.py`
- `scripts\populate_plugin_metadata.py`
- `src\agent\agent_database_methods.py`
- `src\api\dashboard_endpoints.py`
- `src\database\db_access.py`
- `src\web\api.py`

**INSERT Operations:** 8 found

**SELECT Operations:** 13 found

**UPDATE Operations:** 6 found

**DELETE Operations:** 3 found

---

### instance_group_members

**Columns Used:**
- `_enabled`
- `group_name`
- `ig`
- `igm`
- `instance_id`
- `is_active`
- `mtc`
- `plug`
- `plugin_id`
- `plugin_name`

**Referenced In:**
- `src\database\db_access.py`

**SELECT Operations:** 3 found

---

### instance_groups

**Columns Used:**
- `_active`
- `_enabled`
- `config_file`
- `config_key`
- `description`
- `group_name`
- `group_type`
- `ig`
- `instance_id`
- `is_active`
- `member_count`
- `mtc`
- `plug`
- `plugin_id`
- `plugin_name`
- `scope_type`

**Referenced In:**
- `src\database\db_access.py`
- `src\web\api.py`

**SELECT Operations:** 6 found

---

### instance_meta_tags

**Columns Used:**
- `__name__`
- `applied_at`
- `applied_by`
- `c`
- `category_display_name`
- `category_id`
- `category_name`
- `color`
- `confidence_score`
- `conn`
- `count`
- `cursor`
- `d`
- `detail`
- `dictionary`
- `display_name`
- `f`
- `fetch`
- `getting`
- `h`
- `i`
- `icon`
- `id`
- `imt`
- `insert`
- `instance`
- `instance_id`
- `instance_name`
- `is_auto_detected`
- `is_deprecated`
- `jo`
- `meta_tag_h`
- `mt`
- `ra`
- `row`
- `rowcount`
- `status_code`
- `t`
- `t1`
- `tag_id`
- `tag_name`
- `tc`
- `to`
- `usage_count`

**Referenced In:**
- `src\agent\agent_database_methods.py`
- `src\api\tag_manager_endpoints.py`
- `src\engine\hierarchy_resolver.py`

**INSERT Operations:** 11 found

**SELECT Operations:** 10 found

**DELETE Operations:** 8 found

---

### instance_plugins

**Columns Used:**
- `_enabled`
- `affected_`
- `all`
- `an`
- `available_version`
- `bool`
- `conn`
- `cont`
- `currently`
- `cursor`
- `d`
- `datapack`
- `datapack_name`
- `deployment_scope`
- `detail`
- `dictionary`
- `difficulty`
- `dist`
- `file_hash`
- `file_modified_at`
- `file_name`
- `file_path`
- `file_size`
- `first_discovered_at`
- `gamemode`
- `get_`
- `i`
- `ig`
- `insert`
- `install_count`
- `installation_method`
- `installed_at`
- `installed_version`
- `instance_count`
- `instance_id`
- `instance_name`
- `ip`
- `is_active`
- `is_enabled`
- `is_installed`
- `is_outdated`
- `jo`
- `join`
- `l`
- `last_checked_at`
- `last_seen_at`
- `last_updated_at`
- `latest_version`
- `level_name`
- `max_players`
- `mtc`
- `name`
- `p`
- `plug`
- `plugin`
- `plugin_id`
- `plugin_name`
- `plugin_row`
- `properties_json`
- `pvp`
- `ra`
- `reg`
- `row`
- `server_name`
- `simulation_d`
- `simulation_distance`
- `spawn_protection`
- `stalled_version`
- `stance_id`
- `stance_plug`
- `status_code`
- `tag_id`
- `target_instances`
- `th`
- `to`
- `track`
- `un`
- `update_available`
- `version`
- `view_d`
- `view_distance`
- `world_name`

**Referenced In:**
- `scripts\populate_plugin_metadata.py`
- `src\agent\agent_cicd_methods.py`
- `src\agent\agent_database_methods.py`
- `src\agent\agent_update_methods.py`
- `src\api\update_manager_endpoints.py`
- `src\web\api.py`

**INSERT Operations:** 5 found

**SELECT Operations:** 28 found

**UPDATE Operations:** 12 found

---

### instance_server_properties

**Columns Used:**
- `an`
- `bool`
- `currently`
- `datapack`
- `datapack_name`
- `difficulty`
- `enable_command_block`
- `file_hash`
- `file_name`
- `gamemode`
- `get_`
- `insert`
- `instance_id`
- `is_enabled`
- `l`
- `last_checked_at`
- `last_scanned_at`
- `last_updated_at`
- `level_name`
- `max_players`
- `plug`
- `properties_json`
- `pvp`
- `reg`
- `simulation_d`
- `simulation_distance`
- `spawn_protection`
- `stance_id`
- `to`
- `track`
- `un`
- `version`
- `view_d`
- `view_distance`
- `world_name`

**Referenced In:**
- `scripts\populate_plugin_metadata.py`
- `src\agent\agent_database_methods.py`
- `src\database\db_access.py`

**INSERT Operations:** 8 found

**SELECT Operations:** 5 found

---

### instance_tags

**Columns Used:**
- `_active`
- `_enabled`
- `as`
- `assigned_by`
- `basel`
- `config_file`
- `config_key`
- `config_type`
- `conn`
- `cursor`
- `cv`
- `d`
- `detail`
- `dictionary`
- `display_order`
- `drift_id`
- `endpo`
- `f`
- `get_plug`
- `i`
- `id`
- `if`
- `ig`
- `instance`
- `instance_id`
- `instance_name`
- `is_`
- `is_active`
- `it`
- `jo`
- `join`
- `limit`
- `meta_tag_id`
- `mt`
- `mtc`
- `plug`
- `plugin_id`
- `plugin_name`
- `priority`
- `property_key`
- `query`
- `ra`
- `rowcount`
- `rule_id`
- `scope`
- `server_name`
- `server_properties_basel`
- `set`
- `spv`
- `stance_id`
- `status_code`
- `t`
- `tag_id`
- `tag_name`
- `tags`
- `timestamp`
- `updated_at`
- `variance_classification`

**Referenced In:**
- `scripts\drift_scanner_service.py`
- `scripts\populate_config_cache.py`
- `src\api\dashboard_endpoints.py`
- `src\database\db_access.py`
- `src\web\api.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 12 found

**DELETE Operations:** 3 found

---

### instances

**Columns Used:**
- `_active`
- `_discover_plug`
- `_enabled`
- `_scan_`
- `active_instances`
- `affected_`
- `al`
- `all`
- `amp_`
- `amp_instance_id`
- `an`
- `as`
- `basel`
- `baseline_path`
- `baseline_value`
- `bool`
- `cha`
- `chain`
- `change_type`
- `changed_at`
- `changed_by`
- `check_m`
- `config_file_id`
- `config_key`
- `config_path`
- `conn`
- `cont`
- `created_at`
- `currently`
- `cursor`
- `cv`
- `d`
- `database`
- `datapack`
- `datapack_id`
- `datapack_name`
- `db_`
- `db_instance`
- `deployed_at`
- `deployment_id`
- `deployment_scope`
- `deployment_status`
- `description`
- `detail`
- `determ`
- `dictionary`
- `difficulty`
- `display_name`
- `dist`
- `dl`
- `drift_count`
- `drifts`
- `endpo`
- `event_type`
- `exist`
- `existing`
- `f`
- `fetch`
- `file_hash`
- `file_name`
- `folder_name`
- `for`
- `from_version`
- `gamemode`
- `get`
- `get_`
- `group_name`
- `h`
- `has_plug`
- `has_plugin`
- `i`
- `id`
- `if`
- `ig`
- `insert`
- `inst`
- `instance`
- `instance_id`
- `instance_info`
- `instance_name`
- `instance_path`
- `instance_short`
- `instance_type`
- `instances`
- `int`
- `internal_ip`
- `ip`
- `is`
- `is_`
- `is_active`
- `is_deprecated`
- `is_enabled`
- `is_installed`
- `is_intentional`
- `is_production`
- `jo`
- `join`
- `key`
- `l`
- `last_checked_at`
- `last_scanned`
- `last_seen`
- `last_seen_at`
- `last_updated_at`
- `latest_version`
- `level_name`
- `limit`
- `m`
- `match`
- `max_players`
- `mc_compat`
- `meta_tag_h`
- `metric_name`
- `minecraft_version`
- `mtc`
- `name`
- `not`
- `null`
- `p`
- `pack_format`
- `params`
- `parent_tag_id`
- `pend`
- `pi`
- `pl3xmap_version`
- `platform`
- `platform_`
- `platform_version`
- `plug`
- `plugin`
- `plugin_`
- `plugin_id`
- `plugin_l`
- `plugin_name`
- `plugins_dir`
- `port`
- `properties_json`
- `property_key`
- `pv`
- `pvp`
- `query`
- `queue_entry`
- `ra`
- `read`
- `reg`
- `result`
- `row`
- `rowcount`
- `scan_and_reg`
- `scann`
- `server_host`
- `server_name`
- `server_properties_basel`
- `simulation_d`
- `simulation_distance`
- `skipp`
- `spawn_protection`
- `spv`
- `stalled_version`
- `stance`
- `stance_`
- `stance_id`
- `stance_plug`
- `stat`
- `stats`
- `status`
- `status_code`
- `str`
- `substring_`
- `substring_index`
- `t`
- `t1`
- `tag_id`
- `tag_name`
- `tags`
- `target`
- `target_instances`
- `tc`
- `tentional_only`
- `th`
- `timestamp`
- `to`
- `to_version`
- `total`
- `total_datapacks`
- `total_variances`
- `track`
- `un`
- `update`
- `update_available`
- `upsert_`
- `usage_count`
- `user`
- `value`
- `variables`
- `variance_id`
- `variance_value`
- `version`
- `view_d`
- `view_distance`
- `warn`
- `where_clause`
- `where_conditions`
- `world_name`
- `world_path`

**Referenced In:**
- `scripts\drift_scanner_service.py`
- `scripts\enforce_config.py`
- `scripts\platform_version_tracker.py`
- `scripts\populate_config_cache.py`
- `src\agent\agent_cicd_methods.py`
- `src\agent\agent_database_methods.py`
- `src\agent\agent_extensions.py`
- `src\agent\agent_update_methods.py`
- `src\agent\compatibility_checker.py`
- `src\agent\config_deployer.py`
- `src\agent\performance_metrics.py`
- `src\agent\scheduled_tasks.py`
- `src\api\dashboard_endpoints.py`
- `src\api\plugin_configurator_endpoints.py`
- `src\api\tag_manager_endpoints.py`
- `src\database\db_access.py`
- `src\engine\hierarchy_resolver.py`
- `src\liveatlas\map_config_generator.py`
- `src\web\api.py`

**INSERT Operations:** 6 found

**SELECT Operations:** 76 found

**UPDATE Operations:** 4 found

---

### meta_tag_categories

**Columns Used:**
- `_active`
- `_enabled`
- `c`
- `category_id`
- `category_name`
- `color`
- `conn`
- `count`
- `cursor`
- `d`
- `description`
- `detail`
- `dictionary`
- `display_name`
- `display_order`
- `endpo`
- `ex`
- `f`
- `i`
- `icon`
- `ig`
- `insert`
- `instance_id`
- `is_active`
- `is_deprecated`
- `is_mult`
- `is_multiselect`
- `is_required`
- `max_order`
- `mtc`
- `plug`
- `plugin_id`
- `plugin_name`
- `ra`
- `rowcount`
- `rule_id`
- `set`
- `status_code`
- `t`
- `t1`
- `tag_id`
- `tc`
- `updated_at`
- `usage_count`

**Referenced In:**
- `src\api\tag_manager_endpoints.py`
- `src\web\api.py`

**INSERT Operations:** 7 found

**SELECT Operations:** 7 found

**UPDATE Operations:** 2 found

**DELETE Operations:** 2 found

---

### meta_tag_history

**Columns Used:**
- `action`
- `detail`
- `h`
- `insert`
- `instance_id`
- `meta_tag_h`
- `performed_by`
- `ra`
- `reason`
- `rowcount`
- `status_code`
- `tag_id`

**Referenced In:**
- `src\api\tag_manager_endpoints.py`

**INSERT Operations:** 7 found

---

### meta_tags

**Columns Used:**
- `__name__`
- `_active`
- `_enabled`
- `as`
- `basel`
- `c`
- `category_display_name`
- `category_id`
- `category_name`
- `color`
- `config_key`
- `conn`
- `count`
- `created_at`
- `created_by`
- `cursor`
- `cv`
- `d`
- `description`
- `detail`
- `dictionary`
- `display_name`
- `display_order`
- `drift_id`
- `endpo`
- `ex`
- `f`
- `fetch`
- `get_plug`
- `getting`
- `h`
- `i`
- `icon`
- `id`
- `if`
- `ig`
- `insert`
- `instance`
- `instance_id`
- `instance_name`
- `is_`
- `is_active`
- `is_deprecated`
- `is_intentional`
- `is_mult`
- `is_system_tag`
- `jo`
- `join`
- `limit`
- `meta_tag_h`
- `metadata_json`
- `mt`
- `mtc`
- `name`
- `p`
- `parent_tag_id`
- `plug`
- `plugin_`
- `plugin_id`
- `plugin_name`
- `priority`
- `property_key`
- `query`
- `ra`
- `replacement_tag_id`
- `row`
- `rowcount`
- `rule_id`
- `server_properties_basel`
- `set`
- `spv`
- `stance_id`
- `status_code`
- `t`
- `t1`
- `tag_description`
- `tag_id`
- `tag_name`
- `tag_type`
- `tags`
- `tc`
- `timestamp`
- `to`
- `update_available`
- `updated_at`
- `usage_count`
- `variance_classification`

**Referenced In:**
- `src\agent\agent_database_methods.py`
- `src\api\enhanced_endpoints.py`
- `src\api\plugin_configurator_endpoints.py`
- `src\api\tag_manager_endpoints.py`
- `src\database\db_access.py`
- `src\web\api.py`

**INSERT Operations:** 11 found

**SELECT Operations:** 27 found

**UPDATE Operations:** 9 found

**DELETE Operations:** 2 found

---

### notification_log

**Columns Used:**
- `change_type`
- `changed_at`
- `changed_by`
- `channels`
- `config_key`
- `created_at`
- `deployed_at`
- `deployed_by`
- `deployment_status`
- `deployment_type`
- `from_version`
- `id`
- `if`
- `limit`
- `message`
- `metadata`
- `metric_name`
- `notification_type`
- `params`
- `plug`
- `plugin_name`
- `priority`
- `query`
- `read_at`
- `read_by`
- `recorded_at`
- `related_entity_id`
- `related_entity_type`
- `sent_at`
- `snapshot_at`
- `stance_id`
- `status`
- `str`
- `title`
- `to_version`
- `unread_notifications`

**Referenced In:**
- `src\agent\notification_system.py`
- `src\agent\scheduled_tasks.py`
- `src\web\api.py`

**INSERT Operations:** 2 found

**SELECT Operations:** 9 found

**UPDATE Operations:** 8 found

**DELETE Operations:** 1 found

---

### pending

**Columns Used:**
- `change_type`
- `changed_at`
- `changed_by`
- `config_key`
- `created_at`
- `d`
- `deployed_at`
- `deployed_by`
- `deployment_status`
- `deployment_type`
- `from_version`
- `id`
- `if`
- `instance_id`
- `limit`
- `metric_name`
- `notification_type`
- `params`
- `pend`
- `plug`
- `plugin_name`
- `pv`
- `query`
- `recorded_at`
- `severity`
- `snapshot_at`
- `stance_id`
- `status`
- `str`
- `to_version`
- `update_available`

**Referenced In:**
- `src\core\cloud_storage.py`

**DELETE Operations:** 2 found

---

### player_config_overrides

**Columns Used:**
- `config_key`
- `config_value`
- `player_uuid`
- `plugin_id`
- `stance_id`

**Referenced In:**
- `src\engine\hierarchy_resolver.py`

**SELECT Operations:** 3 found

---

### plugin_instances

**Columns Used:**
- `as`
- `basel`
- `baseline_path`
- `config_hash`
- `config_path`
- `conn`
- `cursor`
- `detail`
- `dictionary`
- `has_plug`
- `i`
- `if`
- `instance`
- `instance_id`
- `instance_name`
- `is_intentional`
- `jo`
- `last_scanned`
- `params`
- `pi`
- `plug`
- `plugin`
- `plugin_`
- `plugin_id`
- `ra`
- `read`
- `result`
- `row`
- `status_code`
- `substring_`
- `tags`
- `target`
- `tentional_only`
- `update_available`

**Referenced In:**
- `src\api\plugin_configurator_endpoints.py`

**SELECT Operations:** 3 found

---

### plugin_meta_tags

**Columns Used:**
- `assigned_at`
- `is_intentional`
- `jo`
- `plug`
- `plugin_`
- `plugin_id`
- `row`
- `tag_id`
- `tags`

**Referenced In:**
- `src\api\plugin_configurator_endpoints.py`

**INSERT Operations:** 2 found

**DELETE Operations:** 1 found

---

### plugin_metadata

**Columns Used:**
- `max_mc_version`
- `metadata`
- `min_mc_version`
- `plug`
- `plugin_name`
- `required_plugins`
- `result`
- `supported_mc_versions`

**Referenced In:**
- `src\agent\compatibility_checker.py`

**SELECT Operations:** 6 found

---

### plugin_update_queue

**Columns Used:**
- `completed_at`
- `created_at`
- `created_by`
- `deployment_log`
- `download_url`
- `error_message`
- `failure_count`
- `from_version`
- `id`
- `limit`
- `pend`
- `plugin_id`
- `priority`
- `scheduled_for`
- `server_name`
- `started_at`
- `status`
- `success_count`
- `target_instances`
- `to_version`

**Referenced In:**
- `src\agent\agent_cicd_methods.py`
- `src\agent\agent_update_methods.py`

**INSERT Operations:** 6 found

**SELECT Operations:** 6 found

**UPDATE Operations:** 18 found

---

### plugin_versions

**Columns Used:**
- `affected_`
- `an`
- `bool`
- `checked_at`
- `conn`
- `cont`
- `current_version`
- `currently`
- `cursor`
- `datapack`
- `datapack_name`
- `deployment_scope`
- `determ`
- `dictionary`
- `difficulty`
- `dism`
- `dist`
- `file_hash`
- `file_name`
- `gamemode`
- `get_`
- `group_concat`
- `i`
- `id`
- `insert`
- `installed_version`
- `instance_id`
- `instances`
- `is_enabled`
- `is_intentional`
- `jar_filename`
- `jar_hash`
- `jo`
- `join`
- `l`
- `last_checked`
- `last_checked_at`
- `last_updated_at`
- `latest_version`
- `level_name`
- `mark`
- `max_players`
- `name`
- `needs_update`
- `new_version`
- `p`
- `parent_tag_id`
- `plug`
- `plugin`
- `plugin_`
- `plugin_id`
- `plugin_name`
- `plugin_update`
- `properties_json`
- `pv`
- `pvp`
- `reg`
- `separator`
- `simulation_d`
- `simulation_distance`
- `spawn_protection`
- `stance_id`
- `stance_plug`
- `t`
- `target`
- `target_instances`
- `timestamp`
- `to`
- `total_plugins`
- `track`
- `type`
- `un`
- `up_to_date`
- `update_available`
- `updates`
- `version`
- `version_id`
- `view_d`
- `view_distance`
- `world_name`

**Referenced In:**
- `src\agent\update_checker.py`
- `src\api\dashboard_endpoints.py`
- `src\api\enhanced_endpoints.py`
- `src\api\update_manager_endpoints.py`
- `src\database\db_access.py`
- `src\web\api.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 29 found

**UPDATE Operations:** 3 found

---

### plugins

**Columns Used:**
- `_discover_plug`
- `_enabled`
- `affected_`
- `affected_instances`
- `all`
- `an`
- `as`
- `author`
- `basel`
- `baseline_config_path`
- `baseline_path`
- `bool`
- `bukkit_id`
- `changed_at`
- `changelog_url`
- `check_all_plug`
- `check_plug`
- `cicd_provider`
- `cicd_url`
- `clone_from_`
- `config_file_id`
- `config_key_count`
- `config_type`
- `conn`
- `cont`
- `created_at`
- `current_stable_version`
- `current_version`
- `currently`
- `curseforge_id`
- `cursor`
- `d`
- `data`
- `database`
- `datapack`
- `datapack_name`
- `deployment_scope`
- `description`
- `detail`
- `determ`
- `dictionary`
- `difficulty`
- `discover`
- `discover_plug`
- `display_name`
- `dist`
- `docs_url`
- `existing`
- `f`
- `file_hash`
- `file_name`
- `first_seen_at`
- `for`
- `gamemode`
- `get_`
- `github_repo`
- `group_concat`
- `hangar_slug`
- `has_cicd`
- `has_plug`
- `i`
- `id`
- `if`
- `ig`
- `insert`
- `instance_count`
- `instance_id`
- `instance_name`
- `is_active`
- `is_enabled`
- `is_installed`
- `is_intentional`
- `is_paid`
- `is_premium`
- `jo`
- `join`
- `l`
- `last_available_version_at`
- `last_checked_at`
- `last_update_check_at`
- `last_updated_at`
- `latest_release_date`
- `latest_version`
- `level_name`
- `license`
- `limit`
- `m`
- `max_players`
- `modr`
- `modrinth_id`
- `mtc`
- `name`
- `outdated_plugins`
- `p`
- `params`
- `parent_tag_id`
- `platform`
- `plug`
- `plugin`
- `plugin_`
- `plugin_id`
- `plugin_name`
- `plugin_page_url`
- `plugin_row`
- `plugins`
- `plugins_dir`
- `priority`
- `properties_json`
- `pus`
- `pv`
- `pvp`
- `query`
- `ra`
- `reg`
- `release_date`
- `result`
- `row`
- `rowcount`
- `scan_all_plug`
- `server_name`
- `simulation_d`
- `simulation_distance`
- `source`
- `source_identifier`
- `source_type`
- `source_url`
- `spawn_protection`
- `spigot_id`
- `stalled_plug`
- `stalled_version`
- `stance_id`
- `stance_plug`
- `status`
- `status_code`
- `str`
- `substring_`
- `t`
- `tag_id`
- `tags`
- `target`
- `target_instances`
- `template_id`
- `tentional_only`
- `th`
- `to`
- `total_plugins`
- `track`
- `un`
- `update`
- `update_available`
- `updates`
- `updates_found`
- `version`
- `view_d`
- `view_distance`
- `wiki_url`
- `world_name`

**Referenced In:**
- `scripts\bootstrap_discovery.py`
- `scripts\discover_docs.py`
- `scripts\hangar_sync.py`
- `scripts\modrinth_sync.py`
- `scripts\parse_markdown_to_sql.py`
- `scripts\populate_plugin_metadata.py`
- `src\agent\agent_cicd_methods.py`
- `src\agent\agent_database_methods.py`
- `src\agent\agent_extensions.py`
- `src\agent\agent_update_methods.py`
- `src\agent\update_checker.py`
- `src\api\plugin_configurator_endpoints.py`
- `src\api\update_manager_endpoints.py`
- `src\web\api.py`

**INSERT Operations:** 12 found

**SELECT Operations:** 47 found

**UPDATE Operations:** 18 found

**DELETE Operations:** 2 found

---

### rank_config_rules

**Columns Used:**
- `config_key`
- `config_value`
- `plugin_id`
- `rank_name`
- `stance_id`

**Referenced In:**
- `src\engine\hierarchy_resolver.py`

**SELECT Operations:** 3 found

---

### ranks

**Columns Used:**
- `color_code`
- `discovered_at`
- `display_name`
- `inherits_from`
- `instance_id`
- `is_active`
- `is_default`
- `last_seen_at`
- `permission_count`
- `player_count`
- `prefix`
- `priority`
- `rank_name`
- `server_name`
- `suffix`

**Referenced In:**
- `src\parsers\rank_parser.py`

**INSERT Operations:** 5 found

---

### scheduled_tasks

**Columns Used:**
- `created_at`
- `description`
- `enabled`
- `last_run_at`
- `last_run_duration_seconds`
- `last_run_error`
- `last_run_result`
- `last_run_status`
- `next_run`
- `next_run_at`
- `schedule_type`
- `schedule_value`
- `task_name`

**Referenced In:**
- `src\agent\scheduled_tasks.py`

**INSERT Operations:** 3 found

**UPDATE Operations:** 3 found

---

### server_properties_baselines

**Columns Used:**
- `as`
- `basel`
- `baseline_type`
- `conn`
- `create_baseline_from_`
- `created_at`
- `cursor`
- `cv`
- `d`
- `detail`
- `dictionary`
- `endpo`
- `exist`
- `existing`
- `f`
- `for`
- `i`
- `id`
- `if`
- `insert`
- `instance_id`
- `is_`
- `jo`
- `join`
- `limit`
- `properties`
- `property_key`
- `property_value`
- `query`
- `ra`
- `reference`
- `reg`
- `rowcount`
- `scan_`
- `server_properties_basel`
- `spv`
- `stance_id`
- `status_code`
- `t`
- `timestamp`
- `updated_at`
- `variance_value`

**Referenced In:**
- `src\agent\server_properties_scanner.py`
- `src\api\enhanced_endpoints.py`

**INSERT Operations:** 5 found

**SELECT Operations:** 4 found

---

### server_properties_variances

**Columns Used:**
- `as`
- `basel`
- `conn`
- `create_baseline_from_`
- `cursor`
- `cv`
- `d`
- `detail`
- `dictionary`
- `endpo`
- `exist`
- `existing`
- `f`
- `for`
- `i`
- `id`
- `if`
- `insert`
- `instance_id`
- `is_`
- `is_intentional`
- `jo`
- `join`
- `limit`
- `properties`
- `property_key`
- `property_value`
- `query`
- `ra`
- `reference`
- `reg`
- `rowcount`
- `scan_`
- `server_properties_basel`
- `spv`
- `stance_id`
- `status_code`
- `t`
- `timestamp`
- `variance_value`

**Referenced In:**
- `src\agent\server_properties_scanner.py`
- `src\api\enhanced_endpoints.py`

**INSERT Operations:** 3 found

**SELECT Operations:** 7 found

**UPDATE Operations:** 3 found

---

### system_health_metrics

**Columns Used:**
- `change_type`
- `changed_at`
- `changed_by`
- `component`
- `config_key`
- `created_at`
- `deployed_at`
- `deployed_by`
- `deployment_status`
- `deployment_type`
- `duration_ms`
- `float`
- `from_version`
- `id`
- `if`
- `limit`
- `metadata`
- `metric_name`
- `metric_unit`
- `metric_value`
- `notification_type`
- `operation`
- `params`
- `plug`
- `plugin_name`
- `query`
- `recorded_at`
- `result`
- `snapshot_at`
- `stance_id`
- `status`
- `str`
- `to_version`

**Referenced In:**
- `src\agent\performance_metrics.py`
- `src\agent\scheduled_tasks.py`
- `src\web\api.py`

**INSERT Operations:** 6 found

**SELECT Operations:** 10 found

**DELETE Operations:** 1 found

---

### tag_conflicts

**Columns Used:**
- `conflict_id`
- `conflict_severity`
- `description`
- `display_name`
- `i`
- `instance_id`
- `is_deprecated`
- `t`
- `t1`
- `t2`
- `tag_a_id`
- `tag_a_name`
- `tag_b_id`
- `tag_b_name`
- `tc`
- `usage_count`

**Referenced In:**
- `src\api\tag_manager_endpoints.py`

**SELECT Operations:** 2 found

---

### tag_dependencies

**Columns Used:**
- `dependency_id`
- `dependency_type`
- `dependent_tag_id`
- `dependent_tag_name`
- `description`
- `display_name`
- `i`
- `instance_id`
- `is_deprecated`
- `required_tag_id`
- `required_tag_name`
- `t`
- `t1`
- `t2`
- `tc`
- `td`
- `usage_count`

**Referenced In:**
- `src\api\tag_manager_endpoints.py`

**SELECT Operations:** 3 found

---

### tag_hierarchy

**Columns Used:**
- `child_tag_id`
- `name`
- `p`
- `parent_tag_id`
- `t`
- `update_available`

**Referenced In:**
- `src\api\enhanced_endpoints.py`

**INSERT Operations:** 2 found

---

### world_config_rules

**Columns Used:**
- `config_key`
- `config_value`
- `plugin_id`
- `stance_id`
- `world_name`

**Referenced In:**
- `src\engine\hierarchy_resolver.py`

**SELECT Operations:** 3 found

---

### worlds

**Columns Used:**
- `discovered_at`
- `environment`
- `folder_size_bytes`
- `generator`
- `instance_id`
- `is_active`
- `last_modified`
- `last_seen_at`
- `region_count`
- `seed`
- `world_name`
- `world_type`

**Referenced In:**
- `src\scanners\world_scanner.py`

**INSERT Operations:** 5 found

---

## Recommended Schema (Minimal)

```sql
-- Tables that MUST exist based on code analysis
-- This is the MINIMUM schema needed for code to work

CREATE TABLE IF NOT EXISTS agent_heartbeats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_id TEXT,  -- TODO: Determine proper type
    last_heartbeat TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS approval_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    voted_by VARCHAR(50) NOT NULL,
    vote ENUM('approved', 'rejected') NOT NULL,
    comment TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES change_approval_requests(request_id) ON DELETE CASCADE,
    UNIQUE KEY unique_vote (request_id, voted_by),
    INDEX idx_request (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action TEXT,  -- TODO: Determine proper type
    al TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    details TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    event_id TEXT,  -- TODO: Determine proper type
    event_type TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    match TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    user TEXT,  -- TODO: Determine proper type
    where_clause TEXT,  -- TODO: Determine proper type
    where_conditions TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS backup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _restore_config_from_backup TEXT,  -- TODO: Determine proper type
    backed_up_at TEXT,  -- TODO: Determine proper type
    backup TEXT,  -- TODO: Determine proper type
    backup_id TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    config TEXT,  -- TODO: Determine proper type
    config_file_id TEXT,  -- TODO: Determine proper type
    create TEXT,  -- TODO: Determine proper type
    created TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    def TEXT,  -- TODO: Determine proper type
    determ TEXT,  -- TODO: Determine proper type
    e TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    error TEXT,  -- TODO: Determine proper type
    except TEXT,  -- TODO: Determine proper type
    exception TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    failed TEXT,  -- TODO: Determine proper type
    fetch TEXT,  -- TODO: Determine proper type
    file TEXT,  -- TODO: Determine proper type
    file_path TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    info TEXT,  -- TODO: Determine proper type
    int TEXT,  -- TODO: Determine proper type
    last_id TEXT,  -- TODO: Determine proper type
    last_insert_id TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    logger TEXT,  -- TODO: Determine proper type
    none TEXT,  -- TODO: Determine proper type
    ok TEXT,  -- TODO: Determine proper type
    otherw TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    restore TEXT,  -- TODO: Determine proper type
    restore_to_path TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    return TEXT,  -- TODO: Determine proper type
    self TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    target_path TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    true TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS baseline_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    config_type TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    expected_value TEXT,  -- TODO: Determine proper type
    notes TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    snapshot_id TEXT,  -- TODO: Determine proper type
    value_type TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS change_approval_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    approval_count TEXT,  -- TODO: Determine proper type
    auto_approve_after_hours TEXT,  -- TODO: Determine proper type
    change_data TEXT,  -- TODO: Determine proper type
    change_description TEXT,  -- TODO: Determine proper type
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    elapsed TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    hour TEXT,  -- TODO: Determine proper type
    hours_elapsed TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    now TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    rejection_count TEXT,  -- TODO: Determine proper type
    request TEXT,  -- TODO: Determine proper type
    request_id TEXT,  -- TODO: Determine proper type
    requested_by TEXT,  -- TODO: Determine proper type
    required_approvals TEXT,  -- TODO: Determine proper type
    resolved_at TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    timestampdiff TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    voted_at TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS cicd_webhook_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action_taken TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    event_id TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    processed_at TEXT,  -- TODO: Determine proper type
    received_at TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_baselines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key TEXT,  -- TODO: Determine proper type
    config_value TEXT,  -- TODO: Determine proper type
    file_path TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_change_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id TEXT,  -- TODO: Determine proper type
    change TEXT,  -- TODO: Determine proper type
    change_id TEXT,  -- TODO: Determine proper type
    change_reason TEXT,  -- TODO: Determine proper type
    change_source TEXT,  -- TODO: Determine proper type
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    concat TEXT,  -- TODO: Determine proper type
    config_change_h TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    count TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    date TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_id TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    event TEXT,  -- TODO: Determine proper type
    event_type TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    get_change_stat TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is TEXT,  -- TODO: Determine proper type
    lifecycle TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    m TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    new_value TEXT,  -- TODO: Determine proper type
    not TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    null TEXT,  -- TODO: Determine proper type
    old_value TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_lifecycle TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    stat TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    total TEXT,  -- TODO: Determine proper type
    user TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_drift_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    actual_value TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    config_type TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    detected_at TEXT,  -- TODO: Determine proper type
    drift_id TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    exist TEXT,  -- TODO: Determine proper type
    expected_value TEXT,  -- TODO: Determine proper type
    get_plug TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    resolution_notes TEXT,  -- TODO: Determine proper type
    resolved_at TEXT,  -- TODO: Determine proper type
    reviewed_at TEXT,  -- TODO: Determine proper type
    reviewed_by TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    severity TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_key_migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _breaking TEXT,  -- TODO: Determine proper type
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    comment_inline TEXT,  -- TODO: Determine proper type
    comment_pre TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_filename TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    cont TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    data_type TEXT,  -- TODO: Determine proper type
    determ TEXT,  -- TODO: Determine proper type
    ex TEXT,  -- TODO: Determine proper type
    file_type TEXT,  -- TODO: Determine proper type
    key_path TEXT,  -- TODO: Determine proper type
    observed_value TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_default_value TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    whitespace_prefix TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_locks (
    lock_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    locked_by VARCHAR(50) NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_until TIMESTAMP NOT NULL,
    INDEX idx_lock_key (instance_id, plugin_name, config_key),
    INDEX idx_lock_expiry (locked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS config_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    _calculate_scope_score TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    _get_available_keys TEXT,  -- TODO: Determine proper type
    a TEXT,  -- TODO: Determine proper type
    add TEXT,  -- TODO: Determine proper type
    all TEXT,  -- TODO: Determine proper type
    any TEXT,  -- TODO: Determine proper type
    append TEXT,  -- TODO: Determine proper type
    args TEXT,  -- TODO: Determine proper type
    at TEXT,  -- TODO: Determine proper type
    available TEXT,  -- TODO: Determine proper type
    available_keys TEXT,  -- TODO: Determine proper type
    base TEXT,  -- TODO: Determine proper type
    based TEXT,  -- TODO: Determine proper type
    best TEXT,  -- TODO: Determine proper type
    best_rule TEXT,  -- TODO: Determine proper type
    bonus TEXT,  -- TODO: Determine proper type
    by TEXT,  -- TODO: Determine proper type
    calculate TEXT,  -- TODO: Determine proper type
    config TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    config_keys TEXT,  -- TODO: Determine proper type
    config_type TEXT,  -- TODO: Determine proper type
    config_value TEXT,  -- TODO: Determine proper type
    configcontext TEXT,  -- TODO: Determine proper type
    context TEXT,  -- TODO: Determine proper type
    cr TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    created_by TEXT,  -- TODO: Determine proper type
    ctx TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    db TEXT,  -- TODO: Determine proper type
    debug TEXT,  -- TODO: Determine proper type
    def TEXT,  -- TODO: Determine proper type
    desc TEXT,  -- TODO: Determine proper type
    dict TEXT,  -- TODO: Determine proper type
    display_order TEXT,  -- TODO: Determine proper type
    drift_id TEXT,  -- TODO: Determine proper type
    each TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    exist TEXT,  -- TODO: Determine proper type
    expected_value TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    file TEXT,  -- TODO: Determine proper type
    filename TEXT,  -- TODO: Determine proper type
    first TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    get TEXT,  -- TODO: Determine proper type
    get_plug TEXT,  -- TODO: Determine proper type
    global TEXT,  -- TODO: Determine proper type
    hierarchy TEXT,  -- TODO: Determine proper type
    higher TEXT,  -- TODO: Determine proper type
    identifier TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    in TEXT,  -- TODO: Determine proper type
    instance TEXT,  -- TODO: Determine proper type
    instance_count TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    int TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_variable TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    key TEXT,  -- TODO: Determine proper type
    keys TEXT,  -- TODO: Determine proper type
    lambda TEXT,  -- TODO: Determine proper type
    least TEXT,  -- TODO: Determine proper type
    len TEXT,  -- TODO: Determine proper type
    level TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    list TEXT,  -- TODO: Determine proper type
    logger TEXT,  -- TODO: Determine proper type
    mapping TEXT,  -- TODO: Determine proper type
    matches TEXT,  -- TODO: Determine proper type
    matching TEXT,  -- TODO: Determine proper type
    meta TEXT,  -- TODO: Determine proper type
    meta_tag TEXT,  -- TODO: Determine proper type
    meta_tag_id TEXT,  -- TODO: Determine proper type
    meta_tag_ids TEXT,  -- TODO: Determine proper type
    more TEXT,  -- TODO: Determine proper type
    most TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    multiple TEXT,  -- TODO: Determine proper type
    none TEXT,  -- TODO: Determine proper type
    not TEXT,  -- TODO: Determine proper type
    notes TEXT,  -- TODO: Determine proper type
    of TEXT,  -- TODO: Determine proper type
    on TEXT,  -- TODO: Determine proper type
    once TEXT,  -- TODO: Determine proper type
    optional TEXT,  -- TODO: Determine proper type
    other TEXT,  -- TODO: Determine proper type
    over TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    player TEXT,  -- TODO: Determine proper type
    player_uuid TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    primary TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    pv TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    rank TEXT,  -- TODO: Determine proper type
    rank_name TEXT,  -- TODO: Determine proper type
    resolve TEXT,  -- TODO: Determine proper type
    resolve_all_configs TEXT,  -- TODO: Determine proper type
    resolve_config TEXT,  -- TODO: Determine proper type
    resolved TEXT,  -- TODO: Determine proper type
    resolvedconfig TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    return TEXT,  -- TODO: Determine proper type
    returns TEXT,  -- TODO: Determine proper type
    reverse TEXT,  -- TODO: Determine proper type
    rule TEXT,  -- TODO: Determine proper type
    rule_id TEXT,  -- TODO: Determine proper type
    rules TEXT,  -- TODO: Determine proper type
    s TEXT,  -- TODO: Determine proper type
    same TEXT,  -- TODO: Determine proper type
    scope TEXT,  -- TODO: Determine proper type
    scope_identifier TEXT,  -- TODO: Determine proper type
    scope_level TEXT,  -- TODO: Determine proper type
    scope_score TEXT,  -- TODO: Determine proper type
    scope_scores TEXT,  -- TODO: Determine proper type
    scope_selector TEXT,  -- TODO: Determine proper type
    scope_type TEXT,  -- TODO: Determine proper type
    score TEXT,  -- TODO: Determine proper type
    scored_rules TEXT,  -- TODO: Determine proper type
    scores TEXT,  -- TODO: Determine proper type
    selected TEXT,  -- TODO: Determine proper type
    self TEXT,  -- TODO: Determine proper type
    server TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    set TEXT,  -- TODO: Determine proper type
    sort TEXT,  -- TODO: Determine proper type
    specific TEXT,  -- TODO: Determine proper type
    specificity TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    tag TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    the TEXT,  -- TODO: Determine proper type
    this TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    true TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    updated_at TEXT,  -- TODO: Determine proper type
    value_type TEXT,  -- TODO: Determine proper type
    variable_name TEXT,  -- TODO: Determine proper type
    wins TEXT,  -- TODO: Determine proper type
    within TEXT,  -- TODO: Determine proper type
    without TEXT,  -- TODO: Determine proper type
    world TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    x TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    clone_from_ TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    created_by TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    last_used_at TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    source TEXT,  -- TODO: Determine proper type
    stalled_plug TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    tag TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    template_data TEXT,  -- TODO: Determine proper type
    template_id TEXT,  -- TODO: Determine proper type
    template_name TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    usage_count TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_variables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    scope_identifier TEXT,  -- TODO: Determine proper type
    scope_type TEXT,  -- TODO: Determine proper type
    variable_name TEXT,  -- TODO: Determine proper type
    variable_value TEXT,  -- TODO: Determine proper type
    variables TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_variance_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _drift TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    actual_value TEXT,  -- TODO: Determine proper type
    cache_id TEXT,  -- TODO: Determine proper type
    cached_configs TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    config TEXT,  -- TODO: Determine proper type
    config_drifts TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    config_type TEXT,  -- TODO: Determine proper type
    drift_count TEXT,  -- TODO: Determine proper type
    drifts TEXT,  -- TODO: Determine proper type
    expected_value TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_baseline TEXT,  -- TODO: Determine proper type
    is_drift TEXT,  -- TODO: Determine proper type
    last_scanned TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    scope TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    value_type TEXT,  -- TODO: Determine proper type
    variance_classification TEXT,  -- TODO: Determine proper type
    variance_type TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_variance_detected (
    id INT AUTO_INCREMENT PRIMARY KEY,
    actual_value TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    baseline_path TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    expected_value TEXT,  -- TODO: Determine proper type
    has_plug TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    last_updated TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin TEXT,  -- TODO: Determine proper type
    plugin_ TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reason TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    substring_ TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    target TEXT,  -- TODO: Determine proper type
    tentional_only TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    variance_id TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_variance_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS config_variances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    actual_value TEXT,  -- TODO: Determine proper type
    all TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    baseline_value TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    deleted_count TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    detected_at TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    exist TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_l TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    scan_and_reg TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stance TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    total_variances TEXT,  -- TODO: Determine proper type
    variance_id TEXT,  -- TODO: Determine proper type
    variance_value TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS datapack_deployment_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    scheduled_for TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    all TEXT,  -- TODO: Determine proper type
    an TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    change_type TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    currently TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    datapack TEXT,  -- TODO: Determine proper type
    datapack_id TEXT,  -- TODO: Determine proper type
    datapack_name TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    difficulty TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    exist TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_name TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    gamemode TEXT,  -- TODO: Determine proper type
    get_ TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    is_enabled TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    last_checked_at TEXT,  -- TODO: Determine proper type
    last_updated_at TEXT,  -- TODO: Determine proper type
    level_name TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    max_players TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    pack_format TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    properties_json TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    pvp TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    scan_and_reg TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    simulation_d TEXT,  -- TODO: Determine proper type
    simulation_distance TEXT,  -- TODO: Determine proper type
    spawn_protection TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stance TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    total TEXT,  -- TODO: Determine proper type
    total_datapacks TEXT,  -- TODO: Determine proper type
    track TEXT,  -- TODO: Determine proper type
    un TEXT,  -- TODO: Determine proper type
    version TEXT,  -- TODO: Determine proper type
    view_d TEXT,  -- TODO: Determine proper type
    view_distance TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    world_path TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS deployment_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    completed_at TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    current_version TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment TEXT,  -- TODO: Determine proper type
    deployment_id TEXT,  -- TODO: Determine proper type
    deployment_notes TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    error_message TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    instances_json TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    new_version TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    null TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    scope TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    target_instances TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    type TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS deployment_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TEXT,  -- TODO: Determine proper type
    deployment_id TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dl TEXT,  -- TODO: Determine proper type
    dq TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    message TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    queue_entry TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    stat TEXT,  -- TODO: Determine proper type
    stats TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS deployment_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_content TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    deployment_id TEXT,  -- TODO: Determine proper type
    deployment_notes TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dl TEXT,  -- TODO: Determine proper type
    dq TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    instance_count TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_ids TEXT,  -- TODO: Determine proper type
    json_length TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    queue_entry TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    requested_by TEXT,  -- TODO: Determine proper type
    stat TEXT,  -- TODO: Determine proper type
    stats TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    updated_at TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS discovery_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _log_d TEXT,  -- TODO: Determine proper type
    action TEXT,  -- TODO: Determine proper type
    an TEXT,  -- TODO: Determine proper type
    current_run_id TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    discovered_at TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    item_id TEXT,  -- TODO: Determine proper type
    item_path TEXT,  -- TODO: Determine proper type
    item_type TEXT,  -- TODO: Determine proper type
    run_id TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS discovery_runs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _log_d TEXT,  -- TODO: Determine proper type
    an TEXT,  -- TODO: Determine proper type
    completed_at TEXT,  -- TODO: Determine proper type
    current_run_id TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    run_id TEXT,  -- TODO: Determine proper type
    run_type TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    started_at TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS endpoint_config_backups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    backed_up_at TEXT,  -- TODO: Determine proper type
    backed_up_by TEXT,  -- TODO: Determine proper type
    backup TEXT,  -- TODO: Determine proper type
    backup_content TEXT,  -- TODO: Determine proper type
    backup_id TEXT,  -- TODO: Determine proper type
    backup_metadata TEXT,  -- TODO: Determine proper type
    backup_reason TEXT,  -- TODO: Determine proper type
    config_file_id TEXT,  -- TODO: Determine proper type
    config_file_path TEXT,  -- TODO: Determine proper type
    content_hash TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    determ TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    file_content TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_size_bytes TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    length TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    otherw TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    target_path TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS endpoint_config_change_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    backup_id TEXT,  -- TODO: Determine proper type
    change_details TEXT,  -- TODO: Determine proper type
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    config_file_id TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS endpoint_config_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _create_config_backup TEXT,  -- TODO: Determine proper type
    args TEXT,  -- TODO: Determine proper type
    backup TEXT,  -- TODO: Determine proper type
    cf TEXT,  -- TODO: Determine proper type
    config TEXT,  -- TODO: Determine proper type
    config_file_id TEXT,  -- TODO: Determine proper type
    create TEXT,  -- TODO: Determine proper type
    current_hash TEXT,  -- TODO: Determine proper type
    database TEXT,  -- TODO: Determine proper type
    def TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    e TEXT,  -- TODO: Determine proper type
    error TEXT,  -- TODO: Determine proper type
    except TEXT,  -- TODO: Determine proper type
    exception TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    failed TEXT,  -- TODO: Determine proper type
    fetch TEXT,  -- TODO: Determine proper type
    file TEXT,  -- TODO: Determine proper type
    file_path TEXT,  -- TODO: Determine proper type
    file_size TEXT,  -- TODO: Determine proper type
    file_type TEXT,  -- TODO: Determine proper type
    first_discovered TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    in TEXT,  -- TODO: Determine proper type
    instance_base_path TEXT,  -- TODO: Determine proper type
    instance_folder_name TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    int TEXT,  -- TODO: Determine proper type
    last_discovered TEXT,  -- TODO: Determine proper type
    last_id TEXT,  -- TODO: Determine proper type
    last_insert_id TEXT,  -- TODO: Determine proper type
    logger TEXT,  -- TODO: Determine proper type
    manual TEXT,  -- TODO: Determine proper type
    none TEXT,  -- TODO: Determine proper type
    of TEXT,  -- TODO: Determine proper type
    operations TEXT,  -- TODO: Determine proper type
    optional TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_display_name TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    reason TEXT,  -- TODO: Determine proper type
    register TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    return TEXT,  -- TODO: Determine proper type
    self TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    true TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

# Create table for locks if not exists
CREATE_LOCKS_TABLE =

CREATE TABLE IF NOT EXISTS information_schema (
    id INT AUTO_INCREMENT PRIMARY KEY,
    data_length TEXT,  -- TODO: Determine proper type
    index_length TEXT,  -- TODO: Determine proper type
    round TEXT,  -- TODO: Determine proper type
    size_mb TEXT,  -- TODO: Determine proper type
    table_name TEXT,  -- TODO: Determine proper type
    table_schema TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS installed_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    clone_from_ TEXT,  -- TODO: Determine proper type
    config_data TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    source TEXT,  -- TODO: Determine proper type
    stalled_plug TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    template_id TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instance_datapacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    an TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    change_type TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    currently TEXT,  -- TODO: Determine proper type
    custom_source TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    datapack TEXT,  -- TODO: Determine proper type
    datapack_id TEXT,  -- TODO: Determine proper type
    datapack_name TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    difficulty TEXT,  -- TODO: Determine proper type
    discovered_at TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_name TEXT,  -- TODO: Determine proper type
    file_path TEXT,  -- TODO: Determine proper type
    file_size TEXT,  -- TODO: Determine proper type
    first_discovered_at TEXT,  -- TODO: Determine proper type
    gamemode TEXT,  -- TODO: Determine proper type
    get_ TEXT,  -- TODO: Determine proper type
    github_repo TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    installed_at TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_enabled TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    last_checked_at TEXT,  -- TODO: Determine proper type
    last_seen_at TEXT,  -- TODO: Determine proper type
    last_updated_at TEXT,  -- TODO: Determine proper type
    level_name TEXT,  -- TODO: Determine proper type
    ma TEXT,  -- TODO: Determine proper type
    max_players TEXT,  -- TODO: Determine proper type
    modr TEXT,  -- TODO: Determine proper type
    modrinth_id TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    parser TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    po TEXT,  -- TODO: Determine proper type
    properties_json TEXT,  -- TODO: Determine proper type
    pvp TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    simulation_d TEXT,  -- TODO: Determine proper type
    simulation_distance TEXT,  -- TODO: Determine proper type
    spawn_protection TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    total TEXT,  -- TODO: Determine proper type
    track TEXT,  -- TODO: Determine proper type
    un TEXT,  -- TODO: Determine proper type
    version TEXT,  -- TODO: Determine proper type
    view_d TEXT,  -- TODO: Determine proper type
    view_distance TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    world_path TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instance_group_members (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _enabled TEXT,  -- TODO: Determine proper type
    group_name TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    igm TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instance_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    group_name TEXT,  -- TODO: Determine proper type
    group_type TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    member_count TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    scope_type TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instance_meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    __name__ TEXT,  -- TODO: Determine proper type
    applied_at TEXT,  -- TODO: Determine proper type
    applied_by TEXT,  -- TODO: Determine proper type
    c TEXT,  -- TODO: Determine proper type
    category_display_name TEXT,  -- TODO: Determine proper type
    category_id TEXT,  -- TODO: Determine proper type
    category_name TEXT,  -- TODO: Determine proper type
    color TEXT,  -- TODO: Determine proper type
    confidence_score TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    count TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    fetch TEXT,  -- TODO: Determine proper type
    getting TEXT,  -- TODO: Determine proper type
    h TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    icon TEXT,  -- TODO: Determine proper type
    imt TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_auto_detected TEXT,  -- TODO: Determine proper type
    is_deprecated TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    meta_tag_h TEXT,  -- TODO: Determine proper type
    mt TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    t1 TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    tag_name TEXT,  -- TODO: Determine proper type
    tc TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    usage_count TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instance_plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _enabled TEXT,  -- TODO: Determine proper type
    affected_ TEXT,  -- TODO: Determine proper type
    all TEXT,  -- TODO: Determine proper type
    an TEXT,  -- TODO: Determine proper type
    available_version TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cont TEXT,  -- TODO: Determine proper type
    currently TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    datapack TEXT,  -- TODO: Determine proper type
    datapack_name TEXT,  -- TODO: Determine proper type
    deployment_scope TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    difficulty TEXT,  -- TODO: Determine proper type
    dist TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_modified_at TEXT,  -- TODO: Determine proper type
    file_name TEXT,  -- TODO: Determine proper type
    file_path TEXT,  -- TODO: Determine proper type
    file_size TEXT,  -- TODO: Determine proper type
    first_discovered_at TEXT,  -- TODO: Determine proper type
    gamemode TEXT,  -- TODO: Determine proper type
    get_ TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    install_count TEXT,  -- TODO: Determine proper type
    installation_method TEXT,  -- TODO: Determine proper type
    installed_at TEXT,  -- TODO: Determine proper type
    installed_version TEXT,  -- TODO: Determine proper type
    instance_count TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    ip TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_enabled TEXT,  -- TODO: Determine proper type
    is_installed TEXT,  -- TODO: Determine proper type
    is_outdated TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    last_checked_at TEXT,  -- TODO: Determine proper type
    last_seen_at TEXT,  -- TODO: Determine proper type
    last_updated_at TEXT,  -- TODO: Determine proper type
    latest_version TEXT,  -- TODO: Determine proper type
    level_name TEXT,  -- TODO: Determine proper type
    max_players TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    plugin_row TEXT,  -- TODO: Determine proper type
    properties_json TEXT,  -- TODO: Determine proper type
    pvp TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    simulation_d TEXT,  -- TODO: Determine proper type
    simulation_distance TEXT,  -- TODO: Determine proper type
    spawn_protection TEXT,  -- TODO: Determine proper type
    stalled_version TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    stance_plug TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    target_instances TEXT,  -- TODO: Determine proper type
    th TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    track TEXT,  -- TODO: Determine proper type
    un TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    version TEXT,  -- TODO: Determine proper type
    view_d TEXT,  -- TODO: Determine proper type
    view_distance TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instance_server_properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    an TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    currently TEXT,  -- TODO: Determine proper type
    datapack TEXT,  -- TODO: Determine proper type
    datapack_name TEXT,  -- TODO: Determine proper type
    difficulty TEXT,  -- TODO: Determine proper type
    enable_command_block TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_name TEXT,  -- TODO: Determine proper type
    gamemode TEXT,  -- TODO: Determine proper type
    get_ TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_enabled TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    last_checked_at TEXT,  -- TODO: Determine proper type
    last_scanned_at TEXT,  -- TODO: Determine proper type
    last_updated_at TEXT,  -- TODO: Determine proper type
    level_name TEXT,  -- TODO: Determine proper type
    max_players TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    properties_json TEXT,  -- TODO: Determine proper type
    pvp TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    simulation_d TEXT,  -- TODO: Determine proper type
    simulation_distance TEXT,  -- TODO: Determine proper type
    spawn_protection TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    track TEXT,  -- TODO: Determine proper type
    un TEXT,  -- TODO: Determine proper type
    version TEXT,  -- TODO: Determine proper type
    view_d TEXT,  -- TODO: Determine proper type
    view_distance TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instance_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    assigned_by TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    config_file TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    config_type TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    display_order TEXT,  -- TODO: Determine proper type
    drift_id TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    get_plug TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    instance TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    it TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    meta_tag_id TEXT,  -- TODO: Determine proper type
    mt TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    rule_id TEXT,  -- TODO: Determine proper type
    scope TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    set TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    tag_name TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    updated_at TEXT,  -- TODO: Determine proper type
    variance_classification TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    _discover_plug TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    _scan_ TEXT,  -- TODO: Determine proper type
    active_instances TEXT,  -- TODO: Determine proper type
    affected_ TEXT,  -- TODO: Determine proper type
    al TEXT,  -- TODO: Determine proper type
    all TEXT,  -- TODO: Determine proper type
    amp_ TEXT,  -- TODO: Determine proper type
    amp_instance_id TEXT,  -- TODO: Determine proper type
    an TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    baseline_path TEXT,  -- TODO: Determine proper type
    baseline_value TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    cha TEXT,  -- TODO: Determine proper type
    chain TEXT,  -- TODO: Determine proper type
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    check_m TEXT,  -- TODO: Determine proper type
    config_file_id TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    config_path TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cont TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    currently TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    database TEXT,  -- TODO: Determine proper type
    datapack TEXT,  -- TODO: Determine proper type
    datapack_id TEXT,  -- TODO: Determine proper type
    datapack_name TEXT,  -- TODO: Determine proper type
    db_ TEXT,  -- TODO: Determine proper type
    db_instance TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployment_id TEXT,  -- TODO: Determine proper type
    deployment_scope TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    determ TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    difficulty TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    dist TEXT,  -- TODO: Determine proper type
    dl TEXT,  -- TODO: Determine proper type
    drift_count TEXT,  -- TODO: Determine proper type
    drifts TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    event_type TEXT,  -- TODO: Determine proper type
    exist TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    fetch TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_name TEXT,  -- TODO: Determine proper type
    folder_name TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    gamemode TEXT,  -- TODO: Determine proper type
    get TEXT,  -- TODO: Determine proper type
    get_ TEXT,  -- TODO: Determine proper type
    group_name TEXT,  -- TODO: Determine proper type
    h TEXT,  -- TODO: Determine proper type
    has_plug TEXT,  -- TODO: Determine proper type
    has_plugin TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    inst TEXT,  -- TODO: Determine proper type
    instance TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_info TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    instance_path TEXT,  -- TODO: Determine proper type
    instance_short TEXT,  -- TODO: Determine proper type
    instance_type TEXT,  -- TODO: Determine proper type
    instances TEXT,  -- TODO: Determine proper type
    int TEXT,  -- TODO: Determine proper type
    internal_ip TEXT,  -- TODO: Determine proper type
    ip TEXT,  -- TODO: Determine proper type
    is TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_deprecated TEXT,  -- TODO: Determine proper type
    is_enabled TEXT,  -- TODO: Determine proper type
    is_installed TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    is_production TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    key TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    last_checked_at TEXT,  -- TODO: Determine proper type
    last_scanned TEXT,  -- TODO: Determine proper type
    last_seen TEXT,  -- TODO: Determine proper type
    last_seen_at TEXT,  -- TODO: Determine proper type
    last_updated_at TEXT,  -- TODO: Determine proper type
    latest_version TEXT,  -- TODO: Determine proper type
    level_name TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    m TEXT,  -- TODO: Determine proper type
    match TEXT,  -- TODO: Determine proper type
    max_players TEXT,  -- TODO: Determine proper type
    mc_compat TEXT,  -- TODO: Determine proper type
    meta_tag_h TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    minecraft_version TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    not TEXT,  -- TODO: Determine proper type
    null TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    pack_format TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    parent_tag_id TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    pi TEXT,  -- TODO: Determine proper type
    pl3xmap_version TEXT,  -- TODO: Determine proper type
    platform TEXT,  -- TODO: Determine proper type
    platform_ TEXT,  -- TODO: Determine proper type
    platform_version TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin TEXT,  -- TODO: Determine proper type
    plugin_ TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_l TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    plugins_dir TEXT,  -- TODO: Determine proper type
    port TEXT,  -- TODO: Determine proper type
    properties_json TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    pv TEXT,  -- TODO: Determine proper type
    pvp TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    queue_entry TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    read TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    scan_and_reg TEXT,  -- TODO: Determine proper type
    scann TEXT,  -- TODO: Determine proper type
    server_host TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    simulation_d TEXT,  -- TODO: Determine proper type
    simulation_distance TEXT,  -- TODO: Determine proper type
    skipp TEXT,  -- TODO: Determine proper type
    spawn_protection TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stalled_version TEXT,  -- TODO: Determine proper type
    stance TEXT,  -- TODO: Determine proper type
    stance_ TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    stance_plug TEXT,  -- TODO: Determine proper type
    stat TEXT,  -- TODO: Determine proper type
    stats TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    substring_ TEXT,  -- TODO: Determine proper type
    substring_index TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    t1 TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    tag_name TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    target TEXT,  -- TODO: Determine proper type
    target_instances TEXT,  -- TODO: Determine proper type
    tc TEXT,  -- TODO: Determine proper type
    tentional_only TEXT,  -- TODO: Determine proper type
    th TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    total TEXT,  -- TODO: Determine proper type
    total_datapacks TEXT,  -- TODO: Determine proper type
    total_variances TEXT,  -- TODO: Determine proper type
    track TEXT,  -- TODO: Determine proper type
    un TEXT,  -- TODO: Determine proper type
    update TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    upsert_ TEXT,  -- TODO: Determine proper type
    usage_count TEXT,  -- TODO: Determine proper type
    user TEXT,  -- TODO: Determine proper type
    value TEXT,  -- TODO: Determine proper type
    variables TEXT,  -- TODO: Determine proper type
    variance_id TEXT,  -- TODO: Determine proper type
    variance_value TEXT,  -- TODO: Determine proper type
    version TEXT,  -- TODO: Determine proper type
    view_d TEXT,  -- TODO: Determine proper type
    view_distance TEXT,  -- TODO: Determine proper type
    warn TEXT,  -- TODO: Determine proper type
    where_clause TEXT,  -- TODO: Determine proper type
    where_conditions TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    world_path TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS meta_tag_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _active TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    c TEXT,  -- TODO: Determine proper type
    category_id TEXT,  -- TODO: Determine proper type
    category_name TEXT,  -- TODO: Determine proper type
    color TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    count TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    display_order TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    ex TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    icon TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_deprecated TEXT,  -- TODO: Determine proper type
    is_mult TEXT,  -- TODO: Determine proper type
    is_multiselect TEXT,  -- TODO: Determine proper type
    is_required TEXT,  -- TODO: Determine proper type
    max_order TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    rule_id TEXT,  -- TODO: Determine proper type
    set TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    t1 TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    tc TEXT,  -- TODO: Determine proper type
    updated_at TEXT,  -- TODO: Determine proper type
    usage_count TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS meta_tag_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    h TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    meta_tag_h TEXT,  -- TODO: Determine proper type
    performed_by TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reason TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    __name__ TEXT,  -- TODO: Determine proper type
    _active TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    c TEXT,  -- TODO: Determine proper type
    category_display_name TEXT,  -- TODO: Determine proper type
    category_id TEXT,  -- TODO: Determine proper type
    category_name TEXT,  -- TODO: Determine proper type
    color TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    count TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    created_by TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    display_order TEXT,  -- TODO: Determine proper type
    drift_id TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    ex TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    fetch TEXT,  -- TODO: Determine proper type
    get_plug TEXT,  -- TODO: Determine proper type
    getting TEXT,  -- TODO: Determine proper type
    h TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    icon TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_deprecated TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    is_mult TEXT,  -- TODO: Determine proper type
    is_system_tag TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    meta_tag_h TEXT,  -- TODO: Determine proper type
    metadata_json TEXT,  -- TODO: Determine proper type
    mt TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    parent_tag_id TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_ TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    replacement_tag_id TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    rule_id TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    set TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    t1 TEXT,  -- TODO: Determine proper type
    tag_description TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    tag_name TEXT,  -- TODO: Determine proper type
    tag_type TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    tc TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    updated_at TEXT,  -- TODO: Determine proper type
    usage_count TEXT,  -- TODO: Determine proper type
    variance_classification TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS notification_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    channels TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    message TEXT,  -- TODO: Determine proper type
    metadata TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    read_at TEXT,  -- TODO: Determine proper type
    read_by TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    related_entity_id TEXT,  -- TODO: Determine proper type
    related_entity_type TEXT,  -- TODO: Determine proper type
    sent_at TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    title TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    unread_notifications TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS pending (
    id INT AUTO_INCREMENT PRIMARY KEY,
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    pv TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    severity TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS player_config_overrides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key TEXT,  -- TODO: Determine proper type
    config_value TEXT,  -- TODO: Determine proper type
    player_uuid TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plugin_instances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    baseline_path TEXT,  -- TODO: Determine proper type
    config_hash TEXT,  -- TODO: Determine proper type
    config_path TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    has_plug TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    instance TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    last_scanned TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    pi TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin TEXT,  -- TODO: Determine proper type
    plugin_ TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    read TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    substring_ TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    target TEXT,  -- TODO: Determine proper type
    tentional_only TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plugin_meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assigned_at TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_ TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plugin_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    max_mc_version TEXT,  -- TODO: Determine proper type
    metadata TEXT,  -- TODO: Determine proper type
    min_mc_version TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    required_plugins TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    supported_mc_versions TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plugin_update_queue (
    id INT AUTO_INCREMENT PRIMARY KEY,
    completed_at TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    created_by TEXT,  -- TODO: Determine proper type
    deployment_log TEXT,  -- TODO: Determine proper type
    download_url TEXT,  -- TODO: Determine proper type
    error_message TEXT,  -- TODO: Determine proper type
    failure_count TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    pend TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    scheduled_for TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    started_at TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    success_count TEXT,  -- TODO: Determine proper type
    target_instances TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plugin_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    affected_ TEXT,  -- TODO: Determine proper type
    an TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    checked_at TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cont TEXT,  -- TODO: Determine proper type
    current_version TEXT,  -- TODO: Determine proper type
    currently TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    datapack TEXT,  -- TODO: Determine proper type
    datapack_name TEXT,  -- TODO: Determine proper type
    deployment_scope TEXT,  -- TODO: Determine proper type
    determ TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    difficulty TEXT,  -- TODO: Determine proper type
    dism TEXT,  -- TODO: Determine proper type
    dist TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_name TEXT,  -- TODO: Determine proper type
    gamemode TEXT,  -- TODO: Determine proper type
    get_ TEXT,  -- TODO: Determine proper type
    group_concat TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    installed_version TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instances TEXT,  -- TODO: Determine proper type
    is_enabled TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    jar_filename TEXT,  -- TODO: Determine proper type
    jar_hash TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    last_checked TEXT,  -- TODO: Determine proper type
    last_checked_at TEXT,  -- TODO: Determine proper type
    last_updated_at TEXT,  -- TODO: Determine proper type
    latest_version TEXT,  -- TODO: Determine proper type
    level_name TEXT,  -- TODO: Determine proper type
    mark TEXT,  -- TODO: Determine proper type
    max_players TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    needs_update TEXT,  -- TODO: Determine proper type
    new_version TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    parent_tag_id TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin TEXT,  -- TODO: Determine proper type
    plugin_ TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    plugin_update TEXT,  -- TODO: Determine proper type
    properties_json TEXT,  -- TODO: Determine proper type
    pv TEXT,  -- TODO: Determine proper type
    pvp TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    separator TEXT,  -- TODO: Determine proper type
    simulation_d TEXT,  -- TODO: Determine proper type
    simulation_distance TEXT,  -- TODO: Determine proper type
    spawn_protection TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    stance_plug TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    target TEXT,  -- TODO: Determine proper type
    target_instances TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    total_plugins TEXT,  -- TODO: Determine proper type
    track TEXT,  -- TODO: Determine proper type
    type TEXT,  -- TODO: Determine proper type
    un TEXT,  -- TODO: Determine proper type
    up_to_date TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    updates TEXT,  -- TODO: Determine proper type
    version TEXT,  -- TODO: Determine proper type
    version_id TEXT,  -- TODO: Determine proper type
    view_d TEXT,  -- TODO: Determine proper type
    view_distance TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plugins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    _discover_plug TEXT,  -- TODO: Determine proper type
    _enabled TEXT,  -- TODO: Determine proper type
    affected_ TEXT,  -- TODO: Determine proper type
    affected_instances TEXT,  -- TODO: Determine proper type
    all TEXT,  -- TODO: Determine proper type
    an TEXT,  -- TODO: Determine proper type
    as TEXT,  -- TODO: Determine proper type
    author TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    baseline_config_path TEXT,  -- TODO: Determine proper type
    baseline_path TEXT,  -- TODO: Determine proper type
    bool TEXT,  -- TODO: Determine proper type
    bukkit_id TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changelog_url TEXT,  -- TODO: Determine proper type
    check_all_plug TEXT,  -- TODO: Determine proper type
    check_plug TEXT,  -- TODO: Determine proper type
    cicd_provider TEXT,  -- TODO: Determine proper type
    cicd_url TEXT,  -- TODO: Determine proper type
    clone_from_ TEXT,  -- TODO: Determine proper type
    config_file_id TEXT,  -- TODO: Determine proper type
    config_key_count TEXT,  -- TODO: Determine proper type
    config_type TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    cont TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    current_stable_version TEXT,  -- TODO: Determine proper type
    current_version TEXT,  -- TODO: Determine proper type
    currently TEXT,  -- TODO: Determine proper type
    curseforge_id TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    data TEXT,  -- TODO: Determine proper type
    database TEXT,  -- TODO: Determine proper type
    datapack TEXT,  -- TODO: Determine proper type
    datapack_name TEXT,  -- TODO: Determine proper type
    deployment_scope TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    determ TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    difficulty TEXT,  -- TODO: Determine proper type
    discover TEXT,  -- TODO: Determine proper type
    discover_plug TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    dist TEXT,  -- TODO: Determine proper type
    docs_url TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    file_hash TEXT,  -- TODO: Determine proper type
    file_name TEXT,  -- TODO: Determine proper type
    first_seen_at TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    gamemode TEXT,  -- TODO: Determine proper type
    get_ TEXT,  -- TODO: Determine proper type
    github_repo TEXT,  -- TODO: Determine proper type
    group_concat TEXT,  -- TODO: Determine proper type
    hangar_slug TEXT,  -- TODO: Determine proper type
    has_cicd TEXT,  -- TODO: Determine proper type
    has_plug TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    ig TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_count TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    instance_name TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_enabled TEXT,  -- TODO: Determine proper type
    is_installed TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    is_paid TEXT,  -- TODO: Determine proper type
    is_premium TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    l TEXT,  -- TODO: Determine proper type
    last_available_version_at TEXT,  -- TODO: Determine proper type
    last_checked_at TEXT,  -- TODO: Determine proper type
    last_update_check_at TEXT,  -- TODO: Determine proper type
    last_updated_at TEXT,  -- TODO: Determine proper type
    latest_release_date TEXT,  -- TODO: Determine proper type
    latest_version TEXT,  -- TODO: Determine proper type
    level_name TEXT,  -- TODO: Determine proper type
    license TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    m TEXT,  -- TODO: Determine proper type
    max_players TEXT,  -- TODO: Determine proper type
    modr TEXT,  -- TODO: Determine proper type
    modrinth_id TEXT,  -- TODO: Determine proper type
    mtc TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    outdated_plugins TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    parent_tag_id TEXT,  -- TODO: Determine proper type
    platform TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin TEXT,  -- TODO: Determine proper type
    plugin_ TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    plugin_page_url TEXT,  -- TODO: Determine proper type
    plugin_row TEXT,  -- TODO: Determine proper type
    plugins TEXT,  -- TODO: Determine proper type
    plugins_dir TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    properties_json TEXT,  -- TODO: Determine proper type
    pus TEXT,  -- TODO: Determine proper type
    pv TEXT,  -- TODO: Determine proper type
    pvp TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    release_date TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    row TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    scan_all_plug TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    simulation_d TEXT,  -- TODO: Determine proper type
    simulation_distance TEXT,  -- TODO: Determine proper type
    source TEXT,  -- TODO: Determine proper type
    source_identifier TEXT,  -- TODO: Determine proper type
    source_type TEXT,  -- TODO: Determine proper type
    source_url TEXT,  -- TODO: Determine proper type
    spawn_protection TEXT,  -- TODO: Determine proper type
    spigot_id TEXT,  -- TODO: Determine proper type
    stalled_plug TEXT,  -- TODO: Determine proper type
    stalled_version TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    stance_plug TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    substring_ TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    tag_id TEXT,  -- TODO: Determine proper type
    tags TEXT,  -- TODO: Determine proper type
    target TEXT,  -- TODO: Determine proper type
    target_instances TEXT,  -- TODO: Determine proper type
    template_id TEXT,  -- TODO: Determine proper type
    tentional_only TEXT,  -- TODO: Determine proper type
    th TEXT,  -- TODO: Determine proper type
    to TEXT,  -- TODO: Determine proper type
    total_plugins TEXT,  -- TODO: Determine proper type
    track TEXT,  -- TODO: Determine proper type
    un TEXT,  -- TODO: Determine proper type
    update TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    updates TEXT,  -- TODO: Determine proper type
    updates_found TEXT,  -- TODO: Determine proper type
    version TEXT,  -- TODO: Determine proper type
    view_d TEXT,  -- TODO: Determine proper type
    view_distance TEXT,  -- TODO: Determine proper type
    wiki_url TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS rank_config_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key TEXT,  -- TODO: Determine proper type
    config_value TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    rank_name TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ranks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    color_code TEXT,  -- TODO: Determine proper type
    discovered_at TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    inherits_from TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    is_default TEXT,  -- TODO: Determine proper type
    last_seen_at TEXT,  -- TODO: Determine proper type
    permission_count TEXT,  -- TODO: Determine proper type
    player_count TEXT,  -- TODO: Determine proper type
    prefix TEXT,  -- TODO: Determine proper type
    priority TEXT,  -- TODO: Determine proper type
    rank_name TEXT,  -- TODO: Determine proper type
    server_name TEXT,  -- TODO: Determine proper type
    suffix TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    enabled TEXT,  -- TODO: Determine proper type
    last_run_at TEXT,  -- TODO: Determine proper type
    last_run_duration_seconds TEXT,  -- TODO: Determine proper type
    last_run_error TEXT,  -- TODO: Determine proper type
    last_run_result TEXT,  -- TODO: Determine proper type
    last_run_status TEXT,  -- TODO: Determine proper type
    next_run TEXT,  -- TODO: Determine proper type
    next_run_at TEXT,  -- TODO: Determine proper type
    schedule_type TEXT,  -- TODO: Determine proper type
    schedule_value TEXT,  -- TODO: Determine proper type
    task_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS server_properties_baselines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    baseline_type TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    create_baseline_from_ TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    exist TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    properties TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    property_value TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reference TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    scan_ TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    updated_at TEXT,  -- TODO: Determine proper type
    variance_value TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS server_properties_variances (
    id INT AUTO_INCREMENT PRIMARY KEY,
    as TEXT,  -- TODO: Determine proper type
    basel TEXT,  -- TODO: Determine proper type
    conn TEXT,  -- TODO: Determine proper type
    create_baseline_from_ TEXT,  -- TODO: Determine proper type
    cursor TEXT,  -- TODO: Determine proper type
    cv TEXT,  -- TODO: Determine proper type
    d TEXT,  -- TODO: Determine proper type
    detail TEXT,  -- TODO: Determine proper type
    dictionary TEXT,  -- TODO: Determine proper type
    endpo TEXT,  -- TODO: Determine proper type
    exist TEXT,  -- TODO: Determine proper type
    existing TEXT,  -- TODO: Determine proper type
    f TEXT,  -- TODO: Determine proper type
    for TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    insert TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_ TEXT,  -- TODO: Determine proper type
    is_intentional TEXT,  -- TODO: Determine proper type
    jo TEXT,  -- TODO: Determine proper type
    join TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    properties TEXT,  -- TODO: Determine proper type
    property_key TEXT,  -- TODO: Determine proper type
    property_value TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    ra TEXT,  -- TODO: Determine proper type
    reference TEXT,  -- TODO: Determine proper type
    reg TEXT,  -- TODO: Determine proper type
    rowcount TEXT,  -- TODO: Determine proper type
    scan_ TEXT,  -- TODO: Determine proper type
    server_properties_basel TEXT,  -- TODO: Determine proper type
    spv TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status_code TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    timestamp TEXT,  -- TODO: Determine proper type
    variance_value TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS system_health_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    change_type TEXT,  -- TODO: Determine proper type
    changed_at TEXT,  -- TODO: Determine proper type
    changed_by TEXT,  -- TODO: Determine proper type
    component TEXT,  -- TODO: Determine proper type
    config_key TEXT,  -- TODO: Determine proper type
    created_at TEXT,  -- TODO: Determine proper type
    deployed_at TEXT,  -- TODO: Determine proper type
    deployed_by TEXT,  -- TODO: Determine proper type
    deployment_status TEXT,  -- TODO: Determine proper type
    deployment_type TEXT,  -- TODO: Determine proper type
    duration_ms TEXT,  -- TODO: Determine proper type
    float TEXT,  -- TODO: Determine proper type
    from_version TEXT,  -- TODO: Determine proper type
    if TEXT,  -- TODO: Determine proper type
    limit TEXT,  -- TODO: Determine proper type
    metadata TEXT,  -- TODO: Determine proper type
    metric_name TEXT,  -- TODO: Determine proper type
    metric_unit TEXT,  -- TODO: Determine proper type
    metric_value TEXT,  -- TODO: Determine proper type
    notification_type TEXT,  -- TODO: Determine proper type
    operation TEXT,  -- TODO: Determine proper type
    params TEXT,  -- TODO: Determine proper type
    plug TEXT,  -- TODO: Determine proper type
    plugin_name TEXT,  -- TODO: Determine proper type
    query TEXT,  -- TODO: Determine proper type
    recorded_at TEXT,  -- TODO: Determine proper type
    result TEXT,  -- TODO: Determine proper type
    snapshot_at TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    status TEXT,  -- TODO: Determine proper type
    str TEXT,  -- TODO: Determine proper type
    to_version TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tag_conflicts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    conflict_id TEXT,  -- TODO: Determine proper type
    conflict_severity TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_deprecated TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    t1 TEXT,  -- TODO: Determine proper type
    t2 TEXT,  -- TODO: Determine proper type
    tag_a_id TEXT,  -- TODO: Determine proper type
    tag_a_name TEXT,  -- TODO: Determine proper type
    tag_b_id TEXT,  -- TODO: Determine proper type
    tag_b_name TEXT,  -- TODO: Determine proper type
    tc TEXT,  -- TODO: Determine proper type
    usage_count TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tag_dependencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dependency_id TEXT,  -- TODO: Determine proper type
    dependency_type TEXT,  -- TODO: Determine proper type
    dependent_tag_id TEXT,  -- TODO: Determine proper type
    dependent_tag_name TEXT,  -- TODO: Determine proper type
    description TEXT,  -- TODO: Determine proper type
    display_name TEXT,  -- TODO: Determine proper type
    i TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_deprecated TEXT,  -- TODO: Determine proper type
    required_tag_id TEXT,  -- TODO: Determine proper type
    required_tag_name TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    t1 TEXT,  -- TODO: Determine proper type
    t2 TEXT,  -- TODO: Determine proper type
    tc TEXT,  -- TODO: Determine proper type
    td TEXT,  -- TODO: Determine proper type
    usage_count TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tag_hierarchy (
    id INT AUTO_INCREMENT PRIMARY KEY,
    child_tag_id TEXT,  -- TODO: Determine proper type
    name TEXT,  -- TODO: Determine proper type
    p TEXT,  -- TODO: Determine proper type
    parent_tag_id TEXT,  -- TODO: Determine proper type
    t TEXT,  -- TODO: Determine proper type
    update_available TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS world_config_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key TEXT,  -- TODO: Determine proper type
    config_value TEXT,  -- TODO: Determine proper type
    plugin_id TEXT,  -- TODO: Determine proper type
    stance_id TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS worlds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    discovered_at TEXT,  -- TODO: Determine proper type
    environment TEXT,  -- TODO: Determine proper type
    folder_size_bytes TEXT,  -- TODO: Determine proper type
    generator TEXT,  -- TODO: Determine proper type
    instance_id TEXT,  -- TODO: Determine proper type
    is_active TEXT,  -- TODO: Determine proper type
    last_modified TEXT,  -- TODO: Determine proper type
    last_seen_at TEXT,  -- TODO: Determine proper type
    region_count TEXT,  -- TODO: Determine proper type
    seed TEXT,  -- TODO: Determine proper type
    world_name TEXT,  -- TODO: Determine proper type
    world_type TEXT,  -- TODO: Determine proper type
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

```
