# HomeAMP V2.0 - Production Deployment Guide

## Server: Hetzner Xeon (archivesmp.site - 135.181.212.169)

### Prerequisites

**System Requirements:**
- Ubuntu/Debian Linux
- Python 3.11+
- MariaDB 10.5+
- Git
- Systemd

**Users:**
- `webadmin` - sudo access, deployment user
- `amp` - service user (runs homeamp services)

---

## 1. Initial Server Setup

**Run all commands as webadmin user with sudo access.**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip git mariadb-server mariadb-client build-essential pkg-config default-libmysqlclient-dev

# Create amp user (if doesn't exist)
sudo useradd -m -s /bin/bash amp

# Add amp to necessary groups
sudo usermod -aG adm amp

# Create project directory with correct ownership from the start
sudo mkdir -p /opt/homeamp
sudo chown -R amp:amp /opt/homeamp
sudo chmod -R 755 /opt/homeamp

# Create log directory with correct ownership
sudo mkdir -p /var/log/homeamp
sudo chown -R amp:amp /var/log/homeamp
sudo chmod -R 755 /var/log/homeamp
```

---

## 2. Database Setup

```bash
# Secure MariaDB installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
CREATE DATABASE homeamp_v2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'homeamp'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON homeamp_v2.* TO 'homeamp'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**Configure MariaDB (REQUIRED):**

Edit `/etc/mysql/mariadb.conf.d/50-server.cnf`:
```ini
[mysqld]
# SECURITY: Non-default port (obscurity layer)
port = 3369

# Bind address (localhost only for security, or 0.0.0.0 if remote access needed)
bind-address = 127.0.0.1
```

**If remote access needed from other servers (e.g., OVH):**
```ini
bind-address = 0.0.0.0
```

Then grant remote access:
```sql
GRANT ALL PRIVILEGES ON homeamp_v2.* TO 'homeamp'@'%' IDENTIFIED BY 'your_secure_password';
FLUSH PRIVILEGES;
```

**Restart MariaDB:**
```bash
sudo systemctl restart mariadb

# Verify it's listening on port 3369
sudo netstat -tulpn | grep 3369
```

---

## 3. Clone Repository

**CRITICAL: Run as amp user to ensure correct ownership.**

```bash
# Switch to amp user
sudo -u amp bash

# Clone repository
cd /opt/homeamp
git clone https://github.com/jk33v3rs/homeamp.ampdata.git
## 4. Python Environment Setup

**CRITICAL: All commands must run as amp user to avoid permission errors.**

```bash
# Switch to amp user
sudo -u amp bash

# Create virtual environment
cd /opt/homeamp
python3.11 -m venv venv

# Verify venv ownership
ls -la /opt/homeamp/venv

# Upgrade pip
## 5. Configuration

**Run as amp user to ensure correct file ownership.**

```bash
# Switch to amp user
sudo -u amp bash

# Navigate to project
cd /opt/homeamp/homeamp.ampdata/homeamp-v2

# Copy example config
cp .env.example .env

# Edit configuration
nano .env

# After editing, verify ownership
ls -la .env

# Exit amp user shell
exit
```nstall homeamp-v2 in editable mode
/opt/homeamp/venv/bin/pip install -e .

# Verify installation succeeded
/opt/homeamp/venv/bin/pip list | grep homeamp

# Exit amp user shell
exit
```

**Expected output from pip install:**
- Should show "Successfully installed homeamp-v2"
- Should list all dependencies (fastapi, uvicorn, sqlalchemy, etc.)
- NO permission errors
- NO build failuresbash
# As amp user
sudo -u amp python3.11 -m venv /opt/homeamp/venv
## 6. Database Migration

**Run as amp user with PYTHONPATH set.**

```bash
# Switch to amp user
sudo -u amp bash

# Navigate to project
cd /opt/homeamp/homeamp.ampdata/homeamp-v2

