# Endpoint Config File Tracking Analysis

## 🎯 Critical Gaps Identified

### ❌ Missing: Instance Folder/Path Tracking
**Current State:**
- `instances` table has `instance_id` (BENT01, SMP201, etc.)
- **NO** `instance_folder_name` column
- **NO** `instance_base_path` column
- **NO** `amp_instance_id` tracking (AMP's internal UUID)

**Production Reality:**
- AMP stores instances at: `/home/amp/.ampdata/instances/{FOLDER_NAME}/`
- Folder name **MAY NOT** match instance_id
- Example: `instance_id='SMP201'` but folder might be `SMP201-Season2` or `archivesmp-main`

**Required:**
```sql
ALTER TABLE instances ADD COLUMN instance_folder_name VARCHAR(128);
ALTER TABLE instances ADD COLUMN instance_base_path VARCHAR(512);
ALTER TABLE instances ADD COLUMN amp_instance_id VARCHAR(64);
```

### ❌ Missing: Endpoint YAML Location Tracking
**Current State:**
- NO tracking of where endpoint config files are located
- Agent assumes default locations but doesn't store them

**Production Reality:**
- Each plugin may have MULTIPLE config files:
  - `plugins/PluginName/config.yml`
  - `plugins/PluginName/messages.yml`
  - `plugins/PluginName/data.yml`
  - `plugins/PluginName/settings/advanced.yml`
- File locations can change between plugin versions
- Some plugins use JSON, TOML, or properties files

**Required:**
```sql
CREATE TABLE endpoint_config_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_file_type ENUM('yaml', 'json', 'toml', 'properties', 'xml', 'hocon', 'other'),
    relative_path VARCHAR(1024) NOT NULL,  -- Relative to instance base
    absolute_path VARCHAR(1024),
    file_hash VARCHAR(64),  -- SHA-256 for change detection
    last_modified_at TIMESTAMP,
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_main_config BOOLEAN DEFAULT FALSE,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    UNIQUE KEY unique_instance_plugin_path (instance_id, plugin_id, relative_path),
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id)
);
```

### ❌ Missing: YAML Modification Capability
**Current State:**
- NO YAML parser/writer in agent code
- Config changes are theoretical - no implementation to actually modify files

**Production Reality:**
- Need to parse YAML preserving:
  - Comments
  - Formatting
  - Order
  - Indentation
- Need to handle:
  - Nested keys (e.g., `settings.economy.starting-balance`)
  - Lists/arrays
  - Multi-line strings
  - Anchors/aliases
  - Complex data types

**Required Libraries:**
```python
# ruamel.yaml - Preserves comments and formatting
from ruamel.yaml import YAML
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
```

### ❌ Missing: Plugin/Datapack Add/Remove Auto-Detection
**Current State:**
- Agent discovers plugins during scheduled scans
- **NO** immediate detection when plugin added/removed
- **NO** automatic endpoint config update when plugin list changes

**Production Reality:**
When admin adds new plugin manually:
1. Downloads `NewPlugin.jar` via SFTP
2. Drops into `/home/amp/.ampdata/instances/SMP201/Minecraft/plugins/`
3. Restarts server via AMP
4. **Agent doesn't know until next scan (5 minutes later)**
5. **Endpoint configs NOT updated**
6. **Config rules NOT applied**

**Required:**
- File system watcher (inotify on Linux)
- Immediate re-scan on plugin folder changes
- Auto-queue config deployment for new plugins
- Auto-cleanup config rules for removed plugins

### ❌ Missing: Config File Backup/Rollback
**Current State:**
- NO backup before modifying configs
- NO rollback capability if change breaks server

**Production Reality:**
- Config change could break server startup
- Need point-in-time restore
- Need to track what changed and when

**Required:**
```sql
CREATE TABLE endpoint_config_backups (
    backup_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(16) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    config_file_path VARCHAR(1024) NOT NULL,
    file_content LONGTEXT NOT NULL,  -- Full file snapshot
    file_hash VARCHAR(64),
    backed_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    backed_up_by VARCHAR(128),
    backup_reason ENUM('before_change', 'scheduled', 'manual', 'pre_migration') NOT NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    INDEX idx_instance (instance_id),
    INDEX idx_backed_up_at (backed_up_at)
);
```

## 📂 AMP Instance Folder Structure

### Known Structure:
```
/home/amp/.ampdata/instances/{FOLDER_NAME}/
├── Instance.conf                    # AMP instance metadata (NOT TRACKED!)
├── Minecraft/
│   ├── server.jar
│   ├── server.properties            # ✅ TRACKED (instance_server_properties)
│   ├── bukkit.yml                   # ✅ TRACKED (instance_platform_configs)
│   ├── spigot.yml                   # ✅ TRACKED (instance_platform_configs)
│   ├── config/
│   │   ├── paper-global.yml         # ✅ TRACKED (instance_platform_configs)
│   │   └── paper-world-defaults.yml # ✅ TRACKED (instance_platform_configs)
│   ├── plugins/
│   │   ├── PluginA.jar              # ✅ TRACKED (instance_plugins)
│   │   ├── PluginB.jar              # ✅ TRACKED (instance_plugins)
│   │   └── PluginA/
│   │       ├── config.yml           # ❌ NOT TRACKED!!!
│   │       ├── messages.yml         # ❌ NOT TRACKED!!!
│   │       └── data.yml             # ❌ NOT TRACKED!!!
│   └── world/
│       ├── datapacks/
│       │   └── datapack1.zip        # ✅ TRACKED (instance_datapacks)
│       └── world/
│           └── datapacks/           # ✅ TRACKED (per-world)
└── logs/
```

### Instance.conf Format (AMP):
```ini
[Instance]
InstanceID=a1b2c3d4-e5f6-7890-abcd-ef1234567890
FriendlyName=SMP Season 2
Module=Minecraft
ApplicationPort=25565
ApplicationIPBinding=0.0.0.0
```

**CRITICAL:** We need to parse `Instance.conf` to get:
- `InstanceID` → Store as `amp_instance_id`
- `FriendlyName` → Verify matches `instance_name`
- `ApplicationPort` → Verify matches `port`

## 🔧 Default Config File Locations (Common Patterns)

### Server Core Configs:
```
Minecraft/server.properties          → Always present
Minecraft/bukkit.yml                 → Bukkit/Spigot/Paper
Minecraft/spigot.yml                 → Spigot/Paper
Minecraft/config/paper-global.yml    → Paper 1.19+
Minecraft/config/paper-world-defaults.yml → Paper 1.19+
Minecraft/purpur.yml                 → Purpur
```

### Plugin Config Patterns:
```
# Pattern 1: Single config.yml
plugins/PluginName/config.yml

# Pattern 2: Multiple YAML files
plugins/PluginName/config.yml
plugins/PluginName/messages.yml
plugins/PluginName/lang/en_US.yml

# Pattern 3: Nested configs
plugins/PluginName/settings/general.yml
plugins/PluginName/settings/database.yml
plugins/PluginName/data/storage.yml

# Pattern 4: JSON configs
plugins/PluginName/config.json

# Pattern 5: Properties
plugins/PluginName/plugin.properties
```

### Example - EssentialsX:
```
plugins/Essentials/config.yml        # Main config
plugins/Essentials/kits.yml          # Kits configuration
plugins/Essentials/worth.yml         # Item values
plugins/Essentials/custom_items.yml  # Custom items
plugins/Essentials/commands.yml      # Command config
```

### Example - LuckPerms:
```
plugins/LuckPerms/config.yml         # Main config
plugins/LuckPerms/lang/en.yml        # Language file
```

### Example - WorldGuard:
```
plugins/WorldGuard/config.yml        # Main config
plugins/WorldGuard/worlds/world/config.yml       # Per-world
plugins/WorldGuard/worlds/world_nether/config.yml # Per-world
```

## 🎛️ Config Discovery Strategy

### Step 1: Discover Instance Folder
```python
def _discover_instance_folders(self):
    """Scan AMP instances directory and map instance_id to folder names"""
    amp_base = "/home/amp/.ampdata/instances"
    
    for folder_name in os.listdir(amp_base):
        folder_path = os.path.join(amp_base, folder_name)
        
        # Read Instance.conf
        instance_conf = os.path.join(folder_path, "Instance.conf")
        if os.path.exists(instance_conf):
            config = self._parse_amp_instance_conf(instance_conf)
            
            # Map to database
            self._update_instance_paths(
                instance_id=self._extract_instance_id(folder_name, config),
                folder_name=folder_name,
                base_path=folder_path,
                amp_instance_id=config.get('InstanceID')
            )
```

### Step 2: Discover Plugin Config Files
```python
def _discover_plugin_configs(self, instance_id, plugin_id):
    """Find all config files for a plugin in an instance"""
    instance = self._get_instance_info(instance_id)
    plugin_folder = os.path.join(
        instance['instance_base_path'],
        'Minecraft/plugins',
        plugin_id
    )
    
    if not os.path.exists(plugin_folder):
        return []
    
    config_files = []
    for root, dirs, files in os.walk(plugin_folder):
        for file in files:
            if file.endswith(('.yml', '.yaml', '.json', '.toml', '.properties')):
                rel_path = os.path.relpath(
                    os.path.join(root, file),
                    instance['instance_base_path']
                )
                config_files.append({
                    'relative_path': rel_path,
                    'absolute_path': os.path.join(root, file),
                    'file_type': self._detect_config_type(file),
                    'is_main_config': file == 'config.yml' or file == 'config.yaml'
                })
    
    return config_files
```

### Step 3: Track Config Files
```python
def _register_config_file(self, instance_id, plugin_id, file_info):
    """Register discovered config file in database"""
    file_hash = self._calculate_file_hash(file_info['absolute_path'])
    file_mtime = os.path.getmtime(file_info['absolute_path'])
    
    self.db.execute("""
        INSERT INTO endpoint_config_files 
        (instance_id, plugin_id, config_file_type, relative_path, absolute_path, 
         file_hash, last_modified_at, is_main_config)
        VALUES (%s, %s, %s, %s, %s, %s, FROM_UNIXTIME(%s), %s)
        ON DUPLICATE KEY UPDATE
            file_hash = VALUES(file_hash),
            last_modified_at = VALUES(last_modified_at),
            last_scanned_at = CURRENT_TIMESTAMP
    """, (instance_id, plugin_id, file_info['file_type'], 
          file_info['relative_path'], file_info['absolute_path'],
          file_hash, file_mtime, file_info['is_main_config']))
```

## 🔄 Handling Plugin/Datapack Changes

### Scenario: Admin Adds New Plugin

**Current Behavior:**
1. Admin downloads `NewPlugin.jar` to server
2. Admin moves to `plugins/` folder
3. Admin restarts server
4. **Agent discovers on next scheduled scan (up to 5 minutes later)**

**Improved Behavior:**
1. Admin downloads `NewPlugin.jar` to server
2. Admin moves to `plugins/` folder
3. **File watcher detects new file immediately**
4. **Agent triggers immediate plugin scan**
5. **Agent discovers `NewPlugin.jar`**
6. **Agent scans `plugins/NewPlugin/` for config files**
7. **Agent checks config_rules for NewPlugin defaults**
8. **Agent applies universal/server/meta-tag configs**
9. Admin restarts server
10. Plugin runs with correct configs from first boot

### Scenario: Admin Removes Plugin

**Current Behavior:**
1. Admin deletes `OldPlugin.jar`
2. Admin restarts server
3. **Agent discovers absence on next scan**
4. **Orphaned config files remain in `plugins/OldPlugin/`**
5. **Database still shows plugin as installed**

**Improved Behavior:**
1. Admin deletes `OldPlugin.jar`
2. **File watcher detects deletion**
3. **Agent triggers immediate plugin scan**
4. **Agent marks plugin as removed in database**
5. **Agent logs removal in plugin_event_history**
6. **Agent optionally backs up config files before deletion**
7. **Agent optionally removes `plugins/OldPlugin/` folder**
8. Admin restarts server

### Implementation: File System Watcher
```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class PluginFolderWatcher(FileSystemEventHandler):
    def __init__(self, agent):
        self.agent = agent
    
    def on_created(self, event):
        if event.src_path.endswith('.jar'):
            instance_id = self._extract_instance_id(event.src_path)
            self.agent.trigger_plugin_scan(instance_id)
    
    def on_deleted(self, event):
        if event.src_path.endswith('.jar'):
            instance_id = self._extract_instance_id(event.src_path)
            self.agent.trigger_plugin_scan(instance_id)
    
    def on_modified(self, event):
        if event.src_path.endswith('.jar'):
            instance_id = self._extract_instance_id(event.src_path)
            self.agent.trigger_plugin_scan(instance_id)

# In agent initialization:
def _start_file_watchers(self):
    """Start file system watchers for all instances"""
    observer = Observer()
    
    for instance in self._get_all_instances():
        plugins_path = os.path.join(
            instance['instance_base_path'],
            'Minecraft/plugins'
        )
        observer.schedule(
            PluginFolderWatcher(self),
            plugins_path,
            recursive=False
        )
    
    observer.start()
    self.observer = observer
```

## 📝 YAML Modification Best Practices

### Preserve Formatting:
```python
from ruamel.yaml import YAML

def modify_config_value(self, file_path, key_path, new_value):
    """
    Modify YAML config preserving comments and formatting
    
    Args:
        file_path: Path to YAML file
        key_path: Dot notation (e.g., 'settings.economy.starting-balance')
        new_value: New value to set
    """
    # Backup first
    self._backup_config_file(file_path, 'before_change')
    
    # Load with formatting preservation
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    
    with open(file_path, 'r') as f:
        config = yaml.load(f)
    
    # Navigate nested keys
    keys = key_path.split('.')
    current = config
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set value
    current[keys[-1]] = new_value
    
    # Write back
    with open(file_path, 'w') as f:
        yaml.dump(config, f)
    
    # Verify change
    new_hash = self._calculate_file_hash(file_path)
    self._log_config_change(file_path, key_path, new_value, new_hash)
```

### Handle Edge Cases:
```python
def safe_config_modify(self, file_path, key_path, new_value):
    """Modify config with comprehensive error handling"""
    try:
        # 1. Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        # 2. Backup
        backup_id = self._backup_config_file(file_path, 'before_change')
        
        # 3. Modify
        self.modify_config_value(file_path, key_path, new_value)
        
        # 4. Validate YAML syntax
        if not self._validate_yaml_syntax(file_path):
            # Rollback
            self._restore_config_backup(backup_id)
            raise ValueError(f"Invalid YAML after modification: {file_path}")
        
        # 5. Log success
        self._log_config_change_success(file_path, key_path, new_value)
        
        return True
        
    except Exception as e:
        # Rollback if we have backup
        if 'backup_id' in locals():
            self._restore_config_backup(backup_id)
        
        # Log failure
        self._log_config_change_failure(file_path, key_path, new_value, str(e))
        
        raise
```

## 🎯 Summary of Required Changes

### Database Schema:
1. ✅ Add `instance_folder_name`, `instance_base_path`, `amp_instance_id` to `instances` table
2. ✅ Create `endpoint_config_files` table
3. ✅ Create `endpoint_config_backups` table
4. ✅ Create `endpoint_config_change_history` table

### Agent Code:
1. ✅ Implement `_discover_instance_folders()` - Parse Instance.conf
2. ✅ Implement `_discover_plugin_configs()` - Find all config files
3. ✅ Implement `_register_config_file()` - Track in database
4. ✅ Implement YAML modification with ruamel.yaml
5. ✅ Implement config file backup/restore
6. ✅ Implement file system watchers (watchdog)
7. ✅ Implement immediate plugin scan on file changes

### API Endpoints:
1. ✅ GET `/api/instances/{id}/config-files` - List all config files
2. ✅ GET `/api/instances/{id}/plugins/{plugin}/configs` - Plugin configs
3. ✅ POST `/api/instances/{id}/plugins/{plugin}/config` - Modify config
4. ✅ POST `/api/config/rollback/{backup_id}` - Restore backup

### Future Considerations:
- Config validation per plugin (schema enforcement)
- Config templates for new plugin installations
- Bulk config operations across instances
- Config diff visualization in UI
- Plugin dependency detection (if PluginA added, suggest PluginB)
