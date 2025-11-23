#!/bin/bash
# Deploy database schema to production
# Creates development/testing database (ISOLATED from production)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_FILE="$SCRIPT_DIR/../src/database/schema.sql"

# Source secrets for DB credentials
if [[ -f /etc/archivesmp/secrets.env ]]; then
    source /etc/archivesmp/secrets.env
else
    echo "Error: /etc/archivesmp/secrets.env not found"
    exit 1
fi

echo "Creating database: $DB_NAME..."
mysql -h "${DB_HOST}" -P "${DB_PORT}" -u "$DB_USER" -p"$DB_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME};"

echo "Deploying schema to $DB_NAME..."
mysql -h "${DB_HOST}" -P "${DB_PORT}" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" < "$SCHEMA_FILE"

echo "✓ Database schema deployed"
echo ""
echo "Database: $DB_NAME"
echo "Tables created:"
echo "  - servers"
echo "  - instances"
echo "  - plugins"
echo "  - config_keys"
echo "  - network_defaults"
echo "  - instance_overrides"
echo "  - instance_config_state"
echo "  - drift_log"
echo "  - config_changes"
echo ""
echo "Next step: Run parse_markdown_to_sql.py to populate from baselines"
