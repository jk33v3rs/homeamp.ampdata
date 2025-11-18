#!/bin/bash
# Deploy tracking and history tables on production server
# Run this on Hetzner: bash /tmp/deploy_tracking.sh

set -e

echo "=============================================================================="
echo "DEPLOYING TRACKING & HISTORY TABLES"
echo "=============================================================================="

SQL_FILE="/tmp/add_tracking_history_tables.sql"

if [ ! -f "$SQL_FILE" ]; then
    echo "❌ SQL file not found: $SQL_FILE"
    echo "Please upload add_tracking_history_tables.sql to /tmp/ first"
    exit 1
fi

echo ""
echo "📄 SQL file found: $SQL_FILE"
echo "🔌 Connecting to MariaDB on localhost..."

# Execute SQL
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' asmp_config < "$SQL_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SQL executed successfully"
else
    echo ""
    echo "❌ SQL execution failed"
    exit 1
fi

echo ""
echo "=============================================================================="
echo "VERIFYING TABLES"
echo "=============================================================================="

# Verify tables were created
mysql -h 135.181.212.169 -P 3369 -u sqlworkerSMP -p'2024!SQLdb' asmp_config -e "
SELECT 
    table_name,
    table_rows,
    ROUND(data_length/1024/1024, 2) AS size_mb,
    ROUND(index_length/1024/1024, 2) AS index_mb
FROM information_schema.tables
WHERE table_schema = 'asmp_config'
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
)
ORDER BY table_name;
"

echo ""
echo "=============================================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=============================================================================="
echo ""
echo "Next steps:"
echo "1. Run populate_known_migrations.py to add initial migration data"
echo "2. Update config_updater.py to use database logging"
echo "3. Restart archivesmp-webapi.service"
echo ""
