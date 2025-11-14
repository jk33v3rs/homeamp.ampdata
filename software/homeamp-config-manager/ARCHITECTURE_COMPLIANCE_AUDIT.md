# ArchiveSMP Configuration Manager - Architecture Compliance Audit

**Date**: November 6, 2025  
**Architecture Strategy**: Hetzner-Centric with OVH Thin Client

---

## ✅ FINALIZED ARCHITECTURE

### Storage Strategy

**MinIO on Hetzner (YAML, per-plugin structure):**
```
minio://configs/ (hosted on Hetzner, 135.181.212.169:3800)
├── baselines/
│   ├── HuskSync/
│   │   ├── config.yml          # ~600KB per plugin
│   │   ├── server.yml
│   │   └── messages-en.yml
│   ├── LuckPerms/
│   │   └── config.yml
│   └── [~90 plugins]/
└── deviations.yml                # Single file, all instance overrides
```

**MariaDB on Hetzner (135.181.212.169:3369):**
- Drift reports (structured data)
- Deployment history
- Instance metrics (CPU, memory, player count, TPS)
- Config audit log
- **Auth**: Username + password (no SSL, allowPublicKeyRetrieval=true)

**Redis on Hetzner (135.181.212.169:6379):**
- Job queue ONLY (pub/sub for OVH work distribution)
- Heartbeat checks (agent alive status)
- NO persistent data, NO large payloads
- **Auth**: Password protected (username: default)

**Local Filesystem (per server):**
- Error logs only (`/var/log/archivesmp/*.log`)
- systemd journal output
- NO config caching, NO drift report caching

---

### Server Roles

**Hetzner HOST (Everything):**
- Web UI (port 8000) - ALL interactive tools
- MinIO - Config storage, plugin JARs
- MariaDB - Metrics, drift, deployment tracking
- Redis - Job queue
- Host Agent - Orchestrates everything
- **Executes ALL changes via AMP API** (even for OVH instances)

**OVH CLIENT (Thin Agent Only):**
- Lightweight client agent
- Logs data → ships to Hetzner MariaDB
- Provides AMP API credentials to Hetzner
- **Does NOT execute changes** - just passthrough
- **Does NOT cache configs**
- **Does NOT have web UI**

---

## ❌ NON-COMPLIANT COMPONENTS

### 1. **Drift Detector** (`src/analyzers/drift_detector.py`)

**Current Behavior:**
- Scans local filesystem paths (`server_path.exists()`)
- Loads baseline from local directory (`self.baseline_path`)
- Generates JSON report to local filesystem

**Required Changes:**
- [ ] Remove `scan_server_configs()` - Hetzner can't scan OVH filesystem
- [ ] Change baseline loading to **fetch from MinIO** (YAML per-plugin)
- [ ] Fetch live configs via **AMP API** (GetConfigFile endpoint)
- [ ] Store drift reports in **MariaDB**, not local JSON files
- [ ] Add `physical_server` field to all drift items ('hetzner' or 'ovh')

**Affected Lines:**
- Lines 107-176: `scan_server_configs()` assumes local filesystem access
- Lines 35-100: `load_baseline()` reads from local Path, should fetch from MinIO
- Lines 404-437: `generate_drift_report()` writes JSON to local disk

---

### 2. **Agent Service** (`src/agent/service.py`)

**Current Behavior:**
- Discovers local AMP instances only
- Runs as monolithic service
- No concept of physical server separation

**Required Changes:**
- [ ] Split into `host_agent.py` (Hetzner) and `client_agent.py` (OVH)
- [ ] Host agent: Orchestrates work, publishes to Redis, aggregates results
- [ ] Client agent: Subscribes to Redis, executes locally, reports to Hetzner API
- [ ] Remove drift detection from client (Hetzner does it via AMP API)
- [ ] Add physical_server identifier to all operations

**Affected Lines:**
- Lines 1-500: Entire file needs architectural split

---

### 3. **AMP Integration** (`src/amp_integration/amp_client.py`)

