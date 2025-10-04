# YunoHost Custom App Configuration - Archive SMP Plugin Manager

## App Manifest (manifest.json)

```json
{
  "name": "Archive SMP Plugin Manager",
  "id": "archivesmp_plugin_manager",
  "packaging_format": 1,
  "description": {
    "en": "Plugin management system for Archive SMP Minecraft servers",
    "fr": "Système de gestion des plugins pour les serveurs Minecraft Archive SMP"
  },
  "version": "1.0.0~ynh1",
  "url": "https://github.com/archivesmp/plugin-manager",
  "upstream": {
    "license": "MIT",
    "website": "https://archivesmp.site",
    "demo": "https://demo.archivesmp.site",
    "admindoc": "https://github.com/archivesmp/plugin-manager/blob/main/docs/admin.md",
    "userdoc": "https://github.com/archivesmp/plugin-manager/blob/main/docs/user.md",
    "code": "https://github.com/archivesmp/plugin-manager"
  },
  "license": "MIT",
  "maintainer": {
    "name": "Archive SMP Team",
    "email": "admin@archivesmp.site"
  },
  "requirements": {
    "yunohost": ">= 11.0.0"
  },
  "multi_instance": false,
  "services": [
    "nginx",
    "php8.1-fpm"
  ],
  "arguments": {
    "install": [
      {
        "name": "domain",
        "type": "domain"
      },
      {
        "name": "path",
        "type": "path",
        "example": "/plugin-manager",
        "default": "/plugin-manager"
      },
      {
        "name": "admin",
        "type": "user"
      },
      {
        "name": "is_public",
        "type": "boolean",
        "default": false,
        "help": {
          "en": "If enabled, the app will be accessible by users not logged into YunoHost.",
          "fr": "Si activé, l'application sera accessible aux utilisateurs non connectés à YunoHost."
        }
      },
      {
        "name": "server_type",
        "type": "string",
        "ask": {
          "en": "Server Location",
          "fr": "Emplacement du serveur"
        },
        "choices": ["ovh", "hetzner"],
        "default": "ovh"
      }
    ]
  }
}
```

## Installation Script (scripts/install)

