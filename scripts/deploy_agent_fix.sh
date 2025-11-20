#!/bin/bash
# Deploy agent crash fix to production Hetzner server
# Run this ON THE HETZNER SERVER as webadmin user

set -e

echo "🛠️  Deploying agent crash fix to production..."

# 1. Stop the crashing agent
echo "⏸️  Stopping homeamp-agent..."
sudo systemctl stop homeamp-agent

# 2. Backup current (broken) version
echo "📦 Backing up current version..."
sudo cp /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py \
     /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py.backup

# 3. Copy fixed file from development repo
# NOTE: You need to copy the fixed file to the server first
# Option A: Use RDP file sharing to copy to /tmp/agent_cicd_methods.py
# Option B: Paste the file content into /tmp/agent_cicd_methods.py

if [ ! -f /tmp/agent_cicd_methods.py ]; then
    echo "❌ ERROR: Fixed file not found at /tmp/agent_cicd_methods.py"
    echo "📋 Copy the fixed file from:"
    echo "   d:\\homeamp.ampdata\\homeamp.ampdata\\software\\homeamp-config-manager\\src\\agent\\agent_cicd_methods.py"
    echo "   to /tmp/agent_cicd_methods.py on this server"
    exit 1
fi

# 4. Deploy the fix
echo "🚀 Deploying fixed file..."
sudo cp /tmp/agent_cicd_methods.py \
     /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py

# 5. Verify the fix is in place
if grep -q "from pathlib import Path" /opt/archivesmp-config-manager/src/agent/agent_cicd_methods.py; then
    echo "✅ Fix verified: 'from pathlib import Path' import found"
else
    echo "❌ ERROR: Fix not applied correctly!"
    exit 1
fi

# 6. Start the agent
echo "▶️  Starting homeamp-agent..."
sudo systemctl start homeamp-agent

# 7. Watch logs for 10 seconds
echo "📊 Watching logs (Ctrl+C to exit)..."
sleep 2
sudo journalctl -u homeamp-agent -f --since "10 seconds ago"
