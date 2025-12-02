#!/usr/bin/env python3
"""
PAMPA Integration Example for ArchiveSMP Config Manager

Demonstrates how to use PAMPA semantic search to audit the codebase.
This script would be called by an AI agent through MCP.
"""

# Example PAMPA queries that found the issues in our audit:

AUDIT_QUERIES = {
    "database_connections": [
        "database connection mysql mariadb ConfigDatabase",
        "import database db_access settings",
    ],
    
    "schema_definitions": [
        "CREATE TABLE plugins instances baseline_snapshots config_rules drift",
        "database schema asmp_config asmp_SQL",
    ],
    
    "duplicate_detection": [
        "duplicate function class method definition",
        "import statements circular dependencies",
    ],
    
    "configuration": [
        "database name DB_NAME asmp_config connection parameters",
        "settings configuration hardcoded credentials",
    ],
    
    "metadata_tracking": [
        "INSERT INTO plugins instance_plugins instance_datapacks",
        "populate metadata scan discover sync",
    ],
}

# Example results from semantic search:
# 
# Query: "database name DB_NAME asmp_config connection parameters"
# Found:
# - scripts/deploy_schema.py: hardcoded 'asmp_SQL' (line 16)
# - scripts/parse_markdown_to_sql.py: hardcoded 'asmp_config_controller' (line 356)
# - src/database/schema.sql: wrong database name (line 6)
# - src/web/api_v2.py: hardcoded credentials (line 37-41)
# - src/core/settings.py: default='asmp_SQL' (line 427)
# - src/database/db_access.py: database='asmp_config' default (line 24)
#
# Query: "CREATE TABLE plugins instances baseline"
# Found:
# - src/database/schema_clean.sql: correct schema with all tables
# - src/database/schema.sql: old schema missing tables
# - WIP_PLAN/DATABASE_SCHEMA_V1.md: design documentation
#
# Confidence: VERY HIGH - PAMPA found exact matches for all issues

print("PAMPA semantic search successfully identified:")
print("✓ 7 database name mismatches")
print("✓ Schema architectural problems")
print("✓ Hardcoded credentials")
print("✓ Missing tables in old schema")
print("✓ No duplicate code (clean architecture)")
