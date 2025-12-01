# 🔍 Comprehensive Feature Audit - ArchiveSMP Config Manager
**Date**: November 14, 2025  
**Status**: Pre-Deployment Verification

---

## ✅ WHAT WE HAVE BUILT

### 1. **Plugin Update Checking System** ✅
**Status**: COMPLETE - All CI/CD sources implemented

- ✅ **Jenkins Support**: CodeMC, EngineHub, md5, dmulloy2, citizensnpcs, extendedclip, loohpjames
- ✅ **Modrinth API**: v2 with game version support
- ✅ **GitHub Releases**: Existing implementation
- ✅ **SpigotMC API**: Version checking (no download for premium)
- ✅ **Hangar API**: Paper plugin repository
- ✅ **PLUGIN_REGISTRY.md Parser**: Auto-loads 100+ plugin endpoints from markdown tables
- ✅ **Changelog Parser**: Keyword-based categorization (breaking/features/fixes/warnings)
- ✅ **Risk Assessment**: Semantic version comparison + changelog-based elevation
- ✅ **GUI Integration**: Summary cards, build badges, source icons, categorized changelogs

**Files**:
- `src/updaters/plugin_checker.py` (788 lines)
- `src/web/static/index.html` (Plugin Updates tab enhanced)
- `src/web/static/styles.css` (184 lines of new styles)
- `PLUGIN_REGISTRY.md` (260 lines, 100+ plugins with endpoints)

**Verification Needed**:
- [ ] Test against live Jenkins endpoints
- [ ] Test Modrinth API calls
- [ ] Verify all 60 universal config plugins have working endpoints

---

### 2. **Version Detection System** ✅
**Status**: COMPLETE - Filename-based extraction with nightly builds

- ✅ **Filename Parsing**: Regex patterns for `5.4.145`, `1.21.4-525`, `build-3847`, etc.
- ✅ **Nightly Build Format**: `nightly-YYYYMMDD-NNN` with daily counter
- ✅ **SNAPSHOT Handling**: Appends nightly ID to SNAPSHOT versions
- ✅ **Multi-Server Scanning**: Scans all instances across HETZNER/OVH utildata

**Files**:
- `src/utils/version_detector.py` (444 lines)

**Verification Needed**:
- [ ] Test against actual JAR filenames in utildata
- [ ] Integrate with plugin_checker.py for current version detection

---

### 3. **Configuration Drift Detection** ✅
**Status**: IMPLEMENTED - Needs testing after bug fixes

- ✅ **Drift Detector**: Compares live configs against baselines
- ✅ **Compliance Checker**: Universal config validation
- ✅ **Deviation Tracking**: Stores and manages drifted values

**Files**:
- `src/analyzers/drift_detector.py` (DriftDetector class)
- `src/analyzers/compliance_checker.py`
- `src/web/models.py` (DeviationParser, DeviationManager)

**Known Issues**:
- ⚠️ Drift detector crashes with list/dict type errors (user reported)
- [ ] Needs type safety fixes for baseline comparisons

---

### 4. **Deployment Pipeline** ✅
**Status**: IMPLEMENTED - GUI exists, needs production testing

- ✅ **Deploy Configs**: Multi-instance selection and deployment
- ✅ **Rollback System**: Backup creation before deployment + rollback UI
- ✅ **Health Checks**: Validate deployment success
- ✅ **Pl3xMap Integration**: Specialized deployment for map plugins
- ✅ **GUI Tabs**: Deploy, Restart, Pl3xMap sections

**Files**:
- `src/deployment/pipeline.py` (deployment orchestration)
- `src/web/static/deploy.html` (deployment UI)
- `src/web/api.py` (deploy_configs, rollback endpoints)
- `src/automation/plugin_automation.py` (auto-deploy to DEV01)

**Verification Needed**:
- [ ] Test deployment to production instances
- [ ] Verify rollback functionality
- [ ] Test Pl3xMap deployment workflow

---

### 5. **Configuration Management Core** ✅
**Status**: PARTIAL - Pull/Push exist but no GUI editor

- ✅ **Data Loader**: Platform-specific expectations (`data/expectations/{paper,velocity,geyser}/`)
- ✅ **Universal Configs**: 60 plugins (53 Paper, 6 Velocity, 1 Geyser)
- ✅ **File Handler**: Backup/restore operations
- ✅ **Config Updater**: Apply changes with validation
- ⚠️ **Pull from Live**: API exists (`/api/servers/{server}/config`) - NO GUI
- ⚠️ **Push to Live**: Deploy API exists - NO INDIVIDUAL KEY EDITOR
- ❌ **Web Form Editor**: MISSING - No Monaco/CodeMirror integration
- ❌ **JSON Upload**: Only change request JSON, not full configs
- ❌ **Diff Viewer**: MISSING - No visual diff for staged vs live

