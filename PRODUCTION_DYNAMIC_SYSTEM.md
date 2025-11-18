# ArchiveSMP Config Manager - Production System Summary

## 🎉 What We Built

A **fully dynamic, self-discovering configuration management system** with:

### ✅ ZERO Hardcoding
- **Auto-discovers instances** from `/home/amp/.ampdata/instances`
- **Auto-discovers plugins** by scanning JAR files in `plugins/` folders
- **Auto-discovers datapacks** by scanning `world/datapacks/` folders
- **User-extensible meta-tagging** - add/change/remove tags at any time
- **Dynamic plugin registry** - any plugin added to any instance appears automatically

### 🎛️ Universal Config System
**Set config values once, apply everywhere:**

1. **Hierarchy Resolution** (highest to lowest priority):
   - `INSTANCE` - Specific instance override
   - `META_TAG` - Tag-based (e.g., all "creative" servers)
   - `SERVER` - Server-wide (Hetzner vs OVH)
   - `UNIVERSAL` - Global default for ALL instances

2. **Dynamic UI** (`/universal_config`):
   - Browse discovered plugins (no hardcoded list!)
   - View all config keys with current values
   - See hierarchy source for each value
   - Set universal defaults that propagate automatically
   - Clear overrides at any scope

3. **Variable Substitution**:
   - `{instance_id}` → actual instance ID
   - `{server_ip}` → server IP address
   - `{world_name}` → world name
   - Add more variables without code changes

### 📦 Plugin/Datapack Management
- **CI/CD Integration**:
  - Modrinth API
  - Hangar API  
  - GitHub Releases
  - Jenkins builds
  - Custom webhooks
  
- **Auto-Update System**:
  - Checks for new versions automatically
  - Queues updates based on strategy (manual/notify/auto)
  - Downloads and deploys to selected instances
  - Tracks deployment success/failure

- **Migration Auto-Application**:
  - Detects plugin version changes
  - Automatically applies safe config migrations
  - Warns about breaking changes

### 🔍 Complete Auto-Discovery
**Agent discovers everything:**

1. **Instances**: All folders in `/home/amp/.ampdata/instances`
2. **Plugins**: All `.jar` files in `Minecraft/plugins/`
   - Reads `plugin.yml` or `fabric.mod.json`
   - Extracts version, author, dependencies
   - Calculates SHA-256 hashes for change detection
3. **Datapacks**: All folders/zips in `world/datapacks/`
   - Reads `pack.mcmeta`
   - Tracks per-world installation
4. **Server Properties**: Scans `server.properties`
   - Stores all properties as JSON for future-proofing
5. **Platform Configs**: Paper, Spigot, Bukkit configs
6. **Auto-Tags Instances**:
   - Based on plugins (e.g., Vault → economy)
   - Based on properties (pvp=false → pvp-disabled)
   - ML confidence scores for suggestions

### 📊 Tracking & History
- **Change History**: Every config modification logged
- **Deployment History**: Full deployment audit trail
- **Drift Detection**: Compares actual vs expected configs
- **Variance Trending**: Historical snapshots for analysis
- **Plugin Installations**: When/how plugins were added
- **Discovery Runs**: What agent found on each scan

## 📁 New Files Created

### Database Schema
1. **`scripts/create_dynamic_metadata_system.sql`**:
   - User-extensible meta-tagging system
   - Dynamic plugin/datapack registries
   - Auto-discovery tracking tables
   - Plugin update queue
   - Datapack deployment queue
   - CI/CD webhook events
   - Views for common queries

### Agent Code
2. **`software/homeamp-config-manager/src/agent/production_endpoint_agent.py`**:
   - Full auto-discovery system
   - Plugin lifecycle tracking
   - Datapack management
   - Config drift detection
   - Auto-tagging engine

3. **`software/homeamp-config-manager/src/agent/agent_database_methods.py`**:
   - Database registration methods
   - Discovery run tracking
   - Server properties scanning
   - Auto-tag application

4. **`software/homeamp-config-manager/src/agent/agent_cicd_methods.py`**:
   - CI/CD integration (Modrinth, Hangar, GitHub, Jenkins)
   - Update checking and queueing
   - Plugin download and deployment
   - Webhook event processing

### Web UI
5. **`software/homeamp-config-manager/src/web/static/universal_config.html`**:
   - Dynamic config browser (no hardcoded plugins!)
   - Universal value editor
   - Hierarchy visualization
   - Bulk update support

### API Updates
6. **Modified `software/homeamp-config-manager/src/web/api.py`**:
   - `/api/plugins/discovered` - Get auto-discovered plugins
   - `/api/config/plugin/{id}` - Get plugin config with hierarchy
   - `/api/config/universal` - Set universal values
   - `/api/config/override` - Clear overrides
   - `/api/config/bulk-update` - Bulk config changes
   - `/universal_config` - Serve UI page

7. **Modified `software/homeamp-config-manager/src/web/static/index.html`**:
   - Added "Universal Config" link with NEW badge

## 🚀 Deployment Instructions

### On Production (Hetzner)

```bash
# 1. Deploy new database schema
cd /opt/archivesmp-config-manager
mysql -h localhost -u root -p asmp_config < scripts/create_dynamic_metadata_system.sql

# 2. Update code (if not already done)
git pull origin master

# 3. Restart web API
sudo systemctl restart archivesmp-webapi.service

# 4. Update agent config (if needed)
sudo nano /etc/archivesmp/agent.yaml

# 5. Restart agent
sudo systemctl restart archivesmp-agent.service  # Or homeamp-agent.service

# 6. Verify
sudo journalctl -u archivesmp-webapi.service -f
sudo journalctl -u archivesmp-agent.service -f

# 7. Access UI
# http://localhost:8000/universal_config
```