**Current Behavior:**
- Connects to single AMP panel URL
- No multi-server support

**⚠️ CRITICAL DECISION REQUIRED:**
**Should we bypass AMP API entirely and manage configs directly via filesystem/SFTP?**

**AMP API Concerns:**
- Developer-opinionated design may create arbitrary restrictions
- "Tentacles into everything" - tight coupling to AMP's logic
- May limit flexibility for our automation needs
- Adds complexity and dependency

**Alternative Approach:**
- **Direct filesystem access via SFTP/SSH** from Hetzner to both servers
- Read/write configs directly to `/home/amp/.ampdata/instances/{instance}/plugins/`
- Restart instances via `systemctl restart amp-{instance}` or AMP CLI
- **Pros**: Full control, no API limitations, simpler
- **Cons**: Bypasses AMP's safety checks, need to handle file locking

**TODO**: 
1. Evaluate AMP API capabilities vs. direct filesystem approach
2. Test both methods on DEV01
3. Document trade-offs and make architecture decision

**If keeping AMP API:**
- [ ] Support multiple AMP endpoints (Hetzner: 135.181.212.169:8080, OVH: 37.187.143.41:8080)
- [ ] Config format: `servers: [{name: 'hetzner', amp_url: '...', credentials: ...}, ...]`
- [ ] Add methods: `get_config_file()`, `set_config_file()`, `list_instances_by_server()`
- [ ] Hetzner agent can connect to **both** AMP panels remotely

**If bypassing AMP API:**
- [ ] Create SSH/SFTP client module (`src/core/ssh_client.py`)
- [ ] Direct config file read/write to AMP instance directories
- [ ] Instance restart via systemd or AMP CLI
- [ ] File locking mechanism to prevent conflicts

**Affected Lines:**
- Entire module may need replacement

---

### 4. **Plugin Automation** (`src/automation/plugin_automation.py`)

**Current Behavior:**
- Checks for updates locally
- Downloads JARs to local filesystem
- Deploys via local AMP API

**Required Changes:**
- [ ] Store plugin JARs in **MinIO**, not local disk
- [ ] Deployment jobs published to **Redis** queue
- [ ] Client agent on OVH subscribes, downloads from MinIO, deploys locally
- [ ] Deployment history stored in **MariaDB**
- [ ] All orchestration from Hetzner

**Affected Lines:**
- JAR download logic needs MinIO integration
- Deployment logic needs Redis job queue

---

### 5. **Config Parser** (`src/core/config_parser.py`)

**Current Behavior:**
- Reads files from local filesystem
- Returns dict/list from YAML/JSON/properties

**Required Changes:**
- [ ] Add method: `load_from_minio(bucket, key)` - fetch YAML from MinIO
- [ ] Add method: `save_to_minio(bucket, key, data)` - upload YAML to MinIO
- [ ] Keep local filesystem methods for backward compatibility (dev/testing)

**Affected Lines:**
- Add MinIO client integration (boto3 or minio-py)

---

### 6. **Config Backup** (`src/core/config_backup.py`)

**Current Behavior:**
- Stores `.bak` files in local `backups/` directory
- Timestamped folder structure

**Required Changes:**
- [ ] Store backups in **MinIO**, not local filesystem
- [ ] Structure: `minio://backups/{physical_server}/{instance}/{plugin}/{timestamp}/`
- [ ] Backup metadata stored in **MariaDB** (timestamp, who, what, why)
- [ ] Restoration downloads from MinIO

**Affected Lines:**
- Lines 50-100: `backup_config()` writes to local Path
- Lines 150-200: `restore_config()` reads from local Path
- Lines 250-280: `list_backups()` scans local filesystem

---

### 7. **Server-Aware Config Engine** (`src/core/server_aware_config.py`)

**Current Behavior:**
- Reads universal configs from `data/baselines/universal_configs/` (local markdown)
- Reads server variables from local Excel file
- Generates configs to local filesystem

