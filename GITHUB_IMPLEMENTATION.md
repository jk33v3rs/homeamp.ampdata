# Archive SMP Automation System - GitHub Implementation Guide

## CRITICAL: Development Environment Context

**YOU ARE WORKING IN THE DEVELOPER'S HOME WINDOWS PC - THIS IS THE DEVELOPMENT ENVIRONMENT**

### Environment Setup:
- **Location**: Developer's Windows PC (local development machine)
- **Purpose**: Software development and testing environment
- **Data**: Contains replicated server config state in `utildata/` folder
  - Snapshots from both bare metal servers (Hetzner and OVH)
  - All instances reflected as they were at time of snapshot
- **Software**: Building the system in `software/homeamp-config-manager/`
- **Access**: You (the AI) do NOT have direct access to production servers

### Production Servers:
- **Hetzner Xeon** (archivesmp.site): First deployment target - 11 instances
- **OVH Ryzen** (archivesmp.online): Second deployment target - pending
- **Access**: Developer has SSH and SFTP with sudo privileges
- **Your Role**: Provide commands for the developer to run on production via SSH

### Critical Notes:
- **DO NOT** attempt to modify files on production directly
- **DO NOT** assume you're on the production server
- **DO** fix all code in the local development environment first
- **DO** provide clear bash/shell commands for the developer to copy-paste on production
- **DO** commit all fixes to the local repo before deployment to second server (OVH)

