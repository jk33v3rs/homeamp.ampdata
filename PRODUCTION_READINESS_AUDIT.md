# Production Readiness Audit Framework
**Date**: November 10, 2025  
**Target**: Hetzner (hosting/server) + OVH (client)  
**Current State**: Development environment on Windows PC  
**Production State**: Debian servers with live AMP instances, volunteer operators

---

## Critical Context to Maintain Throughout Audit

### Deployment Reality
- **Human Operators**: Volunteers, not doctoral-level troubleshooters
- **Environment**: Production Debian with existing AMP instances
- **Network**: Airgapped from dev (no direct AI access to production)
- **Data Mirror**: `utildata/` = config snapshots only, NOT live RAID mirror
- **Deployment Method**: Ship ZIP to developer → manual install on Hetzner/OVH

### Previous Failure Context
- Last deployment attempt: 3-4 days of failures
- Need EXHAUSTIVE validation this time
- No assumptions - verify every feature individually

---

## Phase 1: Feature Inventory - What Did We Promise?

### 1.1 Core Features from Project Goals/Docs
- [ ] **Drift Detection** - Detect config deviations from baselines
- [ ] **Plugin Update Management** - Update plugins via web UI
- [ ] **Configuration Deployment** - Deploy configs to instances
- [ ] **Web UI Review/Approval** - Review/approve changes before deployment
- [ ] **Baseline Management** - Store/manage universal configs
- [ ] **Server-Aware Config Engine** - Apply server-specific variables
- [ ] **Backup/Rollback** - Backup before changes, rollback on failure
- [ ] **AMP Integration** - Start/stop/restart instances via AMP API
- [ ] **Multi-Server Support** - Hetzner + OVH coordination
- [ ] **Automated Discovery** - Discover AMP instances automatically

### 1.2 Features from Todo List
- [ ] **Excel/CSV Integration** - Read server variables from Master_Variable_Configurations.xlsx
- [ ] **Config Template Engine** - Generate configs for new plugins
- [ ] **Deployment History** - Track what was deployed when
- [ ] **Health Checks** - Verify deployments succeeded
- [ ] **Auto-Rollback** - Automatic rollback on failed health checks

### 1.3 Infrastructure Requirements
- [ ] **Agent Service** - Background service discovering instances
- [ ] **Web API Service** - REST API for web UI
- [ ] **Web UI Frontend** - User interface for operators
- [ ] **Database/Storage** - MinIO or similar for storing data
- [ ] **Authentication** - Secure access control
- [ ] **Logging** - Diagnostic logs for troubleshooting

---

## Phase 2: Audit Question Framework

For EACH feature above, ask:

### A. Code Existence
```
1. Does code exist for this feature?
   - Location: Which file(s)?
   - Line count: Stub vs implementation?
   - Dependencies: What does it import/require?
   
2. Is it a stub/placeholder?
   - Look for: TODO, FIXME, NotImplemented, pass-only functions
   - Check: Function body length (1-2 lines = likely stub)
   - Verify: Actual logic vs just scaffolding
   
3. Is it production-grade or prototype?
   - Error handling: try/except blocks present?
   - Logging: Diagnostic output for troubleshooting?
   - Input validation: Checks for bad data?
   - Edge cases: Handles failures gracefully?
```

### B. Code Quality
```
1. Syntax errors?
   - Run: Python syntax checker
   - Check: Import statements resolve
   - Verify: No obvious typos/bugs
   
2. Logic errors?
   - Read: Control flow makes sense
   - Check: Variable usage consistent
   - Verify: Return values used correctly
   
3. Integration errors?
   - Check: API endpoints match between caller/callee
   - Verify: Data formats consistent (JSON/YAML/etc)
   - Confirm: File paths match production structure
```

### C. External Dependencies
```
1. Runtime dependencies?
   - Check: requirements.txt or package.json
   - Verify: All imports have corresponding packages
   - Confirm: Versions compatible with Debian production
   
2. System dependencies?
   - OS packages: apt packages needed?
   - Binaries: External tools required (git, curl, etc)?
   - Permissions: Does it need sudo/root?
   
3. Network dependencies?
   - External APIs: What URLs does it call?
   - Credentials: API keys/tokens needed?
   - Firewalls: Ports that need opening?
```

