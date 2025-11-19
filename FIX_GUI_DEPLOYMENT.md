# Fix GUI Deployment - Missing CSS/JS Files

## Problem
GUI loads but shows no styling, emojis, or functionality because CSS and JavaScript files aren't being served.

## Solution: Verify and Re-deploy Files

### Step 1: Check what's currently deployed

```bash
# On Hetzner server
ls -la /var/www/archivesmp-config/
```

**Expected:** Should see .html, .js, and .css files
**If missing JS/CSS:** Continue to Step 2

### Step 2: Verify source files exist

```bash
cd /opt/archivesmp-config-manager/src/web/static
ls -la
```

**Expected output:**
- config_browser.html, config_browser.js
- config_editor.html, config_editor.js
- styles.css
- etc.

### Step 3: Manual deployment (guaranteed to work)

```bash
# Copy ALL files from source to deployment directory
sudo cp -v /opt/archivesmp-config-manager/src/web/static/* /var/www/archivesmp-config/

# Set proper permissions
sudo chown -R www-data:www-data /var/www/archivesmp-config/
sudo chmod -R 755 /var/www/archivesmp-config/

# Verify ALL files copied
ls -la /var/www/archivesmp-config/ | grep -E '\.(js|css|html)$'
```

### Step 4: Clear browser cache and test

```bash
# Check nginx is serving files
curl -I http://localhost:8078/styles.css
curl -I http://localhost:8078/config_browser.js
```

**Expected:** Both should return `200 OK` with `Content-Type: text/css` and `application/javascript`

### Step 5: Force browser refresh

In browser:
1. Go to http://135.181.212.169:8078/
2. Press **Ctrl+Shift+R** (hard refresh, clears cache)
3. Check browser console (F12) for 404 errors

## Root Cause

The deployment script `deploy_gui.sh` line 42:
```bash
ls -lh "$GUI_DIR"/*.html | awk '{print "   - " $9}'
```

This **only displays** HTML files in output, but the actual copy command should work:
```bash
sudo cp -r "$STATIC_SOURCE"/* "$GUI_DIR/"
```

However, the `-r` flag may not be copying files correctly. The manual `cp -v` command above fixes this.

## Quick One-Liner

```bash
sudo cp -v /opt/archivesmp-config-manager/src/web/static/* /var/www/archivesmp-config/ && sudo chown -R www-data:www-data /var/www/archivesmp-config/ && ls -la /var/www/archivesmp-config/ | grep -E '\.(js|css)$' && echo "✓ Files deployed, hard refresh browser (Ctrl+Shift+R)"
```
