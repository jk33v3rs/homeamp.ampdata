# Database Migrations

## Overview

This directory contains SQL migration scripts for the **7-Level Hierarchy Configuration System**.

The system implements a sophisticated config resolution cascade:
```
GLOBAL → SERVER → META_TAG → INSTANCE → WORLD → RANK → PLAYER
```

## Migration Files

### 001_create_meta_tags.sql
Creates the core `meta_tags` table for grouping instances.

**Features:**
- Unique tag names
- Color coding for UI
- System vs user tags
- Priority-based conflict resolution
- Seeds 10 common system tags

**Tables:** `meta_tags`

---

### 002_create_instance_meta_tags.sql
Creates the junction table for many-to-many instance-tag relationships.

**Features:**
- Auto-assignment tracking
- ML confidence scores
- Cascade deletes

**Tables:** `instance_meta_tags`

---

### 003_create_config_rules.sql
Creates the universal config rules table supporting all 7 scope levels.

**Features:**
- Single table for all scopes
- Constraint checks enforce scope integrity
- Composite indexes for fast hierarchy resolution
- JSON-encoded values (supports all data types)
- Active/inactive rules
- Priority tie-breaking

**Tables:** `config_rules`

**Constraints:**
- Each rule must have exactly ONE scope level active
- Scope identifiers must match the declared scope level

---

### 004_create_worlds.sql
Tracks all Minecraft worlds discovered across instances.

**Features:**
- World type classification (normal/nether/end/custom)
- Seed and generator tracking
- Size and region count
- Active/inactive status

**Tables:** `worlds`

---

### 005_create_ranks.sql
Tracks LuckPerms ranks/groups with priorities.

**Features:**
- Server-wide or instance-specific ranks
- Priority/weight from LuckPerms
- Display names, prefixes, suffixes
- Permission count tracking
- Player count (updated periodically)
- Seeds 8 common ranks for Hetzner

**Tables:** `ranks`

---

### 006_create_config_backups.sql
Comprehensive backup system with integrity verification.

**Features:**
- SHA-256 hash verification
- Backup reasons (manual, auto, scheduled, drift, deployment)
- Restoration tracking
- Retention policy support
- Compression flag
- Expiration dates

**Tables:** `config_backups`

**Retention Policy:**
- Manual backups: 90 days
- Auto backups: 30 days
- 7-day grace period before deletion

---

### 007_create_config_variance_view.sql
Creates a view for detecting configuration drift.

**Features:**
- Automatic variance classification:
  - `NONE`: All instances identical
  - `VARIABLE`: Expected variation (e.g., server-port)
  - `META_TAG`: Values align with meta-tag groups
  - `INSTANCE`: Intentional per-instance config
  - `DRIFT`: Unintentional drift (needs attention)
- Value distribution by instance
- Instance and meta-tag grouping

**Views:** `config_variance`

**Note:** For large datasets, consider using the materialized view variant (commented in file).

---

## Running Migrations

### Automated (Recommended)

Use the master migration script:

```bash
cd scripts
chmod +x run_migrations.sh

# With defaults
./run_migrations.sh

# With custom parameters
./run_migrations.sh <host> <port> <user> <password> <database>

# Example
./run_migrations.sh 135.181.212.169 3369 sqlworkerSMP 'SQLdb2024!' archivesmp_config
```

The script will:
1. Test database connection
2. Run all migrations in order
3. Stop on first failure
4. Log all output
5. Run verification queries

### Manual Execution

Run migrations individually in order:

```bash
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'SQLdb2024!' archivesmp_config < migrations/001_create_meta_tags.sql
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'SQLdb2024!' archivesmp_config < migrations/002_create_instance_meta_tags.sql
# ... etc
```

### Windows (PowerShell)

```powershell
cd scripts\migrations

# Run each migration
Get-Content .\001_create_meta_tags.sql | mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'SQLdb2024!' archivesmp_config
Get-Content .\002_create_instance_meta_tags.sql | mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'SQLdb2024!' archivesmp_config
# ... etc
```

---

## Verification Queries

After running migrations, verify table creation:

