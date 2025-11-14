# CONCEPT GROUPING - Pass 3: Organizing Knowledge for Deployment

**Status**: PASS 3 - Grouping definite facts into semantic clusters  
**Generated**: 2025-11-13  
**Method**: Apply semantic clusters from 01_SEMANTIC_CLUSTERS.md to definite facts from 06_DEFINITE_FACTS.md  
**Purpose**: Create organized knowledge base for deployment planning  

---

## IDEA 1: PHYSICAL INFRASTRUCTURE

**What we have**: Two bare metal Debian servers running AMP Panel

### HETZNER_RESOURCE (Primary - Hosting Server)
- **IP**: 135.181.212.169
- **Domain**: archivesmp.site
- **Role**: HOST (provides shared services + runs agent)
- **Hardware**: Xeon processor
- **AMP Instances**: 11 Minecraft game servers
  - ADS01, BIG01, CAR01, DEV01, EVO01, MIN01, PRI01, ROY01, SMP101, SUNK01, TOW01
- **AMP Panel**: Port 8080
- **Instance Path**: `/home/amp/.ampdata/instances/`
- **Status**: Previously deployed, uninstalled Nov 4, ready for fresh deployment

### OVH_RESOURCE (Secondary - Client Server)
- **IP**: 37.187.143.41
- **Domain**: archivesmp.online
- **Role**: CLIENT (consumes services from host, runs agent locally)
- **Hardware**: Ryzen processor
- **AMP Instances**: 12 total (9 game servers + 3 infrastructure)
  - **Controller**: ADS01
  - **Proxy**: VEL01 (Velocity with ViaVersion + ViaBackwards)
  - **Bedrock**: GEY01 (Geyser-Standalone for bedrock compatibility)
  - **Game Servers** (9): BENT01, CLIP01, CREA01, CSMC01, EMAD01, HARD01, HUB01, MINE01, SMP201
- **AMP Panel**: Port 8080
- **Instance Path**: `/home/amp/.ampdata/instances/`
- **Status**: Never had homeamp software deployed, agent deployment pending

### Network Access Requirements
- **Both servers**: Outbound HTTPS to GitHub, Spigot, Hangar (plugin updates)
- **OVH → Hetzner**: Port 3800 (MinIO message bus)
- **Optional**: SSH access for deployment (22), Web UI access (8000)

---

## IDEA 2: DISTRIBUTED ARCHITECTURE

**What we're building**: Multi-server management with centralized control

### HOST_RESOURCE (Services Provided BY Hetzner)
**Shared services that CLIENT (OVH) consumes:**

1. **MinIO (Message Bus)** - Port 3800
   - **Purpose**: Asynchronous communication between agents and web API
   - **Buckets**:
     - `archivesmp-changes`: Change requests from web UI
     - `archivesmp-drift-reports`: Drift detection results from agents
     - `archivesmp-backups`: Configuration backups before changes
   - **Access**: Both agents poll for work, upload results
   - **Firewall-friendly**: Agents only need outbound to MinIO (no exposed ports)

2. **MariaDB (Database)** - Port 3369
   - **Purpose**: Persistent storage for deployment history, change logs
   - **Schema**: TBD (needs migration)

3. **Redis (Cache)** - Port 6379
   - **Purpose**: Session state, job queue management
   - **Usage**: Fast lookups, temporary data

4. **Web API (Control Plane)** - Port 8000
   - **Purpose**: Single HTTP API and web UI for managing both servers
   - **Framework**: FastAPI with 4 uvicorn workers
   - **Endpoints**: Create changes, view drift reports, approve deployments
   - **Service**: `archivesmp-webapi.service` (Hetzner ONLY)

### CLIENT_RESOURCE (Services ON Each Server)
**What each server manages locally:**

