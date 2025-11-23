# ============================================================================
# Database Initialization Script for ArchiveSMP Configuration Manager
# Windows PowerShell Version
# ============================================================================
# This script provides commands to drop and recreate the database
# 
# Usage: .\init_database.ps1
#
# Prerequisites:
#   - MySQL/MariaDB client installed and in PATH
#   - User: sqlworkerSMP with password
#   - AUTHORITATIVE_SCHEMA.sql in repository root
# ============================================================================

param(
    [switch]$Execute = $false
)

$DB_USER = "sqlworkerSMP"
$DB_NAME = "asmp_config"
$REPO_ROOT = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
$SCHEMA_FILE = Join-Path $REPO_ROOT "AUTHORITATIVE_SCHEMA.sql"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "ArchiveSMP Config Manager - Database Init" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Database: $DB_NAME"
Write-Host "Schema: $SCHEMA_FILE"
Write-Host ""

# Check if schema file exists
if (-not (Test-Path $SCHEMA_FILE)) {
    Write-Host "❌ ERROR: AUTHORITATIVE_SCHEMA.sql not found at:" -ForegroundColor Red
    Write-Host "   $SCHEMA_FILE" -ForegroundColor Red
    exit 1
}

if (-not $Execute) {
    Write-Host "⚠️  DRY RUN MODE - Commands to execute:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "# Drop and recreate database:" -ForegroundColor Green
    Write-Host "mysql -u $DB_USER -p -e `"DROP DATABASE IF EXISTS $DB_NAME; CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`"" -ForegroundColor White
    Write-Host ""
    Write-Host "# Load schema:" -ForegroundColor Green
    Write-Host "mysql -u $DB_USER -p $DB_NAME < `"$SCHEMA_FILE`"" -ForegroundColor White
    Write-Host ""
    Write-Host "Run with -Execute flag to actually execute these commands." -ForegroundColor Yellow
    exit 0
}

Write-Host "⚠️  WARNING: This will DROP the existing database and recreate it!" -ForegroundColor Yellow
Write-Host "All data will be LOST." -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Host "Aborted."
    exit 0
}

Write-Host ""
Write-Host "🗑️  Dropping existing database..." -ForegroundColor Yellow
& mysql -u $DB_USER -p -e "DROP DATABASE IF EXISTS $DB_NAME;"

Write-Host "📁 Creating fresh database..." -ForegroundColor Green
& mysql -u $DB_USER -p -e "CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

Write-Host "📋 Loading AUTHORITATIVE_SCHEMA.sql..." -ForegroundColor Green
Get-Content $SCHEMA_FILE | & mysql -u $DB_USER -p $DB_NAME

Write-Host ""
Write-Host "✅ Database initialized successfully!" -ForegroundColor Green
Write-Host ""
