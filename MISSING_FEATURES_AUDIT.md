# Missing Features Audit - Requested but Not Implemented

**Date**: 2025-11-18  
**Context**: User asked to verify change tracking, key remapping/redirection, and other requested features

---

## 1. ❌ Config Key Migration/Remapping System

**Status**: **NOT IMPLEMENTED**

### What You Asked For:
- Track when plugin authors rename/move config keys between versions
- Redirect old key names to new key names automatically
- Example: `old.path.enabled` → `new.location.enable-feature`

### What Exists:
- ❌ No `config_key_migrations` table
- ❌ No key remapping logic in `config_updater.py`
- ❌ No deprecation tracking
- ✅ Only basic value update exists (`_update_yaml_key()`)

### What's Documented:
- `WIP_PLAN/PLUGIN_ANALYSIS_NOTES.md` mentions version migration issues:
  - ExcellentEnchants: Enchant ID mappings change between versions
  - BentoBox: Challenge ID changes causing data loss
  - JobListings: Storage format changes (config → database)
  - CombatPets: NBT data structure changes

### What's Needed:

```sql
-- NOT IN DATABASE YET
CREATE TABLE config_key_migrations (
    migration_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(64) NOT NULL,
    old_key_path VARCHAR(512) NOT NULL,
    new_key_path VARCHAR(512) NOT NULL,
    
    from_version VARCHAR(32),  -- When key was deprecated
    to_version VARCHAR(32),    -- When migration is needed
    
    migration_type ENUM('rename', 'move', 'split', 'merge', 'remove') DEFAULT 'rename',
    value_transform TEXT,      -- Optional SQL/Python to transform value
    
    is_breaking BOOLEAN DEFAULT false,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_migration (plugin_name, old_key_path, from_version)
) ENGINE=InnoDB;
```

```python
# NOT IN config_updater.py YET
def apply_key_migration(self, plugin_name: str, old_config: Dict, new_version: str):
    """Apply key migrations when updating plugin version"""
    # Get migrations for this plugin/version
    migrations = db.get_migrations(plugin_name, new_version)
    
    for migration in migrations:
        old_path = migration['old_key_path']
        new_path = migration['new_key_path']
        
        # Extract value from old location
        old_value = get_nested_value(old_config, old_path)
        
        # Apply value transform if needed
        if migration['value_transform']:
            new_value = eval_transform(old_value, migration['value_transform'])
        else:
            new_value = old_value
        
        # Set to new location
        set_nested_value(old_config, new_path, new_value)
        
        # Remove old key if migration type is 'move'
        if migration['migration_type'] == 'move':
            delete_nested_key(old_config, old_path)
```

---

## 2. ✅ Change Tracking (PARTIALLY IMPLEMENTED)

**Status**: **EXISTS BUT INCOMPLETE**

### What You Asked For:
- Track all config changes
- Audit trail of who changed what when
- History of deployments

### What Exists:

#### ✅ File-Based Audit Logs
**Location**: `config_updater.py:559-615`

```python
def log_change(self, change: Dict[str, Any], result: Dict[str, Any]):
    """Log change to immutable audit trail"""
    audit_dir = self.utildata_path / ".audit_logs"
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'user': os.getenv('USER', 'unknown'),
        'change_request': change,
        'result': result,
        'success': result.get('success', False),
        'affected_files': result.get('affected_files', []),
        'backup_path': result.get('backup_path', None)
    }
    
    # Individual log file
    log_file = audit_dir / f"config_change_{timestamp}_{pid}.log"
    
    # Daily summary log
    daily_log = audit_dir / f"daily_{date}.log"
```

