# Pl3xMap + LiveAtlas Deployment Guide

## Overview

**Public Maps**: maps.archivesmp.com (12 instances)
- BENT01, CLIP01, CREA01, DEV01, EMAD01, EVO01, HARD01, MINE01, MIN01, SMP101, SMP201, TOW01

**Private Maps**: admaps.archivesmp.com (4 instances)
- ROY01 (Battle Royale - hide player positions)
- CSMC01 (Counter-Strike MC - anti screen camping)
- PRI01 (Minigames - admin monitoring)
- BIG01 (BiggerGames - admin monitoring)

## Architecture

```
[Hetzner/OVH Bare Metal]
  Pl3xMap generates tiles
         ↓
  Agent watches tile directories
         ↓
  Uploads to MinIO: pl3xmap-tiles/public/* and pl3xmap-tiles/private/*
         ↓
[YunoHost Server]
  Sync service downloads from MinIO
         ↓
  /var/www/maps.archivesmp.com/data/* (public)
  /var/www/admaps.archivesmp.com/data/* (private with SSO auth)
         ↓
  LiveAtlas renders maps
```

## Deployment Steps

### 1. Install Dependencies on Bare Metal Servers

**On Hetzner (135.181.212.169) and OVH (37.187.143.41):**

```bash
# SSH to server
ssh root@archivesmp.site  # or archivesmp.online for OVH

# Install Python package for file watching
cd /opt/archivesmp-config-manager
source .venv/bin/activate
pip install watchdog

# Copy systemd service file
sudo cp deployment/pl3xmap-tile-sync.service /etc/systemd/system/

# Configure MinIO credentials
sudo nano /etc/systemd/system/pl3xmap-tile-sync.service
# Edit MINIO_ACCESS_KEY and MINIO_SECRET_KEY

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable pl3xmap-tile-sync
sudo systemctl start pl3xmap-tile-sync

# Check status
sudo systemctl status pl3xmap-tile-sync
sudo journalctl -u pl3xmap-tile-sync -f
```

### 2. Configure Pl3xMap on Instances

**Deploy public map configs:**

```bash
# Via web UI or API
curl -X POST http://localhost:8000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "instance_names": ["BENT01", "CLIP01", "CREA01", "DEV01", "EMAD01", "EVO01", "HARD01", "MINE01", "MIN01", "SMP101", "SMP201", "TOW01"],
    "plugin_name": "Pl3xMap",
    "config_variant": "public"
  }'
```

**Deploy private map configs:**

```bash
curl -X POST http://localhost:8000/api/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "instance_names": ["ROY01", "CSMC01", "PRI01", "BIG01"],
    "plugin_name": "Pl3xMap",
    "config_variant": "private"
  }'
```

**Restart instances to load configs:**

```bash
curl -X POST http://localhost:8000/api/restart \
  -H "Content-Type: application/json" \
  -d '{
    "instance_names": ["BENT01", "CLIP01", "CREA01", "DEV01", "EMAD01", "EVO01", "HARD01", "MINE01", "MIN01", "SMP101", "SMP201", "TOW01", "ROY01", "CSMC01", "PRI01", "BIG01"],
    "restart_type": "instances"
  }'
```

### 3. Set Up YunoHost Map Sync

**On YunoHost server:**

```bash
# Create directories
sudo mkdir -p /var/www/maps.archivesmp.com/data
sudo mkdir -p /var/www/admaps.archivesmp.com/data
sudo chown -R www-data:www-data /var/www/maps.archivesmp.com
sudo chown -R www-data:www-data /var/www/admaps.archivesmp.com

# Install code (adjust path as needed)
sudo mkdir -p /home/yunohost.app/archivesmp
# Copy src/yunohost/map_sync.py to the server

# Set up Python environment
cd /home/yunohost.app/archivesmp
sudo python3 -m venv .venv
sudo .venv/bin/pip install minio

# Copy systemd service
sudo cp deployment/yunohost-map-sync.service /etc/systemd/system/

# Configure MinIO credentials
sudo nano /etc/systemd/system/yunohost-map-sync.service
# Edit MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable yunohost-map-sync
sudo systemctl start yunohost-map-sync

# Check status
sudo systemctl status yunohost-map-sync
sudo journalctl -u yunohost-map-sync -f
```

### 4. Install LiveAtlas on YunoHost

**Public maps:**

```bash
# Install LiveAtlas
cd /var/www/maps.archivesmp.com
sudo git clone https://github.com/JLyne/LiveAtlas.git .

# Wait for sync service to generate config.json
# Or manually create it based on template

sudo chown -R www-data:www-data /var/www/maps.archivesmp.com
```

**Private maps:**

```bash
# Install LiveAtlas
cd /var/www/admaps.archivesmp.com
sudo git clone https://github.com/JLyne/LiveAtlas.git .

# Wait for sync service to generate config.json

sudo chown -R www-data:www-data /var/www/admaps.archivesmp.com
```

### 5. Configure Nginx in YunoHost

**You mentioned you'll handle this in YunoHost.**

Key requirements:
- **maps.archivesmp.com**: Open access, no auth required
- **admaps.archivesmp.com**: Protected by YunoHost SSO

The sync service will place tiles at:
- `/var/www/maps.archivesmp.com/data/{instance}/`
- `/var/www/admaps.archivesmp.com/data/{instance}/`

## Monitoring and Maintenance

### Check Sync Status (Bare Metal)

