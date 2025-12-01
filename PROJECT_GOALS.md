# Archive SMP Plugin Management System - Project Goals

## Overview
Automated plugin management system for 17 Paper 1.21.8 servers across OVH and Hetzner infrastructure, with web interface for non-technical administrators.

## Core Components

### 1. Pulumi-Based Plugin Update Monitor
**Location**: Automated infrastructure management
**Function**: Continuous plugin update detection and staging

#### Features:
- **Hourly Update Checks**: Automated scanning of plugin repositories for new versions
- **Staging Only**: Updates are detected and staged but NOT automatically deployed
- **Excel Integration**: Results written to spreadsheet tracking system
- **CI Build Awareness**: Integration with continuous integration systems
- **Admin-Triggered Deployment**: Updates only deployed upon explicit admin command

#### Technical Requirements:
- Pulumi scripts for infrastructure automation
- Integration with existing plugin matrix spreadsheet
- Connection to plugin repositories (SpigotMC, Bukkit, GitHub releases, etc.)
- Staging area for plugin files before deployment

### 2. Safe Plugin Deployment System
**Target**: DEV01 server (development/testing environment)
**Function**: Controlled plugin updates with rollback capability

#### Deployment Process:
1. **Pre-Deployment Backup**:
   - Remove existing plugin JAR files
   - Preserve ALL configuration files
   - Create `.bak` copies of existing configs
   - Document current plugin versions

2. **Plugin Installation**:
   - Deploy new plugin JAR files
   - Server-aware configuration management
   - Auto-populate configs based on server identity (DEV01)
   - Apply server-specific variable settings from master spreadsheet

3. **Rollback Capability**:
   - Restore `.bak` configuration files on command
   - Revert to previous plugin versions
   - Server state restoration

#### Configuration Intelligence:
- **Universal Config Application**: Apply standardized settings from plugin markdown files
- **Server-Specific Variables**: Populate DEV01-specific values from master variable spreadsheet
- **Config Template System**: Generate appropriate configs for new plugins
- **Backup Management**: Organized `.bak` file system with timestamps

### 3. YunoHost Web Application
**Deployment Location**: `/var/www/` on both servers (OVH + Hetzner)
**Function**: User-friendly interface for plugin management operations

#### Web Interface Features:
- **Authentication**: Behind YunoHost's built-in authentication system
- **Dashboard**: Overview of current plugin status across all servers
- **Update Management**:
  - View available plugin updates
  - Approve/reject updates for staging
  - Trigger deployment to DEV01
  - Monitor deployment progress
  - Initiate rollbacks

#### User Interface Components:
- **Plugin Status Grid**: Visual representation of plugin versions across all 17 servers
- **Update Queue**: Pending updates awaiting approval
- **Deployment History**: Log of all plugin management actions
- **Configuration Viewer**: Display current vs. proposed config changes
- **Server Health**: Status monitoring for all managed servers

#### Button Operations:
- `Check for Updates Now` - Force immediate update scan
- `Stage All Updates` - Move detected updates to staging area
- `Deploy to DEV01` - Execute deployment to development server
- `Rollback Last Change` - Revert most recent deployment
- `Backup Configs` - Create manual configuration backups
- `Restore from Backup` - Restore configs from `.bak` files

### 4. Configuration Management Intelligence
**Function**: Server-aware configuration handling

#### Server Awareness System:
- **Server Identity Detection**: Automatic identification of target server (DEV01, CLIP01, etc.)
- **Config Template Engine**: Generate appropriate configs based on:
  - Universal settings from plugin markdown files
  - Server-specific variables from master spreadsheet
  - Infrastructure context (OVH vs Hetzner)
  - Server role (SMP, Creative, Hub, etc.)

#### Config Backup System:
- **Automated Backups**: Create `.bak` files before any config changes
- **Timestamped Archives**: Organized backup system with deployment timestamps
- **Selective Restoration**: Restore individual plugin configs or full server state
- **Config Diff Viewer**: Compare current vs. backup configurations

### 5. Integration Points

#### Existing Systems:
- **Plugin Implementation Matrix**: Excel-based tracking system
- **Universal Config Files**: 57 plugin-specific markdown configuration files
- **Variable Config Spreadsheet**: Master spreadsheet with server-specific settings
- **Server Infrastructure**: 17 Paper 1.21.8 servers across 2 hosts

#### External Dependencies:
- **Pulumi**: Infrastructure automation platform
- **YunoHost**: Web application hosting and authentication
- **Plugin Repositories**: SpigotMC, Bukkit, GitHub, etc.
- **Database Systems**: MySQL/MariaDB for plugin data
- **File Systems**: Server plugin directories and config management

## Implementation Phases

### Phase 1: Core Automation
- Pulumi scripts for update detection
- Staging system implementation
- Basic deployment to DEV01
- Configuration backup system

### Phase 2: Intelligence Layer
- Server-aware configuration management
- Config template engine
- Rollback system implementation
- Integration with existing spreadsheets

### Phase 3: Web Interface
- YunoHost application development
- Authentication integration
- Dashboard and monitoring
- User-friendly operation buttons

### Phase 4: Production Readiness
- Full server fleet integration
- Advanced monitoring and alerting
- Comprehensive logging and audit trails
- Documentation and training materials

## Security Considerations

### Access Control:
- YunoHost authentication required for web interface
- Admin-only deployment triggers
- Audit logging for all operations
- Rollback restrictions and permissions

### Data Protection:
- Configuration backup integrity
- Secure staging area
- Plugin file verification
- Database connection security

### Operational Safety:
- DEV01-first deployment strategy
- Automatic rollback on failure
- Health checks before/after deployment
- Config validation before application

## Success Metrics

### Automation Efficiency:
- Reduce manual plugin update time from hours to minutes
- 100% configuration backup coverage
- Zero-downtime plugin updates
- Successful rollback rate > 95%

### User Experience:
- Non-technical admins can manage updates via web interface
- Clear visibility into plugin status across all servers
- Intuitive rollback and recovery operations
- Comprehensive audit trail for compliance

### System Reliability:
- Automated hourly update detection
- Safe staging-to-production pipeline
- Server-specific configuration accuracy
- Minimal manual intervention required

---

*This specification serves as the blueprint for implementing a comprehensive, safe, and user-friendly plugin management system for the Archive SMP server infrastructure.*