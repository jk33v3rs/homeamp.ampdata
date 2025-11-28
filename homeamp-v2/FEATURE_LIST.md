# Feature List V2.0
**Exhaustive Feature Specifications for Implementation**

## Feature Organization

Features are organized by functional area with:
- **User Stories**: As a [role], I want [feature] so that [benefit]
- **Technical Requirements**: Implementation details
- **API Endpoints**: REST endpoints required
- **CLI Commands**: Command-line interface
- **Database Tables**: Tables accessed
- **Testing Criteria**: Acceptance tests
- **Priority**: MVP (must-have), V2.1 (nice-to-have), Future (backlog)

---

## 1. Instance Management

### 1.1 Instance Discovery

#### User Story
As a **server administrator**, I want the system to **automatically discover all Minecraft instances** so that I don't have to manually register each one.

#### Technical Requirements
- Scan configured base paths for AMP instances
- Detect platform (Paper, Fabric, NeoForge, Geyser, Velocity) from jar files
- Extract metadata (display name, version, instance ID)
- Record discovery results for audit trail
- Support incremental scans (only new/changed instances)

#### API Endpoints
- `GET /instances` - List all instances
- `POST /instances/discover` - Trigger manual discovery

#### CLI Commands
- `homeamp-cli agent trigger-discovery` - Start discovery scan
- `homeamp-cli instance list` - List discovered instances

#### Database Tables
- `instances`, `discovery_runs`, `discovery_items`

#### Testing Criteria
- ✅ Discovers Paper instances with server.jar
- ✅ Discovers Fabric instances with fabric-server-launch.jar
- ✅ Detects correct Minecraft version
- ✅ Handles missing/corrupted instances gracefully
- ✅ Completes full scan in <60 seconds for 50 instances

#### Priority
**MVP** - Core functionality

---

### 1.2 Instance Registration

#### User Story
As a **server administrator**, I want to **manually register instances** so that I can add instances the auto-discovery missed.

#### Technical Requirements
- Validate instance path exists
- Validate required files present (server.jar)
- Extract metadata from instance
- Allow override of auto-detected values
- Prevent duplicate registrations

#### API Endpoints
- `POST /instances` - Register new instance
- `PUT /instances/{instance_id}` - Update instance metadata

#### CLI Commands
- `homeamp-cli instance register <id> <path> <platform>` - Manual registration

#### Database Tables
- `instances`

#### Testing Criteria
- ✅ Rejects invalid paths
- ✅ Prevents duplicate instance_id
- ✅ Validates platform is supported
- ✅ Returns created instance with ID

#### Priority
**MVP** - Essential for manual management

---

### 1.3 Instance Grouping

#### User Story
As a **server administrator**, I want to **organize instances into logical groups** (SMP, Creative, Test) so that I can apply configurations to multiple instances at once.

#### Technical Requirements
- Create named instance groups
- Add/remove instances from groups
- List instances by group
- Support multiple group membership

#### API Endpoints
- `GET /instance-groups` - List groups
- `POST /instance-groups` - Create group
- `POST /instance-groups/{id}/members` - Add instance to group
- `DELETE /instance-groups/{id}/members/{instance_id}` - Remove instance

#### CLI Commands
- `homeamp-cli group list` - List groups
- `homeamp-cli group create <name>` - Create group
- `homeamp-cli group add-instance <group> <instance>` - Add to group

#### Database Tables
- `instance_groups`, `instance_group_members`

#### Testing Criteria
- ✅ Instance can belong to multiple groups
- ✅ Deleting group doesn't delete instances
- ✅ Group operations are atomic

#### Priority
**MVP** - Required for bulk operations

---

### 1.4 Instance Tagging

#### User Story
As a **server administrator**, I want to **tag instances with labels** (production, modded, public) so that I can filter and categorize them.

#### Technical Requirements
- Create reusable tags with categories
- Assign tags to instances (polymorphic tagging)
- Filter instances by tags
- Support tag colors for UI

#### API Endpoints
- `GET /tags` - List all tags
- `POST /tags` - Create tag
- `POST /tags/assign` - Assign tag to entity
- `GET /instances?tags=production,modded` - Filter by tags

#### CLI Commands
- `homeamp-cli tag create <name> --category=<cat> --color=<hex>`
- `homeamp-cli tag assign <tag> instance <id>`

#### Database Tables
- `meta_tags`, `tag_assignments`

#### Testing Criteria
- ✅ Tags are reusable across entity types
- ✅ Tag colors validate as hex codes
- ✅ Filtering by multiple tags works (AND/OR)

#### Priority
**V2.1** - Nice to have

---

## 2. Plugin Management

### 2.1 Plugin Discovery

#### User Story
As a **server administrator**, I want the system to **automatically discover installed plugins** so that I can track what's running on each instance.

#### Technical Requirements
- Scan instance plugins folder
- Extract metadata from plugin.yml/fabric.mod.json
- Calculate JAR file hash
- Detect plugin version
- Link to global plugin registry

