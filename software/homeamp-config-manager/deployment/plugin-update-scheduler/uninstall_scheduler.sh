#!/bin/bash
# ArchiveSMP Plugin Update Scheduler Uninstallation Script

set -e

echo "Uninstalling ArchiveSMP Plugin Update Scheduler..."

# Stop and disable timer
systemctl stop archivesmp-plugin-update.timer || true
systemctl disable archivesmp-plugin-update.timer || true

# Remove systemd files
rm -f /etc/systemd/system/archivesmp-plugin-update.service
rm -f /etc/systemd/system/archivesmp-plugin-update.timer

# Reload systemd
systemctl daemon-reload

echo "✓ Plugin update scheduler uninstalled"
echo "  Note: Staged plugins preserved in /var/lib/archivesmp/plugin-staging"
echo "  Note: Reports preserved in /var/lib/archivesmp/reports"