```bash
# Check tile sync service
sudo systemctl status pl3xmap-tile-sync

# View logs
sudo journalctl -u pl3xmap-tile-sync -f

# Check which instances are being watched
sudo journalctl -u pl3xmap-tile-sync | grep "Started watching"

# Check MinIO bucket contents
# (requires MinIO client installed)
mc ls archivesmp/pl3xmap-tiles/public/
mc ls archivesmp/pl3xmap-tiles/private/
```

### Check Sync Status (YunoHost)

```bash
# Check map sync service
sudo systemctl status yunohost-map-sync

# View logs
sudo journalctl -u yunohost-map-sync -f

# Check synced files
ls -lh /var/www/maps.archivesmp.com/data/
ls -lh /var/www/admaps.archivesmp.com/data/

# Check generated configs
cat /var/www/maps.archivesmp.com/config.json
cat /var/www/admaps.archivesmp.com/config.json
```

### Force Full Resync

**If tiles get out of sync:**

```bash
# On bare metal servers
sudo systemctl restart pl3xmap-tile-sync

# On YunoHost
sudo systemctl restart yunohost-map-sync
```

### Manual Sync Test

```bash
# On bare metal server
cd /opt/archivesmp-config-manager
source .venv/bin/activate
python -c "
from src.agent.tile_watcher import TileWatcher
from minio import Minio
import os

minio = Minio('localhost:9000', 
              access_key=os.getenv('MINIO_ACCESS_KEY'),
              secret_key=os.getenv('MINIO_SECRET_KEY'),
              secure=False)

watcher = TileWatcher(minio)
watcher.sync_full_directory('BENT01')
print('✓ Manual sync complete')
"
```

## Troubleshooting

### Tiles Not Appearing on LiveAtlas

1. **Check if Pl3xMap is generating tiles:**
   ```bash
   ls -lh /home/amp/.ampdata/instances/BENT01/plugins/Pl3xMap/web/tiles/
   ```

2. **Check if agent is watching the instance:**
   ```bash
   sudo journalctl -u pl3xmap-tile-sync | grep BENT01
   ```

3. **Check if tiles are in MinIO:**
   ```bash
   mc ls archivesmp/pl3xmap-tiles/public/bent01/
   ```

4. **Check if YunoHost sync is pulling tiles:**
   ```bash
   ls -lh /var/www/maps.archivesmp.com/data/bent01/tiles/
   ```

5. **Check nginx is serving tiles:**
   ```bash
   curl -I https://maps.archivesmp.com/data/bent01/tiles/world/0/0/0.png
   ```

### Service Won't Start

**Bare metal tile sync:**
```bash
# Check logs for errors
sudo journalctl -u pl3xmap-tile-sync -n 50

# Common issues:
# - MinIO credentials wrong
# - watchdog package not installed
# - Pl3xMap directories don't exist
```

**YunoHost map sync:**
```bash
# Check logs
sudo journalctl -u yunohost-map-sync -n 50

# Common issues:
# - Can't reach MinIO (firewall/network)
# - Directory permissions (needs www-data access)
# - minio Python package not installed
```

### Private Maps Accessible Without Auth

Check nginx configuration - SSO auth must be enforced:
```nginx
location / {
    auth_request /auth;
    error_page 401 = @error401;
    # ...
}
```

### Pl3xMap Plugin Config

**Public instances** (config.yml):
```yaml
settings:
  player-tracker:
    enabled: true  # Show player positions
    update-interval: 5
```

**Private instances** (config.yml):
```yaml
settings:
  player-tracker:
    enabled: false  # DON'T show player positions!
    # Or only show to staff:
    # enabled: true
    # hide-spectators: false
```

## Performance Tuning

### Sync Frequency

**Bare metal (tile watcher):**
- Batches changes every 10 seconds (configurable in code)
- Instant upload on file change

**YunoHost (tile downloader):**
- Default: Every 5 minutes (300 seconds)
- Adjust via `SYNC_INTERVAL` environment variable in systemd service

### Resource Usage

**Tile sync service** (bare metal):
- CPU: Low (~1-2% during sync)
- Memory: ~50-100 MB per instance
- Network: Depends on map render frequency

**Map sync service** (YunoHost):
- CPU: Low (~1-2% during sync)
- Memory: ~50 MB
- Disk I/O: Moderate during sync
- Network: Downloads tiles from MinIO

## Security Considerations

1. **MinIO Access**:
   - Use dedicated credentials for tile sync
   - Restrict bucket access to read/write for tile sync services only

2. **Private Maps**:
   - Ensure YunoHost SSO is enforced on admaps.archivesmp.com
   - Don't expose private tiles via public domain

3. **Player Tracking**:
   - Disabled on private instances (ROY01, CSMC01, PRI01, BIG01)
   - Prevents tactical advantage from map viewing

## Success Checklist

- [ ] Tile sync service running on Hetzner
- [ ] Tile sync service running on OVH
- [ ] Map sync service running on YunoHost
- [ ] Public maps accessible at maps.archivesmp.com
- [ ] Private maps accessible at admaps.archivesmp.com (with auth)
- [ ] Private maps require YunoHost login
- [ ] All 16 instances showing on appropriate domains
- [ ] Player positions visible on public maps
- [ ] Player positions hidden on private maps (ROY01, CSMC01, PRI01, BIG01)
- [ ] Tiles updating within 5 minutes of map changes

## Next Steps

1. Deploy Pl3xMap configs (public vs private variants)
2. Start tile sync services on bare metal servers
3. Configure YunoHost domains (you'll handle this)
4. Start map sync service on YunoHost
5. Verify maps render correctly
6. Test auth protection on private maps