# Set PYTHONPATH and run migrations
PYTHONPATH=/opt/homeamp/homeamp.ampdata/homeamp-v2/src /opt/homeamp/venv/bin/alembic upgrade head

# Verify migrations succeeded (should show current revision)
PYTHONPATH=/opt/homeamp/homeamp.ampdata/homeamp-v2/src /opt/homeamp/venv/bin/alembic current

# Exit amp user shell
exit
```

**Expected output:**
- Should show "Running upgrade..." messages
- Should end with "INFO [alembic.runtime.migration] Running upgrade -> <revision>, <description>"
- NO "ModuleNotFoundError: No module named 'homeamp_v2'"
- NO database connection errors
- NO permission errorso -u amp /opt/homeamp/venv/bin/pip install -e .
```

---

## 5. Configuration

```bash
# Copy example config
sudo -u amp cp .env.example .env

# Edit configuration
sudo -u amp nano .env
```

**Required `.env` settings:**

```ini
# Database - SQLAlchemy URL format (the +pymysql is required)
# Format: mysql+pymysql://username:password@host:port/database
# CRITICAL: Port 3369 matches MariaDB configuration from step 2
DATABASE_URL=mysql+pymysql://homeamp:YOUR_ACTUAL_PASSWORD_HERE@localhost:3369/homeamp_v2

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Environment
ENVIRONMENT=production
DEBUG=false

# Paths (adjust for your AMP installation)
AMP_BASE_PATH=/home/amp/.ampdata/instances

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/homeamp/api.log

# Agent Settings
AGENT_SCAN_INTERVAL=300
AGENT_UPDATE_CHECK_INTERVAL=3600
```

---

## 6. Database Migration

```bash
# Run Alembic migrations
cd /opt/homeamp/homeamp.ampdata/homeamp-v2
sudo -u amp /opt/homeamp/venv/bin/alembic upgrade head
```

---

## 7. Systemd Service Configuration

### API Service

Create `/etc/systemd/system/homeamp-api.service`:

```ini
[Unit]
Description=HomeAMP V2.0 API Service
After=network.target mariadb.service
Requires=mariadb.service

---

## 8. Verify Permissions (CRITICAL)

**Before starting services, verify all permissions are correct.**

```bash
# Check /opt/homeamp ownership (should be amp:amp)
ls -la /opt/homeamp

# Check repository ownership (should be amp:amp)
ls -la /opt/homeamp/homeamp.ampdata

# Check venv ownership (should be amp:amp)
ls -la /opt/homeamp/venv

# Check log directory ownership (should be amp:amp)
ls -la /var/log/homeamp

# If any ownership is wrong, fix it:
sudo chown -R amp:amp /opt/homeamp
sudo chown -R amp:amp /var/log/homeamp
```

**Expected output:**
- All files/directories under /opt/homeamp should show "amp amp"
- All files/directories under /var/log/homeamp should show "amp amp"
- NO files owned by root, webadmin, or other usersndardOutput=journal
StandardError=journal
SyslogIdentifier=homeamp-api

[Install]
WantedBy=multi-user.target
```

### Agent Service

Create `/etc/systemd/system/homeamp-agent.service`:

```ini
[Unit]
Description=HomeAMP V2.0 Discovery Agent
After=network.target mariadb.service homeamp-api.service
Requires=mariadb.service

[Service]
Type=simple
User=amp
Group=amp
WorkingDirectory=/opt/homeamp/homeamp.ampdata/homeamp-v2
Environment="PATH=/opt/homeamp/venv/bin"
Environment="PYTHONPATH=/opt/homeamp/homeamp.ampdata/homeamp-v2/src"
ExecStart=/opt/homeamp/venv/bin/python -m homeamp_v2.agent
Restart=always
RestartSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=homeamp-agent

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable homeamp-api
sudo systemctl enable homeamp-agent

# Start services
sudo systemctl start homeamp-api
sudo systemctl start homeamp-agent

# Check status
sudo systemctl status homeamp-api
sudo systemctl status homeamp-agent
```

---

