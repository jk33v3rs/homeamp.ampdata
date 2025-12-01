# Production Deployment Checklist

## Pre-Deployment Verification

### Database Setup
- [ ] MariaDB installed and running
- [ ] Database `asmp_SQL` created
- [ ] User `archivesmp` created with password
- [ ] User has full permissions on `asmp_SQL`

```sql
CREATE DATABASE IF NOT EXISTS asmp_SQL CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'archivesmp'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON asmp_SQL.* TO 'archivesmp'@'localhost';
FLUSH PRIVILEGES;
```

### System Requirements
- [ ] Ubuntu/Debian 20.04+ or similar
- [ ] Python 3.9+
- [ ] User `amp` exists (AMP panel user)
- [ ] Port 8000 available for web API
- [ ] Git installed
- [ ] Network access to github.com

### Configuration
- [ ] Update `/etc/archivesmp/agent.yaml` with correct database password
- [ ] Update database host if not localhost
- [ ] Verify AMP instances are accessible

## Deployment Steps

### Hetzner (archivesmp.site - 135.181.212.169)

```bash
# SSH to server
ssh webadmin@135.181.212.169

# Download deployment script
wget https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deploy_production_clean.sh

# Make executable
chmod +x deploy_production_clean.sh

# Run deployment
sudo ./deploy_production_clean.sh hetzner
```

### OVH (archivesmp.online - 37.187.143.41)

```bash
# SSH to server
ssh webadmin@37.187.143.41

# Download deployment script
wget https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deploy_production_clean.sh

# Make executable
chmod +x deploy_production_clean.sh

# Run deployment
sudo ./deploy_production_clean.sh ovh
```

## Post-Deployment Verification

### Check Services
```bash
# Web API status
sudo systemctl status archivesmp-webapi

# Agent status
sudo systemctl status homeamp-agent

# View logs
sudo journalctl -u archivesmp-webapi -n 50
sudo journalctl -u homeamp-agent -n 50
```

### Test Web API
```bash
# Health check
curl http://localhost:8000/health

# List instances
curl http://localhost:8000/instances

# List plugins
curl http://localhost:8000/plugins
```

### Verify Database
```bash
mysql -u archivesmp -p asmp_SQL -e "
SELECT COUNT(*) as instances FROM instances;
SELECT COUNT(*) as plugins FROM plugins;
SELECT COUNT(*) as baselines FROM baseline_snapshots;
"
```

## Expected Results

- **Instances**: 11 (Hetzner), 0 (OVH - will be added later)
- **Plugins**: 150+ unique plugins
- **Baselines**: 82 universal configs
- **Web API**: Accessible on port 8000
- **Agent**: Running, no errors in logs

## Troubleshooting

### Database Connection Errors
```bash
# Edit config
sudo nano /etc/archivesmp/agent.yaml

# Update password
# Restart services
sudo systemctl restart archivesmp-webapi homeamp-agent
```

### Permission Errors
```bash
# Fix ownership
sudo chown -R amp:amp /opt/archivesmp-config-manager/software/homeamp-config-manager
sudo chown -R amp:amp /var/lib/archivesmp
```

### Service Won't Start
```bash
# Check logs
sudo journalctl -xeu archivesmp-webapi
sudo journalctl -xeu homeamp-agent

# Test manually
cd /opt/archivesmp-config-manager/software/homeamp-config-manager
sudo -u amp venv/bin/python3 src/web/api.py
sudo -u amp venv/bin/python3 src/agent/agent.py
```

### Missing Python Modules
```bash
cd /opt/archivesmp-config-manager/software/homeamp-config-manager
sudo -u amp venv/bin/pip install mysql-connector-python pymysql requests pyyaml fastapi uvicorn python-multipart
```

## Rollback Plan

If deployment fails:

```bash
# Stop services
sudo systemctl stop archivesmp-webapi homeamp-agent

# Disable services
sudo systemctl disable archivesmp-webapi homeamp-agent

# Remove installation
sudo rm -rf /opt/archivesmp-config-manager

# Remove service files
sudo rm /etc/systemd/system/archivesmp-webapi.service
sudo rm /etc/systemd/system/homeamp-agent.service

# Reload systemd
sudo systemctl daemon-reload
```

## Success Criteria

✅ Both services running without errors
✅ Web API responding to HTTP requests
✅ Database populated with 82 baselines
✅ Agent discovering instances
✅ No errors in journalctl logs
✅ Port 8000 accessible
