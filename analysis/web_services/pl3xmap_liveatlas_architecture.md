# Pl3xMap Dual-Instance + LiveAtlas Aggregation Plan

## Overview

**Goal**: Support two Pl3xMap configurations with LiveAtlas aggregating both:
1. **Public Maps** - Direct access (outside firewall)
2. **Private Maps** - Behind YunoHost auth wall (anti-screen camping, etc.)

**Current State**:
- Pl3xMap installed on 16 instances
- NOT_DEPLOYED: Pl3xMap listed in excluded plugins
- Need to determine which instances = public vs private

## Architecture

### Map Generation (Bare Metal Servers)

**Hetzner** (archivesmp.site - 135.181.212.169):
```
Paper Instances → Pl3xMap Plugin → Generates tiles
  ├── BENT01 → /home/amp/.ampdata/instances/BENT01/plugins/Pl3xMap/web/tiles/
  ├── CLIP01 → /home/amp/.ampdata/instances/CLIP01/plugins/Pl3xMap/web/tiles/
  ├── CREA01 → ...
  ├── DEV01
  ├── EMAD01
  ├── HARD01
  ├── MINE01
  ├── MIN01
  ├── ROY01
  └── SMP201
```

**OVH** (archivesmp.online - 37.187.143.41):
```
Paper Instances → Pl3xMap Plugin → Generates tiles
  ├── BIG01 → /home/amp/.ampdata/instances/BIG01/plugins/Pl3xMap/web/tiles/
  ├── EVO01
  ├── PRI01
  ├── SMP101
  ├── CSMC01
  └── ...
```

### Map Hosting (YunoHost Server)

**YunoHost** (your YunoHost domain):
```
LiveAtlas (Node.js/nginx)
  ├── Public Maps (open access)
  │   ├── maps.archivesmp.site/bent01/
  │   ├── maps.archivesmp.site/clip01/
  │   ├── maps.archivesmp.site/smp201/
  │   └── ... (standard survival worlds)
  │
  └── Private Maps (YunoHost SSO auth required)
      ├── private-maps.archivesmp.site/csmc01/  (anti-screen camping)
      ├── private-maps.archivesmp.site/royale/  (battle royale secrecy)
      └── ... (tactical/competitive worlds)
```

## Instance Classification

### Public Maps (Open Access)
**Standard survival/creative worlds where map viewing doesn't affect gameplay:**

- BENT01 - Standard survival
- BIG01 - Large world
- CLIP01 - Clip world
- CREA01 - Creative world
- DEV01 - Development world
- EMAD01 - EMad's world
- EVO01 - Evolution world
- HARD01 - Hard mode world
- MINE01 - Mining world
- MIN01 - Mini world
- PRI01 - Prison world
- SMP101 - SMP world
- SMP201 - SMP world

### Private Maps (Behind Auth)
**Worlds where map access gives tactical advantage:**

- **CSMC01** - Counter-Strike MC (anti-screen camping)
  - Players shouldn't see opponent positions via map
  
- **ROY01** - Battle Royale
  - Spectators shouldn't reveal player positions
  
- **TOW01** - Towny (if competitive PvP)
  - Protect base locations from reconnaissance

**You tell me which others need auth protection!**

## Sync Solutions

### Option 1: Agent-Backed Sync (Recommended)

**Why best?**
- ✅ Already have agent infrastructure
- ✅ Reliable (no Samba startup issues)
- ✅ Platform-aware (knows which instance = which server)
- ✅ Can implement selective sync (public vs private)
- ✅ Audit trail of sync operations

**How it works:**

```
[Bare Metal Agent] → [MinIO/S3] → [YunoHost Sync Service] → [LiveAtlas]
       ↓
   Watches Pl3xMap tile changes
   Uploads to MinIO bucket
                              ↓
                         Downloads from MinIO
                         Organizes by public/private
                                    ↓
                               LiveAtlas renders
```

**Implementation:**

