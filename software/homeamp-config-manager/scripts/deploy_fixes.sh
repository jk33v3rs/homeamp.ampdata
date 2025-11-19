#!/bin/bash
# Deploy all fixes to production server

set -e  # Exit on error

echo "🚀 Deploying fixes to Hetzner production server..."

# Pull latest code
echo "📥 Pulling latest code..."
cd /opt/archivesmp-config-manager
sudo git pull origin master

# Ensure database tables exist
echo "🗄️  Creating/updating database tables..."
mariadb -u root -p'2024!SQLdb' asmp_config < scripts/add_plugin_tracking_tables.sql
mariadb -u root -p'2024!SQLdb' asmp_config < scripts/add_plugin_metadata_tables.sql

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart homeamp-agent.service
sudo systemctl restart archivesmp-webapi.service

# Show service status
echo ""
echo "✅ Services restarted. Status:"
sudo systemctl status homeamp-agent.service --no-pager -n 5
echo ""
sudo systemctl status archivesmp-webapi.service --no-pager -n 5

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📊 Monitor logs with:"
echo "  sudo journalctl -u homeamp-agent.service -f"
echo "  sudo journalctl -u archivesmp-webapi.service -f"
echo ""
echo "🌐 Check web UI at: http://135.181.212.169:8000/dashboard"
