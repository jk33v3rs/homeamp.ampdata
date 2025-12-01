#!/bin/bash
# ArchiveSMP Configuration Manager - Deployment Script
# 
# This script deploys the config manager to Hetzner or OVH servers.
# Run this script ON THE TARGET SERVER (not from your dev machine).
#
# Usage:
#   sudo bash deploy.sh hetzner   # Deploy to Hetzner (with Web API)
#   sudo bash deploy.sh ovh       # Deploy to OVH (agent only)

# Colors for output
RED='\033[0.31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=================================================="
echo "ArchiveSMP Configuration Manager - Deployment"
echo -e "==================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}ERROR: This script must be run as root (use sudo)${NC}"
  exit 1
fi

# Get server type
SERVER_TYPE=$1
if [[ "$SERVER_TYPE" != "hetzner" ]] && [[ "$SERVER_TYPE" != "ovh" ]]; then
  echo -e "${RED}ERROR: Invalid server type${NC}"
  echo "Usage: sudo bash deploy.sh [hetzner|ovh]"
  exit 1
fi

echo -e "${YELLOW}Server Type: $SERVER_TYPE${NC}"
echo ""

# Configuration
INSTALL_DIR="/opt/archivesmp-config-manager"
CONFIG_DIR="/etc/archivesmp"
DATA_DIR="/var/lib/archivesmp"
LOG_DIR="/var/log/archivesmp"
REPO_URL="https://github.com/jk33v3rs/homeamp.ampdata.git"
REPO_SUBDIR="software/homeamp-config-manager"

# Step 1: Install system dependencies
echo -e "${YELLOW}[1/9] Installing system dependencies...${NC}"
apt-get update || echo "Warning: apt-get update had errors, continuing anyway..."
apt-get install -y python3 python3-pip python3-venv git curl

# Step 2: Create directories
echo -e "${YELLOW}[2/9] Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"/{reports,backups,baselines,reviews,pending_changes,change_history,expectations,reference_data}
mkdir -p "$LOG_DIR"

# Step 3: Clone repository (or pull latest)
echo -e "${YELLOW}[3/9] Fetching code from GitHub...${NC}"
echo "Cloning repository..."
cd /opt

# Create timestamped temp directory
TEMP_DIR="homeamp_deploy_$(date +%Y%m%d%H%M%S)"
git clone "$REPO_URL" "$TEMP_DIR"

