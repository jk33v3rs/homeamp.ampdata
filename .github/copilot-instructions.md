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
- **OVH Ryzen** (archivesmp.online, 37.187.143.41): Second deployment target (pending)
- **Access Model**: Developer has SSH and SFTP access with sudo privileges
- **Your Role**: Provide commands for the developer to execute on production

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
When providing commands to run on production, format them as:

```bash
# Clear description of what this does
sudo <command>
```

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
