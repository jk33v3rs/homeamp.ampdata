# Production-Ready Self-Discovering Config Management System

## 🎯 Overview

This is a **fully dynamic, zero-hardcoded-assumptions** configuration management system for ArchiveSMP. It automatically discovers and tracks:

- ✅ All AMP instances (no hardcoded instance lists)
- ✅ All plugins (no hardcoded plugin names)
- ✅ All datapacks across all worlds (no hardcoded datapack lists)
- ✅ Server properties and platform configs
- ✅ User-extensible meta-tagging system
- ✅ CI/CD-integrated plugin updates (Modrinth, Hangar, GitHub)
- ✅ Datapack deployment management
- ✅ Plugin info page registry

## 📋 Key Features

### 1. **Zero Hardcoding**
- **No plugin lists**: Scans `plugins/` folder, reads JAR metadata
- **No datapack lists**: Scans all `world/datapacks/` folders
- **No instance lists**: Discovers from `/home/amp/.ampdata/instances`
- **Dynamic registries**: Everything auto-populates into database

### 2. **Meta-Tagging System** (User-Extensible)
```sql
-- Add new categories at any time:
INSERT INTO meta_tag_categories (category_name, display_name, is_multiselect) 
VALUES ('my_category', 'My Custom Category', TRUE);

-- Add new tags:
INSERT INTO meta_tags (category_id, tag_name, display_name) 
VALUES (7, 'my-tag', 'My Custom Tag');
```

**Auto-Detection**: Agent suggests tags based on:
- Plugin set (if Vault + EssentialsX → `economy-enabled`)
- Server properties (if `pvp=false` → `pvp-disabled`)
- Gamemode (if `creative` → `creative` tag)
- Plugin count (0-10 = `vanilla-ish`, 30+ = `heavily-modded`)

### 3. **CI/CD Plugin Updates**
Supports automatic update checking via:
- **Modrinth API**: Project versions + download URLs
- **Hangar API**: Paper plugin releases
- **GitHub Releases**: Latest release detection
- **Webhook events**: React to new releases instantly

Update strategies:
- `manual`: User approval required
- `notify_only`: Log new versions, don't deploy
- `auto_stable`: Auto-deploy stable releases
- `auto_latest`: Auto-deploy all releases (including pre-releases)

### 4. **Datapack Deployment**
- Scan all worlds for datapacks
- Track enabled/disabled state
- Load order preservation
- Deployment queue for bulk updates

### 5. **Full Audit Trail**
Every action logged:
- `config_change_history`: All config modifications
- `plugin_installation_history`: Install/update/remove events
- `discovery_runs`: What was found during scans
- `meta_tag_history`: Tag changes over time

## 🗄️ Database Schema

### New Tables (58 tables total)

**Core Discovery**:
- `plugins` - Global plugin registry with CI/CD metadata
- `instance_plugins` - Per-instance plugin installations
- `datapacks` - Global datapack catalog
- `instance_datapacks` - Per-instance/world datapack tracking
- `discovery_runs` - Discovery scan history
- `discovery_items` - Detailed scan results

**Meta-Tagging**:
- `meta_tag_categories` - User-defined tag categories
- `meta_tags` - Extensible tag definitions
- `instance_meta_tags` - Tag assignments with confidence scores
- `meta_tag_history` - Tag change audit trail

**Update Management**:
- `plugin_update_queue` - Scheduled plugin updates
- `datapack_deployment_queue` - Datapack deployment tasks
- `cicd_webhook_events` - Incoming webhook events from CI/CD

**Config Tracking**:
- `instance_server_properties` - server.properties snapshots
- `instance_platform_configs` - paper.yml, spigot.yml, etc.

**Views**:
- `v_plugin_status` - Active plugins with update status
- `v_instance_summary` - Instances with tags and counts
- `v_pending_updates` - Available updates

## 📁 Agent Architecture

### Main Agent (`production_endpoint_agent.py`)
- Auto-discovery orchestration
- Feature flags and intervals
- Main event loop

### Database Methods (`agent_database_methods.py`)
- Plugin/datapack registration
- Instance tracking
- Auto-tagging logic
- Discovery run tracking

### Update Methods (`agent_update_methods.py`)
- CI/CD API integration (Modrinth, Hangar, GitHub)
- Update queue processing
- Plugin deployment
- Webhook event handling

## 🚀 Deployment Steps

### 1. Deploy New Database Schema

