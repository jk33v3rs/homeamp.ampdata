# Config Management Automation Tools - Usage Guide

## Overview

Complete suite of tools to manage Minecraft server configurations across all AMP instances with rule-based enforcement, drift detection, and automated remediation.

## Tools

### 1. Baseline Loader (`load_baselines.py`)
Loads universal baseline configs from markdown files into the database.

**Usage:**
```bash
# On Hetzner production
cd /opt/archivesmp-config-manager
python3 scripts/load_baselines.py
```

**What it does:**
- Parses all 82 `*_universal_config.md` files
- Populates `baseline_snapshots` table
- Creates GLOBAL priority rules in `config_rules` table
- Sets up initial expected values for all plugins

**When to run:**
- Once after deploying schema
- After updating baseline markdown files

---

### 2. Config Cache Populator (`populate_config_cache.py`)
Scans live instance configs and populates the variance cache.

**Usage:**
```bash
# One-time scan
python3 scripts/populate_config_cache.py --amp-dir /home/amp/.ampdata/instances

# On development machine (testing)
python3 scripts/populate_config_cache.py --amp-dir e:/homeamp.ampdata/utildata/hetzner/instances
```

**What it does:**
- Scans all plugin configs (YAML files)
- Scans standard server configs (server.properties, bukkit.yml, etc.)
- Detects datapacks in world/datapacks
- Resolves expected values using rule hierarchy
- Populates `config_variance_cache` table
- Logs drift to `config_drift_log` table

**When to run:**
- After loading baselines (initial population)
- Manually to refresh cache
- Before viewing variance GUI

---

### 3. Drift Scanner Service (`drift_scanner_service.py`)
Periodic service that monitors for config drift.

**Usage:**
```bash
# Run as foreground service (testing)
python3 scripts/drift_scanner_service.py --interval 300

# Run via systemd (production)
sudo systemctl start archivesmp-drift-scanner
sudo systemctl status archivesmp-drift-scanner
sudo journalctl -u archivesmp-drift-scanner -f
```

**What it does:**
- Runs every 5 minutes (configurable)
- Re-scans all instances for drift
- Updates variance cache with latest values
- Logs new drift events
- Detects when rules change and values drift

**When to run:**
- Continuously as a systemd service
- After making rule changes to detect compliance

**Systemd service file** (`/etc/systemd/system/archivesmp-drift-scanner.service`):
```ini
[Unit]
Description=ArchiveSMP Config Drift Scanner
After=network.target mariadb.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/archivesmp-config-manager
ExecStart=/usr/bin/python3 scripts/drift_scanner_service.py --interval 300
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

### 4. Config Enforcer (`enforce_config.py`)
Applies rule changes to live instances with backup/rollback support.

**Usage:**
```bash
# Dry run (see what would change)
python3 scripts/enforce_config.py BENT01

# Apply changes
python3 scripts/enforce_config.py BENT01 --apply

# Custom paths
python3 scripts/enforce_config.py BENT01 --apply \
  --amp-dir /home/amp/.ampdata/instances \
  --backup-dir /var/lib/archivesmp/backups
```

**What it does:**
- Identifies all drift for an instance
- Creates timestamped backup before changes
- Applies expected values to config files
- Updates YAML and .properties files
- Marks drift as resolved in database
- Supports rollback on failure

**When to run:**
- After creating/modifying rules
- To remediate detected drift
- During maintenance windows

**Backups:**
- Stored in `/var/lib/archivesmp/backups/{instance_id}-{timestamp}/`
- Includes manifest.json with backup metadata
- Preserves original file structure

---

## Workflow Examples

### Initial Setup (Fresh Deployment)
```bash
# 1. Load baselines into database
python3 scripts/load_baselines.py

# 2. Populate cache with current state
python3 scripts/populate_config_cache.py

# 3. Start drift scanner service
sudo systemctl enable archivesmp-drift-scanner
sudo systemctl start archivesmp-drift-scanner

# 4. View variance in GUI
# Open http://135.181.212.169:8000/static/variance.html
```

### Creating a New Rule
```bash
# 1. Use GUI or API to create rule
# Example: Set CoreProtect max-time for all survival instances