1. **homeamp-agent.service** (One Per Server)
   - **Hetzner Agent**: Discovers/manages 11 local instances
   - **OVH Agent**: Discovers/manages 12 local instances
   - **Function**: 
     - Scan `/home/amp/.ampdata/instances/` for AMP instances
     - Check drift against baselines
     - Poll MinIO for change requests
     - Execute changes via local AMP API (localhost:8080)
     - Upload results to MinIO
   - **Config**: `/etc/archivesmp/agent.yaml` with `server_name` (unique per server)
   - **Communication**: MinIO only (no direct agent-to-agent or agent-to-API)

2. **AMP Panel Integration**
   - **Local AMP API**: `http://localhost:8080` on each server
   - **AMPClient**: Network-capable but each agent uses local endpoint
   - **Methods**: start(), stop(), restart(), upload_file() via HTTP

### Communication Flow
```
┌─────────────────────────────────────────────────────────┐
│ USER → Web UI (Hetzner:8000)                           │
│   "Deploy config change to OVH instances"              │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Web API → MinIO (Hetzner:3800)                         │
│   Upload change request JSON to archivesmp-changes/    │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌────────────────┐      ┌────────────────┐
│ Hetzner Agent  │      │ OVH Agent      │
│ Poll MinIO     │      │ Poll MinIO     │
│ Download job   │      │ Download job   │
│ Execute local  │      │ Execute local  │
│ Upload result  │      │ Upload result  │
└────────────────┘      └────────────────┘
        │                       │
        └───────────┬───────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│ Web UI polls MinIO for results                          │
│   Display success/failure to user                       │
└─────────────────────────────────────────────────────────┘
```

### Why This Architecture
- **Firewall-friendly**: Agents only need outbound (no exposed ports)
- **Asynchronous**: Web UI doesn't wait for agents (job queue model)
- **Independent**: Agents work on their local servers, no cross-server dependencies
- **Scalable**: Add more servers by deploying agent + pointing to same MinIO
- **Simple**: Each agent only knows about its local filesystem

---

## IDEA 3: SOFTWARE DEPLOYMENT

**Where code lives**: Development → Production

### Development Environment
- **Location**: `e:\homeamp.ampdata\` (Windows PC)
- **Source Code**: `e:\homeamp.ampdata\software\homeamp-config-manager\`
- **Structure**: 32 Python files, 11,371 lines, 48 classes, 8 entry points
- **Status**: All 4 known bugs FIXED in source code

### Production Deployment (Both Servers)
- **Path**: `/opt/archivesmp-config-manager/`
- **Contents**:
  - `src/` - Python source code
  - `data/universal_configs/` - 57 plugin baseline configs (markdown)
  - `data/deployment_matrix.csv` - Plugin-to-server mapping
  - `data/Master_Variable_Configurations.xlsx` - Server-specific variables
  - `requirements.txt` - Python dependencies (TO BE CREATED)
- **Services**:
  - **Hetzner**: agent + webapi
  - **OVH**: agent only

### Dependencies (Must Install)
**Required** (9 packages):
1. `fastapi` - Web framework
2. `pydantic` - Data validation
3. `minio` - S3 storage client
4. `pandas` - Excel reading
5. `openpyxl` - Excel writing
6. `pyyaml` - YAML parsing
7. `requests` - HTTP client
8. `aiohttp` - Async HTTP
9. `prometheus_client` - Metrics

**Optional** (2 packages):
10. `pulumi` - Infrastructure as code
11. `pulumi_aws` - AWS provider

### Systemd Services
**homeamp-agent.service** (both servers):
```ini
[Unit]
Description=ArchiveSMP Configuration Agent
After=network.target

[Service]
Type=simple
User=amp
WorkingDirectory=/opt/archivesmp-config-manager
ExecStart=/usr/bin/python3 -m src.agent.service
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**archivesmp-webapi.service** (Hetzner only):
```ini
[Unit]
Description=ArchiveSMP Web API
After=network.target

[Service]
Type=simple
User=amp
WorkingDirectory=/opt/archivesmp-config-manager
ExecStart=/usr/bin/uvicorn src.web.api:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Agent Configuration
**Location**: `/etc/archivesmp/agent.yaml`

**Hetzner**:
```yaml
server_name: hetzner-xeon
minio:
  endpoint: localhost:3800
  access_key: REDACTED
  secret_key: REDACTED
  secure: false
