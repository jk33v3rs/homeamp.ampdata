# ArchiveSMP Config Manager - Deployment Guide

## System Architecture

### Overview
Distributed configuration management system for ArchiveSMP Minecraft network running across two physical Debian servers with 23 total AMP instances.

### Deployment Topology

```
Development (Windows)
  E:\homeamp.ampdata\software\homeamp-config-manager\
  ↓ Git push / SFTP upload
  ↓
Production Servers (Debian Linux)

Hetzner (135.181.212.169)                    OVH (37.187.143.41)
/home/webadmin/archivesmp-config-manager/    /home/webadmin/archivesmp-config-manager/
├── Agent Service (port 8001)                ├── Agent Service (port 8001)
├── Web UI (port 8000) ← ONLY ON HETZNER    
├── Expectations Data                        ├── Expectations Data
│   ├── universal_configs_analysis.json      │   ├── universal_configs_analysis.json
│   └── variable_configs_analysis_UPDATED.json│   └── variable_configs_analysis_UPDATED.json
└── 11 AMP Instances                         └── 12 AMP Instances
    /home/amp/.ampdata/instances/               /home/amp/.ampdata/instances/
```

### Communication Flow

1. **Web UI → Hetzner Agent** (localhost:8001)
2. **Web UI → OVH Agent** (37.187.143.41:8001)
3. **OVH Agent → Hetzner Web UI** (for drift reports)

## Components

### 1. Agent Service (`src/agent/`)

**Files:**
- `service.py` - Main agent service (existing MinIO-based system)
- `api.py` - NEW REST API for deployment and restart commands
- `drift_checker.py` - NEW drift detection comparing expectations vs reality

**Agent API Endpoints:**
- `GET /api/agent/status` - Get agent status and instance list
- `POST /api/agent/deploy-configs` - Deploy configs to instances
- `POST /api/agent/restart` - Restart AMP instances
- `POST /api/agent/mark-restart-needed` - Flag instance for restart

**Runs on:** Both Hetzner and OVH at port 8001

### 2. Web API (`src/web/api.py`)

**NEW Endpoints Added:**
- `POST /api/deploy` - Deploy configs to selected instances
- `POST /api/restart` - Restart selected instances
- `GET /api/instances/status` - Get status of all instances

**Runs on:** Hetzner only at port 8000

### 3. Web UI (`src/web/static/`)

**Files:**
- `deploy.html` - NEW deployment and restart control interface
- `index.html` - Existing deviation review interface

**Access:** http://135.181.212.169:8000/static/deploy.html

## Configuration Data

### Expectations (Baseline)
Located in `data/expectations/` (to be created during deployment):

**82 Universal Configs** (`universal_configs_analysis.json`)
- Plugins that should have identical configs across all servers
- Examples: bStats, CoreProtect base settings, LuckPerms core config

**23 Variable Configs** (`variable_configs_analysis_UPDATED.json`)
- Plugins with documented server-specific differences
- Includes allowed variances like:
  - CoreProtect.table-prefix (unique per instance)
  - bStats.serverUuid (unique per instance)
  - ImageFrame.WebServer.Port (unique per instance)
  - LevelledMobs (BENT01 has advanced levelling)

**6 Paid Plugins** (subset of 82 universal)
- CombatPets, ExcellentEnchants, ExcellentJobs, HuskSync, HuskTowns, mcMMO

### Reality (Live Configs)
Located on production servers:
```
/home/amp/.ampdata/instances/<INSTANCE>/Minecraft/plugins/<PLUGIN>/config.yml
```

## Deployment Workflow

### Initial Deployment

1. **On Development Machine (Windows):**
   ```cmd
   cd E:\homeamp.ampdata\software\homeamp-config-manager
   git add .
   git commit -m "Add deployment and restart functionality"
   git push
   ```

2. **On Hetzner Server (135.181.212.169):**
   ```bash
   cd /home/webadmin/archivesmp-config-manager
   git pull
   
   # Create expectations directory
   mkdir -p data/expectations
   
   # Copy expectations data
   cp /path/to/universal_configs_analysis.json data/expectations/
   cp /path/to/variable_configs_analysis_UPDATED.json data/expectations/
   
   # Install dependencies
   pip3 install fastapi uvicorn httpx pyyaml
   
   # Start agent API (port 8001)
   python3 -m uvicorn src.agent.api:app --host 0.0.0.0 --port 8001 &
   
   # Start web API (port 8000)
   python3 -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000 &
   ```