**Files**:
- `src/core/data_loader.py` (loads expectations)
- `src/core/file_handler.py` (backup/restore)
- `src/updaters/config_updater.py` (apply changes)
- `src/web/api.py` (GET `/api/servers/{server}/config`)

**Missing Features**:
- ❌ Config editor UI with syntax highlighting
- ❌ JSON form builder reading from markdown baselines
- ❌ Individual key edit form (like web GUI key-value editor)
- ❌ Visual diff viewer (side-by-side or unified)
- ❌ Pull config button in GUI
- ❌ Push individual changes to live

---

### 6. **MinIO Storage Integration** ⚠️
**Status**: CONFIGURED BUT NOT TESTED

- ✅ **Settings Configured**: `settings.py` has MinIOConfig dataclass
- ✅ **Environment Variables**: `ARCHIVESMP_MINIO_*` mappings defined
- ⚠️ **Actual Usage**: NOT FOUND in codebase
- ❌ **Pl3xMap Tile Sync**: Mentioned in docs but no implementation found

**Files**:
- `src/core/settings.py` (lines 15-22: MinIOConfig dataclass)

**Questions**:
- Where is MinIO actually used? Pl3xMap tile storage?
- Is MinIO on localhost or needs tunnel to production?
- Do we have credentials configured?

---

### 7. **Premium/Paid Plugin Handling** ⚠️
**Status**: PARTIAL - Detection exists, no automation

- ✅ **Registry Marking**: CMI, CMILib marked as "Premium - Manual Download"
- ✅ **Version Checking**: SpigotMC API works for version numbers
- ❌ **Download Automation**: NOT POSSIBLE (SpigotMC has no auth API)
- ❌ **Source Compilation**: NOT IMPLEMENTED
- ❌ **GUI Workflow**: No "manual download required" badge or instructions

**Plugins Affected**:
- CMI (Zrips Premium)
- CMILib (Zrips Premium)
- Potentially others marked "manual" in PLUGIN_REGISTRY.md

**Recommendation**:
- [ ] Check if CMI/CMILib have public source repos
- [ ] Add "Manual Download Required" badge in GUI
- [ ] Create workflow doc for premium plugin updates

---

### 8. **Custom Development Plugins** ⚠️
**Status**: IDENTIFIED BUT NO CI/CD STRATEGY

From PLUGIN_REGISTRY.md:
- **Eternal Tower Defense** (TOWER01) - Custom minigame
- **ArmoryCrate** - Custom weapon/armor management

**Questions**:
- Are these compiled from source?
- Do they have git repos?
- Should we add GitHub/Jenkins CI for custom plugins?

---

## ❌ WHAT'S MISSING

### 1. **Config Editor GUI** ❌
**Priority**: HIGH