**Writes to**: `e:\homeamp.ampdata\utildata\.audit_logs\`

#### ❌ Database Audit Trail (NOT IMPLEMENTED)
**Expected from**: `add_comprehensive_tracking.sql`

```sql
-- THIS TABLE WAS NEVER CREATED
CREATE TABLE IF NOT EXISTS config_change_history (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    plugin_id VARCHAR(64),
    config_file_path VARCHAR(512),
    config_key_path VARCHAR(512),
    
    old_value TEXT,
    new_value TEXT,
    
    change_type ENUM('manual', 'automated', 'drift_fix', 'version_upgrade'),
    change_reason TEXT,
    changed_by VARCHAR(64),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    deployment_id INT,
    is_reverted BOOLEAN DEFAULT FALSE,
    reverted_at TIMESTAMP NULL
);
```

#### ❌ Deployment History (NOT IN DATABASE)

```sql
-- MENTIONED IN DOCS, NEVER CREATED
CREATE TABLE IF NOT EXISTS deployment_history (
    deployment_id INT AUTO_INCREMENT PRIMARY KEY,
    deployment_type ENUM('config', 'plugin', 'full'),
    
    target_instances TEXT,  -- JSON array
    deployed_changes TEXT,  -- JSON array of change IDs
    
    deployed_by VARCHAR(64),
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployment_status ENUM('pending', 'success', 'partial', 'failed'),
    
    error_log TEXT,
    rollback_id INT
);
```

### What's Missing:

1. **Database persistence** - Logs are only in files
2. **Web UI access** - Can't query change history from API
3. **Change correlation** - Can't link deployment → changes → results
4. **Rollback tracking** - Can identify what was deployed when
5. **Cross-instance tracking** - See which instances got which changes

---

## 3. ❌ Config Version History

**Status**: **NOT IMPLEMENTED**

### What Exists:
- `add_comprehensive_tracking.sql` proposes `plugin_version_history` table
- **BUT IT WAS NEVER CREATED** (confirmed in `DATABASE_REALITY.md`)

### What's Needed:

```sql
-- NOT IN DATABASE
CREATE TABLE plugin_version_history (
    version_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(64) NOT NULL,
    version_string VARCHAR(32) NOT NULL,
    
    release_date DATETIME,
    changelog TEXT,
    breaking_changes TEXT,  -- Documented breaking changes
    config_migrations TEXT, -- JSON: Which keys changed
    
    minecraft_versions TEXT,  -- Supported MC versions
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY (plugin_id, version_string)
);
```

**Use Case**: When EliteMobs updates from 8.9.5 → 9.0.0:
1. Query version_history for changelog
2. Check `config_migrations` for key renames
3. Apply migrations automatically
4. Log the upgrade in `deployment_history`

---

## 4. ❌ Backward Compatibility Detection

**Status**: **NOT IMPLEMENTED**

### What Was Found:
- `PLUGIN_ANALYSIS_NOTES.md` documents many version compatibility issues
- No automated detection exists

### Problems Documented:
1. **ExcellentEnchants**: Enchant IDs change, items show "Unknown Enchantment"
2. **BentoBox**: Challenge IDs change, progress lost
3. **CombatPets**: NBT structure changes, pet items invalid
4. **JobListings**: Storage migrates YAML→DB, data lost
5. **ViaVersion/ViaBackwards**: Version support differences

### What's Needed:

```python
# NOT IMPLEMENTED
class BackwardCompatibilityChecker:
    """Check if plugin update will break existing data"""
    
    def check_compatibility(self, plugin_name: str, current_version: str, new_version: str):
        """Check if upgrade is safe"""
        
        # 1. Check config_key_migrations for breaking changes
        migrations = self.get_migrations(plugin_name, current_version, new_version)
        breaking = [m for m in migrations if m['is_breaking']]
        
        # 2. Check plugin_version_history for changelog warnings
        version_info = self.get_version_info(plugin_name, new_version)
        changelog_warnings = self.parse_breaking_changes(version_info['changelog'])
        
        # 3. Check known data format changes
        data_format_changes = self.check_data_format_migrations(plugin_name, new_version)
        
        return {
            'safe': len(breaking) == 0 and len(changelog_warnings) == 0,
            'breaking_migrations': breaking,
            'changelog_warnings': changelog_warnings,
            'data_format_changes': data_format_changes,
            'recommendation': 'test_on_dev' if breaking else 'safe_to_deploy'
        }