#### API Endpoints
- `GET /instances/{id}/plugins` - List instance plugins
- `POST /instances/{id}/plugins/scan` - Trigger plugin scan

#### CLI Commands
- `homeamp-cli instance scan <id>` - Scan instance (includes plugins)

#### Database Tables
- `plugins`, `instance_plugins`, `discovery_items`

#### Testing Criteria
- ✅ Discovers all plugins in plugins folder
- ✅ Correctly parses Paper plugin.yml
- ✅ Correctly parses Fabric fabric.mod.json
- ✅ Handles malformed metadata gracefully
- ✅ Calculates SHA-256 hash correctly

#### Priority
**MVP** - Core functionality

---

### 2.2 Plugin Update Checking

#### User Story
As a **server administrator**, I want to **check for plugin updates** from Modrinth, Hangar, GitHub, and SpigotMC so that I can keep plugins current.

#### Technical Requirements
- Support multiple update sources per plugin
- Query Modrinth API for versions
- Query Hangar API for versions
- Query GitHub Releases API
- Scrape SpigotMC (no official API)
- Parse semantic versions
- Identify latest stable release
- Record all available versions

#### API Endpoints
- `POST /plugins/{id}/check-updates` - Check for updates
- `GET /plugins/{id}/versions` - List available versions

#### CLI Commands
- `homeamp-cli plugin check-updates <id>` - Check updates for plugin
- `homeamp-cli plugin check-updates` - Check all plugins

#### Database Tables
- `plugins`, `plugin_versions`, `plugin_update_sources`

#### Testing Criteria
- ✅ Modrinth integration works
- ✅ Hangar integration works
- ✅ GitHub releases integration works
- ✅ Version comparison is correct (1.2.10 > 1.2.9)
- ✅ Handles API rate limits gracefully
- ✅ Completes check for 100 plugins in <5 minutes

#### Priority
**MVP** - Essential for update management

---

### 2.3 Plugin Update Queueing

#### User Story
As a **server administrator**, I want to **queue plugin updates for approval** so that updates don't happen automatically without review.

#### Technical Requirements
- Add update to deployment queue
- Track from/to versions
- Set priority (1-10)
- Allow notes/justification
- Support batch updates (multiple plugins at once)

#### API Endpoints
- `POST /plugins/{id}/queue-update` - Queue single update
- `POST /deployments/queue` - Queue batch deployment
- `GET /deployments/queue` - List queued deployments

#### CLI Commands
- `homeamp-cli plugin queue-update <instance> <plugin> <version>`
- `homeamp-cli deployment list --status=pending`

#### Database Tables
- `plugin_update_queue`, `deployment_queue`

#### Testing Criteria
- ✅ Prevents duplicate queue entries
- ✅ Higher priority items appear first
- ✅ Queueing doesn't execute immediately

#### Priority
**MVP** - Required for controlled updates

---

### 2.4 Plugin Deployment

#### User Story
As a **server administrator**, I want to **deploy approved plugin updates** so that instances stay up to date.

#### Technical Requirements
- Download plugin JAR from source
- Verify file hash if available
- Backup old plugin JAR
- Copy new JAR to plugins folder
- Record deployment in history
- Log all actions for audit trail
- Support rollback on failure

#### API Endpoints
- `POST /deployments/{queue_id}/execute` - Execute deployment
- `POST /deployments/{deployment_id}/rollback` - Rollback

#### CLI Commands
- `homeamp-cli deployment execute <queue_id>`
- `homeamp-cli deployment rollback <deployment_id>`

#### Database Tables
- `deployment_queue`, `deployment_history`, `deployment_changes`, `deployment_logs`, `backups`

#### Testing Criteria
- ✅ Downloads correct file from Modrinth
- ✅ Creates backup before replacing
- ✅ Updates instance_plugins record
- ✅ Logs all steps to deployment_logs
- ✅ Rollback restores old version
- ✅ Handles download failures gracefully

#### Priority
**MVP** - Core deployment functionality

---

## Progress Check #1

**Created so far:**
- Instance Management: 4 features (Discovery, Registration, Grouping, Tagging)
- Plugin Management: 4 features (Discovery, Update Checking, Queueing, Deployment)

**Total: 8 features documented**

**Remaining sections:**
- Configuration Management
- Variance Detection
- Deployment & Approval
- Monitoring & Observability
- Backup & Recovery
- Datapack Management
- World/Region Management
- API & CLI
- Integrations

---

## 3. Configuration Management

### 3.1 Config Rule Definition

#### User Story
As a **server administrator**, I want to **define configuration rules** (expected key-value pairs) so that I can enforce consistent settings across instances.

#### Technical Requirements
- Define rules with scope (global, instance, plugin, world, region, rank)
- Specify plugin name, file path, config key
- Set expected value with type validation
- Set enforcement level (required, recommended, optional)
- Allow variable substitution (${SERVER_IP})
- Support polymorphic scoping

#### API Endpoints
- `POST /config/rules` - Create rule
- `GET /config/rules` - List rules
- `PUT /config/rules/{id}` - Update rule
- `DELETE /config/rules/{id}` - Delete rule