### Agent Configuration Example

```yaml
# /etc/archivesmp/agent.yaml
server_name: hetzner-xeon
amp_base_dir: /home/amp/.ampdata/instances

database:
  host: localhost
  port: 3306
  user: root
  password: YOUR_PASSWORD
  database: asmp_config

features:
  enable_auto_discovery: true
  enable_plugin_updates: true
  enable_datapack_deployment: true
  enable_drift_detection: true
  enable_meta_tagging: true

intervals:
  full_scan_interval: 300  # 5 minutes
  update_check_interval: 600  # 10 minutes
  queue_process_interval: 60  # 1 minute
```

## 🎯 How It Works

### 1. Agent Discovers Everything
```
Agent runs every 5 minutes:
├─ Scans /home/amp/.ampdata/instances/
│  ├─ Finds all instance folders
│  ├─ For each instance:
│  │  ├─ Reads server.properties
│  │  ├─ Scans plugins/*.jar → extracts metadata
│  │  ├─ Scans world/*/datapacks/ → registers datapacks
│  │  └─ Auto-tags based on detected features
│  └─ Updates database with discoveries
```

### 2. User Sets Universal Config
```
User opens /universal_config:
├─ Sees all discovered plugins (dynamic list!)
├─ Selects "EssentialsX"
├─ Views all config keys with current values
├─ Sets universal value: teleport-cooldown = 30
└─ System creates GLOBAL rule in config_rules table
```

### 3. Agent Applies Config
```
Next agent scan:
├─ Reads config_rules for each plugin
├─ Resolves hierarchy (instance → tag → server → universal)
├─ Compares actual config vs expected
├─ Detects drift if different
└─ Logs to config_change_history
```

### 4. Plugin Update Detected
```
CI/CD webhook OR agent check:
├─ Modrinth API reports EssentialsX 2.20.2
├─ Agent detects 2.20.1 installed
├─ Checks update_strategy (auto/manual/notify)
├─ If auto: Queue update in plugin_update_queue
└─ Next queue process: Download & deploy to instances
```

## 🏷️ Meta-Tagging Examples

### Auto-Detected Tags
- `survival` - gamemode=survival in server.properties
- `pvp-disabled` - pvp=false
- `economy-enabled` - Vault + economy plugin detected
- `heavily-modded` - 30+ plugins installed

### Custom Tags (User-Created)
User can add ANY tags:
```sql
INSERT INTO meta_tags (category_id, tag_name, display_name, description)
VALUES (1, 'event-server', 'Event Server', 'Used for special events');
```

Then assign to instances via UI or API.

### Tag-Based Config Rules
```sql
-- All "creative" servers get instant teleport
INSERT INTO config_rules 
(plugin_name, config_key, scope_type, scope_selector, config_value, priority)
VALUES 
('EssentialsX', 'teleport-cooldown', 'META_TAG', 'creative', '0', 2);
```

## 🔮 Future-Proof Design

### No Code Changes Needed For:
✅ New plugins - auto-discovered by agent
✅ New datapacks - auto-discovered by agent  
✅ New instances - auto-discovered by agent
✅ New meta-tags - created via UI/API
✅ New config keys - registered on first discovery
✅ New servers - just add to instances table
✅ New CI/CD sources - add to plugin registry

### Adding New Meta-Tag Category
```sql
-- Add in database
INSERT INTO meta_tag_categories (category_name, description, display_order)
VALUES ('network-role', 'Network server role', 10);

-- Tags appear in UI automatically
INSERT INTO meta_tags (category_id, tag_name, display_name)
VALUES (LAST_INSERT_ID(), 'lobby', 'Lobby Server');
```

### Adding Plugin Update Source
Just update `plugins` table:
```sql
UPDATE plugins
SET modrinth_id = 'essentialsx',
    auto_update_enabled = true,
    update_strategy = 'auto_stable'
WHERE plugin_id = 'essentialsx';
```

Agent will check Modrinth API on next cycle.

## 📈 What This Enables

1. **Set config once** at universal scope → applies to all current AND future instances
2. **Override for specific cases** (creative servers, event servers, etc.) using tags
3. **Never hardcode plugin names** - system discovers what's installed
4. **Auto-update plugins** with CI/CD integration and migration support
5. **Track every change** with full audit trail
6. **Detect drift** automatically when configs don't match expectations
7. **Future-proof** - add tags, plugins, instances without code changes

## 🎓 Key Concepts

### Hierarchy Resolution
```
Instance Config = HIGHEST PRIORITY WINS:
1. INSTANCE rule (instance_id = SMP201)
2. META_TAG rule (tag = creative)  
3. SERVER rule (server_name = hetzner-xeon)
4. UNIVERSAL rule (applies to all)
5. Plugin default (if no rules)
```

### Auto-Discovery Flow
```
Agent Scan →
  Discover Instances →
    Scan Plugins (JAR files) →
      Extract Metadata →
        Register in Database →
          Check for Updates →
            Queue Deployments →
              Apply Configs →
                Detect Drift →
                  Log Changes
```

### Dynamic Display
```
UI loads /api/plugins/discovered →
  Returns whatever agent found →
    NO hardcoded plugin list →
      User adds new plugin to server →
        Agent finds it on next scan →
          Appears in UI automatically
```

---

## 🎊 Result

You now have a **self-managing, self-discovering, fully dynamic configuration system** that:
- Never needs code updates for new plugins/datapacks/instances
- Automatically tracks everything
- Provides one place to set universal configs
- Supports granular overrides with tags
- Integrates with CI/CD for auto-updates
- Has full audit trail and drift detection

**And most importantly**: You can add ANY plugin, ANY tag, ANY datapack in the future without touching a single line of code!