1. **Agent tile watcher** (on Hetzner/OVH):
```python
# src/agent/tile_watcher.py
class TileWatcher:
    """Watch Pl3xMap tile directories for changes"""
    
    def __init__(self, minio_client):
        self.minio = minio_client
        self.watch_dirs = {
            'BENT01': '/home/amp/.ampdata/instances/BENT01/plugins/Pl3xMap/web/',
            'CSMC01': '/home/amp/.ampdata/instances/CSMC01/plugins/Pl3xMap/web/',
            # ... all instances
        }
        self.access_levels = {
            'public': ['BENT01', 'BIG01', 'CLIP01', ...],
            'private': ['CSMC01', 'ROY01', 'TOW01']
        }
    
    def sync_tiles(self, instance_name: str):
        """Sync tiles for instance to MinIO"""
        web_dir = self.watch_dirs[instance_name]
        access_level = 'private' if instance_name in self.access_levels['private'] else 'public'
        
        # Upload to MinIO: pl3xmap-tiles/{access_level}/{instance_name}/
        bucket = 'pl3xmap-tiles'
        prefix = f'{access_level}/{instance_name.lower()}/'
        
        for file in Path(web_dir).rglob('*'):
            if file.is_file():
                relative_path = file.relative_to(web_dir)
                object_name = f'{prefix}{relative_path}'
                self.minio.fput_object(bucket, object_name, str(file))
        
        print(f"✓ Synced {instance_name} tiles to {access_level}")
```

2. **YunoHost sync service**:
```bash
# /etc/systemd/system/archivesmp-map-sync.service
[Unit]
Description=Archive SMP Map Tile Sync
After=network.target

[Service]
Type=simple
User=yunohost.app
WorkingDirectory=/home/yunohost.app/archivesmp
ExecStart=/home/yunohost.app/archivesmp/.venv/bin/python -m src.yunohost.map_sync
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

```python
# src/yunohost/map_sync.py
import time
from pathlib import Path
from minio import Minio