```bash
#!/bin/bash

#=================================================
# GENERIC START
#=================================================
# IMPORT GENERIC HELPERS
source _common.sh
source /usr/share/yunohost/helpers

#=================================================
# MANAGE SCRIPT FAILURE
#=================================================
ynh_clean_setup () {
    true
}
ynh_abort_if_errors

#=================================================
# RETRIEVE ARGUMENTS FROM THE MANIFEST
#=================================================
domain=$YNH_APP_ARG_DOMAIN
path_url=$YNH_APP_ARG_PATH
admin=$YNH_APP_ARG_ADMIN
is_public=$YNH_APP_ARG_IS_PUBLIC
server_type=$YNH_APP_ARG_SERVER_TYPE

app=$YNH_APP_INSTANCE_NAME

#=================================================
# CHECK IF THE APP CAN BE INSTALLED WITH THESE ARGS
#=================================================
ynh_script_progression --message="Validating installation parameters..." --weight=1

final_path=/var/www/$app
test ! -e "$final_path" || ynh_die --message="This path already contains a folder"

ynh_webpath_register --app=$app --domain=$domain --path_url=$path_url

#=================================================
# STORE SETTINGS FROM MANIFEST
#=================================================
ynh_script_progression --message="Storing installation settings..." --weight=1

ynh_app_setting_set --app=$app --key=domain --value=$domain
ynh_app_setting_set --app=$app --key=path --value=$path_url
ynh_app_setting_set --app=$app --key=admin --value=$admin
ynh_app_setting_set --app=$app --key=server_type --value=$server_type

#=================================================
# CREATE DEDICATED USER
#=================================================
ynh_script_progression --message="Configuring system user..." --weight=1

ynh_system_user_create --username=$app --home_dir="$final_path"

#=================================================
# DOWNLOAD, CHECK AND UNPACK SOURCE
#=================================================
ynh_script_progression --message="Setting up source files..." --weight=1

ynh_app_setting_set --app=$app --key=final_path --value=$final_path
ynh_setup_source --dest_dir="$final_path"

chmod 750 "$final_path"
chmod -R o-rwx "$final_path"
chown -R $app:www-data "$final_path"

#=================================================
# NGINX CONFIGURATION
#=================================================
ynh_script_progression --message="Configuring NGINX web server..." --weight=1

ynh_add_nginx_config

#=================================================
# CREATE DATA DIRECTORY
#=================================================
ynh_script_progression --message="Creating a data directory..." --weight=1

datadir=/home/yunohost.app/$app
ynh_app_setting_set --app=$app --key=datadir --value=$datadir

mkdir -p $datadir/backups
mkdir -p $datadir/staging
mkdir -p $datadir/logs

chmod 750 "$datadir"
chmod -R o-rwx "$datadir"
chown -R $app:www-data "$datadir"

#=================================================
# ADD A CONFIGURATION
#=================================================
ynh_script_progression --message="Adding a configuration file..." --weight=1

ynh_add_config --template="../conf/config.php" --destination="$final_path/config/config.php"

chmod 400 "$final_path/config/config.php"
chown $app:$app "$final_path/config/config.php"

#=================================================
# INSTALL DEPENDENCIES
#=================================================
ynh_script_progression --message="Installing dependencies..." --weight=1

# Install Node.js for the frontend
ynh_install_nodejs --nodejs_version=18

# Install PHP dependencies via Composer
ynh_install_composer --phpversion=$phpversion --workdir="$final_path"

# Build frontend
pushd "$final_path/frontend"
    ynh_use_nodejs
    npm install
    npm run build
popd

#=================================================
# SETUP SYSTEMD
#=================================================
ynh_script_progression --message="Configuring a systemd service..." --weight=1

ynh_add_systemd_config --service="$app-monitor" --template="plugin-monitor.service"
ynh_add_systemd_config --service="$app-api" --template="api-server.service"

#=================================================
# GENERIC FINALIZATION
#=================================================

#=================================================
# INTEGRATE SERVICE IN YUNOHOST
#=================================================
ynh_script_progression --message="Integrating service in YunoHost..." --weight=1

yunohost service add "$app-monitor" --description="Archive SMP Plugin Monitor" --log="/var/log/$app/$app-monitor.log"
yunohost service add "$app-api" --description="Archive SMP API Server" --log="/var/log/$app/$app-api.log"

#=================================================
# START SYSTEMD SERVICE
#=================================================
ynh_script_progression --message="Starting systemd services..." --weight=1

ynh_systemd_action --service_name="$app-monitor" --action="start" --log_path="/var/log/$app/$app-monitor.log"
ynh_systemd_action --service_name="$app-api" --action="start" --log_path="/var/log/$app/$app-api.log"

#=================================================
# SETUP SSOWAT
#=================================================
ynh_script_progression --message="Configuring permissions..." --weight=1

if [ $is_public -eq 1 ]
then
    ynh_permission_update --permission="main" --add="visitors"
fi

# Create admin permission
ynh_permission_create --permission="admin" --url="$domain$path_url/admin" --allowed="$admin"

#=================================================
# RELOAD NGINX
#=================================================
ynh_script_progression --message="Reloading NGINX web server..." --weight=1

ynh_systemd_action --service_name=nginx --action=reload

#=================================================
# SETUP CRON JOBS
#=================================================
ynh_script_progression --message="Setting up cron jobs..." --weight=1

# Hourly plugin update check
echo "0 * * * * $app /var/www/$app/scripts/check-updates.sh >> /var/log/$app/cron.log 2>&1" > /etc/cron.d/$app

#=================================================
# END OF SCRIPT
#=================================================
ynh_script_progression --message="Installation of $app completed" --weight=1
```

## Configuration Template (conf/config.php)

