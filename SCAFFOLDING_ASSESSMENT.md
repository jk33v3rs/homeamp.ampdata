# 🎯 Scaffolding Assessment for 42 TODO Implementation

**Analysis Date:** November 18, 2025  
**Codebase:** homeamp-config-manager  
**Schema:** create_dynamic_metadata_system.sql (524 lines)

---

## 📊 Executive Summary

**Overall Readiness:** 🟡 **MODERATE (65%)**

| Category | Readiness | Status |
|----------|-----------|--------|
| **Database Schema** | 🟢 85% | Well-structured, needs extensions |
| **Agent Discovery** | 🟢 90% | Excellent foundation exists |
| **YAML Handling** | 🔴 40% | Basic PyYAML only, no ruamel |
| **File Watching** | 🟡 60% | Watchdog exists for tiles, not plugins |
| **Instance Tracking** | 🔴 30% | Missing folder names & paths |
| **Config Modification** | 🔴 35% | Read-only, no write capability |
| **Multi-Level Scopes** | 🔴 20% | Only 4 scopes, missing WORLD/RANK/PLAYER |
| **API Endpoints** | 🟢 75% | Good foundation, needs expansion |
| **UI Components** | 🟡 50% | Basic UIs exist, need multi-level views |

---

## ✅ **STRONG SCAFFOLDING** (What We Have)

### 1️⃣ **Auto-Discovery Agent** ✨ **EXCELLENT**
**Files:**
- `production_endpoint_agent.py` (474 lines)
- `agent_database_methods.py` (446 lines)  
- `agent_cicd_methods.py` (450+ lines)
- `agent_update_methods.py`

**Capabilities:**
- ✅ Scans `/home/amp/.ampdata/instances` dynamically
- ✅ Discovers plugins from JAR files
- ✅ Reads `plugin.yml` from ZIP archives
- ✅ Discovers datapacks from world folders
- ✅ Reads `pack.mcmeta`
- ✅ Calculates file hashes (SHA-256)
- ✅ Platform detection (Paper/Fabric/NeoForge)
- ✅ Minecraft version extraction
- ✅ Server properties scanning
- ✅ Discovery run tracking

**Code Quality:** Professional, well-structured mixins

**Gap:** Missing `Instance.conf` parsing to get folder names and AMP UUIDs

---

### 2️⃣ **Database Schema** ✨ **VERY GOOD**
**File:** `create_dynamic_metadata_system.sql` (524 lines)

**Tables Created:**
- ✅ `meta_tag_categories` - User-extensible categories
- ✅ `meta_tags` - Tags with deprecation support
- ✅ `instance_meta_tags` - Instance tagging with confidence scores
- ✅ `plugins` - Full plugin registry with CI/CD fields
- ✅ `instance_plugins` - Per-instance installations with hashes
- ✅ `datapacks` - Datapack catalog
- ✅ `instance_datapacks` - Per-world datapack tracking
- ✅ `instance_server_properties` - server.properties as JSON
- ✅ `instance_platform_configs` - Paper/Spigot/Bukkit configs
- ✅ `discovery_runs` - Discovery session tracking
- ✅ `plugin_update_queue` - Scheduled updates
- ✅ `datapack_deployment_queue` - Datapack deployments
- ✅ `cicd_webhook_events` - Webhook integration

**Existing (from add_config_rules_tables.sql):**
- ✅ `config_rules` - 4-scope hierarchy (GLOBAL/SERVER/META_TAG/INSTANCE)
- ✅ `config_substitution_variables` - Variable system

**Gap:** Missing tables for:
- ❌ `endpoint_config_files` - Track config file locations
- ❌ `endpoint_config_backups` - Backup system
- ❌ `world_meta_tags`, `rank_meta_tags`, `player_meta_tags`
- ❌ Extended `scope_type` enum for WORLD/RANK/PLAYER

---

### 3️⃣ **CI/CD Integration** ✨ **EXCELLENT**
**File:** `agent_cicd_methods.py`

**Platforms Supported:**
- ✅ Modrinth API v2
- ✅ Hangar API v1
- ✅ GitHub Releases
- ✅ Jenkins builds

**Features:**
- ✅ Version comparison
- ✅ Update queueing
- ✅ Download management
- ✅ Plugin deployment
- ✅ Webhook processing
- ✅ Update strategies (manual/notify/auto_stable/auto_latest)

**Gap:** None - this is production-ready

---

### 4️⃣ **File System Watcher** 🟡 **EXISTS BUT WRONG USE CASE**
**File:** `tile_watcher.py` (327 lines)

**Current Use:**
- ✅ Uses `watchdog` library
- ✅ Monitors file changes
- ✅ Batch processing with delays
- ✅ Event handlers (created/modified/deleted)

**Problem:** Only watches Pl3xMap tiles, NOT plugin folders

**What We Need:**
```python
# Watch these directories:
/home/amp/.ampdata/instances/*/Minecraft/plugins/
/home/amp/.ampdata/instances/*/Minecraft/world/*/datapacks/
```

**Effort:** LOW - Just adapt existing tile_watcher code

---

### 5️⃣ **Config Reading** 🟡 **READ-ONLY**
**File:** `config_reader.py`

**Capabilities:**
- ✅ Read plugin configs
- ✅ Parse YAML files
- ✅ Extract key-value pairs

**Gap:** 
- ❌ NO write capability
- ❌ NO formatting preservation
- ❌ Uses basic `pyyaml` not `ruamel.yaml`

---

### 6️⃣ **Dependencies** 🟡 **MISSING RUAMEL**
**File:** `requirements.txt`

**Installed:**
- ✅ `pyyaml==6.0.1` - Basic YAML
- ✅ `watchdog==3.0.0` - File watching
- ✅ `fastapi==0.104.1` - Web API
- ✅ `mysql-connector-python==8.2.0` - Database

**Missing:**
- ❌ `ruamel.yaml` - Format-preserving YAML parser

**Fix:** Add to requirements.txt:
```
ruamel.yaml==0.18.5
```

---

### 7️⃣ **Web API** 🟢 **GOOD FOUNDATION**
**File:** `api.py` (1649 lines)

**Endpoints:**
- ✅ GET `/api/instances` - List instances
- ✅ GET `/api/plugins` - List plugins  
- ✅ GET `/api/variances` - Variance data
- ✅ POST `/api/deploy` - Deploy configs
- ✅ GET `/api/history` - Change history
- ✅ GET `/api/migrations` - Migration data

**Recent Additions (from conversation summary):**
- ✅ GET `/api/plugins/discovered` - Auto-discovered plugins
- ✅ GET `/api/config/plugin/{id}` - Config with hierarchy
- ✅ POST `/api/config/universal` - Set universal values
- ✅ DELETE `/api/config/override` - Clear overrides
- ✅ POST `/api/config/bulk-update` - Bulk updates

**Gap:** Need to add for TODO implementation:
- ❌ GET `/api/instances/{id}/config-files` - List all config files
- ❌ GET `/api/instances/{id}/plugins/{plugin}/configs` - Plugin config files
- ❌ POST `/api/instances/{id}/plugins/{plugin}/config` - Modify config
- ❌ POST `/api/config/rollback/{backup_id}` - Restore backup
- ❌ Endpoints for WORLD/RANK/PLAYER scopes

---

## ❌ **WEAK SCAFFOLDING** (What's Missing)

### 1️⃣ **Instance Path Tracking** 🔴 **CRITICAL GAP**

**Current State:**
```sql
-- instances table (from seed_instances.sql)
CREATE TABLE instances (
    instance_id VARCHAR(16) PRIMARY KEY,
    instance_name VARCHAR(128) NOT NULL,
    server_name VARCHAR(32) NOT NULL,
    port INT,
    amp_instance_id VARCHAR(64),  -- EXISTS BUT NOT POPULATED!
    ...
);
```

**Problems:**
1. ❌ `amp_instance_id` column exists but NEVER populated
2. ❌ NO `instance_folder_name` column
3. ❌ NO `instance_base_path` column
4. ❌ Agent assumes `instance_id` = folder name (WRONG!)

**Real-World Example:**
```
instance_id: SMP201
Folder name: ArchiveSMP-Season2  ← DIFFERENT!
AMP UUID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Fix Required:**
```sql
ALTER TABLE instances 
ADD COLUMN instance_folder_name VARCHAR(128),
ADD COLUMN instance_base_path VARCHAR(512);

-- Then populate from Instance.conf parsing
```

---

### 2️⃣ **Config File Location Tracking** 🔴 **MISSING ENTIRELY**

**Current State:** DOES NOT EXIST

**What We Need:**
```sql
CREATE TABLE endpoint_config_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_file_type ENUM('yaml', 'json', 'toml', 'properties'),
    relative_path VARCHAR(1024) NOT NULL,
    absolute_path VARCHAR(1024),
    file_hash VARCHAR(64),
    last_modified_at TIMESTAMP,
    is_main_config BOOLEAN DEFAULT FALSE,
    ...
);
```

**Why Critical:**
- Can't modify configs without knowing where they are
- Can't track config changes
- Can't detect config file additions/removals

---

### 3️⃣ **YAML Modification Capability** 🔴 **READ-ONLY**

**Current Code:**
```python
# config_reader.py - READ ONLY!
import yaml

def read_config(self, file_path: Path) -> Dict:
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)
```

**What We Need:**
```python
from ruamel.yaml import YAML

def modify_config(self, file_path: Path, key_path: str, new_value: Any):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    
    # Backup first
    self._backup_config_file(file_path)
    
    # Modify preserving formatting
    with open(file_path, 'r') as f:
        config = yaml.load(f)
    
    # Navigate nested keys
    keys = key_path.split('.')
    current = config
    for key in keys[:-1]:
        current = current[key]
    current[keys[-1]] = new_value
    
    # Write back
    with open(file_path, 'w') as f:
        yaml.dump(config, f)
```

**Gap:** COMPLETE - no write functionality exists

---

### 4️⃣ **Config Backup System** 🔴 **MISSING**

**Current State:** NO backup before config changes

**What We Need:**
```sql
CREATE TABLE endpoint_config_backups (
    backup_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16),
    plugin_id VARCHAR(128),
    config_file_path VARCHAR(1024),
    file_content LONGTEXT,  -- Full snapshot
    file_hash VARCHAR(64),
    backed_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    backup_reason ENUM('before_change', 'scheduled', 'manual'),
    ...
);
```

**Plus Code:**
```python
def _backup_config_file(self, file_path: Path, reason: str) -> int:
    """Backup config file before modification, return backup_id"""
    
def _restore_config_backup(self, backup_id: int):
    """Restore config from backup"""
```

**Risk Without This:** Breaking changes with no rollback

---

### 5️⃣ **Multi-Level Scope Support** 🔴 **ONLY 4 SCOPES**

**Current Schema:**
```sql
-- config_rules table
scope_type VARCHAR(16) NOT NULL,  -- GLOBAL, SERVER, META_TAG, INSTANCE
```

**What We Need:**
```sql
-- Extend to:
scope_type ENUM('GLOBAL', 'SERVER', 'META_TAG', 'INSTANCE', 'WORLD', 'RANK', 'PLAYER')
```

**Plus New Tables:**
```sql
CREATE TABLE world_meta_tags (...);
CREATE TABLE rank_meta_tags (...);
CREATE TABLE player_meta_tags (...);

CREATE TABLE world_config_rules (...);
CREATE TABLE rank_config_rules (...);
CREATE TABLE player_config_overrides (...);
```

**Gap:** Entire multi-level hierarchy system missing

---

### 6️⃣ **Plugin Folder Watcher** 🔴 **WRONG TARGET**

**Existing Watcher:** Monitors Pl3xMap tiles (irrelevant)

**What We Need:**
```python
class PluginFolderWatcher(FileSystemEventHandler):
    def __init__(self, agent):
        self.agent = agent
    
    def on_created(self, event):
        if event.src_path.endswith('.jar'):
            # Trigger immediate plugin scan
            instance_id = self._extract_instance_id(event.src_path)
            self.agent.trigger_plugin_scan(instance_id)

# Watch all instances
for instance in instances:
    observer.schedule(
        PluginFolderWatcher(agent),
        f'{instance_base_path}/Minecraft/plugins',
        recursive=False
    )
```

**Effort:** MEDIUM - Adapt tile_watcher.py

---

### 7️⃣ **Instance.conf Parser** 🔴 **DOES NOT EXIST**

**What We Need:**
```python
def _parse_amp_instance_conf(self, conf_path: Path) -> Dict:
    """
    Parse AMP Instance.conf file
    
    Returns:
        {
            'InstanceID': 'a1b2c3d4-...',
            'FriendlyName': 'SMP Season 2',
            'Module': 'Minecraft',
            'ApplicationPort': 25565
        }
    """
    import configparser
    config = configparser.ConfigParser()
    config.read(conf_path)
    return dict(config['Instance'])
