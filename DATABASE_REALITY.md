# Database Reality Check Results
**Date**: November 18, 2025  
**Database**: asmp_config @ 135.181.212.169:3369

---

## CRITICAL FINDINGS

### ✅ WHAT EXISTS (30 Tables)

**Core Schema** (from create_database_schema.sql):
- ✓ `instances` - **19 instances** (11 Hetzner + 8 OVH)
- ✓ `meta_tags` - **16 tags** (hetzner, ovh, survival, creative, etc.)
- ✓ `meta_tag_categories` - Tag categories
- ✓ `instance_tags` - Tag assignments
- ✓ `instance_groups` - **8 groups** (physical clusters, logical groups)
- ✓ `instance_group_members` - Group memberships
- ✓ `worlds`, `world_groups`, `world_group_members`, `world_tags` - Multi-world support
- ✓ `regions`, `region_groups`, `region_group_members`, `region_tags` - Region support
- ✓ **`config_rules`** - **6 rules** (THIS IS THE GLOBAL CONFIG)
- ✓ `config_variables` - Variable substitution
- ✓ `config_variance_cache` - **0 entries** (NOT POPULATED)
- ✓ `baseline_snapshots` - Baseline snapshots
- ✓ `config_drift_log` - Drift logging

**Plugin Schema** (from add_plugin_metadata_tables.sql):
- ✓ `plugins` - **0 plugins** (TABLE EXISTS BUT EMPTY)
- ✓ `instance_plugins` - **0 mappings** (TABLE EXISTS BUT EMPTY)
- ✓ `instance_datapacks` - Datapack tracking (exists)
- ✓ `instance_server_properties` - Server properties (exists)
- ✓ `plugin_update_queue` - Update queue (exists)

**Player/Rank System**:
- ✓ `player_ranks`, `rank_definitions` - Rank system
- ✓ `player_roles`, `player_role_categories`, `player_role_assignments` - Role system
- ✓ `player_config_overrides` - Player-specific overrides

### ❌ WHAT DOESN'T EXIST

**Comprehensive Tracking Tables** (from add_comprehensive_tracking.sql):
- ✗ `global_config_baseline` - NOT CREATED
- ✗ `instance_config_values` - NOT CREATED
- ✗ `config_variance_detected` - NOT CREATED
- ✗ `plugin_developers` - NOT CREATED
- ✗ `plugin_cicd_builds` - NOT CREATED
- ✗ `plugin_documentation_pages` - NOT CREATED
- ✗ `plugin_version_history` - NOT CREATED

**Conclusion**: The `add_comprehensive_tracking.sql` schema was NEVER executed on the database.

---

## THE "GLOBAL CONFIG" SYSTEM

### What You Meant By "we already have the global config"

**It's the `config_rules` table** - and you're RIGHT, it exists!

**Current State**:
```
Total config rules: 6
[7] Minecraft    gamemode             = creative     (META_TAG:creative)
[7] Minecraft    spawn-protection     = 0            (META_TAG:creative)
[8] HuskSync     database.host        = 135.181.212.169  (SERVER:Hetzner)
[8] HuskSync     database.host        = 37.187.143.41    (SERVER:OVH)
[9] EliteMobs    language             = english      (GLOBAL)
[9] EliteMobs    setupDoneV4          = true         (GLOBAL)
```

**This IS key-level config tracking**:
- Plugin name: `HuskSync`, `EliteMobs`, `Minecraft`
- Config key: `database.host`, `gamemode`, `language`
- Scope: GLOBAL, SERVER, META_TAG, INSTANCE
- Priority: Lower number = higher priority (0-9 scale)

**I was wrong**: You DON'T need `global_config_baseline` and `instance_config_values` tables. The `config_rules` table IS the global baseline system.

---

## THE ACTUAL PROBLEM

### Why Web UI Shows 0 for Everything

**Empty Tables**:
1. ❌ `plugins` table: **0 rows** - No plugin metadata
2. ❌ `instance_plugins` table: **0 rows** - No install mappings
3. ❌ `config_variance_cache` table: **0 rows** - No variance analysis

**Broken API Endpoints** (api.py):
```python
@app.get("/api/plugins")
async def get_plugins():
    # Query distinct plugins from instances (would need plugin tracking table)
    return []  # HARDCODED EMPTY LIST
```

**Root Cause**: Population scripts were NEVER run on production.

---

## WHAT NEEDS TO HAPPEN

### 1. Run Population Scripts (On Hetzner Production)

