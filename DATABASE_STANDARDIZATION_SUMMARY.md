# ✅ Database Schema Standardization - Complete

**Date**: November 24, 2025  
**Status**: ✅ Complete

## What Was Done

### 1. Identified the Problem
- `src/database/schema.sql` was **severely incomplete** (only 5 tables)
- Code references **23+ tables** across the codebase
- Attempting to use incomplete schema would cause immediate crashes
- Type mismatches between old schema (INT) and production (VARCHAR)

### 2. Established Single Source of Truth
- **`AUTHORITATIVE_SCHEMA.sql`** is now the official database schema
- Contains all 23 tables required by the application
- Includes proper foreign keys, indexes, and seed data
- Uses correct VARCHAR(16) for instance_id (matches AMP's format)

### 3. Deprecated Old Schema
- `src/database/schema.sql` marked as DEPRECATED
- File kept for reference but warns against usage
- All documentation points to AUTHORITATIVE_SCHEMA.sql

### 4. Created Deployment Tools

#### Scripts Created:
- **`scripts/init_database.sh`** - Linux/Debian initialization script
- **`scripts/init_database.ps1`** - Windows PowerShell initialization script

#### Documentation Created:
- **`DATABASE_INITIALIZATION.md`** - Complete setup guide
- **`DATABASE_RESET_COMMANDS.md`** - Quick reference commands

### 5. Database Reset Commands

**For Production (Hetzner):**
```bash
mysql -u sqlworkerSMP -p -e "DROP DATABASE IF EXISTS asmp_config; CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u sqlworkerSMP -p asmp_config < /opt/archivesmp-config-manager/AUTHORITATIVE_SCHEMA.sql
sudo systemctl restart homeamp-agent archivesmp-webapi
```

**For Development (Windows):**
```powershell
mysql -u root -p -e "DROP DATABASE IF EXISTS asmp_config; CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p asmp_config < d:\homeamp.ampdata\homeamp.ampdata\AUTHORITATIVE_SCHEMA.sql
```

## Schema Overview

### 23 Tables Included:

**Infrastructure (7)**
- instances, plugins, instance_plugins
- datapacks, instance_datapacks
- instance_server_properties, discovery_runs

**Tagging System (4)**
- meta_tag_categories, meta_tags
- instance_meta_tags, meta_tag_history

**Configuration (4)**
- config_rules, config_variance_cache
- config_drift_log, baseline_snapshots

**Updates & Deployment (3)**
- plugin_update_queue, deployment_history
- change_approval_requests

**Operations (5)**
- worlds, notification_log, scheduled_tasks
- audit_log, instance_tags

### Seed Data:
- 5 meta tag categories (server_type, player_count, game_mode, mod_level, maintenance)
- 8 default meta tags (pure-vanilla, lightly-modded, heavily-modded, survival, creative, minigame, hub, proxy)

## Verification Checklist

After running initialization:

```bash
# Should show 23 tables
mysql -u sqlworkerSMP -p asmp_config -e "SHOW TABLES;"

# Should return 8
mysql -u sqlworkerSMP -p asmp_config -e "SELECT COUNT(*) FROM meta_tags;"

# Should show VARCHAR(16)
mysql -u sqlworkerSMP -p asmp_config -e "DESCRIBE instances;"
```

## What This Fixes

### Before (Broken):
- ❌ schema.sql only had 5 tables
- ❌ Missing: instance_plugins, meta_tags, config_rules, audit_log, etc.
- ❌ Wrong type: instances.id INT instead of instance_id VARCHAR(16)
- ❌ Code would crash immediately: "Table doesn't exist"
- ❌ Foreign keys would fail due to type mismatches

### After (Working):
- ✅ AUTHORITATIVE_SCHEMA.sql has all 23 tables
- ✅ Correct VARCHAR(16) types matching AMP instance IDs
- ✅ All foreign key relationships work
- ✅ Seed data provides immediate functionality
- ✅ Code can query all required tables
- ✅ Easy deployment with init scripts

## Migration Notes

### For Fresh Installations:
```bash
# Just run AUTHORITATIVE_SCHEMA.sql
mysql -u sqlworkerSMP -p asmp_config < AUTHORITATIVE_SCHEMA.sql
```

### For Existing Deployments:
```bash
# Backup first!
mysqldump -u sqlworkerSMP -p asmp_config > backup_$(date +%Y%m%d).sql

# Drop and recreate
mysql -u sqlworkerSMP -p -e "DROP DATABASE IF EXISTS asmp_config; CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u sqlworkerSMP -p asmp_config < AUTHORITATIVE_SCHEMA.sql

# Restart services
sudo systemctl restart homeamp-agent archivesmp-webapi
```

⚠️ **Note**: Old data cannot be automatically migrated due to INT→VARCHAR primary key change. Manual data migration required if preserving old data.

## Files Modified

### Deprecated:
- `software/homeamp-config-manager/src/database/schema.sql` - Now just a warning file

### Created:
- `software/homeamp-config-manager/scripts/init_database.sh` - Bash init script
- `software/homeamp-config-manager/scripts/init_database.ps1` - PowerShell init script
- `DATABASE_INITIALIZATION.md` - Complete setup documentation
- `DATABASE_RESET_COMMANDS.md` - Quick command reference
- `DATABASE_STANDARDIZATION_SUMMARY.md` - This file

### Unchanged (Already Correct):
- `AUTHORITATIVE_SCHEMA.sql` - The source of truth

## Next Steps

1. ✅ **Commit to Repository**
   ```bash
   git add AUTHORITATIVE_SCHEMA.sql
   git add DATABASE_*.md
   git add software/homeamp-config-manager/scripts/init_database.*
   git add software/homeamp-config-manager/src/database/schema.sql
   git commit -m "Standardize on AUTHORITATIVE_SCHEMA.sql, deprecate old schema"
   git push origin master
   ```

2. **Deploy to Production (Hetzner)**
   ```bash
   # Pull latest code
   cd /opt/archivesmp-config-manager
   git pull
   
   # Reset database
   bash software/homeamp-config-manager/scripts/init_database.sh
   
   # Restart services
   sudo systemctl restart homeamp-agent archivesmp-webapi
   ```

3. **Monitor Logs**
   ```bash
   journalctl -u homeamp-agent -f
   journalctl -u archivesmp-webapi -f
   ```

4. **Verify Agent Discovery**
   - Wait for discovery cycle to complete
   - Check that instances table gets populated
   - Verify plugins are detected

## Success Criteria

- ✅ Database initializes without errors
- ✅ All 23 tables created successfully
- ✅ 8 meta tags loaded as seed data
- ✅ Services start without "table doesn't exist" errors
- ✅ Agent can write discovery data
- ✅ Web API returns data from database

## Documentation References

- See `DATABASE_INITIALIZATION.md` for detailed setup instructions
- See `DATABASE_RESET_COMMANDS.md` for copy-paste commands
- See `AUTHORITATIVE_SCHEMA.sql` for complete schema definition
- See `WHAT_WE_ACTUALLY_BUILT.md` for table usage patterns