```

**Current:** Agent assumes folder name = instance_id (WRONG)

---

## 📋 **TODO Scaffolding Breakdown**

### **TODOs 1-12: Endpoint Config Management**

| ID | Task | Scaffolding | Effort |
|----|------|-------------|--------|
| 1 | Add instance_folder_name/base_path columns | 🔴 None | LOW - SQL ALTER |
| 2 | Add endpoint_yaml_path tracking | 🔴 None | LOW - SQL ALTER |
| 3 | Create endpoint_config_files table | 🔴 None | LOW - SQL CREATE |
| 4 | Add plugin config file path tracking | 🔴 None | MEDIUM - Agent code |
| 5 | Build YAML parser/modifier library | 🔴 None | MEDIUM - New code |
| 6 | Agent method to read endpoint YAMLs | 🟡 Partial | LOW - Extend existing |
| 7 | Agent method to modify endpoint YAMLs | 🔴 None | MEDIUM - New code |
| 8 | Endpoint config change tracking | 🔴 None | MEDIUM - SQL + Agent |
| 9 | Plugin add/remove detection | 🟡 Partial | MEDIUM - Adapt watcher |
| 10 | Datapack add/remove detection | 🟡 Partial | MEDIUM - Adapt watcher |
| 11 | Config backup before modification | 🔴 None | MEDIUM - SQL + code |
| 12 | Rollback capability | 🔴 None | MEDIUM - SQL + API |

**Overall: 🔴 20% Scaffolded**

---

### **TODOs 13-20: Multi-Level Scope System**

| ID | Task | Scaffolding | Effort |
|----|------|-------------|--------|
| 13 | Extend scope_type enum | 🔴 None | LOW - SQL ALTER |
| 14 | World-level config rules | 🔴 None | MEDIUM - SQL + logic |
| 15 | Rank-level config rules | 🔴 None | HIGH - LuckPerms integration |
| 16 | Player-level config overrides | 🔴 None | HIGH - Player tracking |
| 17 | Meta-tag hierarchy system | 🟡 Partial | HIGH - Complex logic |
| 18 | world_meta_tags table | 🔴 None | LOW - SQL CREATE |
| 19 | rank_meta_tags table | 🔴 None | LOW - SQL CREATE |
| 20 | player_meta_tags table | 🔴 None | LOW - SQL CREATE |

**Overall: 🔴 15% Scaffolded**

---

### **TODOs 21-32: Variance & Management UIs**

| ID | Task | Scaffolding | Effort |
|----|------|-------------|--------|
| 21 | Variance tracking per scope | 🟡 Partial | HIGH - Multi-level diff |
| 22 | API: Query configs by hierarchy | 🟡 Partial | MEDIUM - Extend existing |
| 23 | API: Apply configs at any scope | 🟡 Partial | MEDIUM - Extend existing |
| 24-29 | UIs for variance management | 🟡 Partial | HIGH - 6 new UIs |
| 30 | Tag-based bulk operations | 🔴 None | MEDIUM - API + UI |
| 31 | Variance comparison views | 🟡 Partial | MEDIUM - SQL views |
| 32 | Drift detection all levels | 🟡 Partial | HIGH - Extend agent |

**Overall: 🟡 35% Scaffolded**

---

### **TODOs 33-42: Advanced Features**

| ID | Task | Scaffolding | Effort |
|----|------|-------------|--------|
| 33 | Meta-tag suggestion engine | 🔴 None | HIGH - ML/heuristics |
| 34 | Feature inventory system | 🟡 Partial | MEDIUM - Aggregate data |
| 35 | Server capability matrix | 🔴 None | MEDIUM - Server profiling |
| 36 | Instance feature set tracking | 🟡 Partial | LOW - Extend discovery |
| 37 | World feature tracking | 🔴 None | MEDIUM - World analysis |
| 38 | Config propagation engine | 🔴 None | HIGH - Cascade logic |
| 39 | Tag-based deployment targeting | 🟡 Partial | MEDIUM - Deployment logic |
| 40 | Multi-scope variance dashboard | 🔴 None | HIGH - Complex UI |
| 41 | Tag dependency system | 🔴 None | MEDIUM - Dependency graph |
| 42 | Tag conflict detection | 🔴 None | MEDIUM - Conflict rules |

**Overall: 🔴 25% Scaffolded**

---

## 🎯 **Implementation Priority**

### **Phase 1: Foundation (CRITICAL)** 🔴
**Effort:** 2-3 weeks

1. ✅ Add `instance_folder_name`, `instance_base_path` to instances table
2. ✅ Build Instance.conf parser
3. ✅ Create `endpoint_config_files` table
4. ✅ Create `endpoint_config_backups` table
5. ✅ Add `ruamel.yaml` to requirements
6. ✅ Build YAML modification library
7. ✅ Build config file discovery agent method
8. ✅ Build config backup/restore system

**Why First:** Can't modify configs without knowing where they are

---

### **Phase 2: File Watching (HIGH)** 🟡
**Effort:** 1 week

9. ✅ Adapt tile_watcher.py for plugin folders
10. ✅ Implement immediate plugin scan on changes
11. ✅ Auto-apply config rules to new plugins

**Why Second:** Reduces config drift window from 5 minutes to instant

---

### **Phase 3: Multi-Level Scopes (HIGH)** 🔴
**Effort:** 3-4 weeks

12. ✅ Extend `scope_type` enum
13. ✅ Create world/rank/player meta-tag tables
14. ✅ Create world/rank/player config rule tables
15. ✅ Build hierarchy resolver logic
16. ✅ Update API endpoints for all scopes

**Why Third:** Enables granular control that users need

---

### **Phase 4: UIs & Visualization (MEDIUM)** 🟡
**Effort:** 2-3 weeks

17. ✅ Per-server variance UI
18. ✅ Per-instance variance UI
19. ✅ Per-world variance UI
20. ✅ Multi-scope dashboard

**Why Fourth:** Backend first, then pretty UI

---

### **Phase 5: Advanced Features (NICE TO HAVE)** 🔴
**Effort:** 4-6 weeks

21. ✅ Meta-tag suggestion engine
22. ✅ Feature inventory
23. ✅ Tag dependencies/conflicts
24. ✅ Config propagation engine

**Why Last:** System works without these, but they make it awesome

---

## 📊 **Effort Estimates**

| Phase | Scaffolding | New Code | SQL | Testing | Total |
|-------|-------------|----------|-----|---------|-------|
| **Phase 1** | 20% | 400 lines | 150 lines | 2 days | **2-3 weeks** |
| **Phase 2** | 60% | 200 lines | 50 lines | 1 day | **1 week** |
| **Phase 3** | 15% | 600 lines | 300 lines | 3 days | **3-4 weeks** |
| **Phase 4** | 35% | 800 lines | 100 lines | 2 days | **2-3 weeks** |
| **Phase 5** | 25% | 1000 lines | 200 lines | 5 days | **4-6 weeks** |
| **TOTAL** |  | **3000 lines** | **800 lines SQL** | **13 days** | **12-17 weeks** |

---

## 🚀 **Immediate Next Steps**

1. **Add Missing Columns to instances Table**
   ```sql
   ALTER TABLE instances 
   ADD COLUMN instance_folder_name VARCHAR(128),
   ADD COLUMN instance_base_path VARCHAR(512),
   ADD INDEX idx_folder_name (instance_folder_name);
   
   UPDATE instances SET amp_instance_id = NULL WHERE amp_instance_id = '';
   ```

2. **Create endpoint_config_files Table**
   ```sql
   -- Full schema in ENDPOINT_CONFIG_TRACKING_ANALYSIS.md
   ```

3. **Add ruamel.yaml to requirements.txt**
   ```
   ruamel.yaml==0.18.5
   ```

4. **Build Instance.conf Parser**
   ```python
   # Add to production_endpoint_agent.py
   def _parse_instance_conf(self, conf_path: Path) -> Dict:
       ...
   ```

5. **Test on Development Server First**
   - Parse Instance.conf for all 11 instances
   - Verify folder names match
   - Update database with real paths

---

## ✅ **Conclusion**

**We have EXCELLENT scaffolding for:**
- Auto-discovery (90%)
- CI/CD integration (95%)
- Database schema foundation (85%)

**We have POOR scaffolding for:**
- Config modification (35%)
- Multi-level scopes (20%)
- Instance path tracking (30%)

**Bottom Line:** The **discovery and tracking** infrastructure is production-ready. The **config modification and multi-level hierarchy** systems need to be built from scratch.

**Recommendation:** Implement Phase 1 (Foundation) immediately to enable config modifications, then Phase 2 (File Watching) for real-time updates, before tackling Phase 3 (Multi-Level Scopes).

---

## 📋 **255 TODO IMPLEMENTATION DETAILS**

### 🔍 **Context Refresh Todos** (Periodic LLM Context Reset)

| ID | Title | Action | Files/Context |
|----|-------|--------|---------------|
| 1 | READ: Review SCAFFOLDING_ASSESSMENT.md | `read_file` this document | Lines 1-719 |
| 2 | READ: Review ENDPOINT_CONFIG_TRACKING_ANALYSIS.md | `read_file` endpoint analysis | Full file (~400 lines) |
| 3 | READ: Review PRODUCTION_DYNAMIC_SYSTEM.md | `read_file` architecture doc | Full system design |
| 39 | READ: Review tile_watcher.py | `read_file` lines 1-327 | Understand watchdog pattern before adapting |
| 51 | READ: Review production_endpoint_agent.py | `read_file` lines 1-474 | Understand current discovery logic |
| 61 | READ: Review agent_database_methods.py | `read_file` lines 1-446 | Understand DB interaction patterns |
| 82 | READ: Review api.py | `read_file` lines 1-1649 | Understand endpoint structure |
| 108 | READ: Review UI files | `list_dir src/web/static/` | Current UI structure |
| 155 | READ: Review deployment instructions | `read_file .github/copilot-instructions.md` | Production deployment rules |
| 189 | READ: Review verification results | Review logs/output from IDs 169-188 | Fix issues found |
| 211 | REFRESH: Re-read SCAFFOLDING_ASSESSMENT.md | `read_file` lines 300-600 | Phase 2-5 details |
| 244 | READ: Review network topology | Check Hetzner/OVH connection | Cross-server sync requirements |

---

### 🗄️ **Database Schema Todos** (SQL DDL Statements)

#### **Instance Path Tracking** (IDs 4-7)

| ID | SQL Statement | Table | Columns Added | Purpose |
|----|--------------|-------|---------------|---------|
| 4 | `ALTER TABLE instances ADD COLUMN instance_folder_name VARCHAR(128)` | `instances` | `instance_folder_name` | Store actual folder name on disk (e.g., 'ArchiveSMP-Season2') |
| 5 | `ALTER TABLE instances ADD COLUMN instance_base_path VARCHAR(512)` | `instances` | `instance_base_path` | Store full path (e.g., '/home/amp/.ampdata/instances/ArchiveSMP-Season2') |
| 6 | `ALTER TABLE instances ADD INDEX idx_folder_name (instance_folder_name)` | `instances` | INDEX | Fast lookup by folder name |
| 7 | `UPDATE instances SET amp_instance_id = NULL WHERE amp_instance_id = ''` | `instances` | - | Clean up empty amp_instance_id values |

**Files:** `software/homeamp-config-manager/scripts/add_instance_path_columns.sql` (create this)

---

#### **Endpoint Config File Tracking** (IDs 8-10)

| ID | SQL Statement | Table | Columns | Purpose |
|----|--------------|-------|---------|---------|
| 8 | CREATE TABLE endpoint_config_files | `endpoint_config_files` | See below | Track all config files for all plugins |
| 9 | CREATE TABLE endpoint_config_backups | `endpoint_config_backups` | See below | Store config backups before modification |
| 10 | CREATE TABLE endpoint_config_change_history | `endpoint_config_change_history` | See below | Audit trail of all config changes |

**ID 8 Schema:**
```sql
CREATE TABLE endpoint_config_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_file_type ENUM('yaml', 'json', 'toml', 'properties') NOT NULL,
    relative_path VARCHAR(1024) NOT NULL COMMENT 'plugins/PluginName/config.yml',
    absolute_path VARCHAR(1024) COMMENT '/home/amp/.ampdata/instances/{folder}/Minecraft/plugins/PluginName/config.yml',
    file_hash VARCHAR(64) COMMENT 'SHA-256 hash for change detection',
    file_size_bytes INT,
    last_modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_scanned_at TIMESTAMP,
    is_main_config BOOLEAN DEFAULT FALSE COMMENT 'config.yml vs settings.yml',
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY uk_instance_plugin_path (instance_id, plugin_id, relative_path),
    INDEX idx_plugin_id (plugin_id),
    INDEX idx_instance_id (instance_id),
    INDEX idx_file_hash (file_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 9 Schema:**
```sql
CREATE TABLE endpoint_config_backups (
    backup_id INT AUTO_INCREMENT PRIMARY KEY,
    config_file_id INT NOT NULL,
    file_content MEDIUMTEXT NOT NULL COMMENT 'Full file content before modification',
    file_hash VARCHAR(64) NOT NULL,
    backup_reason ENUM('pre_modify', 'manual', 'scheduled', 'pre_deploy') DEFAULT 'pre_modify',
    created_by VARCHAR(64) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (config_file_id) REFERENCES endpoint_config_files(id) ON DELETE CASCADE,
    INDEX idx_config_file_id (config_file_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 10 Schema:**
```sql
CREATE TABLE endpoint_config_change_history (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    config_file_id INT NOT NULL,
    change_type ENUM('create', 'modify', 'delete', 'rollback') NOT NULL,
    config_key VARCHAR(512) COMMENT 'Nested key path e.g., settings.economy.starting-balance',
    old_value TEXT,
    new_value TEXT,
    scope_type VARCHAR(16) COMMENT 'Which scope triggered change: GLOBAL/SERVER/INSTANCE/WORLD/RANK/PLAYER',
    scope_selector VARCHAR(128) COMMENT 'server_name, instance_id, world_name, rank_name, player_uuid',
    changed_by VARCHAR(64) DEFAULT 'system',
    backup_id INT COMMENT 'Reference to backup created before change',
    change_status ENUM('pending', 'applied', 'failed', 'rolled_back') DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP NULL,
    FOREIGN KEY (config_file_id) REFERENCES endpoint_config_files(id) ON DELETE CASCADE,
    FOREIGN KEY (backup_id) REFERENCES endpoint_config_backups(backup_id) ON DELETE SET NULL,
    INDEX idx_config_file_id (config_file_id),
    INDEX idx_created_at (created_at),
    INDEX idx_change_status (change_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**File:** `software/homeamp-config-manager/scripts/create_endpoint_config_tables.sql` (create this)

---

#### **Multi-Level Scope Tables** (IDs 11-17)

| ID | SQL Statement | Table | Purpose |
|----|--------------|-------|---------|
| 11 | CREATE TABLE world_meta_tags | `world_meta_tags` | Tag worlds (e.g., 'overworld' tagged as 'survival') |
| 12 | CREATE TABLE rank_meta_tags | `rank_meta_tags` | Tag LuckPerms ranks (e.g., 'vip' tagged as 'donor') |
| 13 | CREATE TABLE player_meta_tags | `player_meta_tags` | Tag players (e.g., player X tagged as 'beta-tester') |
| 14 | ALTER config_rules MODIFY scope_type | `config_rules` | Extend ENUM to include WORLD, RANK, PLAYER |
| 15 | CREATE TABLE world_config_rules | `world_config_rules` | Per-world config overrides |
| 16 | CREATE TABLE rank_config_rules | `rank_config_rules` | Per-rank config overrides |
| 17 | CREATE TABLE player_config_overrides | `player_config_overrides` | Per-player overrides |

**ID 11 Schema:**
```sql
CREATE TABLE world_meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL COMMENT 'world, world_nether, world_the_end, custom_world',
    tag_id INT NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 1.00 COMMENT '0.00-1.00 for ML-based tagging',
    assigned_by VARCHAR(64) DEFAULT 'system',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    UNIQUE KEY uk_world_tag (instance_id, world_name, tag_id),
    INDEX idx_world_name (world_name),
    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 12 Schema:**
```sql
CREATE TABLE rank_meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(32) NOT NULL COMMENT 'LuckPerms is server-wide, not instance-specific',
    rank_name VARCHAR(64) NOT NULL COMMENT 'default, vip, moderator, admin',
    tag_id INT NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    assigned_by VARCHAR(64) DEFAULT 'system',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    UNIQUE KEY uk_rank_tag (server_name, rank_name, tag_id),
    INDEX idx_server_rank (server_name, rank_name),
    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 13 Schema:**
```sql
CREATE TABLE player_meta_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36) NOT NULL COMMENT 'Minecraft player UUID',
    player_name VARCHAR(16) COMMENT 'Current IGN for display',
    tag_id INT NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    assigned_by VARCHAR(64) DEFAULT 'system',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL COMMENT 'For temporary tags like beta-tester',
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    UNIQUE KEY uk_player_tag (player_uuid, tag_id),
    INDEX idx_player_uuid (player_uuid),
    INDEX idx_tag_id (tag_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 14 Statement:**
```sql
ALTER TABLE config_rules 
MODIFY COLUMN scope_type ENUM('GLOBAL', 'SERVER', 'META_TAG', 'INSTANCE', 'WORLD', 'RANK', 'PLAYER') NOT NULL;
```

**ID 15 Schema:**
```sql
CREATE TABLE world_config_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    plugin_name VARCHAR(128) NOT NULL,
    config_file VARCHAR(255) NOT NULL DEFAULT 'config.yml',
    config_key VARCHAR(512) NOT NULL COMMENT 'Nested path: settings.economy.enabled',
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object') DEFAULT 'string',
    priority INT DEFAULT 50 COMMENT 'Higher = more important, range 0-100',
    enabled BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(64) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY uk_world_config (instance_id, world_name, plugin_name, config_file, config_key),
    INDEX idx_world (instance_id, world_name),
    INDEX idx_plugin (plugin_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 16 Schema:**
```sql
CREATE TABLE rank_config_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(32) NOT NULL,
    rank_name VARCHAR(64) NOT NULL,
    plugin_name VARCHAR(128) NOT NULL,
    config_file VARCHAR(255) NOT NULL DEFAULT 'config.yml',
    config_key VARCHAR(512) NOT NULL,
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object') DEFAULT 'string',
    priority INT DEFAULT 60,
    enabled BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(64) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_rank_config (server_name, rank_name, plugin_name, config_file, config_key),
    INDEX idx_rank (server_name, rank_name),
    INDEX idx_plugin (plugin_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 17 Schema:**
```sql
CREATE TABLE player_config_overrides (
    id INT AUTO_INCREMENT PRIMARY KEY,
    player_uuid CHAR(36) NOT NULL,
    plugin_name VARCHAR(128) NOT NULL,
    config_key VARCHAR(512) NOT NULL,
    config_value TEXT NOT NULL,
    value_type ENUM('string', 'number', 'boolean', 'list', 'object') DEFAULT 'string',
    priority INT DEFAULT 100 COMMENT 'Player overrides highest priority',
    expires_at TIMESTAMP NULL COMMENT 'For temporary overrides',
    created_by VARCHAR(64) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_player_override (player_uuid, plugin_name, config_key),
    INDEX idx_player (player_uuid),
    INDEX idx_plugin (plugin_name),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**File:** `software/homeamp-config-manager/scripts/create_multi_level_scope_tables.sql` (create this)

---

#### **Advanced Feature Tables** (IDs 18-22)

| ID | SQL Statement | Table | Purpose |
|----|--------------|-------|---------|
| 18 | CREATE TABLE tag_dependencies | `tag_dependencies` | Tag A requires Tag B (e.g., 'economy' requires 'vault') |
| 19 | CREATE TABLE tag_conflicts | `tag_conflicts` | Tag A conflicts with Tag B (e.g., 'creative-only' vs 'survival-only') |
| 20 | CREATE TABLE instance_feature_inventory | `instance_feature_inventory` | Track features per instance (economy, permissions, pvp, etc.) |
| 21 | CREATE TABLE server_capabilities | `server_capabilities` | What each server supports (plugin count, RAM, Java version) |
| 22 | CREATE TABLE world_features | `world_features` | Per-world feature detection |

**ID 18 Schema:**
```sql
CREATE TABLE tag_dependencies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tag_id INT NOT NULL COMMENT 'The tag that has dependencies',
    required_tag_id INT NOT NULL COMMENT 'The tag that is required',
    dependency_type ENUM('required', 'recommended', 'suggested') DEFAULT 'required',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (required_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    UNIQUE KEY uk_dependency (tag_id, required_tag_id),
    INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 19 Schema:**
```sql
CREATE TABLE tag_conflicts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tag_id INT NOT NULL,
    conflicts_with_tag_id INT NOT NULL,
    conflict_severity ENUM('error', 'warning', 'info') DEFAULT 'warning',
    conflict_reason VARCHAR(512),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (conflicts_with_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    UNIQUE KEY uk_conflict (tag_id, conflicts_with_tag_id),
    INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 20 Schema:**
```sql
CREATE TABLE instance_feature_inventory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    feature_name VARCHAR(128) NOT NULL COMMENT 'economy, permissions, pvp, custom-items, etc.',
    is_enabled BOOLEAN DEFAULT TRUE,
    detected_via VARCHAR(255) COMMENT 'Plugin name or detection method',
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    last_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY uk_instance_feature (instance_id, feature_name),
    INDEX idx_feature (feature_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 21 Schema:**
```sql
CREATE TABLE server_capabilities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(32) NOT NULL,
    capability_name VARCHAR(128) NOT NULL COMMENT 'max_ram_gb, java_version, max_instances, etc.',
    capability_value VARCHAR(255),
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_server_capability (server_name, capability_name),
    INDEX idx_server (server_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**ID 22 Schema:**
```sql
CREATE TABLE world_features (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    world_name VARCHAR(128) NOT NULL,
    feature_name VARCHAR(128) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    detected_via VARCHAR(255),
    last_detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    UNIQUE KEY uk_world_feature (instance_id, world_name, feature_name),
    INDEX idx_world (instance_id, world_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**File:** `software/homeamp-config-manager/scripts/create_advanced_feature_tables.sql` (create this)

---

#### **Views for Hierarchy Resolution** (IDs 23-25)

| ID | SQL Statement | View | Purpose |
|----|--------------|------|---------|
| 23 | CREATE VIEW v_config_hierarchy | View | Show full 7-level hierarchy for any config key |
| 24 | CREATE VIEW v_instance_effective_configs | View | Final resolved config values per instance |
| 25 | CREATE VIEW v_variance_by_scope | View | Variance analysis at each scope level |

**ID 23 Schema:**
```sql
CREATE OR REPLACE VIEW v_config_hierarchy AS
SELECT 
    'GLOBAL' AS scope_level,
    1 AS priority_order,
    cr.plugin_name,
    cr.config_file,
    cr.config_key,
    cr.config_value,
    cr.scope_type,
    cr.scope_selector,
    cr.priority
FROM config_rules cr
WHERE cr.scope_type = 'GLOBAL' AND cr.enabled = TRUE

UNION ALL

SELECT 
    'SERVER' AS scope_level,
    2 AS priority_order,
    cr.plugin_name,
    cr.config_file,
    cr.config_key,
    cr.config_value,
    cr.scope_type,
    cr.scope_selector,
    cr.priority
FROM config_rules cr
WHERE cr.scope_type = 'SERVER' AND cr.enabled = TRUE

UNION ALL

SELECT 
    'META_TAG' AS scope_level,
    3 AS priority_order,
    cr.plugin_name,
    cr.config_file,
    cr.config_key,
    cr.config_value,
    cr.scope_type,
    cr.scope_selector,
    cr.priority
FROM config_rules cr
WHERE cr.scope_type = 'META_TAG' AND cr.enabled = TRUE

UNION ALL

SELECT 
    'INSTANCE' AS scope_level,
    4 AS priority_order,
    cr.plugin_name,
    cr.config_file,
    cr.config_key,
    cr.config_value,
    cr.scope_type,
    cr.scope_selector,
    cr.priority
FROM config_rules cr
WHERE cr.scope_type = 'INSTANCE' AND cr.enabled = TRUE

UNION ALL

SELECT 
    'WORLD' AS scope_level,
    5 AS priority_order,
    wcr.plugin_name,
    wcr.config_file,
    wcr.config_key,
    wcr.config_value,
    'WORLD' AS scope_type,
    CONCAT(wcr.instance_id, ':', wcr.world_name) AS scope_selector,
    wcr.priority
FROM world_config_rules wcr
WHERE wcr.enabled = TRUE

UNION ALL

SELECT 
    'RANK' AS scope_level,
    6 AS priority_order,
    rcr.plugin_name,
    rcr.config_file,
    rcr.config_key,
    rcr.config_value,
    'RANK' AS scope_type,
    CONCAT(rcr.server_name, ':', rcr.rank_name) AS scope_selector,
    rcr.priority
FROM rank_config_rules rcr
WHERE rcr.enabled = TRUE

UNION ALL

SELECT 
    'PLAYER' AS scope_level,
    7 AS priority_order,
    pco.plugin_name,
    'N/A' AS config_file,
    pco.config_key,
    pco.config_value,
    'PLAYER' AS scope_type,
    pco.player_uuid AS scope_selector,
    pco.priority
FROM player_config_overrides pco
WHERE (pco.expires_at IS NULL OR pco.expires_at > NOW());
```

**File:** `software/homeamp-config-manager/scripts/create_hierarchy_views.sql` (create this)

---

### 📦 **Dependency Management Todos** (IDs 26-28)

| ID | Title | Action | File/Command | Purpose |
|----|-------|--------|--------------|---------|
| 26 | Add ruamel.yaml to requirements | Edit file | `software/homeamp-config-manager/requirements.txt` | Add line: `ruamel.yaml==0.18.5` |
| 27 | Add configparser | Edit file | `software/homeamp-config-manager/requirements.txt` | Add line: `configparser>=5.3.0` |
| 28 | Install ruamel.yaml | Run command | `pip install ruamel.yaml==0.18.5` | Install on dev environment |

**Why ruamel.yaml?**
- Preserves YAML formatting (comments, indentation, quotes)
- Round-trip safe (read → modify → write without destroying structure)
- Essential for modifying plugin configs without breaking manual edits

---

### 🔧 **Core Utility Todos** (IDs 29-38)

#### **YAML Handler** (IDs 29-33)

| ID | Method/Class | File | Signature | Purpose |
|----|--------------|------|-----------|---------|
| 29 | Create module | `src/utils/yaml_handler.py` | New file | Format-preserving YAML operations |
| 30 | `YAMLHandler.read_yaml()` | `yaml_handler.py` | `def read_yaml(self, file_path: Path) -> CommentedMap` | Read YAML preserving structure |
| 31 | `YAMLHandler.write_yaml()` | `yaml_handler.py` | `def write_yaml(self, file_path: Path, data: CommentedMap) -> None` | Write YAML preserving formatting |
| 32 | `YAMLHandler.modify_key()` | `yaml_handler.py` | `def modify_key(self, data: CommentedMap, key_path: str, new_value: Any) -> CommentedMap` | Modify nested key (e.g., 'settings.economy.enabled') |
| 33 | `YAMLHandler.validate_syntax()` | `yaml_handler.py` | `def validate_syntax(self, file_path: Path) -> Tuple[bool, Optional[str]]` | Syntax check before deployment |

**ID 30 Implementation:**
```python
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from pathlib import Path
from typing import Any, Optional, Tuple

class YAMLHandler:
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False
        self.yaml.width = 4096  # Prevent line wrapping
        
    def read_yaml(self, file_path: Path) -> CommentedMap:
        """Read YAML file preserving structure."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.yaml.load(f)
```

**ID 31 Implementation:**
```python
def write_yaml(self, file_path: Path, data: CommentedMap) -> None:
    """Write YAML file preserving formatting."""
    with open(file_path, 'w', encoding='utf-8') as f:
        self.yaml.dump(data, f)
```

**ID 32 Implementation:**
```python
def modify_key(self, data: CommentedMap, key_path: str, new_value: Any) -> CommentedMap:
    """
    Modify nested YAML key.
    
    Args:
        data: YAML data structure
        key_path: Dot-separated path (e.g., 'settings.economy.enabled')
        new_value: Value to set
        
    Returns:
        Modified data structure
        
    Example:
        modify_key(data, 'settings.pvp.enabled', False)
    """
    keys = key_path.split('.')
    current = data
    
    # Navigate to parent
    for key in keys[:-1]:
        if key not in current:
            current[key] = CommentedMap()
        current = current[key]
    
    # Set final key
    current[keys[-1]] = new_value
    return data
```

**ID 33 Implementation:**
```python
def validate_syntax(self, file_path: Path) -> Tuple[bool, Optional[str]]:
    """Validate YAML syntax."""
    try:
        self.read_yaml(file_path)
        return (True, None)
    except Exception as e:
        return (False, str(e))
```

---

#### **Config Backup System** (IDs 34-38)

| ID | Method/Class | File | Signature | Purpose |
|----|--------------|------|-----------|---------|
| 34 | Create module | `src/utils/config_backup.py` | New file | Backup/restore system |
| 35 | `ConfigBackup.create_backup()` | `config_backup.py` | `def create_backup(self, config_file_id: int, reason: str = 'pre_modify') -> int` | Create backup before change |
| 36 | `ConfigBackup.restore_backup()` | `config_backup.py` | `def restore_backup(self, backup_id: int) -> bool` | Rollback to backup |
| 37 | `ConfigBackup.list_backups()` | `config_backup.py` | `def list_backups(self, config_file_id: int, limit: int = 10) -> List[Dict]` | History for file |
| 38 | `ConfigBackup.prune_old_backups()` | `config_backup.py` | `def prune_old_backups(self, keep_count: int = 50) -> int` | Cleanup old backups |

**ID 35 Implementation:**
```python
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ConfigBackup:
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_backup(self, config_file_id: int, reason: str = 'pre_modify') -> int:
        """
        Create backup of config file before modification.
        
        Args:
            config_file_id: ID from endpoint_config_files table
            reason: Why backup is created
            
        Returns:
            backup_id: ID of created backup
        """
        # Get file info
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT absolute_path, file_hash 
            FROM endpoint_config_files 
            WHERE id = %s
        """, (config_file_id,))
        file_info = cursor.fetchone()
        
        if not file_info:
            raise ValueError(f"Config file {config_file_id} not found")
        
        # Read file content
        with open(file_info['absolute_path'], 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate hash
        file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Insert backup
        cursor.execute("""
            INSERT INTO endpoint_config_backups 
            (config_file_id, file_content, file_hash, backup_reason, created_by)
            VALUES (%s, %s, %s, %s, 'system')
        """, (config_file_id, content, file_hash, reason))
        
        self.db.commit()
        backup_id = cursor.lastrowid
        cursor.close()
        
        return backup_id
```

**ID 36 Implementation:**
```python
def restore_backup(self, backup_id: int) -> bool:
    """
    Restore config file from backup.
    
    Args:
        backup_id: ID from endpoint_config_backups table
        
    Returns:
        True if restored successfully
    """
    cursor = self.db.cursor(dictionary=True)
    
    # Get backup and file info
    cursor.execute("""
        SELECT 
            ecb.file_content,
            ecf.absolute_path,
            ecf.id as config_file_id
        FROM endpoint_config_backups ecb
        JOIN endpoint_config_files ecf ON ecb.config_file_id = ecf.id
        WHERE ecb.backup_id = %s
    """, (backup_id,))
    
    backup = cursor.fetchone()
    if not backup:
        return False
    
    # Write content back
    with open(backup['absolute_path'], 'w', encoding='utf-8') as f:
        f.write(backup['file_content'])
    
    # Log restoration in change history
    cursor.execute("""
        INSERT INTO endpoint_config_change_history
        (config_file_id, change_type, backup_id, changed_by, change_status, applied_at)
        VALUES (%s, 'rollback', %s, 'system', 'applied', NOW())
    """, (backup['config_file_id'], backup_id))
    
    self.db.commit()
    cursor.close()
    
    return True
```

---

#### **File Watchers** (IDs 40-46)

| ID | Method/Class | File | Purpose |
|----|--------------|------|---------|
| 40 | Create module | `src/agent/plugin_folder_watcher.py` | Watch `/plugins/` folders for JAR changes |
| 41 | `PluginFolderWatcher.on_created()` | `plugin_folder_watcher.py` | Detect new plugin JARs added |
| 42 | `PluginFolderWatcher.on_deleted()` | `plugin_folder_watcher.py` | Detect plugin JARs removed |
| 43 | `PluginFolderWatcher.on_modified()` | `plugin_folder_watcher.py` | Detect plugin JAR updates |
| 44 | `PluginFolderWatcher.trigger_immediate_scan()` | `plugin_folder_watcher.py` | Force immediate rescan |
| 45 | Create module | `src/agent/datapack_folder_watcher.py` | Watch `/datapacks/` folders |
| 46 | `DatapackWatcher.watch_all_worlds()` | `datapack_folder_watcher.py` | Monitor all world datapack folders |

**ID 41 Implementation (based on tile_watcher.py pattern):**
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import time
from typing import Callable

class PluginFolderWatcher(FileSystemEventHandler):
    """
    Watch plugin folders for JAR file changes.
    Based on tile_watcher.py pattern.
    """
    
    def __init__(self, instance_id: str, plugins_path: Path, callback: Callable):
        """
        Args:
            instance_id: Instance identifier
            plugins_path: Path to /Minecraft/plugins/ folder
            callback: Function to call on changes (signature: callback(instance_id, event_type, file_path))
        """
        self.instance_id = instance_id
        self.plugins_path = plugins_path
        self.callback = callback
        self.batch_delay = 10  # Wait 10s before triggering (like tile_watcher)
        self.pending_changes = set()
        
    def on_created(self, event):
        """New JAR file added."""
        if not event.is_directory and event.src_path.endswith('.jar'):
            self.pending_changes.add(('created', event.src_path))
            self._schedule_batch_process()
            
    def on_deleted(self, event):
        """JAR file removed."""
        if not event.is_directory and event.src_path.endswith('.jar'):
            self.pending_changes.add(('deleted', event.src_path))
            self._schedule_batch_process()
            
    def on_modified(self, event):
        """JAR file updated."""
        if not event.is_directory and event.src_path.endswith('.jar'):
            self.pending_changes.add(('modified', event.src_path))
            self._schedule_batch_process()
            
    def _schedule_batch_process(self):
        """Wait for batch_delay before processing."""
        time.sleep(self.batch_delay)
        self.trigger_immediate_scan()
        
    def trigger_immediate_scan(self):
        """Force immediate plugin scan."""
        self.callback(self.instance_id, 'batch_change', list(self.pending_changes))
        self.pending_changes.clear()
```

---

### 📄 **Parser Todos** (IDs 47-50)

| ID | Method/Class | File | Purpose |
|----|--------------|------|---------|
| 47 | Create module | `src/parsers/instance_conf_parser.py` | Parse AMP Instance.conf files |
| 48 | `InstanceConfParser.parse()` | `instance_conf_parser.py` | Extract InstanceID, FriendlyName, ApplicationPort |
| 49 | `InstanceConfParser.get_amp_uuid()` | `instance_conf_parser.py` | Get AMP internal UUID |
| 50 | `InstanceConfParser.get_port()` | `instance_conf_parser.py` | Extract port number |

**Instance.conf Format Example:**
```ini
# AMP Instance Configuration File
InstanceID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
FriendlyName=ArchiveSMP Season 2
ApplicationPort=25565
ApplicationUDPPort=25565
Module=Minecraft
ModuleName=Minecraft
```

**ID 48 Implementation:**
```python
from pathlib import Path
from typing import Dict, Optional
import configparser

class InstanceConfParser:
    """Parse AMP Instance.conf files to get folder-to-UUID mapping."""
    
    def __init__(self):
        pass
        
    def parse(self, conf_file_path: Path) -> Dict[str, str]:
        """
        Parse Instance.conf file.
        
        Args:
            conf_file_path: Path to Instance.conf (e.g., /home/amp/.ampdata/instances/ArchiveSMP-Season2/Instance.conf)
            
        Returns:
            Dict with keys: instance_id, friendly_name, port, module
            
        Example:
            {
                'instance_id': 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
                'friendly_name': 'ArchiveSMP Season 2',
                'port': 25565,
                'module': 'Minecraft',
                'folder_name': 'ArchiveSMP-Season2'
            }
        """
        config = configparser.ConfigParser()
        
        # Instance.conf doesn't have sections, add fake section
        with open(conf_file_path, 'r') as f:
            config_string = '[DEFAULT]\n' + f.read()
        config.read_string(config_string)
        
        # Extract folder name from path
        folder_name = conf_file_path.parent.name
        
        return {
            'instance_id': config['DEFAULT'].get('InstanceID', ''),
            'friendly_name': config['DEFAULT'].get('FriendlyName', ''),
            'port': int(config['DEFAULT'].get('ApplicationPort', 0)),
            'module': config['DEFAULT'].get('Module', ''),
            'folder_name': folder_name
        }
        
    def get_amp_uuid(self, conf_file_path: Path) -> str:
        """Get AMP UUID from Instance.conf."""
        data = self.parse(conf_file_path)
        return data['instance_id']
        
    def get_port(self, conf_file_path: Path) -> int:
        """Get port from Instance.conf."""
        data = self.parse(conf_file_path)
        return data['port']
```

---

### 🤖 **Agent Discovery Todos** (IDs 52-60)

**Context:** These extend `production_endpoint_agent.py` (474 lines)

| ID | Method | File | Location | Purpose |
|----|--------|------|----------|---------|
| 52 | `Agent._discover_instance_folders()` | `production_endpoint_agent.py` | Add after `_discover_instances()` | Scan `/home/amp/.ampdata/instances/` for folders |
| 53 | `Agent._parse_instance_conf_for_folder()` | `production_endpoint_agent.py` | Add after line 200 | Read Instance.conf for each folder |
| 54 | `Agent._map_folder_to_instance_id()` | `production_endpoint_agent.py` | Add after line 220 | Match folder name to database instance_id |
| 55 | `Agent._update_instance_paths()` | `production_endpoint_agent.py` | Add after line 240 | UPDATE instances SET instance_folder_name, instance_base_path |
| 56 | `Agent._discover_plugin_config_files()` | `production_endpoint_agent.py` | Add after `_discover_instance_plugins()` | Find all YAML/JSON/properties files |
| 57 | `Agent._register_config_file()` | `production_endpoint_agent.py` | Add after line 350 | INSERT into endpoint_config_files |
| 58 | `Agent._detect_config_file_type()` | `production_endpoint_agent.py` | Add utility method | Identify file type by extension |
| 59 | `Agent._calculate_config_file_hash()` | `production_endpoint_agent.py` | Add utility method | SHA-256 hash for change detection |
| 60 | `Agent._scan_all_plugin_configs()` | `production_endpoint_agent.py` | Add to main scan loop | Full config file discovery run |

**ID 52 Implementation:**
```python
def _discover_instance_folders(self) -> List[Dict]:
    """
    Scan /home/amp/.ampdata/instances/ for all folders.
    Parse Instance.conf for each folder to get AMP UUID and friendly name.
    
    Returns:
        List of dicts with folder_name, amp_uuid, friendly_name, port
    """
    instances_dir = Path('/home/amp/.ampdata/instances')
    discovered = []
    
    for folder in instances_dir.iterdir():
        if not folder.is_dir():
            continue
            
        conf_file = folder / 'Instance.conf'
        if not conf_file.exists():
            logger.warning(f"No Instance.conf in {folder.name}")
            continue
            
        try:
            parser = InstanceConfParser()
            conf_data = parser.parse(conf_file)
            
            discovered.append({
                'folder_name': folder.name,
                'amp_uuid': conf_data['instance_id'],
                'friendly_name': conf_data['friendly_name'],
                'port': conf_data['port'],
                'base_path': str(folder)
            })
            
            logger.info(f"Discovered folder: {folder.name} -> UUID: {conf_data['instance_id']}")
            
        except Exception as e:
            logger.error(f"Failed to parse {conf_file}: {e}")
            
    return discovered
```

**ID 56 Implementation:**
```python
def _discover_plugin_config_files(self, instance_id: str, plugin_name: str) -> List[Dict]:
    """
    Discover all config files for a plugin.
    
    Args:
        instance_id: Instance identifier
        plugin_name: Plugin name
        
    Returns:
        List of config file dicts with relative_path, absolute_path, file_type
    """
    # Get instance folder path
    cursor = self.db.cursor(dictionary=True)
    cursor.execute("""
        SELECT instance_folder_name, instance_base_path
        FROM instances
        WHERE instance_id = %s
    """, (instance_id,))
    instance = cursor.fetchone()
    
    if not instance or not instance['instance_base_path']:
        return []
    
    plugin_dir = Path(instance['instance_base_path']) / 'Minecraft' / 'plugins' / plugin_name
    
    if not plugin_dir.exists():
        return []
    
    config_files = []
    
    # Common config file patterns
    patterns = ['*.yml', '*.yaml', '*.json', '*.properties', '*.toml', '*.conf']
    
    for pattern in patterns:
        for file_path in plugin_dir.rglob(pattern):
            relative_path = file_path.relative_to(Path(instance['instance_base_path']) / 'Minecraft')
            
            config_files.append({
                'relative_path': str(relative_path),
                'absolute_path': str(file_path),
                'file_type': self._detect_config_file_type(file_path),
                'file_size': file_path.stat().st_size,
                'is_main_config': file_path.name in ['config.yml', 'config.yaml', 'config.json']
            })
    
    return config_files
```

---

### 💾 **Database Method Todos** (IDs 62-67)

**Context:** These extend `agent_database_methods.py` (446 lines)

| ID | Method | File | Purpose |
|----|--------|------|---------|
| 62 | `DBMethods._register_endpoint_config_file()` | `agent_database_methods.py` | INSERT/UPDATE endpoint_config_files |
| 63 | `DBMethods._create_config_backup()` | `agent_database_methods.py` | Call ConfigBackup.create_backup() |
| 64 | `DBMethods._restore_config_from_backup()` | `agent_database_methods.py` | Call ConfigBackup.restore_backup() |
| 65 | `DBMethods._log_config_change()` | `agent_database_methods.py` | INSERT into endpoint_config_change_history |
| 66 | `DBMethods._get_config_file_info()` | `agent_database_methods.py` | SELECT from endpoint_config_files |
| 67 | `DBMethods._mark_config_outdated()` | `agent_database_methods.py` | Flag files with changed hashes |

**ID 62 Implementation:**
```python
def _register_endpoint_config_file(self, instance_id: str, plugin_id: str, config_data: Dict) -> int:
    """
    Register or update config file in database.
    
    Args:
        instance_id: Instance ID
        plugin_id: Plugin ID
        config_data: Dict with relative_path, absolute_path, file_type, etc.
        
    Returns:
        config_file_id: ID of registered file
    """
    cursor = self.db.cursor()
    
    # Calculate hash
    file_hash = self._calculate_config_file_hash(Path(config_data['absolute_path']))
    
    cursor.execute("""
        INSERT INTO endpoint_config_files
        (instance_id, plugin_id, config_file_type, relative_path, absolute_path, 
         file_hash, file_size_bytes, is_main_config, last_scanned_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            file_hash = VALUES(file_hash),
            file_size_bytes = VALUES(file_size_bytes),
            last_scanned_at = NOW(),
            last_modified_at = IF(file_hash != VALUES(file_hash), NOW(), last_modified_at)
    """, (
        instance_id,
        plugin_id,
        config_data['file_type'],
        config_data['relative_path'],
        config_data['absolute_path'],
        file_hash,
        config_data['file_size'],
        config_data['is_main_config']
    ))
    
    self.db.commit()
    config_file_id = cursor.lastrowid
    cursor.close()
    
    return config_file_id
```

---

### ✏️ **Config Modification Todos** (IDs 68-73)

| ID | Method/Class | File | Purpose |
|----|--------------|------|---------|
| 68 | Create module | `src/agent/config_modifier.py` | Safe config modification with backups |
| 69 | `ConfigModifier.modify_yaml_key()` | `config_modifier.py` | Update YAML key preserving format |
| 70 | `ConfigModifier.modify_json_key()` | `config_modifier.py` | Update JSON file |
| 71 | `ConfigModifier.modify_properties_key()` | `config_modifier.py` | Update .properties file |
| 72 | `ConfigModifier.safe_modify()` | `config_modifier.py` | Backup → modify → validate → commit |
| 73 | `ConfigModifier.rollback_on_error()` | `config_modifier.py` | Auto-restore if syntax breaks |

**ID 72 Implementation (safe_modify is the main method):**
```python
from pathlib import Path
from typing import Any, Tuple
from src.utils.yaml_handler import YAMLHandler
from src.utils.config_backup import ConfigBackup
import json

class ConfigModifier:
    """
    Safe config file modification with automatic backup and rollback.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.yaml_handler = YAMLHandler()
        self.backup_system = ConfigBackup(db_connection)
        
    def safe_modify(self, config_file_id: int, key_path: str, new_value: Any) -> Tuple[bool, str]:
        """
        Safely modify config file with backup and validation.
        
        Workflow:
        1. Create backup
        2. Modify file
        3. Validate syntax
        4. If valid: commit, log change
        5. If invalid: rollback to backup
        
        Args:
            config_file_id: ID from endpoint_config_files
            key_path: Dot-separated key path (e.g., 'settings.economy.enabled')
            new_value: New value to set
            
        Returns:
            (success: bool, message: str)
        """
        # Get file info
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, absolute_path, config_file_type, plugin_id, instance_id
            FROM endpoint_config_files
            WHERE id = %s
        """, (config_file_id,))
        file_info = cursor.fetchone()
        cursor.close()
        
        if not file_info:
            return (False, f"Config file {config_file_id} not found")
        
        file_path = Path(file_info['absolute_path'])
        file_type = file_info['config_file_type']
        
        # Step 1: Create backup
        try:
            backup_id = self.backup_system.create_backup(config_file_id, 'pre_modify')
        except Exception as e:
            return (False, f"Backup failed: {e}")
        
        # Step 2: Modify file
        try:
            if file_type in ['yaml', 'yml']:
                success = self.modify_yaml_key(file_path, key_path, new_value)
            elif file_type == 'json':
                success = self.modify_json_key(file_path, key_path, new_value)
            elif file_type == 'properties':
                success = self.modify_properties_key(file_path, key_path, new_value)
            else:
                return (False, f"Unsupported file type: {file_type}")
                
            if not success:
                self.rollback_on_error(backup_id)
                return (False, "Modification failed")
                
        except Exception as e:
            self.rollback_on_error(backup_id)
            return (False, f"Modification error: {e}")
        
        # Step 3: Validate syntax
        if file_type in ['yaml', 'yml']:
            is_valid, error_msg = self.yaml_handler.validate_syntax(file_path)
            if not is_valid:
                self.rollback_on_error(backup_id)
                return (False, f"Invalid YAML after modification: {error_msg}")
        
        # Step 4: Log change
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO endpoint_config_change_history
            (config_file_id, change_type, config_key, new_value, backup_id, 
             change_status, changed_by, applied_at)
            VALUES (%s, 'modify', %s, %s, %s, 'applied', 'system', NOW())
        """, (config_file_id, key_path, str(new_value), backup_id))
        self.db.commit()
        cursor.close()
        
        return (True, "Config modified successfully")
        
    def rollback_on_error(self, backup_id: int) -> bool:
        """Restore from backup if modification failed."""
        return self.backup_system.restore_backup(backup_id)
```

---

### 🔗 **Hierarchy Resolution Todos** (IDs 74-81)

| ID | Method | File | Purpose |
|----|--------|------|---------|
| 74 | Create module | `src/engine/hierarchy_resolver.py` | 7-level config resolution |
| 75 | `HierarchyResolver.resolve_config_value()` | `hierarchy_resolver.py` | Cascade through 7 levels |
| 76 | `HierarchyResolver.get_effective_value()` | `hierarchy_resolver.py` | Final value for instance/world/rank/player |
| 77 | `HierarchyResolver.get_override_chain()` | `hierarchy_resolver.py` | Show full hierarchy (for UI display) |
| 78 | `HierarchyResolver.apply_substitution_vars()` | `hierarchy_resolver.py` | Variable replacement like {{server_name}} |
| 79 | `HierarchyResolver.resolve_for_world()` | `hierarchy_resolver.py` | World-specific resolution |
| 80 | `HierarchyResolver.resolve_for_rank()` | `hierarchy_resolver.py` | Rank-specific resolution |
| 81 | `HierarchyResolver.resolve_for_player()` | `hierarchy_resolver.py` | Player-specific resolution |

**Hierarchy Order (highest priority last):**
1. GLOBAL (priority 0-10)
2. SERVER (priority 11-20)
3. META_TAG (priority 21-40)
4. INSTANCE (priority 41-50)
5. WORLD (priority 51-60)
6. RANK (priority 61-80)
7. PLAYER (priority 81-100)

**ID 75 Implementation:**
```python
from typing import Any, List, Dict, Optional

class HierarchyResolver:
    """
    Resolve config values through 7-level hierarchy.
    Order: GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        
    def resolve_config_value(
        self,
        plugin_name: str,
        config_key: str,
        instance_id: Optional[str] = None,
        world_name: Optional[str] = None,
        rank_name: Optional[str] = None,
        player_uuid: Optional[str] = None
    ) -> Tuple[Any, List[Dict]]:
        """
        Resolve config value through hierarchy.
        
        Args:
            plugin_name: Plugin identifier
            config_key: Config key path
            instance_id: Optional instance filter
            world_name: Optional world filter
            rank_name: Optional rank filter
            player_uuid: Optional player filter
            
        Returns:
            (final_value, override_chain)
            override_chain shows which scopes contributed
        """
        cursor = self.db.cursor(dictionary=True)
        override_chain = []
        final_value = None
        
        # Level 1: GLOBAL
        cursor.execute("""
            SELECT config_value, priority, scope_type
            FROM config_rules
            WHERE scope_type = 'GLOBAL'
                AND plugin_name = %s
                AND config_key = %s
                AND enabled = TRUE
            ORDER BY priority DESC
            LIMIT 1
        """, (plugin_name, config_key))
        global_rule = cursor.fetchone()
        if global_rule:
            final_value = global_rule['config_value']
            override_chain.append({
                'level': 'GLOBAL',
                'value': final_value,
                'priority': global_rule['priority']
            })
        
        # Level 2: SERVER (if instance_id provided)
        if instance_id:
            cursor.execute("""
                SELECT cr.config_value, cr.priority, cr.scope_selector
                FROM config_rules cr
                JOIN instances i ON cr.scope_selector = i.server_name
                WHERE cr.scope_type = 'SERVER'
                    AND i.instance_id = %s
                    AND cr.plugin_name = %s
                    AND cr.config_key = %s
                    AND cr.enabled = TRUE
                ORDER BY cr.priority DESC
                LIMIT 1
            """, (instance_id, plugin_name, config_key))
            server_rule = cursor.fetchone()
            if server_rule:
                final_value = server_rule['config_value']
                override_chain.append({
                    'level': 'SERVER',
                    'server': server_rule['scope_selector'],
                    'value': final_value,
                    'priority': server_rule['priority']
                })
        
        # Level 3: META_TAG (check instance tags)
        if instance_id:
            cursor.execute("""
                SELECT cr.config_value, cr.priority, mt.tag_name
                FROM config_rules cr
                JOIN meta_tags mt ON cr.scope_selector = mt.tag_name
                JOIN instance_meta_tags imt ON mt.tag_id = imt.tag_id
                WHERE cr.scope_type = 'META_TAG'
                    AND imt.instance_id = %s
                    AND cr.plugin_name = %s
                    AND cr.config_key = %s
                    AND cr.enabled = TRUE
                ORDER BY cr.priority DESC
                LIMIT 1
            """, (instance_id, plugin_name, config_key))
            tag_rule = cursor.fetchone()
            if tag_rule:
                final_value = tag_rule['config_value']
                override_chain.append({
                    'level': 'META_TAG',
                    'tag': tag_rule['tag_name'],
                    'value': final_value,
                    'priority': tag_rule['priority']
                })
        
        # Level 4: INSTANCE
        if instance_id:
            cursor.execute("""
                SELECT config_value, priority
                FROM config_rules
                WHERE scope_type = 'INSTANCE'
                    AND scope_selector = %s
                    AND plugin_name = %s
                    AND config_key = %s
                    AND enabled = TRUE
                ORDER BY priority DESC
                LIMIT 1
            """, (instance_id, plugin_name, config_key))
            instance_rule = cursor.fetchone()
            if instance_rule:
                final_value = instance_rule['config_value']
                override_chain.append({
                    'level': 'INSTANCE',
                    'instance': instance_id,
                    'value': final_value,
                    'priority': instance_rule['priority']
                })
        
        # Level 5: WORLD
        if instance_id and world_name:
            cursor.execute("""
                SELECT config_value, priority
                FROM world_config_rules
                WHERE instance_id = %s
                    AND world_name = %s
                    AND plugin_name = %s
                    AND config_key = %s
                    AND enabled = TRUE
                ORDER BY priority DESC
                LIMIT 1
            """, (instance_id, world_name, plugin_name, config_key))
            world_rule = cursor.fetchone()
            if world_rule:
                final_value = world_rule['config_value']
                override_chain.append({
                    'level': 'WORLD',
                    'world': world_name,
                    'value': final_value,
                    'priority': world_rule['priority']
                })
        
        # Level 6: RANK
        if rank_name:
            cursor.execute("""
                SELECT config_value, priority, server_name
                FROM rank_config_rules
                WHERE rank_name = %s
                    AND plugin_name = %s
                    AND config_key = %s
                    AND enabled = TRUE
                ORDER BY priority DESC
                LIMIT 1
            """, (rank_name, plugin_name, config_key))
            rank_rule = cursor.fetchone()
            if rank_rule:
                final_value = rank_rule['config_value']
                override_chain.append({
                    'level': 'RANK',
                    'rank': rank_name,
                    'value': final_value,
                    'priority': rank_rule['priority']
                })
        
        # Level 7: PLAYER (highest priority)
        if player_uuid:
            cursor.execute("""
                SELECT config_value, priority
                FROM player_config_overrides
                WHERE player_uuid = %s
                    AND plugin_name = %s
                    AND config_key = %s
                    AND (expires_at IS NULL OR expires_at > NOW())
                ORDER BY priority DESC
                LIMIT 1
            """, (player_uuid, plugin_name, config_key))
            player_rule = cursor.fetchone()
            if player_rule:
                final_value = player_rule['config_value']
                override_chain.append({
                    'level': 'PLAYER',
                    'player': player_uuid,
                    'value': final_value,
                    'priority': player_rule['priority']
                })
        
        cursor.close()
        return (final_value, override_chain)
```

---

### 🌐 **API Endpoint Todos** (IDs 83-107)

**Context:** Extends `src/web/api.py` (1649 lines)

#### **Config File Management Endpoints** (IDs 83-90)

| ID | Endpoint | Method | Purpose | Response Example |
|----|----------|--------|---------|------------------|
| 83 | `/api/instances/{id}/config-files` | GET | List all tracked config files for instance | `[{id: 1, plugin: "EssentialsX", path: "plugins/Essentials/config.yml", type: "yaml"}]` |
| 84 | `/api/instances/{id}/plugins/{plugin}/configs` | GET | List config files for specific plugin | `[{id: 1, file: "config.yml", size: 12345}]` |
| 85 | `/api/config-file/{id}` | GET | Get config file metadata | `{id: 1, path: "...", hash: "abc123", last_modified: "2025-11-18T..."}` |
| 86 | `/api/config-file/modify` | POST | Modify config key safely | `{success: true, backup_id: 42}` |
| 87 | `/api/config-file/backup` | POST | Create manual backup | `{backup_id: 43}` |
| 88 | `/api/config-file/backups/{id}` | GET | List backups for config file | `[{backup_id: 1, created_at: "...", reason: "pre_modify"}]` |
| 89 | `/api/config-file/rollback` | POST | Restore from backup | `{success: true, restored_backup_id: 42}` |
| 90 | `/api/config/hierarchy/{instance}/{plugin}/{key}` | GET | Show full hierarchy chain | `{final_value: true, chain: [{level: "GLOBAL", value: false}, ...]}` |

**ID 86 Request Body:**
```json
{
  "config_file_id": 123,
  "key_path": "settings.economy.enabled",
  "new_value": true
}
```

**ID 86 Implementation:**
```python
@app.post("/api/config-file/modify")
async def modify_config_file(request: Request):
    """Safely modify config file with backup and validation."""
    data = await request.json()
    
    config_file_id = data.get('config_file_id')
    key_path = data.get('key_path')
    new_value = data.get('new_value')
    
    if not all([config_file_id, key_path, new_value is not None]):
        return JSONResponse(
            status_code=400,
            content={"error": "Missing required fields"}
        )
    
    # Use ConfigModifier
    modifier = ConfigModifier(db_connection)
    success, message = modifier.safe_modify(config_file_id, key_path, new_value)
    
    if success:
        return JSONResponse(content={
            "success": True,
            "message": message,
            "config_file_id": config_file_id,
            "key_path": key_path,
            "new_value": new_value
        })
    else:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": message}
        )
```

---

#### **Multi-Level Scope Endpoints** (IDs 91-94)

| ID | Endpoint | Method | Purpose | Request Body |
|----|----------|--------|---------|--------------|
| 91 | `/api/config/set-world` | POST | Set world-level config override | `{instance_id, world_name, plugin_name, config_key, config_value}` |
| 92 | `/api/config/set-rank` | POST | Set rank-level config override | `{server_name, rank_name, plugin_name, config_key, config_value}` |
| 93 | `/api/config/set-player` | POST | Set player-level override | `{player_uuid, plugin_name, config_key, config_value, expires_at?}` |
| 94 | `/api/config/clear-override` | DELETE | Remove scope override | `{scope_type, scope_selector, plugin_name, config_key}` |

**ID 91 Implementation:**
```python
@app.post("/api/config/set-world")
async def set_world_config(request: Request):
    """Set world-level config override."""
    data = await request.json()
    
    cursor = db_connection.cursor()
    cursor.execute("""
        INSERT INTO world_config_rules
        (instance_id, world_name, plugin_name, config_file, config_key, config_value, 
         value_type, priority, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'api')
        ON DUPLICATE KEY UPDATE
            config_value = VALUES(config_value),
            updated_at = NOW()
    """, (
        data['instance_id'],
        data['world_name'],
        data['plugin_name'],
        data.get('config_file', 'config.yml'),
        data['config_key'],
        data['config_value'],
        data.get('value_type', 'string'),
        data.get('priority', 50)
    ))
    db_connection.commit()
    rule_id = cursor.lastrowid
    cursor.close()
    
    return JSONResponse(content={
        "success": True,
        "rule_id": rule_id,
        "message": f"World config set for {data['world_name']}"
    })
```

---

#### **Variance & Feature Endpoints** (IDs 95-103)

| ID | Endpoint | Method | Purpose | Response |
|----|----------|--------|---------|----------|
| 95 | `/api/variance/by-scope` | GET | Variance analysis at each scope level | `{GLOBAL: 0.05, SERVER: 0.12, ...}` |
| 96 | `/api/variance/world/{world}` | GET | World-specific variances | `{configs: [{key: "...", variance: 0.2}]}` |
| 97 | `/api/variance/rank/{rank}` | GET | Rank-specific variances | Similar to 96 |
| 98 | `/api/meta-tags/world` | POST | Tag a world | `{instance_id, world_name, tag_id}` |
| 99 | `/api/meta-tags/rank` | POST | Tag a rank | `{server_name, rank_name, tag_id}` |
| 100 | `/api/meta-tags/player` | POST | Tag a player | `{player_uuid, tag_id, expires_at?}` |
| 101 | `/api/features/inventory` | GET | Feature inventory report | `{instances: [{id: "SMP201", features: ["economy", "pvp"]}]}` |
| 102 | `/api/features/server/{server}` | GET | Server capabilities | `{max_ram_gb: 64, java_version: "21", ...}` |
| 103 | `/api/features/instance/{id}` | GET | Instance feature set | `{features: [{name: "economy", detected_via: "Vault"}]}` |

---

#### **Advanced Endpoints** (IDs 104-107)

| ID | Endpoint | Method | Purpose | Use Case |
|----|----------|--------|---------|----------|
| 104 | `/api/tags/check-dependencies` | POST | Validate tag dependencies | Before applying tag, check if required tags present |
| 105 | `/api/tags/check-conflicts` | POST | Detect tag conflicts | Warn if 'creative-only' + 'survival-hardcore' |
| 106 | `/api/deploy/by-tag` | POST | Deploy configs to all instances with tag | Apply config to all 'economy-enabled' instances |
| 107 | `/api/config/propagate` | POST | Cascade config down hierarchy | Push GLOBAL value to all children |

---

### 🎨 **UI Component Todos** (IDs 109-133)

**Context:** Extends `src/web/static/` directory

#### **Config File Browser** (IDs 109-112)

| ID | File | Purpose | Key Features |
|----|------|---------|-------------|
| 109 | `config_files.html` | Browse all config files | Table with search, filter by plugin/instance/type |
| 110 | JavaScript in 109 | Config file browser logic | AJAX search, DataTables integration |
| 111 | Code editor component | Syntax-highlighted editor | Monaco Editor or CodeMirror, YAML syntax |
| 112 | Backup/restore buttons | Quick rollback UI | Show backup history, one-click restore |

**ID 109 HTML Structure:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Config File Browser</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
</head>
<body>
    <h1>Config File Browser</h1>
    
    <div class="filters">
        <select id="instanceFilter">
            <option value="">All Instances</option>
            <!-- Populated via API -->
        </select>
        
        <select id="pluginFilter">
            <option value="">All Plugins</option>
            <!-- Populated via API -->
        </select>
        
        <select id="typeFilter">
            <option value="">All Types</option>
            <option value="yaml">YAML</option>
            <option value="json">JSON</option>
            <option value="properties">Properties</option>
        </select>
    </div>
    
    <table id="configFilesTable">
        <thead>
            <tr>
                <th>ID</th>
                <th>Instance</th>
                <th>Plugin</th>
                <th>File Path</th>
                <th>Type</th>
                <th>Size</th>
                <th>Last Modified</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            <!-- Populated via DataTables AJAX -->
        </tbody>
    </table>
    
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
    <script src="/static/js/config_files.js"></script>
</body>
</html>
```

---

#### **World Config UI** (IDs 113-116)

| ID | File | Purpose | Features |
|----|------|---------|----------|
| 113 | `world_config.html` | World-level config management | CRUD for world_config_rules |
| 114 | World selector dropdown | Choose world | Populated from instances table (world_name discovery) |
| 115 | World config editor | Override editor | Form to set world-specific values |
| 116 | World meta-tag UI | Assign tags to worlds | Drag-drop interface for tagging |

---

#### **Rank Config UI** (IDs 117-119)

| ID | File | Purpose | Integration |
|----|------|---------|-------------|
| 117 | `rank_config.html` | Rank-level config management | CRUD for rank_config_rules |
| 118 | LuckPerms rank integration | Fetch ranks from LuckPerms | Query LuckPerms database or API |
| 119 | Rank config editor | Per-rank overrides | Form with rank selector + config key/value |

**ID 118 Note:** 
- LuckPerms stores ranks in `luckperms_groups` table
- Need database connection to LuckPerms MySQL DB
- Alternative: Parse `luckperms/groups/*.yml` files

---

#### **Player Override UI** (IDs 120-122)

| ID | File | Purpose | Features |
|----|------|---------|----------|
| 120 | `player_overrides.html` | Player-specific config overrides | CRUD for player_config_overrides |
| 121 | Player search/autocomplete | Find players | Query Minecraft UUIDs, autocomplete by name |
| 122 | Player override editor | Set player overrides | Support temporary overrides with `expires_at` |

---

#### **Hierarchy Viewer** (IDs 123-125)

| ID | File | Purpose | Visualization |
|----|------|---------|---------------|
| 123 | `hierarchy_viewer.html` | Visual config hierarchy | Interactive graph showing 7 levels |
| 124 | D3.js graph | Interactive visualization | Tree diagram with nodes for each scope level |
| 125 | Breadcrumb trail | Show override sources | List: GLOBAL (false) → SERVER (true) → INSTANCE (unchanged) = **true** |

**ID 124 Visualization:**
```javascript
// D3.js tree layout
const data = {
    name: "Config: settings.pvp.enabled",
    children: [
        {
            name: "GLOBAL: false (priority 5)",
            children: [
                {
                    name: "SERVER (Hetzner): true (priority 15) ✓",
                    children: [
                        { name: "INSTANCE (SMP201): unchanged" }
                    ]
                }
            ]
        }
    ]
};

// Final value: true (from SERVER level)
```

---

#### **Variance Dashboard** (IDs 126-128)

| ID | Component | Purpose | Display |
|----|-----------|---------|---------|
| 126 | Update `variance.html` | Add multi-scope view | Tabs for each scope level |
| 127 | Scope selector | Switch between scopes | Dropdown: GLOBAL / SERVER / INSTANCE / WORLD / RANK / PLAYER |
| 128 | Variance heatmap | Visual variance by scope | Color-coded cells: green (low variance) → red (high variance) |

---

#### **Feature Inventory UI** (IDs 129-132)

| ID | File | Purpose | Display |
|----|------|---------|---------|
| 129 | `feature_inventory.html` | Feature tracking dashboard | Matrix of instances × features |
| 130 | Server capability matrix | What each server supports | Table: Server / Max RAM / Java Version / Max Instances |
| 131 | Instance feature comparison | Compare feature sets | Side-by-side comparison of 2+ instances |
| 132 | World feature tracking | Per-world capabilities | List features per world (e.g., world has custom-mobs, nether doesn't) |

---

#### **Navigation Update** (IDs 133)

| ID | File | Change | New Links |
|----|------|--------|-----------|
| 133 | `index.html` | Add navigation links | Config Files, World Config, Rank Config, Player Overrides, Hierarchy Viewer, Feature Inventory |

---

### ✅ **Testing Todos** (IDs 134-146)

| ID | Test File | Test Function | Purpose | Assertions |
|----|-----------|---------------|---------|------------|
| 134 | `test_yaml_handler.py` | `test_format_preservation()` | YAML round-trip preserves formatting | Comments preserved, indentation same |
| 135 | `test_yaml_handler.py` | `test_nested_key_modification()` | Modify deep nested key | `data['a']['b']['c'] = 'new'` works |
| 136 | `test_yaml_handler.py` | `test_comment_preservation()` | Comments survive modification | `# This is a comment` still present |
| 137 | `test_config_backup.py` | `test_backup_creation()` | Backup created successfully | backup_id returned, content matches file |
| 138 | `test_config_backup.py` | `test_backup_content()` | Backup stores full content | file_content field populated |
| 139 | `test_config_backup.py` | `test_rollback_after_bad_change()` | Rollback restores original | File content matches backup |
| 140 | `test_hierarchy_resolver.py` | `test_7_level_cascade()` | All 7 levels resolved correctly | Final value = PLAYER override |
| 141 | `test_hierarchy_resolver.py` | `test_global_server_instance()` | 3-level resolution | INSTANCE > SERVER > GLOBAL |
| 142 | `test_hierarchy_resolver.py` | `test_world_rank_player()` | Advanced levels work | PLAYER > RANK > WORLD |
| 143 | `test_hierarchy_resolver.py` | `test_variable_substitution()` | `{{server_name}}` replaced | Value = "Hetzner" not "{{server_name}}" |
| 144 | `test_instance_conf_parser.py` | `test_uuid_extraction()` | AMP UUID parsed | instance_id is valid UUID |
| 145 | `test_instance_conf_parser.py` | `test_friendly_name()` | Friendly name extracted | friendly_name = "ArchiveSMP Season 2" |
| 146 | `test_instance_conf_parser.py` | `test_port_parsing()` | Port number correct | port = 25565 |

**ID 134 Test Example:**
```python
import pytest
from src.utils.yaml_handler import YAMLHandler
from pathlib import Path

def test_format_preservation():
    """Test that YAML formatting is preserved after modification."""
    handler = YAMLHandler()
    
    # Create test file
    test_content = """# Main config
settings:
  economy:
    enabled: false  # Economy disabled by default
    starting-balance: 100
"""
    test_file = Path('/tmp/test_config.yml')
    test_file.write_text(test_content)
    
    # Read, modify, write
    data = handler.read_yaml(test_file)
    handler.modify_key(data, 'settings.economy.enabled', True)
    handler.write_yaml(test_file, data)
    
    # Read back and check
    modified_content = test_file.read_text()
    
    assert '# Main config' in modified_content  # Comment preserved
    assert 'enabled: true' in modified_content  # Value changed
    assert '# Economy disabled by default' in modified_content  # Inline comment preserved
    assert modified_content.count('  ') == test_content.count('  ')  # Indentation same
```

---

### 🚀 **Agent Integration Todos** (IDs 147-154)

**Context:** Integrate new capabilities into main agent loop

| ID | Integration | File | Change |
|----|-------------|------|--------|
| 147 | Integrate PluginFolderWatcher | `production_endpoint_agent.py` | Import and initialize watcher in `__init__()` |
| 148 | Start watchers on startup | `production_endpoint_agent.py` | In `start()` method, start observer for each instance |
| 149 | Handle immediate plugin scan | `production_endpoint_agent.py` | Callback triggers `_discover_instance_plugins()` |
| 150 | Auto-apply config rules | `agent_database_methods.py` | After plugin registration, apply matching config_rules |
| 151 | Cleanup orphaned configs | `agent_database_methods.py` | On plugin removal, mark configs as deleted |
| 152 | Add config file discovery | `production_endpoint_agent.py` | Call `_scan_all_plugin_configs()` in main scan |
| 153 | Track config file hashes | `agent_database_methods.py` | Update endpoint_config_files.file_hash on each scan |
| 154 | Auto-backup before agent mods | `agent_database_methods.py` | Before modifying config, create backup |

**ID 147 Implementation:**
```python
# In production_endpoint_agent.py __init__()

from src.agent.plugin_folder_watcher import PluginFolderWatcher
from watchdog.observers import Observer

def __init__(self, config):
    # ... existing init code ...
    
    self.observers = []  # Store Observer instances
    self.plugin_watchers = {}  # instance_id -> PluginFolderWatcher
    
def start(self):
    """Start agent with file watchers."""
    # ... existing start code ...
    
    # Start file watchers for all instances
    self._start_file_watchers()
    
def _start_file_watchers(self):
    """Initialize file watchers for all instances."""
    cursor = self.db.cursor(dictionary=True)
    cursor.execute("""
        SELECT instance_id, instance_folder_name, instance_base_path
        FROM instances
        WHERE instance_base_path IS NOT NULL
    """)
    instances = cursor.fetchall()
    cursor.close()
    
    for instance in instances:
        plugins_path = Path(instance['instance_base_path']) / 'Minecraft' / 'plugins'
        
        if not plugins_path.exists():
            continue
        
        # Create watcher
        watcher = PluginFolderWatcher(
            instance_id=instance['instance_id'],
            plugins_path=plugins_path,
            callback=self._handle_plugin_change
        )
        
        # Create observer
        observer = Observer()
        observer.schedule(watcher, str(plugins_path), recursive=False)
        observer.start()
        
        self.observers.append(observer)
        self.plugin_watchers[instance['instance_id']] = watcher
        
        logger.info(f"Started file watcher for {instance['instance_id']}")
        
def _handle_plugin_change(self, instance_id: str, event_type: str, changes: List):
    """Handle plugin folder changes."""
    logger.info(f"Plugin change detected for {instance_id}: {event_type}")
    
    # Trigger immediate scan
    self._discover_instance_plugins(instance_id)
```

---

### 📤 **Deployment Todos** (IDs 156-168)

**Context:** Deploy to Hetzner production server (135.181.212.169)

| ID | Task | Command/Action | Location |
|----|------|----------------|----------|
| 156 | Run create_dynamic_metadata_system.sql | `mysql -u root -p homeamp_config < create_dynamic_metadata_system.sql` | Hetzner |
| 157 | Run instance path ALTER statements | `mysql -u root -p homeamp_config < add_instance_path_columns.sql` | Hetzner |
| 158 | Run endpoint config tables | `mysql -u root -p homeamp_config < create_endpoint_config_tables.sql` | Hetzner |
| 159 | Run multi-level scope tables | `mysql -u root -p homeamp_config < create_multi_level_scope_tables.sql` | Hetzner |
| 160 | Verify tables created | `mysql -u root -p homeamp_config -e "SHOW TABLES;"` | Hetzner |
| 161 | Deploy requirements.txt | SFTP copy `requirements.txt` to `/opt/archivesmp-config-manager/` | Hetzner |
| 162 | Install ruamel.yaml | `pip install ruamel.yaml==0.18.5` | Hetzner |
| 163 | Copy new agent files | SFTP copy `src/` directory to `/opt/archivesmp-config-manager/src/` | Hetzner |
| 164 | Copy API endpoints | SFTP copy `api.py` to `/opt/archivesmp-config-manager/src/web/` | Hetzner |
| 165 | Copy UI files | SFTP copy `src/web/static/` to server | Hetzner |
| 166 | Update agent.yaml config | Edit `/etc/archivesmp/agent.yaml` to enable new features | Hetzner |
| 167 | Restart web API | `sudo systemctl restart archivesmp-webapi.service` | Hetzner |
| 168 | Restart agent | `sudo systemctl restart homeamp-agent.service` | Hetzner |

**Deployment Script Example:**
```bash
#!/bin/bash
# deploy_to_hetzner.sh

SERVER="root@135.181.212.169"
REMOTE_DIR="/opt/archivesmp-config-manager"

echo "Deploying to Hetzner..."

# 1. Copy SQL scripts
scp scripts/*.sql $SERVER:/tmp/

# 2. Run SQL migrations
ssh $SERVER << 'EOF'
cd /tmp
mysql -u root -p homeamp_config < create_dynamic_metadata_system.sql
mysql -u root -p homeamp_config < add_instance_path_columns.sql
mysql -u root -p homeamp_config < create_endpoint_config_tables.sql
mysql -u root -p homeamp_config < create_multi_level_scope_tables.sql
EOF

# 3. Copy code
rsync -avz --exclude '__pycache__' src/ $SERVER:$REMOTE_DIR/src/
rsync -avz requirements.txt $SERVER:$REMOTE_DIR/

# 4. Install dependencies
ssh $SERVER << 'EOF'
cd /opt/archivesmp-config-manager
pip install -r requirements.txt
EOF

# 5. Restart services
ssh $SERVER << 'EOF'
systemctl restart archivesmp-webapi.service
systemctl restart homeamp-agent.service
EOF

echo "Deployment complete!"
```

---

### ✔️ **Verification Todos** (IDs 169-188)

| ID | Verification | Command/Check | Expected Result |
|----|--------------|---------------|-----------------|
| 169 | Instance folders discovered | Check agent logs: `journalctl -u homeamp-agent -n 50` | See "Discovered folder: ArchiveSMP-Season2 -> UUID: ..." |
| 170 | Instance.conf parsing | `SELECT instance_folder_name, amp_instance_id FROM instances;` | All 11 instances have folder names |
| 171 | Instance paths populated | `SELECT instance_id, instance_base_path FROM instances;` | All paths like `/home/amp/.ampdata/instances/...` |
| 172 | Plugin configs discovered | `SELECT COUNT(*) FROM endpoint_config_files;` | > 0 config files tracked |
| 173 | File watchers started | Check agent startup logs | "Started file watcher for SMP201" × 11 instances |
| 174 | Manual plugin add test | Copy JAR to `/plugins/` folder | Agent log shows immediate scan within 10s |
| 175 | Manual plugin remove test | Delete JAR from `/plugins/` | Agent log shows plugin removed |
| 176 | Config modification formatting | Modify YAML, check file | Comments and indentation preserved |
| 177 | Backup created | `SELECT COUNT(*) FROM endpoint_config_backups;` | > 0 backups exist |
| 178 | Rollback works | Restore backup, check file content | Original content restored |
| 179 | Hierarchy resolver | Call API `/api/config/hierarchy/SMP201/EssentialsX/enabled` | Returns chain with multiple levels |
| 180 | WORLD-level override | Set world config, query effective value | World override takes precedence |
| 181 | RANK-level override | Set rank config, query effective value | Rank override works |
| 182 | PLAYER-level override | Set player override, query | Player override is highest priority |
| 183 | UI loads | Navigate to `http://135.181.212.169:8000/config_files.html` | Page loads without errors |
| 184 | Config file browser | Open config files page | Table displays all config files |
| 185 | World config editor | Open world config page | Can set world-specific overrides |
| 186 | Rank config editor | Open rank config page | Can set rank-specific overrides |
| 187 | Hierarchy viewer | Open hierarchy viewer | Visual graph displays |
| 188 | Feature inventory | Open feature inventory | Matrix displays instance features |

---

### 📖 **Documentation Todos** (IDs 190-194)

| ID | Document | Action | Content |
|----|----------|--------|---------|
| 190 | PRODUCTION_DYNAMIC_SYSTEM.md | Update | Add sections: Multi-Level Scopes, Config Modification, File Watching |
| 191 | MULTI_LEVEL_SCOPE_GUIDE.md | Create | Explain 7-level hierarchy, examples, priority system |
| 192 | CONFIG_MODIFICATION_GUIDE.md | Create | How to safely modify configs, backup/restore, best practices |
| 193 | API_DOCUMENTATION.md | Update | Add all 25 new endpoints with examples |
| 194 | USER_GUIDE.md | Create | End-user guide for world/rank/player config management |

---

### 💾 **Version Control Todos** (IDs 195-200)

| ID | Action | Command | Files |
|----|--------|---------|-------|
| 195 | Stage SQL files | `git add scripts/*.sql` | All schema files |
| 196 | Stage Python modules | `git add src/` | New utils, agent methods, parsers |
| 197 | Stage UI files | `git add src/web/static/*.html src/web/static/js/*.js` | New HTML pages |
| 198 | Stage requirements | `git add requirements.txt` | Updated dependencies |
| 199 | Commit | `git commit -m "feat: multi-level scope system + endpoint config modification"` | All staged files |
| 200 | Push | `git push origin master` | Push to GitHub |

**Commit Message Template:**
```
feat: multi-level scope system + endpoint config modification

- Added 7-level config hierarchy (GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER)
- Implemented format-preserving YAML modification with ruamel.yaml
- Added config backup/restore system
- Built hierarchy resolver with variable substitution
- Created 25+ new API endpoints for multi-level config management
- Added file watchers for real-time plugin detection
- Implemented Instance.conf parser for AMP folder mapping
- Built UIs for world/rank/player config management
- Added feature inventory and capability tracking
- Extended database schema with 10+ new tables

Tables: endpoint_config_files, endpoint_config_backups, world_meta_tags, rank_meta_tags, 
        player_meta_tags, world_config_rules, rank_config_rules, player_config_overrides,
        tag_dependencies, tag_conflicts, instance_feature_inventory, server_capabilities

Files changed: 50+ files, ~3000 lines of new code, 800 lines SQL
```

---

### 🔮 **Advanced Feature Todos** (IDs 212-243)

#### **Tag Suggestion Engine** (IDs 212-215)

| ID | Method/Class | Purpose | Algorithm |
|----|--------------|---------|-----------|
| 212 | Create `src/engine/tag_suggestion_engine.py` | ML-based tag suggestions | Heuristic + pattern matching |
| 213 | `TagSuggestionEngine.analyze_plugin_set()` | Suggest tags based on plugins | If has Vault + economy plugin → suggest 'economy' tag |
| 214 | `TagSuggestionEngine.analyze_config_patterns()` | Detect patterns in configs | If `pvp=true` in multiple configs → suggest 'pvp-enabled' |
| 215 | `TagSuggestionEngine.confidence_scoring()` | Rank suggestions by confidence | Return sorted list with scores 0.0-1.0 |

**ID 213 Example Logic:**
```python
def analyze_plugin_set(self, instance_id: str) -> List[Dict]:
    """
    Suggest tags based on installed plugins.
    
    Returns:
        [{tag_name: "economy", confidence: 0.95, reason: "Has Vault + EssentialsX"}]
    """
    cursor = self.db.cursor(dictionary=True)
    
    # Get plugins
    cursor.execute("""
        SELECT plugin_name FROM instance_plugins WHERE instance_id = %s
    """, (instance_id,))
    plugins = [row['plugin_name'] for row in cursor.fetchall()]
    
    suggestions = []
    
    # Economy detection
    if 'Vault' in plugins and any(p in plugins for p in ['EssentialsX', 'CMI', 'BossShopPro']):
        suggestions.append({
            'tag_name': 'economy',
            'confidence': 0.95,
            'reason': 'Has Vault + economy plugin'
        })
    
    # PvP detection
    pvp_plugins = ['CombatLog', 'Heroes', 'mcMMO']
    if any(p in plugins for p in pvp_plugins):
        suggestions.append({
            'tag_name': 'pvp-enabled',
            'confidence': 0.85,
            'reason': f'Has PvP plugins: {[p for p in pvp_plugins if p in plugins]}'
        })
    
    return suggestions
```

---

#### **Feature Detector** (IDs 216-221)

| ID | Method | Purpose | Detection Method |
|----|--------|---------|------------------|
| 216 | Create `src/engine/feature_detector.py` | Feature inventory system | Plugin-based + config-based detection |
| 217 | `FeatureDetector.detect_economy()` | Economy feature | Vault + economy plugin |
| 218 | `FeatureDetector.detect_permissions()` | Permission system | LuckPerms / PermissionsEx |
| 219 | `FeatureDetector.detect_pvp_systems()` | PvP features | PvP plugins or `pvp=true` in server.properties |
| 220 | `FeatureDetector.detect_custom_items()` | Custom items | ItemsAdder / Oraxen / MMOItems |
| 221 | `FeatureDetector.build_feature_matrix()` | Cross-instance matrix | Compare features across all instances |

---

#### **Config Propagator** (IDs 222-226)

| ID | Method | Purpose | Example |
|----|--------|---------|---------|
| 222 | Create `src/engine/config_propagator.py` | Config cascade engine | Push global changes down |
| 223 | `ConfigPropagator.propagate_from_global()` | Push GLOBAL configs | Set GLOBAL → apply to all instances without overrides |
| 224 | `ConfigPropagator.propagate_to_children()` | Cascade to lower levels | SERVER change → update all instances on that server |
| 225 | `ConfigPropagator.skip_overridden()` | Don't overwrite overrides | If INSTANCE has override, don't apply GLOBAL |
| 226 | `ConfigPropagator.preview_changes()` | Dry-run mode | Show what would change without applying |

---

#### **Tag Validator** (IDs 227-231)

| ID | Method | Purpose | Example |
|----|--------|---------|---------|
| 227 | Create `src/engine/tag_validator.py` | Tag dependency/conflict checking | Validate before applying tags |
| 228 | `TagValidator.check_dependencies()` | Validate required tags | If applying 'economy', check if 'vault-present' exists |
| 229 | `TagValidator.check_conflicts()` | Detect conflicts | Warn if 'creative-only' + 'survival-hardcore' |
| 230 | `TagValidator.suggest_missing_deps()` | Auto-suggest dependencies | "Tag 'economy' requires 'vault-present' - apply it?" |
| 231 | `TagValidator.warn_conflicts()` | Warn before applying | "Tag 'X' conflicts with existing tag 'Y' - continue?" |

---

### 🌍 **Cross-Server Sync Todos** (IDs 244-250)

| ID | Component | Purpose | Sync Method |
|----|-----------|---------|-------------|
| 244 | READ network topology | Understand Hetzner ↔ OVH connection | Review firewall rules, VPN/tunnel |
| 245 | Create `src/network/cross_server_sync.py` | Sync between servers | HTTP API calls or database replication |
| 246 | `CrossServerSync.sync_meta_tags()` | Tag synchronization | POST `/api/meta-tags/sync` between servers |
| 247 | `CrossServerSync.sync_global_configs()` | Global config sync | Replicate config_rules WHERE scope_type='GLOBAL' |
| 248 | `CrossServerSync.conflict_resolution()` | Handle sync conflicts | Last-write-wins or manual resolution |
| 249 | CREATE TABLE cross_server_sync_log | Track sync operations | Log what was synced when |
| 250 | CREATE TABLE sync_conflicts | Store conflicts | Manual resolution queue |

---

### 🏁 **Final Integration Todos** (IDs 251-255)

| ID | Task | Environment | Success Criteria |
|----|------|-------------|------------------|
| 251 | Full system integration test | Dev instance | All components work together |
| 252 | Load test | Dev | 20 concurrent config mods without errors |
| 253 | Backup entire system | Production | Full DB dump + file backup |
| 254 | Deploy to OVH | OVH Ryzen (37.187.143.41) | Same as Hetzner deployment |
| 255 | Update documentation | All docs | Reflect production deployment state |

---

## 🎯 **Summary: 255 Actionable Building Blocks**

**Breakdown by Category:**
- 📚 Context Refreshes: 12 todos
- 🗄️ Database Schema: 22 todos (SQL DDL)
- 📦 Dependencies: 3 todos
- 🔧 Core Utilities: 18 todos (YAML handler, backups, watchers)
- 📄 Parsers: 4 todos (Instance.conf)
- 🤖 Agent Discovery: 9 todos
- 💾 Database Methods: 6 todos
- ✏️ Config Modification: 6 todos
- 🔗 Hierarchy Resolution: 8 todos
- 🌐 API Endpoints: 25 todos
- 🎨 UI Components: 25 todos
- ✅ Testing: 13 todos
- 🚀 Agent Integration: 8 todos
- 📤 Deployment: 13 todos
- ✔️ Verification: 20 todos
- 📖 Documentation: 5 todos
- 💾 Version Control: 6 todos
- 🔮 Advanced Features: 32 todos
- 🌍 Cross-Server Sync: 7 todos
- 🏁 Final Integration: 5 todos

**Total: 255 granular, actionable todos with implementation details, code examples, SQL schemas, API signatures, and verification steps.**

---

*[End of TODO Implementation Details]*

Summarized conversation historyCreated **255 granular todos** organized as building blocks for the full meta-tag + endpoint config modification system:

Summarized conversation historyCreated **255 granular todos** organized as building blocks for the full meta-tag + endpoint config modification system:

## Structure:

📚 **Context Refresh Points** (IDs 1-3, 39, 51, 61, 82, 108, 155, 189, 211, 244)
- Strategically placed documentation reads to refresh LLM context
- Review key docs before major implementation phases

🗄️ **Database Schema** (IDs 4-25)
- ALTER instances table for folder tracking
- CREATE endpoint config tables (files, backups, change history)
- CREATE multi-level scope tables (world, rank, player)
- CREATE advanced tables (dependencies, conflicts, features, capabilities)

📦 **Dependencies** (IDs 26-28)
- Add ruamel.yaml for format-preserving YAML modification
- Add configparser for .properties handling

🔧 **Core Utilities** (IDs 29-46)
- YAML handler with format preservation
- Config backup/restore system
- Plugin/datapack folder watchers

📄 **Parsers** (IDs 47-50)
- Instance.conf parser for AMP folder mapping

🤖 **Agent Discovery** (IDs 52-60)
- Instance folder discovery with actual paths
- Config file discovery and tracking

💾 **Database Methods** (IDs 62-67)
- Config file registration
- Backup/restore operations
- Change history tracking

✏️ **Config Modification** (IDs 68-73)
- Safe YAML/JSON/properties modification
- Automatic rollback on syntax errors

🔗 **Hierarchy Resolution** (IDs 74-81)
- 7-level scope cascade (GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER)
- Variable substitution

🌐 **API Endpoints** (IDs 83-107)
- Config file management (25 new endpoints)
- Multi-level scope endpoints
- Feature inventory APIs

🎨 **UI Components** (IDs 109-133)
- Config file browser/editor
- World/rank/player config UIs
- Hierarchy visualizer
- Feature inventory dashboard

✅ **Testing** (IDs 134-146)
- YAML handler tests
- Backup/restore tests
- Hierarchy resolver tests
- Parser tests

🚀 **Agent Integration** (IDs 147-154)
- File watcher integration
- Auto-apply rules to new plugins
- Config hash tracking

📤 **Deployment** (IDs 156-168)
- Schema deployment to Hetzner
- Code deployment
- Service restarts

✔️ **Verification** (IDs 169-189)
- Database verification (30 checks)
- Feature verification
- UI verification

📖 **Documentation** (IDs 190-194)
- Update system docs
- Create user guides

💾 **Version Control** (IDs 195-200)
- Commit strategy

🔮 **Advanced Features** (IDs 212-243)
- Tag suggestion engine (ML-based)
- Feature detector
- Config propagator
- Tag dependency validator

🌍 **Cross-Server Sync** (IDs 244-250)
- Hetzner ⟷ OVH synchronization
- Conflict resolution

🏁 **Final Integration** (IDs 251-255)
- Full system testing
- Production deployment

Each todo is **one concrete building block** - one file, one method, one table, one endpoint, one test, or one verification step.