#### CLI Commands
- `homeamp-cli config create-rule --plugin=EssentialsX --key=max-homes --value=5 --scope=global`
- `homeamp-cli config list-rules --scope=plugin --plugin=CoreProtect`

#### Database Tables
- `config_rules`, `config_variables`

#### Testing Criteria
- ✅ Global rules apply to all instances
- ✅ Instance-scoped rules override global
- ✅ Variables are substituted correctly
- ✅ Type validation works (int, boolean, string, list)
- ✅ Enforcement levels are respected

#### Priority
**MVP** - Foundation for variance detection

---

### 3.2 Config Scanning

#### User Story
As a **server administrator**, I want the system to **scan all configuration files** on each instance so that I can detect drift from expected values.

#### Technical Requirements
- Scan server.properties
- Scan plugin config.yml files
- Scan Fabric mod JSON configs
- Parse YAML, JSON, .properties formats
- Calculate file hashes for change detection
- Store all discovered key-value pairs
- Track last scan timestamp

#### API Endpoints
- `POST /instances/{id}/configs/scan` - Trigger config scan
- `GET /instances/{id}/configs` - Get all config values

#### CLI Commands
- `homeamp-cli instance scan <id>` - Full scan (includes configs)

#### Database Tables
- `config_values`, `config_file_metadata`, `server_properties`

#### Testing Criteria
- ✅ Parses YAML correctly (preserves types)
- ✅ Parses JSON correctly
- ✅ Parses .properties files
- ✅ Handles malformed files gracefully
- ✅ Detects file changes via hash
- ✅ Scans 100 config files in <30 seconds

#### Priority
**MVP** - Required for variance detection

---

### 3.3 Config Variable Templating

#### User Story
As a **server administrator**, I want to **use template variables** in config rules (${SERVER_IP}, ${DOMAIN}) so that I can define rules that adapt to each server.

#### Technical Requirements
- Define variables with scope (global, server, instance)
- Support variable substitution in expected values
- Validate variable references
- Allow variable overrides at different scopes

#### API Endpoints
- `POST /config/variables` - Create variable
- `GET /config/variables` - List variables
- `PUT /config/variables/{id}` - Update variable

#### CLI Commands
- `homeamp-cli config create-variable SERVER_IP "192.168.1.100" --scope=server`

#### Database Tables
- `config_variables`

#### Testing Criteria
- ✅ Variables substitute correctly in rules
- ✅ Instance-scoped variables override server-scoped
- ✅ Missing variables are detected and reported
- ✅ Variable updates cascade to rule evaluations

#### Priority
**V2.1** - Enhances flexibility

---

## 4. Variance Detection

### 4.1 Config Variance Detection

#### User Story
As a **server administrator**, I want to **automatically detect when configs differ from expected values** so that I can identify and fix configuration drift.

#### Technical Requirements
- Compare actual config values to rules
- Detect missing keys, wrong values, extra keys
- Calculate severity (critical, high, medium, low)
- Support auto-resolution for simple cases
- Generate variance reports

#### API Endpoints
- `GET /config/variances` - List all variances
- `GET /instances/{id}/variances` - Get instance variances
- `POST /config/variances/{id}/resolve` - Mark resolved

#### CLI Commands
- `homeamp-cli config list-variances --severity=critical`
- `homeamp-cli config resolve-variance <id> --notes="Fixed manually"`

#### Database Tables
- `config_variances`, `config_rules`, `config_values`

#### Testing Criteria
- ✅ Detects missing required keys
- ✅ Detects incorrect values
- ✅ Severity calculated from enforcement level
- ✅ Resolved variances are timestamped
- ✅ Detects variances in <10 seconds for 50 instances

#### Priority
**MVP** - Core variance functionality

---

### 4.2 Server Properties Variance

#### User Story
As a **server administrator**, I want to **detect server.properties drift** so that critical server settings don't diverge.

#### Technical Requirements
- Compare server.properties to baseline/rules
- Detect changes in critical properties (max-players, port, etc.)
- Generate separate variance table
- Support baseline templates

#### API Endpoints
- `GET /instances/{id}/server-properties` - Get properties
- `GET /instances/{id}/server-properties/variances` - Get variances

#### CLI Commands
- `homeamp-cli server-properties list-variances`

#### Database Tables
- `server_properties`, `server_properties_variances`, `config_rules`

#### Testing Criteria
- ✅ Detects port conflicts
- ✅ Detects difficulty changes
- ✅ Detects max-players changes
- ✅ Links to instance correctly

#### Priority
**MVP** - Critical for server stability

---

### 4.3 Variance Auto-Resolution

#### User Story
As a **server administrator**, I want **low-severity variances to auto-resolve** (with approval) so that I don't manually fix trivial config drift.

#### Technical Requirements
- Identify auto-resolvable variances
- Queue config changes for approval
- Apply changes on approval
- Log all auto-resolutions
- Support dry-run mode

