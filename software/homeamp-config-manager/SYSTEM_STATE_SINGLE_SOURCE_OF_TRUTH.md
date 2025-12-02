# ArchiveSMP Configuration Manager - Single Source of Truth

**Last Updated**: December 3, 2025  
**Production Status**: Hetzner Deployed, OVH Pending  
**Critical Issues**: See Section 8

---

## 1. PRODUCTION ARCHITECTURE (CURRENT STATE)

### 1.1 Deployment Topology

```
DEVELOPMENT (Windows PC)
  E:\homeamp.ampdata\
  ├── software/homeamp-config-manager/     ← THIS SOFTWARE
  ├── utildata/                            ← PRODUCTION DATA SNAPSHOTS
  │   ├── plugin_universal_configs/        ← Baseline configs (57 plugins)
  │   └── [server snapshots from both bare metal servers]
  
PRODUCTION SERVERS (Debian Linux)

HETZNER XEON (135.181.212.169) - archivesmp.site
/opt/archivesmp-config-manager/
├── Web API Service (port 8000) - 4 workers
├── Agent Service (port 8001) - Background daemon
├── Database: asmp_config (MariaDB on 135.181.212.169:3369)
├── 11 AMP Instances discovered
└── Services:
    ├── archivesmp-webapi.service (RUNNING)
    └── homeamp-agent.service (RUNNING with CRASHES)

OVH RYZEN (37.187.143.41) - archivesmp.online  
NOT YET DEPLOYED - Final one-shot deployment pending fixes
```

### 1.2 Current Capabilities