```

---

## 5. ⚠️ Variance Cache Refresh Tracking

**Status**: **EXISTS BUT NO HISTORY**

### What Exists:
- `config_variance_cache` table tracks current variance state
- `populate_config_cache.py` regenerates cache from live configs

### What's Missing:
- **No history** - Can't see how variance changed over time
- **No comparison** - Can't see "variance was fixed on Nov 10, drifted again Nov 15"

### What's Needed:

```sql
-- NOT IN DATABASE
CREATE TABLE config_variance_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_name VARCHAR(64),
    config_key VARCHAR(512),
    
    variance_type VARCHAR(16),
    is_expected_variance BOOLEAN,
    
    instance_count INT,
    unique_values INT,
    variance_reason TEXT,
    
    snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_variance_history_key (plugin_name, config_key),
    INDEX idx_variance_history_time (snapshot_timestamp)
);
```

**Use Case**: 
- Run drift detection daily
- Store snapshot in `config_variance_history`
- Compare today vs. last week: "3 new drift items detected"

---

## 6. ❌ Config Rule Change Tracking

**Status**: **NOT IMPLEMENTED**

### What Exists:
- `config_rules` table has `created_at`, `last_modified_at`
- **NO HISTORY** of what the rule used to be

### What's Missing:

```sql
-- NOT IN DATABASE
CREATE TABLE config_rule_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    rule_id INT NOT NULL,
    
    plugin_name VARCHAR(64),
    config_key VARCHAR(512),
    scope_type VARCHAR(16),
    scope_selector VARCHAR(128),
    
    old_value TEXT,
    new_value TEXT,
    
    changed_by VARCHAR(64),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_reason TEXT,
    
    FOREIGN KEY (rule_id) REFERENCES config_rules(rule_id)
);
```

**Trigger needed**:
```sql
-- Auto-log rule changes
CREATE TRIGGER config_rule_history_trigger
AFTER UPDATE ON config_rules
FOR EACH ROW
BEGIN
    INSERT INTO config_rule_history 
        (rule_id, plugin_name, config_key, old_value, new_value, changed_by)
    VALUES 
        (OLD.rule_id, OLD.plugin_name, OLD.config_key, OLD.config_value, NEW.config_value, NEW.last_modified_by);
