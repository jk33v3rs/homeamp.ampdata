#!/bin/bash
# Deploy all fixes to production server

echo "🚀 Deploying fixes to Hetzner production server..."

# Pull latest code
echo "📥 Pulling latest code..."
cd /opt/archivesmp-config-manager
sudo git pull origin master

# Database tables already exist - skip creation

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
echo "🌐 Check web UI at: http://localhost:8000/dashboard"
