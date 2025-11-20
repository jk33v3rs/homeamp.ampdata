# Deploy Agent Crash Fix to Production

**Issue**: Agent crash-looping with `NameError: name 'Path' is not defined` (287+ restarts)  
**Fix**: Added `from pathlib import Path` import to `agent_cicd_methods.py` line 7  
**Status**: ✅ Fixed locally, ❌ NOT deployed to production

---

## Quick Deployment Steps

### Step 1: Copy Fixed File to Production Server

**Option A - Via RDP File Sharing:**
1. Open RDP connection to Hetzner (135.181.212.169)
2. Use RDP file sharing to copy:
   - **From:** `d:\homeamp.ampdata\homeamp.ampdata\software\homeamp-config-manager\src\agent\agent_cicd_methods.py`
   - **To:** `/tmp/agent_cicd_methods.py` on Hetzner

**Option B - Manual Copy/Paste:**
1. Open the local file in editor
2. Copy all contents
3. On Hetzner terminal, create new file:
   ```bash
   nano /tmp/agent_cicd_methods.py
   # Paste contents, save with Ctrl+O, exit with Ctrl+X
   ```

### Step 2: Deploy the Fix

On Hetzner server as `webadmin`:

```bash
# Stop the crashing agent
sudo systemctl stop homeamp-agent

# Backup current (broken) version
sudo cp /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py \
     /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py.backup

# Deploy the fix
sudo cp /tmp/agent_cicd_methods.py \
     /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py

# Verify the fix
grep "from pathlib import Path" /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py
# Should show: from pathlib import Path

# Start the agent
sudo systemctl start homeamp-agent

# Watch logs - should NOT see NameError anymore
sudo journalctl -u homeamp-agent -f
```

### Step 3: Verify Fix Worked

Look for in the logs:
- ✅ **GOOD**: "Agent service started successfully"
- ✅ **GOOD**: "Starting drift detection scan"
- ❌ **BAD**: "NameError: name 'Path' is not defined"

If you see the agent running for more than 30 seconds without crashing, the fix worked!

---

## Alternative: Use Deployment Script

Copy `scripts/deploy_agent_fix.sh` to Hetzner and run it:

```bash
# On Hetzner as webadmin
chmod +x /tmp/deploy_agent_fix.sh
/tmp/deploy_agent_fix.sh
```

---

## What The Fix Does

**Before (BROKEN):**
```python
# Line 7 was missing this import
import os
import json
from datetime import datetime
```

**After (FIXED):**
```python
from pathlib import Path  # ← ADDED THIS LINE
import os
import json
from datetime import datetime
```

**Result**: Agent can now use `Path()` objects on line 339 without crashing.

---

## Rollback (If Needed)

If something goes wrong:

```bash
sudo systemctl stop homeamp-agent
sudo cp /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py.backup \
     /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py
sudo systemctl start homeamp-agent
```
