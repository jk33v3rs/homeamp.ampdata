# Quick Start - Deploy to Production

## Prerequisites
- Development code at: `E:\homeamp.ampdata\software\homeamp-config-manager\`
- SSH access to both servers (135.181.212.169 and 37.187.143.41)
- sudo privileges on both servers

## Step 1: Package Expectations Data (Windows)

```cmd
cd E:\homeamp.ampdata
python scripts\package_expectations.py
```

This creates `software\homeamp-config-manager\data\expectations\` with:
- `universal_configs.json` (82 plugins)
- `variable_configs.json` (23 plugins)
- `metadata.json`

## Step 2: Deploy to Hetzner (135.181.212.169)

```bash
# SSH to Hetzner
ssh webadmin@135.181.212.169

# Navigate to install directory
cd /home/webadmin

# Clone or update repo
# If first time:
git clone <your-repo-url> archivesmp-config-manager

# If already exists:
cd archivesmp-config-manager
git pull

# Install Python dependencies
pip3 install fastapi uvicorn httpx pyyaml

# Create logs directory
mkdir -p logs

# Make startup script executable
chmod +x start_services.sh

# Start services (agent + web API)
./start_services.sh
```

**Expected output:**
```
==================================================
ArchiveSMP Config Manager - Service Startup
==================================================
Server: hetzner
Server type: hetzner

✓ Dependencies OK
✓ Expectations data found
✓ Found AMP instances directory (11 instances)
✓ Cleaned up old processes

Starting Agent API (port 8001)...
✓ Agent API started (PID: 12345)

Starting Web API (port 8000)...
✓ Web API started (PID: 12346)

✓ Agent API responding on port 8001
✓ Web API responding on port 8000

==================================================
Services Started Successfully!
==================================================

Access points:
  - Web UI: http://135.181.212.169:8000/static/deploy.html
  - API Docs: http://135.181.212.169:8000/docs
```

## Step 3: Deploy to OVH (37.187.143.41)

```bash
# SSH to OVH
ssh webadmin@37.187.143.41

# Navigate to install directory
cd /home/webadmin

# Clone or update repo
# If first time:
git clone <your-repo-url> archivesmp-config-manager

# If already exists:
cd archivesmp-config-manager
git pull

# Install Python dependencies
pip3 install fastapi uvicorn httpx pyyaml

# Create logs directory
mkdir -p logs

# Make startup script executable
chmod +x start_services.sh

# Start services (agent only)
./start_services.sh
```

**Expected output:**
```
==================================================
ArchiveSMP Config Manager - Service Startup
==================================================
Server: ovh
Server type: ovh

✓ Dependencies OK
✓ Expectations data found
✓ Found AMP instances directory (12 instances)
✓ Cleaned up old processes

Starting Agent API (port 8001)...
✓ Agent API started (PID: 23456)

✓ Agent API responding on port 8001

==================================================
Services Started Successfully!
==================================================

Access points:
  - Agent API: http://localhost:8001/docs
```

## Step 4: Verify Deployment

### Test from Hetzner
```bash
# Check agent status
curl http://localhost:8001/api/agent/status

# Should return JSON with:
# {
#   "server_name": "hetzner",
#   "instances": ["BENT01", "BIG01", ...],
#   "needs_restart": [],
#   "agent_version": "1.0.0"
# }

# Check web API
curl http://localhost:8000/api/instances/status

# Should return JSON with both servers:
# {
#   "servers": {
#     "Hetzner": { "instances": [...], "needs_restart": [] },
#     "OVH": { "instances": [...], "needs_restart": [] }
#   },
#   "all_needs_restart": []
# }
```

### Test OVH connectivity from Hetzner
```bash
# From Hetzner server
curl http://37.187.143.41:8001/api/agent/status

