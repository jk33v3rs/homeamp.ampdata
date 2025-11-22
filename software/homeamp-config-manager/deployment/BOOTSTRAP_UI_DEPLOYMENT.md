# Bootstrap UI Deployment Script

## Step 1: Copy systemd service file
Copy the Bootstrap UI service file to production:

```bash
# On production Hetzner server as webadmin
sudo cp /opt/archivesmp-config-manager/deployment/archivesmp-bootstrap-ui.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## Step 2: Enable and start the service
```bash
sudo systemctl enable archivesmp-bootstrap-ui
sudo systemctl start archivesmp-bootstrap-ui
```

## Step 3: Check status
```bash
sudo systemctl status archivesmp-bootstrap-ui
sudo journalctl -u archivesmp-bootstrap-ui -f
```

## Step 4: Open firewall port (if needed)
```bash
# If using ufw firewall
sudo ufw allow 8001/tcp

# If using iptables
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
```

## Step 5: Access the Bootstrap UI
Open browser to: http://135.181.212.169:8001

## Features of Bootstrap UI
- Modern Bootstrap 4 design
- Responsive layout
- Toast notifications
- Modal dialogs for editing
- Tabbed interfaces
- Real-time updates
- Card-based stats
- Icon-rich navigation

## Pages Available
- `/` - Dashboard with stats and instance overview
- `/plugins` - Plugin configurator with filtering and bulk updates
- `/tags` - Tag manager with instance tags, tag management, and categories
- `/updates` - Update manager (template needed)
- `/variance` - Variance report (template needed)
- `/instance/{name}` - Instance detail view (template needed)

## API Compatibility
Uses the same API endpoints as the original UI (port 8000), so both can run simultaneously.

## Differences from Original UI
1. **Framework**: Bootstrap 4 vs vanilla CSS
2. **Navigation**: Traditional multi-page vs single-page app
3. **Components**: Bootstrap modals, cards, badges vs custom CSS
4. **Icons**: Font Awesome vs custom icons
5. **Responsiveness**: Mobile-first Bootstrap grid
6. **Port**: 8001 vs 8000