### D. Configuration Requirements
```
1. Config files needed?
   - List: What config files must exist?
   - Format: YAML/JSON/INI/etc?
   - Location: Where does code expect them?
   - Defaults: Sensible defaults or will it crash?
   
2. Environment variables?
   - List: What env vars are read?
   - Required: Which are mandatory vs optional?
   - Secrets: Any passwords/keys needed?
   
3. Deployment structure?
   - Directories: What folders must exist?
   - Permissions: File/directory permissions needed?
   - Ownership: User/group ownership requirements?
```

### E. Data Requirements
```
1. Initial data needed?
   - Databases: Schema setup scripts?
   - Seed data: Initial records required?
   - Migration: Data migration from old system?
   
2. Runtime data storage?
   - Location: Where is data stored?
   - Persistence: Survives restarts?
   - Backup: How is data backed up?
   
3. External data sources?
   - AMP API: Connection details configured?
   - MinIO: S3 credentials configured?
   - Excel: Master_Variable_Configurations.xlsx location?
```

---

## Phase 3: Feature-Specific Deep Dives

### 3.1 Plugin Update Management - CI/CD Interrogation

For EACH of 89 plugins, answer:

#### A. Update Source Discovery
```
1. Where are updates published?
   - GitHub Releases? (URL pattern: github.com/{owner}/{repo}/releases)
   - SpigotMC? (URL: spigotmc.org/resources/{id})
   - Modrinth? (URL: modrinth.com/plugin/{slug})
   - Jenkins/CI? (Custom URL)
   - Direct download link?
   - Manual/no updates?
   
2. Do we have this documented?
   - File: plugin_registry.json or similar?
   - Per-plugin: Source URL stored?
   - Fallback: Generic "check GitHub" logic?
```

#### B. Update Detection Method
```
1. How do we check for updates?
   - GitHub API: /repos/{owner}/{repo}/releases/latest
   - SpigotMC API: External version API?
   - Modrinth API: /v2/project/{id}/version
   - RSS feed parsing?
   - HTML scraping? (brittle!)
   - Manual check only?
   
2. Do we need authentication?
   - GitHub: Rate limits without token (60/hr vs 5000/hr)
   - API keys: Do we have them?
   - Credentials: Where are they stored?
```

#### C. Version Comparison
```
1. How do we parse versions?
   - Semantic versioning: 1.2.3
   - Date versioning: 2025-11-10
   - Build numbers: #4523
   - Custom format: v1.2.3-SNAPSHOT
   
2. How do we compare?
   - Code exists: Version comparison logic?
   - Library used: packaging.version or custom?
   - Edge cases: Pre-release vs stable?
```

#### D. Download Mechanism
```
1. What do we download?
   - JAR file directly?
   - ZIP with JAR inside?
   - Source code (requires compile)?
   
2. How do we download?
   - Direct URL: wget/curl style?
   - API call: With authentication?
   - Asset selection: Multiple files, which one?
   
3. Where do we store it?
   - Staging area: Temp directory?
   - Verification: Checksum validation?
   - Deployment: Copy to AMP instance?
```

#### E. Compilation Requirements
```
1. Is compilation needed?
   - Pre-built binaries available? (preferred)
   - Source-only: Must compile?
   - Build tool: Maven/Gradle/other?
   
2. If compilation required:
   - Build dependencies: JDK version?
   - Build script: How to invoke?
   - Build time: How long does it take?
   - Error handling: What if build fails?
   - Who debugs: Requires developer? (bad!)
```

#### F. Extensibility for New Plugins
```
1. How do we add new plugin?
   - Config file: Add entry to plugin_registry?
   - Auto-detect: Scan installed plugins?
   - Template: Copy/paste existing entry?
   
2. Can volunteer do it?
   - Documentation: Step-by-step guide?
   - Validation: Error messages if wrong?
   - No coding: Pure config/UI changes?
```

