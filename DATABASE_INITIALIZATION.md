# Database Initialization Guide

## Overview

The ArchiveSMP Configuration Manager uses a single authoritative database schema defined in `AUTHORITATIVE_SCHEMA.sql` at the repository root. This file is the **SINGLE SOURCE OF TRUTH** for the database structure.

## Files

- **`AUTHORITATIVE_SCHEMA.sql`** - Complete database schema with all tables, indexes, and seed data
- **`software/homeamp-config-manager/scripts/init_database.sh`** - Linux/Debian initialization script
- **`software/homeamp-config-manager/scripts/init_database.ps1`** - Windows PowerShell initialization script
- **`software/homeamp-config-manager/src/database/schema.sql`** - ⚠️ DEPRECATED (do not use)

## Quick Start

### Production (Hetzner/OVH Debian 12)

```bash
# SSH/RDP into the server as webadmin
cd /opt/archivesmp-config-manager
bash software/homeamp-config-manager/scripts/init_database.sh

# Or manually:
mysql -u sqlworkerSMP -p -e "DROP DATABASE IF EXISTS asmp_config; CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u sqlworkerSMP -p asmp_config < AUTHORITATIVE_SCHEMA.sql

# Restart services
sudo systemctl restart homeamp-agent
sudo systemctl restart archivesmp-webapi
```

### Development (Windows)

```powershell
# From repository root
cd d:\homeamp.ampdata\homeamp.ampdata

# Show commands (dry run)
.\software\homeamp-config-manager\scripts\init_database.ps1

# Actually execute
.\software\homeamp-config-manager\scripts\init_database.ps1 -Execute

# Or manually via MySQL client:
mysql -u root -p
DROP DATABASE IF EXISTS asmp_config;
CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asmp_config;
SOURCE d:/homeamp.ampdata/homeamp.ampdata/AUTHORITATIVE_SCHEMA.sql;
```

## What Gets Created

### Core Tables (23 total)

1. **Infrastructure**
   - `instances` - AMP instance registry
   - `plugins` - Global plugin catalog
   - `instance_plugins` - Plugin installations per instance
   - `datapacks` - Datapack registry
   - `instance_datapacks` - Datapack installations
   - `instance_server_properties` - Server.properties tracking
   - `discovery_runs` - Agent discovery history

2. **Tagging System**
   - `meta_tag_categories` - Tag categories
   - `meta_tags` - Available tags
   - `instance_meta_tags` - Tag assignments
   - `instance_tags` - Alternative tag table
   - `meta_tag_history` - Tag change history

3. **Configuration Management**
   - `config_rules` - Baseline configuration rules
   - `config_variance_cache` - Pre-calculated variance data
   - `config_drift_log` - Detected drift events
   - `baseline_snapshots` - Loaded baseline tracking
   - `config_change_history` - Config change audit

4. **Updates & Deployment**
   - `plugin_update_queue` - Pending plugin updates
   - `deployment_history` - Deployment tracking
   - `change_approval_requests` - Approval workflow

5. **Monitoring & Operations**
   - `worlds` - Minecraft world tracking
   - `notification_log` - System notifications
   - `scheduled_tasks` - Scheduled operations
   - `audit_log` - System audit trail

### Seed Data

- **Meta Tag Categories**: server_type, player_count, game_mode, mod_level, maintenance
- **Default Tags**: pure-vanilla, lightly-modded, heavily-modded, survival, creative, minigame, hub, proxy

## Database Credentials

### Production (Hetzner)
- Host: `localhost` (MariaDB runs locally)
- User: `sqlworkerSMP`
- Database: `asmp_config`
- Note: No `-h` or `-P` needed for local connections

### Production (OVH)
- Not yet deployed - will use same setup as Hetzner

### Development (Windows)
- Host: `localhost` or `127.0.0.1`
- User: `root` or custom
- Database: `asmp_config`

## Verification

After initialization, verify tables exist:

```sql
USE asmp_config;
SHOW TABLES;
SELECT COUNT(*) FROM instances;
SELECT COUNT(*) FROM meta_tags;
```

Expected output: 23 tables, 8 default meta tags

## Troubleshooting

### "Table doesn't exist" errors
- You're using the old incomplete schema.sql
- Solution: Run `AUTHORITATIVE_SCHEMA.sql`

### Foreign key errors
- Old data incompatible with new schema
- Solution: Drop database completely and recreate

### Import fails
- Check MySQL user permissions
- Ensure `utf8mb4` charset support
- Verify file path is correct

## Migration from Old Schema

If you have existing data in the old schema:

1. **Backup first**: `mysqldump -u sqlworkerSMP -p asmp_config > backup.sql`
2. **Drop old database**: `DROP DATABASE asmp_config;`
3. **Load new schema**: Run AUTHORITATIVE_SCHEMA.sql
4. **Manually migrate data** if needed (instances, plugins, config_rules)

⚠️ The old schema had INT primary keys, new schema uses VARCHAR - data migration requires transformation.

## Best Practices

1. ✅ **Always use AUTHORITATIVE_SCHEMA.sql** for fresh installations
2. ✅ **Backup before reinitializing** on production
3. ✅ **Restart services** after schema changes
4. ✅ **Test on dev first** before production deployment
5. ❌ **Never use src/database/schema.sql** (incomplete, deprecated)

## Related Documentation

- `AUTHORITATIVE_SCHEMA.sql` - The actual schema file
- `WHAT_WE_ACTUALLY_BUILT.md` - Table usage documentation
- `PRODUCTION_READINESS_AUDIT.md` - Deployment checklist
