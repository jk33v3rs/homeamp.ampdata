# ArchiveSMP Configuration Manager - Distributed Architecture Design

**Date**: November 6, 2025  
**Status**: ARCHITECTURAL REDESIGN REQUIRED

---

## CONFIRMED FACTS

### Terminology Corrections Applied

**Physical Servers (Bare Metal):**
- **Hetzner** (archivesmp.site, 135.181.212.169) - More cores (slower), better for background/web services
- **OVH** (archivesmp.online, 37.187.143.41) - Fewer cores (faster), primary gaming server

**Gaming Context Nomenclature:**
- **PRIMARY Gaming Server**: OVH (hosts velocity proxy, geyser standalone, floodgate auth, game instances)
- **SECONDARY Gaming Server**: Hetzner (additional game instances)

**Plugin Management Context Nomenclature:**
- **HOST Server**: Hetzner (runs main operational software, web UI, orchestration)
- **CLIENT Server**: OVH (reports to Hetzner, no web UI, lighter footprint)

### Verified Data Structure

**From `universal_configs_analysis.json`** (5,294 lines):
- Contains ~90 plugins with their universal/common settings
- Format: `{plugin_name: {setting_key: value}}` where value is **identical across ALL instances with that plugin**
- Example: AxiomPaper has 44 universal settings, bStats has 2 universal settings
- This represents the **common core** - settings that are THE SAME for every instance using that plugin

**From `variable_configs_analysis.json`** (1,307 lines):
- Contains settings that **DEVIATE** from universal configs
- Format: `{plugin_name: {setting_key: {instance_name: instance_specific_value}}}`
- Example: bStats.serverUuid varies by instance (BENT01, BIG01, CLIP01, etc.)
- Example: CMI.ReSpawn.Enabled is true for some instances, false for others
- This represents **per-instance deviations** from the common core

**From `deployment_matrix.csv`**:
- 138 rows (plugins)
- Columns: plugin_name, plugin_type, auto_update, update_source, then 23 server/instance columns
- Server instances identified: GEYSER, VEL01, SMP201, HUB01, EMAD01, SMPC01, NEOC01, BENT01, CLIP01, CSMC01, HC01, MINE01, EVO01, TOWER01, DEV01, MINI01, BIGG01, FORT01, PRIV01, CRAF01
- ~90 unique plugins across all instances
- **NOT all plugins are on all instances** (matrix shows deployment per instance)

**Instance Count**: Approximately 17-20 game instances across both physical servers

---

## ARCHITECTURAL PROBLEM: CURRENT DESIGN IS HOST-CENTRIC

### Current (Broken) Architecture

```
[Hetzner Server]
  ├── homeamp-agent.service (discovers local instances only)
  ├── archivesmp-webapi.service (web UI)
  ├── Plugin automation
  ├── Drift detection (scans local paths only)
  └── Config management (local only)

[OVH Server]
  ├── 11+ game instances (UNREACHABLE by current system)
  └── No management agent installed
```

**CRITICAL FLAW**: The agent on Hetzner can only discover and manage instances on Hetzner. OVH instances are invisible to the system.

---

## REQUIRED DISTRIBUTED ARCHITECTURE

### Proposed Client-Server Model

```
[Hetzner HOST Server] - Plugin Management HOST
  ├── archivesmp-webapi.service (web UI, orchestration, approval workflow)
  ├── homeamp-coordinator.service (NEW - orchestrates clients)
  ├── Redis (shared state, job queue)
  ├── MariaDB (persistent storage, config history, drift reports)
  ├── MinIO (file storage for JARs, backups, reports)
  └── homeamp-host-agent.service (manages local Hetzner instances)

[OVH CLIENT Server] - Reports to Hetzner
  ├── homeamp-client-agent.service (NEW - lightweight client)
  ├── Redis client (subscribes to job queue)
  ├── Reports to Hetzner API endpoint
  └── No web UI, no orchestration
```

### Communication Flow