amp:
  base_url: http://localhost:8080
  username: admin
  password: REDACTED
data_dir: /opt/archivesmp-config-manager/data
```

**OVH**:
```yaml
server_name: ovh-ryzen
minio:
  endpoint: 135.181.212.169:3800
  access_key: REDACTED
  secret_key: REDACTED
  secure: false
amp:
  base_url: http://localhost:8080
  username: admin
  password: REDACTED
data_dir: /opt/archivesmp-config-manager/data
```

---

## IDEA 4: CONFIGURATION MANAGEMENT

**How configs work**: Templates → Variables → Deployment

### BASELINE_DATA (Universal Configs)
**Location**: `data/universal_configs/` (57 .md files)

**Examples**:
- `CMI_universal_config.md` (1,709 lines)
- `Citizens_universal_config.md`
- `EliteMobs_universal_config.md`

**Format**: Markdown with embedded YAML blocks
```markdown
# CMI Plugin Configuration

## settings.yml
```yaml
Economy:
  MainCurrency:
    DecimalPlaces: 2
    Server:
      Account: ServerAccount
      Port: {{SERVER_PORT}}
```
```

**Deployment**: Ships with software at `/opt/archivesmp-config-manager/data/universal_configs/`

### VARIANCE_DATA (Server-Specific Variables)
**Location**: `data/Master_Variable_Configurations.xlsx`

**Variables** (examples):
- `{{SERVER_PORT}}`: 25565, 25566, 25567, etc.
- `{{SERVER_IP}}`: 135.181.212.169 or 37.187.143.41
- `{{DATABASE_NAME}}`: Server-specific database name
- `{{WORLD_NAME}}`: world, world_nether, world_the_end

**Substitution**: `core/server_aware_config.py:apply_server_variables()` replaces `{{VAR}}` with values from Excel

### Deployment Matrix
**Location**: `data/deployment_matrix.csv`

**Purpose**: Maps which plugins deploy to which servers/instances

**Example**:
```csv
Plugin,Hetzner,OVH,DEV01,BENT01,GEY01,VEL01
CMI,✓,✓,✓,✓,✗,✗
Geyser,✗,✓,✗,✗,✓,✗
ViaVersion,✗,✓,✗,✗,✗,✓
```

### Drift Detection
**Process**:
1. Agent scans `/home/amp/.ampdata/instances/{INSTANCE}/Minecraft/plugins/`
2. Reads current config files (YAML/JSON)
3. Compares to baseline from `universal_configs/`
4. Applies variables from `Master_Variable_Configurations.xlsx`
5. Detects differences (drift)
6. Uploads report to MinIO

**Analyzer**: `src/analyzers/drift_detector.py` (568 lines, bug-free)

---

## IDEA 5: PLUGIN UPDATE SYSTEM

**How plugins stay current**: Three update mechanisms

### 1. PluginChecker (Auto-Discovery)
**File**: `src/updaters/plugin_checker.py` (443 lines)

**Sources**:
- **GitHub Releases**: Direct API checks
- **SpigotMC**: Web scraping + API
- **Hangar (PaperMC)**: API integration

**Output**: List of available updates with download URLs

### 2. BedrockUpdater (Specialized)
**File**: `src/updaters/bedrock_updater.py` (527 lines)

**Targets**:
- **Geyser** (GEY01 instance on OVH)
- **Floodgate** (bedrock authentication)
- **ViaVersion + ViaBackwards** (VEL01 proxy on OVH)

**NEW REQUIREMENT**: Web UI button for Geyser updates
- Update Geyser-Standalone on GEY01
- Auto-cascade update to ViaVersion/ViaBackwards on VEL01
- Status: **NOT YET IMPLEMENTED**

### 3. PluginUpdateMonitor (Staging Area)
**File**: `src/automation/pulumi_update_monitor.py` (595 lines)

**Function**: 
- Monitors staging directory for new plugin JARs
- Generates Excel reports of pending updates
- Tracks version changes

**Note**: This is monitoring/reporting, not execution

### Update Flow
```
1. PluginChecker → Detect available updates
2. BedrockUpdater → Download to staging area
3. PluginUpdateMonitor → Generate update report
4. Human approval → Review report
5. DeploymentPipeline → Apply to DEV01 first
6. Validation → Test on DEV01
7. Production approval → Deploy to prod instances
```

---

## IDEA 6: DEPLOYMENT PIPELINE

**How changes reach production**: DEV01 → Validation → Production

### Pipeline Stages (Implemented)
**File**: `src/deployment/pipeline.py` (584 lines)

**States**:
1. **CREATED**: Change request submitted
2. **DEV_PENDING**: Queued for DEV01 deployment
3. **DEV_IN_PROGRESS**: Being deployed to DEV01
4. **DEV_COMPLETE**: Successfully deployed to DEV01
5. **PROD_APPROVED**: Human approved for production
6. **PROD_IN_PROGRESS**: Being deployed to prod instances
7. **PROD_COMPLETE**: Deployment complete

### DEV01 Instance (Hetzner)
**Purpose**: Testing ground before production
- Test plugin updates
- Test config changes
- Validate drift detection
- Ensure no crashes

**Status**: Pipeline implemented but **NEEDS TESTING**

### Production Deployment
**Method**:
1. Change request uploaded to MinIO
2. Agent polls MinIO
3. Agent downloads request
4. Agent executes via AMP API
5. Agent uploads result to MinIO
6. Web UI retrieves result

**Rollback**: Backups stored in MinIO `archivesmp-backups/` bucket before changes

---

## IDEA 7: DATA MANAGEMENT

**What data exists and where**

### Critical Runtime Data (3 files)
1. **deployment_matrix.csv**
   - Location: `data/` (production), `utildata/ActualDBs/` (dev)
   - Used by: `core/excel_reader.py:load_deployment_matrix()`
   - Purpose: Plugin-to-server mapping
   - Status: ✅ EXISTS

2. **Master_Variable_Configurations.xlsx**
   - Location: `data/` (production), `utildata/` (dev)
   - Used by: `core/excel_reader.py:load_server_variables()`
   - Purpose: Server-specific variable substitutions
   - Status: ✅ EXISTS

3. **universal_configs/*.md** (57 files)
   - Location: `data/universal_configs/` (production), `utildata/plugin_universal_configs/` (dev)
   - Used by: `core/data_loader.py:load_universal_plugin_configs()`
   - Purpose: Baseline configuration templates
   - Status: ✅ EXISTS

### Legacy Data (Can Be Deleted)
**Excel files** (4 files):
- `ArchiveSMP_MASTER_WITH_VIEWS.xlsx`
- `Plugin_Configurations.xlsx`
- `Plugin_Detailed_Configurations.xlsx`
- `Plugin_Implementation_Matrix.xlsx`

**Why delete**: Markdown universal_config files are superior
- Human-readable (plain text)
- Git-trackable (meaningful diffs)
- More detailed (1,700+ lines per plugin vs Excel rows)
- Actually used by code (Excel not imported)

**Status**: ✅ SAFE TO ARCHIVE/DELETE

### Development Artifacts (Not Runtime)
**JSON analysis files** (4 files):
- `universal_configs_analysis.json`
- `universal_configs_analysis_UPDATED.json`
- `variable_configs_analysis.json`
- `variable_configs_analysis_UPDATED.json`

**Purpose**: Development analysis, not production use
**Status**: Keep in dev, don't deploy to production

### Snapshot Data (Historical Reference)
**HETZNER_amp_config_snapshot/** and **11octSNAPSHOTovh/**
- **Date**: October 11, 2025 (33 days old)
- **State**: Pre-uninstall AMP configurations
- **Use**: Reference for baseline configs
- **Status**: Extract learnings, then ✅ SAFE TO DELETE

**ReturnedData/** (Hetzner deployment backup):
- **Date**: November 4, 2025 (9 days old)
- **State**: Snapshot taken moments before uninstalling services
- **Use**: Extract systemd service files, config patterns
- **Status**: Extract learnings, then ✅ SAFE TO DELETE

---

## IDEA 8: EXTERNAL INTEGRATIONS

**Systems we talk to**

### AMP Panel (Local)
**Integration**: `src/amp_integration/amp_client.py`

**Capabilities**:
- `get_instances()`: List all AMP instances
- `start(instance_id)`: Start Minecraft server
- `stop(instance_id)`: Stop Minecraft server
- `restart(instance_id)`: Restart Minecraft server
- `upload_file(instance_id, local_path, remote_path)`: Upload config files

**Connection**:
- **Hetzner agent**: `http://localhost:8080`
- **OVH agent**: `http://localhost:8080`
- Network-capable but each agent uses local endpoint