#### API Endpoints
- `POST /config/variances/auto-resolve` - Queue auto-resolutions
- `GET /config/variances?auto_resolvable=true` - List candidates

#### CLI Commands
- `homeamp-cli config auto-resolve --dry-run`
- `homeamp-cli config auto-resolve --approve`

#### Database Tables
- `config_variances`, `deployment_queue`, `config_changes`

#### Testing Criteria
- ✅ Only resolves optional/recommended variances
- ✅ Requires approval for critical variances
- ✅ Dry-run shows what would change
- ✅ Logs all resolutions to audit trail

#### Priority
**V2.1** - Automation enhancement

---

## 5. Deployment & Approval Workflow

### 5.1 Deployment Queue

#### User Story
As a **server administrator**, I want to **queue changes for approval** before they're deployed so that I can review and approve updates.

#### Technical Requirements
- Queue config changes, plugin updates, datapack deployments
- Set priority (1-10, 1=highest)
- Attach notes/justification
- Support batch deployments (multiple instances)
- Track status (pending, approved, deploying, completed, failed)

#### API Endpoints
- `POST /deployments/queue` - Add to queue
- `GET /deployments/queue` - List queue
- `PATCH /deployments/{id}/priority` - Update priority

#### CLI Commands
- `homeamp-cli deployment queue --type=config --payload=changes.json`
- `homeamp-cli deployment list --status=pending`

#### Database Tables
- `deployment_queue`

#### Testing Criteria
- ✅ Queue sorts by priority then timestamp
- ✅ Prevents duplicate pending deployments
- ✅ Status transitions are valid
- ✅ JSON payload validates

#### Priority
**MVP** - Core workflow

---

### 5.2 Approval System

#### User Story
As a **lead administrator**, I want to **approve/reject deployments** so that changes don't happen without oversight.

#### Technical Requirements
- Create approval requests
- Support multiple approvers
- Track individual votes (approve/reject)
- Set required approval count
- Support expiration timestamps
- Prevent self-approval (optional)

#### API Endpoints
- `POST /deployments/{id}/approve` - Approve deployment
- `POST /deployments/{id}/reject` - Reject deployment
- `GET /approvals/pending` - List pending approvals

#### CLI Commands
- `homeamp-cli deployment approve <id> --comment="LGTM"`
- `homeamp-cli deployment reject <id> --comment="Too risky"`

#### Database Tables
- `approval_requests`, `approval_votes`, `deployment_queue`

#### Testing Criteria
- ✅ Requires configured number of approvals
- ✅ Rejection blocks deployment
- ✅ Expired approvals auto-reject
- ✅ Approval updates deployment status

#### Priority
**MVP** - Required for production safety

---

### 5.3 Deployment Execution

#### User Story
As a **server administrator**, I want approved deployments to **execute automatically or manually** so that changes are applied consistently.

#### Technical Requirements
- Execute config changes (file writes)
- Execute plugin updates (download + install)
- Execute datapack deployments
- Create backups before changes
- Log all actions
- Support rollback on failure
- Record execution metrics (duration, success rate)

#### API Endpoints
- `POST /deployments/{id}/execute` - Execute deployment
- `GET /deployments/{id}/status` - Get execution status
- `GET /deployments/{id}/logs` - Get execution logs

#### CLI Commands
- `homeamp-cli deployment execute <id>`
- `homeamp-cli deployment status <id>`

#### Database Tables
- `deployment_queue`, `deployment_history`, `deployment_changes`, `deployment_logs`, `backups`

#### Testing Criteria
- ✅ Creates backup before changes
- ✅ Applies all changes atomically (or none)
- ✅ Logs detailed steps
- ✅ Records duration accurately
- ✅ Updates deployment status correctly
- ✅ Handles file permission errors

#### Priority
**MVP** - Core execution

---

## Progress Check #2

**Completed:**
- Instance Management: 4 features
- Plugin Management: 4 features
- Configuration Management: 3 features
- Variance Detection: 3 features
- Deployment & Approval: 3 features

**Total: 17 features**

**Remaining:**
- Monitoring & Observability
- Backup & Recovery
- Datapack Management
- World/Region Management
- Integrations
- API & CLI features

---

## 6. Monitoring & Observability

### 6.1 Agent Health Monitoring

#### User Story
As a **system administrator**, I want to **monitor agent health** (uptime, CPU, memory) so that I know the agent is running correctly.

#### Technical Requirements
- Agent sends heartbeats every 60 seconds
- Record CPU usage, memory usage, uptime
- Track last discovery run, last update check
- Detect stale agents (no heartbeat in 5 minutes)
- Alert on agent failures

#### API Endpoints
- `GET /monitoring/agents` - Get agent status
- `GET /monitoring/agents/{server}` - Get specific agent status

#### CLI Commands
- `homeamp-cli agent status` - Show agent health

#### Database Tables
- `agent_heartbeats`, `system_metrics`

#### Testing Criteria
- ✅ Heartbeats recorded every 60 seconds
- ✅ Stale agents flagged correctly
- ✅ Metrics are accurate
- ✅ Missing heartbeats trigger alerts

