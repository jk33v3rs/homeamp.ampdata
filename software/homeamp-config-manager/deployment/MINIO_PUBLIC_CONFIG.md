# MinIO Public IP Configuration Guide

**Goal**: Configure MinIO on Hetzner to listen on public IP `135.181.212.169:3800` (accessible from OVH)

---

## Current State

```bash
# MinIO currently running at:
# API: localhost:9000
# Console: localhost:9001
```

---

## Required Configuration

### Step 1: Stop MinIO Service

```bash
# On Hetzner
sudo systemctl stop minio
```

### Step 2: Edit MinIO Configuration

**Option A: SystemD Service File** (if using systemd)

```bash
sudo nano /etc/systemd/system/minio.service
```

Update `ExecStart` to bind to public IP:

```ini
[Unit]
Description=MinIO
Documentation=https://docs.min.io
Wants=network-online.target
After=network-online.target
AssertFileIsExecutable=/usr/local/bin/minio

[Service]
WorkingDirectory=/usr/local

User=minio-user
Group=minio-user

# MinIO API on public IP:3800, console on localhost:9001
ExecStart=/usr/local/bin/minio server \
  --address 135.181.212.169:3800 \
  --console-address 127.0.0.1:9001 \
  /var/lib/minio/data

# Restart policy
Restart=always
RestartSec=5
LimitNOFILE=65536
TasksMax=infinity

# Security settings
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=/var/lib/minio

[Install]
WantedBy=multi-user.target
```

**Option B: Docker Compose** (if using Docker)

```yaml
version: '3.8'

services:
  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "135.181.212.169:3800:9000"  # API on public IP
      - "127.0.0.1:9001:9001"         # Console localhost only
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: <secure_password>
    command: server /data --console-address ":9001"
    volumes:
      - /var/lib/minio/data:/data
    restart: always
```

### Step 3: Reload SystemD and Start MinIO

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Start MinIO
sudo systemctl start minio

# Check status
sudo systemctl status minio

# View logs
journalctl -u minio -f
```

### Step 4: Verify MinIO is Listening on Public IP

```bash
# Check if MinIO is listening on 135.181.212.169:3800
sudo ss -tlnp | grep 3800

# Expected output:
# LISTEN 0 4096 135.181.212.169:3800 0.0.0.0:* users:(("minio",pid=XXXX,fd=X))
```

### Step 5: Configure Firewall Rules

```bash
# Allow MinIO API port from OVH
sudo ufw allow from 37.187.143.41 to any port 3800 proto tcp comment 'MinIO API from OVH'

# Or if using iptables:
sudo iptables -A INPUT -p tcp -s 37.187.143.41 --dport 3800 -j ACCEPT -m comment --comment "MinIO API from OVH"
sudo iptables-save > /etc/iptables/rules.v4
```

### Step 6: Test from OVH

```bash
# From OVH server, test connectivity
curl -v http://135.181.212.169:3800/minio/health/live

# Expected: 200 OK response
```

---

## MinIO Client Configuration

### On Hetzner (localhost access)

```bash
mc alias set hetzner-local http://localhost:3800 <ACCESS_KEY> <SECRET_KEY>
mc ls hetzner-local
```

### On OVH (remote access)

```bash
mc alias set hetzner-remote http://135.181.212.169:3800 <ACCESS_KEY> <SECRET_KEY>
mc ls hetzner-remote
```

---

## Python MinIO Client Configuration

### Install MinIO Python Client

```bash
pip install minio
```

### Example Usage

```python
from minio import Minio

# On Hetzner (localhost)
client = Minio(
    "localhost:3800",
    access_key="<ACCESS_KEY>",
    secret_key="<SECRET_KEY>",
    secure=False  # Use True if TLS enabled
)

# On OVH (remote)
client = Minio(
    "135.181.212.169:3800",
    access_key="<ACCESS_KEY>",
    secret_key="<SECRET_KEY>",
    secure=False  # Use True if TLS enabled
)

# List buckets
buckets = client.list_buckets()
for bucket in buckets:
    print(bucket.name)
