#!/bin/bash
# Deploy Aqua GUI for ArchiveSMP Configuration Manager
# Run this on Hetzner server (checks for existing deployment)

set -e

echo "=========================================="
echo "ArchiveSMP Config Manager - Aqua GUI Deployment"
echo "=========================================="

REPO_DIR="/opt/archivesmp-config-manager"
STATIC_SOURCE="$REPO_DIR/src/web/static"
GUI_DIR="/var/www/archivesmp-config"
NGINX_SITE="/etc/nginx/sites-available/archivesmp-config"

# Check if already deployed
if [ -d "$GUI_DIR" ] && [ -f "$GUI_DIR/index.html" ]; then
    echo "⚠️  GUI already deployed at $GUI_DIR"
    echo "   Updating existing deployment..."
    UPDATING=1
else
    echo "🆕 New GUI deployment"
    UPDATING=0
fi

# Pull latest code from Git
echo "[1/5] Pulling latest code..."
cd "$REPO_DIR"
sudo -u amp git pull origin master || echo "⚠️  Git pull failed (continuing with existing code)"

# Create/update web directory
echo "[2/5] Setting up web directory..."
sudo mkdir -p "$GUI_DIR"

# Copy ALL static files (aqua GUI)
echo "[3/5] Copying aqua GUI files..."
sudo cp -r "$STATIC_SOURCE"/* "$GUI_DIR/"
sudo chown -R www-data:www-data "$GUI_DIR"
sudo chmod -R 755 "$GUI_DIR"

echo "   Deployed files:"
ls -lh "$GUI_DIR"/*.html | awk '{print "   - " $9}'

# Create/update nginx configuration
echo "[4/5] Configuring nginx..."
if [ -f "$NGINX_SITE" ]; then
    echo "   ℹ️  Nginx config exists, backing up..."
    sudo cp "$NGINX_SITE" "${NGINX_SITE}.bak.$(date +%Y%m%d_%H%M%S)"
fi

sudo tee "$NGINX_SITE" > /dev/null << 'EOF'
server {
    listen 8078;
    server_name config.archivesmp.site;
    
    root /var/www/archivesmp-config;
    index index.html;
    
    # Serve static GUI files
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Proxy API requests to FastAPI backend
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Enable CORS for API calls
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
    add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    
    access_log /var/log/nginx/archivesmp-config-access.log;
    error_log /var/log/nginx/archivesmp-config-error.log;
}
EOF

# Enable site and reload nginx
if [ ! -L "/etc/nginx/sites-enabled/archivesmp-config" ]; then
    echo "   Enabling nginx site..."
    sudo ln -s "$NGINX_SITE" /etc/nginx/sites-enabled/
fi

echo "   Testing nginx config..."
sudo nginx -t

echo "   Reloading nginx..."
sudo systemctl reload nginx

# Verify deployment
echo "[5/5] Verifying deployment..."

# Test GUI access
if curl -s http://localhost/ | grep -q "ArchiveSMP"; then
    echo "   ✓ GUI is accessible"
else
    echo "   ✗ GUI not responding (check nginx logs)"
fi

# Test API access
if curl -s http://localhost:8000/api/instances > /dev/null 2>&1; then
    echo "   ✓ API is accessible"
else
    echo "   ✗ API not responding (check service status)"
fi

echo ""
echo "=========================================="
if [ $UPDATING -eq 1 ]; then
    echo "✓ GUI UPDATED SUCCESSFULLY"
else
    echo "✓ GUI DEPLOYED SUCCESSFULLY"
fi
echo "=========================================="
echo ""
echo "🌊 Aqua GUI Features:"
echo "   - Main Dashboard (index.html)"
echo "   - Config Browser (config_browser.html)"
echo "   - Config Editor (config_editor.html)"
echo "   - Hierarchy Viewer (hierarchy_viewer.html)"
echo "   - Variance Report (variance_report.html)"
echo "   - Meta Tag Manager (meta_tag_manager.html)"
echo "   - World Config (world_config.html)"
echo "   - Rank Config (rank_config.html)"
echo "   - Player Overrides (player_overrides.html)"
echo "   - Deploy Manager (deploy.html)"
echo "   - History Viewer (history.html)"
echo "   - Migrations (migrations.html)"
echo ""
echo "📍 Access URLs:"
echo "   Main GUI:  http://135.181.212.169:8078/"
echo "   API Docs:  http://135.181.212.169:8000/docs"
echo ""
echo "📋 Nginx logs:"
echo "   sudo tail -f /var/log/nginx/archivesmp-config-access.log"
echo "   sudo tail -f /var/log/nginx/archivesmp-config-error.log"
echo ""