#### Priority
**MVP** - Essential for operations

---

### 6.2 Discovery Run Tracking

#### User Story
As a **server administrator**, I want to **track discovery run history** so that I can see what was discovered and when.

#### Technical Requirements
- Record each discovery run (full/incremental/manual)
- Track start time, end time, duration
- Count instances/plugins/datapacks discovered
- Record errors encountered
- Link to discovered items

#### API Endpoints
- `GET /monitoring/discovery-runs` - List discovery runs
- `GET /monitoring/discovery-runs/{id}` - Get run details
- `GET /monitoring/discovery-runs/{id}/items` - Get discovered items

#### CLI Commands
- `homeamp-cli discovery history --limit=10`

#### Database Tables
- `discovery_runs`, `discovery_items`

#### Testing Criteria
- ✅ Runs are recorded accurately
- ✅ Duration calculated correctly
- ✅ Item counts match actual discoveries
- ✅ Errors are logged

#### Priority
**MVP** - Important for troubleshooting

---

### 6.3 Audit Logging

#### User Story
As a **compliance officer**, I want **all actions logged** (who, what, when) so that I can audit system changes.

#### Technical Requirements
- Log all config changes
- Log all deployments
- Log all approvals/rejections
- Log all user actions (via API/CLI)
- Store actor (user or 'system')
- Store IP address (if available)
- Support filtering by event type, actor, date range

#### API Endpoints
- `GET /monitoring/audit-log` - Query audit log
- `GET /monitoring/audit-log?actor=admin&event_type=deployment`

#### CLI Commands
- `homeamp-cli audit-log --since=2025-11-20 --actor=system`

#### Database Tables
- `audit_log`

#### Testing Criteria
- ✅ All API actions logged
- ✅ All CLI actions logged
- ✅ All agent actions logged
- ✅ Actor is recorded correctly
- ✅ Filtering works correctly
- ✅ Pagination works for large logs

#### Priority
**MVP** - Required for production

---

### 6.4 Deployment Metrics

#### User Story
As a **DevOps engineer**, I want to **track deployment metrics** (success rate, duration, failure reasons) so that I can optimize the deployment process.

#### Technical Requirements
- Record deployment duration
- Track success/failure rates
- Log error messages
- Calculate average deployment time
- Identify slow deployments
- Generate deployment reports

#### API Endpoints
- `GET /monitoring/deployment-metrics` - Get metrics
- `GET /monitoring/deployment-metrics?start_date=2025-11-01&end_date=2025-11-30`

#### CLI Commands
- `homeamp-cli deployment metrics --month=11`

#### Database Tables
- `deployment_history`, `deployment_changes`

#### Testing Criteria
- ✅ Metrics are accurate
- ✅ Duration calculated correctly
- ✅ Success rate percentage correct
- ✅ Reports filter by date range

#### Priority
**V2.1** - Nice to have

---

## 7. Backup & Recovery

### 7.1 Automatic Backups

#### User Story
As a **server administrator**, I want **automatic backups before changes** so that I can rollback if something goes wrong.

#### Technical Requirements
- Backup before plugin updates
- Backup before config changes
- Support full/config-only/plugins-only backups
- Store backups in configured location
- Record backup metadata (size, file count, timestamp)
- Set expiration dates for auto-cleanup

#### API Endpoints
- `POST /backups` - Create manual backup
- `GET /backups` - List backups
- `GET /backups?instance_id=X` - List instance backups

#### CLI Commands
- `homeamp-cli backup create <instance_id> --type=full`
- `homeamp-cli backup list --instance=<id>`

#### Database Tables
- `backups`, `config_file_metadata`

#### Testing Criteria
- ✅ Backup created before deployment
- ✅ Metadata recorded correctly
- ✅ Backup files exist on disk
- ✅ Expiration set correctly

#### Priority
**MVP** - Critical for safety

---

### 7.2 Backup Restoration

#### User Story
As a **server administrator**, I want to **restore from backups** so that I can recover from bad deployments.

#### Technical Requirements
- Restore config files from backup
- Restore plugin JARs from backup
- Verify backup integrity before restore
- Log restoration actions
- Support partial restore (specific files)

#### API Endpoints
- `POST /backups/{id}/restore` - Restore backup
- `POST /deployments/{id}/rollback` - Rollback deployment (uses backup)

#### CLI Commands
- `homeamp-cli backup restore <backup_id>`
- `homeamp-cli deployment rollback <deployment_id>`

#### Database Tables
- `backups`, `deployment_history`, `config_file_metadata`

#### Testing Criteria
- ✅ Restores all files correctly
- ✅ Verifies backup integrity first
- ✅ Logs restoration steps
- ✅ Handles missing files gracefully
- ✅ Rollback works after deployment

#### Priority
**MVP** - Critical for recovery

---

### 7.3 Backup Cleanup

#### User Story
As a **server administrator**, I want **old backups automatically deleted** so that I don't run out of disk space.