class MapSyncService:
    """Sync map tiles from MinIO to local filesystem for LiveAtlas"""
    
    def __init__(self):
        self.minio = Minio(
            'minio.archivesmp.internal:9000',
            access_key=os.getenv('MINIO_ACCESS_KEY'),
            secret_key=os.getenv('MINIO_SECRET_KEY'),
            secure=False
        )
        self.public_dir = Path('/var/www/maps.archivesmp.site/data')
        self.private_dir = Path('/var/www/private-maps.archivesmp.site/data')
        self.bucket = 'pl3xmap-tiles'
    
    def sync_loop(self):
        """Continuously sync tiles from MinIO"""
        while True:
            try:
                # Sync public maps
                for obj in self.minio.list_objects(self.bucket, prefix='public/', recursive=True):
                    local_path = self.public_dir / obj.object_name.replace('public/', '')
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    self.minio.fget_object(self.bucket, obj.object_name, str(local_path))
                
                # Sync private maps
                for obj in self.minio.list_objects(self.bucket, prefix='private/', recursive=True):
                    local_path = self.private_dir / obj.object_name.replace('private/', '')
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    self.minio.fget_object(self.bucket, obj.object_name, str(local_path))
                
                print(f"✓ Map sync completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                time.sleep(300)  # Sync every 5 minutes
                
            except Exception as e:
                print(f"✗ Sync error: {e}")
                time.sleep(60)  # Retry after 1 minute on error
```

### Option 2: NFS/Samba Share (Alternative)

**If you prefer direct filesystem access:**

1. **Export map directories via NFS** (on Hetzner/OVH):
```bash
# /etc/exports
/home/amp/.ampdata/instances/*/plugins/Pl3xMap/web yunohost-server(ro,sync,no_subtree_check)
```

2. **Mount on YunoHost**:
```bash
# /etc/fstab
hetzner-server:/home/amp/.ampdata/instances/*/plugins/Pl3xMap/web /mnt/hetzner-maps nfs ro,soft,timeo=10 0 0
ovh-server:/home/amp/.ampdata/instances/*/plugins/Pl3xMap/web /mnt/ovh-maps nfs ro,soft,timeo=10 0 0
```

3. **Symlink to web directories**:
```bash
# Public maps
ln -s /mnt/hetzner-maps/BENT01/plugins/Pl3xMap/web /var/www/maps.archivesmp.site/data/bent01
ln -s /mnt/hetzner-maps/CLIP01/plugins/Pl3xMap/web /var/www/maps.archivesmp.site/data/clip01

# Private maps
ln -s /mnt/hetzner-maps/CSMC01/plugins/Pl3xMap/web /var/www/private-maps.archivesmp.site/data/csmc01
```

**Samba startup issue fix:**
```bash
# /etc/systemd/system/mount-maps.service
[Unit]
Description=Mount Map Tile Shares
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/mount -a -t nfs
ExecStart=/bin/mount -a -t cifs

[Install]
WantedBy=multi-user.target
```

### Option 3: Rsync over SSH (Simplest)

**Cron job on YunoHost:**
```bash
# /etc/cron.d/sync-map-tiles
*/5 * * * * yunohost.app /home/yunohost.app/archivesmp/scripts/sync_maps.sh

# /home/yunohost.app/archivesmp/scripts/sync_maps.sh
#!/bin/bash

# Public maps from Hetzner
for instance in BENT01 CLIP01 CREA01 DEV01 EMAD01 HARD01 MINE01 MIN01 ROY01 SMP201; do
    rsync -avz --delete \
        root@135.181.212.169:/home/amp/.ampdata/instances/$instance/plugins/Pl3xMap/web/ \
        /var/www/maps.archivesmp.site/data/${instance,,}/
done

# Public maps from OVH
for instance in BIG01 EVO01 PRI01 SMP101; do
    rsync -avz --delete \
        root@37.187.143.41:/home/amp/.ampdata/instances/$instance/plugins/Pl3xMap/web/ \
        /var/www/maps.archivesmp.site/data/${instance,,}/
done

# Private maps from Hetzner
for instance in CSMC01; do
    rsync -avz --delete \
        root@135.181.212.169:/home/amp/.ampdata/instances/$instance/plugins/Pl3xMap/web/ \
        /var/www/private-maps.archivesmp.site/data/${instance,,}/
done

# Private maps from OVH (if any)
# for instance in TOW01; do
#     rsync -avz --delete \
#         root@37.187.143.41:/home/amp/.ampdata/instances/$instance/plugins/Pl3xMap/web/ \
#         /var/www/private-maps.archivesmp.site/data/${instance,,}/
# done
```

## LiveAtlas Configuration

### Public LiveAtlas (maps.archivesmp.site)

**nginx configuration:**
```nginx
# /etc/nginx/sites-available/maps.archivesmp.site
server {
    listen 80;
    listen [::]:80;
    server_name maps.archivesmp.site;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name maps.archivesmp.site;
    
    ssl_certificate /etc/letsencrypt/live/maps.archivesmp.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/maps.archivesmp.site/privkey.pem;
    
    root /var/www/maps.archivesmp.site;
    index index.html;
    
    # LiveAtlas static files
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Map tile data
    location /data/ {
        alias /var/www/maps.archivesmp.site/data/;
        add_header Cache-Control "public, max-age=300";
        add_header Access-Control-Allow-Origin "*";
    }
    
    # Instance list API
    location /api/instances {
        default_type application/json;
        return 200 '[
            {"name": "BENT01", "title": "Bent World", "url": "/data/bent01/"},
            {"name": "CLIP01", "title": "Clip World", "url": "/data/clip01/"},
            {"name": "SMP201", "title": "SMP 2.0", "url": "/data/smp201/"}
        ]';
    }
}
```

**LiveAtlas config.json:**
```json
{
  "servers": [
    {
      "id": "bent01",
      "name": "Bent World",
      "dynmap": false,
      "pl3xmap": true,
      "url": "https://maps.archivesmp.site/data/bent01/"
    },
    {
      "id": "clip01",
      "name": "Clip World",
      "dynmap": false,
      "pl3xmap": true,
      "url": "https://maps.archivesmp.site/data/clip01/"
    },
    {
      "id": "smp201",
      "name": "SMP 2.0",
      "dynmap": false,
      "pl3xmap": true,
      "url": "https://maps.archivesmp.site/data/smp201/"
    }
  ],
  "ui": {
    "playersAboveMarkers": true,
    "compactPlayerMarkers": false,
    "playersSearch": true,
    "coordinates": {
      "enabled": true
    }
  }
}
```

### Private LiveAtlas (private-maps.archivesmp.site)

**nginx with YunoHost SSO:**
```nginx
# /etc/nginx/sites-available/private-maps.archivesmp.site
server {
    listen 443 ssl http2;
    server_name private-maps.archivesmp.site;
    
    ssl_certificate /etc/letsencrypt/live/private-maps.archivesmp.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/private-maps.archivesmp.site/privkey.pem;
    
    root /var/www/private-maps.archivesmp.site;
    index index.html;
    
    # YunoHost SSO authentication
    include /etc/nginx/conf.d/yunohost_sso.conf.inc;
    
    # Require authentication for all access
    location / {
        # SSO protection
        auth_request /auth;
        error_page 401 = @error401;
        
        try_files $uri $uri/ =404;
    }
    
    # Map data also requires auth
    location /data/ {
        auth_request /auth;
        error_page 401 = @error401;
        
        alias /var/www/private-maps.archivesmp.site/data/;
        add_header Cache-Control "public, max-age=300";
    }
    
    # SSO authentication endpoint
    location /auth {
        internal;
        proxy_pass http://127.0.0.1:9999/auth;
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";
        proxy_set_header X-Original-URI $request_uri;
    }
    
    location @error401 {
        return 302 https://sso.archivesmp.site/?r=$scheme://$http_host$request_uri;
    }
}
```

**Private LiveAtlas config.json:**
```json
{
  "servers": [
    {
      "id": "csmc01",
      "name": "Counter-Strike MC",
      "dynmap": false,
      "pl3xmap": true,
      "url": "https://private-maps.archivesmp.site/data/csmc01/",
      "description": "🔒 Authenticated access only - Anti screen camping"
    },
    {
      "id": "roy01",
      "name": "Battle Royale",
      "dynmap": false,
      "pl3xmap": true,
      "url": "https://private-maps.archivesmp.site/data/roy01/",
      "description": "🔒 Staff/spectator access only"
    }
  ],
  "ui": {
    "playersAboveMarkers": false,
    "compactPlayerMarkers": true,
    "playersSearch": false,
    "coordinates": {
      "enabled": false
    }
  }
}
```

## Pl3xMap Plugin Configuration

### Universal Config (All Instances)

```yaml
# data/expectations/paper/Pl3xMap/config.yml
settings:
  language: en
  debug-mode: false
  
  # Internal web server (disabled - use LiveAtlas instead)
  internal-webserver:
    enabled: false  # Don't serve tiles directly from game servers
    port: 0
  
  # Tile rendering
  web-directory:
    path: plugins/Pl3xMap/web
  
  render:
    background-render: true
    render-interval: 15  # Render every 15 seconds
    max-render-threads: 2
  
  # Player markers (different for public vs private)
  # This will be variable config based on instance