```
1. Hetzner Coordinator → Publishes job to Redis queue
2. OVH Client Agent → Subscribes to Redis, receives job
3. OVH Client Agent → Executes locally (drift scan, plugin deploy, etc.)
4. OVH Client Agent → Reports results back to Hetzner API
5. Hetzner HOST → Stores results in MariaDB
6. Web UI on Hetzner → Displays unified view of both servers
```

---

## COMPONENTS REQUIRING REDESIGN

### 1. Agent Service (`src/agent/service.py`)

**Current**: Monolithic agent that discovers and manages local instances only

**Required**:
- **Host Agent** (Hetzner): Full-featured, orchestrates work distribution
- **Client Agent** (OVH): Lightweight, executes jobs from queue, reports back

**Shared Code**: Config parser, drift detector, AMP client, backup manager

**Separation**:
- Host: Job scheduling, web API integration, coordination logic
- Client: Job execution, result reporting, no orchestration

### 2. Drift Detector (`src/analyzers/drift_detector.py`)

**Current**: Scans local filesystem paths only

**Required**:
- Must work on both HOST and CLIENT
- Client runs scans locally, serializes results
- Client sends results to HOST via API
- HOST aggregates drift reports from multiple servers

**Changes**:
- Add `server_id` parameter to all methods (identifies which physical server)
- Results must include `physical_server` field ('hetzner' or 'ovh')
- HOST stores results in MariaDB with server attribution

### 3. AMP Integration (`src/amp_integration/amp_client.py`)

**Current**: Connects to single AMP panel URL

**Required**:
- **Each physical server runs its own AMP panel**
- Hetzner agent connects to Hetzner AMP (135.181.212.169:8080)
- OVH agent connects to OVH AMP (37.187.143.41:8080)
- Credentials may differ per server

**Changes**:
- Config must specify per-server AMP endpoints
- Format: `servers: [{name: 'hetzner', amp_url: '...', credentials: ...}, ...]`

### 4. Plugin Automation (`src/automation/plugin_automation.py`)

**Current**: Deploys only to local DEV01 instance

**Required**:
- HOST coordinates plugin updates across both servers
- Publish update job to Redis queue with target instance ID
- Client agents pick up jobs for their instances
- Client agents execute deployment via local AMP API
- Client agents report success/failure back to HOST

**Changes**:
- Add `target_server` field to all deployment jobs
- Route jobs through Redis pub/sub system
- Implement result callback mechanism

### 5. Web API (`src/webapi/routes.py`)

**Current**: Queries local agent only

**Required**:
- Must query MariaDB for multi-server data
- Drift reports include physical_server field
- Instance discovery aggregates from both servers
- Deployment history tracks which server was targeted

**Changes**:
- Add server filter to all API endpoints
- `/api/drift?server=hetzner` or `?server=ovh` or `?server=all`
- `/api/instances?server=hetzner` returns instances from Hetzner only
- Dashboard shows split view or unified view

### 6. Configuration Files

**Current**: Single `agent.yaml` config file

**Required**:

**Hetzner HOST Config** (`/etc/archivesmp/host-config.yaml`):
```yaml
role: host
physical_server: hetzner
amp:
  url: http://135.181.212.169:8080
  username: admin
  password: <encrypted>

redis:
  host: localhost
  port: 6379
  db: 0

mariadb:
  host: localhost
  port: 3306
  database: archivesmp
  username: archivesmp
  password: <encrypted>

minio:
  endpoint: localhost:9001
  access_key: <key>
  secret_key: <secret>

webapi:
  enabled: true
  port: 8000
```

**OVH CLIENT Config** (`/etc/archivesmp/client-config.yaml`):
```yaml
role: client
physical_server: ovh
amp:
  url: http://37.187.143.41:8080
  username: admin
  password: <encrypted>

redis:
  host: 135.181.212.169  # Connect to Hetzner Redis
  port: 6379
  db: 0

host_api:
  url: http://archivesmp.site:8000  # Report back to Hetzner
  api_key: <secret>

webapi:
  enabled: false  # No web UI on client
```

