# n8n Workflow Design for ArchiveSMP Config Manager

**Created:** November 24, 2025  
**Purpose:** Automation workflows for configuration drift detection, plugin updates, and deployment orchestration

---

## Overview

This document describes the n8n automation workflows designed to orchestrate the ArchiveSMP Configuration Manager system. These workflows connect the discovery agent, drift detector, web API, and deployment systems into a cohesive automation pipeline.

---

## Workflow 1: Configuration Drift Detection Pipeline

**Trigger:** Cron schedule (every 6 hours) or Manual webhook  
**Purpose:** Detect configuration drift across all instances and notify admins

### Node Flow:

```
1. [Schedule Trigger] (Cron: 0 */6 * * *)
   ↓
2. [HTTP Request: Trigger Discovery]
   → POST http://localhost:8000/api/discovery/scan
   → Headers: {"X-API-Key": "discovery-secret"}
   ↓
3. [Wait 5 minutes] (Allow discovery to complete)
   ↓
4. [HTTP Request: Run Drift Detector]
   → POST http://localhost:8000/api/drift/detect
   → Body: {"full_scan": true}
   ↓
5. [HTTP Request: Get Drift Summary]
   → GET http://localhost:8000/api/drift/summary
   ↓
6. [IF node: Drift Detected?]
   → If summary.total_drift > 0:
      ├─ True Branch:
      │  ↓
      │  7a. [Send Discord Notification]
      │     → Webhook URL: Discord alert channel
      │     → Message: "🚨 Config Drift Detected: {{$json.total_drift}} issues"
      │  ↓
      │  8a. [Create GitHub Issue] (Optional)
      │     → Repo: jk33v3rs/homeamp.ampdata
      │     → Title: "Auto: Config Drift Detected - {{$now.format('YYYY-MM-DD')}}"
      │     → Body: Drift summary JSON
      │
      └─ False Branch:
         ↓
         7b. [Log Success]
            → Send to monitoring log (optional)
```

### Configuration:

**Schedule Trigger Settings:**
- Cron Expression: `0 */6 * * *` (Every 6 hours)
- Timezone: UTC

**HTTP Request Nodes:**
- Base URL: `http://localhost:8000` (or production domain)
- Authentication: API Key in header `X-API-Key`
- Error workflow: Retry 3 times with exponential backoff

**Discord Notification:**
```json
{
  "content": "🚨 **Config Drift Alert**",
  "embeds": [{
    "title": "Configuration Drift Detected",
    "description": "Drift analysis found {{$json.total_drift}} configuration issues",
    "color": 15158332,
    "fields": [
      {"name": "Plugin Drift", "value": "{{$json.plugin_drift}}", "inline": true},
      {"name": "Config Drift", "value": "{{$json.config_drift}}", "inline": true},
      {"name": "Timestamp", "value": "{{$now.toISO()}}", "inline": false}
    ],
    "footer": {"text": "ArchiveSMP Config Manager"}
  }]
}
```

---

## Workflow 2: Plugin Update Pipeline

**Trigger:** Cron schedule (daily at 3 AM) or Manual webhook  
**Purpose:** Check for plugin updates and queue approved updates

### Node Flow:

```
1. [Schedule Trigger] (Cron: 0 3 * * *)
   ↓
2. [HTTP Request: Check Plugin Updates]
   → GET http://localhost:8000/api/plugins/check-updates
   ↓
3. [HTTP Request: Get Available Updates]
   → GET http://localhost:8000/api/plugins/updates/available
   ↓
4. [IF node: Updates Available?]
   → If $json.length > 0:
      ├─ True Branch:
      │  ↓
      │  5a. [Split In Batches] (Process 5 plugins at a time)
      │     ↓
      │     6a. [Function: Filter Auto-Approved]
      │        → Filter plugins with auto_approve=true OR minor version bumps
      │     ↓
      │     7a. [HTTP Request: Queue Update]
      │        → POST http://localhost:8000/api/plugins/queue-update
      │        → Body: {"plugin_id": "{{$json.plugin_id}}", "version": "{{$json.latest_version}}"}
      │     ↓
      │     8a. [Function: Filter Manual Review]
      │        → Filter plugins requiring approval (major version bumps)
      │     ↓
      │     9a. [Send Discord Review Request]
      │        → Message: "🔔 Plugin {{$json.plugin_name}} has major update: {{$json.current}} → {{$json.latest}}"
      │        → Include approval buttons (if using Discord slash commands)
      │
      └─ False Branch:
         ↓
         5b. [Log: No Updates]
```