#### Technical Requirements
- Delete backups older than retention period
- Respect configured retention days
- Never delete backups referenced by active deployments
- Log deletions to audit trail
- Run cleanup on schedule

#### API Endpoints
- `POST /backups/cleanup` - Trigger manual cleanup
- `GET /backups?expired=true` - List expired backups

#### CLI Commands
- `homeamp-cli backup cleanup --days=30`

#### Database Tables
- `backups`, `deployment_history`

#### Testing Criteria
- ✅ Deletes only expired backups
- ✅ Preserves recent backups
- ✅ Deletes files from disk
- ✅ Updates database records
- ✅ Logs cleanup actions

#### Priority
**V2.1** - Operational hygiene

---

## 8. Datapack Management

### 8.1 Datapack Discovery

#### User Story
As a **server administrator**, I want **datapacks automatically discovered** so that I can track what's installed in each world.

#### Technical Requirements
- Scan world/datapacks folders
- Detect datapack.zip or unpacked folders
- Extract metadata from pack.mcmeta
- Calculate file hashes
- Link to global datapack registry

#### API Endpoints
- `GET /instances/{id}/datapacks` - List datapacks
- `POST /instances/{id}/datapacks/scan` - Trigger scan

#### CLI Commands
- `homeamp-cli instance scan <id>` - Full scan (includes datapacks)

#### Database Tables
- `datapacks`, `instance_datapacks`, `discovery_items`

#### Testing Criteria
- ✅ Discovers all datapacks in world folders
- ✅ Parses pack.mcmeta correctly
- ✅ Handles nested world folders (world_nether, world_the_end)
- ✅ Detects datapack versions

#### Priority
**V2.1** - Nice to have

---

### 8.2 Datapack Deployment

#### User Story
As a **server administrator**, I want to **deploy datapacks to world folders** so that I can update datapacks across instances.

#### Technical Requirements
- Download datapack from source (GitHub, etc.)
- Deploy to correct world/datapacks folder
- Support multiple worlds per instance
- Queue for approval like plugins
- Record deployment history

#### API Endpoints
- `POST /datapacks/deploy` - Queue datapack deployment

#### CLI Commands
- `homeamp-cli datapack deploy <instance> <world> <datapack> <version>`

#### Database Tables
- `datapack_deployment_queue`, `instance_datapacks`, `deployment_history`

#### Testing Criteria
- ✅ Deploys to correct world folder
- ✅ Handles world folder variants (world, world_nether)
- ✅ Creates backup before deployment
- ✅ Records deployment history

#### Priority
**V2.1** - Enhancement

---

## Progress Check #3

**Completed:**
- Instance Management: 4 features
- Plugin Management: 4 features
- Configuration Management: 3 features
- Variance Detection: 3 features
- Deployment & Approval: 3 features
- Monitoring: 4 features
- Backup & Recovery: 3 features
- Datapack Management: 2 features

**Total: 26 features**

**Remaining:**
- World/Region Management
- Integrations
- API/CLI Cross-Cutting Features
- Summary

---

## 9. World/Region/Rank Management

### 9.1 World Discovery

#### User Story
As a **server administrator**, I want **worlds automatically discovered** (overworld, nether, end) so that I can track world folders.

#### Technical Requirements
- Scan for world folders (level.dat present)
- Detect world type (overworld, nether, end, custom)
- Extract seed, game mode, difficulty
- Link to instance
- Support custom world names

#### API Endpoints
- `GET /instances/{id}/worlds` - List worlds
- `GET /worlds/{id}` - Get world details

#### CLI Commands
- `homeamp-cli world list --instance=<id>`

#### Database Tables
- `worlds`

#### Testing Criteria
- ✅ Discovers world, world_nether, world_the_end
- ✅ Detects custom world folders
- ✅ Parses level.dat correctly
- ✅ Identifies world type

#### Priority
**V2.1** - Nice to have

---

### 9.2 World Grouping

#### User Story
As a **server administrator**, I want to **group worlds** (e.g., all survival worlds) so that I can apply rules to world groups.

#### Technical Requirements
- Create world groups
- Add/remove worlds from groups
- Apply config rules to world groups
- Support scoped rules (world-level)

#### API Endpoints
- `GET /world-groups` - List groups
- `POST /world-groups` - Create group
- `POST /world-groups/{id}/members` - Add world

#### CLI Commands
- `homeamp-cli world-group create <name>`
- `homeamp-cli world-group add <group> <world>`

#### Database Tables
- `world_groups`, `world_group_members`, `config_rules`

#### Testing Criteria
- ✅ Groups created successfully
- ✅ Worlds can belong to multiple groups
- ✅ Config rules apply to group members

#### Priority
**Future** - Low priority

---

### 9.3 Region Tracking

#### User Story
As a **server administrator**, I want to **track WorldGuard/GriefPrevention regions** so that I can apply region-specific configs.

#### Technical Requirements
- Scan for WorldGuard regions
- Scan for GriefPrevention claims
- Link regions to worlds
- Support region-scoped config rules