---

## DATABASE SCHEMA ADDITIONS

### MariaDB Tables (NEW)

**`physical_servers` table**:
```sql
CREATE TABLE physical_servers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,  -- 'hetzner' or 'ovh'
    role VARCHAR(20) NOT NULL,         -- 'host' or 'client'
    gaming_role VARCHAR(20),           -- 'primary' or 'secondary'
    ip_address VARCHAR(50),
    amp_url VARCHAR(255),
    last_seen TIMESTAMP,
    status VARCHAR(20)                 -- 'online', 'offline', 'degraded'
);
```

**`instances` table** (MODIFIED):
```sql
CREATE TABLE instances (
    id INT PRIMARY KEY AUTO_INCREMENT,
    physical_server_id INT NOT NULL,  -- NEW: FK to physical_servers
    instance_id VARCHAR(50) UNIQUE NOT NULL,  -- AMP instance UUID
    instance_name VARCHAR(100),
    status VARCHAR(20),
    last_seen TIMESTAMP,
    FOREIGN KEY (physical_server_id) REFERENCES physical_servers(id)
);
```

**`drift_reports` table** (MODIFIED):
```sql
CREATE TABLE drift_reports (
    id INT PRIMARY KEY AUTO_INCREMENT,
    physical_server_id INT NOT NULL,  -- NEW: FK to physical_servers
    instance_id INT NOT NULL,
    plugin_name VARCHAR(100),
    config_file VARCHAR(255),
    drift_type VARCHAR(50),
    severity VARCHAR(20),
    detected_at TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (physical_server_id) REFERENCES physical_servers(id),
    FOREIGN KEY (instance_id) REFERENCES instances(id)
);
```

**`deployment_jobs` table** (NEW):
```sql
CREATE TABLE deployment_jobs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    job_uuid VARCHAR(50) UNIQUE NOT NULL,
    target_server VARCHAR(50),         -- 'hetzner', 'ovh', or 'all'
    target_instance_id VARCHAR(50),
    plugin_name VARCHAR(100),
    plugin_version VARCHAR(50),
    job_type VARCHAR(50),              -- 'deploy', 'rollback', 'config_update'
    status VARCHAR(20),                -- 'pending', 'in_progress', 'completed', 'failed'
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_message TEXT
);
```

---

## REDIS PUB/SUB CHANNELS

**Job Distribution**:
- `archivesmp:jobs:hetzner` - Jobs for Hetzner client agent
- `archivesmp:jobs:ovh` - Jobs for OVH client agent
- `archivesmp:jobs:broadcast` - Jobs for all clients

**Result Reporting**:
- `archivesmp:results:drift` - Drift scan results
- `archivesmp:results:deployment` - Deployment results
- `archivesmp:results:health` - Health check results

**Job Message Format**:
```json
{
  "job_id": "uuid-here",
  "job_type": "plugin_deploy",
  "target_instance": "DEV01",
  "plugin_name": "CoreProtect",
  "plugin_version": "22.2",
  "plugin_jar_url": "http://archivesmp.site:9001/plugins/CoreProtect-22.2.jar",
  "timestamp": "2025-11-06T10:30:00Z"
}
```

---

## MIGRATION PLAN

### Phase 1: Add Multi-Server Support (HOST Only)
1. Add `physical_servers` table to MariaDB
2. Insert records for Hetzner and OVH
3. Modify agent to accept `server_id` parameter
4. Update drift detector to tag results with server
5. Update web API to filter by server

### Phase 2: Implement Redis Job Queue
1. Set up Redis on Hetzner
2. Create job publisher in HOST coordinator
3. Define job message schemas
4. Implement job routing logic

### Phase 3: Build Client Agent
1. Create lightweight `homeamp-client-agent.service`
2. Implement Redis subscriber
3. Implement result reporting to HOST API
4. Package for OVH deployment

