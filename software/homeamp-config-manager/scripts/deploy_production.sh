#!/bin/bash
# =============================================================================
# Production Deployment Script for Hetzner
# Deploys all metadata tracking, config management, and automation tools
# =============================================================================

set -e  # Exit on error

SERVER="135.181.212.169"
DEPLOY_DIR="/opt/archivesmp-config-manager"
DATA_DIR="/var/lib/archivesmp"
BACKUP_DIR="$DATA_DIR/backups"
AMP_DIR="/home/amp/.ampdata/instances"

echo "=========================================="
echo "ArchiveSMP Config Manager - Deployment"
echo "Server: $SERVER"
echo "=========================================="

# =============================================================================
# Step 1: Deploy Database Schema
# =============================================================================

echo ""
echo "[1/8] Deploying database schema..."

scp scripts/add_plugin_metadata_tables.sql root@$SERVER:/tmp/
scp scripts/add_config_rules_tables.sql root@$SERVER:/tmp/
scp scripts/seed_meta_tags.sql root@$SERVER:/tmp/

ssh root@$SERVER << 'ENDSSH'
    echo "Applying plugin metadata tables..."
    mysql -u asmp_admin -p'Y0urP@ssw0rd' asmp_config < /tmp/add_plugin_metadata_tables.sql
    
    echo "Applying config rules tables..."
    mysql -u asmp_admin -p'Y0urP@ssw0rd' asmp_config < /tmp/add_config_rules_tables.sql
    
    echo "Seeding meta tags..."
    mysql -u asmp_admin -p'Y0urP@ssw0rd' asmp_config < /tmp/seed_meta_tags.sql
    
    echo "Schema deployment complete!"
ENDSSH

# =============================================================================
# Step 2: Deploy Scripts
# =============================================================================

echo ""
echo "[2/8] Deploying automation scripts..."

ssh root@$SERVER "mkdir -p $DEPLOY_DIR/scripts"

scp scripts/load_baselines.py root@$SERVER:$DEPLOY_DIR/scripts/
scp scripts/populate_config_cache.py root@$SERVER:$DEPLOY_DIR/scripts/
scp scripts/populate_plugin_metadata.py root@$SERVER:$DEPLOY_DIR/scripts/
scp scripts/drift_scanner_service.py root@$SERVER:$DEPLOY_DIR/scripts/
scp scripts/enforce_config.py root@$SERVER:$DEPLOY_DIR/scripts/
scp scripts/modrinth_sync.py root@$SERVER:$DEPLOY_DIR/scripts/
scp scripts/hangar_sync.py root@$SERVER:$DEPLOY_DIR/scripts/
scp scripts/platform_version_tracker.py root@$SERVER:$DEPLOY_DIR/scripts/

echo "Scripts deployed!"

# =============================================================================
# Step 3: Create Data Directories
# =============================================================================

echo ""
echo "[3/8] Creating data directories..."

ssh root@$SERVER << ENDSSH
    mkdir -p $DATA_DIR/backups
    mkdir -p $DATA_DIR/reports
    mkdir -p $DATA_DIR/logs
    chmod 755 $DATA_DIR
    chmod 755 $BACKUP_DIR
    echo "Data directories created!"
ENDSSH

# =============================================================================
# Step 4: Load Baseline Configs
# =============================================================================

echo ""
echo "[4/8] Loading baseline configs into database..."

ssh root@$SERVER << ENDSSH
    cd $DEPLOY_DIR
    python3 scripts/load_baselines.py
    echo "Baselines loaded!"
ENDSSH

# =============================================================================
# Step 5: Populate Plugin Metadata
# =============================================================================

echo ""
echo "[5/8] Scanning instances and populating plugin metadata..."

ssh root@$SERVER << ENDSSH
    cd $DEPLOY_DIR
    python3 scripts/populate_plugin_metadata.py --amp-dir $AMP_DIR
    echo "Plugin metadata populated!"
ENDSSH

# =============================================================================
# Step 6: Sync with Modrinth & Hangar
# =============================================================================

echo ""
echo "[6/8] Syncing with Modrinth and Hangar APIs..."

ssh root@$SERVER << ENDSSH
    cd $DEPLOY_DIR
    
    echo "Syncing with Modrinth..."
    python3 scripts/modrinth_sync.py --scan-plugins --scan-datapacks
    
    echo "Syncing with Hangar..."
    python3 scripts/hangar_sync.py --scan-plugins
    
    echo "API sync complete!"
ENDSSH

# =============================================================================
# Step 7: Track Platform Versions
# =============================================================================

echo ""
echo "[7/8] Tracking platform versions..."

ssh root@$SERVER << ENDSSH
    cd $DEPLOY_DIR
    python3 scripts/platform_version_tracker.py --amp-dir $AMP_DIR
    python3 scripts/platform_version_tracker.py --check-updates
    echo "Platform versions tracked!"
ENDSSH

# =============================================================================
# Step 8: Populate Config Cache & Start Drift Scanner
# =============================================================================

echo ""
echo "[8/8] Populating config cache and starting drift scanner..."

ssh root@$SERVER << ENDSSH
    cd $DEPLOY_DIR
    
    echo "Populating config variance cache..."
    python3 scripts/populate_config_cache.py --amp-dir $AMP_DIR
    
    echo "Installing drift scanner systemd service..."
    
    cat > /etc/systemd/system/archivesmp-drift-scanner.service << 'EOF'
[Unit]
Description=ArchiveSMP Config Drift Scanner
After=network.target mariadb.service

[Service]
Type=simple
User=root
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/python3 scripts/drift_scanner_service.py --interval 300
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable archivesmp-drift-scanner
    systemctl restart archivesmp-drift-scanner
    
    echo "Drift scanner service started!"
    systemctl status archivesmp-drift-scanner --no-pager
ENDSSH

# =============================================================================
# Deployment Summary
# =============================================================================

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Services Running:"
echo "  - Web API:        http://$SERVER:8000"
echo "  - Variance GUI:   http://$SERVER:8000/static/variance.html"
echo "  - Main GUI:       http://$SERVER:8000/static/index.html"
echo "  - Drift Scanner:  systemctl status archivesmp-drift-scanner"
echo ""
echo "Database Tables:"
echo "  - plugins: Plugin metadata with CI/CD tracking"
echo "  - instance_plugins: What's installed where"
echo "  - instance_datapacks: Datapack tracking"
echo "  - config_rules: Hierarchical config rules"
echo "  - config_variance_cache: Current variance state"
echo "  - config_drift_log: Drift event history"
echo "  - baseline_snapshots: Universal baseline configs"
echo ""
echo "Next Steps:"
echo "  1. Review variance GUI for drift"
echo "  2. Create custom rules via /api/rules/create"
echo "  3. Enforce configs: python3 scripts/enforce_config.py INSTANCE_ID --apply"
echo "  4. Monitor drift: journalctl -u archivesmp-drift-scanner -f"
echo ""
echo "=========================================="
