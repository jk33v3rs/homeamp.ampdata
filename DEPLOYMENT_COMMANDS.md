# DEPLOYMENT COMMANDS - Option C Implementation

**Date**: 2025-11-18  
**Target Server**: Hetzner (archivesmp.site, 135.181.212.169)  
**Status**: Ready to deploy

---

## ⚠️ IMPORTANT: Run These On Production Server

These commands should be run **on the Hetzner server** via SSH, not on your local Windows PC.

---

## Step 1: Upload Files to Production

From your Windows PC, upload the new/modified files:

```cmd
REM Upload SQL files
scp d:\homeamp.ampdata\homeamp.ampdata\scripts\add_tracking_history_tables.sql root@135.181.212.169:/tmp/
scp d:\homeamp.ampdata\homeamp.ampdata\scripts\populate_known_migrations.py root@135.181.212.169:/tmp/
scp d:\homeamp.ampdata\homeamp.ampdata\scripts\apply_config_migrations.py root@135.181.212.169:/tmp/

REM Upload updated code
scp d:\homeamp.ampdata\homeamp.ampdata\software\homeamp-config-manager\src\database\db_access.py root@135.181.212.169:/opt/archivesmp-config-manager/src/database/
scp d:\homeamp.ampdata\homeamp.ampdata\software\homeamp-config-manager\src\updaters\config_updater.py root@135.181.212.169:/opt/archivesmp-config-manager/src/updaters/
scp d:\homeamp.ampdata\homeamp.ampdata\software\homeamp-config-manager\src\web\api.py root@135.181.212.169:/opt/archivesmp-config-manager/src/web/
```

---

## Step 2: SSH to Production Server

```cmd
ssh root@135.181.212.169
```

---

## Step 3: Deploy Database Tables (5 minutes)

```bash
# Execute SQL to create 11 new tables
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' asmp_config < /tmp/add_tracking_history_tables.sql

# Verify tables were created
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' asmp_config -e "
SELECT table_name, table_rows, ROUND(data_length/1024/1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'asmp_config'
AND table_name IN (
    'config_key_migrations',
    'config_change_history',
    'deployment_history',
    'deployment_changes',
    'config_rule_history',
    'config_variance_history',
    'plugin_installation_history',
    'change_approval_requests',
    'notification_log',
    'scheduled_tasks',
    'system_health_metrics'
)
ORDER BY table_name;
"
```

**Expected Output**:
```
+-------------------------------+------------+---------+
| table_name                    | table_rows | size_mb |
+-------------------------------+------------+---------+
| change_approval_requests      |          0 |    0.02 |
| config_change_history         |          0 |    0.02 |
| config_key_migrations         |          0 |    0.02 |
| config_rule_history           |          0 |    0.02 |
| config_variance_history       |          0 |    0.02 |
| deployment_changes            |          0 |    0.02 |
| deployment_history            |          0 |    0.02 |
| notification_log              |          0 |    0.02 |
| plugin_installation_history   |          0 |    0.02 |
| scheduled_tasks               |          0 |    0.02 |
| system_health_metrics         |          0 |    0.02 |
+-------------------------------+------------+---------+
11 rows in set
```

✅ If you see all 11 tables, proceed to Step 4.

---

## Step 4: Populate Known Migrations (2 minutes)

```bash
# Install Python MySQL connector if not present
pip3 install mysql-connector-python

# Run migration population script
cd /tmp
python3 populate_known_migrations.py
```

**Expected Output**:
```
================================================================================
POPULATING KNOWN MIGRATIONS
================================================================================

✅ Connected to 135.181.212.169:3369

📋 Inserting 10 migrations...

  ✅ ExcellentEnchants: enchants.*.id → enchantments.*.identifier
     ⚠️  BREAKING CHANGE
  ✅ BentoBox: challenges.*.challenge_id → challenges.*.identifier
     ⚠️  BREAKING CHANGE
  ✅ HandsOffMyBook: hotmb.protect → handsoffmybook.protect
     ⚠️  BREAKING CHANGE
  ✅ ResurrectionChest: expiry.timer → expiry.duration_seconds
     ⚠️  BREAKING CHANGE
  ✅ JobListings: storage.type → database.enabled
     ⚠️  BREAKING CHANGE
  ✅ LevelledMobs: spawn-conditions.*.world → spawn-conditions.*.worlds
  ✅ EliteMobs: ranks.*.min_level → ranks.*.minimum_level
  ✅ Pl3xMap: settings.zoom.default → settings.default-zoom
  ✅ SimpleVoiceChat: port → voice_chat.port
     ⚠️  BREAKING CHANGE
  ✅ DiscordSRV: Experiment_WebhookChatMessageDelivery → UseWebhooksForChat

================================================================================
✅ Inserted: 10
⏭️  Skipped:  0
📊 Total:    10
================================================================================

📈 MIGRATION SUMMARY BY TYPE:

Type            Total  Breaking
----------------------------------------
rename              6         4
move                2         1
type_change         1         1
remove              1         1

✅ Migration data populated successfully
```