END;
```

---

## 7. ❌ Plugin Installation/Removal Tracking

**Status**: **NOT IMPLEMENTED**

### What Exists:
- `plugins` table tracks which plugins exist
- `instance_plugins` tracks which instances have which plugins

### What's Missing:
- **NO HISTORY** - Can't see when plugin was added/removed
- **NO WHO** - Can't see who added/removed it

```sql
-- NOT IN DATABASE
CREATE TABLE plugin_installation_history (
    install_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    plugin_id VARCHAR(64),
    
    action ENUM('install', 'remove', 'update', 'enable', 'disable'),
    version_from VARCHAR(32),
    version_to VARCHAR(32),
    
    performed_by VARCHAR(64),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    
    INDEX idx_plugin_history_instance (instance_id),
    INDEX idx_plugin_history_plugin (plugin_id),
    INDEX idx_plugin_history_time (performed_at)
);
```

---

## Summary Table

| Feature | Status | Documented | Tables Exist | Code Exists | Web API |
|---------|--------|------------|--------------|-------------|---------|
| **Key Migration/Remapping** | ❌ None | ✅ Issues noted | ❌ No | ❌ No | ❌ No |
| **File-Based Audit Logs** | ✅ Works | ✅ Yes | N/A | ✅ Yes | ❌ No |
| **Database Audit Trail** | ❌ None | ✅ Proposed | ❌ No | ❌ No | ❌ No |
| **Deployment History** | ❌ None | ✅ Mentioned | ❌ No | ❌ No | ❌ No |
| **Plugin Version History** | ❌ None | ✅ Proposed | ❌ No | ❌ No | ❌ No |
| **Backward Compat Check** | ❌ None | ✅ Issues noted | ❌ No | ❌ No | ❌ No |
| **Variance Change History** | ❌ None | ❌ No | ❌ No | ❌ No | ❌ No |
| **Config Rule History** | ❌ None | ❌ No | ❌ No | ❌ No | ❌ No |
| **Plugin Install History** | ❌ None | ❌ No | ❌ No | ❌ No | ❌ No |

---

## What Actually Works Today

### ✅ Implemented Features:

1. **Config Rules** - Define expected config values per scope
2. **Variance Cache** - Detect differences from baseline (current snapshot only)
3. **File-Based Audit Logs** - JSON logs in `.audit_logs/` directory
4. **Plugin CRUD** - Add/remove/update plugins via API
5. **Meta Tag CRUD** - Add/remove/update tags via API
6. **Config Rule CRUD** - Add/remove/update rules via API

### ❌ What You Can't Do Yet:

1. **Track config changes over time** - No database history
2. **Remap deprecated config keys** - No migration system
3. **See deployment history** - Not stored anywhere
4. **Query audit logs via API** - Only flat files
5. **Track plugin version upgrades** - No version history
6. **Detect breaking changes** - No compatibility checker
7. **Compare variance over time** - No historical snapshots
8. **See rule change history** - No audit trail for rules

---

## Recommendation: Priority Implementation Order

### High Priority (Core Functionality):
1. **config_key_migrations** table + migration logic
2. **config_change_history** table + trigger
3. **deployment_history** table + API endpoints
4. **API endpoints** to query audit logs

### Medium Priority (Operational Visibility):
5. **plugin_version_history** table + changelog parser
6. **config_variance_history** table + daily snapshot
7. **config_rule_history** table + UPDATE trigger

### Low Priority (Nice to Have):
8. **plugin_installation_history** table
9. **Backward compatibility checker** (heuristic-based)
10. **Web UI** for viewing all history tables

---

## Files That Mention These Features

1. `add_comprehensive_tracking.sql` - Proposes many tables (NEVER CREATED)
2. `config_updater.py` - Has file-based audit logging
3. `PLUGIN_ANALYSIS_NOTES.md` - Documents version migration issues
4. `DATABASE_REALITY.md` - Confirms tables don't exist
5. `CODEBASE_REALITY_CHECK.md` - Notes redundant schemas
6. `CONFIG_WORKFLOW.md` - Describes desired audit trail format

---

---

## 10. ❌ Approval Workflow

**Status**: **PARTIALLY IMPLEMENTED (File-Based Only)**

### What Exists:
- `DeviationManager` in `models.py` - review workflow for deviations
- `DeviationStatus` enum: PENDING_REVIEW, APPROVED_GOOD, FLAGGED_BAD, FIXED
- Stores reviews in JSON files, not database

### What's Missing:
- **No database table** for approval requests
- **No multi-user approval** (can't require 2+ approvers)
- **No expiration** of pending approvals
- **No risk-based routing** (high-risk changes need senior approval)
- **No approval history** (who approved what when)

### What's Needed:

```sql
CREATE TABLE change_approval_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    request_type ENUM('config_change', 'deployment', 'plugin_update', 'rule_change'),
    
    requested_by VARCHAR(64),
    requested_at TIMESTAMP,
    
    risk_level ENUM('low', 'medium', 'high', 'critical'),
    impact_scope VARCHAR(32),
    
    approval_status ENUM('pending', 'approved', 'rejected', 'cancelled'),
    approved_by VARCHAR(64),
    approved_at TIMESTAMP,
    
    deployment_id INT  -- Link to actual deployment
);
```

**Current Limitation**: All changes go through manual JSON file review, no automated approval routing

---

## 11. ❌ Notification System

**Status**: **NOT IMPLEMENTED**

### What Was Found:
- `PLUGIN_ANALYSIS_NOTES.md` mentions webhook notification issues
- Discord integration problems documented (spicord plugin)
- No notification code in codebase

### What's Missing:
- **No notification log**
- **No webhook support**
- **No email alerts**
- **No Discord/Slack integration**
- **No deployment notifications**

### What's Needed:

```python
# NOT IN CODEBASE
class NotificationService:
    """Send notifications about system events"""
    
    def notify_deployment(self, deployment_id: int, status: str):
        """Notify about deployment success/failure"""
        
    def notify_drift_detected(self, drift_count: int, critical_items: list):
        """Alert when critical drift detected"""
        
    def notify_approval_needed(self, request_id: int, risk_level: str):
        """Request approval for high-risk change"""
        
    def notify_plugin_update(self, plugin: str, new_version: str):
        """Alert about available plugin update"""