## 8. Logging Setup

```bash
# Create log directory
sudo mkdir -p /var/log/homeamp
sudo chown amp:amp /var/log/homeamp

# View logs
journalctl -u homeamp-api -f
journalctl -u homeamp-agent -f
```

---

## 9. Firewall Configuration

```bash
# Allow API port (if using UFW)
sudo ufw allow 8000/tcp

# For external access, configure reverse proxy (recommended)
```

---

## 10. Nginx Reverse Proxy (Optional but Recommended)

Install Nginx:
```bash
sudo apt install -y nginx
```

Create `/etc/nginx/sites-available/homeamp`:

```nginx
server {
    listen 80;
    server_name archivesmp.site;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/homeamp/homeamp.ampdata/homeamp-v2/src/web/static;
        expires 30d;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/homeamp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 11. Verification

```bash
# Check services are running
sudo systemctl status homeamp-api
sudo systemctl status homeamp-agent

# Check API is responding
curl http://localhost:8000/health
### Service won't start

Check logs:
```bash
journalctl -u homeamp-api -n 100 --no-pager
journalctl -u homeamp-agent -n 100 --no-pager
```

Common issues:

**Permission Denied Errors:**
```bash
# Fix all ownership
sudo chown -R amp:amp /opt/homeamp
sudo chown -R amp:amp /var/log/homeamp

# Verify
ls -la /opt/homeamp | head -20
ls -la /opt/homeamp/venv | head -20

# Restart services
sudo systemctl restart homeamp-api
sudo systemctl restart homeamp-agent
```

**Database connection failure:**
```bash
# Test database connection as amp user
sudo -u amp mysql -u homeamp -p homeamp_v2

# Check credentials in .env match database
cat /opt/homeamp/homeamp.ampdata/homeamp-v2/.env | grep DATABASE_URL
```

**Port already in use:**
```bash
# Check what's using port 8000
sudo netstat -tulpn | grep 8000

# Kill existing process if needed
sudo kill <PID>
```

**Missing dependencies:**
```bash
# Reinstall as amp user
sudo -u amp bash
cd /opt/homeamp/homeamp.ampdata/homeamp-v2
/opt/homeamp/venv/bin/pip install -e .
exit
```

**Module import errors:**
```bash
# Verify PYTHONPATH is set in service file
grep PYTHONPATH /etc/systemd/system/homeamp-api.service
grep PYTHONPATH /etc/systemd/system/homeamp-agent.service

## Quick Reference Commands

```bash
# Service management
sudo systemctl start homeamp-api
sudo systemctl start homeamp-agent
sudo systemctl stop homeamp-api
sudo systemctl stop homeamp-agent
sudo systemctl restart homeamp-api
sudo systemctl restart homeamp-agent
sudo systemctl status homeamp-api
sudo systemctl status homeamp-agent

# Logs (real-time)
journalctl -u homeamp-api -f
journalctl -u homeamp-agent -f
journalctl -u homeamp-api -u homeamp-agent -f

# Logs (last 100 lines)
journalctl -u homeamp-api -n 100 --no-pager
journalctl -u homeamp-agent -n 100 --no-pager

# Update deployment (ALWAYS as amp user)
sudo -u amp bash
cd /opt/homeamp/homeamp.ampdata
git pull origin master
exit
sudo systemctl restart homeamp-api homeamp-agent

# Database migrations (ALWAYS as amp user with PYTHONPATH)
sudo -u amp bash
cd /opt/homeamp/homeamp.ampdata/homeamp-v2
PYTHONPATH=/opt/homeamp/homeamp.ampdata/homeamp-v2/src /opt/homeamp/venv/bin/alembic upgrade head
exit

# Manual discovery scan
curl -X POST http://localhost:8000/api/instances/scan

# Check permissions (if anything breaks)
sudo chown -R amp:amp /opt/homeamp
sudo chown -R amp:amp /var/log/homeamp
ls -la /opt/homeamp | head -20
ls -la /opt/homeamp/venv | head -20

