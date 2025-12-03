# Nuclear Reset Deployment Instructions

## Complete Fresh Start - Step by Step

### Prerequisites
- NoMachine access to target server
- Terminal open on the server

---

## For Hetzner (135.181.212.169)

### Step 1: Download the script from GitHub
```bash
cd ~
wget https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/nuclear_reset_hetzner.sh
```

### Step 2: Make it executable
```bash
chmod +x nuclear_reset_hetzner.sh
```

### Step 3: Run the script
```bash
sudo ./nuclear_reset_hetzner.sh
```

### Step 4: Follow the prompts
- Type `YES` to confirm nuclear reset
- Wait for steps 1-9 to complete
- **PAUSE at step 9** - Edit config files:
  - `/etc/archivesmp/agent.yaml` - Set server_name: hetzner, AMP credentials, database config
  - `/etc/archivesmp/secrets.env` - Set MinIO credentials, AMP passwords
- Press ENTER to continue
- Services will start automatically

### Step 5: Verify deployment
```bash
# Check web UI
curl http://135.181.212.169:8000/static/index.html

# Check agent status
curl http://135.181.212.169:8001/api/agent/status

# Monitor logs
sudo journalctl -u homeamp-agent.service -f
```

---

## For OVH (37.187.143.41)

**⚠️ ONLY deploy to OVH AFTER Hetzner is validated and working!**

### Step 1: Download the script from GitHub
```bash
cd ~
wget https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/nuclear_reset_ovh.sh
```

### Step 2: Make it executable
```bash
chmod +x nuclear_reset_ovh.sh
```

### Step 3: Run the script
```bash
sudo ./nuclear_reset_ovh.sh
```

### Step 4: Follow the prompts
- Type `YES` to confirm nuclear reset
- Wait for steps 1-9 to complete
- **PAUSE at step 9** - Edit config files:
  - `/etc/archivesmp/agent.yaml` - Set server_name: ovh, AMP credentials, database config (points to Hetzner DB)
  - `/etc/archivesmp/secrets.env` - Set MinIO credentials, AMP passwords
- Press ENTER to continue
- Services will start automatically

### Step 5: Verify deployment
```bash
# Check web UI
curl http://37.187.143.41:8000/static/index.html

# Check agent status
curl http://37.187.143.41:8001/api/agent/status

# Monitor logs
sudo journalctl -u homeamp-agent.service -f
```

---

## What the Scripts Do

1. **Stop services** - archivesmp-webapi.service, homeamp-agent.service
2. **Drop database** (Hetzner only) - DROP DATABASE asmp_config; CREATE DATABASE asmp_config;
3. **Delete directories** - /opt/archivesmp-config-manager, /var/lib/archivesmp, /var/log/archivesmp
4. **Fresh clone** - Latest code from GitHub master branch
5. **Create directories** - /var/lib/archivesmp/{configs,snapshots,cache,baselines}
6. **Install dependencies** - Python venv + pip install -r requirements.txt
7. **Initialize schema** (Hetzner only) - Load src/database/schema.sql
8. **Copy config templates** - agent.yaml.template, secrets.env.template to /etc/archivesmp/
9. **Set permissions** - chown amp:amp all directories
10. **Start services** - archivesmp-webapi.service, homeamp-agent.service
11. **Show status** - Display service status and next steps

---

## Troubleshooting

### Services failed to start
```bash
# Check logs for errors
sudo journalctl -u homeamp-agent.service --since "5 min ago" | grep -i error
sudo journalctl -u archivesmp-webapi.service --since "5 min ago" | grep -i error
```

### Database connection failed
```bash
# Test database connection
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p asmp_config
# Password: SQLdb2024!
```

### Web UI not accessible
```bash
# Check if port 8000 is listening
sudo netstat -tlnp | grep 8000

# Check web API service
sudo systemctl status archivesmp-webapi.service
```

### Agent crashed immediately
```bash
# Full agent logs
sudo journalctl -u homeamp-agent.service -n 100 --no-pager

# Check config file syntax
cat /etc/archivesmp/agent.yaml
```

---

## Post-Deployment Checklist

- [ ] Web UI accessible (http://SERVER_IP:8000/static/index.html)
- [ ] Agent discovering instances (check /api/agent/status)
- [ ] Database populated with instances
- [ ] No crashes in logs for 5 minutes
- [ ] Drift detector running without errors
- [ ] Config files properly edited (no template placeholders)
