#!/bin/bash
# Deploy Phase 0: Database Schema & Agent Enhancement
# Run this on Hetzner server (135.181.212.169) as root

set -e  # Exit on error

echo "============================================="
echo "Phase 0 Deployment: Database Schema & Agent"
echo "============================================="
echo ""

# Database credentials
DB_USER="sqlworkerSMP"
DB_PASS="SQLdb2024!"
DB_HOST="135.181.212.169"
DB_PORT="3369"
DB_NAME="asmp_config"

REPO_DIR="/opt/archivesmp-config-manager"
VENV_DIR="$REPO_DIR/venv"

echo "[1/6] Creating new database tables..."
mysql -u $DB_USER -p"$DB_PASS" -h $DB_HOST -P $DB_PORT $DB_NAME < $REPO_DIR/scripts/create_new_tables.sql
echo "✓ Database tables created"
echo ""

echo "[2/6] Verifying table creation..."
mysql -u $DB_USER -p"$DB_PASS" -h $DB_HOST -P $DB_PORT $DB_NAME -e "
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = '$DB_NAME' 
AND table_name IN (
    'deployment_queue', 'deployment_logs', 'plugin_update_sources', 
    'plugin_versions', 'meta_tags', 'tag_instances', 'tag_hierarchy',
    'config_variances', 'server_properties_baselines', 'server_properties_variances',
    'datapacks', 'datapack_update_sources', 'config_history', 'audit_log', 'agent_heartbeats'
)
ORDER BY table_name;
"
echo "✓ Tables verified"
echo ""

echo "[3/6] Deploying agent enhancement files..."
# Variance Detector
if [ -f "$REPO_DIR/src/agent/variance_detector.py" ]; then
    echo "  ✓ variance_detector.py already in place"
else
    echo "  ⚠ variance_detector.py not found - ensure it's been committed to repo"
fi

# Server Properties Scanner
if [ -f "$REPO_DIR/src/agent/server_properties_scanner.py" ]; then
    echo "  ✓ server_properties_scanner.py already in place"
else
    echo "  ⚠ server_properties_scanner.py not found - ensure it's been committed to repo"
fi

# Datapack Discovery
if [ -f "$REPO_DIR/src/agent/datapack_discovery.py" ]; then
    echo "  ✓ datapack_discovery.py already in place"
else
    echo "  ⚠ datapack_discovery.py not found - ensure it's been committed to repo"
fi

# Enhanced Discovery Integration
if [ -f "$REPO_DIR/src/agent/enhanced_discovery.py" ]; then
    echo "  ✓ enhanced_discovery.py already in place"
else
    echo "  ⚠ enhanced_discovery.py not found - ensure it's been committed to repo"
fi

# Enhanced API Endpoints
if [ -f "$REPO_DIR/src/api/enhanced_endpoints.py" ]; then
    echo "  ✓ enhanced_endpoints.py already in place"
else
    echo "  ⚠ enhanced_endpoints.py not found - ensure it's been committed to repo"
fi
echo ""

echo "[4/6] Restarting homeamp-agent service..."
systemctl restart homeamp-agent.service
sleep 2
systemctl status homeamp-agent.service --no-pager
echo "✓ Agent restarted"
echo ""

echo "[5/6] Running enhanced discovery..."
cd $REPO_DIR
sudo -u amp $VENV_DIR/bin/python scripts/run_enhanced_discovery.py
echo "✓ Discovery complete"
echo ""

echo "[6/6] Verification - Checking populated tables..."
mysql -u $DB_USER -p"$DB_PASS" -h $DB_HOST -P $DB_PORT $DB_NAME -e "
SELECT 
    'config_variances' AS table_name, COUNT(*) AS row_count 
FROM config_variances
UNION ALL
SELECT 
    'server_properties_variances', COUNT(*) 
FROM server_properties_variances
UNION ALL
SELECT 
    'datapacks', COUNT(*) 
FROM datapacks;
"
echo ""

echo "============================================="
echo "Phase 0 Deployment Complete!"
echo "============================================="
echo ""
echo "Next steps:"
echo "  1. Verify row counts above meet expectations"
echo "  2. Check agent logs: journalctl -u homeamp-agent -f"
echo "  3. Test API endpoints: curl http://localhost:8000/api/plugins"
echo ""
