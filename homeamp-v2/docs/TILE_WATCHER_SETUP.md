# Pl3xMap Tile Watcher Setup Guide

## Overview

The tile watcher monitors Pl3xMap plugin directories on your Minecraft servers and automatically syncs map tiles to MinIO (S3-compatible storage) for serving via LiveAtlas on a separate web server.

## Architecture

```
Paper Servers (Hetzner/OVH)
  ├── BENT01/plugins/Pl3xMap/web/tiles/
  ├── CSMC01/plugins/Pl3xMap/web/tiles/
  └── ... (16 instances)
         ↓
    Tile Watcher (monitors changes)
         ↓
    MinIO Server (S3 storage)
      ├── pl3xmap-tiles/
      │   ├── public/bent01/    (open access)
      │   ├── public/big01/
      │   └── private/csmc01/   (auth-walled)
         ↓
    YunoHost Server (LiveAtlas)
      ├── maps.archivesmp.site/      (public)
      └── private-maps.archivesmp.site/  (auth)
```

## Configuration

### 1. Install MinIO

**On a separate server or same server:**

```bash
# Download MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Create directories
sudo mkdir -p /data/minio
sudo mkdir -p /etc/minio

# Create systemd service
sudo tee /etc/systemd/system/minio.service > /dev/null <<EOF
[Unit]
Description=MinIO Object Storage
After=network.target

[Service]
Type=simple
User=amp
WorkingDirectory=/home/amp
ExecStart=/usr/local/bin/minio server /data/minio --address ":9000" --console-address ":9001"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start MinIO
sudo systemctl daemon-reload
sudo systemctl enable minio
sudo systemctl start minio
```

Access MinIO console at `http://your-server:9001` (default credentials: `minioadmin` / `minioadmin`)

### 2. Configure Environment Variables

Edit `.env` in homeamp-v2 directory:

```dotenv
# MinIO Configuration
MINIO_ENDPOINT=your-minio-server.com:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_SECURE=False  # Set True for HTTPS
MINIO_BUCKET_TILES=pl3xmap-tiles

# Tile Watcher
TILE_WATCHER_ENABLED=True
TILE_WATCHER_SYNC_INTERVAL=300  # Sync every 5 minutes
TILE_WATCHER_FORCE_SYNC=False   # Set True for initial full sync
```

### 3. Configure Access Levels

Edit `src/agent/tile_watcher.py` to customize which instances are public vs private:

```python
self.access_levels: Dict[str, List[str]] = {
    "public": [
        "BENT01", "BIG01", "CLIP01", "CREA01", "DEV01",
        "EMAD01", "EVO01", "HARD01", "MINE01", "MIN01",
        "PRI01", "SMP101", "SMP201",
    ],
    "private": [
        "CSMC01",  # Counter-Strike MC (anti-screen camping)
        "ROY01",   # Battle Royale (spectator protection)
        "TOW01",   # Towny PvP (base protection)
    ],
}
```

**Public maps** = Anyone can view  
**Private maps** = Require authentication (useful for tactical gameplay where map visibility gives unfair advantage)

## Usage

### Option 1: Run as Standalone Service

```bash
# Install dependencies
cd homeamp-v2
pip install -e .

# Run tile watcher
homeamp-tile-watcher
```

### Option 2: Run with Main Agent

Enable tile watcher in `.env`:

```dotenv
TILE_WATCHER_ENABLED=True
```

Then start the agent:

```bash
homeamp-agent
```

The tile watcher will run in the background alongside other agent tasks.

### Option 3: Systemd Service (Production)

Create `/etc/systemd/system/homeamp-tile-watcher.service`:

```ini
[Unit]
Description=HomeAMP Pl3xMap Tile Watcher
After=network.target minio.service

[Service]
Type=simple
User=amp
WorkingDirectory=/home/amp/.ampdata/homeamp.ampdata/homeamp-v2
Environment="PATH=/home/amp/.ampdata/homeamp.ampdata/.conda/bin:/usr/bin"
ExecStart=/home/amp/.ampdata/homeamp.ampdata/.conda/bin/homeamp-tile-watcher
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable homeamp-tile-watcher
sudo systemctl start homeamp-tile-watcher
sudo systemctl status homeamp-tile-watcher
```

## YunoHost LiveAtlas Setup

On your YunoHost server, create a sync service to pull tiles from MinIO:

```python
# /home/yunohost.app/map-sync.py
from minio import Minio
from pathlib import Path
import time

minio = Minio(
    'your-minio-server.com:9000',
    access_key='your-access-key',
    secret_key='your-secret-key',
    secure=False
)

public_dir = Path('/var/www/maps.archivesmp.site/data')
private_dir = Path('/var/www/private-maps.archivesmp.site/data')

while True:
    # Sync public maps
    for obj in minio.list_objects('pl3xmap-tiles', prefix='public/', recursive=True):
        local_path = public_dir / obj.object_name.replace('public/', '')
        local_path.parent.mkdir(parents=True, exist_ok=True)
        minio.fget_object('pl3xmap-tiles', obj.object_name, str(local_path))
    
    # Sync private maps
    for obj in minio.list_objects('pl3xmap-tiles', prefix='private/', recursive=True):
        local_path = private_dir / obj.object_name.replace('private/', '')
        local_path.parent.mkdir(parents=True, exist_ok=True)
        minio.fget_object('pl3xmap-tiles', obj.object_name, str(local_path))
    
    print(f"Sync completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    time.sleep(300)  # Every 5 minutes
```

## Monitoring

### Check Sync Status

```bash
# View logs
tail -f logs/homeamp.log | grep -i tile

# Check systemd service
sudo journalctl -u homeamp-tile-watcher -f
```

### Manual Sync

```python
from homeamp_v2.core.config import Settings
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.integrations.minio import MinIOClient
from homeamp_v2.agent.tile_watcher import TileWatcher

settings = Settings()
minio = MinIOClient(
    settings.minio_endpoint,
    settings.minio_access_key,
    settings.minio_secret_key,
    secure=settings.minio_secure
)

uow = UnitOfWork()
watcher = TileWatcher(uow, minio)

# Force full sync
results = watcher.sync_all_instances(force=True)
print(f"Synced {sum(results.values())} files across {len(results)} instances")
```

## Troubleshooting

### MinIO Connection Failed

```bash
# Test connectivity
curl http://your-minio-server:9000/minio/health/live

# Check credentials in MinIO console
http://your-minio-server:9001
```

### Tiles Not Syncing

1. Check Pl3xMap is installed: `homeamp plugins list | grep -i pl3x`
2. Check tile directories exist: `ls -la instances/BENT01/plugins/Pl3xMap/web/`
3. Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`
4. Force sync: `TILE_WATCHER_FORCE_SYNC=True`

### High CPU Usage

Reduce sync frequency: `TILE_WATCHER_SYNC_INTERVAL=600` (10 minutes)

### Storage Costs

MinIO is self-hosted, no cloud storage costs! But monitor disk space:

```bash
du -sh /data/minio/pl3xmap-tiles
```

## Performance Tips

1. **Use SSD storage** for MinIO for faster tile serving
2. **Network bandwidth**: 16 instances × 300-second sync = tiles updated every 5 minutes
3. **Incremental sync**: Only changed files are uploaded (hash comparison)
4. **Compression**: Tiles are already PNG (compressed), no further compression needed

## Security Notes

- **Public bucket**: Maps in `public/` prefix can be accessed without auth
- **Private bucket**: Maps in `private/` prefix should be behind YunoHost SSO
- **MinIO access**: Keep access keys secret, don't commit to git
- **Firewall**: Only expose MinIO port (9000) to your servers and YunoHost