### Plugin Repositories (Remote)
**Integrations**:
1. **GitHub API**: Direct release checks
2. **SpigotMC**: Web scraping + API
3. **Hangar (PaperMC)**: API integration
4. **GeyserMC**: Bedrock compatibility updates

**Network Requirements**: Outbound HTTPS from both servers

### MinIO (Message Bus)
**Integration**: `src/core/cloud_storage.py`

**Buckets**:
- `archivesmp-changes`: Change requests (Web UI → Agents)
- `archivesmp-drift-reports`: Drift reports (Agents → Web UI)
- `archivesmp-backups`: Configuration backups (before changes)

**Access Pattern**: Poll-based (agents check for new objects periodically)

---

## IDEA 9: MONITORING & OBSERVABILITY

**How we know what's happening**

### Metrics (Implemented)
**File**: `src/utils/metrics.py`

**Framework**: Prometheus client

**Metrics to Track**:
- Drift detection runs (success/failure)
- Config changes deployed
- Plugin updates applied
- Agent uptime
- API request rates

**Status**: Infrastructure present, needs Prometheus server deployment

### Logging
**Framework**: Python standard logging

**Levels**:
- ERROR: Failures, exceptions
- WARNING: Drift detected, update available
- INFO: Operations starting/completing
- DEBUG: Detailed execution traces