```sql
-- Show all new tables
SHOW TABLES LIKE 'meta%';
SHOW TABLES LIKE 'config_%';
SHOW TABLES LIKE 'worlds';
SHOW TABLES LIKE 'ranks';

-- Check row counts
SELECT 'meta_tags' as tbl, COUNT(*) as rows FROM meta_tags
UNION ALL
SELECT 'instance_meta_tags', COUNT(*) FROM instance_meta_tags
UNION ALL
SELECT 'config_rules', COUNT(*) FROM config_rules
UNION ALL
SELECT 'worlds', COUNT(*) FROM worlds
UNION ALL
SELECT 'ranks', COUNT(*) FROM ranks
UNION ALL
SELECT 'config_backups', COUNT(*) FROM config_backups;

-- Check variance view
SELECT COUNT(*) as variance_entries FROM config_variance;
```

---

## Rollback

Each migration is idempotent (uses `IF NOT EXISTS`), so re-running is safe.

To completely rollback:

```sql
DROP VIEW IF EXISTS config_variance;
DROP TABLE IF EXISTS config_backups;
DROP TABLE IF EXISTS ranks;
DROP TABLE IF EXISTS worlds;
DROP TABLE IF EXISTS config_rules;
DROP TABLE IF EXISTS instance_meta_tags;
DROP TABLE IF EXISTS meta_tags;
```

**Warning:** This will delete all data. Always backup first!

---

## Dependencies

### External Tables (Must Exist)
- `instances` - Core instance registry
- `config_files` - Config file tracking (for backups)
- `plugins` - Plugin registry (for config_rules FK)

### Required Privileges
```sql
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER 
ON archivesmp_config.* 
TO 'sqlworkerSMP'@'%';
```

---

## Troubleshooting

### Error: Cannot add foreign key constraint

**Cause:** Referenced table doesn't exist or column mismatch

**Fix:** Ensure `instances`, `config_files`, and `plugins` tables exist with correct schema

### Error: Duplicate entry for key 'unique_instance_tag'

**Cause:** Attempting to assign same tag to instance twice

**Fix:** Normal behavior - constraint prevents duplicates. Check existing assignments:
```sql
SELECT * FROM instance_meta_tags WHERE instance_id = 'your_instance';
```

### Performance Issues

**Symptoms:** Slow variance view queries

**Fix:** Create materialized view (see 007_create_config_variance_view.sql comments)

---

## Post-Migration Steps

After successful migration:

1. **Seed Meta Tags** (if not auto-seeded):
   ```sql
   -- Run seed queries from 001_create_meta_tags.sql
   ```

2. **Assign Initial Tags**:
   ```bash
   # Use instance grouping script (create if doesn't exist)
   python scripts/assign_initial_tags.py
   ```

3. **Discover Worlds**:
   ```bash
   python scripts/discover_worlds.py
   ```

4. **Parse LuckPerms Ranks**:
   ```bash
   python scripts/discover_ranks.py
   ```

5. **Test API Endpoints**:
   ```bash
   curl http://localhost:8000/api/meta-tags
   curl http://localhost:8000/api/worlds
   curl http://localhost:8000/api/ranks
   ```

---

## Schema Diagram

```
┌─────────────────┐
│   meta_tags     │
└────────┬────────┘
         │
    ┌────▼──────────────────┐
    │ instance_meta_tags    │◄────┐
    └────────┬──────────────┘     │
             │                    │
    ┌────────▼────────┐    ┌──────┴──────┐
    │  config_rules   │    │  instances  │
    └─────────────────┘    └─────────────┘
             │                    │
    ┌────────▼────────┐    ┌──────┴──────┐
    │     worlds      │    │    ranks    │
    └─────────────────┘    └─────────────┘
```

---

## Support

For issues or questions:
1. Check logs: `migration_YYYYMMDD_HHMMSS.log`
2. Review verification queries in each migration file
3. Test with small datasets first
4. Ensure network connectivity to database server

---

**Last Updated:** 2025-11-18  
**Version:** 1.0.0  
**Compatibility:** MariaDB 10.5+, MySQL 8.0+