**Required Changes:**
- [ ] Read universal configs from **MinIO** (`baselines/{plugin}/config.yml`)
- [ ] Read server variables from **MinIO** (`deviations.yml`)
- [ ] Write generated configs to **MinIO** (per-instance)
- [ ] No local filesystem dependency

**Affected Lines:**
- Lines 100-150: `load_universal_config()` reads local .md files
- Lines 200-250: `apply_server_variables()` reads local Excel
- Lines 300-350: `generate_server_config()` writes to local disk

---

### 8. **Web API** (`src/api/`)

**Current Behavior:**
- Runs on Hetzner (correct)
- Queries local data only

**Required Changes:**
- [ ] Query **MariaDB** for drift reports, metrics, deployment history
- [ ] Fetch configs from **MinIO** (not local disk)
- [ ] Publish deployment jobs to **Redis** (not direct execution)
- [ ] Add endpoint: `POST /api/results` (for OVH client to report data)
- [ ] Add UI indicator: "⚠️ CLIENT UNAVAILABLE" if OVH unreachable

**Affected Lines:**
- All endpoints reading from `data/` directory
- No endpoints for receiving results from OVH client

---

### 9. **Excel Reader** (`src/core/excel_reader.py`)

**Current Behavior:**
- Reads from `data/reference_data/*.xlsx` (local files)

**Required Changes:**
- [ ] Store Excel files in **MinIO** (`reference_data/*.xlsx`)
- [ ] OR convert Excel → YAML and store in MinIO
- [ ] Fetch from MinIO instead of local disk

**Affected Lines:**
- Lines 50-100: `load_deployment_matrix()` reads local file
- Lines 150-200: `load_server_variables()` reads local file

---

### 10. **Configuration Files**

**Current Config:**
```yaml
# /etc/archivesmp/agent.yaml (example)
amp_url: http://localhost:8080
baseline_path: /opt/archivesmp-config-manager/data/baselines
```

**Required Config:**
```yaml
# Hetzner host-agent.yaml
role: host
physical_server: hetzner
amp_servers:
  - name: hetzner
    url: http://135.181.212.169:8080
    username: admin
    password: xxx
  - name: ovh
    url: http://37.187.143.41:8080
    username: admin
    password: xxx
minio:
  endpoint: localhost:3800  # Public: 135.181.212.169:3800
  access_key: xxx
  secret_key: xxx
  secure: false  # Use true if TLS enabled
mariadb:
  host: localhost
  port: 3369
  database: asmp_SQL
  username: sqlworkerSMP
  password: ${MARIADB_PASSWORD}
  ssl: false
  options:
    allowPublicKeyRetrieval: true
redis:
  host: localhost
  port: 6379
  password: ${REDIS_PASSWORD}
  username: default  # Redis default user

# OVH client-agent.yaml
role: client
physical_server: ovh
hetzner_api: https://archivesmp.site:8000
redis:
  host: 135.181.212.169  # Connect to Hetzner Redis
  port: 6379
amp_local:
  url: http://localhost:8080
  username: admin
  password: xxx
```

---

## ✅ COMPLIANT COMPONENTS

### 1. **systemd Services** (Correct deployment model)
- `archivesmp-webapi.service` on Hetzner ✅
- `homeamp-agent.service` on Hetzner ✅
- Need to create `homeamp-client-agent.service` on OVH

### 2. **MinIO Service** (Already on Hetzner)
- Currently running at `127.0.0.1:9001` (console)
- **REQUIRED**: Reconfigure to listen on `135.181.212.169:3800` (API)
- Need firewall rule to allow OVH → Hetzner:3800

### 3. **MariaDB Service** (Already on Hetzner)
- Running at `135.181.212.169:3369` ✅
- Database `asmp_SQL` exists ✅
- Auth: `sqlworkerSMP` / password (no SSL, allowPublicKeyRetrieval=true)
- Need to create new tables for drift reports, deployment history

---

## 📊 MIGRATION CHECKLIST

