# Quick Installation - Hetzner Server

## One-Line Install

Run this command on your Hetzner server (135.181.212.169) as root:

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/install_hetzner.sh)
```

## What It Installs

### Services
- **homeamp-agent**: Background monitoring agent
- **archivesmp-webapi**: Web UI on port 8000

### Directories
- `/opt/archivesmp-config-manager/` - Application code
- `/etc/archivesmp/` - Configuration files
- `/var/lib/archivesmp/` - Data storage
- `/var/log/archivesmp/` - Log files

### Configuration
- `/etc/archivesmp/agent.yaml` - Agent configuration

## Post-Installation

1. **Start Services:**
   ```bash
   sudo systemctl enable homeamp-agent
   sudo systemctl start homeamp-agent
   
   sudo systemctl enable archivesmp-webapi
   sudo systemctl start archivesmp-webapi
   ```

2. **Check Status:**
   ```bash
   sudo systemctl status homeamp-agent
   sudo systemctl status archivesmp-webapi
   ```

3. **View Logs:**
   ```bash
   sudo journalctl -u homeamp-agent -f
   sudo journalctl -u archivesmp-webapi -f
   ```

4. **Access Web UI:**
   - http://135.181.212.169:8000/
   - http://archivesmp.site:8000/

## Troubleshooting

### Service won't start
```bash
# Check detailed logs
sudo journalctl -u homeamp-agent -xe
sudo journalctl -u archivesmp-webapi -xe
```

### Permission issues
```bash
sudo chown -R amp:amp /opt/archivesmp-config-manager
sudo chown -R amp:amp /var/lib/archivesmp
```

### Python errors
```bash
cd /opt/archivesmp-config-manager
sudo -u amp venv/bin/pip install -r requirements.txt
```

### Firewall blocking port 8000
```bash
sudo ufw allow 8000/tcp
```

## Manual Installation

If you prefer to see each step, download and run the script manually:

```bash
cd /tmp
curl -fsSL -o install_hetzner.sh https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/install_hetzner.sh
chmod +x install_hetzner.sh
sudo ./install_hetzner.sh
```

## Updating

To update to the latest version:

```bash
cd /opt/archivesmp-config-manager
sudo -u amp git pull
sudo -u amp venv/bin/pip install -r requirements.txt
sudo systemctl restart homeamp-agent
sudo systemctl restart archivesmp-webapi
```