**What's Needed**:
1. **Monaco Editor Integration** (VS Code's editor)
   - Syntax highlighting for YAML/JSON
   - Validation
   - Auto-complete from schema
   
2. **Web Form Builder**
   - Parse markdown baselines (`data/plugin_definitions/*.md`)
   - Generate HTML forms with proper types (text, number, boolean, select)
   - Save back to JSON/YAML
   
3. **Key-Value Editor**
   - Table view with editable cells
   - Add/remove keys
   - Validate against expectations
   
4. **Pull/Push Buttons**
   - "Pull from Live" → fetch current instance config
   - "Push to Live" → deploy edited config
   - Show diff before pushing

**Files to Create**:
- `src/web/static/config_editor.html`
- `src/web/static/config_editor.js`
- Add Monaco CDN or CodeMirror

**API Endpoints Needed**:
- ✅ `GET /api/servers/{server}/config` (EXISTS)
- ❌ `POST /api/servers/{server}/config` (MISSING)
- ❌ `GET /api/plugins/{plugin}/schema` (MISSING - for form generation)

---

### 2. **Diff Viewer** ❌
**Priority**: HIGH

**What's Needed**:
- Visual diff between staged config and live config
- Support for YAML and JSON
- Highlight additions (green), deletions (red), changes (yellow)
- Collapsible sections for large configs

**Libraries**:
- `diff2html` (JavaScript)
- `monaco-editor` (has built-in diff viewer)
- `jsdiff` (lightweight alternative)

**Where to Add**:
- Config editor page (before pushing)
- Deployment review page (before deploying)
- Drift detection view (show what drifted)

---

### 3. **JSON Upload for Full Configs** ❌
**Priority**: MEDIUM

**Current State**:
- Only supports change request JSON (`expected_changes_template.json` format)
- Cannot upload a full plugin config JSON

**What's Needed**:
- Upload button accepting `.json` or `.yml` files
- Parse and validate against plugin schema
- Preview changes before saving
- Option to deploy immediately or stage

---

### 4. **MinIO File Operations** ❌
**Priority**: DEPENDS ON USAGE

**What's Needed** (IF MinIO is for Pl3xMap tiles):
1. Tile upload/download functions
2. Sync utility (local ↔ MinIO ↔ production instances)
3. MinIO client initialization with credentials
4. Health check for MinIO connectivity

**What's Needed** (IF MinIO is for config backups):
1. Backup upload to S3-compatible storage
2. Restore from MinIO backups
3. Retention policy management

**Files to Create/Modify**:
- `src/storage/minio_client.py` (new)
- Integration in `file_handler.py`

---

### 5. **Tunnel Handling** ❌
**Priority**: CRITICAL FOR PRODUCTION

**Questions**:
- Do we need SSH tunnels to access production AMP instances?
- Is MinIO local or remote?
- Are AMP APIs exposed publicly or only localhost?

**Current Deployment Plan** (from docs):
- Hetzner (135.181.212.169): Already deployed with agent
- OVH (37.187.143.41): Not deployed yet

**What's Needed**:
- Document network topology
- SSH tunnel configuration if needed
- VPN or WireGuard setup (if used)
- Firewall rules documentation

---

### 6. **Markdown to Form Parser** ❌
**Priority**: MEDIUM

**Current State**:
- Baselines are markdown files in `data/plugin_definitions/*.md`
- Contains human-readable descriptions, not machine-parseable schemas

**What's Needed**:
1. Parser to extract:
   - Key paths (e.g., `MySQL.Database.Name`)
   - Types (string, number, boolean, list)
   - Default values
   - Descriptions/comments
   
2. Schema generator:
   - Convert markdown → JSON Schema
   - Use for validation and form generation
   
3. Form renderer:
   - Generate HTML forms from schema
   - Handle nested objects
   - Support arrays/lists

**Files to Create**:
- `src/parsers/markdown_schema.py`
- `src/web/static/form_builder.js`

---

### 7. **Source Compilation for Open-Source Paid Plugins** ❌
**Priority**: LOW (Manual workflow acceptable)

**Plugins to Investigate**:
- CMI (check if Zrips has public repo)
- CMILib
- Others marked "Premium" in registry

**What's Needed**:
1. Check if source is available (GitHub, GitLab, BitBucket)
2. If yes, add Jenkins/GitHub Actions CI
3. Auto-compile and deploy to dev
4. Document build process

---

## 🔧 IMMEDIATE ACTION ITEMS

### Priority 1: HIGH - Production Blockers

1. **Fix Drift Detector Type Errors** ⚠️
   - User reported crashes with list/dict comparisons
   - Add type safety checks in `drift_detector.py`
   - Test with actual production configs

2. **Add Config Editor GUI** ❌
   - At minimum: textarea with JSON validation
   - Better: Monaco Editor integration
   - Must have: Pull/Push buttons

3. **Add Diff Viewer** ❌
   - Show changes before deployment
   - Critical for safety (prevent accidental overwrites)

4. **Test Plugin Update Checker** ⚠️
   - Verify all CI/CD endpoints work
   - Test with production plugin list
   - Confirm PLUGIN_REGISTRY.md parsing

### Priority 2: MEDIUM - Enhanced Features

5. **Implement Pull/Push API Endpoints**
   - `POST /api/servers/{server}/config` for pushing individual configs
   - `GET /api/plugins/{plugin}/schema` for form generation

6. **Add Premium Plugin Workflow**
   - GUI badge for "Manual Download Required"
   - Link to Spigot resource page
   - Track manual update status

7. **MinIO Integration Clarification**
   - Determine actual use case (tiles vs backups)
   - Implement client if needed
   - Test connectivity

8. **Network Topology Documentation**
   - Document tunnel requirements
   - SSH access setup
   - Firewall configurations

### Priority 3: LOW - Nice to Have

9. **Markdown Schema Parser**
   - Extract types from baselines
   - Generate JSON Schema
   - Auto-build forms

10. **Custom Plugin CI/CD**
    - Setup build pipeline for Eternal Tower Defense
    - Setup build pipeline for ArmoryCrate
    - Document development workflow

---

## 📊 PLUGIN REGISTRY VERIFICATION

### By CI/CD Source:

| Source | Count | Status |
|--------|-------|--------|
| **Jenkins** | ~15 | ✅ Implemented (CodeMC, EngineHub, md5, dmulloy2, citizensnpcs, extendedclip, loohpjames) |
| **Modrinth** | ~20 | ✅ Implemented (v2 API with game versions) |
| **GitHub** | ~10 | ✅ Existing implementation |
| **SpigotMC** | ~30 | ✅ Implemented (version check only) |
| **Hangar** | ~5 | ✅ Existing implementation |
| **Manual** | ~20 | ⚠️ Detection exists, no automation |
| **Premium** | 2 (CMI, CMILib) | ⚠️ Version check only, manual download |
| **Custom** | 2 (Tower Defense, ArmoryCrate) | ❌ No CI/CD |

**Total Plugins**: ~104 in PLUGIN_REGISTRY.md
**Universal Configs**: 60 (53 Paper, 6 Velocity, 1 Geyser)

### Verification Checklist:

- [ ] All 60 universal config plugins have CI/CD endpoints
- [ ] All endpoints return valid responses
- [ ] Plugin name matching works (registry → installed JARs)
- [ ] Version comparison logic works for all formats
- [ ] Changelog parsing works for all sources

---

## 🌐 DEPLOYMENT VERIFICATION

### What's Deployed on Hetzner (135.181.212.169):

✅ **Running Services**:
- `archivesmp-webapi.service` (Port 8000, 4 workers)
- `homeamp-agent.service` (discovers 11 instances)

✅ **Installation Paths**:
- Software: `/opt/archivesmp-config-manager/`
- Config: `/etc/archivesmp/agent.yaml`
- Data: `/var/lib/archivesmp/`
- Logs: `/var/log/archivesmp/` + `journalctl -u <service>`

⚠️ **Known Issues**:
- Drift detector crashes (type errors)
- Plugin updates not working (needs verification)
- Web UI filtering broken (shows all instances instead of server-specific)

### What's NOT Deployed on OVH (37.187.143.41):

❌ **Nothing deployed yet** - Second server pending

---

## 🔐 SECURITY & CREDENTIALS

### What Needs Secrets:

1. **MinIO** (if used):
   - `ARCHIVESMP_MINIO_ENDPOINT`
   - `ARCHIVESMP_MINIO_ACCESS_KEY`
   - `ARCHIVESMP_MINIO_SECRET_KEY`
   - `ARCHIVESMP_MINIO_BUCKET`

2. **GitHub API** (for releases):
   - `GITHUB_TOKEN` (optional, increases rate limit)

3. **Modrinth API**:
   - No auth required (public API)

4. **SpigotMC Premium**:
   - No API available (manual browser download)

5. **AMP Instances**:
   - SSH keys for access
   - AMP API tokens (if using AMP REST API)

### Where Secrets Should Go:

- ❌ NOT in code/config files
- ✅ Environment variables
- ✅ `/etc/archivesmp/secrets.env` (systemd EnvironmentFile)
- ✅ GitHub Secrets (for CI/CD)

---

## 📝 NEXT STEPS

### Before Production Deployment:

1. **Fix Drift Detector** (CRITICAL)
   ```bash
   # On Hetzner, apply fix via script:
   sudo python3 /opt/archivesmp-config-manager/scripts/fix_drift_detector.py
   sudo systemctl restart homeamp-agent
   ```

2. **Add Config Editor** (HIGH)
   - Create `config_editor.html` with Monaco Editor
   - Add API endpoints for pull/push
   - Test with sample configs

3. **Add Diff Viewer** (HIGH)
   - Integrate `monaco-editor` diff component
   - Add to deployment workflow
   - Add to drift detection view

4. **Test Plugin Checker** (HIGH)
   ```bash
   # Run test script:
   cd /opt/archivesmp-config-manager
   python3 -m pytest tests/test_plugin_checker.py
   ```

5. **Document Network Setup** (MEDIUM)
   - SSH tunnel requirements?
   - MinIO location and access?
   - Firewall rules?

6. **Deploy to OVH** (PENDING)
   - Only after Hetzner is stable
   - Use same deployment process
   - Test cross-server communication

---

## 🎯 SUCCESS CRITERIA

### Minimum Viable Product:

- ✅ Plugin update checking works for all sources
- ✅ Drift detection works without crashes
- ✅ Config editor exists with pull/push
- ✅ Diff viewer shows changes before deployment
- ✅ Deployment pipeline works end-to-end
- ✅ Rollback functionality tested
- ✅ GUI is fully functional
- ✅ Production deployment on Hetzner stable

### Stretch Goals:

- ✅ MinIO integration working
- ✅ Markdown form parser
- ✅ Premium plugin workflow documented
- ✅ Custom plugin CI/CD
- ✅ OVH deployment complete
- ✅ Automated drift checking (systemd timer)

---

**End of Audit** - Generated Nov 14, 2025