### Phase 1: Infrastructure Setup (Hetzner)
- [ ] Install Redis on Hetzner (port 6379) with password auth
- [ ] Reconfigure MinIO to listen on public IP (135.181.212.169:3800)
- [ ] Create MariaDB tables (drift_reports, deployment_history, instance_metrics, config_audit)
- [ ] Configure MinIO buckets (configs, backups, reference_data, jars)
- [ ] Upload existing configs to MinIO (convert .md → .yml per-plugin)
- [ ] Configure YunoHost reverse proxy (HTTPS) for MinIO/Web API (optional)
- [ ] Firewall: Allow OVH → Hetzner MinIO (port 3800)
- [ ] Firewall: Allow OVH → Hetzner Redis (port 6379)
- [ ] Firewall: Allow OVH → Hetzner MariaDB (port 3369)

### Phase 2: Code Refactoring
- [ ] Create MinIO integration module (`src/storage/minio_client.py`)
- [ ] Create MariaDB integration module (`src/storage/db_client.py`)
- [ ] Create Redis integration module (`src/queue/redis_client.py`)
- [ ] Refactor drift_detector.py (AMP API + MinIO baselines)
- [ ] Refactor config_backup.py (MinIO storage)
- [ ] Refactor server_aware_config.py (MinIO baselines + deviations)
- [ ] Split agent/service.py → host_agent.py + client_agent.py

### Phase 3: Testing (Hetzner Only)
- [ ] Test drift detection via AMP API
- [ ] Test config backup/restore via MinIO
- [ ] Test deployment history in MariaDB
- [ ] Test web UI with new storage backend

### Phase 4: OVH Client Deployment
- [ ] Package client agent for OVH
- [ ] Deploy client-agent.yaml to OVH
- [ ] Test Redis job queue (publish from Hetzner, execute on OVH)
- [ ] Test result reporting (OVH → Hetzner API)
- [ ] Verify "⚠️ CLIENT UNAVAILABLE" banner when OVH down

### Phase 5: Validation
- [ ] Run drift scan across all ~20 instances
- [ ] Verify web UI shows both Hetzner and OVH instances
- [ ] Test plugin deployment to OVH instances via Hetzner
- [ ] Verify all data stored in MinIO/MariaDB, not local disk

---

## 🔍 DRIFT SCAN VALIDATION (Informal Test)

**Goal**: Scan all ~90 plugins across ~20 instances to identify "odd one out" settings

**Example Issue**: One instance has `CMI.ReSpawn.Enabled = false` while all others have `true`

**Current Problem**: 
- Drift detector scans local filesystem only
- Baselines are markdown files, not parsed YAML
- No cross-server scanning capability
- No "detect outliers" logic (finds 1 instance different from the other 19)

**Required Fix BEFORE running scan:**
1. Convert `data/baselines/universal_configs/*.md` → MinIO `baselines/{plugin}/config.yml`
2. Rewrite drift detector to use AMP API `GetConfigFile()`
3. Add MariaDB storage for drift reports
4. Test on Hetzner instances first, then extend to OVH

**Once fixed, run:**
```bash
# On Hetzner (via host agent)
python -m src.agent.host_agent scan-drift --server=hetzner --all-instances
python -m src.agent.host_agent scan-drift --server=ovh --all-instances

# View results in web UI
curl http://localhost:8000/api/drift?server=all&severity=high
```

Expected output: Detailed drift report showing which instances have config deviations from baseline

---

## 📝 SUMMARY

**Non-Compliant Files**: 10  
**Major Refactoring Needed**: drift_detector.py, agent/service.py, config_backup.py, server_aware_config.py  
**New Components Needed**: MinIO client, MariaDB schema, Redis queue, client agent  
**Estimated Effort**: 20-24 hours development + 8-12 hours testing

**Critical Path**:
1. Set up MinIO/MariaDB/Redis on Hetzner
2. Refactor drift detector to use AMP API + MinIO
3. Test on Hetzner instances
4. Deploy client to OVH
5. Validate end-to-end

**No caching on OVH, all storage on Hetzner, OVH is thin passthrough client.**
