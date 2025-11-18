# LiveAtlas Multi-Server Setup Guide

## Overview

This setup creates **two separate LiveAtlas deployments**:

1. **Public Map** (`map.archivesmp.site`) - Open access to standard survival worlds
2. **BTS Map** (`btsmap.archivesmp.site`) - Auth-required for tactical/competitive worlds

Each deployment shows a **server dropdown menu** with all relevant instances.

## Architecture

```
User Browser
    ↓
nginx Reverse Proxy (on proxy server/YunoHost)
    ↓
┌─────────────────────────────────────────────────────┐
│ Public Map (map.archivesmp.site)                    │
│   → /map/bent01/ → http://135.181.212.169:8080/     │
│   → /map/clip01/ → http://135.181.212.169:8081/     │
│   → /map/smp201/ → http://37.187.143.41:8080/       │
│   ... (all PUBLIC_INSTANCES)                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ BTS Map (btsmap.archivesmp.site) [Auth Required]    │
│   → /map/roy01/  → http://135.181.212.169:8082/     │
│   → /map/csmc01/ → http://135.181.212.169:8083/     │
│   ... (all BTS_INSTANCES)                           │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

### On Each Minecraft Server (Hetzner/OVH)

1. **Pl3xMap installed and configured** on all instances
2. **Internal webserver enabled** in each Pl3xMap `config.yml`:
   ```yaml
   settings:
     internal-webserver:
       enabled: true
       bind: 0.0.0.0
       port: 8080  # Unique port per instance!
   ```
3. **Unique ports assigned** to each instance:
   - BENT01: 8080
   - CLIP01: 8081
   - CSMC01: 8082
   - ROY01: 8083
   - etc.

### On YunoHost Server

1. **Two custom domains configured**:
   - `map.archivesmp.site` - Public map (no auth)
   - `btsmap.archivesmp.site` - Private map (SSO auth)

2. **nginx already installed** (comes with YunoHost)

3. **LiveAtlas to be installed** at:
   - `/var/www/map.archivesmp.site/`
   - `/var/www/btsmap.archivesmp.site/`

## Step 1: Generate Configs

On your development machine:

```bash
cd /d/homeamp.ampdata/homeamp.ampdata/software/homeamp-config-manager