**Script 1: Populate Plugin Metadata**
```bash
# On Hetzner: /opt/archivesmp-config-manager/
python scripts/populate_plugin_metadata.py --amp-dir /home/amp/.ampdata/instances
```
**What it does**:
- Scans all 11 Hetzner instances
- Reads plugin.yml from installed JARs
- Populates `plugins` table (name, version, sources, CI/CD, docs)
- Populates `instance_plugins` table (what's installed where)
- Scans datapacks
- Reads server.properties

**Script 2: Load Baseline Configs**
```bash
python scripts/load_baselines.py
```
**What it does**:
- Reads markdown baseline files from `data/baselines/universal_configs/`
- Parses YAML blocks
- Inserts into `baseline_snapshots` table
- Creates GLOBAL rules in `config_rules` table

**Script 3: Populate Variance Cache**
```bash
python scripts/populate_config_cache.py --amp-dir /home/amp/.ampdata/instances
```
**What it does**:
- Scans actual config files from live instances
- Compares to `config_rules` baseline
- Populates `config_variance_cache` with differences
- Classifies: NONE, VARIABLE, META_TAG, INSTANCE, DRIFT

### 2. Fix API Endpoints

**Change in api.py** (line 258):
```python
# BEFORE (WRONG):
@app.get("/api/plugins")
async def get_plugins():
    return []  # EMPTY

# AFTER (CORRECT):
@app.get("/api/plugins")
async def get_plugins():
    db.cursor.execute("""
        SELECT plugin_id, plugin_name, platform, current_version,
               has_cicd, cicd_provider, docs_url, wiki_url
        FROM plugins
        ORDER BY plugin_name
    """)
    plugins = db.cursor.fetchall()
    return {"plugins": plugins, "total": len(plugins)}
```

**Add /api/datapacks endpoint**:
```python
@app.get("/api/datapacks")
async def get_datapacks():
    db.cursor.execute("SELECT COUNT(DISTINCT datapack_name) as count FROM instance_datapacks")
    result = db.cursor.fetchone()
    return {"total": result['count'] if result else 0}
```

**Add /api/plugins/outdated endpoint**:
```python
@app.get("/api/plugins/outdated")
async def get_outdated_plugins():
    db.cursor.execute("""
        SELECT p.plugin_name, p.current_version, p.latest_version
        FROM plugins p
        WHERE p.latest_version IS NOT NULL 
        AND p.current_version != p.latest_version
    """)
    plugins = db.cursor.fetchall()
    return {"plugins": plugins, "count": len(plugins)}
```

### 3. Deploy to Hetzner

```bash
# SSH to Hetzner
ssh user@135.181.212.169

# Pull latest code
cd /opt/archivesmp-config-manager
git pull origin master

# Run population scripts
python scripts/populate_plugin_metadata.py
python scripts/load_baselines.py  
python scripts/populate_config_cache.py

# Restart web service
sudo systemctl restart archivesmp-webapi.service

# Check logs
journalctl -u archivesmp-webapi.service -f
```

---

## DECISION ON add_comprehensive_tracking.sql

### ❌ DO NOT USE IT (For Now)

**Reasons**:
1. **Duplicate functionality**: `config_rules` already provides global baseline
2. **Tables don't exist**: Never executed, would require migration
3. **No data**: Even if created, we'd need new population scripts
4. **Current system works**: `config_rules` + `config_variance_cache` is sufficient

**What to keep from it** (maybe later):
- `plugin_version_history` - Track version releases over time
- `plugin_cicd_builds` - Track CI/CD build history
- `plugin_documentation_pages` - Multiple doc sources per plugin

**What's redundant**:
- `global_config_baseline` → Use `config_rules` instead
- `instance_config_values` → Use variance cache or scan on-demand
- `config_variance_detected` → Use `config_variance_cache` instead

---

## IMMEDIATE ACTION PLAN

### Local (Development):
1. ✅ Fix `/api/plugins` endpoint to query `plugins` table
2. ✅ Add `/api/datapacks` endpoint
3. ✅ Add `/api/plugins/outdated` endpoint
4. ✅ Commit and push to GitHub

### Production (Hetzner):
1. Pull latest code from GitHub
2. Run `populate_plugin_metadata.py` to scan all instances
3. Run `load_baselines.py` to populate config_rules
4. Run `populate_config_cache.py` to detect variances
5. Restart web API service
6. Verify Web UI shows real data

### Verification:
```bash
# Check database after population
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p asmp_config
SELECT COUNT(*) FROM plugins;           # Should be > 0
SELECT COUNT(*) FROM instance_plugins;  # Should be > 0
SELECT COUNT(*) FROM config_variance_cache;  # Should be > 0
SELECT COUNT(*) FROM config_rules;      # Should be > 6

# Check API endpoints
curl http://localhost:8000/api/plugins
curl http://localhost:8000/api/datapacks
curl http://localhost:8000/api/variance/summary
```

---

## SUMMARY

**You were right**: 
- ✅ `config_rules` IS the global config system
- ✅ Schema exists and works
- ✅ `add_comprehensive_tracking.sql` is redundant

**The real issue**:
- ❌ `plugins` table is EMPTY (0 rows)
- ❌ `instance_plugins` table is EMPTY (0 rows)
- ❌ `config_variance_cache` table is EMPTY (0 rows)
- ❌ API endpoints return hardcoded empty lists
- ❌ Population scripts never ran on production

**The fix**:
1. Fix API endpoints (query tables instead of returning `[]`)
2. Run existing population scripts on Hetzner
3. Web UI will show real data
4. NO NEW SCHEMAS NEEDED