```php
<?php
/**
 * Archive SMP Plugin Manager Configuration
 * Generated by YunoHost installation
 */

return [
    'app' => [
        'name' => 'Archive SMP Plugin Manager',
        'version' => '1.0.0',
        'debug' => false,
        'url' => 'https://__DOMAIN____PATH_URL__',
    ],
    
    'yunohost' => [
        'auth_enabled' => true,
        'admin_user' => '__ADMIN__',
        'server_type' => '__SERVER_TYPE__',
    ],
    
    'servers' => [
        'ovh' => [
            'host' => '37.187.143.41',
            'ssh_key' => '/home/yunohost.app/__APP__/.ssh/ovh_key',
            'servers' => ['BENT01', 'CLIP01', 'CREA01', 'CSMC01', 'EMAD01', 'HARD01', 'HUB01', 'MINE01', 'SMP201']
        ],
        'hetzner' => [
            'host' => '135.181.212.169',
            'ssh_key' => '/home/yunohost.app/__APP__/.ssh/hetzner_key',
            'servers' => ['BIG01', 'DEV01', 'EVO01', 'MIN01', 'PRI01', 'ROY01', 'SMP101', 'TOW01']
        ],
    ],
    
    'database' => [
        'host' => '135.181.212.169:3369',
        'username' => 'sqlworkerSMP',
        'password' => 'SQLdb2024!',
        'database' => 'asmp_SQL',
    ],
    
    'paths' => [
        'data_dir' => '/home/yunohost.app/__APP__',
        'backup_dir' => '/home/yunohost.app/__APP__/backups',
        'staging_dir' => '/home/yunohost.app/__APP__/staging',
        'logs_dir' => '/var/log/__APP__',
        'plugin_matrix' => '/home/yunohost.app/__APP__/data/Plugin_Implementation_Matrix.xlsx',
        'universal_configs' => '/home/yunohost.app/__APP__/data/plugin_universal_configs',
        'variable_configs' => '/home/yunohost.app/__APP__/data/Master_Variable_Configurations.xlsx',
    ],
    
    'plugin_repositories' => [
        'spigot' => [
            'enabled' => true,
            'api_url' => 'https://api.spigotmc.org/legacy/update.php',
            'rate_limit' => 100, // requests per hour
        ],
        'bukkit' => [
            'enabled' => true,
            'api_url' => 'https://api.curseforge.com/v1/',
            'api_key' => '', // Set via environment
        ],
        'github' => [
            'enabled' => true,
            'api_url' => 'https://api.github.com',
            'token' => '', // Set via environment
        ],
    ],
    
    'deployment' => [
        'target_server' => 'DEV01',
        'backup_retention' => 30, // days
        'rollback_timeout' => 300, // seconds
        'health_check_timeout' => 60, // seconds
    ],
    
    'monitoring' => [
        'update_check_interval' => 3600, // seconds (1 hour)
        'health_check_interval' => 300, // seconds (5 minutes)
        'log_retention' => 90, // days
    ],
    
    'security' => [
        'allowed_operations' => [
            'check_updates',
            'stage_updates', 
            'deploy_dev01',
            'rollback',
            'backup_configs',
            'restore_configs',
        ],
        'rate_limiting' => [
            'enabled' => true,
            'max_requests' => 100,
            'window' => 3600, // seconds
        ],
    ],
];
```

## Systemd Service Templates

### Plugin Monitor Service (conf/plugin-monitor.service)
```ini
[Unit]
Description=Archive SMP Plugin Update Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=__APP__
Group=__APP__
WorkingDirectory=__FINALPATH__
Environment=NODE_ENV=production
Environment=CONFIG_PATH=__FINALPATH__/config/config.php
ExecStart=__YNH_NODE__ __FINALPATH__/backend/monitor.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=__APP__-monitor

[Install]
WantedBy=multi-user.target
```

### API Server Service (conf/api-server.service)
```ini
[Unit]
Description=Archive SMP Plugin Manager API
After=network.target
Wants=network.target

[Service]
Type=simple
User=__APP__
Group=__APP__
WorkingDirectory=__FINALPATH__
Environment=NODE_ENV=production
Environment=CONFIG_PATH=__FINALPATH__/config/config.php
Environment=PORT=3000
ExecStart=__YNH_NODE__ __FINALPATH__/backend/server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=__APP__-api

[Install]
WantedBy=multi-user.target
```

## Nginx Configuration (conf/nginx.conf)
```nginx
location __PATH__/ {
    alias __FINALPATH__/public/;
    index index.html index.php;
    
    # Serve static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }
    
    # API endpoints
    location __PATH__/api/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # YunoHost authentication headers
        proxy_set_header Remote-User $remote_user;
        proxy_set_header Remote-Groups $remote_groups;
        proxy_set_header Remote-Name $remote_name;
        proxy_set_header Remote-Email $remote_email;
    }
    
    # Fallback to index.html for SPA routing
    try_files $uri $uri/ __PATH__/index.html;
    
    # Include SSOWAT user panel
    include conf.d/yunohost_panel.conf.inc;
}
```

## Deployment Instructions

### For OVH Server:
```bash
# Install the custom app
yunohost app install https://github.com/archivesmp/plugin-manager \
  --args "domain=ovh.archivesmp.site&path=/plugin-manager&admin=admin&server_type=ovh"
```

### For Hetzner Server:
```bash
# Install the custom app  
yunohost app install https://github.com/archivesmp/plugin-manager \
  --args "domain=hetzner.archivesmp.site&path=/plugin-manager&admin=admin&server_type=hetzner"
```

This YunoHost configuration provides:
- ✅ Authentication via YunoHost's built-in system
- ✅ Deployment to `/var/www/` directory
- ✅ Button interface for non-technical users
- ✅ Systemd services for background monitoring
- ✅ Proper security and permissions
- ✅ Server-aware configuration based on installation location