✅ Migrations loaded!

---

## Step 5: Restart Web API Service (1 minute)

```bash
# Restart the web API to load new code
systemctl restart archivesmp-webapi.service

# Check status
systemctl status archivesmp-webapi.service

# Check logs for startup errors
journalctl -u archivesmp-webapi.service -n 50 --no-pager
```

**Expected Output**:
```
● archivesmp-webapi.service - ArchiveSMP Config Manager Web API
   Loaded: loaded (/etc/systemd/system/archivesmp-webapi.service; enabled)
   Active: active (running) since Mon 2025-11-18 14:23:45 UTC; 3s ago
 Main PID: 12345
   CGroup: /system.slice/archivesmp-webapi.service
           └─12345 /usr/bin/python3 -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000

Nov 18 14:23:45 hetzner-xeon systemd[1]: Started ArchiveSMP Config Manager Web API.
Nov 18 14:23:46 hetzner-xeon python3[12345]: INFO:     Started server process [12345]
Nov 18 14:23:46 hetzner-xeon python3[12345]: INFO:     Waiting for application startup.
Nov 18 14:23:46 hetzner-xeon python3[12345]: ✓ Database connection established
Nov 18 14:23:46 hetzner-xeon python3[12345]: INFO:     Application startup complete.
Nov 18 14:23:46 hetzner-xeon python3[12345]: INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ Service running!

---

## Step 6: Test New API Endpoints (5 minutes)

```bash
# Test change history endpoint
curl -s http://localhost:8000/api/history/changes?limit=5 | jq

# Test migrations endpoint
curl -s http://localhost:8000/api/migrations/ExcellentEnchants | jq

# Test deployment history
curl -s http://localhost:8000/api/history/deployments?limit=5 | jq

# Test change statistics
curl -s http://localhost:8000/api/stats/changes | jq

# Test all migrations summary
curl -s http://localhost:8000/api/migrations | jq
```

**Expected Output for migrations**:
```json
{
  "plugin": "ExcellentEnchants",
  "migrations": [
    {
      "migration_id": 1,
      "plugin_name": "ExcellentEnchants",
      "old_key_path": "enchants.*.id",
      "new_key_path": "enchantments.*.identifier",
      "from_version": "4.x",
      "to_version": "5.0.0",
      "migration_type": "rename",
      "value_transform": null,
      "is_breaking": true,
      "is_automatic": false,
      "notes": "Enchant ID system changed in 5.0.0. Causes \"Unknown Enchantment\" errors...",
      "documentation_url": "https://github.com/nulli0n/ExcellentEnchants-spigot/wiki/Migration-Guide",
      "created_at": "2025-11-18T14:20:00",
      "created_by": "initial_population"
    }
  ],
  "total": 1,
  "breaking_count": 1,
  "automatic_count": 0
}
```

✅ All endpoints working!

---

## Step 7: Verify Database Logging (Test Run)

```bash
# Create a test config rule change via API
curl -X POST http://localhost:8000/api/rules/create \
  -H "Content-Type: application/json" \
  -d '{
    "plugin_name": "TestPlugin",
    "config_key": "test.deployment.enabled",
    "config_value": "true",
    "scope_type": "GLOBAL",
    "scope_value": "",
    "description": "Test change for Option C deployment"
  }'

# Check if it was logged to database
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' asmp_config -e "
SELECT change_id, plugin_name, config_key, old_value, new_value, changed_by, changed_at
FROM config_change_history
ORDER BY changed_at DESC
LIMIT 5;
"
```

**Expected**: You should see your test change in the database!

✅ Database logging working!

---

## Step 8: Copy Migration Script to Production (Optional)

```bash
# Copy to system scripts directory
cp /tmp/apply_config_migrations.py /opt/archivesmp-config-manager/scripts/

