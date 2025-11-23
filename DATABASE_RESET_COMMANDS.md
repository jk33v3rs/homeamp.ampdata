# ============================================================================
# QUICK COMMANDS: Database Reset & Initialization
# ============================================================================
# Copy-paste ready commands for resetting the database
#
# CRITICAL: This drops ALL data! Backup first if needed!
# ============================================================================

# ============================================================================
# FOR PRODUCTION (Hetzner Debian 12) - Run via RDP/SSH as webadmin
# ============================================================================

# Option 1: Using the init script (recommended)
cd /opt/archivesmp-config-manager
bash software/homeamp-config-manager/scripts/init_database.sh

# Option 2: Manual commands (if script fails)
mysql -u sqlworkerSMP -p << 'EOF'
DROP DATABASE IF EXISTS asmp_config;
CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

mysql -u sqlworkerSMP -p asmp_config < /opt/archivesmp-config-manager/AUTHORITATIVE_SCHEMA.sql

# Restart services after database reset
sudo systemctl restart homeamp-agent
sudo systemctl restart archivesmp-webapi

# Check service status
sudo systemctl status homeamp-agent
sudo systemctl status archivesmp-webapi

# View logs
journalctl -u homeamp-agent -f
journalctl -u archivesmp-webapi -f


# ============================================================================
# FOR DEVELOPMENT (Windows - Local MySQL)
# ============================================================================

# Option 1: PowerShell script (shows commands)
cd d:\homeamp.ampdata\homeamp.ampdata
.\software\homeamp-config-manager\scripts\init_database.ps1

# Option 1b: PowerShell script (actually execute)
.\software\homeamp-config-manager\scripts\init_database.ps1 -Execute

# Option 2: Direct MySQL commands (Windows CMD)
mysql -u root -p -e "DROP DATABASE IF EXISTS asmp_config; CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root -p asmp_config < d:\homeamp.ampdata\homeamp.ampdata\AUTHORITATIVE_SCHEMA.sql

# Option 3: MySQL interactive client
mysql -u root -p
-- Then paste:
DROP DATABASE IF EXISTS asmp_config;
CREATE DATABASE asmp_config CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE asmp_config;
SOURCE d:/homeamp.ampdata/homeamp.ampdata/AUTHORITATIVE_SCHEMA.sql;
SHOW TABLES;
SELECT COUNT(*) FROM meta_tags;  -- Should return 8
EXIT;


# ============================================================================
# VERIFICATION COMMANDS (Both platforms)
# ============================================================================

# Check table count (should be 23)
mysql -u sqlworkerSMP -p asmp_config -e "SHOW TABLES;"

# Verify seed data loaded
mysql -u sqlworkerSMP -p asmp_config -e "SELECT COUNT(*) as tag_count FROM meta_tags;"
mysql -u sqlworkerSMP -p asmp_config -e "SELECT tag_name, display_name FROM meta_tags;"

# Check table structure
mysql -u sqlworkerSMP -p asmp_config -e "DESCRIBE instances;"
mysql -u sqlworkerSMP -p asmp_config -e "DESCRIBE config_variance_cache;"

# Verify foreign keys work
mysql -u sqlworkerSMP -p asmp_config -e "SHOW CREATE TABLE instance_plugins\G"


# ============================================================================
# BACKUP COMMANDS (Run BEFORE reset if you have data to save)
# ============================================================================

# Full database backup
mysqldump -u sqlworkerSMP -p asmp_config > asmp_config_backup_$(date +%Y%m%d_%H%M%S).sql

# Backup specific tables only
mysqldump -u sqlworkerSMP -p asmp_config instances plugins config_rules > essential_data.sql

# Restore from backup
mysql -u sqlworkerSMP -p asmp_config < asmp_config_backup_20251124_123456.sql


# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# If "table doesn't exist" errors occur:
# 1. Check which tables exist:
mysql -u sqlworkerSMP -p asmp_config -e "SHOW TABLES;"

# 2. Compare with expected 23 tables in AUTHORITATIVE_SCHEMA.sql
# 3. If mismatch, re-run initialization

# If foreign key errors:
# - Old data incompatible with new VARCHAR-based schema
# - Solution: Drop database and start fresh (no partial migration possible)

# If services crash after DB reset:
# - Tables are empty, agents need to repopulate
# - Wait for agent discovery cycle (check logs)
# - Manually trigger: systemctl restart homeamp-agent
