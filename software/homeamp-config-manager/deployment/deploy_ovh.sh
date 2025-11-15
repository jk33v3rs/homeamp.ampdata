#!/bin/bash
# Deploy ArchiveSMP Config Manager to OVH Server
# Run this script on OVH (37.187.143.41) as amp user

set -e

SERVER_NAME="ovh-ryzen"
INSTALL_DIR="/opt/archivesmp-config-manager"
REPO_URL="https://github.com/jk33v3rs/homeamp.ampdata.git"

echo "================================================================================"
echo "Deploying ArchiveSMP Config Manager to ${SERVER_NAME}"
echo "================================================================================"

# Check if running as amp user
if [ "$(whoami)" != "amp" ]; then
    echo "ERROR: This script must be run as 'amp' user"
    exit 1
fi

# Create install directory if needed
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating install directory..."
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown amp:amp "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Clone or update repository
if [ -d ".git" ]; then
    echo "Updating repository..."
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" .
fi

cd software/homeamp-config-manager

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Install dependencies
echo "Installing dependencies..."
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# Install mysql-connector-python for database access
.venv/bin/pip install mysql-connector-python pyyaml

# Create systemd service file for endpoint agent
echo "Creating systemd service for endpoint agent..."
cat > /tmp/archivesmp-endpoint-agent.service << EOF
[Unit]
Description=ArchiveSMP Configuration Management Endpoint Agent
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=amp
Group=amp
WorkingDirectory=$INSTALL_DIR/software/homeamp-config-manager
Environment="PYTHONPATH=$INSTALL_DIR/software/homeamp-config-manager"
ExecStart=$INSTALL_DIR/software/homeamp-config-manager/.venv/bin/python -m src.agent.endpoint_agent \\
    --server=${SERVER_NAME} \\
    --db-host=135.181.212.169 \\
    --db-port=3369 \\
    --db-user=sqlworkerSMP \\
    --db-password=SQLdb2024!

Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/archivesmp-endpoint-agent.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "================================================================================"
echo "✓ Deployment complete!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start endpoint agent:"
echo "   sudo systemctl enable archivesmp-endpoint-agent.service"
echo "   sudo systemctl start archivesmp-endpoint-agent.service"
echo ""
echo "2. Check status:"
echo "   sudo systemctl status archivesmp-endpoint-agent.service"
echo ""
echo "3. View logs:"
echo "   sudo journalctl -u archivesmp-endpoint-agent.service -f"
echo ""
echo "NOTE: Web API is NOT deployed on OVH - it runs on Hetzner only"
echo ""