### 3.2 Drift Detection - Full Stack Audit

#### A. Detection Logic
```
1. How do we detect drift?
   - File: Which module/function?
   - Algorithm: Compare what to what?
   - Threshold: What counts as drift?
   
2. What do we compare?
   - Baseline: Where loaded from?
   - Current: How fetched from AMP?
   - Format: Both in same format?
   - Normalization: Handle formatting differences?
```

#### B. Baseline Management
```
1. Where are baselines?
   - Universal configs: In JSON files?
   - Plugin definitions: In YAML files?
   - Path: Absolute or relative?
   - Packaging: Included in ZIP?
   
2. How are they updated?
   - Manual edit: Volunteer can do it?
   - Auto-update: From DEV01?
   - Version control: Track changes?
```

#### C. Instance Config Fetching
```
1. How do we get current configs?
   - AMP API: Which endpoint?
   - File access: Direct filesystem read?
   - Permissions: Can we read the files?
   
2. Error handling:
   - Instance offline: How handled?
   - Permission denied: Fallback?
   - Malformed config: Crash or skip?
```

#### D. Crash History
```
CRITICAL: Last deployment had list/dict type errors in drift detector!

1. What was the crash?
   - Error message: Exact traceback?
   - Root cause: Type confusion?
   - Fixed: Is fix in current code?
   
2. Testing:
   - Unit tests: Do they exist?
   - Integration tests: Cover this case?
   - Manual test: Run before deploying?
```

### 3.3 Web UI - Frontend/Backend Contract

#### A. Backend API Endpoints
```
For each expected UI feature, verify:

1. Endpoint exists?
   - Route: Flask/FastAPI route defined?
   - Handler: Function implementation exists?
   - Response: Returns correct data structure?
   
2. Authentication:
   - Required: Endpoints protected?
   - Method: API key/JWT/session?
   - Configured: Credentials set up?
   
3. Error handling:
   - 400 errors: Bad request validation?
   - 500 errors: Caught and logged?
   - Messages: User-friendly errors?
```

#### B. Frontend Implementation
```
1. UI pages exist?
   - HTML: Template files present?
   - JavaScript: Frontend logic coded?
   - CSS: Styling complete (or acceptable)?
   
2. API calls match backend?
   - URLs: Correct endpoint paths?
   - Methods: GET/POST/PUT/DELETE match?
   - Data format: JSON structure matches?
   
3. User experience:
   - Error messages: Displayed to user?
   - Loading states: Spinners/feedback?
   - Success feedback: Confirmation shown?
```

### 3.4 Multi-Server Architecture

#### A. Server Discovery
```
1. How are servers identified?
   - Config file: List of servers?
   - Auto-discover: Network scan?
   - Manual: Operator inputs?
   
2. Hetzner vs OVH:
   - Differentiation: How tell them apart?
   - Routing: Correct server for operation?
   - Failover: If one server down?
```

#### B. Agent Deployment
```
1. Where does agent run?
   - Hetzner only: Central server?
   - Both servers: Agent per server?
   - Per instance: Agent per AMP instance?
   
2. Communication:
   - Agent to API: How do they talk?
   - Port: What port/protocol?
   - Firewall: Needs opening?
```

#### C. Data Synchronization
```
1. What needs to sync?
   - Configs: Shared between servers?
   - State: Drift detection results?
   - Updates: Plugin update status?
   
2. How is it synced?
   - Shared database: PostgreSQL/MySQL?
   - MinIO: S3-compatible storage?
   - File sync: rsync/scp?
   - API calls: REST between servers?
```

---

## Phase 4: Audit Execution Plan

### Step 1: Code Structure Discovery
```bash
# Navigate to actual software directory
cd e:/homeamp.ampdata/software/homeamp-config-manager/

# Get directory structure
tree /F /A > structure.txt

# Find all Python files
dir /s /b *.py > python_files.txt

# Find all config files
dir /s /b *.yaml *.yml *.json *.toml *.ini > config_files.txt

# Find all documentation
dir /s /b *.md > docs.txt
```

