# ArchiveSMP Configuration Manager - Database Schema Deployment Summary

**Date**: November 16, 2025  
**Status**: Ready for Production Deployment

## What Was Built

### 1. Database Schema (MariaDB)
- **Database**: `asmp_config` on Hetzner (135.181.212.169:3369)
- **Tables**: 22 tables with 54 indexes
- **Hierarchy**: 10-level priority system (PLAYER_OVERRIDE → GLOBAL)
- **Features**: Meta-grouping, config variables, variance tracking

### 2. Data Populated
- ✅ 6 meta-tag categories (gameplay, modding, intensity, economy, combat, persistence)
- ✅ 23 system meta-tags
- ✅ 19 instances (11 on OVH, 8 on Hetzner)
- ✅ 8 instance groups (physical/logical/administrative)
- ✅ All group memberships assigned

### 3. Software Components

#### Database Access Layer (`src/database/db_access.py`)
- Connection management
- Instance queries
- Config hierarchy resolution
- Variable substitution
- Variance reporting

#### Endpoint Agent (`src/agent/endpoint_agent.py`)
- Discovers local AMP instances
- Scans plugin configurations
- Detects configuration drift
- Reports to central database
- Runs as systemd service on each server

#### Web API v2 (`src/web/api_v2.py`)
- FastAPI REST endpoints
- Database-backed queries
- Instance management
- Config resolution
- Variance reporting
- Serves web GUI (future)

#### Supporting Modules
- `src/amp_integration/instance_scanner.py` - Discovers instances
- `src/analyzers/config_reader.py` - Reads YAML configs

### 4. Deployment Tools

#### Systemd Services
- `archivesmp-endpoint-agent.service` - Agent on each server
- `archivesmp-webapi.service` - Web API on Hetzner only

#### Deployment Scripts
- `deployment/deploy_hetzner.sh` - Full deployment (agent + web API)
- `deployment/deploy_ovh.sh` - Agent only
- `deployment/QUICKSTART.md` - Quick reference commands
- `deployment/AGENT_DEPLOYMENT.md` - Detailed deployment guide

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Hetzner Server (135.181.212.169)                            │
│                                                              │
│  MariaDB (port 3369)                                         │
│  └── asmp_config database                                   │
│      ├── 19 instances                                        │
│      ├── 8 instance groups                                   │
│      ├── 23 meta tags                                        │
│      └── Config rules (to be populated from baselines)      │
│                                                              │
│  Endpoint Agent (systemd)                                    │
│  └── Scans 8 local instances                                │
│      └── Reports drift to database                          │
│                                                              │
│  Web API (systemd, port 8000)                                │
│  └── REST endpoints for GUI                                 │
│      └── Database queries                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ OVH Server (37.187.143.41)                                   │
│                                                              │
│  Endpoint Agent (systemd)                                    │
│  └── Scans 11 local instances                               │
│      └── Reports drift to database on Hetzner              │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Commands

### Quick Deploy

```bash
# Hetzner (as amp user)
ssh amp@135.181.212.169
curl -sSL https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/deploy_hetzner.sh | bash

# OVH (as amp user)
ssh amp@37.187.143.41
curl -sSL https://raw.githubusercontent.com/jk33v3rs/homeamp.ampdata/master/software/homeamp-config-manager/deployment/deploy_ovh.sh | bash
```

### Start Services

```bash
# On both servers
sudo systemctl enable archivesmp-endpoint-agent.service
sudo systemctl start archivesmp-endpoint-agent.service

# On Hetzner only
sudo systemctl enable archivesmp-webapi.service
sudo systemctl start archivesmp-webapi.service
```

## What's Next

### Remaining Tasks

1. **Parse Baseline Configs** (`data/baselines/universal_configs/*.md`)
   - Extract global config rules
   - Populate `config_rules` table
   - Define config variables

2. **Initial Variance Analysis**
   - Run agents to scan production configs
   - Compare against baseline rules
   - Generate drift report
   - Populate `config_variance_cache`

3. **Web GUI Development**
   - React components for config editor
   - Variance highlighting (green/blue/pink/red)
   - Bulk operations interface
   - Rule builder with meta-tag logic

4. **Advanced Features**
   - GUI builders (Jobs, Quests, Worth, LuckPerms, Commands)
   - Scheduled config changes (time constraints)
   - Automated drift remediation
   - Change approval workflow

## Files Created This Session

### Database
- `WIP_PLAN/DATABASE_SCHEMA_V1.md` - Complete schema documentation
- `scripts/create_database_schema.sql` - DDL for 22 tables
- `scripts/deploy_schema.py` - Python deployment script
- `scripts/seed_meta_tags.sql` - Meta-tag seed data
- `scripts/seed_instances.sql` - Instance seed data (SQL)
- `scripts/deploy_instances.py` - Instance deployment (Python)
- `scripts/seed_instance_groups.sql` - Group seed data (SQL)
- `scripts/deploy_instance_groups.py` - Group deployment (Python)

### Software
- `src/database/db_access.py` - Database access layer
- `src/agent/endpoint_agent.py` - Lightweight endpoint agent
- `src/web/api_v2.py` - Database-backed web API
- `src/amp_integration/instance_scanner.py` - Instance discovery
- `src/analyzers/config_reader.py` - Config file reader

### Deployment
- `deployment/archivesmp-endpoint-agent.service` - Systemd service
- `deployment/deploy_hetzner.sh` - Hetzner deployment script
- `deployment/deploy_ovh.sh` - OVH deployment script
- `deployment/QUICKSTART.md` - Quick deployment reference
- `deployment/AGENT_DEPLOYMENT.md` - Detailed deployment guide

## Database State

- **Host**: 135.181.212.169:3369
- **Database**: asmp_config
- **User**: sqlworkerSMP / SQLdb2024!
- **Access**: Remote connections allowed from any host
- **Tables**: 22 created with proper indexes
- **Data**: Meta-tags, instances, and groups populated

## Ready for Production

All code is tested locally and ready to deploy to production servers. The system will:

1. Discover all 19 instances across both servers
2. Scan their plugin configurations
3. Compare against database rules (once baseline rules are added)
4. Log drift for review
5. Provide web API for configuration management
6. Support future GUI for easy config editing

---

**Current Phase**: Infrastructure complete, ready for baseline config parsing and agent deployment.