```

### Variable Config: Public vs Private

**Public instances (BENT01, CLIP01, etc.):**
```yaml
settings:
  player-tracker:
    enabled: true
    nameplate-show-health: true
    nameplate-show-armor: true
    update-interval: 5  # Update player positions every 5 seconds
```

**Private instances (CSMC01, ROY01):**
```yaml
settings:
  player-tracker:
    enabled: false  # DON'T show player positions on tactical maps!
    # Or if you want staff to see:
    enabled: true
    hide-invisible-players: true
    hide-spectators: false  # Staff can see other staff
```

## Pl3xMap Config Management

### Add to Plugin Categorization

```python
# scripts/categorize_plugins.py - UPDATE

# Add after Paper plugins section:
PAPER_MAP_CONFIGS = {
    'public': [
        'BENT01', 'BIG01', 'CLIP01', 'CREA01', 'DEV01',
        'EMAD01', 'EVO01', 'HARD01', 'MINE01', 'MIN01',
        'PRI01', 'SMP101', 'SMP201'
    ],
    'private': [
        'CSMC01',  # Counter-Strike MC - anti screen camping
        'ROY01',   # Battle Royale - hide player positions
        # 'TOW01',  # Towny - if competitive (you tell me!)
    ]
}
```

### Platform-Specific Baseline

```
data/baselines/plugin_configs/
  └── paper/
      └── Pl3xMap/
          ├── universal/
          │   ├── config.yml (common settings)
          │   └── lang/en.yml
          ├── public/
          │   └── config.yml (player tracking ON)
          └── private/
              └── config.yml (player tracking OFF)
