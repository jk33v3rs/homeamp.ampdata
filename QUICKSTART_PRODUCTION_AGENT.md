# 🚀 Quick Start: Deploy Production Agent

## Prerequisites
- Hetzner server with 11 AMP instances running
- MariaDB 10.6+ with `asmp_config` database
- Root SSH access
- Git repo access

## Step 1: Deploy Database Schema (5 minutes)

```bash
# SSH into Hetzner
ssh root@135.181.212.169

# Navigate to repo
cd /opt/archivesmp-config-manager

# Pull latest changes
git pull origin master

# Apply new schema
mariadb -u root -p asmp_config < scripts/create_dynamic_metadata_system.sql

# Verify tables created
mariadb -u root -p asmp_config -e "
SHOW TABLES LIKE 'meta_%';
SHOW TABLES LIKE 'plugin%';
SHOW TABLES LIKE 'datapack%';
SHOW TABLES LIKE 'discovery%';
"

# Expected output: 15 new tables
```

## Step 2: Seed Meta Tags (2 minutes)

```bash
# Apply initial tag categories (gameplay, modding, intensity, etc.)
mariadb -u root -p asmp_config < scripts/seed_meta_tags.sql

# Verify tags loaded
mariadb -u root -p asmp_config -e "
SELECT COUNT(*) AS category_count FROM meta_tag_categories;
SELECT COUNT(*) AS tag_count FROM meta_tags;
"

# Expected: 6 categories, 20+ tags
```

## Step 3: Test Agent (10 minutes)

```bash
# Run agent in foreground to test discovery
cd /opt/archivesmp-config-manager

python3 -m src.agent.production_endpoint_agent \
    --server hetzner-xeon \
    --db-host localhost \
    --db-user root \
    --db-password <PASSWORD> \
    --db-name asmp_config

# Watch for output:
# 🚀 Starting production endpoint agent for hetzner-xeon
# 📁 AMP Base Dir: /home/amp/.ampdata/instances
# 🔍 Starting full discovery scan
# 📦 Scanning instance: BENT01
# 🆕 Registered new plugin: worldedit
# ...
# ✅ Discovery complete: {'instances': 11, 'plugins': 300+, ...}

# Press Ctrl+C to stop after first scan completes
```

## Step 4: Verify Discovery Results (5 minutes)

```bash
# Check discovery run
mariadb -u root -p asmp_config -e "
SELECT 
    run_id, 
    run_type, 
    status,
    instances_discovered,
    plugins_discovered,
    datapacks_discovered,
    started_at,
    completed_at
FROM discovery_runs 
ORDER BY run_id DESC LIMIT 1;
"

# Check discovered plugins
mariadb -u root -p asmp_config -e "
SELECT 
    plugin_id,
    display_name,
    platform,
    current_stable_version,
    author
FROM plugins 
ORDER BY display_name 
LIMIT 20;
"

# Check instance plugins
mariadb -u root -p asmp_config -e "
SELECT 
    instance_id,
    COUNT(*) AS plugin_count
FROM instance_plugins
GROUP BY instance_id
ORDER BY instance_id;
"

# Expected: 11 instances, each with 20-40 plugins

# Check auto-tags
mariadb -u root -p asmp_config -e "
SELECT 
    i.instance_id,
    GROUP_CONCAT(mt.display_name ORDER BY mtc.display_order SEPARATOR ', ') AS tags
FROM instances i
LEFT JOIN instance_meta_tags imt ON i.instance_id = imt.instance_id
LEFT JOIN meta_tags mt ON imt.tag_id = mt.tag_id
LEFT JOIN meta_tag_categories mtc ON mt.category_id = mtc.category_id
GROUP BY i.instance_id;
"

# Expected: Each instance has 3-5 auto-detected tags
```

## Step 5: Install as Service (5 minutes)

```bash
# Create systemd service
cat > /etc/systemd/system/archivesmp-agent.service << 'EOF'
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
    --db-password <PASSWORD> \
    --db-name asmp_config

Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Replace <PASSWORD> with actual password
nano /etc/systemd/system/archivesmp-agent.service

# Enable and start service
systemctl daemon-reload
systemctl enable archivesmp-agent.service
systemctl start archivesmp-agent.service

# Check status
systemctl status archivesmp-agent.service

# View live logs
journalctl -u archivesmp-agent.service -f
```

## Step 6: Monitor First Production Run (5 minutes)

```bash
# Watch agent logs (wait for full scan - 5 min interval)
journalctl -u archivesmp-agent.service -f

# Look for:
# 🔍 Starting full discovery scan
# 📦 Scanning instance: BENT01
# 🆕 Plugin installed: BENT01/WorldEdit v7.3.0
# 🏷️  Auto-tagged BENT01 with 'survival' (confidence: 0.95)
# ✅ Discovery complete: {...}

# In another terminal, monitor database
watch -n 5 "mariadb -u root -p<PASSWORD> asmp_config -e '
SELECT * FROM discovery_runs ORDER BY run_id DESC LIMIT 1;
SELECT item_type, action, COUNT(*) FROM discovery_items 
WHERE run_id = (SELECT MAX(run_id) FROM discovery_runs) 
GROUP BY item_type, action;
'"
```