**Output**: Systemd journal (view with `journalctl -u homeamp-agent`)

### Health Checks
**Needs Implementation**:
- Agent heartbeat to MinIO
- Web API health endpoint
- AMP Panel connectivity check
- Database connectivity check

---

## IDEA 10: KNOWN ISSUES & FIXES

**What was broken, what's fixed**

### Bug 1: Drift Detector TypeError ✅ FIXED
**Location**: `src/analyzers/drift_detector.py:203`

**Problem**: Missing `isinstance(current_plugin, dict)` check caused crashes when plugin data was malformed

**Fix**: Added type check before dictionary access
```python
if not isinstance(current_plugin, dict):
    continue
```

**Status**: ✅ FIXED in source code

### Bug 2: IP Address Parsed as Float ✅ FIXED
**Location**: `src/core/config_parser.py:75`

**Problem**: IP addresses like "192.168.1.1" were being parsed as floats because they contain dots

**Fix**: Check for exactly one dot AND verify it's a number, leave IP addresses as strings
```python
elif '.' in value and value.replace('.', '', 1).isdigit() and value.count('.') == 1:
    value = float(value)  # Only single decimal, not IP addresses
```

**Status**: ✅ FIXED in source code

### Bug 3: UTF-8 BOM Encoding ✅ FIXED
**Location**: `src/core/config_parser.py`

**Problem**: Files with UTF-8 BOM markers caused parsing failures

**Fix**: Handle BOM in file reading (encoding='utf-8-sig')

**Status**: ✅ FIXED in source code

### Bug 4: Duplicate DriftDetector Initialization ✅ FIXED
**Location**: `src/agent/service.py:323`

**Problem**: DriftDetector was being initialized multiple times, causing memory leaks

**Fix**: Check if already initialized before creating new instance
```python
if not hasattr(self, 'drift_detector') or not self.drift_detector:
    self.drift_detector = DriftDetector(baseline_path)
```