```bash
# On Hetzner production server
cd /opt/archivesmp-config-manager

# Apply dynamic metadata schema
sudo mariadb -u root -p asmp_config < scripts/create_dynamic_metadata_system.sql

# Verify tables created
sudo mariadb -u root -p asmp_config -e "SHOW TABLES LIKE '%plugin%'; SHOW TABLES LIKE '%datapack%'; SHOW TABLES LIKE '%meta_%';"
```

### 2. Seed Meta Tags (Initial Categories)

```bash
# Apply initial tag categories and system tags
sudo mariadb -u root -p asmp_config < scripts/seed_meta_tags.sql

# Verify tags
sudo mariadb -u root -p asmp_config -e "SELECT * FROM meta_tag_categories; SELECT COUNT(*) FROM meta_tags;"
```

### 3. Run Initial Discovery

```bash
# Test agent in discovery mode
cd /opt/archivesmp-config-manager
sudo python3 -m src.agent.production_endpoint_agent \
    --server hetzner-xeon \
    --db-host localhost \
    --db-user root \
    --db-password <password> \
    --db-name asmp_config

# Check discovery results
sudo mariadb -u root -p asmp_config -e "
SELECT * FROM discovery_runs ORDER BY run_id DESC LIMIT 1;
SELECT item_type, COUNT(*) FROM discovery_items GROUP BY item_type;
SELECT * FROM plugins;
SELECT * FROM instance_plugins;
"
```

### 4. Configure Agent Service

```ini
# /etc/systemd/system/archivesmp-agent.service
[Unit]
Description=ArchiveSMP Config Management Agent
After=network.target mariadb.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/archivesmp-config-manager
Environment="PYTHONPATH=/opt/archivesmp-config-manager"
ExecStart=/usr/bin/python3 -m src.agent.production_endpoint_agent \
    --server hetzner-xeon \
    --db-host localhost \
    --db-user root \
    --db-password <password> \
    --db-name asmp_config

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-agent.service
sudo systemctl start archivesmp-agent.service
sudo systemctl status archivesmp-agent.service

# View logs
sudo journalctl -u archivesmp-agent.service -f
```

## 🔧 Configuration Options

### Agent Config File (`/etc/archivesmp/agent.yaml`)

```yaml
server:
  name: hetzner-xeon
  amp_base_dir: /home/amp/.ampdata/instances

database:
  host: localhost
  port: 3306
  user: root
  password: <password>
  database: asmp_config

features:
  enable_auto_discovery: true
  enable_plugin_updates: true
  enable_datapack_deployment: true
  enable_drift_detection: true
  enable_meta_tagging: true

intervals:
  full_scan_interval: 300        # 5 minutes
  update_check_interval: 600     # 10 minutes
  queue_process_interval: 60     # 1 minute

logging:
  level: INFO
  file: /var/log/archivesmp/agent-hetzner-xeon.log
```

## 📊 Usage Examples

### View All Discovered Plugins

```sql
SELECT 
    p.display_name,
    p.platform,
    p.current_stable_version,
    p.latest_version,
    COUNT(ip.instance_id) AS instances_installed,
    p.has_cicd,
    p.auto_update_enabled
FROM plugins p
LEFT JOIN instance_plugins ip ON p.plugin_id = ip.plugin_id
GROUP BY p.plugin_id
ORDER BY instances_installed DESC;
```

### Check Pending Updates

```sql
SELECT * FROM v_pending_updates;
```

### View Instance Tags

```sql
SELECT 
    i.instance_id,
    i.display_name,
    GROUP_CONCAT(mt.display_name ORDER BY mtc.display_order SEPARATOR ', ') AS tags
FROM instances i
LEFT JOIN instance_meta_tags imt ON i.instance_id = imt.instance_id
LEFT JOIN meta_tags mt ON imt.tag_id = mt.tag_id
LEFT JOIN meta_tag_categories mtc ON mt.category_id = mtc.category_id
GROUP BY i.instance_id;
```

### Add Custom Tag Category

```sql
-- Add "performance" category
INSERT INTO meta_tag_categories (category_name, display_name, is_multiselect, display_order)
VALUES ('performance', 'Performance Profile', FALSE, 10);

-- Add tags to category
INSERT INTO meta_tags (category_id, tag_name, display_name, description)
SELECT category_id, 'high-performance', 'High Performance', 'Optimized for max TPS'
FROM meta_tag_categories WHERE category_name = 'performance';

INSERT INTO meta_tags (category_id, tag_name, display_name, description)
SELECT category_id, 'low-latency', 'Low Latency', 'Optimized for ping'
FROM meta_tag_categories WHERE category_name = 'performance';
```

