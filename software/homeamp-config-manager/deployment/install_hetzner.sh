#!/bin/bash
# ArchiveSMP Configuration Manager - Hetzner Installer
# Run this on Hetzner server with: bash <(curl -fsSL https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/install_hetzner.sh)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}  ArchiveSMP Config Manager - Hetzner Installation${NC}"
echo -e "${GREEN}========================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}ERROR: This script must be run as root${NC}"
  echo "Try: sudo bash install_hetzner.sh"
  exit 1
fi

# Configuration
INSTALL_DIR="/opt/archivesmp-config-manager"
CONFIG_DIR="/etc/archivesmp"
DATA_DIR="/var/lib/archivesmp"
LOG_DIR="/var/log/archivesmp"
REPO_URL="https://github.com/jk33v3rs/homeamp.ampdata.git"
REPO_SUBDIR="software/homeamp-config-manager"

echo -e "${YELLOW}[1/7] Installing system dependencies...${NC}"
apt-get update -qq || true
apt-get install -y python3 python3-pip python3-venv git curl

echo -e "${YELLOW}[2/7] Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR"/{reports,backups,baselines,reviews,pending_changes,change_history,expectations,reference_data}
mkdir -p "$LOG_DIR"

echo -e "${YELLOW}[3/7] Fetching code from GitHub...${NC}"
cd /opt
TEMP_DIR="homeamp_deploy_$(date +%Y%m%d%H%M%S)"
git clone --depth 1 "$REPO_URL" "$TEMP_DIR"
cp -rf "$TEMP_DIR/$REPO_SUBDIR"/* "$INSTALL_DIR/"
rm -rf "$TEMP_DIR"
cd "$INSTALL_DIR"

echo -e "${YELLOW}[4/7] Installing Python dependencies...${NC}"
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt
echo -e "${GREEN}✓ Python packages installed${NC}"

echo -e "${YELLOW}[5/7] Creating configuration files...${NC}"

# Create agent config
cat > "$CONFIG_DIR/agent.yaml" << 'EOF'
agent:
  server_name: "HETZNER"
  amp_data_path: "/home/amp/.ampdata/instances"
  polling:
    change_poll_interval: 30
    drift_check_interval: 3600
    health_check_interval: 300

storage:
  minio:
    endpoint: "localhost:9000"
    secure: false
EOF

echo -e "${GREEN}✓ Created $CONFIG_DIR/agent.yaml${NC}"

echo -e "${YELLOW}[6/7] Installing systemd services...${NC}"

# Install homeamp-agent service
cp deployment/homeamp-agent.service /etc/systemd/system/
echo -e "${GREEN}✓ Installed homeamp-agent.service${NC}"

# Install archivesmp-webapi service (Hetzner only)
if [ -f "deployment/archivesmp-webapi.service" ]; then
  cp deployment/archivesmp-webapi.service /etc/systemd/system/
  echo -e "${GREEN}✓ Installed archivesmp-webapi.service${NC}"
fi

# Install agent API service
if [ -f "deployment/archivesmp-agent-api.service" ]; then
  cp deployment/archivesmp-agent-api.service /etc/systemd/system/
  echo -e "${GREEN}✓ Installed archivesmp-agent-api.service${NC}"
fi

systemctl daemon-reload

echo -e "${YELLOW}[7/7] Setting permissions...${NC}"
chown -R amp:amp "$INSTALL_DIR"
chown -R amp:amp "$DATA_DIR"
chown -R amp:amp "$LOG_DIR"
chmod 644 "$CONFIG_DIR/agent.yaml"

echo ""
echo -e "${GREEN}========================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}========================================================${NC}"
echo ""
echo -e "${YELLOW}Services installed:${NC}"
echo "  • homeamp-agent (background monitoring)"
echo "  • archivesmp-webapi (web UI on port 8000)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Start the agent:"
echo "   ${GREEN}sudo systemctl enable homeamp-agent${NC}"
echo "   ${GREEN}sudo systemctl start homeamp-agent${NC}"
echo ""
echo "2. Start the web API:"
echo "   ${GREEN}sudo systemctl enable archivesmp-webapi${NC}"
echo "   ${GREEN}sudo systemctl start archivesmp-webapi${NC}"
echo ""
echo "3. Check status:"
echo "   ${GREEN}sudo systemctl status homeamp-agent${NC}"
echo "   ${GREEN}sudo systemctl status archivesmp-webapi${NC}"
echo ""
echo "4. View logs:"
echo "   ${GREEN}sudo journalctl -u homeamp-agent -f${NC}"
echo "   ${GREEN}sudo journalctl -u archivesmp-webapi -f${NC}"
echo ""
echo "5. Access web UI:"
echo "   ${GREEN}http://135.181.212.169:8000/${NC}"
echo ""
