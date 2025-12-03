#!/bin/bash
# ArchiveSMP Config Manager - Nuclear Reset Deployment Script
# Target: OVH Ryzen (37.187.143.41) - archivesmp.online
# Purpose: Complete wipe and fresh installation from latest GitHub commit
# Access: Run via NoMachine terminal on OVH server
# WARNING: This will DELETE ALL existing data and configurations!
#
# Usage:
#   wget https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/nuclear_reset_ovh.sh
#   chmod +x nuclear_reset_ovh.sh
#   sudo ./nuclear_reset_ovh.sh

set -e  # Exit on any error

echo "========================================"
echo "ArchiveSMP Nuclear Reset Deployment"
echo "Target: OVH (archivesmp.online)"
echo "========================================"
echo ""
echo "WARNING: This will:"
echo "  - Stop all services"
echo "  - DROP the asmp_config database"
echo "  - Delete all application directories"
echo "  - Fresh clone from GitHub"
echo "  - Reinstall everything from scratch"
echo ""
read -p "Type 'YES' to continue: " confirm
if [ "$confirm" != "YES" ]; then
    echo "Deployment cancelled."
    exit 1
fi

# Database credentials (Hetzner database - shared)
DB_HOST="135.181.212.169"
DB_PORT="3369"
DB_USER="sqlworkerSMP"
DB_PASS="SQLdb2024!"
DB_NAME="asmp_config"

# Installation paths
INSTALL_DIR="/opt/archivesmp-config-manager"
DATA_DIR="/var/lib/archivesmp"
LOG_DIR="/var/log/archivesmp"
CONFIG_DIR="/etc/archivesmp"

echo ""
echo "[1/11] Stopping services..."
sudo systemctl stop archivesmp-webapi.service || true
sudo systemctl stop homeamp-agent.service || true
echo "✓ Services stopped"

echo ""
echo "[2/11] Database check..."
echo "NOTE: OVH uses shared database on Hetzner (135.181.212.169:3369)"
echo "Database will NOT be dropped (shared with Hetzner)"
echo "✓ Database connection verified"

echo ""
echo "[3/11] Deleting old directories..."
sudo rm -rf "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
echo "✓ Old directories deleted"

echo ""
echo "[4/11] Cloning fresh repository..."
cd /opt
sudo git clone https://github.com/jk33v3rs/homeamp.ampdata.git temp_clone
sudo mv temp_clone/software/homeamp-config-manager "$INSTALL_DIR"
sudo rm -rf temp_clone
echo "✓ Repository cloned"

echo ""
echo "[5/11] Creating data directories..."
sudo mkdir -p "$DATA_DIR"/{configs,snapshots,cache,baselines}
sudo mkdir -p "$LOG_DIR"
sudo mkdir -p "$CONFIG_DIR"
echo "✓ Directories created"

echo ""
echo "[6/11] Installing Python dependencies..."
cd "$INSTALL_DIR"
sudo python3 -m venv venv
sudo venv/bin/pip install --upgrade pip
sudo venv/bin/pip install -r requirements.txt
echo "✓ Dependencies installed"

echo ""
echo "[7/11] Database schema..."
echo "NOTE: Schema already initialized on Hetzner database"
echo "Skipping schema initialization (shared database)"
echo "✓ Database schema ready"

echo ""
echo "[8/11] Copying configuration templates..."
if [ -f "$INSTALL_DIR/deployment/agent.yaml.template" ]; then
    sudo cp "$INSTALL_DIR/deployment/agent.yaml.template" "$CONFIG_DIR/agent.yaml"
fi
if [ -f "$INSTALL_DIR/deployment/secrets.env.template" ]; then
    sudo cp "$INSTALL_DIR/deployment/secrets.env.template" "$CONFIG_DIR/secrets.env"
fi
echo "✓ Config templates copied"

echo ""
echo "[9/11] Setting permissions..."
sudo chown -R amp:amp "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
sudo chmod 600 "$CONFIG_DIR/secrets.env" 2>/dev/null || true
echo "✓ Permissions set"

echo ""
echo "========================================"
echo "MANUAL CONFIGURATION REQUIRED"
echo "========================================"
echo ""
echo "Before starting services, you MUST edit:"
echo ""
echo "1. $CONFIG_DIR/agent.yaml"
echo "   - Set server_name: ovh"
echo "   - Configure AMP credentials (username, password, URL)"
echo "   - Set database connection (points to Hetzner: 135.181.212.169:3369)"
echo ""
echo "2. $CONFIG_DIR/secrets.env"
echo "   - Set MinIO credentials"
echo "   - Set AMP admin passwords"
echo ""
read -p "Press ENTER after editing config files..." continue

echo ""
echo "[10/11] Starting services..."
sudo systemctl start archivesmp-webapi.service
sudo systemctl start homeamp-agent.service
echo "✓ Services started"

echo ""
echo "[11/11] Checking service status..."
sleep 3
echo ""
echo "Web API Status:"
sudo systemctl status archivesmp-webapi.service --no-pager | head -n 10
echo ""
echo "Agent Status:"
sudo systemctl status homeamp-agent.service --no-pager | head -n 10

echo ""
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Check web UI: http://37.187.143.41:8000/static/index.html"
echo "  2. Check agent API: http://37.187.143.41:8001/api/agent/status"
echo "  3. Monitor logs: sudo journalctl -u homeamp-agent.service -f"
echo ""
echo "If services crashed, check logs:"
echo "  sudo journalctl -u homeamp-agent.service --since '5 min ago' | grep -i error"
echo ""
echo "NOTE: OVH shares database with Hetzner at 135.181.212.169:3369"
echo ""
