#!/bin/bash
################################################################################
# Verify Option C Tracking System Deployment
# Quick health check after deployment
################################################################################

echo "================================================================================"
echo "DEPLOYMENT VERIFICATION"
echo "================================================================================"
echo ""

DB_HOST="135.181.212.169"
DB_PORT="3369"
DB_USER="sqlworkerSMP"
DB_PASS="2024!SQLdb"
DB_NAME="asmp_config"
API_URL="http://localhost:8000"

# 1. Check database tables
echo "📊 Checking database tables..."
TABLES=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -se "
SELECT GROUP_CONCAT(table_name ORDER BY table_name SEPARATOR ', ')
FROM information_schema.tables 
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

TABLE_COUNT=$(echo "$TABLES" | tr ',' '\n' | wc -l)
if [ "$TABLE_COUNT" -eq 11 ]; then
    echo "✅ All 11 tables present"
else
    echo "⚠️  Only $TABLE_COUNT/11 tables found: $TABLES"
fi
echo ""

# 2. Check migrations data
echo "📋 Checking migration data..."
MIGRATION_COUNT=$(mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -se "
SELECT COUNT(*) FROM config_key_migrations")
echo "✅ $MIGRATION_COUNT migrations in database"
echo ""

# 3. Check service status
echo "🔍 Checking service status..."
if sudo systemctl is-active --quiet archivesmp-webapi.service; then
    echo "✅ archivesmp-webapi.service is running"
    
    # Get uptime
    UPTIME=$(sudo systemctl show archivesmp-webapi.service -p ActiveEnterTimestamp --value)
    echo "   Started: $UPTIME"
else
    echo "❌ archivesmp-webapi.service is NOT running"
fi
echo ""

# 4. Check API endpoints
echo "🧪 Testing API endpoints..."

# Test each endpoint
ENDPOINTS=(
    "/api/migrations"
    "/api/history/changes"
    "/api/history/deployments"
    "/api/stats/changes"
)

ALL_OK=true
for ENDPOINT in "${ENDPOINTS[@]}"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL$ENDPOINT")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ $ENDPOINT - HTTP $HTTP_CODE"
    else
        echo "❌ $ENDPOINT - HTTP $HTTP_CODE"
        ALL_OK=false
    fi
done
echo ""

# 5. Check recent logs for errors
echo "📝 Checking recent logs..."
ERROR_COUNT=$(sudo journalctl -u archivesmp-webapi.service --since "5 minutes ago" | grep -i error | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo "✅ No errors in last 5 minutes"
else
    echo "⚠️  $ERROR_COUNT errors in last 5 minutes:"
    sudo journalctl -u archivesmp-webapi.service --since "5 minutes ago" | grep -i error | tail -5
fi
echo ""

# Summary
echo "================================================================================"
if [ "$TABLE_COUNT" -eq 11 ] && [ "$MIGRATION_COUNT" -gt 0 ] && $ALL_OK; then
    echo "✅ DEPLOYMENT VERIFIED - All systems operational!"
else
    echo "⚠️  DEPLOYMENT INCOMPLETE - See warnings above"
fi
echo "================================================================================"
echo ""