```

## Deployment Strategy

### 1. Enable Pl3xMap on Instances

```python
# Remove from NOT_DEPLOYED set in categorize_plugins.py
NOT_DEPLOYED = {
    'DeluxeMenus', 'Duels', 'Essentials', 'EssentialsChat', 
    'EssentialsSpawn', 'Geyser-Spigot', 'LibertyBans', 'LiveAtlas'
    # Removed: 'Pl3xMap'
}

# Add to Paper plugins
PAPER_PLUGINS.add('Pl3xMap')
```

### 2. Deploy Configs via Agent

```bash
# Deploy public map configs
curl -X POST http://localhost:8000/api/deploy \
  -d '{
    "instance_names": ["BENT01", "CLIP01", "SMP201"],
    "plugin_name": "Pl3xMap",
    "config_variant": "public"
  }'

# Deploy private map configs
curl -X POST http://localhost:8000/api/deploy \
  -d '{
    "instance_names": ["CSMC01", "ROY01"],
    "plugin_name": "Pl3xMap",
    "config_variant": "private"
  }'
```

### 3. Set Up Sync Service

**Choice A: Agent-backed (recommended)**
```bash
# On Hetzner/OVH
sudo systemctl enable archivesmp-tile-sync
sudo systemctl start archivesmp-tile-sync

# On YunoHost
sudo systemctl enable archivesmp-map-sync
sudo systemctl start archivesmp-map-sync
```

**Choice B: Rsync cron**
```bash
# On YunoHost
crontab -e
# Add:
*/5 * * * * /home/yunohost.app/archivesmp/scripts/sync_maps.sh
```

### 4. Install LiveAtlas

```bash
# On YunoHost
cd /var/www
git clone https://github.com/JLyne/LiveAtlas.git maps.archivesmp.site
git clone https://github.com/JLyne/LiveAtlas.git private-maps.archivesmp.site

# Configure
cp maps.archivesmp.site/config.example.json maps.archivesmp.site/config.json
cp private-maps.archivesmp.site/config.example.json private-maps.archivesmp.site/config.json

# Edit configs (see above)
nano maps.archivesmp.site/config.json
nano private-maps.archivesmp.site/config.json

# Set permissions
chown -R www-data:www-data /var/www/maps.archivesmp.site
chown -R www-data:www-data /var/www/private-maps.archivesmp.site
```

## Questions for You

Before I implement this, please tell me:

1. **Which instances should be private?**
   - Confirmed: CSMC01, ROY01
   - Unsure: TOW01?
   - Any others?

2. **Preferred sync method?**
   - Option 1: Agent-backed sync via MinIO (most robust)
   - Option 2: NFS/Samba mount (direct filesystem)
   - Option 3: Rsync cron job (simplest)

3. **YunoHost domains?**
   - Public: `maps.archivesmp.site`?
   - Private: `private-maps.archivesmp.site`? Or different subdomain?

4. **Who needs access to private maps?**
   - Staff only?
   - Donors?
   - Specific YunoHost groups?

5. **Map update frequency?**
   - Current: Every 15 seconds (aggressive)
   - Sync: Every 5 minutes (suggested)
   - Adjust?

Let me know and I'll implement the solution!
