#!/bin/bash
# Deploy database schema to production
# Creates asmp_config database (ISOLATED from production AMP databases)

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

echo "Creating asmp_config database..."
mysql -h 135.181.212.169 -P 3369 -u "$DB_USER" -p"$DB_PASSWORD" < "$SCHEMA_FILE"

echo "✓ Database schema deployed"
echo ""
echo "Database: asmp_config"
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
