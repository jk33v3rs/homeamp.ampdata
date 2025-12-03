#!/bin/bash
# Quick fix for OVH service files
# Run this on OVH server to fix the broken services

set -e

echo "========================================"
echo "Fixing OVH Service Configuration"
echo "========================================"

# Stop the broken services
echo "Stopping services..."
sudo systemctl stop archivesmp-webapi.service || true
sudo systemctl stop homeamp-agent.service || true

# Create corrected service files
echo "Creating corrected service files..."

# Web API Service
sudo tee /etc/systemd/system/archivesmp-webapi.service > /dev/null <<'EOF'
[Unit]
Description=ArchiveSMP Config Manager Web API
Documentation=https://github.com/jk33v3rs/homeamp.ampdata
After=network-online.target homeamp-agent.service
Wants=network-online.target
Requires=homeamp-agent.service

[Service]
Type=simple
User=webadmin
Group=webadmin
WorkingDirectory=/opt/archivesmp-config-manager
Environment="PYTHONPATH=/opt/archivesmp-config-manager"
Environment="ARCHIVESMP_WEB_HOST=0.0.0.0"
Environment="ARCHIVESMP_WEB_PORT=8000"
EnvironmentFile=-/etc/archivesmp/secrets.env

# Start web API with uvicorn
ExecStart=/opt/archivesmp-config-manager/venv/bin/python -m uvicorn src.web.api:app --host ${ARCHIVESMP_WEB_HOST} --port ${ARCHIVESMP_WEB_PORT} --workers 4

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=archivesmp-webapi

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits
LimitNOFILE=65536
MemoryLimit=4G

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Agent Service
sudo tee /etc/systemd/system/homeamp-agent.service > /dev/null <<'EOF'
[Unit]
Description=ArchiveSMP Config Manager Agent
Documentation=https://github.com/jk33v3rs/homeamp.ampdata
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=webadmin
Group=webadmin
WorkingDirectory=/opt/archivesmp-config-manager
Environment="PYTHONPATH=/opt/archivesmp-config-manager"
Environment="ARCHIVESMP_AGENT_PORT=8001"
EnvironmentFile=-/etc/archivesmp/secrets.env

# Start agent service
ExecStart=/opt/archivesmp-config-manager/venv/bin/python -m src.agent.service

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=archivesmp-agent

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits
LimitNOFILE=65536
MemoryLimit=2G

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service files created"

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "Enabling services..."
sudo systemctl enable archivesmp-webapi.service
sudo systemctl enable homeamp-agent.service

# Start services
echo "Starting services..."
sudo systemctl start archivesmp-webapi.service
sudo systemctl start homeamp-agent.service

echo ""
echo "Waiting 5 seconds for services to start..."
sleep 5

echo ""
echo "========================================"
echo "Service Status"
echo "========================================"
echo ""
echo "Web API:"
sudo systemctl status archivesmp-webapi.service --no-pager -l | head -n 15
echo ""
echo "Agent:"
sudo systemctl status homeamp-agent.service --no-pager -l | head -n 15

echo ""
echo "========================================"
echo "Fix Complete!"
echo "========================================"
echo ""
echo "Check logs if services failed:"
echo "  sudo journalctl -u archivesmp-webapi.service -n 50"
echo "  sudo journalctl -u homeamp-agent.service -n 50"
echo ""