### Step 2: Code Analysis
```python
# For each Python file:
# 1. Check imports - do they resolve?
# 2. Check functions - stub or implemented?
# 3. Check error handling - try/except present?
# 4. Check logging - diagnostic output?
# 5. Count LOC - is it substantial?

# For each config file:
# 1. Parse validity - YAML/JSON parseable?
# 2. Check references - paths exist?
# 3. Check completeness - all required fields?
```

### Step 3: Dependency Verification
```bash
# Check Python dependencies
cat requirements.txt
# Verify each can install on Debian

# Check system dependencies
grep -r "subprocess\|os\.system\|Popen" *.py
# List all external commands called

# Check network dependencies
grep -r "requests\|http\|urllib" *.py
# List all external URLs called
```

### Step 4: Configuration Completeness
```bash
# Find all config files referenced in code
grep -r "\.yaml\|\.json\|\.toml\|\.ini" src/ --include="*.py"

# Check if they exist in deployment/
ls -R deployment/

# Check for hardcoded paths
grep -r "/opt/\|/var/\|/etc/" src/ --include="*.py"
```

### Step 5: Service Definitions
```bash
# Check systemd service files
ls deployment/*.service

# Validate service files
systemd-analyze verify deployment/*.service

# Check service dependencies
grep "Requires\|After\|Wants" deployment/*.service
```

### Step 6: Installation Script
```bash
# Check if installer exists
ls deployment/install.sh deployment/setup.py

# Check what it does
cat deployment/install.sh

# Verify idempotency (can run multiple times)
# Verify error handling (stops on errors)
# Verify rollback (can undo)
```

### Step 7: Documentation Audit
```bash
# Check README
cat README.md
# Does it explain how to install?
# Does it explain how to configure?
# Does it explain how to troubleshoot?

# Check architecture docs
cat ARCHITECTURE*.md
# Does it match actual code?
# Are diagrams up to date?

# Check handover docs
cat handover.md
# Is it complete for volunteer operators?
```

---

## Phase 5: Production Readiness Checklist

### Deployment Package Contents
- [ ] All Python source code
- [ ] All dependencies (requirements.txt)
- [ ] All config files with sensible defaults
- [ ] All systemd service definitions
- [ ] Installation script (idempotent, error-handling)
- [ ] README with installation steps
- [ ] Troubleshooting guide for volunteers
- [ ] Rollback procedure documented

### Service Requirements
- [ ] Agent service: Complete, tested, no crashes
- [ ] Web API service: Complete, tested, endpoints work
- [ ] Web UI: Complete, tested, user-friendly
- [ ] Database/MinIO: Setup script exists
- [ ] AMP integration: Credentials configured
- [ ] Logging: All services log to journald

### Feature Completeness
- [ ] Drift detection: Works, doesn't crash, handles errors
- [ ] Plugin updates: At least manual update works
- [ ] CI/CD automation: Nice-to-have, document manual process as fallback
- [ ] Config deployment: Works for at least one plugin
- [ ] Backup/rollback: Manual process documented minimum
- [ ] Web UI review: Can view diffs, can approve

### Volunteer Operator Readiness
- [ ] Installation: Single script, no coding required
- [ ] Configuration: Config file with comments
- [ ] Operation: Web UI for all common tasks
- [ ] Troubleshooting: Error messages are helpful
- [ ] Recovery: Rollback procedure documented
- [ ] Updates: How to update the software itself

---

## Phase 6: Execution

I will now:

1. **Read the actual codebase** - Not assumptions, actual files
2. **Build feature matrix** - What exists vs what was promised
3. **Identify gaps** - What's missing or broken
4. **Assess production readiness** - Red/Yellow/Green for each feature
5. **Create shipping checklist** - What can ship NOW vs what needs work
6. **Generate deployment package** - If anything is ready, make it shippable

Proceed with audit? This will take multiple tool calls to read all the code.