# Generate LiveAtlas configs
python -m src.liveatlas.map_config_generator
```

This creates:
- `/tmp/liveatlas-public-config.json` - Public map server list
- `/tmp/liveatlas-bts-config.json` - BTS map server list
- `/tmp/nginx-public-pl3xmap.conf` - nginx config for public
- `/tmp/nginx-bts-pl3xmap.conf` - nginx config for BTS

## Step 2: Deploy LiveAtlas on YunoHost

### 2.1 Download LiveAtlas

```bash
# On YunoHost server
wget https://github.com/JLyne/LiveAtlas/releases/latest/download/LiveAtlas.zip
unzip LiveAtlas.zip -d /tmp/liveatlas
```

### 2.2 Deploy Public Map

```bash
# Create directory (YunoHost structure)
sudo mkdir -p /var/www/map.archivesmp.site/
sudo cp -r /tmp/liveatlas/* /var/www/map.archivesmp.site/

# Set permissions for YunoHost
sudo chown -R www-data:www-data /var/www/map.archivesmp.site/

# Inject config into index.html
sudo nano /var/www/map.archivesmp.site/index.html
```

Find the `<script>` tag and add:

```html
<script>
    window.liveAtlasConfig = {
        "servers": {
            "bent01": {
                "label": "BENT01 - Standard Survival",
                "pl3xmap": "https://map.archivesmp.site/map/bent01/"
            },
            "clip01": {
                "label": "CLIP01 - Clip World",
                "pl3xmap": "https://map.archivesmp.site/map/clip01/"
            }
            // ... paste from liveatlas-public-config.json
        }
    };
</script>
```

### 2.3 Deploy BTS Map

```bash
# Create directory
sudo mkdir -p /var/www/btsmap.archivesmp.site/
sudo cp -r /tmp/liveatlas/* /var/www/btsmap.archivesmp.site/

# Set permissions
sudo chown -R www-data:www-data /var/www/btsmap.archivesmp.site/

# Inject config
sudo nano /var/www/btsmap.archivesmp.site/index.html
```

Same process, but use `liveatlas-bts-config.json` content.

## Step 3: Configure YunoHost nginx Reverse Proxy

### 3.1 Public Map Config

Create `/etc/nginx/conf.d/map.archivesmp.site.conf` (YunoHost custom config):

```nginx
# Public LiveAtlas Map - No Authentication
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name map.archivesmp.site;
    
    # YunoHost SSL (auto-managed by certbot)
    ssl_certificate /etc/yunohost/certs/map.archivesmp.site/crt.pem;
    ssl_certificate_key /etc/yunohost/certs/map.archivesmp.site/key.pem;
    
    # YunoHost SSL settings
    include /etc/nginx/conf.d/ssl.conf;
    
    # LiveAtlas static files (root serves from /var/www/map.archivesmp.site/)
    root /var/www/map.archivesmp.site;
    index index.html;
    
    # Serve LiveAtlas - catch all server URLs
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # Reverse proxy to Pl3xMap instances
    include /etc/nginx/conf.d/pl3xmap-public-proxies.conf;
    
    # Logging
    access_log /var/log/nginx/map.archivesmp.site-access.log;
    error_log /var/log/nginx/map.archivesmp.site-error.log;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name map.archivesmp.site;
    return 301 https://$server_name$request_uri;
}
```

### 3.2 BTS Map Config (with YunoHost SSO)

Create `/etc/nginx/conf.d/btsmap.archivesmp.site.conf`:

```nginx
# BTS LiveAtlas Map - Requires YunoHost SSO Authentication
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name btsmap.archivesmp.site;
    
    # YunoHost SSL
    ssl_certificate /etc/yunohost/certs/btsmap.archivesmp.site/crt.pem;
    ssl_certificate_key /etc/yunohost/certs/btsmap.archivesmp.site/key.pem;
    include /etc/nginx/conf.d/ssl.conf;
    
    # YunoHost SSO Portal for authentication
    include /etc/nginx/conf.d/yunohost_sso.conf.inc;
    
    root /var/www/btsmap.archivesmp.site;
    index index.html;
    
    # Require authentication for all map access
    location / {
        # YunoHost SSO authentication
        include /etc/nginx/conf.d/yunohost_panel.conf.inc;
        more_clear_input_headers 'Accept-Encoding';
        
        try_files $uri $uri/ /index.html;
    }
    
    # Reverse proxy to Pl3xMap instances (also protected)
    include /etc/nginx/conf.d/pl3xmap-bts-proxies.conf;
    
    access_log /var/log/nginx/btsmap.archivesmp.site-access.log;
    error_log /var/log/nginx/btsmap.archivesmp.site-error.log;
}

# HTTP redirect
server {
    listen 80;
    listen [::]:80;
    server_name btsmap.archivesmp.site;
    return 301 https://$server_name$request_uri;
}
```

### 3.3 Create Reverse Proxy Configs

Copy generated configs to YunoHost nginx:

```bash
# Public map proxies
sudo cp /tmp/nginx-public-pl3xmap.conf /etc/nginx/conf.d/pl3xmap-public-proxies.conf

# BTS map proxies
sudo cp /tmp/nginx-bts-pl3xmap.conf /etc/nginx/conf.d/pl3xmap-bts-proxies.conf
```

### 3.4 Add Domains to YunoHost

```bash
# Add domains via YunoHost CLI
sudo yunohost domain add map.archivesmp.site
sudo yunohost domain add btsmap.archivesmp.site

# Install SSL certificates (Let's Encrypt)
sudo yunohost domain cert-install map.archivesmp.site
sudo yunohost domain cert-install btsmap.archivesmp.site
```

### 3.5 Test and Reload

```bash
# Test nginx config
sudo nginx -t

# Reload nginx (YunoHost manages the service)
sudo systemctl reload nginx
```

## Step 4: Configure Pl3xMap Internal Webservers

On each Minecraft server, ensure Pl3xMap is configured:

### Hetzner (135.181.212.169)

For each instance, edit `plugins/Pl3xMap/config.yml`:

```yaml
settings:
  internal-webserver:
    enabled: true
    bind: 0.0.0.0
    port: 8080  # BENT01
    # port: 8081  # CLIP01
    # port: 8082  # CSMC01
    # etc.
```

Restart servers to apply.

### OVH (37.187.143.41)

Same process, assign unique ports starting from 8080.

## Step 5: Test

### Public Map

Visit: `https://map.archivesmp.site/`

- Should see LiveAtlas interface with server dropdown
- Click dropdown → select BENT01 → map loads
- URL should change to `https://map.archivesmp.site/bent01/`
- No authentication required

### BTS Map

Visit: `https://btsmap.archivesmp.site/`

- Should redirect to YunoHost SSO portal (if not logged in)
- Login with YunoHost user account
- After auth, see server dropdown with BTS instances only
- Select ROY01 → map loads
- URL: `https://btsmap.archivesmp.site/roy01/`

## Automation

### Auto-Update Configs

Add to config manager agent or create systemd timer:

```python
# In agent startup or cron job
from src.liveatlas.map_config_generator import LiveAtlasConfigGenerator

generator = LiveAtlasConfigGenerator(db)

# Regenerate on plugin changes and push to YunoHost
generator.save_liveatlas_config('public', '/tmp/liveatlas-public-config.json')
generator.save_liveatlas_config('bts', '/tmp/liveatlas-bts-config.json')

# Use SSH/SFTP to deploy to YunoHost (or run generator on YunoHost directly)
```

### Web UI Integration

Add to `deploy.html` "Pl3xMap Sync" tab:

- Button: "Regenerate LiveAtlas Config"
- Shows current server count (public vs BTS)
- Preview config before deployment
- Deploy to proxy server via API/SSH

## Instance Classification

Edit `src/liveatlas/map_config_generator.py` to change which instances are public vs BTS:

```python
PUBLIC_INSTANCES = {
    'BENT01', 'CLIP01', 'SMP101', 'SMP201', ...
}

BTS_INSTANCES = {
    'ROY01',   # Battle Royale - hide player positions
    'CSMC01',  # Counter-Strike - anti-screen camping
}
```

## Troubleshooting

### Map not loading for a server

1. Check Pl3xMap internal webserver is running:
   ```bash
   curl http://localhost:8080/
   ```

2. Check nginx can reach it:
   ```bash
   curl http://135.181.212.169:8080/
   ```

3. Check browser console for CORS/SSL errors

### Server not in dropdown

1. Verify instance has Pl3xMap installed (check database)
2. Regenerate config with updated instance list
3. Check instance classification (public vs BTS)

### CORS errors

Ensure nginx reverse proxy has proper headers:

```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-Proto $scheme;
```

## Security Notes

- **BTS map requires authentication** - configure YunoHost SSO properly
- **Internal Pl3xMap webservers** should NOT be exposed to public internet
- **Reverse proxy** acts as security layer
- **SSL required** if hosting LiveAtlas over HTTPS (mixed content blocks)