#### API Endpoints
- `GET /worlds/{id}/regions` - List regions
- `GET /regions/{id}` - Get region details

#### CLI Commands
- `homeamp-cli region list --world=<id>`

#### Database Tables
- `regions`, `config_rules` (scope_type=region)

#### Testing Criteria
- ✅ Discovers WorldGuard regions
- ✅ Links regions to correct world
- ✅ Region-scoped rules work

#### Priority
**Future** - Advanced feature

---

### 9.4 Rank Management

#### User Story
As a **server administrator**, I want to **track LuckPerms ranks** so that I can apply rank-specific configs.

#### Technical Requirements
- Sync ranks from LuckPerms
- Track player rank assignments
- Support rank-scoped config rules
- Cache rank data in database

#### API Endpoints
- `GET /ranks` - List ranks
- `GET /players/{uuid}/ranks` - Get player ranks

#### CLI Commands
- `homeamp-cli rank list`
- `homeamp-cli rank sync` - Sync from LuckPerms

#### Database Tables
- `ranks`, `player_ranks`, `config_rules` (scope_type=rank)

#### Testing Criteria
- ✅ Syncs ranks from LuckPerms
- ✅ Tracks player rank assignments
- ✅ Rank-scoped rules work
- ✅ Respects rank hierarchy

#### Priority
**Future** - Advanced feature

---

## 10. External Integrations

### 10.1 Modrinth Integration

#### User Story
As a **server administrator**, I want to **check Modrinth for plugin updates** so that I can use the official Modrinth API.

#### Technical Requirements
- Search projects on Modrinth
- Get project details and versions
- Download specific versions
- Parse version metadata (MC version compatibility)
- Handle API rate limits

#### API Endpoints
- (Internal integration, not user-facing endpoint)

#### CLI Commands
- (Integrated into plugin update commands)

#### Database Tables
- `plugins`, `plugin_versions`, `plugin_update_sources`

#### Testing Criteria
- ✅ Searches return correct results
- ✅ Downloads work correctly
- ✅ Version metadata parsed
- ✅ Rate limits respected

#### Priority
**MVP** - Core integration

---

### 10.2 Hangar Integration

#### User Story
As a **server administrator**, I want to **check Hangar (PaperMC) for plugin updates** so that I can track Paper-specific plugins.

#### Technical Requirements
- Search Hangar projects
- Get project versions
- Download versions
- Parse changelog
- Handle authentication if needed

#### API Endpoints
- (Internal integration)

#### CLI Commands
- (Integrated into plugin update commands)

#### Database Tables
- `plugins`, `plugin_versions`, `plugin_update_sources`

#### Testing Criteria
- ✅ Hangar API calls work
- ✅ Downloads succeed
- ✅ Changelog parsed correctly

#### Priority
**MVP** - Core integration

---

### 10.3 GitHub Releases Integration

#### User Story
As a **server administrator**, I want to **check GitHub for plugin releases** so that I can track plugins distributed via GitHub.

#### Technical Requirements
- Query GitHub Releases API
- Get release assets (JAR files)
- Download assets
- Parse release notes
- Handle GitHub rate limits

#### API Endpoints
- (Internal integration)

#### CLI Commands
- (Integrated into plugin update commands)

#### Database Tables
- `plugins`, `plugin_versions`, `plugin_update_sources`

#### Testing Criteria
- ✅ GitHub API calls work
- ✅ Identifies correct JAR assets
- ✅ Downloads succeed
- ✅ Rate limits handled

#### Priority
**MVP** - Core integration

---

### 10.4 Discord Notifications

#### User Story
As a **server administrator**, I want **Discord notifications** for deployments and critical variances so that I'm alerted in real-time.

#### Technical Requirements
- Send webhook notifications to Discord
- Support rich embeds
- Configurable notification levels (critical, high, medium, low)
- Track notification delivery status
- Retry failed notifications

#### API Endpoints
- `POST /notifications/test` - Test Discord webhook

#### CLI Commands
- `homeamp-cli notify test` - Send test notification

#### Database Tables
- `notification_log`

#### Testing Criteria
- ✅ Notifications sent successfully
- ✅ Embeds display correctly
- ✅ Delivery status tracked
- ✅ Failed notifications retried

#### Priority
**V2.1** - Nice to have

---

### 10.5 CI/CD Webhook Integration

#### User Story
As a **DevOps engineer**, I want **webhooks from GitHub/Jenkins** to trigger update checks so that deployments can be automated.

#### Technical Requirements
- Accept webhook POSTs from GitHub, Modrinth, Hangar, Jenkins
- Validate webhook signatures
- Parse event payloads
- Trigger appropriate actions (update check, deployment queue)
- Log all webhook events

#### API Endpoints
- `POST /webhooks/github` - GitHub webhook
- `POST /webhooks/modrinth` - Modrinth webhook
- `POST /webhooks/jenkins` - Jenkins webhook

#### CLI Commands
- (N/A - webhook only)

#### Database Tables
- `webhook_events`, `plugin_update_queue`

