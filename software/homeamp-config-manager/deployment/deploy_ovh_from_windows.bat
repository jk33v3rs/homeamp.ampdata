@echo off
REM Deploy ArchiveSMP Config Manager to OVH from Windows PC
REM Run this from your Windows PC (already has SSH access to servers)

echo ================================================================================
echo Deploying to OVH (37.187.143.41)
echo ================================================================================

ssh amp@37.187.143.41 "bash -s" << 'ENDSSH'
set -e

echo "Step 1: Create/update installation directory..."
sudo mkdir -p /opt/archivesmp-config-manager
sudo chown amp:amp /opt/archivesmp-config-manager
cd /opt/archivesmp-config-manager

echo "Step 2: Clone/update repository..."
if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/jk33v3rs/homeamp.ampdata.git .
fi

echo "Step 3: Setup Python environment..."
cd software/homeamp-config-manager
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install mysql-connector-python pyyaml

echo "Step 4: Create endpoint agent service..."
sudo tee /etc/systemd/system/archivesmp-endpoint-agent.service > /dev/null << EOF
[Unit]
Description=ArchiveSMP Configuration Management Endpoint Agent
After=network.target

[Service]
Type=simple
User=amp
Group=amp
WorkingDirectory=/opt/archivesmp-config-manager/software/homeamp-config-manager
Environment="PYTHONPATH=/opt/archivesmp-config-manager/software/homeamp-config-manager"
ExecStart=/opt/archivesmp-config-manager/software/homeamp-config-manager/.venv/bin/python -m src.agent.endpoint_agent --server=ovh-ryzen --db-host=135.181.212.169 --db-port=3369 --db-user=sqlworkerSMP --db-password=SQLdb2024!
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "Step 5: Enable and start service..."
sudo systemctl daemon-reload
sudo systemctl enable archivesmp-endpoint-agent.service
sudo systemctl restart archivesmp-endpoint-agent.service

echo ""
echo "==================================================================="
echo "Deployment Complete!"
echo "==================================================================="
echo ""
echo "Checking service status..."
sudo systemctl status archivesmp-endpoint-agent.service --no-pager -l
echo ""
echo "Recent agent logs:"
sudo journalctl -u archivesmp-endpoint-agent.service --since "1 min ago" --no-pager
echo ""
ENDSSH

echo.
echo ================================================================================
echo Done! Check output above for any errors.
echo ================================================================================
pause