3. **On OVH Server (37.187.143.41):**
   ```bash
   cd /home/webadmin/archivesmp-config-manager
   git pull
   
   # Create expectations directory
   mkdir -p data/expectations
   
   # Copy expectations data
   cp /path/to/universal_configs_analysis.json data/expectations/
   cp /path/to/variable_configs_analysis_UPDATED.json data/expectations/
   
   # Install dependencies
   pip3 install fastapi uvicorn httpx pyyaml
   
   # Start agent API ONLY (port 8001)
   python3 -m uvicorn src.agent.api:app --host 0.0.0.0 --port 8001 &
   ```

### Systemd Services (Recommended)

**Create `/etc/systemd/system/archivesmp-agent.service`:**
```ini
[Unit]
Description=ArchiveSMP Config Agent
After=network.target

[Service]
Type=simple
User=webadmin
WorkingDirectory=/home/webadmin/archivesmp-config-manager
ExecStart=/usr/bin/python3 -m uvicorn src.agent.api:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Create `/etc/systemd/system/archivesmp-webapi.service` (Hetzner only):**
```ini
[Unit]
Description=ArchiveSMP Config Web API
After=network.target

[Service]
Type=simple
User=webadmin
WorkingDirectory=/home/webadmin/archivesmp-config-manager
ExecStart=/usr/bin/python3 -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start services:**
```bash
# Both servers
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-agent
sudo systemctl start archivesmp-agent

# Hetzner only
sudo systemctl enable archivesmp-webapi
sudo systemctl start archivesmp-webapi
```

## Usage

### 1. Access Web UI
Navigate to: http://135.181.212.169:8000/static/deploy.html

### 2. View Instance Status
- See all 23 instances across both servers
- Check which instances need restart (orange border)
- View Hetzner vs OVH instance counts

### 3. Deploy Configs
1. Click "Deploy Configs" tab
2. Select target instances
3. Click "Deploy Selected Configs"
4. Instances will be flagged for restart

### 4. Restart Instances
1. Click "Restart Instances" tab
2. Select instances to restart OR
3. Click "Restart Flagged Only" to restart instances with pending changes
4. Confirm restart operation

**Restart Commands Executed:**
- Individual: `sudo -u amp sudo ampinstmgr restart <shortname>`
- All: `sudo ampinstmgr restartAll`

## Instance Mapping

### Hetzner Instances (11)
BENT01, BIG01, CLIP01, CREA01, DEV01, EVO01, HARD01, HUB01, MIN01, SMP101, SMP201

### OVH Instances (12)
CSMC01, EMAD01, MINE01, PRI01, ROY01, TOW01, + 6 others (pending deployment)

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status archivesmp-agent
sudo systemctl status archivesmp-webapi  # Hetzner only
```

### View Logs
```bash
journalctl -u archivesmp-agent -f
journalctl -u archivesmp-webapi -f
```

### Test Agent API
```bash
# Check Hetzner agent
curl http://localhost:8001/api/agent/status

# Check OVH agent from Hetzner
curl http://37.187.143.41:8001/api/agent/status
```

### Test Web API
```bash
curl http://localhost:8000/api/instances/status
```

### Manual Instance Discovery
```bash
ls /home/amp/.ampdata/instances/
```

### Test Restart Command
```bash
# Single instance
sudo -u amp sudo ampinstmgr restart DEV01

# All instances
sudo ampinstmgr restartAll
```

## Security Notes

- Web UI runs on Hetzner internal network (port 8000)
- Agent APIs run on port 8001 (configure firewall if needed)
- OVH agent must be accessible from Hetzner (37.187.143.41:8001)
- All restart commands use sudo - ensure webadmin user has proper permissions

## Next Steps

1. ✅ Deploy code to both servers
2. ✅ Copy expectations data to `data/expectations/`
3. ✅ Start services (systemd recommended)
4. ⏳ Implement drift detection scheduled task
5. ⏳ Add drift visualization to web UI
6. ⏳ Integrate with plugin update system
7. ⏳ Add config validation before deployment
8. ⏳ Add rollback functionality

## Related Files

- **Development:** `E:\homeamp.ampdata\software\homeamp-config-manager\`
- **Expectations Data:** `E:\homeamp.ampdata\utildata\*_configs_analysis*.json`
- **Baseline Docs:** `E:\homeamp.ampdata\utildata\plugin_universal_configs\`
- **Plugin Definitions:** `E:\homeamp.ampdata\data\plugin_definitions\`
