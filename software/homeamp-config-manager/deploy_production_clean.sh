#!/bin/bash
# Production Deployment Script - ONE SHOT ONLY
# Deploys to Hetzner OR OVH with full dependency setup
# Usage: ./deploy_production_clean.sh [hetzner|ovh]

set -e  # Exit on any error

SERVER_TYPE="${1:-hetzner}"
INSTALL_DIR="/opt/archivesmp-config-manager"
REPO_URL="https://github.com/jk33v3rs/homeamp.ampdata.git"
VENV_DIR="${INSTALL_DIR}/software/homeamp-config-manager/venv"
PROJECT_DIR="${INSTALL_DIR}/software/homeamp-config-manager"

echo "========================================"
echo "ArchiveSMP Config Manager Deployment"
echo "Server: ${SERVER_TYPE}"
echo "========================================"

# Check we're running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo" 
   exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-venv python3-pip git mariadb-client unzip

# Create install directory
echo "Creating installation directory..."
mkdir -p ${INSTALL_DIR}
cd ${INSTALL_DIR}

# Clone repository
echo "Cloning repository..."
if [ -d ".git" ]; then
    echo "Repository exists, pulling latest..."
    git pull origin master
else
    git clone ${REPO_URL} .
fi

# Navigate to project directory
cd ${PROJECT_DIR}

# Create Python virtual environment
echo "Creating Python virtual environment..."
sudo -u amp python3 -m venv ${VENV_DIR}

# Install Python dependencies
echo "Installing Python dependencies..."
sudo -u amp ${VENV_DIR}/bin/pip install --upgrade pip
sudo -u amp ${VENV_DIR}/bin/pip install \
    mysql-connector-python \
    pymysql \
    requests \
    pyyaml \
    fastapi \
    uvicorn \
    python-multipart

# Create configuration directory
echo "Creating configuration directory..."
mkdir -p /etc/archivesmp
chmod 755 /etc/archivesmp

# Create settings file if it doesn't exist
if [ ! -f /etc/archivesmp/agent.yaml ]; then
    echo "Creating default agent configuration..."
    cat > /etc/archivesmp/agent.yaml <<EOF
# ArchiveSMP Configuration Manager Settings

database:
  production_db_host: "localhost:3306"
  production_db_name: "asmp_SQL"
  user: "archivesmp"
  password: ""

agent:
  polling:
    change_poll_interval: 300
    drift_check_interval: 3600
    health_check_interval: 60
  logging:
    level: "INFO"

web:
  server:
    host: "0.0.0.0"
    port: 8000
    workers: 4
    reload: false

safety:
  dry_run_by_default: false
  backup_retention_days: 30
  change_validation:
    require_backup: true
EOF
    chmod 644 /etc/archivesmp/agent.yaml
fi

# Create data directories
echo "Creating data directories..."
mkdir -p /var/lib/archivesmp/{backups,logs,temp}
chown -R amp:amp /var/lib/archivesmp

# Create systemd service for web API
echo "Creating systemd service for web API..."
cat > /etc/systemd/system/archivesmp-webapi.service <<EOF
[Unit]
Description=ArchiveSMP Config Manager Web API
After=network.target mariadb.service

[Service]
Type=simple
User=amp
Group=amp
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${VENV_DIR}/bin/uvicorn src.web.api:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for agent
echo "Creating systemd service for agent..."
cat > /etc/systemd/system/homeamp-agent.service <<EOF
[Unit]
Description=HomeAMP Configuration Agent
After=network.target mariadb.service

[Service]
Type=simple
User=amp
Group=amp
WorkingDirectory=${PROJECT_DIR}
Environment="PATH=${VENV_DIR}/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=${VENV_DIR}/bin/python3 src/agent/agent.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Deploy database schema
echo "Deploying database schema..."
if mysql -u root -e "USE asmp_SQL;" 2>/dev/null; then
    echo "Database exists, checking for schema updates..."
    # Run schema migrations
    if [ -f scripts/deploy_schema.py ]; then
        sudo -u amp ${VENV_DIR}/bin/python3 scripts/deploy_schema.py
    fi
else
    echo "Database doesn't exist - please create it first"
    exit 1
fi

# Load baseline configurations
echo "Loading baseline configurations..."
sudo -u amp ${VENV_DIR}/bin/python3 scripts/load_baselines.py

# Populate plugin metadata
echo "Populating plugin metadata..."
sudo -u amp ${VENV_DIR}/bin/python3 scripts/populate_plugin_metadata.py

# Sync with external APIs
echo "Syncing with Modrinth API..."
sudo -u amp ${VENV_DIR}/bin/python3 scripts/modrinth_sync.py

echo "Syncing with Hangar API..."
sudo -u amp ${VENV_DIR}/bin/python3 scripts/hangar_sync.py

echo "Tracking platform versions..."
sudo -u amp ${VENV_DIR}/bin/python3 scripts/platform_version_tracker.py

echo "Discovering documentation URLs..."
sudo -u amp ${VENV_DIR}/bin/python3 scripts/discover_docs.py

# Enable and start services
echo "Enabling and starting services..."
systemctl enable archivesmp-webapi
systemctl enable homeamp-agent

systemctl restart archivesmp-webapi
systemctl restart homeamp-agent

# Wait a moment for services to start
sleep 3

# Check service status
echo ""
echo "========================================"
echo "Service Status"
echo "========================================"
systemctl status archivesmp-webapi --no-pager || true
echo ""
systemctl status homeamp-agent --no-pager || true

echo ""
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo "Web API: http://localhost:8000"
echo "Logs: journalctl -u archivesmp-webapi -f"
echo "      journalctl -u homeamp-agent -f"
echo "========================================"
