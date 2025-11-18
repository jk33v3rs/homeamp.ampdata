#!/bin/bash
################################################################################
# Deploy Option C Tracking System to Hetzner Production
# Run this script on Hetzner server after git pull
################################################################################

set -e  # Exit on any error

echo "================================================================================"
echo "DEPLOYING OPTION C TRACKING SYSTEM"
echo "================================================================================"
echo ""

# Fix git permissions if needed
if [ ! -w .git/FETCH_HEAD ] 2>/dev/null; then
    echo "🔧 Fixing git permissions..."
    sudo chown -R $USER:$USER .git/
    sudo chmod -R u+rwX .git/
    echo "✅ Permissions fixed"
    echo ""
fi

# Database connection details
DB_HOST="135.181.212.169"
DB_PORT="3369"
DB_USER="sqlworkerSMP"
DB_PASS="2024!SQLdb"
DB_NAME="asmp_config"

# Step 1: Verify we're in the right directory
echo "📂 Step 1: Verifying location..."
if [ ! -f "scripts/add_tracking_history_tables.sql" ]; then
    echo "❌ ERROR: Must run from /opt/archivesmp-config-manager/"
    exit 1
fi
echo "✅ In correct directory"
echo ""

# Step 2: Deploy database tables
echo "📊 Step 2: Creating 11 tracking tables..."
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" < scripts/add_tracking_history_tables.sql
echo "✅ Tables created"
echo ""

# Step 3: Verify tables exist
echo "🔍 Step 3: Verifying tables..."
TABLE_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -se "
SELECT COUNT(*) FROM information_schema.tables 
WHERE table_schema = '$DB_NAME' 
AND table_name IN (
    'config_key_migrations',
    'config_change_history',
    'deployment_history',
    'deployment_changes',
    'config_rule_history',
    'config_variance_history',
    'plugin_installation_history',
    'change_approval_requests',
    'notification_log',
    'scheduled_tasks',
    'system_health_metrics'
)")

if [ "$TABLE_COUNT" -eq 11 ]; then
    echo "✅ All 11 tables verified"
else
    echo "⚠️  Warning: Only $TABLE_COUNT/11 tables found"
fi
echo ""

# Step 4: Install Python dependencies
echo "🐍 Step 4: Installing Python dependencies..."
pip3 install -q mysql-connector-python
echo "✅ Dependencies installed"
echo ""

# Step 5: Populate known migrations
echo "📋 Step 5: Populating known migrations..."
cd scripts
python3 populate_known_migrations.py
cd ..
echo ""

# Step 6: Restart web API service
echo "🔄 Step 6: Restarting web API service..."
sudo systemctl restart archivesmp-webapi.service
sleep 2
echo "✅ Service restarted"
echo ""

# Step 7: Check service status
echo "🔍 Step 7: Checking service status..."
if sudo systemctl is-active --quiet archivesmp-webapi.service; then
    echo "✅ Service is running"
else
    echo "❌ Service failed to start!"
    echo "Logs:"
    sudo journalctl -u archivesmp-webapi.service -n 20 --no-pager
    exit 1
fi
echo ""

# Step 8: Test API endpoints
echo "🧪 Step 8: Testing API endpoints..."
API_URL="http://localhost:8000"

# Test migrations endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/migrations")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ /api/migrations - OK"
else
    echo "❌ /api/migrations - HTTP $HTTP_CODE"
fi

# Test change history endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/history/changes")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ /api/history/changes - OK"
else
    echo "❌ /api/history/changes - HTTP $HTTP_CODE"
fi

# Test deployments endpoint
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/history/deployments")
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ /api/history/deployments - OK"
else
    echo "❌ /api/history/deployments - HTTP $HTTP_CODE"
fi

echo ""
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Test migration script: python3 scripts/apply_config_migrations.py --help"
echo "  2. View change history: curl $API_URL/api/history/changes | jq"
echo "  3. View migrations: curl $API_URL/api/migrations | jq"
echo ""
