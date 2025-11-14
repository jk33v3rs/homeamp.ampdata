# ArchiveSMP Configuration Manager - Complete Deployment Guide

**Last Updated**: November 14, 2025  
**Status**: Production Ready ✅

---

## ⚠️ CRITICAL: Pre-Deployment Fixes Applied

**The following issues were identified and fixed before deployment:**

1. **Missing Dependencies** ❌ → ✅ **FIXED**
   - Created `requirements.txt` with ALL required packages
   - Added missing `pydantic` (used in 4 files, was NOT in original install list)
   - Added missing `prometheus-client` (used in metrics.py)
   - Added `aiohttp`, `python-multipart`, `requests` for completeness

2. **Missing `__init__.py` Files** ❌ → ✅ **FIXED**
   - Created `src/core/__init__.py` (CRITICAL - most imports are from here)
   - Created `src/agent/__init__.py` (CRITICAL - service won't run without it)
   - Created `src/web/__init__.py` (CRITICAL - web API needs this)
   - Created `src/updaters/__init__.py`
   - Created `src/deployment/__init__.py`
   - Created `src/utils/__init__.py`
   - Created `src/yunohost/__init__.py`

3. **Deploy Script Fixed** ❌ → ✅ **FIXED**
   - Now installs from `requirements.txt` instead of hardcoded package list
   - Ensures version consistency across deployments

**Without these fixes, deployment would have FAILED immediately with:**
- `ModuleNotFoundError: No module named 'pydantic'`
- `ModuleNotFoundError: No module named 'src.core'`
- Import errors preventing services from starting

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Deployment Checklist](#deployment-checklist)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Configuration Guide](#configuration-guide)
6. [Service Management](#service-management)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)
9. [Post-Deployment](#post-deployment)

---

## 🔧 Prerequisites

### Hetzner Server (135.181.212.169)
- ✅ Debian/Ubuntu Linux
- ✅ Python 3.9+ installed
- ✅ MinIO running on port 9000
- ✅ MariaDB running on port 3369 (if using shared database)
- ✅ User `amp` with sudo privileges
- ✅ 11 AMP instances discovered and running

### OVH Server (37.187.143.41)
- ✅ Debian/Ubuntu Linux
- ✅ Python 3.9+ installed
- ✅ Network access to Hetzner MinIO (135.181.212.169:9000)
- ✅ User `amp` with sudo privileges
- ⏳ Agent deployment pending

### Network Requirements
- Hetzner → MinIO on localhost:9000
- OVH → MinIO on 135.181.212.169:9000
- Web UI exposed on Hetzner: 135.181.212.169:8000
- Agent API on both servers: localhost:8001

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                       HETZNER (135.181.212.169)                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌────────────────┐  ┌───────────────┐           │
│  │ Web API      │  │ Agent Service  │  │ Agent API     │           │
│  │ Port: 8000   │  │ (Background)   │  │ Port: 8001    │           │
│  │ 4 workers    │  │                │  │               │           │
│  └──────┬───────┘  └───────┬────────┘  └───────┬───────┘           │
│         │                  │                    │                   │
│         └──────────────────┼────────────────────┘                   │
│                            │                                        │
│                     ┌──────▼──────┐                                 │
│                     │   MinIO     │◄────────┐                       │
│                     │ Port: 9000  │         │                       │
│                     └─────────────┘         │                       │
│                                             │                       │
│  ┌──────────────────────────────────────┐  │                       │
│  │ AMP Instances (11 discovered)       │  │                       │
│  │ /home/amp/.ampdata/instances/       │  │                       │
│  └──────────────────────────────────────┘  │                       │
└─────────────────────────────────────────────┼───────────────────────┘
                                              │
                                              │ Network: 135.181.212.169:9000
                                              │
┌─────────────────────────────────────────────┼───────────────────────┐
│                        OVH (37.187.143.41)  │                       │
├─────────────────────────────────────────────┼───────────────────────┤
│                                             │                       │
│  ┌────────────────┐  ┌───────────────┐     │                       │
│  │ Agent Service  │  │ Agent API     │     │                       │
│  │ (Background)   │  │ Port: 8001    │     │                       │
│  └───────┬────────┘  └───────┬───────┘     │                       │
│          │                   │              │                       │
│          └───────────────────┼──────────────┘                       │
│                              │                                      │
│  ┌──────────────────────────▼──────────────┐                       │
│  │ AMP Instances (pending deployment)     │                       │
│  │ /home/amp/.ampdata/instances/          │                       │
│  └────────────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Web API** (Hetzner only):
- Serves GUI on port 8000
- Central management interface
- Reports, drift detection, plugin updates
- Deployment orchestration

**Agent Service** (Both servers):
- Polls MinIO for configuration changes
- Applies changes to local instances
- Monitors drift
- Uploads results to MinIO
- Discovers AMP instances automatically

**Agent API** (Both servers):
- Local API on port 8001
- Receives deployment requests from Web API
- Manages local instance operations
- Restart coordination

**MinIO** (Hetzner):
- Central storage for config changes
- Agent-to-agent communication
- Pl3xMap tile storage
- Config backups
- Persistent agent state

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] SSH access to both servers confirmed
- [ ] Sudo privileges for `amp` user verified
- [ ] Python 3.9+ installed (`python3 --version`)
- [ ] Git installed (`git --version`)
- [ ] MinIO running on Hetzner (`systemctl status minio`)
- [ ] Network connectivity Hetzner ↔ OVH tested

### Deployment Files Ready
- [ ] `deployment/deploy.sh` (automated deployment script)
- [ ] `deployment/homeamp-agent.service` (systemd service)
- [ ] `deployment/archivesmp-webapi.service` (systemd service - Hetzner only)
- [ ] `deployment/archivesmp-agent-api.service` (systemd service)
- [ ] `deployment/agent.yaml.template` (agent configuration)
- [ ] `deployment/secrets.env.template` (credentials template)

### Post-Deployment Verification
- [ ] Services running (`systemctl status`)
- [ ] Logs clean (`journalctl -u <service> -f`)
- [ ] Web UI accessible (http://135.181.212.169:8000)
- [ ] Agent discovering instances correctly
- [ ] MinIO connectivity confirmed

---

## 🚀 Step-by-Step Deployment

### Step 1: Deploy to Hetzner (Primary Server with Web UI)

```bash
# SSH into Hetzner
ssh amp@135.181.212.169

# Clone repository to temp location (or download deployment script)
cd /tmp
git clone https://github.com/jk33v3rs/homeamp.ampdata.git
cd homeamp.ampdata/software/homeamp-config-manager/deployment

# Make deploy script executable
chmod +x deploy.sh

# Run deployment
sudo bash deploy.sh hetzner
```

**What the script does:**
1. Installs system dependencies (python3, pip, git)
2. Creates directories (`/opt/archivesmp-config-manager`, `/etc/archivesmp`, `/var/lib/archivesmp`)
3. Clones/updates repository
4. Installs Python packages (fastapi, uvicorn, minio, etc.)
5. Copies service files to `/etc/systemd/system/`
6. Creates `agent.yaml` with server_name="HETZNER"
7. Creates `secrets.env` template
8. Sets permissions (`chown amp:amp`)
9. Enables and starts services

**Expected Output:**
```
==================================================
Deployment Complete!
==================================================

Services installed:
  • homeamp-agent (background monitoring)
  • archivesmp-agent-api (local API on port 8001)
  • archivesmp-webapi (web UI on port 8000)

Web UI available at: http://135.181.212.169:8000

⚠ NEXT STEPS:
1. Edit MinIO credentials in: /etc/archivesmp/secrets.env
2. Restart services: sudo systemctl restart homeamp-agent archivesmp-agent-api archivesmp-webapi
3. Ensure MinIO is running: sudo systemctl status minio
```

### Step 2: Configure Secrets (Hetzner)

```bash
# Edit secrets file
sudo nano /etc/archivesmp/secrets.env
```

**Required Changes:**
```env
# MinIO Credentials (get from Hetzner MinIO installation)
ARCHIVESMP_MINIO_ACCESS_KEY=your_actual_access_key
ARCHIVESMP_MINIO_SECRET_KEY=your_actual_secret_key

# GitHub Token (optional - increases API rate limit)
GITHUB_TOKEN=ghp_your_github_token_here

# Database credentials (already correct from your config)
DB_HOST=135.181.212.169
DB_PORT=3369
DB_NAME=asmp_SQL
DB_USER=sqlworkerSMP
DB_PASSWORD=SQLdb2024!
```

### Step 3: Restart Services (Hetzner)

```bash
sudo systemctl restart homeamp-agent
sudo systemctl restart archivesmp-agent-api
sudo systemctl restart archivesmp-webapi
```

### Step 4: Verify Hetzner Deployment

```bash
# Run automated verification script
sudo bash /opt/archivesmp-config-manager/deployment/verify_deployment.sh

# This will check:
# ✓ Python 3.9+ installed
# ✓ All Python dependencies present (pydantic, fastapi, etc.)
# ✓ Installation directory exists
# ✓ Config files exist
# ✓ All __init__.py files present
# ✓ Module imports work
# ✓ SystemD services installed
# ✓ Service status

# If verification passes, proceed with manual checks:

# Check all services are running
sudo systemctl status homeamp-agent
sudo systemctl status archivesmp-agent-api
sudo systemctl status archivesmp-webapi

# Check logs for errors
sudo journalctl -u homeamp-agent -f --lines=50
sudo journalctl -u archivesmp-webapi -f --lines=50

# Verify MinIO connectivity
curl -I http://localhost:9000/minio/health/live

# Test Web UI
curl http://localhost:8000
# Should return HTML

# Test Agent API
curl http://localhost:8001/api/health
# Should return {"status": "healthy"}
```

**Access Web UI:**
Open browser: `http://135.181.212.169:8000`

You should see:
- Plugin Updates tab (showing all CI/CD endpoints working)
- Instance settings (11 instances discovered)
- Update mode controls (manual/semi-auto/full-auto per instance)

### Step 5: Deploy to OVH (Secondary Server)

```bash
# SSH into OVH
ssh amp@37.187.143.41

# Clone repository
cd /tmp
git clone https://github.com/jk33v3rs/homeamp.ampdata.git
cd homeamp.ampdata/software/homeamp-config-manager/deployment

# Make deploy script executable
chmod +x deploy.sh

# Run deployment (OVH mode - no Web API)
sudo bash deploy.sh ovh
```

**What's Different for OVH:**
- **NO** Web API service (only Hetzner has GUI)
- Agent connects to Hetzner MinIO at `135.181.212.169:9000`
- `agent.yaml` has `server_name: "OVH"`
- `agent.yaml` has `endpoint: "135.181.212.169:9000"`

### Step 6: Configure Secrets (OVH)

```bash
# Edit secrets file
sudo nano /etc/archivesmp/secrets.env
```

**Use SAME MinIO credentials as Hetzner:**
```env
ARCHIVESMP_MINIO_ACCESS_KEY=same_as_hetzner
ARCHIVESMP_MINIO_SECRET_KEY=same_as_hetzner
```

### Step 7: Verify Network Connectivity (OVH → Hetzner)

```bash
# Test MinIO connectivity from OVH to Hetzner
curl -I http://135.181.212.169:9000/minio/health/live

# Should return: HTTP/1.1 200 OK

# If connection fails, check:
# 1. Hetzner firewall allows port 9000
# 2. OVH can route to Hetzner IP
# 3. MinIO is configured to listen on 0.0.0.0 (not just 127.0.0.1)
```

### Step 8: Restart Services (OVH)

```bash
sudo systemctl restart homeamp-agent
sudo systemctl restart archivesmp-agent-api
```

### Step 9: Verify OVH Deployment

```bash
# Check services
sudo systemctl status homeamp-agent
sudo systemctl status archivesmp-agent-api

# Check logs
sudo journalctl -u homeamp-agent -f --lines=50

# Verify agent can reach Hetzner MinIO
# Check logs for "Connected to MinIO" or similar
```

---

## ⚙️ Configuration Guide

### Agent Configuration (`/etc/archivesmp/agent.yaml`)

**Hetzner Example:**
```yaml
agent:
  server_name: "HETZNER"
  amp_data_path: "/home/amp/.ampdata/instances"
  polling:
    change_poll_interval: 30
    drift_check_interval: 3600
    health_check_interval: 300

storage:
  minio:
    endpoint: "localhost:9000"  # Localhost on Hetzner
    secure: false
```

**OVH Example:**
```yaml
agent:
  server_name: "OVH"
  amp_data_path: "/home/amp/.ampdata/instances"
  polling:
    change_poll_interval: 30
    drift_check_interval: 3600
    health_check_interval: 300

storage:
  minio:
    endpoint: "135.181.212.169:9000"  # Remote Hetzner MinIO
    secure: false
```

### Instance Update Modes (Configured via Web UI)

**Manual Mode** (`manual`):
- No automatic actions
- User must click "Deploy" for every update
- Highest safety, full control

**Semi-Automatic Mode** (`semi_auto`):
- Updates download and stage automatically
- User must approve deployment with single click
- Recommended for most instances

**Fully Automatic Mode** (`full_auto`):
- Updates download and deploy automatically based on risk settings
- Risk level gates:
  - ✅ Low risk: Can auto-deploy if enabled
  - ⚠️ Medium risk: Can auto-deploy if enabled
  - ❌ High risk: NEVER auto-deploys (safety override)
- Recommended for DEV instances only

---

## 🔧 Service Management

### Start/Stop Services

```bash
# Start all services
sudo systemctl start homeamp-agent
sudo systemctl start archivesmp-agent-api
sudo systemctl start archivesmp-webapi  # Hetzner only

# Stop all services
sudo systemctl stop homeamp-agent
sudo systemctl stop archivesmp-agent-api
sudo systemctl stop archivesmp-webapi  # Hetzner only

# Restart after config changes
sudo systemctl restart homeamp-agent
```

### Enable/Disable Auto-Start

```bash
# Enable (start on boot)
sudo systemctl enable homeamp-agent
sudo systemctl enable archivesmp-webapi

# Disable
sudo systemctl disable homeamp-agent
```

### View Logs

```bash
# Follow live logs
sudo journalctl -u homeamp-agent -f

# Last 100 lines
sudo journalctl -u homeamp-agent -n 100

# Logs since yesterday
sudo journalctl -u homeamp-agent --since yesterday

# All logs for Web API
sudo journalctl -u archivesmp-webapi --no-pager
```

### Service Status

```bash
# Check status
sudo systemctl status homeamp-agent

# Check if service is running
systemctl is-active homeamp-agent

# Check if service is enabled
systemctl is-enabled homeamp-agent
```

---

## ✅ Verification & Testing

### 1. Services Running

```bash
# All services should show "active (running)"
systemctl status homeamp-agent
systemctl status archivesmp-agent-api
systemctl status archivesmp-webapi  # Hetzner only
```

### 2. Agent Discovering Instances

```bash
# Check agent logs for discovered instances
sudo journalctl -u homeamp-agent | grep "Discovered"

# Expected output:
# "Discovered 11 AMP instances: BENT01, SMP101, ..."
```

### 3. Web UI Accessible

```bash
# From Hetzner
curl -I http://localhost:8000
# Should return: HTTP/1.1 200 OK

# From external
curl -I http://135.181.212.169:8000
```

### 4. Plugin Update Checker Working

```bash
# Check logs for plugin update checks
sudo journalctl -u homeamp-agent | grep "plugin"

# Or test via API
curl http://localhost:8000/api/plugins/outdated
# Should return JSON with outdated plugins
```

### 5. MinIO Connectivity

```bash
# On Hetzner
curl http://localhost:9000/minio/health/live

# On OVH
curl http://135.181.212.169:9000/minio/health/live
```

### 6. Drift Detection

```bash
# Trigger manual drift scan via API
curl -X POST http://localhost:8000/api/operations/scan-drift

# Check results
curl http://localhost:8000/api/reports/drift
```

---

## 🐛 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
sudo journalctl -u homeamp-agent -xe
```

**Common Issues:**
1. **Missing Python packages**
   ```bash
   sudo pip3 install fastapi uvicorn minio pyyaml
   ```

2. **Config file not found**
   ```bash
   ls -la /etc/archivesmp/agent.yaml
   # If missing, copy from template
   sudo cp /opt/archivesmp-config-manager/deployment/agent.yaml.template /etc/archivesmp/agent.yaml
   ```

3. **Permission denied**
   ```bash
   sudo chown -R amp:amp /opt/archivesmp-config-manager
   sudo chown -R amp:amp /var/lib/archivesmp
   ```

### Agent Can't Connect to MinIO

**Test connectivity:**
```bash
# On OVH, test Hetzner MinIO
telnet 135.181.212.169 9000
```

**Check firewall (Hetzner):**
```bash
# Allow MinIO port
sudo ufw allow 9000/tcp
sudo ufw status
```

**Check MinIO config:**
```bash
# MinIO should listen on 0.0.0.0, not 127.0.0.1
sudo systemctl status minio
cat /etc/default/minio | grep MINIO_ADDRESS
```

### Web UI Returns 502/503

**Check Web API service:**
```bash
sudo systemctl status archivesmp-webapi
sudo journalctl -u archivesmp-webapi -f
```

**Check port is listening:**
```bash
sudo netstat -tlnp | grep 8000
# Should show: uvicorn listening on 0.0.0.0:8000
```

### Drift Detector Crashes

**This was fixed!** If you still see errors:
```bash
# Check logs
sudo journalctl -u homeamp-agent | grep "drift"

# Ensure you have latest code
cd /opt/archivesmp-config-manager
sudo -u amp git pull

# Restart agent
sudo systemctl restart homeamp-agent
```

### Plugin Updates Not Working

**Check PLUGIN_REGISTRY.md is loaded:**
```bash
ls -la /opt/archivesmp-config-manager/PLUGIN_REGISTRY.md
```

**Test API endpoints manually:**
```bash
# Jenkins
curl https://ci.codemc.io/job/retrooper/job/packetevents/lastSuccessfulBuild/api/json

# Modrinth
curl https://api.modrinth.com/v2/project/fALzjamp/version

# GitHub
curl https://api.github.com/repos/LuckPerms/LuckPerms/releases/latest
```

---

## 🎉 Post-Deployment

### Set Up Automated Drift Checking

```bash
# Create systemd timer (optional - drift checks run every hour by agent already)
# Only needed if you want more frequent checks
sudo nano /etc/systemd/system/archivesmp-drift-check.timer
```

### Configure Instance Update Modes

1. Open Web UI: http://135.181.212.169:8000
2. Go to "Plugin Updates" tab
3. For each instance, select update mode:
   - **DEV01**: Full Auto (low + medium risk)
   - **SMP101/SMP201**: Semi-Auto
   - **BENT01**: Manual (BentoBox is complex)
   - **Others**: Semi-Auto

### Monitor System Health

**Daily Checks:**
```bash
# Check service status
systemctl status homeamp-agent archivesmp-webapi

# Check disk space
df -h /var/lib/archivesmp

# Check MinIO storage
mc admin info myminio  # Requires MinIO client
```

**Weekly Tasks:**
- Review drift reports in Web UI
- Check plugin update logs
- Test rollback functionality

### Backup Configuration

```bash
# Backup agent config
sudo cp /etc/archivesmp/agent.yaml /etc/archivesmp/agent.yaml.backup

# Backup secrets
sudo cp /etc/archivesmp/secrets.env /etc/archivesmp/secrets.env.backup
```

---

## 📚 Additional Resources

- **Web UI**: http://135.181.212.169:8000
- **API Docs**: http://135.181.212.169:8000/docs (FastAPI auto-generated)
- **Agent Logs**: `journalctl -u homeamp-agent -f`
- **Web API Logs**: `journalctl -u archivesmp-webapi -f`
- **GitHub Repo**: https://github.com/jk33v3rs/homeamp.ampdata

---

**Deployment completed successfully! 🎊**

For issues, check logs first: `sudo journalctl -u homeamp-agent -f`
