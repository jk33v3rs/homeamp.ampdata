#!/bin/bash
# ============================================================================
# Deploy Clean Schema to Production
# ============================================================================
# WARNING: This will DROP the existing asmp_config database!
# Make sure you have a backup if needed.
# ============================================================================

set -e  # Exit on error

DB_HOST="${DB_HOST:-135.181.212.169}"
DB_PORT="${DB_PORT:-3369}"
DB_USER="${DB_USER:-sqlworkerSMP}"
DB_PASS="${DB_PASS:-2024!SQLdb}"

echo "========================================"
echo "ARCHIVESMP CLEAN SCHEMA DEPLOYMENT"
echo "========================================"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo ""
echo "WARNING: This will DROP and recreate asmp_config database!"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

echo ""
echo "[1/4] Deploying clean schema..."
mariadb -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" < CLEAN_SCHEMA.sql

echo ""
echo "[2/4] Verifying tables..."
mariadb -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" asmp_config -e "SHOW TABLES;"

echo ""
echo "[3/4] Checking table sizes..."
mariadb -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" asmp_config -e "
SELECT 
    table_name,
    table_rows,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'asmp_config'
ORDER BY table_name;
"

echo ""
echo "[4/4] Done! Database is clean and ready."
echo ""
echo "Next steps:"
echo "1. Update /etc/archivesmp/agent.yaml with correct credentials"
echo "2. Restart agent: sudo systemctl restart homeamp-agent"
echo "3. Restart web API: sudo systemctl restart archivesmp-webapi"
echo "4. Agent will auto-discover and populate tables"
echo ""