### Auto-Approval Logic:

**Function Node JavaScript:**
```javascript
// Auto-approve minor/patch updates, flag major for review
const items = $input.all();
const autoApproved = [];
const needsReview = [];

for (const item of items) {
  const current = item.json.current_version;
  const latest = item.json.latest_version;
  
  // Parse semantic versions
  const [currMajor, currMinor, currPatch] = current.split('.').map(Number);
  const [latestMajor, latestMinor, latestPatch] = latest.split('.').map(Number);
  
  // Auto-approve if:
  // - Patch version bump (1.2.3 → 1.2.4)
  // - Minor version bump (1.2.x → 1.3.0)
  if (latestMajor === currMajor && (latestMinor > currMinor || latestPatch > currPatch)) {
    autoApproved.push(item);
  } else if (latestMajor > currMajor) {
    // Major version bump - needs review
    needsReview.push(item);
  }
}

return [
  { json: { auto: autoApproved, manual: needsReview } }
];
```

---

## Workflow 3: Deployment Orchestration

**Trigger:** Manual webhook or scheduled maintenance window  
**Purpose:** Execute queued deployments with rollback safety

### Node Flow:

```
1. [Webhook Trigger] (Path: /deploy/execute)
   → Auth: API Key
   → Body: {"deployment_id": "uuid", "scope": "instance|group|network"}
   ↓
2. [HTTP Request: Get Deployment Details]
   → GET http://localhost:8000/api/deployments/{{$json.deployment_id}}
   ↓
3. [Function: Pre-Deployment Validation]
   → Check target instances are online
   → Verify no active player sessions (if force=false)
   → Create snapshot backup
   ↓
4. [HTTP Request: Create Snapshot]
   → POST http://localhost:8000/api/snapshots/create
   → Body: {"instances": "{{$json.target_instances}}", "type": "pre-deployment"}
   ↓
5. [HTTP Request: Execute Deployment]
   → POST http://localhost:8000/api/deployments/execute
   → Body: {"deployment_id": "{{$json.deployment_id}}", "snapshot_id": "{{$json.snapshot_id}}"}
   ↓
6. [Wait] (Poll deployment status every 30s, max 30 minutes)
   ↓
7. [HTTP Request: Get Deployment Status]
   → GET http://localhost:8000/api/deployments/{{$json.deployment_id}}/status
   ↓
8. [IF node: Deployment Success?]
   → If status === 'success':
      ├─ True Branch:
      │  ↓
      │  9a. [Send Success Notification]
      │     → Discord: "✅ Deployment {{$json.deployment_id}} completed successfully"
      │  ↓
      │  10a. [HTTP Request: Run Verification]
      │      → POST http://localhost:8000/api/deployments/verify
      │      → Verify configs match baselines
      │
      └─ False Branch (status === 'failed' or 'partial'):
         ↓
         9b. [Send Alert Notification]
            → Discord: "🚨 Deployment {{$json.deployment_id}} FAILED"
         ↓
         10b. [IF node: Auto-Rollback Enabled?]
            → If $json.auto_rollback === true:
               ↓
               11b. [HTTP Request: Trigger Rollback]
                  → POST http://localhost:8000/api/deployments/rollback
                  → Body: {"deployment_id": "{{$json.deployment_id}}", "snapshot_id": "{{$json.snapshot_id}}"}
               ↓
               12b. [Send Rollback Notification]
                  → Discord: "🔄 Auto-rollback initiated for deployment {{$json.deployment_id}}"
```