**Status**: ✅ FIXED in source code

### Hotfix Script Obsolete
**File**: `production-hotfix-v2.sh`

**Status**: All 4 bugs fixed in source code, script is ✅ SAFE TO DELETE

---

## IDEA 11: BLOCKERS & MISSING COMPONENTS

**What must be created before deployment**

### 1. requirements.txt ❌ MISSING (CRITICAL)
**Contents**:
```
fastapi>=0.104.0
pydantic>=2.5.0
minio>=7.2.0
pandas>=2.1.0
openpyxl>=3.1.0
pyyaml>=6.0.1
requests>=2.31.0
aiohttp>=3.9.0
prometheus-client>=0.19.0

# Optional
pulumi>=3.97.0
pulumi-aws>=6.13.0
```

**Priority**: CRITICAL - Cannot deploy without this

### 2. Installation Guide ❌ MISSING (CRITICAL)
**Contents Needed**:
- System requirements (Debian version, Python 3.x)
- External service setup (MinIO, MariaDB, Redis)
- Deployment steps for Hetzner
- Deployment steps for OVH
- Agent configuration examples
- Verification steps

**Priority**: CRITICAL - Operators need this to deploy

### 3. agent.yaml Template ❌ NEEDS DOCUMENTATION (HIGH)
**Current Status**: Format known from code, but no documented template

**Needed**: Example configurations with explanations

**Priority**: HIGH - Deployment will fail without correct config

### 4. API Documentation ❌ MISSING (MEDIUM)
**Contents Needed**:
- Available endpoints
- Request/response formats
- Authentication (if any)
- Example curl commands

**Priority**: MEDIUM - Web UI provides interface, but API docs helpful

---

## IDEA 12: NEW FEATURES TO IMPLEMENT

**What users requested but doesn't exist yet**

### Geyser Update Function ⚠️ NOT IMPLEMENTED
**User Requirement**: "Geyser from GeyserMC should have a function accessible through the webui which allows it to be updated independently"

**Components**:
1. **Web UI Button**: Trigger Geyser update
2. **Update Logic**:
   - Check GeyserMC releases API
   - Download latest Geyser-Standalone JAR
   - Deploy to GEY01 instance (OVH)
3. **Cascade Logic**:
   - Detect ViaVersion plugin on VEL01 (OVH proxy)
   - Detect ViaBackwards plugin on VEL01
   - Auto-update both when Geyser updates (compatibility requirement)
4. **Status Display**: Show update progress in web UI

**Priority**: User-requested feature

**Status**: ⚠️ NOT YET IMPLEMENTED

---

## IDEA 13: CLEANUP TASKS

**What to delete after completing Pass 3**

### 1. production-hotfix-v2.sh
**Reason**: All 4 bugs fixed in source code
**Status**: ✅ SAFE TO DELETE immediately

### 2. ReturnedData/ Backup
**Reason**: "Get rid of it immediately so it doesn't clutter context"
**Action**:
1. Extract systemd service file formats (if not already documented)
2. Note production config patterns (if not already captured)
3. DELETE entire directory

**Status**: ⏳ Extract learnings first, then DELETE

### 3. Legacy Excel Files (4 files)
**Files**:
- ArchiveSMP_MASTER_WITH_VIEWS.xlsx
- Plugin_Configurations.xlsx
- Plugin_Detailed_Configurations.xlsx
- Plugin_Implementation_Matrix.xlsx

**Reason**: Markdown universal_config files are superior (1,700+ lines per plugin, git-trackable, human-readable)

**Status**: ✅ SAFE TO ARCHIVE/DELETE immediately

### 4. HETZNER_amp_config_snapshot/
**Reason**: "Done with that Hetzner stuff and its learnings are integrated"
**Action**:
1. Confirm baseline configs extracted to universal_configs/
2. DELETE entire directory

**Status**: ⏳ Confirm learnings integrated, then DELETE

