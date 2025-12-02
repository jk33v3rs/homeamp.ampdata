# ArchiveSMP Infrastructure Connection Details

**Quick reference for all service endpoints and credentials**

---

## Hetzner Server (135.181.212.169)

### MinIO (Object Storage)
- **API Endpoint**: `135.181.212.169:3800`
- **Console**: `127.0.0.1:9001` (localhost only)
- **YunoHost HTTPS** (recommended): `https://minio.archivesmp.site`
- **Auth**: Access key + Secret key
- **Protocol**: HTTP (or HTTPS via YunoHost proxy)

### MariaDB (Database)
- **Endpoint**: `135.181.212.169:3369`
- **Database**: `asmp_config`
- **Username**: `sqlworkerSMP`
- **Password**: `<from environment>`
- **SSL**: Disabled
- **Options**: `allowPublicKeyRetrieval=true`

### Redis (Job Queue)
- **Endpoint**: `135.181.212.169:6379`
- **Username**: `default`
- **Password**: `<from environment>`
- **Protocol**: Redis TCP

### Web API (Management Interface)
- **Endpoint**: `135.181.212.169:8000`
- **YunoHost HTTPS**: `https://archivesmp.site` (or subdomain)
- **Workers**: 4 (uvicorn)

### AMP Panel
- **Endpoint**: `http://135.181.212.169:8080`
- **Instances**: ~11 game servers
- **Credentials**: Admin user/pass

---

## OVH Server (37.187.143.41)

### AMP Panel
- **Endpoint**: `http://37.187.143.41:8080`
- **Instances**: ~9-11 game servers
- **Credentials**: Admin user/pass

### OVH Client Agent (to be deployed)
- Connects to Hetzner Redis for job queue
- Reports results to Hetzner Web API
- No local storage except logs

---

## Connection Strings

### Python MinIO Client
```python
from minio import Minio

# Option 1: Direct connection (HTTP)
client = Minio(
    "135.181.212.169:3800",
    access_key="<ACCESS_KEY>",
    secret_key="<SECRET_KEY>",
    secure=False
)

# Option 2: YunoHost HTTPS (recommended)
client = Minio(
    "minio.archivesmp.site",
    access_key="<ACCESS_KEY>",
    secret_key="<SECRET_KEY>",
    secure=True
)
```

### Python MariaDB Client
```python
import mysql.connector

conn = mysql.connector.connect(
    host="135.181.212.169",
    port=3369,
    database="asmp_config",
    user="sqlworkerSMP",
    password="<PASSWORD>",
    ssl_disabled=True,
    allow_public_key_retrieval=True
)
```

### Python Redis Client
```python
import redis

r = redis.Redis(
    host="135.181.212.169",
    port=6379,
    username="default",
    password="<PASSWORD>",
    decode_responses=True
)
```

### SQLAlchemy Connection String
```python
DATABASE_URL = "mysql+mysqlconnector://sqlworkerSMP:<PASSWORD>@135.181.212.169:3369/asmp_config?ssl_disabled=true&allow_public_key_retrieval=true"
```

---

## Firewall Rules Required

```bash
# On Hetzner, allow OVH to access services
sudo ufw allow from 37.187.143.41 to any port 3800 proto tcp comment 'MinIO from OVH'
sudo ufw allow from 37.187.143.41 to any port 6379 proto tcp comment 'Redis from OVH'
sudo ufw allow from 37.187.143.41 to any port 3369 proto tcp comment 'MariaDB from OVH'
sudo ufw allow from 37.187.143.41 to any port 8000 proto tcp comment 'Web API from OVH'
```

---

## Environment Variables

### Hetzner Host Agent (.env)
```bash
# MinIO
MINIO_ENDPOINT=localhost:3800
MINIO_ACCESS_KEY=<key>
MINIO_SECRET_KEY=<secret>
MINIO_SECURE=false

# MariaDB
MARIADB_HOST=localhost
MARIADB_PORT=3369
MARIADB_DATABASE=asmp_config
MARIADB_USER=sqlworkerSMP
MARIADB_PASSWORD=<password>

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<password>

# AMP
AMP_HETZNER_URL=http://localhost:8080
AMP_HETZNER_USER=admin
AMP_HETZNER_PASS=<password>
AMP_OVH_URL=http://37.187.143.41:8080
AMP_OVH_USER=admin
AMP_OVH_PASS=<password>
```

### OVH Client Agent (.env)
```bash
# Hetzner services (remote)
HETZNER_MINIO=135.181.212.169:3800
HETZNER_REDIS_HOST=135.181.212.169
HETZNER_REDIS_PORT=6379
HETZNER_REDIS_PASSWORD=<password>
HETZNER_API=http://135.181.212.169:8000

# MinIO credentials
MINIO_ACCESS_KEY=<key>
MINIO_SECRET_KEY=<secret>

# Local AMP
AMP_LOCAL_URL=http://localhost:8080
AMP_LOCAL_USER=admin
AMP_LOCAL_PASS=<password>
```

---

## YunoHost Integration (Optional but Recommended)

### Benefits
- Free Let's Encrypt SSL certificates
- Automatic certificate renewal
- Clean subdomain routing
- Built-in nginx reverse proxy

### Setup
```bash
# Install YunoHost app (if not already)
# or configure manual nginx reverse proxy

# For MinIO
Domain: minio.archivesmp.site → localhost:3800

# For Web API
Domain: config.archivesmp.site → localhost:8000

# Update DNS
minio.archivesmp.site A 135.181.212.169
config.archivesmp.site A 135.181.212.169
```

### Updated Connection Strings with HTTPS
```python
# MinIO via YunoHost
client = Minio("minio.archivesmp.site", secure=True, ...)

# Web API via YunoHost
API_URL = "https://config.archivesmp.site"
```

---

## Testing Connectivity

### From OVH to Hetzner

```bash
# Test MinIO
curl -v http://135.181.212.169:3800/minio/health/live

# Test Redis
redis-cli -h 135.181.212.169 -p 6379 -a <password> PING

# Test MariaDB
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p<password> asmp_config -e "SELECT 1"

# Test Web API
curl http://135.181.212.169:8000/health
```

---

## Security Notes

1. **Passwords**: Store in environment variables, NEVER in code
2. **Firewall**: Restrict access to OVH IP only (37.187.143.41)
3. **HTTPS**: Use YunoHost reverse proxy for SSL (recommended)
4. **Redis**: Password protected, username is "default"
5. **MariaDB**: No SSL but allowPublicKeyRetrieval for auth
6. **MinIO**: Consider bucket policies for access control

---

## Service Status Commands

### On Hetzner
```bash
# MinIO
sudo systemctl status minio

# Redis
sudo systemctl status redis

# MariaDB
sudo systemctl status mariadb

# Web API
sudo systemctl status archivesmp-webapi

# Host Agent
sudo systemctl status homeamp-agent
```

### Check Logs
```bash
# MinIO logs
journalctl -u minio -f

# Redis logs
journalctl -u redis -f

# MariaDB logs
sudo tail -f /var/log/mysql/error.log

# Web API logs
journalctl -u archivesmp-webapi -f

# Agent logs
journalctl -u homeamp-agent -f
```