### Deployment Safety Checks:

**Function Node: Pre-Deployment Validation**
```javascript
const deployment = $json;
const errors = [];

// Check instance availability
const instances = deployment.target_instances || [];
for (const instanceId of instances) {
  const status = await $http.get(`http://localhost:8000/api/instances/${instanceId}/status`);
  if (status.json.state !== 'Running') {
    errors.push(`Instance ${instanceId} is not running`);
  }
  
  // Check for active players (unless force=true)
  if (!deployment.force && status.json.online_players > 0) {
    errors.push(`Instance ${instanceId} has ${status.json.online_players} active players`);
  }
}

// Validate deployment window (if configured)
const now = new Date();
const hour = now.getUTCHours();
if (deployment.require_maintenance_window && (hour < 2 || hour > 6)) {
  errors.push('Deployment outside maintenance window (02:00-06:00 UTC)');
}

return {
  json: {
    valid: errors.length === 0,
    errors: errors,
    deployment_id: deployment.deployment_id,
    can_proceed: errors.length === 0
  }
};
```

---

## Workflow 4: Health Monitoring & Alerting

**Trigger:** Cron schedule (every 15 minutes)  
**Purpose:** Monitor system health and alert on issues

### Node Flow:

```
1. [Schedule Trigger] (Cron: */15 * * * *)
   ↓
2. [HTTP Request: Health Check - Agent]
   → GET http://localhost:5000/health
   ↓
3. [HTTP Request: Health Check - Web API]
   → GET http://localhost:8000/health
   ↓
4. [HTTP Request: Health Check - Database]
   → GET http://localhost:8000/api/system/db-status
   ↓
5. [Function: Aggregate Health Status]
   → Combine all health checks
   → Calculate uptime, response times
   ↓
6. [IF node: Any Service Down?]
   → If any service.status !== 'healthy':
      ├─ True Branch:
      │  ↓
      │  7a. [Send Alert]
      │     → Discord: "🔴 Service Down: {{$json.failed_service}}"
      │     → Include error details
      │  ↓
      │  8a. [HTTP Request: Log Incident]
      │     → POST http://localhost:8000/api/incidents/create
      │
      └─ False Branch:
         ↓
         7b. [Update Metrics Dashboard] (Optional)
            → Send metrics to monitoring system
```

---

## Workflow 5: Database Maintenance

**Trigger:** Cron schedule (weekly, Sunday 4 AM)  
**Purpose:** Clean up old logs, optimize tables, create backups

### Node Flow:

```
1. [Schedule Trigger] (Cron: 0 4 * * 0)
   ↓
2. [HTTP Request: Create Database Backup]
   → POST http://localhost:8000/api/admin/backup/database
   ↓
3. [HTTP Request: Clean Old Logs]
   → DELETE http://localhost:8000/api/admin/cleanup/logs
   → Query: {"older_than_days": 90}
   ↓
4. [HTTP Request: Archive Deployment History]
   → POST http://localhost:8000/api/admin/archive/deployments
   → Query: {"older_than_days": 180}
   ↓
5. [HTTP Request: Optimize Database Tables]
   → POST http://localhost:8000/api/admin/optimize/database
   ↓
6. [Send Summary Notification]
   → Discord: "🗄️ Weekly maintenance completed"
   → Include cleanup stats
