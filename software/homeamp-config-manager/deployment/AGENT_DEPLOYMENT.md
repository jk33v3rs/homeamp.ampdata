# ArchiveSMP Configuration Manager - Agent Deployment Guide

## Database-Backed Architecture

The new system uses a centralized MariaDB database (`asmp_config`) hosted on Hetzner (135.181.212.169:3369).

### Architecture Components

1. **Central Database** (Hetzner): MariaDB with configuration hierarchy
2. **Endpoint Agents** (Both servers): Lightweight agents that scan local instances and report drift
3. **Web API** (Hetzner): FastAPI service for GUI and manual operations
4. **Web GUI** (Hetzner): React-based configuration editor

## Deployment Steps

### 1. Deploy Endpoint Agent on Hetzner

```bash
# SSH to Hetzner
ssh amp@135.181.212.169

# Navigate to project directory
cd /opt/archivesmp-config-manager

# Update code from git
git pull

# Install/update dependencies
.venv/bin/pip install -r requirements.txt

# Edit service file - set SERVER_NAME to 'hetzner-xeon'
sudo nano deployment/archivesmp-endpoint-agent.service
# Change: --server=hetzner-xeon

# Install systemd service
sudo cp deployment/archivesmp-endpoint-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-endpoint-agent.service
sudo systemctl start archivesmp-endpoint-agent.service

# Check status
sudo systemctl status archivesmp-endpoint-agent.service
sudo journalctl -u archivesmp-endpoint-agent.service -f
```

### 2. Deploy Endpoint Agent on OVH

```bash
# SSH to OVH
ssh amp@37.187.143.41

# Clone repository (if first time)
sudo mkdir -p /opt/archivesmp-config-manager
sudo chown amp:amp /opt/archivesmp-config-manager
cd /opt/archivesmp-config-manager
git clone https://github.com/jk33v3rs/homeamp.ampdata.git .

# OR update existing
cd /opt/archivesmp-config-manager
git pull

# Create virtual environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Edit service file - set SERVER_NAME to 'ovh-ryzen'
nano deployment/archivesmp-endpoint-agent.service
# Change: --server=ovh-ryzen

# Install systemd service
sudo cp deployment/archivesmp-endpoint-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-endpoint-agent.service
sudo systemctl start archivesmp-endpoint-agent.service

# Check status
sudo systemctl status archivesmp-endpoint-agent.service
sudo journalctl -u archivesmp-endpoint-agent.service -f
```

### 3. Deploy Web API (Hetzner only)

```bash
# SSH to Hetzner
ssh amp@135.181.212.169

cd /opt/archivesmp-config-manager

# Install web API systemd service
sudo cp deployment/archivesmp-webapi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-webapi.service
sudo systemctl restart archivesmp-webapi.service

# Check status
sudo systemctl status archivesmp-webapi.service
sudo journalctl -u archivesmp-webapi.service -f

# Test API
curl http://localhost:8000/api/instances
curl http://localhost:8000/api/variance
```

### 4. Access Web GUI

The web GUI is served by the web API service:

- **Local**: http://localhost:8000/
- **SSH Tunnel**: `ssh -L 8000:localhost:8000 amp@135.181.212.169`
- **Public** (if configured): http://135.181.212.169:8000/

## Verification

### Check Agent Discovery

```bash
# On Hetzner
sudo journalctl -u archivesmp-endpoint-agent.service --since "5 minutes ago"
# Should see: "Discovered N instances"

# On OVH
sudo journalctl -u archivesmp-endpoint-agent.service --since "5 minutes ago"
# Should see: "Discovered N instances"
```

### Check Database Connectivity

```python
# Test script
from src.database.db_access import ConfigDatabase

db = ConfigDatabase(
    host='135.181.212.169',
    port=3369,
    user='sqlworkerSMP',
    password='SQLdb2024!'
)

db.connect()
instances = db.get_all_instances()
print(f"Found {len(instances)} instances")

for inst in instances:
    print(f"  {inst['instance_id']}: {inst['instance_name']} on {inst['server_name']}")

db.disconnect()
```

### Check Drift Detection

```bash
# Agents log drift when configs don't match database expectations
sudo journalctl -u archivesmp-endpoint-agent.service | grep DRIFT

# Example output:
# DRIFT SMP201/LuckPerms/config.yml:server → Expected: SMP201 (from INSTANCE:SMP201), Got: SMP101
```

## Troubleshooting

### Agent Not Discovering Instances

1. Check AMP instance directory exists: `/home/amp/.ampdata/instances/`
2. Check permissions: `ls -la /home/amp/.ampdata/instances/`
3. Check agent logs: `sudo journalctl -u archivesmp-endpoint-agent.service -n 100`

### Database Connection Errors

1. Test connectivity: `telnet 135.181.212.169 3369`
2. Check firewall: `sudo ufw status`
3. Verify database user has remote access permissions
4. Check MariaDB bind-address: `/etc/mysql/mariadb.conf.d/50-server.cnf`

### Web API Not Starting

1. Check port 8000 available: `sudo netstat -tlnp | grep 8000`
2. Check logs: `sudo journalctl -u archivesmp-webapi.service -n 50`
3. Test uvicorn directly: `.venv/bin/uvicorn src.web.api:app --host 0.0.0.0 --port 8000`

## Service Management

```bash
# Start/stop/restart agents
sudo systemctl start archivesmp-endpoint-agent.service
sudo systemctl stop archivesmp-endpoint-agent.service
sudo systemctl restart archivesmp-endpoint-agent.service

# View logs
sudo journalctl -u archivesmp-endpoint-agent.service -f
sudo journalctl -u archivesmp-webapi.service -f

# Check status
sudo systemctl status archivesmp-endpoint-agent.service
sudo systemctl status archivesmp-webapi.service
```

## Next Steps

1. Deploy agents to both servers
2. Verify instance discovery
3. Parse baseline configs and populate config_rules table
4. Run initial drift detection
5. Review drift reports in web GUI
6. Create first configuration changes through GUI