echo "Copying files to installation directory..."
# Use cp -r to handle existing directories properly
cp -rf "$TEMP_DIR/$REPO_SUBDIR"/* "$INSTALL_DIR/"

echo "Cleaning up temporary clone..."
rm -rf "$TEMP_DIR"

cd "$INSTALL_DIR"

# Step 4: Install Python dependencies
echo -e "${YELLOW}[4/9] Installing Python dependencies...${NC}"
# Create virtual environment if it doesn't exist
if [ ! -d "$INSTALL_DIR/venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$INSTALL_DIR/venv"
fi

# Activate virtual environment and install dependencies
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
  echo "Installing from requirements.txt..."
  pip install -r requirements.txt
else
  echo -e "${RED}ERROR: requirements.txt not found!${NC}"
  exit 1
fi

# Step 5: Configure agent.yaml
echo -e "${YELLOW}[5/9] Configuring agent...${NC}"
if [ ! -f "$CONFIG_DIR/agent.yaml" ]; then
  echo "Creating agent config from template..."
  cp deployment/agent.yaml.template "$CONFIG_DIR/agent.yaml"
  
  # Set server name based on deployment target
  if [ "$SERVER_TYPE" == "hetzner" ]; then
    sed -i 's/server_name: "HETZNER"/server_name: "HETZNER"/' "$CONFIG_DIR/agent.yaml"
  else
    sed -i 's/server_name: "HETZNER"/server_name: "OVH"/' "$CONFIG_DIR/agent.yaml"
  fi
  
  echo -e "${GREEN}✓ Created $CONFIG_DIR/agent.yaml${NC}"
else
  echo -e "${YELLOW}⚠ agent.yaml already exists, skipping${NC}"
fi

# Step 6: Configure secrets
echo -e "${YELLOW}[6/9] Setting up secrets...${NC}"
if [ ! -f "$CONFIG_DIR/secrets.env" ]; then
  cp deployment/secrets.env.template "$CONFIG_DIR/secrets.env"
  chmod 600 "$CONFIG_DIR/secrets.env"
  echo -e "${RED}⚠ IMPORTANT: Edit $CONFIG_DIR/secrets.env with your credentials${NC}"
else
  echo -e "${YELLOW}⚠ secrets.env already exists, skipping${NC}"
fi

# Step 7: Install systemd services
echo -e "${YELLOW}[7/9] Installing systemd services...${NC}"

# Always install agent and agent API
cp deployment/homeamp-agent.service /etc/systemd/system/
cp deployment/archivesmp-agent-api.service /etc/systemd/system/

# Only install Web API on Hetzner
if [ "$SERVER_TYPE" == "hetzner" ]; then
  cp deployment/archivesmp-webapi.service /etc/systemd/system/
  echo -e "${GREEN}✓ Installed Web API service (Hetzner only)${NC}"
fi

systemctl daemon-reload
echo -e "${GREEN}✓ Systemd services installed${NC}"

# Step 8: Set permissions
echo -e "${YELLOW}[8/9] Setting permissions...${NC}"
chown -R amp:amp "$INSTALL_DIR"
chown -R amp:amp "$DATA_DIR"
chown -R amp:amp "$LOG_DIR"
chmod 755 "$INSTALL_DIR"

# Step 9: Start services
echo -e "${YELLOW}[9/9] Starting services...${NC}"

# Enable and start agent
systemctl enable homeamp-agent.service
systemctl enable archivesmp-agent-api.service

# Only start Web API on Hetzner
if [ "$SERVER_TYPE" == "hetzner" ]; then
  systemctl enable archivesmp-webapi.service
  systemctl start archivesmp-webapi.service
fi

systemctl start homeamp-agent.service
systemctl start archivesmp-agent-api.service

echo ""
echo -e "${GREEN}=================================================="
echo "Deployment Complete!"
echo -e "==================================================${NC}"
echo ""
echo "Services installed:"
echo "  • homeamp-agent (background monitoring)"
echo "  • archivesmp-agent-api (local API on port 8001)"

if [ "$SERVER_TYPE" == "hetzner" ]; then
  echo "  • archivesmp-webapi (web UI on port 8000)"
fi

echo ""
echo "Check service status:"
echo "  sudo systemctl status homeamp-agent"
echo "  sudo systemctl status archivesmp-agent-api"

if [ "$SERVER_TYPE" == "hetzner" ]; then
  echo "  sudo systemctl status archivesmp-webapi"
fi

echo ""
echo "View logs:"
echo "  sudo journalctl -u homeamp-agent -f"
echo "  sudo journalctl -u archivesmp-agent-api -f"

if [ "$SERVER_TYPE" == "hetzner" ]; then
  echo "  sudo journalctl -u archivesmp-webapi -f"
  echo ""
  echo -e "${GREEN}Web UI available at: http://135.181.212.169:8000${NC}"
fi

echo ""
echo -e "${RED}⚠ NEXT STEPS:${NC}"
echo "1. Edit MinIO credentials in: $CONFIG_DIR/secrets.env"
echo "2. Restart services: sudo systemctl restart homeamp-agent archivesmp-agent-api"

if [ "$SERVER_TYPE" == "hetzner" ]; then
  echo "3. Restart Web API: sudo systemctl restart archivesmp-webapi"
  echo "4. Ensure MinIO is running: sudo systemctl status minio"
fi

echo ""
