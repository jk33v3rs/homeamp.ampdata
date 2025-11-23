#!/bin/bash
# ============================================================================
# Database Initialization Script for ArchiveSMP Configuration Manager
# ============================================================================
# This script drops and recreates the database from AUTHORITATIVE_SCHEMA.sql
# 
# Usage:
#   Local Dev (Windows):     Run commands manually in MySQL client
#   Production (Debian 12):  bash init_database.sh
#
# Prerequisites:
#   - MariaDB running locally
#   - User: sqlworkerSMP with password
#   - AUTHORITATIVE_SCHEMA.sql in repository root
# ============================================================================

set -e  # Exit on error

# Database configuration
DB_USER="sqlworkerSMP"
DB_NAME="asmp_config"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../" && pwd)"
SCHEMA_FILE="$REPO_ROOT/AUTHORITATIVE_SCHEMA.sql"

echo "=================================================="
echo "ArchiveSMP Config Manager - Database Init"
echo "=================================================="
echo "Database: $DB_NAME"
echo "Schema: $SCHEMA_FILE"
echo ""

# Check if schema file exists
if [ ! -f "$SCHEMA_FILE" ]; then
    echo "❌ ERROR: AUTHORITATIVE_SCHEMA.sql not found at:"
    echo "   $SCHEMA_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will DROP the existing database and recreate it!"
echo "All data will be LOST."
echo ""
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "🗑️  Dropping existing database..."
mysql -u "$DB_USER" -p -e "DROP DATABASE IF EXISTS $DB_NAME;"

echo "📁 Creating fresh database..."
mysql -u "$DB_USER" -p -e "CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

echo "📋 Loading AUTHORITATIVE_SCHEMA.sql..."
mysql -u "$DB_USER" -p "$DB_NAME" < "$SCHEMA_FILE"

echo ""
echo "✅ Database initialized successfully!"
echo ""
echo "Next steps:"
echo "  1. Restart the agent: sudo systemctl restart homeamp-agent"
echo "  2. Restart the API: sudo systemctl restart archivesmp-webapi"
echo "  3. Check logs: journalctl -u homeamp-agent -f"
echo ""