### Phase 4: Deploy to OVH
1. Install client agent on OVH
2. Configure client to connect to Hetzner Redis
3. Test job execution and result reporting
4. Verify web UI shows both servers

### Phase 5: Test End-to-End
1. Deploy plugin update from Hetzner to OVH instance
2. Run drift scan on OVH, view results in Hetzner web UI
3. Test backup/rollback across servers
4. Validate all 17-20 instances are discovered

---

## FILES REQUIRING MODIFICATION

### Critical Changes
- `src/agent/service.py` → Split into `host_agent.py` and `client_agent.py`
- `src/analyzers/drift_detector.py` → Add server_id parameter everywhere
- `src/amp_integration/amp_client.py` → Support per-server AMP endpoints
- `src/automation/plugin_automation.py` → Use Redis job queue
- `src/webapi/routes.py` → Query MariaDB with server filters
- `src/core/config_parser.py` → No changes needed (works on both)

### New Files Needed
- `src/coordinator/job_queue.py` → Redis pub/sub implementation
- `src/coordinator/job_scheduler.py` → Job creation and distribution
- `src/client/client_agent.py` → Lightweight client service
- `src/client/result_reporter.py` → Report results back to HOST
- `src/database/models.py` → SQLAlchemy models for MariaDB
- `src/database/migrations/` → Database schema migrations

### Configuration Files
- `deployment/host-config.yaml.template` → Hetzner configuration
- `deployment/client-config.yaml.template` → OVH configuration
- `deployment/install-client.sh` → OVH installation script

---

## DEPLOYMENT TARGETS CLARIFIED

**Current State (Nov 6, 2025)**:
- Hetzner: 11 instances discovered and managed
- OVH: Unknown instance count (estimated 6-9 based on deployment matrix)

**After Migration**:
- Hetzner HOST: Manages itself + coordinates OVH
- OVH CLIENT: Reports to Hetzner, executes local jobs
- Total: ~17-20 instances across both servers fully managed

---

## IMMEDIATE ACTION ITEMS

1. **Database Migration**: Create `physical_servers` table and populate with Hetzner/OVH records
2. **Config Split**: Separate agent config into host vs client templates
3. **Redis Setup**: Install and configure Redis on Hetzner
4. **Code Audit**: Review all files that assume single-server operation
5. **Client Agent**: Build minimal client service for OVH deployment
6. **Testing**: Set up test environment to validate distributed operation before production

---

## DEPENDENCIES TO ADD

**Python Packages**:
- `redis` - Redis client for pub/sub
- `pymysql` or `mysqlclient` - MariaDB connector
- `sqlalchemy` - ORM for database operations
- `alembic` - Database migrations

**System Services**:
- Redis server (on Hetzner)
- MariaDB server (on Hetzner)
- MinIO (already installed on Hetzner)

---

## RISK ASSESSMENT

**High Risk**:
- Network connectivity between Hetzner and OVH (Redis, API calls)
- Credential management (storing OVH credentials on Hetzner)
- Job queue reliability (what if Redis goes down?)

**Medium Risk**:
- Database performance with 17-20 instances reporting
- Redis message queue size with frequent drift scans
- Client agent crashes on OVH (no local monitoring)

**Mitigation**:
- Implement health checks and heartbeats
- Add job retry logic with exponential backoff
- Set up monitoring and alerting for both servers
- Keep client agent stateless and restartable

---

## CONCLUSION

The current single-server design **CANNOT manage OVH instances**. A distributed client-server architecture using Redis for job distribution and MariaDB for persistent storage is **REQUIRED** to manage all ~17-20 instances across both physical servers.

**Estimated Effort**: 
- Database migration: 2-4 hours
- Redis integration: 4-6 hours  
- Client agent build: 6-8 hours
- Testing and deployment: 4-6 hours
- **Total**: ~20-24 hours of development

**Priority**: HIGH - Current system is only managing ~60% of infrastructure.