```

```sql
CREATE TABLE notification_log (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    notification_type ENUM('deployment', 'drift_alert', 'plugin_update', 'approval_request'),
    recipient VARCHAR(128),
    delivery_method ENUM('email', 'webhook', 'discord', 'slack'),
    sent_at TIMESTAMP,
    delivery_status ENUM('pending', 'sent', 'failed')
);
```

**Use Cases**:
- Email admin when deployment fails
- Discord alert for critical drift detection
- Slack message for plugin updates available
- Webhook to external monitoring system

---

## 12. ❌ Scheduled Tasks / Automation

**Status**: **PARTIAL (Code exists, no tracking)**

### What Exists:
- `scheduler_installer.py` - Creates systemd timers/cron
- `UpdateSchedulerInstaller` class - generates timer configs
- `instance_settings.py` - auto-deploy settings per instance

### What's Missing:
- **No task history table** - Can't see when tasks ran
- **No task status tracking** - Don't know if last run succeeded
- **No task configuration UI** - Must edit files manually
- **No task dependency management** - Can't chain tasks

### What's Needed:

```sql
CREATE TABLE scheduled_tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(128),
    task_type ENUM('drift_check', 'plugin_update_check', 'variance_snapshot', 'backup'),
    
    schedule_expression VARCHAR(64),  -- Cron expression
    
    last_run_at TIMESTAMP,
    last_run_status ENUM('success', 'failed', 'partial'),
    last_run_duration_seconds INT,
    
    next_run_at TIMESTAMP,
    is_enabled BOOLEAN
);
```

**Example Automated Tasks**:
1. **Hourly**: Check for plugin updates
2. **Daily 3am**: Run drift detection
3. **Daily 4am**: Snapshot variance cache to history
4. **Weekly**: Clean up old audit logs
5. **Monthly**: Generate compliance report

---

## 13. ❌ Rollback / Revert Capability

**Status**: **STUB ONLY**

### What Exists:
- `config_updater.py` has `rollback_change()` method stub
- Creates backups before changes
- **WIP_PLAN** notes "Rollback endpoint exists" but "Does rollback actually work? Unknown"

### What's Missing:
- **No rollback verification** - Backups exist but never tested
- **No rollback history** - Don't track what was rolled back
- **No partial rollback** - Can't undo specific changes from a deployment
- **No rollback UI** - Must manually restore files

### What's Needed:

```python
# STUB IN config_updater.py
def rollback_change(self, change_id: str) -> Dict[str, Any]:
    """
    Rollback a change (NOT FULLY IMPLEMENTED)
    
    Args:
        change_id: Change ID to rollback
        
    Returns:
        Rollback result
    """
    # TODO: Implement actual rollback logic
    # 1. Find backup from change
    # 2. Verify backup integrity
    # 3. Restore files
    # 4. Restart services if needed
    # 5. Verify rollback success
    # 6. Log rollback in history
    pass
