#!/usr/bin/env python3
"""
Deploy database configuration fixes to production

This script:
1. Fixes the table name from config_variances to config_variance_detected
2. Copies the new centralized db_config.py module
3. Updates all API endpoint files to use centralized config
4. Restarts the API service
"""

import sys
import subprocess
from pathlib import Path

# Production paths
PROD_API_DIR = Path("/opt/archivesmp-config-manager/software/homeamp-config-manager/src/api")
SERVICE_NAME = "archivesmp-webapi.service"

# Files to update on production
FILES_TO_UPDATE = {
    "db_config.py": """\"\"\"Database Configuration Helper for API Endpoints\"\"\"
import mysql.connector
import yaml
from pathlib import Path

def _load_agent_config():
    config_locations = [
        Path("/etc/archivesmp/agent.yaml"),
        Path(__file__).parent.parent.parent / "config" / "agent.yaml",
    ]
    for config_path in config_locations:
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
    return {}

def get_db_connection():
    config = _load_agent_config()
    db_config = config.get('database', {})
    
    host = db_config.get('host', 'localhost')
    port = db_config.get('port', 3306)
    user = db_config.get('user', 'sqlworkerSMP')
    password = db_config.get('password', '')
    database = db_config.get('database', 'asmp_config')
    
    return mysql.connector.connect(
        host=host, port=port, user=user, password=password, database=database
    )

get_db = get_db_connection
""",
}

def run_command(cmd, description):
    """Run a shell command and check result"""
    print(f"[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[!] Error: {result.stderr}")
            return False
        if result.stdout:
            print(f"    {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"[!] Exception: {e}")
        return False

def main():
    print("=" * 60)
    print("Deploying database configuration fixes to production")
    print("=" * 60)
    
    # Step 1: Create db_config.py
    print("\n[1/4] Creating centralized database configuration module...")
    db_config_path = PROD_API_DIR / "db_config.py"
    try:
        with open(db_config_path, 'w') as f:
            f.write(FILES_TO_UPDATE["db_config.py"])
        print(f"    Created: {db_config_path}")
    except Exception as e:
        print(f"[!] Failed to create db_config.py: {e}")
        return 1
    
    # Step 2: Fix table name in plugin_configurator_endpoints.py
    print("\n[2/4] Fixing table name config_variances -> config_variance_detected...")
    plugin_endpoints = PROD_API_DIR / "plugin_configurator_endpoints.py"
    try:
        with open(plugin_endpoints, 'r') as f:
            content = f.read()
        
        # Replace table name
        import re
        content = re.sub(r'\bconfig_variances\b', 'config_variance_detected', content)
        
        with open(plugin_endpoints, 'w') as f:
            f.write(content)
        
        count = content.count('config_variance_detected')
        print(f"    Updated {count} occurrences of table name")
    except Exception as e:
        print(f"[!] Failed to fix table name: {e}")
        return 1
    
    # Step 3: Update import statements in all endpoint files
    print("\n[3/4] Updating API endpoint files to use centralized config...")
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
        filepath = PROD_API_DIR / filename
        if not filepath.exists():
            print(f"    Skipping {filename} (not found)")
            continue
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Replace the get_db function definition with import
            old_pattern = r'# Database connection helper\s*\ndef get_db\(\):.*?(?=\n\n|\nrouter|\n# Pydantic)'
            new_text = '# Database connection helper\nfrom .db_config import get_db_connection as get_db'
            
            import re
            content = re.sub(old_pattern, new_text, content, flags=re.DOTALL)
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"    Updated {filename}")
        except Exception as e:
            print(f"    Warning: Failed to update {filename}: {e}")
    
    # Step 4: Restart API service
    print("\n[4/4] Restarting API service...")
    if not run_command(f"systemctl restart {SERVICE_NAME}", "Restarting service"):
        return 1
    
    # Check service status
    if not run_command(f"systemctl is-active {SERVICE_NAME}", "Checking service status"):
        print("[!] Service may not be running properly")
        run_command(f"journalctl -u {SERVICE_NAME} -n 20 --no-pager", "Recent service logs")
        return 1
    
    print("\n" + "=" * 60)
    print("Deployment completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Test API endpoints:")
    print("   curl http://localhost:8000/api/dashboard/network-status")
    print("2. Check logs if needed:")
    print(f"   journalctl -u {SERVICE_NAME} -f")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