### Enable Auto-Updates for Plugin

```sql
-- Enable auto-update for LuckPerms (stable only)
UPDATE plugins
SET auto_update_enabled = TRUE,
    update_strategy = 'auto_stable'
WHERE plugin_id = 'luckperms';

-- Enable for EssentialsX (all releases)
UPDATE plugins
SET auto_update_enabled = TRUE,
    update_strategy = 'auto_latest'
WHERE plugin_id = 'essentialsx';
```

### Manually Queue Plugin Update

```sql
-- Queue update for specific instances
INSERT INTO plugin_update_queue (
    plugin_id, target_instances, to_version, download_url, 
    priority, created_by
) VALUES (
    'worldedit',
    '["BENT01", "BENT02", "BENT03"]',
    '7.3.0',
    'https://github.com/EngineHub/WorldEdit/releases/download/7.3.0/worldedit-bukkit-7.3.0.jar',
    8,
    'admin'
);
```

## 🔍 Monitoring

### Agent Health Check

```sql
-- Check last discovery run
SELECT * FROM discovery_runs 
ORDER BY started_at DESC LIMIT 1;

-- Check recent discoveries
SELECT 
    item_type,
    action,
    COUNT(*) AS count
FROM discovery_items 
WHERE run_id = (SELECT MAX(run_id) FROM discovery_runs)
GROUP BY item_type, action;
```

### Update Queue Status

```sql
SELECT 
    status,
    COUNT(*) AS count,
    MIN(created_at) AS oldest,
    MAX(created_at) AS newest
FROM plugin_update_queue
GROUP BY status;
```

### Webhook Event Status

```sql
SELECT 
    provider,
    status,
    COUNT(*) AS count
FROM cicd_webhook_events
WHERE received_at > DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY provider, status;
```

## 🎛️ Admin Commands

### Force Full Discovery Scan

```bash
# Via systemd
sudo systemctl restart archivesmp-agent.service

# Or send SIGUSR1 signal
sudo kill -USR1 $(pidof python3 archivesmp-agent)
```

### Clear Discovery Cache

```sql
-- Remove old discovery runs (keep last 30 days)
DELETE FROM discovery_runs 
WHERE started_at < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

### Reset Auto-Tag Confidence

```sql
-- Re-run auto-tagging for all instances
UPDATE instance_meta_tags
SET confidence_score = 0
WHERE is_auto_detected = TRUE;

-- Agent will recalculate on next scan
```

## 🐛 Troubleshooting

### Agent Not Discovering Instances

```bash
# Check AMP base directory
ls -la /home/amp/.ampdata/instances

# Check agent logs
sudo journalctl -u archivesmp-agent.service --since "10 minutes ago"

# Verify database connectivity
sudo mariadb -u root -p asmp_config -e "SELECT 1;"
```

### Plugin Updates Not Applying

```sql
-- Check queue status
SELECT * FROM plugin_update_queue WHERE status = 'failed';

-- Check error messages
SELECT id, plugin_id, error_message, deployment_log
FROM plugin_update_queue
WHERE status = 'failed'
ORDER BY created_at DESC;
```

### Tags Not Auto-Applying

```sql
-- Check if tags exist
SELECT * FROM meta_tags WHERE tag_name = 'survival';

-- Check agent auto-tag logs
-- Look for lines like: "🏷️  Auto-tagged BENT01 with 'survival' (confidence: 0.95)"
```

## 📈 Future Enhancements

- [ ] ML-based plugin compatibility detection
- [ ] Automated config migration on plugin updates
- [ ] Datapack conflict detection
- [ ] Performance metrics integration
- [ ] Slack/Discord notifications for updates
- [ ] Web UI for queue management
- [ ] Instance group deployments

## 📝 Notes

- **No hardcoded plugin names**: Agent discovers everything dynamically
- **No hardcoded instance names**: Scans `/home/amp/.ampdata/instances`
- **User-extensible tags**: Add categories/tags anytime via SQL
- **CI/CD webhooks**: POST to `/api/webhooks/cicd` for instant updates
- **Plugin info registry**: Tracks docs URLs, changelogs, support links