```

**Database Support Needed**:
- Link `deployment_history.rollback_deployment_id` to original
- Track rollback success/failure
- Store pre-rollback snapshot for re-rollback

---

## 14. ❌ Performance Metrics / Monitoring

**Status**: **NOT IMPLEMENTED**

### What Was Found:
- `YUNOHOST_CONFIG.md` mentions health check monitoring
- `PLUGIN_ANALYSIS_NOTES.md` mentions spark profiler for performance
- No metrics collection in codebase

### What's Missing:
- **No performance metrics** - Response time, memory, CPU
- **No health checks** - Don't know if services are up
- **No drift count trends** - Can't see if drift increasing over time
- **No plugin update lag** - Don't track how long plugins are outdated

### What's Needed:

```sql
CREATE TABLE system_health_metrics (
    metric_id INT AUTO_INCREMENT PRIMARY KEY,
    metric_source VARCHAR(32),  -- 'web_api', 'agent', 'database'
    instance_id VARCHAR(16),
    
    metric_type VARCHAR(64),  -- 'response_time', 'drift_count', 'plugin_count'
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(16),  -- 'ms', 'count', 'MB'
    
    recorded_at TIMESTAMP
);
```

**Metrics to Track**:
1. API response time (ms)
2. Agent heartbeat status
3. Drift detection count per day
4. Plugin update lag (days behind latest)
5. Database query performance
6. Config deployment success rate
7. Variance cache size

---

## 15. ❌ Permission / Access Control

**Status**: **NOT IMPLEMENTED**

### What Was Found:
- `YUNOHOST_CONFIG.md` has YunoHost permission integration
- No RBAC in actual codebase
- API has no authentication

### What's Missing:
- **No user authentication** - API is wide open
- **No role-based access** - Everyone has full admin
- **No audit of who did what** - Only logs username if provided
- **No permission checks** - Can't restrict certain operations

### What's Needed:

```python
# NOT IN CODEBASE
class PermissionChecker:
    """Check if user has permission for action"""
    
    def can_deploy(self, user: str, scope: str) -> bool:
        """Check if user can deploy to given scope"""
        
    def can_approve(self, user: str, risk_level: str) -> bool:
        """Check if user can approve changes at risk level"""
        
    def can_modify_rules(self, user: str) -> bool:
        """Check if user can modify config rules"""
```

**Roles Needed**:
- **Viewer**: Read-only access
- **Operator**: Deploy approved changes
- **Admin**: Create/approve changes
- **Super Admin**: Modify config rules, delete history

---

## 16. ❌ Config Templates / Blueprints

**Status**: **NOT IMPLEMENTED**

### What Was Found:
- `YUNOHOST_CONFIG.md` has config file templates
- `WIP_PLAN/08_DEPLOYMENT_READINESS.md` notes "No agent.yaml template"
- No template system in codebase

### What's Missing:
- **No config templates** - Must configure each instance manually
- **No instance blueprints** - Can't clone config from template
- **No plugin presets** - Can't deploy standard plugin sets
- **No variable substitution** - Must hardcode values

### What Exists (Partial):
- `config_variables` table for template substitution ({{SHORTNAME}}, etc.)
- But no template files or UI to use them

### What's Needed:

```sql
CREATE TABLE config_templates (
    template_id INT AUTO_INCREMENT PRIMARY KEY,
    template_name VARCHAR(128),
    template_type ENUM('instance', 'plugin_set', 'config_file'),
    
    description TEXT,
    config_json TEXT,  -- Template with {{VARIABLES}}
    
    created_by VARCHAR(64),
    is_system_template BOOLEAN
);

CREATE TABLE template_variables (
    variable_id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT,
    variable_name VARCHAR(64),
    variable_type VARCHAR(16),  -- string, number, boolean, list
    default_value TEXT,
    is_required BOOLEAN
);
```

**Use Cases**:
- "New Survival Instance" template → Auto-configure 50 plugins
- "Creative Build Server" template → Different plugin set
- "Event Server" template → Temporary config preset

---

## 17. ❌ Conflict Detection / Dependency Checks

**Status**: **NOT IMPLEMENTED**

### What Was Found:
- `consolidate_configs.py` has comment about avoiding conflicts
- `PLUGIN_ANALYSIS_NOTES.md` documents many plugin incompatibilities
- No conflict detection code

### What's Missing:
- **No plugin conflict detection** - Don't warn about incompatible plugins
- **No version dependency checks** - Don't verify required dependencies
- **No config validation** - Don't check if config values are valid
- **No merge conflict detection** - Don't detect conflicting config rules

### What's Needed:

```python
# NOT IN CODEBASE
class ConflictDetector:
    """Detect conflicts before deployment"""
    
    def check_plugin_conflicts(self, plugins: List[str]) -> List[str]:
        """Check for incompatible plugin combinations"""
        # e.g., "EssentialsX conflicts with CMI economy"
        
    def check_dependency_versions(self, plugin: str, version: str) -> bool:
        """Check if plugin version has required dependencies"""
        # e.g., "Requires ProtocolLib >= 5.0.0"
        
    def check_config_rule_conflicts(self, new_rule: dict) -> List[dict]:
        """Check if new rule conflicts with existing rules"""
        # e.g., "Rule at INSTANCE scope conflicts with SERVER scope"
        
    def validate_config_value(self, key: str, value: Any, schema: dict) -> bool:
        """Validate config value against schema"""
        # e.g., "Port must be 1024-65535"