```

---

## Security Considerations

### Option 1: Firewall-Only (Simplest)
- MinIO API on port 3800 (unencrypted HTTP)
- Firewall restricts access to OVH IP only
- **Risk**: Traffic not encrypted between servers
- **Use if**: Servers on same private network or you trust the route

### Option 2: YunoHost HTTPS Reverse Proxy (Recommended)
- YunoHost already has built-in HTTPS reverse proxy (nginx)
- Configure subdomain: `minio.archivesmp.site` → `localhost:3800`
- Automatic Let's Encrypt SSL certificate
- OVH connects via: `https://minio.archivesmp.site`
- **Pros**: Free SSL, automatic renewal, cleaner setup
- **Cons**: Requires DNS setup, YunoHost domain

**YunoHost Config Example:**
```bash
# Add MinIO as a YunoHost app or manual nginx config
sudo yunohost app setting minio domain -v minio.archivesmp.site
sudo yunohost app setting minio path -v /
sudo yunohost app setting minio port -v 3800

# Or manual nginx reverse proxy config
sudo nano /etc/nginx/conf.d/minio.conf
```

```nginx
server {
    listen 443 ssl http2;
    server_name minio.archivesmp.site;
    
    ssl_certificate /etc/yunohost/certs/minio.archivesmp.site/crt.pem;
    ssl_certificate_key /etc/yunohost/certs/minio.archivesmp.site/key.pem;
    
    location / {
        proxy_pass http://localhost:3800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # MinIO-specific headers
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

Then from OVH:
```python
client = Minio(
    "minio.archivesmp.site",
    access_key="<ACCESS_KEY>",
    secret_key="<SECRET_KEY>",
    secure=True  # HTTPS via YunoHost
)
```

### Option 3: Self-Signed TLS Encryption
```bash
# Generate self-signed cert (or use Let's Encrypt)
sudo mkdir -p /etc/minio/certs
cd /etc/minio/certs

# Generate private key and certificate
sudo openssl req -new -x509 -nodes -days 365 \
  -keyout private.key -out public.crt \
  -subj "/C=FI/ST=Helsinki/L=Helsinki/O=ArchiveSMP/CN=135.181.212.169"

# Set permissions
sudo chown -R minio-user:minio-user /etc/minio/certs
sudo chmod 600 /etc/minio/certs/private.key
sudo chmod 644 /etc/minio/certs/public.crt
```

Update systemd service to enable TLS:
```ini
ExecStart=/usr/local/bin/minio server \
  --address 135.181.212.169:3800 \
  --console-address 127.0.0.1:9001 \
  --certs-dir /etc/minio/certs \
  /var/lib/minio/data
```

Python client with TLS:
```python
client = Minio(
    "135.181.212.169:3800",
    access_key="<ACCESS_KEY>",
    secret_key="<SECRET_KEY>",
    secure=True,  # Enable TLS
    cert_check=False  # If using self-signed cert
)
```

---

## Troubleshooting

### MinIO Won't Start
```bash
# Check logs
journalctl -u minio -n 50

# Common issues:
# 1. Port already in use
sudo lsof -i :3800

# 2. Permission issues
sudo chown -R minio-user:minio-user /var/lib/minio
```

### OVH Can't Connect
```bash
# On Hetzner, verify listening
sudo ss -tlnp | grep 3800

# On OVH, test connectivity
telnet 135.181.212.169 3800

# Check firewall
sudo ufw status
sudo iptables -L -n | grep 3800
```

### Performance Issues
```bash
# Increase file descriptor limits
echo "minio-user soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "minio-user hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Restart MinIO
sudo systemctl restart minio
```

---

## Bucket Creation

```bash
# Create required buckets
mc mb hetzner-local/configs
mc mb hetzner-local/backups
mc mb hetzner-local/jars
mc mb hetzner-local/reference-data

# Set bucket policies (public read for configs if needed)
mc anonymous set download hetzner-local/configs

# Or keep private (recommended)
mc anonymous set none hetzner-local/configs
```

---

## Integration with homeamp-config-manager

Update config files to use public IP:

**Hetzner agent config:**
```yaml
minio:
  endpoint: localhost:3800
  access_key: ${MINIO_ACCESS_KEY}
  secret_key: ${MINIO_SECRET_KEY}
  secure: false
```

**OVH client config:**
```yaml
minio:
  endpoint: 135.181.212.169:3800
  access_key: ${MINIO_ACCESS_KEY}
  secret_key: ${MINIO_SECRET_KEY}
  secure: false
```
