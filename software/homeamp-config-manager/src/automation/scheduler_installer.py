"""
Systemd Timer + Cron-Based Plugin Update Scheduler

For bare metal Debian servers (without AWS Lambda).
Sets up hourly plugin update checks using systemd timers or cron.
"""

from pathlib import Path
from typing import Dict, Any
import logging


class UpdateSchedulerInstaller:
    """
    Installs systemd timer and service for hourly plugin update checks
    on bare metal Debian servers
    """
    
    def __init__(self, install_path: Path = Path("/opt/archivesmp-config-manager")):
        """
        Initialize installer
        
        Args:
            install_path: Base installation directory
        """
        self.install_path = install_path
        self.logger = logging.getLogger(__name__)
    
    def generate_systemd_service(self) -> str:
        """Generate systemd service file content"""
        return f"""[Unit]
Description=ArchiveSMP Plugin Update Checker
After=network.target

[Service]
Type=oneshot
User=webadmin
Group=amp
WorkingDirectory={self.install_path}
ExecStart=/usr/bin/python3 -m src.automation.pulumi_update_monitor
StandardOutput=journal
StandardError=journal
SyslogIdentifier=archivesmp-plugin-update
Environment="PYTHONPATH={self.install_path}"
Environment="PLUGIN_REGISTRY=/etc/archivesmp/plugin_registry.yaml"
Environment="STAGING_PATH=/var/lib/archivesmp/plugin-staging"
Environment="EXCEL_PATH=/var/lib/archivesmp/reports/plugin_updates.xlsx"

[Install]
WantedBy=multi-user.target
"""
    
    def generate_systemd_timer(self) -> str:
        """Generate systemd timer file content"""
        return """[Unit]
Description=Hourly ArchiveSMP Plugin Update Check
Requires=archivesmp-plugin-update.service

[Timer]
OnCalendar=hourly
Persistent=true
Unit=archivesmp-plugin-update.service

[Install]
WantedBy=timers.target
"""
    
    def generate_crontab_entry(self) -> str:
        """Generate crontab entry as alternative to systemd timer"""
        return f"""# ArchiveSMP Plugin Update Checker - Runs hourly
0 * * * * cd {self.install_path} && /usr/bin/python3 -m src.automation.pulumi_update_monitor >> /var/log/archivesmp/plugin-update.log 2>&1
"""
    
    def generate_install_script(self) -> str:
        """Generate installation script"""
        return f"""#!/bin/bash
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
{self.generate_systemd_service()}
EOF

cat > /etc/systemd/system/archivesmp-plugin-update.timer << 'EOF'
{self.generate_systemd_timer()}
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
"""
    
    def generate_plugin_registry_template(self) -> str:
        """Generate plugin registry YAML template"""
        return """# ArchiveSMP Plugin Registry
# Defines plugin update sources and current versions

# GitHub releases
LuckPerms:
  repository_type: github
  github_repo: LuckPerms/LuckPerms
  current_version: 5.4.102
  requires_restart: true
  compatibility_notes: "Compatible with Paper 1.21+"

Pl3xMap:
  repository_type: github
  github_repo: pl3xgaming/Pl3xMap
  current_version: 1.2.0
  requires_restart: true
  compatibility_notes: "Requires Paper 1.20.6+"

Geyser-Spigot:
  repository_type: github
  github_repo: GeyserMC/Geyser
  current_version: 2.2.0
  requires_restart: true
  compatibility_notes: "Bedrock crossplay support"

HuskSync:
  repository_type: github
  github_repo: WiIIiam278/HuskSync
  current_version: 3.6.0
  requires_restart: true
  compatibility_notes: "Cross-server inventory sync"

# SpigotMC resources (using Spiget API)
CoreProtect:
  repository_type: spigot
  spigot_id: "8631"
  current_version: 22.2
  requires_restart: false
  compatibility_notes: "Block logging and rollback"

PlaceholderAPI:
  repository_type: spigot
  spigot_id: "6245"
  current_version: 2.11.5
  requires_restart: false
  compatibility_notes: "Required by many plugins"

Citizens:
  repository_type: spigot
  spigot_id: "13811"
  current_version: 2.0.33
  requires_restart: true
  compatibility_notes: "NPC framework"

ProtocolLib:
  repository_type: spigot
  spigot_id: "1997"
  current_version: 5.1.0
  requires_restart: true
  compatibility_notes: "Packet manipulation library"

Vault:
  repository_type: spigot
  spigot_id: "34315"
  current_version: 1.7.3
  requires_restart: true
  compatibility_notes: "Economy/permissions API"

# Jenkins CI builds
WorldEdit:
  repository_type: jenkins
  jenkins_url: https://ci.enginehub.org/job/worldedit/job/master
  current_version: build-6497
  requires_restart: false
  compatibility_notes: "World editing tool"

WorldGuard:
  repository_type: jenkins
  jenkins_url: https://ci.enginehub.org/job/worldguard/job/master
  current_version: build-2154
  requires_restart: true
  compatibility_notes: "Region protection"

# CurseForge/Bukkit (requires API key - implement when available)
# EssentialsX:
#   repository_type: bukkit
#   bukkit_id: essentialsx
#   current_version: 2.20.1
#   requires_restart: true
#   compatibility_notes: "Server essentials suite"
"""
    
    def generate_uninstall_script(self) -> str:
        """Generate uninstallation script"""
        return """#!/bin/bash
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
"""
    
    def write_install_files(self, output_dir: Path):
        """
        Write all installation files to directory
        
        Args:
            output_dir: Directory to write installation files
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write systemd service
        service_file = output_dir / "archivesmp-plugin-update.service"
        with open(service_file, 'w') as f:
            f.write(self.generate_systemd_service())
        self.logger.info(f"Written: {service_file}")
        
        # Write systemd timer
        timer_file = output_dir / "archivesmp-plugin-update.timer"
        with open(timer_file, 'w') as f:
            f.write(self.generate_systemd_timer())
        self.logger.info(f"Written: {timer_file}")
        
        # Write crontab entry
        crontab_file = output_dir / "crontab.txt"
        with open(crontab_file, 'w') as f:
            f.write(self.generate_crontab_entry())
        self.logger.info(f"Written: {crontab_file}")
        
        # Write install script
        install_script = output_dir / "install_scheduler.sh"
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write(self.generate_install_script())
        install_script.chmod(0o755)
        self.logger.info(f"Written: {install_script}")
        
        # Write uninstall script
        uninstall_script = output_dir / "uninstall_scheduler.sh"
        with open(uninstall_script, 'w', encoding='utf-8') as f:
            f.write(self.generate_uninstall_script())
        uninstall_script.chmod(0o755)
        self.logger.info(f"Written: {uninstall_script}")
        
        # Write plugin registry template
        registry_file = output_dir / "plugin_registry.yaml"
        with open(registry_file, 'w') as f:
            f.write(self.generate_plugin_registry_template())
        self.logger.info(f"Written: {registry_file}")
        
        self.logger.info(f"All installation files written to: {output_dir}")


def main():
    """Generate installation files"""
    logging.basicConfig(level=logging.INFO)
    
    installer = UpdateSchedulerInstaller()
    output_dir = Path(__file__).parent.parent.parent / "deployment" / "plugin-update-scheduler"
    
    installer.write_install_files(output_dir)
    
    print(f"\n=== Installation files generated ===")
    print(f"Location: {output_dir}")
    print(f"\nTo install on production server:")
    print(f"1. Copy {output_dir} to server")
    print(f"2. Run: sudo bash install_scheduler.sh")
    print(f"3. Check: systemctl status archivesmp-plugin-update.timer")
    print(f"4. View logs: journalctl -u archivesmp-plugin-update.service -f")


if __name__ == "__main__":
    main()