## Step 7: Enable CI/CD Updates (Optional, 10 minutes)

```bash
# Pick a few safe plugins for auto-updates
mariadb -u root -p asmp_config << 'EOF'

-- Enable auto-update for WorldEdit (stable only)
UPDATE plugins
SET auto_update_enabled = TRUE,
    update_strategy = 'auto_stable',
    github_repo = 'EngineHub/WorldEdit'
WHERE plugin_id = 'worldedit';

-- Enable for LuckPerms
UPDATE plugins
SET auto_update_enabled = TRUE,
    update_strategy = 'auto_stable',
    modrinth_id = 'Opugpqh1'
WHERE plugin_id = 'luckperms';

-- Just notify for EssentialsX (don't auto-deploy)
UPDATE plugins
SET auto_update_enabled = TRUE,
    update_strategy = 'notify_only',
    github_repo = 'EssentialsX/Essentials'
WHERE plugin_id = 'essentialsx';

EOF

# Wait for next update check (10 min interval)
# Or restart agent to trigger immediate check
systemctl restart archivesmp-agent.service

# Check for queued updates
mariadb -u root -p asmp_config -e "
SELECT * FROM plugin_update_queue;
SELECT * FROM v_pending_updates;
"
```

## Step 8: Test Web UI (5 minutes)

```bash
# Restart web API to load new routes
systemctl restart archivesmp-webapi.service

# Check API endpoints
curl http://localhost:8000/api/plugins
curl http://localhost:8000/api/instances/BENT01/plugins
curl http://localhost:8000/api/tags/categories
curl http://localhost:8000/api/discovery/runs/latest

# Visit web UI
# http://archivesmp.site:8000/history (already deployed)
# http://archivesmp.site:8000/migrations (already deployed)
```

## Troubleshooting

### Agent Won't Start

```bash
# Check Python path
which python3
python3 --version  # Should be 3.9+

# Check dependencies
pip3 list | grep -E 'PyYAML|requests|mysql'

# Check AMP directory
ls -la /home/amp/.ampdata/instances

# Check database connection
mariadb -u root -p asmp_config -e "SELECT 1;"
```

### No Instances Discovered

```bash
# Verify AMP instances exist
ls -la /home/amp/.ampdata/instances

# Check each instance has Minecraft folder
for dir in /home/amp/.ampdata/instances/*/; do
    echo -n "$dir: "
    [ -d "$dir/Minecraft" ] && echo "✓ OK" || echo "✗ MISSING Minecraft/"
done

# Check agent base dir config
journalctl -u archivesmp-agent.service | grep "AMP Base Dir"
```

### Plugins Not Discovered

```bash
# Check plugins folder exists
ls -la /home/amp/.ampdata/instances/BENT01/Minecraft/plugins

# Check JAR files
ls -la /home/amp/.ampdata/instances/BENT01/Minecraft/plugins/*.jar | wc -l

# Check agent logs for errors
journalctl -u archivesmp-agent.service | grep -E "ERROR|Failed"
```

### Tags Not Applied

```bash
# Check if tags exist in database
mariadb -u root -p asmp_config -e "SELECT * FROM meta_tags LIMIT 10;"

# Check auto-tag logic
journalctl -u archivesmp-agent.service | grep "Auto-tagged"

# Manually apply tag to test
mariadb -u root -p asmp_config << 'EOF'
INSERT INTO instance_meta_tags (instance_id, tag_id, applied_by)
SELECT 'BENT01', tag_id, 'manual'
FROM meta_tags WHERE tag_name = 'survival';
EOF

mariadb -u root -p asmp_config -e "SELECT * FROM instance_meta_tags WHERE instance_id = 'BENT01';"
```

## Success Criteria

After deployment, you should have:

- ✅ 11 instances in `instances` table
- ✅ 200+ plugins in `plugins` table
- ✅ 200+ entries in `instance_plugins` table
- ✅ 20+ tags in `meta_tags` table
- ✅ 50+ tag assignments in `instance_meta_tags` table
- ✅ 1+ discovery runs in `discovery_runs` table (status = 'completed')
- ✅ Agent service running (`systemctl status archivesmp-agent.service` = active)
- ✅ Agent logging to journal (`journalctl -u archivesmp-agent.service` shows activity)

## Next Steps

1. **Monitor for 24 hours** - Ensure agent runs smoothly
2. **Enable more auto-updates** - Add Modrinth IDs for plugins
3. **Add custom tags** - Create your own tag categories
4. **Build UI pages** - Plugin registry browser, tag manager
5. **Deploy to OVH** - Second agent pointing to same database

## Support

- **Logs**: `journalctl -u archivesmp-agent.service -f`
- **Database**: `mariadb -u root -p asmp_config`
- **Config**: `/etc/systemd/system/archivesmp-agent.service`
- **Documentation**: `PRODUCTION_AGENT_GUIDE.md`