```

**Database Support**:
```sql
CREATE TABLE plugin_conflicts (
    conflict_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_a VARCHAR(64),
    plugin_b VARCHAR(64),
    conflict_type ENUM('incompatible', 'duplicate_feature', 'performance'),
    severity ENUM('error', 'warning', 'info'),
    notes TEXT
);
```

---

## 18. ❌ Testing / Validation Framework

**Status**: **NOT IMPLEMENTED**

### What Was Found:
- No test files in codebase
- No pytest, unittest, or test directories
- `WIP_PLAN` mentions "Can't verify code works without production"

### What's Missing:
- **No unit tests**
- **No integration tests**
- **No config validation tests**
- **No deployment dry-run** capability
- **No CI/CD pipeline**

### What's Needed:

```bash
# NOT IN REPO
software/homeamp-config-manager/tests/
    test_drift_detector.py
    test_config_updater.py
    test_api_endpoints.py
    test_database_schema.py
    test_variance_cache.py
```

**Validation Needed**:
1. **Config syntax validation** - Verify YAML is valid before deployment
2. **Rule priority validation** - Check scope hierarchy is correct
3. **Migration testing** - Test key migrations work correctly
4. **Deployment simulation** - Dry-run without actual changes
5. **Rollback testing** - Verify backups can be restored

---

## 19. ❌ Environment Configuration

**Status**: **INCOMPLETE**

### What Exists:
- `settings.py` exists with hardcoded defaults
- Environment variables referenced but not documented

### What's Missing:
- **No .env.example** file
- **No environment documentation**
- **No secrets management**
- **No production vs dev configs**

### What's Needed:

```bash
# NOT IN REPO
.env.example

# Database
DB_HOST=135.181.212.169
DB_PORT=3369
DB_USER=sqlworkerSMP
DB_PASSWORD=<from environment>
DB_NAME=asmp_config

# MinIO
MINIO_HOST=135.181.212.169
MINIO_PORT=3800
MINIO_ACCESS_KEY=<from environment>
MINIO_SECRET_KEY=<from environment>

# Redis
REDIS_HOST=135.181.212.169
REDIS_PORT=6379
REDIS_PASSWORD=<from environment>

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=<from environment>

# Agent
AGENT_HOST=0.0.0.0
AGENT_PORT=8001
AGENT_API_KEY=<from environment>
```

---

## 20. ❌ Cache Management

**Status**: **REDIS EXISTS BUT NOT USED**

### What Exists:
- Redis mentioned in architecture docs
- `config_variance_cache` table (SQL, not Redis)

### What's Missing:
- **No Redis integration code**
- **No cache invalidation**
- **No TTL management**
- **No cache hit/miss metrics**

### What's Needed:

```python
# NOT IN CODEBASE
class CacheManager:
    """Manage Redis cache for performance"""
    
    def cache_variance_results(self, key: str, data: dict, ttl: int = 3600):
        """Cache variance detection results"""
        
    def invalidate_instance_cache(self, instance_id: str):
        """Clear cache when instance config changes"""
        
    def get_cached_drift_report(self, instance_id: str) -> Optional[dict]:
        """Get cached drift report if still valid"""
