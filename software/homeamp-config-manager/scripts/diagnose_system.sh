#!/bin/bash
# Comprehensive system diagnostic

echo "=========================================="
echo "ArchiveSMP Config Manager - System Diagnostic"
echo "=========================================="
echo

echo "=== 1. Database Status ==="
mysql -h 135.181.212.169 -P 3369 -u root -p'2024!SQLdb' asmp_config -e "
SELECT 'Instances' as table_name, COUNT(*) as count FROM instances
UNION ALL
SELECT 'Plugins', COUNT(*) FROM plugins
UNION ALL
SELECT 'Servers', COUNT(*) FROM servers
UNION ALL
SELECT 'Instance Groups', COUNT(*) FROM instance_groups
UNION ALL
SELECT 'Config Baselines', COUNT(*) FROM config_baselines
UNION ALL
SELECT 'Meta Tags', COUNT(*) FROM meta_tags
UNION ALL
SELECT 'Plugin Versions', COUNT(*) FROM plugin_versions;
"
echo

echo "=== 2. Sample Plugin Data ==="
mysql -h 135.181.212.169 -P 3369 -u root -p'2024!SQLdb' asmp_config -e "
SELECT name, current_version, latest_version, update_available 
FROM plugins 
LIMIT 5;
"
echo

echo "=== 3. Agent Service Status ==="
systemctl status homeamp-agent.service --no-pager | head -20
echo

echo "=== 4. Agent Recent Logs ==="
journalctl -u homeamp-agent.service -n 30 --no-pager
echo

echo "=== 5. API Service Status ==="
systemctl status archivesmp-webapi.service --no-pager | head -20
echo

echo "=== 6. API Recent Logs ==="
journalctl -u archivesmp-webapi.service -n 30 --no-pager
echo

echo "=== 7. Test API Endpoints ==="
echo "GET /api/plugins:"
curl -s http://localhost:8000/api/plugins | python3 -m json.tool | head -30
echo
echo "GET /api/instances:"
curl -s http://localhost:8000/api/instances | python3 -m json.tool | head -30
echo

echo "=== 8. Check Baseline Files ==="
if [ -f "/opt/archivesmp-config-manager/data/baselines/universal_configs.zip" ]; then
    echo "✓ Baseline zip exists"
    unzip -l /opt/archivesmp-config-manager/data/baselines/universal_configs.zip | head -20
else
    echo "✗ Baseline zip missing"
fi
echo

echo "=== 9. Check GUI Files ==="
echo "HTML files in /var/www/archivesmp-config:"
ls -lh /var/www/archivesmp-config/*.html | wc -l
echo "JS files:"
ls -lh /var/www/archivesmp-config/*.js | wc -l
echo "CSS files:"
ls -lh /var/www/archivesmp-config/*.css | wc -l
echo

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
