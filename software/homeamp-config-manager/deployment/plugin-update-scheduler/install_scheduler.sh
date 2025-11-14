#!/bin/bash
# ArchiveSMP Plugin Update Scheduler Installation Script

set -e

echo "Installing ArchiveSMP Plugin Update Scheduler..."

# Create required directories
mkdir -p /var/lib/archivesmp/plugin-staging
mkdir -p /var/lib/archivesmp/plugin-staging/metadata
mkdir -p /var/lib/archivesmp/reports
mkdir -p /etc/archivesmp
mkdir -p /var/log/archivesmp

# Set permissions
chown -R webadmin:amp /var/lib/archivesmp/plugin-staging
chown -R webadmin:amp /var/lib/archivesmp/reports
chmod 755 /var/lib/archivesmp/plugin-staging
chmod 755 /var/lib/archivesmp/reports

# Install Python dependencies
pip3 install aiohttp pyyaml openpyxl

# Install systemd service and timer
cat > /etc/systemd/system/archivesmp-plugin-update.service << 'EOF'
[Unit]
Description=ArchiveSMP Plugin Update Checker
After=network.target

[Service]
Type=oneshot
User=webadmin
Group=amp
WorkingDirectory=\opt\archivesmp-config-manager
ExecStart=/usr/bin/python3 -m src.automation.pulumi_update_monitor
StandardOutput=journal
StandardError=journal
SyslogIdentifier=archivesmp-plugin-update
Environment="PYTHONPATH=\opt\archivesmp-config-manager"
Environment="PLUGIN_REGISTRY=/etc/archivesmp/plugin_registry.yaml"
Environment="STAGING_PATH=/var/lib/archivesmp/plugin-staging"
Environment="EXCEL_PATH=/var/lib/archivesmp/reports/plugin_updates.xlsx"

[Install]
WantedBy=multi-user.target

EOF

cat > /etc/systemd/system/archivesmp-plugin-update.timer << 'EOF'
[Unit]
Description=Hourly ArchiveSMP Plugin Update Check
Requires=archivesmp-plugin-update.service

[Timer]
OnCalendar=hourly
Persistent=true
Unit=archivesmp-plugin-update.service

[Install]
WantedBy=timers.target

EOF

# Reload systemd
systemctl daemon-reload

# Enable and start timer
systemctl enable archivesmp-plugin-update.timer
systemctl start archivesmp-plugin-update.timer

# Check status
systemctl status archivesmp-plugin-update.timer

echo "✓ Plugin update scheduler installed successfully"
echo "  Timer: systemctl status archivesmp-plugin-update.timer"
echo "  Logs:  journalctl -u archivesmp-plugin-update.service -f"
echo "  Run manually: systemctl start archivesmp-plugin-update.service"
