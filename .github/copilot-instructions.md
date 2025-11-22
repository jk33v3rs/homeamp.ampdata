# GitHub Copilot Instructions for ArchiveSMP Configuration Manager

## CRITICAL: Development Environment Context

**YOU ARE WORKING IN THE DEVELOPER'S HOME WINDOWS PC - THIS IS THE DEVELOPMENT ENVIRONMENT**

### Environment Setup:
- **Location**: Developer's Windows PC at `e:\homeamp.ampdata\`
- **Purpose**: Software development and testing environment
- **Data Structure**:
  - `utildata/`: Contains replicated server config state from production
    - Snapshots from both bare metal servers (Hetzner and OVH)
    - All instances reflected as they were at time of snapshot
  - `software/homeamp-config-manager/`: The actual software being built
- **Your Access**: You do NOT have direct access to production servers

### Production Servers:
- **Hetzner Xeon** (archivesmp.site, 135.181.212.169): First deployment target
  - 11 instances currently deployed and running
  - Services: archivesmp-webapi.service, homeamp-agent.service
  - MariaDB runs locally on this server (no `-h` or `-P` needed for mysql commands)
- **OVH Ryzen** (archivesmp.online, 37.187.143.41): Second deployment target (pending)
- **Access Model**: Developer has RDP access via Nom Machine (NOT SSH)
- **Your Role**: Provide commands for the developer to execute on production via RDP terminal

### User Accounts & Permissions:
- **webadmin**: Admin user for sudo commands and system operations
- **amp**: Application user - runs all services and agents
- **Development Rule**: Avoid hardcoded values; features should dynamically detect what agents find

### Workflow Rules:

#### DO:
- ✅ Fix all code in the local development environment first (`e:\homeamp.ampdata\software\homeamp-config-manager\`)
- ✅ Test locally when possible
- ✅ Provide clear, copy-paste ready bash/shell commands for production deployment
- ✅ Commit all working fixes to the local repo before deploying to second server
- ✅ Use tools like `replace_string_in_file`, `create_file` on local files
- ✅ Provide direct commands that developer can run via SSH

#### DO NOT:
- ❌ Attempt to modify files on production servers directly with tools
- ❌ Assume you're on the production server when using tools
- ❌ Tell the developer to "upload" files without providing the exact commands
- ❌ Create complex multi-step solutions when simple sed/script commands work
- ❌ Use relative imports or assumptions about production file structure

### Command Format for Production:
When providing commands to run on production (Debian 12), format them as:

```bash
# Clear description of what this does
# Run as webadmin user for sudo operations
sudo <command>
```

**Local Commands (Windows PowerShell):**
```powershell
# Description
<powershell command>
```

**Important:**
- MariaDB on Hetzner: Use `mysql -u sqlworkerSMP -p asmp_config` (local connection, no host/port)
- Production access: Via RDP/Nom Machine, NOT SSH
- Sudo user: `webadmin`
- Service user: `amp`

### Deployment Process:
1. **Fix Locally**: Edit code in `e:\homeamp.ampdata\software\homeamp-config-manager\`
2. **Test**: Verify syntax, logic locally if possible
3. **Generate Fix Script**: Create Python script or sed command to apply fix
4. **Provide Command**: Give developer exact command to run on production
5. **Verify**: Developer runs command and provides log output
6. **Commit**: Once working, commit to repo for next deployment

### Current State (as of Nov 4, 2025):
- Web API: Running on Hetzner, port 8000, 4 workers
- Agent: Running on Hetzner, discovering 11 instances
- Issues: 
  - Drift detector crashes with list/dict type errors
  - Plugin updates not working
  - Web UI filtering broken (server/instance views show all instances)
  - Baselines are markdown files, not parsed configs

### File Locations:
- **Local Dev**: `e:\homeamp.ampdata\software\homeamp-config-manager\`
- **Production**: `/opt/archivesmp-config-manager/`
- **Production Config**: `/etc/archivesmp/agent.yaml`
- **Production Data**: `/var/lib/archivesmp/`
- **Production Logs**: `/var/log/archivesmp/` and `journalctl -u <service>`

## Project Context

This is a configuration management system for managing Minecraft server plugin configurations across multiple AMP (Application Management Panel) instances on two bare metal servers. The system detects configuration drift, manages plugin updates, and provides a web interface for review and deployment.

### Critical Instruction: Always Verify Before Making Architectural Claims

**BEFORE making claims about what the system can/cannot do:**
1. ✅ **Ask for evidence**: Request logs, config files, actual behavior
2. ✅ **State certainty level**: Use "I assume..." vs "The logs show..." vs "I don't know..."
3. ✅ **Ask clarifying questions**: Don't fill gaps with assumptions
4. ✅ **Request verification**: "Can you run X command to confirm Y?"
5. ✅ **Check deployment state**: What's actually installed where?

**NEVER assume without evidence:**
- ❌ What's deployed on which server
- ❌ Network topology or connectivity
- ❌ Service capabilities without reading actual logs
- ❌ Architecture limitations without testing
- ❌ Why something isn't working without diagnostics

**Both human and AI can be wrong - always verify critical facts before proposing solutions**

**Example of WRONG approach:**
- "The system can't reach OVH instances" → Actually nothing was ever deployed there

**Example of RIGHT approach:**
- "I don't see evidence of deployment on OVH. Can you confirm: Is the agent installed there? What does `systemctl status homeamp-agent` show on OVH?"

## Context7 Library Documentation Usage

**ALWAYS use Context7 tools when working with external libraries or frameworks:**

### When to Use Context7:
1. ✅ **Before generating code** for any external library (FastAPI, Bootstrap, Jinja2, SQLAlchemy, etc.)
2. ✅ **When debugging** import errors, API changes, or deprecated methods
3. ✅ **When user mentions** a specific library or asks "how do I use X"
4. ✅ **When implementing new features** that require library-specific patterns
5. ✅ **When upgrading** or changing library versions

### How to Use:
1. First call `mcp_context72_resolve-library-id` with the library name (e.g., "FastAPI", "Bootstrap", "Jinja2")
2. Then call `mcp_context72_get-library-docs` with the resolved library ID and relevant topic
3. Use the documentation to generate accurate, up-to-date code

### Example Workflow:
```
User: "Add a new FastAPI endpoint for uploading files"
→ Call mcp_context72_resolve-library-id(libraryName="FastAPI")
→ Call mcp_context72_get-library-docs(context7CompatibleLibraryID="/tiangolo/fastapi", topic="file upload")
→ Generate code using the latest API patterns from documentation
```

### Libraries We Use:
- **FastAPI**: Web framework for APIs
- **Jinja2**: Template engine
- **Bootstrap 4/5**: Frontend CSS framework
- **SQLAlchemy**: Database ORM (if we add it)
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
- **mysql-connector-python**: MySQL driver

**Don't assume you know the API - verify with Context7 first!**