```

**Cache Strategy**:
- Variance detection results (1 hour TTL)
- Plugin update info (6 hour TTL)
- Instance config snapshots (until deployment)
- API response caching (5 minutes)

---

## Updated Summary Table

| Feature | Status | Database Tables | Code | API | Priority |
|---------|--------|-----------------|------|-----|----------|
| **Key Migration** | ❌ | ❌ | ❌ | ❌ | 🔴 HIGH |
| **Change History (DB)** | ❌ | ❌ | ⚠️ Files | ❌ | 🔴 HIGH |
| **Deployment History** | ❌ | ❌ | ❌ | ❌ | 🔴 HIGH |
| **Rule Change History** | ❌ | ❌ | ❌ | ❌ | 🟡 MEDIUM |
| **Variance History** | ❌ | ❌ | ❌ | ❌ | 🟡 MEDIUM |
| **Plugin Install History** | ❌ | ❌ | ❌ | ❌ | 🟡 MEDIUM |
| **Approval Workflow** | ⚠️ | ❌ | ⚠️ JSON | ⚠️ | 🟡 MEDIUM |
| **Notifications** | ❌ | ❌ | ❌ | ❌ | 🟡 MEDIUM |
| **Scheduled Tasks** | ⚠️ | ❌ | ✅ | ❌ | 🟢 LOW |
| **Rollback** | ⚠️ | ❌ | ⚠️ Stub | ❌ | 🔴 HIGH |
| **Performance Metrics** | ❌ | ❌ | ❌ | ❌ | 🟢 LOW |
| **Access Control** | ❌ | ❌ | ❌ | ❌ | 🟡 MEDIUM |
| **Config Templates** | ⚠️ | ⚠️ Table | ❌ | ❌ | 🟡 MEDIUM |
| **Conflict Detection** | ❌ | ❌ | ❌ | ❌ | 🟡 MEDIUM |
| **Testing Framework** | ❌ | N/A | ❌ | ❌ | 🟡 MEDIUM |
| **Environment Config** | ⚠️ | N/A | ⚠️ | N/A | 🟡 MEDIUM |
| **Cache Management** | ❌ | N/A | ❌ | ❌ | 🟢 LOW |
| **Backward Compat Check** | ❌ | ❌ | ❌ | ❌ | 🟢 LOW |

---

## OPTION C: Full Tracking Suite Implementation

**Created**: `scripts/add_tracking_history_tables.sql`

### What It Adds (11 New Tables):

1. **config_key_migrations** - Track config key renames between versions
2. **config_change_history** - Complete audit trail of all changes
3. **deployment_history** - Track all deployments with outcomes
4. **deployment_changes** - Link changes to deployments
5. **config_rule_history** - Auto-track rule modifications (with triggers)
6. **config_variance_history** - Historical variance snapshots
7. **plugin_installation_history** - Plugin lifecycle tracking
8. **change_approval_requests** - Approval workflow database
9. **notification_log** - All notifications sent by system
10. **scheduled_tasks** - Automated task tracking
11. **system_health_metrics** - Time-series performance data

### Implementation Priority:

**Phase 1: Core Tracking** (Deploy to production ASAP)
```bash
# Create tables
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p asmp_config < scripts/add_tracking_history_tables.sql

# Verify
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p asmp_config -e "SHOW TABLES LIKE '%history%';"
```

**Phase 2: Code Integration** (Modify existing services)
- Update `config_updater.py` → Write to `config_change_history` instead of files
- Update `api.py` → Add endpoints for querying history tables
- Create `migration_applier.py` → Apply key migrations automatically
- Create `deployment_manager.py` → Track deployments in database

**Phase 3: New Features** (Build what doesn't exist)
- `notification_service.py` → Discord/email alerts
- `approval_workflow.py` → Multi-user approval routing
- `rollback_manager.py` → Actual rollback implementation
- `metrics_collector.py` → Gather performance metrics

**Phase 4: UI/UX** (Web interface)
- History viewer (changes, deployments, approvals)
- Approval dashboard (pending requests)
- Metrics dashboard (charts, trends)
- Notification preferences

---

**Next Steps**: Execute Option C?
1. ✅ **SQL created**: `add_tracking_history_tables.sql`
2. ⏳ **Deploy to database**: Run SQL on production
3. ⏳ **Update code**: Integrate with existing services
4. ⏳ **Add API endpoints**: Query history via REST API
5. ⏳ **Build new features**: Notifications, approvals, metrics