# Make executable
chmod +x /opt/archivesmp-config-manager/scripts/apply_config_migrations.py

# Test dry run
cd /opt/archivesmp-config-manager
python3 scripts/apply_config_migrations.py \
  --plugin ExcellentEnchants \
  --from-version 4.x \
  --to-version 5.0.0 \
  --instance BENT01 \
  --dry-run \
  --utildata /var/lib/archivesmp/utildata
```

✅ Migration script ready for use!

---

## Step 9: Clean Up Temporary Files

```bash
# Remove temp files
rm /tmp/add_tracking_history_tables.sql
rm /tmp/populate_known_migrations.py
rm /tmp/apply_config_migrations.py
```

---

## What You've Deployed

### ✅ Database Tables (11 new):
1. `config_key_migrations` - Plugin version upgrade migrations
2. `config_change_history` - Complete audit trail
3. `deployment_history` - Deployment tracking
4. `deployment_changes` - Link changes to deployments
5. `config_rule_history` - Auto-tracked rule modifications
6. `config_variance_history` - Historical variance snapshots
7. `plugin_installation_history` - Plugin lifecycle
8. `change_approval_requests` - Approval workflow
9. `notification_log` - All notifications
10. `scheduled_tasks` - Automated task tracking
11. `system_health_metrics` - Performance monitoring

### ✅ Code Updates:
- **db_access.py**: Added `log_config_change()`, `get_change_history()`, `get_plugin_migrations()`, `create_deployment()`, `update_deployment_status()`
- **config_updater.py**: Now logs to database + keeps file backup
- **api.py**: Added 9 new history/tracking endpoints

### ✅ Scripts:
- **populate_known_migrations.py**: 10 known plugin migrations
- **apply_config_migrations.py**: Automated migration applier

### ✅ New API Endpoints:
- `GET /api/history/changes` - Query change history
- `GET /api/history/changes/{id}` - Get change details
- `GET /api/history/deployments` - List deployments
- `GET /api/history/deployments/{id}` - Deployment details
- `GET /api/history/variance` - Historical variance
- `GET /api/migrations` - All migrations summary
- `GET /api/migrations/{plugin}` - Plugin-specific migrations
- `GET /api/stats/changes` - Change statistics

---

## What's Next?

Now that tracking is deployed, you can:

1. **View change history**: `curl http://135.181.212.169:8000/api/history/changes`
2. **Apply migrations**: Use `apply_config_migrations.py` when updating plugins
3. **Track deployments**: Every config change is now auditable
4. **Analyze trends**: Historical variance data accumulates over time

---

## Troubleshooting

### If web API won't start:
```bash
# Check Python import errors
cd /opt/archivesmp-config-manager
python3 -c "from src.database.db_access import ConfigDatabase; print('OK')"
python3 -c "from src.web.api import app; print('OK')"

# Check logs in detail
journalctl -u archivesmp-webapi.service -f
```

### If database queries fail:
```bash
# Test database connection
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' -e "SELECT 1"

# Check table existence
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' asmp_config -e "SHOW TABLES LIKE '%history%'"
```

### If API returns 500 errors:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
systemctl restart archivesmp-webapi.service
journalctl -u archivesmp-webapi.service -f
```

---

## Rollback Plan (If Needed)

If something goes wrong:

```bash
# 1. Restore old code
cd /opt/archivesmp-config-manager
git checkout HEAD -- src/database/db_access.py
git checkout HEAD -- src/updaters/config_updater.py
git checkout HEAD -- src/web/api.py

# 2. Restart service
systemctl restart archivesmp-webapi.service

# 3. Database tables can stay (they won't break anything)
# Or drop them if needed:
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' asmp_config -e "
DROP TABLE IF EXISTS config_key_migrations;
DROP TABLE IF EXISTS config_change_history;
DROP TABLE IF EXISTS deployment_history;
DROP TABLE IF EXISTS deployment_changes;
DROP TABLE IF EXISTS config_rule_history;
DROP TABLE IF EXISTS config_variance_history;
DROP TABLE IF EXISTS plugin_installation_history;
DROP TABLE IF EXISTS change_approval_requests;
DROP TABLE IF EXISTS notification_log;
DROP TABLE IF EXISTS scheduled_tasks;
DROP TABLE IF EXISTS system_health_metrics;
"
```

---

**Deployment complete! Option C is now live on Hetzner.** 🚀