# Should return OVH agent status with OVH instances
```

## Step 5: Access Web UI

Open in browser: **http://135.181.212.169:8000/static/deploy.html**

You should see:
- Status dashboard showing instance counts
- Two tabs: "Deploy Configs" and "Restart Instances"
- Instance selection grids (11 Hetzner + 12 OVH = 23 total)

## Step 6: Test Restart Functionality

1. In Web UI, click "Restart Instances" tab
2. Select DEV01 (test instance)
3. Click "Restart Selected"
4. Confirm dialog
5. Wait for success message

**Behind the scenes:**
```bash
# This command is executed:
sudo -u amp sudo ampinstmgr restart DEV01
```

## Troubleshooting

### Services won't start
```bash
# Check Python is installed
python3 --version

# Check dependencies
python3 -c "import fastapi, uvicorn, httpx, yaml"

# Check port availability
netstat -tulpn | grep :8001
netstat -tulpn | grep :8000

# Check permissions
ls -la /home/amp/.ampdata/instances/
```

### Can't access web UI
```bash
# Check web API is running
ps aux | grep uvicorn

# Check logs
tail -f /home/webadmin/archivesmp-config-manager/logs/webapi.log

# Check firewall
sudo ufw status
```

### OVH agent not reachable from Hetzner
```bash
# From Hetzner, test OVH connectivity
ping 37.187.143.41
telnet 37.187.143.41 8001

# On OVH, check if agent is listening on external interface
netstat -tulpn | grep :8001

# Should show: 0.0.0.0:8001 (not 127.0.0.1:8001)
```

### Restart commands fail
```bash
# Test AMP command manually
sudo -u amp sudo ampinstmgr restart DEV01

# Check if amp user exists
id amp

# Check ampinstmgr location
which ampinstmgr

# Check webadmin sudo permissions
sudo -l
```

## Setup as Systemd Services (Recommended)

### Hetzner
```bash
# Create agent service
sudo tee /etc/systemd/system/archivesmp-agent.service << 'EOF'
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
EOF

# Create web API service
sudo tee /etc/systemd/system/archivesmp-webapi.service << 'EOF'
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
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-agent archivesmp-webapi
sudo systemctl start archivesmp-agent archivesmp-webapi

# Check status
sudo systemctl status archivesmp-agent
sudo systemctl status archivesmp-webapi
```

### OVH (Agent Only)
```bash
# Create agent service
sudo tee /etc/systemd/system/archivesmp-agent.service << 'EOF'
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
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-agent
sudo systemctl start archivesmp-agent

# Check status
sudo systemctl status archivesmp-agent
```

## Useful Commands

### View logs
```bash
# Real-time logs
tail -f /home/webadmin/archivesmp-config-manager/logs/agent.log
tail -f /home/webadmin/archivesmp-config-manager/logs/webapi.log

# Systemd logs
journalctl -u archivesmp-agent -f
journalctl -u archivesmp-webapi -f
```

### Restart services
```bash
# If using systemd
sudo systemctl restart archivesmp-agent
sudo systemctl restart archivesmp-webapi

# If using start_services.sh
pkill -f "uvicorn src.agent.api"
pkill -f "uvicorn src.web.api"
./start_services.sh
```

### Update code
```bash
cd /home/webadmin/archivesmp-config-manager
git pull
sudo systemctl restart archivesmp-agent archivesmp-webapi
```

## Success Indicators

✅ **Agent running on both servers** - Port 8001 responding  
✅ **Web UI accessible** - http://135.181.212.169:8000/static/deploy.html  
✅ **Instance discovery working** - Shows 11 Hetzner + 12 OVH instances  
✅ **OVH connectivity working** - Hetzner can call OVH agent API  
✅ **Restart commands working** - Can restart DEV01 from Web UI  
✅ **Status tracking working** - needs_restart flags updating correctly  

## Next Steps

1. Run drift detection to identify config differences
2. Review drift report in web UI
3. Deploy corrected configs to selected instances
4. Restart instances to apply changes
5. Verify configs are now correct

## Support

- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Expectations Format**: `data/expectations/README.md`
- **API Documentation**: http://135.181.212.169:8000/docs