```

---

## Common Configuration

### Global Variables (n8n Environment):
```bash
API_BASE_URL=http://localhost:8000
API_KEY=your-secure-api-key-here
DISCORD_WEBHOOK_ALERTS=https://discord.com/api/webhooks/...
DISCORD_WEBHOOK_INFO=https://discord.com/api/webhooks/...
GITHUB_TOKEN=ghp_...
GITHUB_REPO=jk33v3rs/homeamp.ampdata
```

### Error Handling (All Workflows):
- **Retry Logic**: 3 attempts with exponential backoff (5s, 15s, 45s)
- **Error Workflow**: Dedicated error handler workflow that:
  - Logs error to database
  - Sends alert to Discord
  - Creates GitHub issue for critical failures
  - Stores failed workflow execution for replay

### Notification Templates:

**Discord Embed Template (Success):**
```json
{
  "embeds": [{
    "title": "{{$json.title}}",
    "description": "{{$json.message}}",
    "color": 3066993,
    "timestamp": "{{$now.toISO()}}",
    "footer": {"text": "ArchiveSMP Config Manager"}
  }]
}
```

**Discord Embed Template (Error):**
```json
{
  "embeds": [{
    "title": "{{$json.title}}",
    "description": "{{$json.error_message}}",
    "color": 15158332,
    "fields": [
      {"name": "Workflow", "value": "{{$workflow.name}}", "inline": true},
      {"name": "Execution ID", "value": "{{$execution.id}}", "inline": true},
      {"name": "Error Code", "value": "{{$json.error_code}}", "inline": true}
    ],
    "timestamp": "{{$now.toISO()}}",
    "footer": {"text": "ArchiveSMP Config Manager - ERROR"}
  }]
}
```

---

## Integration Points

### Web API Endpoints Used:
- `/health` - Health check
- `/api/discovery/scan` - Trigger discovery
- `/api/drift/detect` - Run drift detection
- `/api/drift/summary` - Get drift summary
- `/api/plugins/check-updates` - Check for plugin updates
- `/api/plugins/updates/available` - Get available updates
- `/api/plugins/queue-update` - Queue plugin update
- `/api/deployments/execute` - Execute deployment
- `/api/deployments/{id}/status` - Get deployment status
- `/api/deployments/rollback` - Rollback deployment
- `/api/snapshots/create` - Create configuration snapshot
- `/api/admin/*` - Admin operations

### External Services:
- **Discord Webhooks**: Notifications and alerts
- **GitHub API**: Issue creation for tracking
- **Database**: Direct queries for complex operations (optional)

---

## Deployment Notes

### n8n Installation:
```bash
# On production server (as webadmin)
sudo npm install -g n8n

# Create systemd service
sudo nano /etc/systemd/system/n8n.service
```

**n8n Service File:**
```ini
[Unit]
Description=n8n Workflow Automation
After=network.target

[Service]
Type=simple
User=amp
WorkingDirectory=/opt/n8n
Environment="N8N_PORT=5678"
Environment="N8N_PROTOCOL=http"
Environment="N8N_HOST=localhost"
Environment="WEBHOOK_URL=http://archivesmp.site:5678"
ExecStart=/usr/bin/n8n start

Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Security:
- Run n8n as `amp` user (not root)
- Use API keys for all webhook/API endpoints
- Restrict n8n UI to localhost or VPN only
- Store credentials in n8n's encrypted credential store

### Monitoring:
- n8n provides built-in execution history
- Set up workflow execution notifications
- Monitor n8n process with systemd
- Log rotation for n8n logs

---

## Future Enhancements

1. **Player-aware deployments**: Check player locations before world changes
2. **Approval workflow integration**: Discord slash commands for approvals
3. **Cost optimization**: Schedule heavy scans during off-peak hours
4. **Multi-server orchestration**: Coordinate deployments across Hetzner and OVH
5. **Automated testing**: Run config validation tests before deployment
6. **Metrics collection**: Push data to Grafana/Prometheus
7. **Incident response**: Auto-remediation workflows for common issues

---

**Status:** Design phase - awaiting implementation after database deployment  
**Next Steps:** Deploy database schema, implement Web API endpoints, configure n8n workflows
