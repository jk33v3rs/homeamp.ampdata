#!/bin/bash
# Fix Production Issues - Run on Hetzner
# This script fixes the drift detector bug and creates MinIO buckets

set -e

echo "=== Fixing Production Issues ==="

# 1. Fix drift_detector.py
echo "[1/4] Patching drift_detector.py..."
cat > /tmp/drift_fix.patch << 'EOF'
--- a/src/analyzers/drift_detector.py
+++ b/src/analyzers/drift_detector.py
@@ -267,6 +267,10 @@ class DriftDetector:
                 for config_file, baseline_config in baseline_plugin.items():
                     current_config = current_plugin.get(config_file, {})
                     
+                    # Ensure current_config is a dict before comparing
+                    if not isinstance(current_config, dict):
+                        current_config = {}
+                    
                     # Compare configurations recursively
                     drift_items.extend(
                         self._compare_configs(
EOF

cd /opt/archivesmp-config-manager
sudo -u amp patch -p1 < /tmp/drift_fix.patch

# 2. Install MinIO client
echo "[2/4] Installing MinIO client..."
if [ ! -f /usr/local/bin/mc ]; then
  wget -q https://dl.min.io/client/mc/release/linux-amd64/mc -O /tmp/mc
  chmod +x /tmp/mc
  sudo mv /tmp/mc /usr/local/bin/mc
fi

# 3. Configure MinIO and create buckets
echo "[3/4] Creating MinIO buckets..."
mc alias set yunohost https://cloud.archivesmp.site webadmin DogWhistle599! 2>/dev/null || true

# Create buckets if they don't exist
mc mb yunohost/archivesmp-changes 2>/dev/null || echo "Bucket archivesmp-changes already exists"
mc mb yunohost/archivesmp-config 2>/dev/null || echo "Bucket archivesmp-config already exists"

# Set public policy for web access (optional)
mc anonymous set download yunohost/archivesmp-changes 2>/dev/null || true

# 4. Restart services
echo "[4/4] Restarting services..."
sudo systemctl restart homeamp-agent
sudo systemctl restart archivesmp-agent-api
sudo systemctl restart archivesmp-webapi

echo ""
echo "=== Fix Complete ==="
echo "Check logs: sudo journalctl -u homeamp-agent -f"
