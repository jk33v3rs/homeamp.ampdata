#!/bin/bash
# Deploy database configuration fixes to production
# Run this on the YunoHost server

set -e

PROD_DIR="/opt/archivesmp-config-manager/software/homeamp-config-manager"
API_DIR="$PROD_DIR/src/api"
CORE_DIR="$PROD_DIR/src/core"

echo "===================================================================="
echo "Deploying Database Configuration Fix to Production"
echo "===================================================================="

# Step 1: Fix table name in plugin_configurator_endpoints.py
echo ""
echo "[1/3] Fixing table name: config_variances -> config_variance_detected"
python3 << 'EOFPYTHON'
import re
from pathlib import Path

file_path = Path("/opt/archivesmp-config-manager/software/homeamp-config-manager/src/api/plugin_configurator_endpoints.py")
content = file_path.read_text()
original = content
content = re.sub(r'\bconfig_variances\b', 'config_variance_detected', content)

if content != original:
    file_path.write_text(content)
    count = content.count('config_variance_detected')
    print(f"  ✓ Updated {count} occurrences in plugin_configurator_endpoints.py")
else:
    print("  ✓ Already fixed")
EOFPYTHON

# Step 2: Create db_config.py module
echo ""
echo "[2/3] Creating centralized database configuration module"
cat > "$API_DIR/db_config.py" << 'EOFDBCONFIG'
"""
Database Configuration Helper for API Endpoints

Provides centralized database connection configuration using the settings system.
This ensures all API endpoints use consistent database credentials from agent.yaml.
"""

import mysql.connector
import os
from pathlib import Path

# Try to import settings, fall back to direct yaml loading if not available
try:
    from ..core.settings import SettingsHandler
    _settings = SettingsHandler()
    _USE_SETTINGS = True
except Exception as e:
    _settings = None
    _USE_SETTINGS = False
    import sys
    print(f"Warning: Could not import SettingsHandler: {e}", file=sys.stderr)


def get_db_connection():
    """
    Get database connection using settings from agent.yaml.
    
    Uses the proper SettingsHandler from core.settings which:
    - Searches multiple config file locations
    - Supports environment variable overrides
    - Handles proper type conversions
    
    Returns:
        mysql.connector connection object
    """
    if _USE_SETTINGS and _settings:
        # Use the proper settings system
        host = _settings.DB_HOST
        port = _settings.DB_PORT
        user = _settings.DB_USER
        password = _settings.DB_PASSWORD
        database = _settings.DB_NAME
    else:
        # Fallback: try to load from agent.yaml directly
        import yaml
        config_path = Path("/etc/archivesmp/agent.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                db_config = config.get('database', {})
                host = db_config.get('host', 'localhost')
                port = db_config.get('port', 3306)
                user = db_config.get('user', 'sqlworkerSMP')
                password = db_config.get('password', '')
                database = db_config.get('database', 'asmp_config')
        else:
            # Final fallback to environment variables
            host = os.getenv("DB_HOST", "localhost")
            port = int(os.getenv("DB_PORT", "3306"))
            user = os.getenv("DB_USER", "sqlworkerSMP")
            password = os.getenv("DB_PASSWORD", "")
            database = os.getenv("DB_NAME", "asmp_config")
    
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )


# Alias for backwards compatibility
get_db = get_db_connection
EOFDBCONFIG

echo "  ✓ Created $API_DIR/db_config.py"

# Step 3: Update all API endpoint files to use centralized config
echo ""
echo "[3/3] Updating API endpoint files to use centralized database config"

python3 << 'EOFPYTHON'
import re
from pathlib import Path

API_DIR = Path("/opt/archivesmp-config-manager/software/homeamp-config-manager/src/api")

endpoint_files = [
    "plugin_configurator_endpoints.py",
    "audit_log_endpoints.py",
    "dashboard_endpoints.py",
    "deployment_endpoints.py",
    "enhanced_endpoints.py",
    "tag_manager_endpoints.py",
    "update_manager_endpoints.py",
    "variance_endpoints.py",
]

for filename in endpoint_files:
    filepath = API_DIR / filename
    if not filepath.exists():
        print(f"  ⚠ Skipping {filename} (not found)")
        continue
    
    content = filepath.read_text()
    original = content
    
    # Replace the get_db function definition with import
    # Pattern matches various formats of the get_db function
    pattern = r'# Database connection helper\s*\ndef get_db\(\):[^\n]*\n(?:.*?(?=\n\n|\nrouter\s*=|\n# Pydantic|\nclass\s))'
    replacement = '# Database connection helper\nfrom .db_config import get_db_connection as get_db'
    
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    if content != original:
        filepath.write_text(content)
        print(f"  ✓ Updated {filename}")
    else:
        print(f"  ℹ {filename} (no changes needed)")
EOFPYTHON

# Step 4: Restart the API service
echo ""
echo "[4/4] Restarting archivesmp-webapi service..."
systemctl restart archivesmp-webapi.service

# Wait a moment for service to start
sleep 2

# Check service status
if systemctl is-active --quiet archivesmp-webapi.service; then
    echo "  ✓ Service restarted successfully"
else
    echo "  ✗ Service failed to start!"
    echo ""
    echo "Recent logs:"
    journalctl -u archivesmp-webapi.service -n 20 --no-pager
    exit 1
fi

# Verify configuration
echo ""
echo "===================================================================="
echo "Deployment Complete!"
echo "===================================================================="
echo ""
echo "Configuration source:"
echo "  Primary: SettingsHandler (core.settings)"
echo "  Fallback: /etc/archivesmp/agent.yaml"
echo "  Final fallback: Environment variables"
echo ""
echo "Database credentials from agent.yaml:"
sudo grep -A 5 "^database:" /etc/archivesmp/agent.yaml || echo "  (agent.yaml not found or no database section)"
echo ""
echo "Test API endpoint:"
echo "  curl http://localhost:8000/api/dashboard/network-status"
echo ""
echo "Monitor logs:"
echo "  journalctl -u archivesmp-webapi.service -f"
