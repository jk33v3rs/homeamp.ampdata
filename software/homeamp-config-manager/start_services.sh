#!/bin/bash
# Start ArchiveSMP Config Manager services
# Run this on Hetzner to start both agent and web API
# Run this on OVH to start agent only

set -e

INSTALL_DIR="/home/webadmin/archivesmp-config-manager"
SERVER_NAME=$(hostname)

echo "=================================================="
echo "ArchiveSMP Config Manager - Service Startup"
echo "=================================================="
echo "Server: $SERVER_NAME"
echo "Install Dir: $INSTALL_DIR"
echo ""

# Check if running on correct server
if [[ "$SERVER_NAME" != *"hetzner"* ]] && [[ "$SERVER_NAME" != *"ovh"* ]]; then
    echo "⚠️  WARNING: Could not detect server type from hostname"
    echo "Expected 'hetzner' or 'ovh' in hostname"
    echo ""
    read -p "Is this the Hetzner server? (y/n): " is_hetzner
    if [[ "$is_hetzner" == "y" ]]; then
        SERVER_TYPE="hetzner"
    else
        SERVER_TYPE="ovh"
    fi
else
    if [[ "$SERVER_NAME" == *"hetzner"* ]]; then
        SERVER_TYPE="hetzner"
    else
        SERVER_TYPE="ovh"
    fi
fi

echo "Server type: $SERVER_TYPE"
echo ""

# Change to install directory
cd "$INSTALL_DIR"

# Check Python dependencies
echo "Checking Python dependencies..."
python3 -c "import fastapi, uvicorn, httpx, yaml" 2>/dev/null || {
    echo "❌ ERROR: Missing Python dependencies"
    echo ""
    echo "Install with:"
    echo "  pip3 install fastapi uvicorn httpx pyyaml"
    exit 1
}
echo "✓ Dependencies OK"
echo ""

# Check expectations data
if [ ! -f "data/expectations/universal_configs.json" ]; then
    echo "❌ ERROR: Expectations data not found"
    echo "Expected: $INSTALL_DIR/data/expectations/universal_configs.json"
    echo ""
    echo "Run package_expectations.py on development machine first"
    exit 1
fi
echo "✓ Expectations data found"
echo ""

# Check AMP instances directory
if [ ! -d "/home/amp/.ampdata/instances" ]; then
    echo "⚠️  WARNING: AMP instances directory not found"
    echo "Expected: /home/amp/.ampdata/instances"
    echo ""
    echo "Agent will not be able to discover instances"
    read -p "Continue anyway? (y/n): " continue_anyway
    if [[ "$continue_anyway" != "y" ]]; then
        exit 1
    fi
else
    instance_count=$(find /home/amp/.ampdata/instances -maxdepth 1 -type d | wc -l)
    echo "✓ Found AMP instances directory ($((instance_count - 1)) instances)"
fi
echo ""

# Kill any existing processes
echo "Checking for existing processes..."
pkill -f "uvicorn src.agent.api" || true
if [[ "$SERVER_TYPE" == "hetzner" ]]; then
    pkill -f "uvicorn src.web.api" || true
fi
sleep 2
echo "✓ Cleaned up old processes"
echo ""

# Start agent API (both servers)
echo "Starting Agent API (port 8001)..."
nohup python3 -m uvicorn src.agent.api:app --host 0.0.0.0 --port 8001 \
    > logs/agent.log 2>&1 &
AGENT_PID=$!
echo "✓ Agent API started (PID: $AGENT_PID)"
echo "  Log: $INSTALL_DIR/logs/agent.log"
echo ""

# Start web API (Hetzner only)
if [[ "$SERVER_TYPE" == "hetzner" ]]; then
    echo "Starting Web API (port 8000)..."
    nohup python3 -m uvicorn src.web.api:app --host 0.0.0.0 --port 8000 \
        > logs/webapi.log 2>&1 &
    WEBAPI_PID=$!
    echo "✓ Web API started (PID: $WEBAPI_PID)"
    echo "  Log: $INSTALL_DIR/logs/webapi.log"
    echo ""
fi

# Wait a moment for services to start
echo "Waiting for services to start..."
sleep 3

# Test endpoints
echo "Testing endpoints..."

# Test agent
if curl -s http://localhost:8001/api/agent/status > /dev/null; then
    echo "✓ Agent API responding on port 8001"
else
    echo "❌ Agent API not responding"
fi

# Test web API (Hetzner only)
if [[ "$SERVER_TYPE" == "hetzner" ]]; then
    if curl -s http://localhost:8000/docs > /dev/null; then
        echo "✓ Web API responding on port 8000"
    else
        echo "❌ Web API not responding"
    fi
fi

echo ""
echo "=================================================="
echo "Services Started Successfully!"
echo "=================================================="
echo ""

if [[ "$SERVER_TYPE" == "hetzner" ]]; then
    echo "Access points:"
    echo "  - Web UI: http://135.181.212.169:8000/static/deploy.html"
    echo "  - API Docs: http://135.181.212.169:8000/docs"
    echo "  - Agent API: http://localhost:8001/docs"
    echo ""
    echo "Process IDs:"
    echo "  - Agent: $AGENT_PID"
    echo "  - Web API: $WEBAPI_PID"
else
    echo "Access points:"
    echo "  - Agent API: http://localhost:8001/docs"
    echo ""
    echo "Process IDs:"
    echo "  - Agent: $AGENT_PID"
fi

echo ""
echo "To stop services:"
echo "  kill $AGENT_PID"
if [[ "$SERVER_TYPE" == "hetzner" ]]; then
    echo "  kill $WEBAPI_PID"
fi

echo ""
echo "To view logs:"
echo "  tail -f $INSTALL_DIR/logs/agent.log"
if [[ "$SERVER_TYPE" == "hetzner" ]]; then
    echo "  tail -f $INSTALL_DIR/logs/webapi.log"
fi

echo ""
echo "For systemd service setup, see DEPLOYMENT_GUIDE.md"
echo ""
