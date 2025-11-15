# Quick Deployment Commands for ArchiveSMP Config Manager

## From Your PC

### Deploy to Hetzner (with Web API)

```bash
# SSH to Hetzner
ssh amp@135.181.212.169

# Download and run deployment script
curl -sSL https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/deploy_hetzner.sh | bash

# Or if repo is already cloned:
cd /opt/archivesmp-config-manager/software/homeamp-config-manager
bash deployment/deploy_hetzner.sh
```

### Deploy to OVH (agent only)

```bash
# SSH to OVH
ssh amp@37.187.143.41

# Download and run deployment script
curl -sSL https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/deploy_ovh.sh | bash

# Or if repo is already cloned:
cd /opt/archivesmp-config-manager/software/homeamp-config-manager
bash deployment/deploy_ovh.sh
```

## Manual Steps (if needed)

### Hetzner Full Deployment

```bash
ssh amp@135.181.212.169

# Update repo
cd /opt/archivesmp-config-manager && git pull

# Install deps
cd software/homeamp-config-manager
.venv/bin/pip install mysql-connector-python pyyaml fastapi uvicorn

# Start services
sudo systemctl enable archivesmp-endpoint-agent.service
sudo systemctl enable archivesmp-webapi.service
sudo systemctl restart archivesmp-endpoint-agent.service
sudo systemctl restart archivesmp-webapi.service

# Check logs
sudo journalctl -u archivesmp-endpoint-agent.service -f
sudo journalctl -u archivesmp-webapi.service -f
```

### OVH Agent Only

```bash
ssh amp@37.187.143.41

# Update repo
cd /opt/archivesmp-config-manager && git pull

# Install deps
cd software/homeamp-config-manager
.venv/bin/pip install mysql-connector-python pyyaml

# Start service
sudo systemctl enable archivesmp-endpoint-agent.service
sudo systemctl restart archivesmp-endpoint-agent.service

# Check logs
sudo journalctl -u archivesmp-endpoint-agent.service -f
```

## Verification

### Check Agent Discovery

```bash
# On Hetzner
sudo journalctl -u archivesmp-endpoint-agent.service --since "5 min ago" | grep "Discovered"

# On OVH
sudo journalctl -u archivesmp-endpoint-agent.service --since "5 min ago" | grep "Discovered"
```

### Test Web API (Hetzner only)

```bash
# From Hetzner
curl http://localhost:8000/api/instances
curl http://localhost:8000/api/servers
curl http://localhost:8000/api/groups

# Or open in browser (via SSH tunnel from your PC):
ssh -L 8000:localhost:8000 amp@135.181.212.169
# Then visit: http://localhost:8000/
```

### Check for Drift

```bash
# Agents log drift when configs don't match database
sudo journalctl -u archivesmp-endpoint-agent.service | grep DRIFT
```

## Update After Code Changes

```bash
# On both servers
cd /opt/archivesmp-config-manager && git pull
sudo systemctl restart archivesmp-endpoint-agent.service

# On Hetzner also restart web API
sudo systemctl restart archivesmp-webapi.service
```
