#!/bin/bash
# Master Migration Script - Run All Database Migrations
# Purpose: Execute all migrations in order for the 7-level hierarchy system
# Author: AI Assistant
# Date: 2025-11-18
# Usage: ./run_migrations.sh [mysql_host] [mysql_port] [mysql_user] [mysql_password] [database]

# =============================================================================
# Configuration
# =============================================================================
MYSQL_HOST="${1:-135.181.212.169}"
MYSQL_PORT="${2:-3369}"
MYSQL_USER="${3:-sqlworkerSMP}"
MYSQL_PASSWORD="${4:-SQLdb2024!}"
DATABASE="${5:-archivesmp_config}"

MIGRATIONS_DIR="$(dirname "$0")/migrations"
LOG_FILE="migration_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Functions
# =============================================================================
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

run_migration() {
    local migration_file="$1"
    local migration_name=$(basename "$migration_file")
    
    log "Running migration: $migration_name"
    
    if mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$DATABASE" < "$migration_file" 2>>"$LOG_FILE"; then
        success "Migration completed: $migration_name"
        return 0
    else
        error "Migration failed: $migration_name"
        return 1
    fi
}

# =============================================================================
# Pre-flight checks
# =============================================================================
log "Starting database migration process"
log "Target: $MYSQL_USER@$MYSQL_HOST:$MYSQL_PORT/$DATABASE"

# Check if mysql client is available
if ! command -v mysql &> /dev/null; then
    error "mysql client not found. Please install mysql-client package."
    exit 1
fi

# Test database connection
log "Testing database connection..."
if mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1;" "$DATABASE" &>/dev/null; then
    success "Database connection successful"
else
    error "Cannot connect to database. Check credentials and network access."
    exit 1
fi

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    error "Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

# =============================================================================
# Run migrations in order
# =============================================================================
log "Found migrations directory: $MIGRATIONS_DIR"

# Get sorted list of migration files
MIGRATIONS=$(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort)

if [ -z "$MIGRATIONS" ]; then
    warning "No migration files found in $MIGRATIONS_DIR"
    exit 0
fi

MIGRATION_COUNT=$(echo "$MIGRATIONS" | wc -l)
log "Found $MIGRATION_COUNT migration(s) to execute"

# Execute each migration
FAILED_COUNT=0
SUCCESS_COUNT=0

for migration_file in $MIGRATIONS; do
    if run_migration "$migration_file"; then
        ((SUCCESS_COUNT++))
    else
        ((FAILED_COUNT++))
        error "Migration failed. Stopping execution."
        break
    fi
done

# =============================================================================
# Summary
# =============================================================================
echo ""
log "========================================="
log "Migration Summary"
log "========================================="
log "Total migrations: $MIGRATION_COUNT"
success "Successful: $SUCCESS_COUNT"

if [ $FAILED_COUNT -gt 0 ]; then
    error "Failed: $FAILED_COUNT"
    log "Check log file for details: $LOG_FILE"
    exit 1
else
    success "All migrations completed successfully!"
    log "Log file: $LOG_FILE"
    exit 0
fi

# =============================================================================
# Verification
# =============================================================================
log ""
log "Running post-migration verification..."

# Check table counts
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$DATABASE" << 'EOF' 2>/dev/null
SELECT 
    'meta_tags' as table_name, COUNT(*) as row_count FROM meta_tags
UNION ALL
SELECT 'instance_meta_tags', COUNT(*) FROM instance_meta_tags
UNION ALL
SELECT 'config_rules', COUNT(*) FROM config_rules
UNION ALL
SELECT 'worlds', COUNT(*) FROM worlds
UNION ALL
SELECT 'ranks', COUNT(*) FROM ranks
UNION ALL
SELECT 'config_backups', COUNT(*) FROM config_backups;
EOF

success "Verification complete"