curl -X POST http://135.181.212.169:8000/api/rules/create \
  -H "Content-Type: application/json" \
  -d '{
    "config_type": "plugin",
    "plugin_name": "CoreProtect",
    "config_file": "config.yml",
    "config_key": "max-time",
    "expected_value": "30",
    "scope": "META_TAG",
    "meta_tag_id": "survival",
    "priority": 2
  }'

# 2. Wait for drift scanner to detect non-compliance (5 min)
# OR trigger manual scan:
python3 scripts/populate_config_cache.py

# 3. Review drift in GUI
# Red entries show instances violating new rule

# 4. Enforce on specific instance (dry run first)
python3 scripts/enforce_config.py BENT01

# 5. Apply changes
python3 scripts/enforce_config.py BENT01 --apply
```

### Bulk Enforcement
```bash
# Enforce all instances with drift
for instance in $(mysql -h localhost -P 3369 -u asmp_admin -p'Y0urP@ssw0rd' asmp_config \
  -N -e "SELECT DISTINCT instance_id FROM config_variance_cache WHERE is_drift = TRUE"); do
  echo "Enforcing $instance..."
  python3 scripts/enforce_config.py $instance --apply
done
```

### Rollback After Bad Change
```bash
# If enforcement broke something, rollback:
# (Backups are in /var/lib/archivesmp/backups/)

# List backups
ls -lah /var/lib/archivesmp/backups/

# Manual rollback (restore from backup dir)
# Or re-run enforcer with corrected rule
```

---

## Database Tables Usage

### `config_rules`
- **GLOBAL** (priority 4): Universal defaults from baselines
- **SERVER** (priority 3): Server-specific overrides (Hetzner vs OVH)
- **META_TAG** (priority 2): Tag-based rules (survival, creative, pvp-enabled)
- **INSTANCE** (priority 1): Instance-specific exceptions

### `config_variance_cache`
- Current state of all configs across all instances
- `variance_type`: GLOBAL, VARIABLE, META_TAG, INSTANCE, DRIFT, NONE
- `is_drift`: TRUE when actual != expected
- Updated by: `populate_config_cache.py`, `drift_scanner_service.py`

### `config_drift_log`
- Historical log of all drift events
- `status`: PENDING, RESOLVED, IGNORED
- `severity`: LOW, MEDIUM, HIGH
- Used for auditing and reporting

### `baseline_snapshots`
- Archive of expected values from baseline markdown files
- Reference for what GLOBAL rules should be
- Updated when baselines change

---

## Monitoring

### Check drift scanner status
```bash
sudo systemctl status archivesmp-drift-scanner
sudo journalctl -u archivesmp-drift-scanner -f
```

### Query current drift
```bash
mysql -h localhost -P 3369 -u asmp_admin -p'Y0urP@ssw0rd' asmp_config \
  -e "SELECT instance_id, COUNT(*) as drift_count 
      FROM config_variance_cache 
      WHERE is_drift = TRUE 
      GROUP BY instance_id;"
```

### View recent drift events
```bash
mysql -h localhost -P 3369 -u asmp_admin -p'Y0urP@ssw0rd' asmp_config \
  -e "SELECT * FROM config_drift_log 
      WHERE detected_at > DATE_SUB(NOW(), INTERVAL 24 HOUR) 
      ORDER BY detected_at DESC 
      LIMIT 20;"
```

---

## Troubleshooting

### Cache shows no data
- Run `populate_config_cache.py` to initial populate
- Check drift scanner service is running
- Verify instances exist in database

### Enforcer fails to apply changes
- Check AMP instance is stopped (safer to modify configs when offline)
- Verify file permissions (root or amp user)
- Review backup directory has space
- Check logs for specific errors

### Drift not detected
- Ensure rule exists with correct scope
- Verify instance has matching tags (for META_TAG rules)
- Check rule priority (lower = higher priority)
- Run cache populator manually to refresh

### Variable substitution not working
- Ensure `config_variables` table has values for instance
- Check variable name matches `{{VARIABLE_NAME}}` format
- Verify `is_variable` flag set on rule