### 5. 11octSNAPSHOTovh/
**Reason**: 33 days old, baselines already extracted
**Status**: ✅ SAFE TO DELETE after confirming OVH instance names documented

---

## DEPLOYMENT CHECKLIST

### Prerequisites (Before Deployment)
- [ ] Create requirements.txt
- [ ] Write installation guide
- [ ] Document agent.yaml format
- [ ] Verify MinIO running on Hetzner (port 3800)
- [ ] Verify MariaDB running on Hetzner (port 3369)
- [ ] Verify Redis running on Hetzner (port 6379)

### Hetzner Deployment
- [ ] Install Python 3 and pip
- [ ] Install dependencies from requirements.txt
- [ ] Copy code to `/opt/archivesmp-config-manager/`
- [ ] Copy universal_configs/ to `/opt/archivesmp-config-manager/data/`
- [ ] Copy deployment_matrix.csv to `/opt/archivesmp-config-manager/data/`
- [ ] Copy Master_Variable_Configurations.xlsx to `/opt/archivesmp-config-manager/data/`
- [ ] Create `/etc/archivesmp/agent.yaml` with server_name=hetzner-xeon
- [ ] Install homeamp-agent.service (systemd)
- [ ] Install archivesmp-webapi.service (systemd)
- [ ] Start both services
- [ ] Verify agent discovers 11 instances
- [ ] Verify web UI accessible on port 8000

### OVH Deployment
- [ ] Install Python 3 and pip
- [ ] Install dependencies from requirements.txt
- [ ] Copy code to `/opt/archivesmp-config-manager/`
- [ ] Copy universal_configs/ to `/opt/archivesmp-config-manager/data/`
- [ ] Copy deployment_matrix.csv to `/opt/archivesmp-config-manager/data/`
- [ ] Copy Master_Variable_Configurations.xlsx to `/opt/archivesmp-config-manager/data/`
- [ ] Create `/etc/archivesmp/agent.yaml` with server_name=ovh-ryzen, minio endpoint=135.181.212.169:3800
- [ ] Install homeamp-agent.service (systemd)
- [ ] Start service
- [ ] Verify agent discovers 12 instances
- [ ] Verify agent can reach Hetzner MinIO (port 3800)

### Verification
- [ ] Both agents reporting heartbeat
- [ ] Drift detection running on both servers
- [ ] Web UI shows instances from both servers
- [ ] Can deploy config change to DEV01 (Hetzner)
- [ ] Can deploy config change to BENT01 (OVH)
- [ ] MinIO buckets receiving data from both agents

### Post-Deployment Cleanup
- [ ] Delete production-hotfix-v2.sh
- [ ] Delete ReturnedData/ backup
- [ ] Archive/delete 4 legacy Excel files
- [ ] Delete HETZNER_amp_config_snapshot/
- [ ] Delete 11octSNAPSHOTovh/

---

## SUMMARY: IDEAS FOR DEPLOYMENT PLANNING

**13 semantic idea clusters organized:**

1. **Physical Infrastructure**: Two bare metal servers (Hetzner + OVH), 23 AMP instances total
2. **Distributed Architecture**: Agents + Web API + MinIO message bus
3. **Software Deployment**: Code structure, dependencies, systemd services
4. **Configuration Management**: Baselines, variables, drift detection
5. **Plugin Update System**: Auto-discovery, bedrock compatibility, staging
6. **Deployment Pipeline**: DEV01 testing, production approval, rollback
7. **Data Management**: Runtime files, legacy cleanup, snapshots
8. **External Integrations**: AMP API, plugin repos, MinIO
9. **Monitoring & Observability**: Metrics, logging, health checks
10. **Known Issues & Fixes**: All 4 bugs fixed, hotfix script obsolete
11. **Blockers & Missing Components**: requirements.txt, installation guide, docs
12. **New Features**: Geyser update function (not yet implemented)
13. **Cleanup Tasks**: 5 items to delete after deployment

**Ready for deployment planning once blockers resolved.**

---

*Pass 3 Complete. Knowledge organized. Deployment checklist created.*