#### Testing Criteria
- ✅ GitHub webhooks parsed correctly
- ✅ Signatures validated
- ✅ Update checks triggered
- ✅ Events logged

#### Priority
**V2.1** - Automation

---

## 11. API & CLI Cross-Cutting Features

### 11.1 Authentication & Authorization

#### User Story
As a **system administrator**, I want **API key authentication** so that only authorized clients can access the API.

#### Technical Requirements
- Generate API keys (hashed storage)
- Define permissions per key
- Support key expiration
- Track last usage timestamp
- Revoke keys
- Rate limiting per key

#### API Endpoints
- `POST /api-keys` - Create API key
- `GET /api-keys` - List keys
- `DELETE /api-keys/{id}` - Revoke key

#### CLI Commands
- `homeamp-cli api-key create <name> --permissions=read,write`
- `homeamp-cli api-key list`
- `homeamp-cli api-key revoke <id>`

#### Database Tables
- `api_keys`

#### Testing Criteria
- ✅ Keys are hashed (not stored plaintext)
- ✅ Expired keys rejected
- ✅ Permissions enforced
- ✅ Last usage tracked

#### Priority
**MVP** - Security requirement

---

### 11.2 Dashboard Statistics

#### User Story
As a **server administrator**, I want a **dashboard overview** (instance count, variance count, pending deployments) so that I can see system status at a glance.

#### Technical Requirements
- Count total instances
- Count active/inactive instances
- Count critical variances
- Count pending deployments
- Calculate deployment success rate
- Show recent activity feed

#### API Endpoints
- `GET /dashboard/stats` - Get statistics
- `GET /dashboard/recent-activity` - Get activity feed
- `GET /dashboard/alerts` - Get critical alerts

#### CLI Commands
- `homeamp-cli dashboard` - Show dashboard in terminal

#### Database Tables
- `instances`, `config_variances`, `deployment_queue`, `deployment_history`, `audit_log`

#### Testing Criteria
- ✅ Counts are accurate
- ✅ Statistics calculated correctly
- ✅ Recent activity shows latest 20 items
- ✅ Critical alerts prioritized

#### Priority
**MVP** - User interface

---

### 11.3 Feature Flags

#### User Story
As a **product owner**, I want **runtime feature toggles** so that I can enable/disable features without code changes.

#### Technical Requirements
- Define feature flags
- Enable/disable flags at runtime
- Support gradual rollout (percentage)
- Enable for specific instances/users
- Check flags in code before executing features

#### API Endpoints
- `GET /feature-flags` - List flags
- `PUT /feature-flags/{id}` - Update flag
- `GET /feature-flags/{name}/enabled` - Check if enabled

#### CLI Commands
- `homeamp-cli feature-flag list`
- `homeamp-cli feature-flag enable <name>`

#### Database Tables
- `feature_flags`

#### Testing Criteria
- ✅ Flags can be toggled
- ✅ Gradual rollout works
- ✅ Instance-specific flags work
- ✅ Code checks flags correctly

#### Priority
**V2.1** - Operational flexibility

---

## Feature Summary

### Total Feature Count: 38 features

### By Category
| Category | Feature Count | Priority Breakdown |
|----------|---------------|-------------------|
| **Instance Management** | 4 | MVP: 3, V2.1: 1 |
| **Plugin Management** | 4 | MVP: 4 |
| **Configuration Management** | 3 | MVP: 2, V2.1: 1 |
| **Variance Detection** | 3 | MVP: 2, V2.1: 1 |
| **Deployment & Approval** | 3 | MVP: 3 |
| **Monitoring** | 4 | MVP: 3, V2.1: 1 |
| **Backup & Recovery** | 3 | MVP: 2, V2.1: 1 |
| **Datapack Management** | 2 | V2.1: 2 |
| **World/Region/Rank** | 4 | V2.1: 1, Future: 3 |
| **Integrations** | 5 | MVP: 3, V2.1: 2 |
| **API/CLI Cross-Cutting** | 3 | MVP: 2, V2.1: 1 |

### Priority Distribution
- **MVP (Must-Have)**: 24 features (63%)
- **V2.1 (Nice-to-Have)**: 10 features (26%)
- **Future (Backlog)**: 4 features (11%)

### MVP Feature List (24 features)
1. Instance Discovery
2. Instance Registration
3. Instance Grouping
4. Plugin Discovery
5. Plugin Update Checking
6. Plugin Update Queueing
7. Plugin Deployment
8. Config Rule Definition
9. Config Scanning
10. Config Variance Detection
11. Server Properties Variance
12. Deployment Queue
13. Approval System
14. Deployment Execution
15. Agent Health Monitoring
16. Discovery Run Tracking
17. Audit Logging
18. Automatic Backups
19. Backup Restoration
20. Modrinth Integration
21. Hangar Integration
22. GitHub Releases Integration
23. API Authentication
24. Dashboard Statistics

---

**Feature list complete. All 38 features documented with user stories, technical requirements, API endpoints, CLI commands, database tables, testing criteria, and priorities.**
