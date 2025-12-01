#!/bin/bash
# Deployment Verification Script
# Run this AFTER deployment to verify everything is working

set -e

echo "======================================"
echo "ArchiveSMP Deployment Verification"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

FAILED=0

# Check 1: Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
    echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python $PYTHON_VERSION (need 3.9+)${NC}"
    FAILED=1
fi

# Check 2: Required Python packages
echo -n "Checking Python dependencies... "
MISSING_DEPS=()
for pkg in fastapi uvicorn pydantic httpx minio pyyaml watchdog pandas openpyxl prometheus-client; do
    if ! python3 -c "import ${pkg//-/_}" 2>/dev/null; then
        MISSING_DEPS+=($pkg)
    fi
done

if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All dependencies installed${NC}"
else
    echo -e "${RED}✗ Missing: ${MISSING_DEPS[*]}${NC}"
    FAILED=1
fi

# Check 3: Installation directory
echo -n "Checking installation directory... "
if [ -d "/opt/archivesmp-config-manager" ]; then
    echo -e "${GREEN}✓ /opt/archivesmp-config-manager exists${NC}"
else
    echo -e "${RED}✗ Directory not found${NC}"
    FAILED=1
fi

# Check 4: Config files
echo -n "Checking configuration files... "
if [ -f "/etc/archivesmp/agent.yaml" ] && [ -f "/etc/archivesmp/secrets.env" ]; then
    echo -e "${GREEN}✓ Config files exist${NC}"
else
    echo -e "${RED}✗ Missing config files${NC}"
    FAILED=1
fi

# Check 5: __init__.py files
echo -n "Checking Python package structure... "
MISSING_INIT=()
for dir in core agent web updaters deployment utils yunohost; do
    if [ ! -f "/opt/archivesmp-config-manager/src/$dir/__init__.py" ]; then
        MISSING_INIT+=($dir)
    fi
done

if [ ${#MISSING_INIT[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All __init__.py files present${NC}"
else
    echo -e "${RED}✗ Missing __init__.py in: ${MISSING_INIT[*]}${NC}"
    FAILED=1
fi

# Check 6: Module import test
echo -n "Testing module imports... "
cd /opt/archivesmp-config-manager
if python3 -c "import sys; sys.path.insert(0, '.'); import src.core; import src.agent; import src.web" 2>/dev/null; then
    echo -e "${GREEN}✓ Module structure valid${NC}"
else
    echo -e "${RED}✗ Module import failed${NC}"
    FAILED=1
fi

# Check 7: SystemD services
echo -n "Checking systemd services... "
MISSING_SERVICES=()
for svc in homeamp-agent archivesmp-agent-api; do
    if ! systemctl list-unit-files | grep -q "^$svc.service"; then
        MISSING_SERVICES+=($svc)
    fi
done

if [ ${#MISSING_SERVICES[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ SystemD services installed${NC}"
else
    echo -e "${RED}✗ Missing services: ${MISSING_SERVICES[*]}${NC}"
    FAILED=1
fi

# Check 8: Service status
echo ""
echo "Service Status:"
echo "---------------"
for svc in homeamp-agent archivesmp-agent-api archivesmp-webapi; do
    if systemctl list-unit-files | grep -q "^$svc.service"; then
        STATUS=$(systemctl is-active $svc 2>/dev/null || echo "inactive")
        if [ "$STATUS" = "active" ]; then
            echo -e "$svc: ${GREEN}$STATUS${NC}"
        else
            echo -e "$svc: ${YELLOW}$STATUS${NC}"
        fi
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}======================================"
    echo "All checks passed! ✓"
    echo -e "======================================${NC}"
    exit 0
else
    echo -e "${RED}======================================"
    echo "Some checks failed! ✗"
    echo -e "======================================${NC}"
    exit 1
fi