**✅ WORKING:**
- Web API running on Hetzner (http://135.181.212.169:8000)
- Agent discovering all 11 instances on Hetzner
- Database connectivity (asmp_config on port 3369)
- MinIO integration (cloud.archivesmp.site)
- Web UI accessible (index.html, variance.html, deploy.html)

**❌ BROKEN:**
- Drift detector crashes with list/dict type errors
- Plugin update system not functional
- Web UI filtering (server/instance views show all instances)
- Baseline configs not parsed (markdown files instead of YAML)
- Restart functionality incomplete

---

## 2. DATABASE ARCHITECTURE

### 2.1 Database: asmp_config

**Connection Details:**
- Host: 135.181.212.169
- Port: 3369
- Database: `asmp_config` (CORRECT - all deployment files fixed)
- User: sqlworkerSMP
- Password: SQLdb2024!
- SSL: Disabled, allowPublicKeyRetrieval=true

**Schema Status:**
- ✅ Core tables exist: servers, instances, plugins, config_keys
- ⚠️ Missing 5 tables: instance_plugins, instance_datapacks, instance_server_properties, baseline_snapshots, config_rules
- ⚠️ Duplicate index in schema.sql line 130 (idx_plugin_name)

### 2.2 Data Storage Strategy

**MariaDB (135.181.212.169:3369):**
- Server metadata (Hetzner, OVH)
- Instance registry (23 total: 11 Hetzner + 12 OVH)
- Plugin catalog (~100 plugins)
- Drift reports and deviation tracking
- Config change history
- Deployment audit logs

**MinIO (cloud.archivesmp.site:3800):**
- Baseline configs (YAML per-plugin structure)
- Plugin JARs for deployment
- Config snapshots and backups
- Path: `minio://configs/baselines/<PLUGIN>/config.yml`

**Local Filesystem (per server):**
- Live instance configs: `/home/amp/.ampdata/instances/<INSTANCE>/Minecraft/plugins/<PLUGIN>/`
- Application logs: `/var/log/archivesmp/*.log`
- systemd journal: `journalctl -u homeamp-agent.service`

---

## 3. SERVER INFRASTRUCTURE

### 3.1 Hetzner Xeon (Primary Active)

**Hardware:**
- Location: Helsinki, Finland
- CPU: Intel Xeon W-2295 (18 cores)
- RAM: 128GB
- Storage: 1TB SSD
- Network: 135.181.212.169
- Domain: archivesmp.site

**11 Active Instances (2XXX port range):**
- TOWER01 (tower01) - Eternal Tower Defense [2171]
- EVO01 (ev01) - Evolution SMP (Modded) [2172]
- DEV01 (dev01) - Development/Testing [2173]
- MINI01 (mini01) - General Minigames [2174]
- BIGG01 (bigg01) - BiggerGAMES [2175]
- FORT01 (fort01) - Battle Royale [2176]
- PRIV01 (priv01) - Private Worlds [2177]
- SMP101 (smp101) - SMP Season 1 [2178]
- [3 additional instances]

**Services Running:**
- archivesmp-webapi.service (Uvicorn, 4 workers, port 8000)
- homeamp-agent.service (Background, port 8001)

### 3.2 OVH Ryzen (Pending Deployment)

**Hardware:**
- Location: Gravelines, France
- CPU: AMD Ryzen 7 9700X
- RAM: 64GB DDR5
- Storage: 2x 500GB NVMe (RAID 1)
- Network: 37.187.143.41
- Domain: archivesmp.online

**12 Expected Instances (1XXX port range):**
- CLIP01 (clippycore01) - ClippyCore Hardcore [1179]
- CSMC01 (csmc01) - CounterStrike: Minecraft [1180]
- EMAD01 (emad01) - EMadventure [1181]
- BENT01 (bent01) - BentoBox Skyblock [1182]
- HCRE01 (hardcore01) - Hardcore Survival [1183]
- SMP201 (smp201) - Archive SMP Season 2 [1184]
- HUB01 (hub01) - Network Hub [1185]
- MINT01 (minetorio01) - Minetorio Automation [1186]
- CREA01 (creative01) - Creative Mode [1187]
- GEY01 (geyser01) - Bedrock Support [19132]
- VEL01 (velocity01) - Velocity Proxy [XX69]
- [1 additional instance]

**Deployment Status:** NOT DEPLOYED (one-shot deployment planned after all fixes verified)

---

## 4. CONFIGURATION EXPECTATIONS

### 4.1 Universal Configs (82 plugins)

**Source:** `data/expectations/universal_configs_analysis.json`
**Definition:** Plugins that should have IDENTICAL configs across ALL instances

**Categories:**
- **Core Infrastructure**: LuckPerms, CoreProtect, Vault, ProtocolLib
- **bStats Integration**: Metrics collection (unique serverUuid per instance)
- **Economy System**: TheNewEconomy, QuickShop-Hikari suite
- **Gameplay Enhancement**: mcMMO, EliteMobs, Citizens
- **Utilities**: WorldEdit, WorldGuard, PlaceholderAPI

**Standardization Status:**
- ✅ 57 plugins have baseline configs in `utildata/plugin_universal_configs/`
- ⚠️ Baselines are markdown files, NOT parsed YAML (drift detector can't use them)
- ❌ 25 plugins missing baseline documentation

### 4.2 Variable Configs (23 plugins)

**Source:** `data/expectations/variable_configs_analysis_UPDATED.json`
**Definition:** Plugins with DOCUMENTED server-specific differences

**Allowed Variances:**
- **Per-Instance Unique:**
  - CoreProtect.table-prefix = `co_<INSTANCE>_`
  - QuickShop.database.table = `qs_hik_<INSTANCE>_`
  - mcMMO.database.tablePrefix = `mcmmo_<INSTANCE>_`
  - bStats.serverUuid (unique per instance)
  
- **Server-Specific:**
  - LevelledMobs (BENT01 has advanced levelling, others disabled)
  - ImageFrame.WebServer.Port (unique per instance: 31XX range)
  - Pl3xMap.settings.web-address (per-server domain)

- **Network-Aware:**
  - HuskSync.network.id (SMPnet vs DEVnet groupings)
  - Velocity plugins (cross-server coordination)

### 4.3 Config Rules System

**Purpose:** Automated validation and enforcement of config standards

**Rule Types:**
1. **Must Match Baseline:** Universal configs must be identical
2. **Allowed Variance:** Variable configs with documented exceptions
3. **Server-Specific Required:** Configs that MUST differ per server
4. **Network Coordination:** Configs that must align across server groups

**Implementation Status:** ❌ Database table `config_rules` not created

---

## 5. WEB INTERFACE (Current State)

### 5.1 Accessible URLs

**Base:** http://135.181.212.169:8000

**Pages:**
- `/static/index.html` - Deviation Review (PRIMARY INTERFACE)
- `/static/variance.html` - Variance Analysis
- `/static/deploy.html` - Deployment Control Panel

### 5.2 Known UI Issues

**CRITICAL:**
1. **Filtering Broken:**
   - Server filter (Hetzner/OVH) shows all instances
   - Instance dropdown shows all instances regardless of server selection
   - No proper isolation of server-specific data

2. **Baseline Display:**
   - Shows markdown file content instead of parsed YAML
   - "Expected" column displays raw markdown with headers
   - Cannot properly compare against live configs

3. **Deployment Panel:**
   - Restart buttons not fully functional
   - Plugin update workflow incomplete
   - No rollback mechanism implemented

**COSMETIC:**
- 424 HTML/CSS linting warnings (inline styles in deploy.html)
- Should extract to external stylesheet for maintainability

### 5.3 Theme System (Incomplete)

**Current:** Single dark theme (VS Code style)

**Requested Features:**
- Multiple theme choices (light, dark, high contrast)
- Theme persistence (localStorage)
- Per-user theme preferences
- More polished, professional appearance

---

## 6. AGENT SYSTEM

### 6.1 Current Architecture

**Type:** Monolithic agent (same codebase for both servers)

**Discovery:**
- Scans AMP instances via AMP API
- Detects instance metadata (friendly name, app ID, port)
- Populates database with discovered instances

**Drift Detection:**
- Compares live configs against baselines
- **BROKEN:** Crashes with `'list' object has no attribute 'get'` errors
- Root cause: Doesn't handle YAML files that return lists at top level

### 6.2 Required Agent Split (ARCHITECTURE_COMPLIANCE_AUDIT.md)

**Host Agent (Hetzner):**
- Orchestrates all operations
- Executes changes via AMP API for BOTH servers
- Publishes jobs to Redis queue
- Aggregates results from both servers
- Runs web UI and API

**Client Agent (OVH):**
- Lightweight passthrough only
- Provides AMP API credentials to Hetzner
- Ships logs to Hetzner MariaDB
- Does NOT execute changes
- Does NOT cache configs
- Does NOT have web UI

**Implementation Status:** ❌ Not implemented (monolithic agent on Hetzner only)

---

## 7. PLUGIN MANAGEMENT SYSTEM

### 7.1 Plugin Catalog

**Total Plugins:** ~100 across network

**Minimal Build ("M" Rating - Essential Foundation):**
- LuckPerms (5.4.145) - Permissions
- CoreProtect (23.2) - Block logging
- CMI + CMILib (9.7.14.2 / 1.5.4.4) - Multi-tool
- PlaceholderAPI (2.11.6) - Variables
- ProtocolLib (5.3.0) - Packet manipulation
- WorldEdit/WorldGuard (7.3.11 / 7.0.13)

**Standard Build ("S" Rating - Full Deployment):**
- QuickShop-Hikari (6.2.0.9+) - Player shops
- mcMMO (1.4.06) - Skills system
- EliteMobs (9.4.2) - Boss mobs
- BetterStructures (1.8.1) - World gen
- Citizens (2.0.38) - NPCs
- Pl3xMap (1.21.4-525) - Live maps

**Bespoke (One-Off Specialized):**
- EternalTD (1.4.0) - Tower defense (TOWER01 only)
- Minetorio - Factorio automation (MINT01 only)
- BentoBox Ecosystem - Skyblock suite (BENT01 only)
- ArmoryCrate - Advanced weapons (specific servers)

### 7.2 Plugin Update Workflow (Broken)

**Intended Flow:**
1. Pulumi hourly checks for new plugin versions
2. Detected updates staged in MinIO
3. Admin reviews in web UI
4. Approved updates deployed to DEV01 first
5. Test on DEV01, then promote to production

**Current Status:**
- ❌ Pulumi scripts not integrated
- ❌ Update detection not automated
- ❌ Staging area not implemented
- ❌ Web UI update approval interface incomplete
- ❌ Rollback system not built

---

## 8. CRITICAL ISSUES (BLOCKING DEPLOYMENT)

### 8.1 Drift Detector Crashes

**Error:** `AttributeError: 'list' object has no attribute 'get'`

**Root Cause:**
```python
# Line 204: current_plugin can be a LIST if YAML returns top-level list
current_plugin = current.get(plugin_name, {})

# Line 206: Crashes when calling .get() on a list
current_config = current_plugin.get(config_file, {})
```

**Fix Required:**
```python
current_plugin = current.get(plugin_name, {})
if not isinstance(current_plugin, dict):
    continue  # Skip non-dict configs
for config_file, baseline_config in baseline_plugin.items():
    current_config = current_plugin.get(config_file, {})
```

**Status:** ⚠️ Fix identified (BUG_ANALYSIS_DRIFT_DETECTOR.md), not yet deployed

### 8.2 Empty Baselines Folder

**Location:** `/opt/archivesmp-config-manager/data/baselines/`  
**Status:** EMPTY

**Impact:**
- Drift detector has nothing to compare against
- Cannot validate configs against standards
- No automated deviation detection

**Fix Required:**
- Parse markdown files in `utildata/plugin_universal_configs/`
- Extract YAML configs from markdown code blocks
- Populate `/opt/archivesmp-config-manager/data/baselines/<PLUGIN>/config.yml`
- Script: `scripts/parse_markdown_to_sql.py` (needs updating)

### 8.3 Hardcoded Values Still Present

**Database Connection Examples:**
- Some scripts still have hardcoded credentials (src/web/api_v2.py lines 37-41)
- Should use settings.py singleton instead

**Network Values:**
- Hardcoded IPs in various config files
- Port numbers not centralized
- Domain names scattered across codebase

**Fix Required:**
- Audit all Python files for hardcoded values
- Centralize to `src/core/settings.py`
- Use environment variables or config files

### 8.4 Web UI Filtering Broken

**Issue:**
```javascript
// Intended: Show only Hetzner instances when "Hetzner" selected
// Actual: Shows ALL instances regardless of filter
```

**Impact:**
- Cannot isolate server-specific operations
- Risk of deploying to wrong server
- Confusion when reviewing deviations

**Fix Required:**
- Fix JavaScript filtering in deploy.html
- Properly filter instance lists by physical_server field
- Ensure server selection cascades to instance dropdown

---

## 9. DEPLOYMENT CHECKLIST (Before OVH Deploy)

### 9.1 Hetzner Fixes (REQUIRED)

- [ ] Deploy drift detector fix (isinstance check for lists)
- [ ] Populate baselines folder from plugin_universal_configs
- [ ] Fix duplicate agent initialization (service.py line 325)
- [ ] Verify drift detector stops crashing
- [ ] Test full drift detection cycle
- [ ] Fix web UI filtering (server/instance dropdowns)
- [ ] Parse markdown baselines to YAML format
- [ ] Test baseline comparison in web UI

### 9.2 Code Quality (OPTIONAL)

- [ ] Remove hardcoded credentials (use settings.py)
- [ ] Centralize network configuration
- [ ] Add Python type hints (50+ missing return types)
- [ ] Extract inline CSS to external stylesheet (424 warnings)
- [ ] Add multiple theme support to web UI

### 9.3 OVH Deployment (ONE-SHOT - NO RETRIES)

- [ ] Commit all working fixes to git
- [ ] Create deployment package
- [ ] Deploy to OVH (final one-shot deployment)
- [ ] Verify both servers communicating
- [ ] Test cross-server drift detection
- [ ] Validate plugin deployment workflow

---

## 10. FUTURE ENHANCEMENTS (Post-Deployment)

### 10.1 Architecture Migration

**From:** Monolithic agent on Hetzner  
**To:** Distributed host/client architecture

**Benefits:**
- Hetzner orchestrates everything via AMP API
- OVH becomes thin client (logs only)
- Centralized control and visibility
- Better failure isolation

### 10.2 Plugin Automation

**Pulumi Integration:**
- Hourly update checks
- Automated staging
- Version tracking
- Dependency management

**Admin Workflow:**
- Review pending updates in web UI
- Approve/reject with one click
- Automated deployment to DEV01
- Rollback capability

### 10.3 Advanced Deviation Analysis

**Statistical Outlier Detection:**
- Identify configs that deviate from network norms
- Highlight suspicious changes
- Auto-approve known good variances
- Flag potential misconfigurations

**Machine Learning:**
- Learn normal config patterns
- Detect anomalies automatically
- Suggest standardization opportunities

---

## 11. GLOSSARY

**AMP:** CubeCoders Application Management Panel - server management platform  
**Baseline:** Expected/standard configuration for a plugin  
**Deviation:** Difference between live config and baseline  
**Drift:** Unintended configuration changes over time  
**Instance:** Single Minecraft server (e.g., SMP201, DEV01)  
**Physical Server:** Bare metal machine (Hetzner Xeon or OVH Ryzen)  
**Universal Config:** Plugin config that should be identical everywhere  
**Variable Config:** Plugin config with documented allowed differences

---

## 12. QUICK REFERENCE

### Database Connection
```bash
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p asmp_config
# Password: SQLdb2024!
```

### Service Management (Hetzner)
```bash
sudo systemctl status archivesmp-webapi.service
sudo systemctl status homeamp-agent.service
sudo journalctl -u homeamp-agent.service -f
```

### Web Access
```
Primary UI:   http://135.181.212.169:8000/static/index.html
Agent Status: http://135.181.212.169:8001/api/agent/status
```

### Critical Paths
```
Application:  /opt/archivesmp-config-manager/
Logs:         /var/log/archivesmp/
Instances:    /home/amp/.ampdata/instances/
Baselines:    /opt/archivesmp-config-manager/data/baselines/ (EMPTY!)
```

---

**Document Version:** 1.0  
**Maintained By:** AI Assistant + Developer  
**Update Frequency:** After each significant change or deployment