### Workflow:
1. Fix code in local development environment (`e:\homeamp.ampdata\software\homeamp-config-manager\`)
2. Test locally if possible
3. Provide deployment commands for developer to run on production server
4. Developer executes commands via SSH
5. Verify via logs that developer provides
6. Commit working fixes to repo for next server deployment

## Repository Structure

```
archive-smp-automation/
├── pulumi-infrastructure/
│   ├── plugin-monitor/          # Hourly update detection
│   ├── staging-system/          # Update staging area
│   └── deployment-engine/       # DEV01 deployment automation
├── web-interface/
│   ├── yunohost-app/           # YunoHost custom application
│   ├── frontend/               # React/Vue.js dashboard
│   └── backend/                # API for plugin operations
├── config-management/
│   ├── templates/              # Server-aware config templates
│   ├── backup-system/          # .bak file management
│   └── restoration/            # Config rollback system
├── integration/
│   ├── spreadsheet-sync/       # Excel integration
│   └── plugin-repositories/    # Repository connectors
└── docs/
    ├── deployment/             # Deployment guides
    └── user-manual/            # Web interface documentation
```

## Development Priorities

### 1. Pulumi Infrastructure (Priority: HIGH)
**Files to create:**
- `pulumi-infrastructure/plugin-monitor/index.ts`
- `pulumi-infrastructure/staging-system/staging.ts`
- `pulumi-infrastructure/deployment-engine/deploy.ts`

**Key Functions:**
```typescript
// plugin-monitor/index.ts
export async function checkPluginUpdates(): Promise<UpdateManifest[]>
export async function stageUpdates(updates: UpdateManifest[]): Promise<void>
export async function writeToSpreadsheet(results: UpdateResults): Promise<void>

// deployment-engine/deploy.ts
export async function deployToDEV01(plugins: PluginUpdate[]): Promise<DeploymentResult>
export async function backupConfigs(server: string): Promise<BackupManifest>
export async function rollbackDeployment(backupId: string): Promise<void>
```

### 2. Configuration Management (Priority: HIGH)
**Files to create:**
- `config-management/templates/ConfigTemplateEngine.ts`
- `config-management/backup-system/BackupManager.ts`
- `config-management/restoration/RestoreManager.ts`

**Server Awareness System:**
```typescript
interface ServerConfig {
  serverId: string;              // DEV01, CLIP01, etc.
  host: 'ovh-1' | 'hetzner-1';
  serverType: 'smp' | 'creative' | 'hub' | 'special';
  pluginLimits: PluginLimits;
  databaseConfig: DatabaseConfig;
}

class ConfigTemplateEngine {
  generateConfig(plugin: string, server: ServerConfig): PluginConfig;
  applyUniversalSettings(plugin: string): UniversalConfig;
  applyServerVariables(plugin: string, server: ServerConfig): VariableConfig;
}
```

### 3. YunoHost Web Application (Priority: MEDIUM)
**Files to create:**
- `web-interface/yunohost-app/manifest.json`
- `web-interface/yunohost-app/scripts/install`
- `web-interface/yunohost-app/scripts/upgrade`
- `web-interface/frontend/src/components/PluginDashboard.vue`
- `web-interface/backend/src/api/plugin-operations.ts`

**Web Interface Requirements:**
```javascript
// Frontend Components
- PluginStatusGrid.vue      // 17-server plugin matrix display
- UpdateQueue.vue           // Pending updates management
- DeploymentLog.vue         // Operation history
- ServerHealth.vue          // Server status monitoring
- ConfigViewer.vue          // Configuration comparison

// Backend API Endpoints
POST /api/check-updates     // Trigger update scan
POST /api/stage-updates     // Move to staging
POST /api/deploy-dev01      // Deploy to development
POST /api/rollback/:id      // Rollback deployment
GET  /api/server-status     // Server health check
```

### 4. Integration Layer (Priority: MEDIUM)
**Files to create:**
- `integration/spreadsheet-sync/ExcelIntegration.ts`
- `integration/plugin-repositories/RepositoryConnector.ts`

**Repository Connectors:**
```typescript
interface PluginRepository {
  name: string;
  type: 'spigot' | 'bukkit' | 'github' | 'custom';
  baseUrl: string;
  apiKey?: string;
}

class RepositoryConnector {
  async checkUpdates(plugin: PluginManifest): Promise<PluginUpdate | null>;
  async downloadPlugin(update: PluginUpdate): Promise<Buffer>;
  async verifyChecksum(plugin: Buffer, expectedHash: string): Promise<boolean>;
}
```

## Implementation Phases

### Phase 1: Core Infrastructure (Weeks 1-2)
```bash
# Tasks
□ Set up Pulumi project structure
□ Implement plugin update detection
□ Create staging system
□ Build basic DEV01 deployment
□ Develop config backup system
```

### Phase 2: Configuration Intelligence (Weeks 3-4)
```bash
# Tasks
□ Implement ConfigTemplateEngine
□ Build server awareness system
□ Create .bak file management
□ Develop rollback capabilities
□ Test with existing plugin matrix
```

### Phase 3: Web Interface (Weeks 5-6)
```bash
# Tasks
□ Create YunoHost application structure
□ Build React/Vue.js frontend
□ Implement backend API
□ Add authentication integration
□ Deploy to /var/www/ locations
```

### Phase 4: Testing & Production (Weeks 7-8)
```bash
# Tasks
□ End-to-end testing on DEV01
□ Performance optimization
□ Security audit
□ Documentation completion
□ Production deployment
```

## Required GitHub Actions

### Continuous Integration
```yaml
# .github/workflows/ci.yml
name: Archive SMP Automation CI
on: [push, pull_request]
jobs:
  test-pulumi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Pulumi
        uses: pulumi/action-install-pulumi-cli@v2
      - name: Test Infrastructure
        run: |
          cd pulumi-infrastructure
          npm install
          npm test
  
  test-web-interface:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Test Frontend
        run: |
          cd web-interface/frontend
          npm install
          npm run test
      - name: Test Backend
        run: |
          cd web-interface/backend
          npm install
          npm test
```

### Deployment Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Servers
on:
  push:
    branches: [main]
jobs:
  deploy-ovh:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to OVH YunoHost
        run: |
          # Deploy web interface to OVH server
  
  deploy-hetzner:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Hetzner YunoHost
        run: |
          # Deploy web interface to Hetzner server
```

## Environment Variables Required

```bash
# Plugin Repository Access
SPIGOT_API_KEY=xxx
BUKKIT_API_KEY=xxx
GITHUB_TOKEN=xxx

# Server Access
OVH_SSH_KEY=xxx
HETZNER_SSH_KEY=xxx
YUNOHOST_API_KEY=xxx

# Database Connections
MYSQL_HOST=135.181.212.169:3369
MYSQL_USER=sqlworkerSMP
MYSQL_PASS=SQLdb2024!

# Pulumi Configuration
PULUMI_ACCESS_TOKEN=xxx
PULUMI_STACK=production
```

## Success Criteria

### Automation Goals
- [ ] Hourly plugin update detection running
- [ ] Safe staging system operational
- [ ] DEV01 deployment with config preservation
- [ ] Rollback system tested and verified
- [ ] Web interface accessible via YunoHost auth

### User Experience Goals
- [ ] Non-technical admins can manage updates
- [ ] One-click deployment to DEV01
- [ ] Visual plugin status across all 17 servers
- [ ] Comprehensive audit logging
- [ ] Successful rollback in <5 minutes

### Technical Goals
- [ ] Integration with existing Excel plugin matrix
- [ ] Server-aware configuration management
- [ ] .bak file system with timestamps
- [ ] 99.9% uptime for monitoring system
- [ ] Zero config loss during updates

---

*This implementation guide provides the technical roadmap for building the Archive SMP plugin management automation system.*