# Verify services are actually running
ps aux | grep homeamp
sudo netstat -tulpn | grep 8000
```irect API: `http://135.181.212.169:8000`
- With Nginx: `http://archivesmp.site`

**Available endpoints:**
- `/` - Web UI Dashboard
- `/api` - API info
- `/health` - Health check
- `/docs` - OpenAPI documentation (Swagger UI)
- `/redoc` - ReDoc API documentation

---

## 14. Monitoring & Maintenance

### View Logs
```bash
# API logs
journalctl -u homeamp-api -f

# Agent logs
journalctl -u homeamp-agent -f

# Combined
journalctl -u homeamp-api -u homeamp-agent -f
```

### Restart Services
```bash
sudo systemctl restart homeamp-api
sudo systemctl restart homeamp-agent
```

### Update Code
```bash
cd /opt/homeamp/homeamp.ampdata
sudo -u amp git pull origin master
sudo systemctl restart homeamp-api
sudo systemctl restart homeamp-agent
```

### Database Backups
```bash
# Backup
mysqldump -u homeamp -p homeamp_v2 > homeamp_backup_$(date +%Y%m%d).sql

# Restore
mysql -u homeamp -p homeamp_v2 < homeamp_backup_20251128.sql
```

---

## 15. Troubleshooting

### Service won't start

Check logs:
```bash
journalctl -u homeamp-api -n 100 --no-pager
```

Common issues:
- Database connection failure (check credentials in `.env`)
- Port already in use (check with `netstat -tulpn | grep 8000`)
- Permission issues (ensure `amp` user owns files)
- Missing dependencies (reinstall with `pip install -e .`)

### Agent not discovering instances

Check:
- `AMP_BASE_PATH` in `.env` points to correct directory
- `amp` user has read access to AMP instance directories
- Agent logs show scan attempts: `journalctl -u homeamp-agent -f`

### Database connection errors

Test connection:
```bash
mysql -u homeamp -p -h localhost homeamp_v2
```

Check MariaDB is running:
```bash
sudo systemctl status mariadb
```

### Web UI not loading

Check:
- API service is running
- Static files exist in `src/web/static/`
- Browser console for JavaScript errors
- Network tab shows API calls succeeding

---

## 16. Security Considerations

**Production Checklist:**

- [ ] Change default database password
- [ ] Configure firewall (UFW/iptables)
- [ ] Use Nginx reverse proxy with SSL (Let's Encrypt)
- [ ] Set `DEBUG=false` in `.env`
- [ ] Restrict MariaDB bind address if not needed remotely
- [ ] Regular database backups (cron job)
- [ ] Keep system packages updated
- [ ] Monitor logs for suspicious activity
- [ ] Use strong passwords for all accounts

---

## Quick Reference Commands

```bash
# Service management
sudo systemctl start|stop|restart|status homeamp-api
sudo systemctl start|stop|restart|status homeamp-agent

# Logs
journalctl -u homeamp-api -f
journalctl -u homeamp-agent -f

# Update deployment
cd /opt/homeamp/homeamp.ampdata && sudo -u amp git pull
sudo systemctl restart homeamp-api homeamp-agent

# Database migrations
cd /opt/homeamp/homeamp.ampdata/homeamp-v2
/opt/homeamp/venv/bin/alembic upgrade head

# Manual discovery scan
curl -X POST http://localhost:8000/api/instances/scan
```

---

## Post-Deployment Verification

After deployment, verify:

1. ✅ API responds to health check: `curl http://localhost:8000/health`
2. ✅ Web UI loads: Visit `http://archivesmp.site` in browser
3. ✅ Dashboard shows stats (after agent scan completes)
4. ✅ Instances discovered (check Instances page)
5. ✅ Plugins detected (check Plugins page)
6. ✅ Services auto-start on reboot: `sudo reboot` and verify

---

**Deployment Complete!** 🚀

Access your HomeAMP V2.0 instance at: **http://archivesmp.site**
