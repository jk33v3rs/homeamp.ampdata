webadmin@archivesmp:/opt/archivesmp-config-manager/software/homeamp-config-manager$ # 1. Navigate to project directory
cd /opt/archivesmp-config-manager/software/homeamp-config-manager

# 2. Pull latest changes
sudo -u amp git pull

# 3. Restart both services
sudo systemctl restart homeamp-agent
sudo systemctl restart archivesmp-bootstrap-ui
sudo systemctl restart archivesmp-webapi

# 4. Verify services are running
sudo systemctl status homeamp-agent
sudo systemctl status archivesmp-bootstrap-ui
sudo systemctl status archivesmp-webapi

# 5. Test Bootstrap UI API endpoints
curl http://localhost:8001/api/dashboard/summary
curl http://localhost:8001/api/dashboard/servers

# 6. Check logs if there are issues
sudo journalctl -u archivesmp-bootstrap-ui -n 50 --no-pager
sudo journalctl -u homeamp-agent -n 50 --no-pager
[sudo] password for webadmin: 
remote: Enumerating objects: 35, done.
remote: Counting objects: 100% (35/35), done.
remote: Compressing objects: 100% (2/2), done.
remote: Total 18 (delta 15), reused 18 (delta 15), pack-reused 0 (from 0)
Unpacking objects: 100% (18/18), 1.47 KiB | 83.00 KiB/s, done.
From https://github.com/jk33v3rs/homeamp.ampdata
   142addd..264cbae  master     -> origin/master
Updating 142addd..264cbae
error: unable to unlink old 'software/homeamp-config-manager/config/agent.yaml.example': Permission denied
● homeamp-agent.service - HomeAMP Discovery Agent
     Loaded: loaded (/etc/systemd/system/homeamp-agent.service; enabled; preset: enabled)
     Active: active (running) since Sat 2025-11-22 20:53:03 CET; 522ms ago
   Main PID: 1165015 (python)
      Tasks: 1 (limit: 146647)
     Memory: 26.3M
        CPU: 451ms
     CGroup: /system.slice/homeamp-agent.service
             └─1165015 /opt/archivesmp-config-manager/software/homeamp-config-manager/venv/bin/python -m src.agent.production_endpoint_a>

Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,793 - agent-hetzner-xeon - ERROR - Failed to register plugin instal>
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,796 - agent-hetzner-xeon - ERROR - Failed to register plugin qsaddo>
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,796 - src.database.db_access - ERROR - Query execution error: 1054 >
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,796 - agent-hetzner-xeon - ERROR - Failed to register plugin instal>
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,799 - agent-hetzner-xeon - ERROR - Failed to register plugin qssuit>
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,799 - src.database.db_access - ERROR - Query execution error: 1054 >
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,799 - agent-hetzner-xeon - ERROR - Failed to register plugin instal>
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,804 - agent-hetzner-xeon - ERROR - Failed to register plugin papipr>
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,806 - src.database.db_access - ERROR - Query execution error: 1054 >
Nov 22 20:53:03 archivesmp.site python[1165015]: 2025-11-22 20:53:03,807 - agent-hetzner-xeon - ERROR - Failed to register plugin instal>

● archivesmp-bootstrap-ui.service - ArchiveSMP Config Manager - Bootstrap UI (Port 8001)
     Loaded: loaded (/etc/systemd/system/archivesmp-bootstrap-ui.service; enabled; preset: enabled)
     Active: active (running) since Sat 2025-11-22 20:53:03 CET; 23s ago
   Main PID: 1165021 (python)
      Tasks: 6 (limit: 146647)
     Memory: 98.6M
        CPU: 1.228s
     CGroup: /system.slice/archivesmp-bootstrap-ui.service
             ├─1165021 /opt/archivesmp-config-manager/software/homeamp-config-manager/venv/bin/python -m uvicorn src.web.bootstrap_app:a>
             ├─1165026 /opt/archivesmp-config-manager/software/homeamp-config-manager/venv/bin/python -c "from multiprocessing.resource_>
             ├─1165027 /opt/archivesmp-config-manager/software/homeamp-config-manager/venv/bin/python -c "from multiprocessing.spawn imp>
             └─1165028 /opt/archivesmp-config-manager/software/homeamp-config-manager/venv/bin/python -c "from multiprocessing.spawn imp>

Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: No settings file found, using default location: /opt/archivesmp-config>
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: Settings file not found: /opt/archivesmp-config-manager/software/homea>
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: No settings file found, using default location: /opt/archivesmp-config>
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: Settings file not found: /opt/archivesmp-config-manager/software/homea>
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: INFO:     Started server process [1165028]
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: INFO:     Waiting for application startup.
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: INFO:     Application startup complete.
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     Started server process [1165027]
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     Waiting for application startup.
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     Application startup complete.

● archivesmp-webapi.service - ArchiveSMP Web API
     Loaded: loaded (/etc/systemd/system/archivesmp-webapi.service; enabled; preset: enabled)
     Active: active (running) since Sat 2025-11-22 20:53:03 CET; 28s ago
   Main PID: 1165029 (python)
      Tasks: 1 (limit: 146647)
     Memory: 39.0M
        CPU: 686ms
     CGroup: /system.slice/archivesmp-webapi.service
             └─1165029 /opt/archivesmp-config-manager/software/homeamp-config-manager/venv/bin/python -m uvicorn src.web.api:app --host >

Nov 22 20:53:04 archivesmp.site python[1165029]: No settings file found, using default location: /opt/archivesmp-config-manager/software>
Nov 22 20:53:04 archivesmp.site python[1165029]: Settings file not found: /opt/archivesmp-config-manager/software/homeamp-config-manager>
Nov 22 20:53:04 archivesmp.site python[1165029]: INFO:     Started server process [1165029]
Nov 22 20:53:04 archivesmp.site python[1165029]: INFO:     Waiting for application startup.
Nov 22 20:53:04 archivesmp.site python[1165029]: INFO:     Application startup complete.
Nov 22 20:53:04 archivesmp.site python[1165029]: INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
Nov 22 20:53:05 archivesmp.site python[1165029]: INFO:     127.0.0.1:58994 - "GET /dashboard/approval-queue HTTP/1.1" 200 OK
Nov 22 20:53:05 archivesmp.site python[1165029]: INFO:     127.0.0.1:59000 - "GET /dashboard/network-status HTTP/1.1" 200 OK
Nov 22 20:53:05 archivesmp.site python[1165029]: INFO:     127.0.0.1:59008 - "GET /dashboard/plugin-summary HTTP/1.1" 200 OK
Nov 22 20:53:05 archivesmp.site python[1165029]: INFO:     127.0.0.1:59014 - "GET /dashboard/recent-activity?limit=10 HTTP/1.1" 200 OK

{"detail":"1045 (28000): Access denied for user 'archivesmp'@'Debian-bookworm-latest-amd64-base' (using password: NO)"}{"detail":"1045 (28000): Access denied for user 'archivesmp'@'Debian-bookworm-latest-amd64-base' (using password: NO)"}Nov 22 20:47:31 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     135.181.212.169:35604 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:48:01 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     135.181.212.169:36170 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:48:31 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     135.181.212.169:46794 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:49:01 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     135.181.212.169:60328 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:49:31 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     135.181.212.169:53770 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:50:01 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     135.181.212.169:57832 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:50:31 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     135.181.212.169:59128 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:51:01 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     135.181.212.169:49116 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:51:31 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     135.181.212.169:35372 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:52:01 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     135.181.212.169:45780 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:52:31 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     135.181.212.169:54896 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:53:01 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     135.181.212.169:53642 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:53:03 archivesmp.site systemd[1]: Stopping archivesmp-bootstrap-ui.service - ArchiveSMP Config Manager - Bootstrap UI (Port 8001)...
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     Shutting down
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     Shutting down
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126135]: INFO:     Received SIGTERM, exiting.
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126135]: INFO:     Terminated child process [1126143]
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126135]: INFO:     Terminated child process [1126144]
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126135]: INFO:     Waiting for child process [1126143]
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     Waiting for application shutdown.
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     Application shutdown complete.
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126143]: INFO:     Finished server process [1126143]
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126135]: INFO:     Waiting for child process [1126144]
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     Waiting for application shutdown.
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     Application shutdown complete.
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126144]: INFO:     Finished server process [1126144]
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1126135]: INFO:     Stopping parent process [1126135]
Nov 22 20:53:03 archivesmp.site systemd[1]: archivesmp-bootstrap-ui.service: Deactivated successfully.
Nov 22 20:53:03 archivesmp.site systemd[1]: Stopped archivesmp-bootstrap-ui.service - ArchiveSMP Config Manager - Bootstrap UI (Port 8001).
Nov 22 20:53:03 archivesmp.site systemd[1]: archivesmp-bootstrap-ui.service: Consumed 1min 43.718s CPU time.
Nov 22 20:53:03 archivesmp.site systemd[1]: Started archivesmp-bootstrap-ui.service - ArchiveSMP Config Manager - Bootstrap UI (Port 8001).
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1165021]: INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
Nov 22 20:53:03 archivesmp.site archivesmp-bootstrap-ui[1165021]: INFO:     Started parent process [1165021]
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: No settings file found, using default location: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: Settings file not found: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: No settings file found, using default location: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: Settings file not found: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: No settings file found, using default location: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: Settings file not found: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: No settings file found, using default location: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: Settings file not found: /opt/archivesmp-config-manager/software/homeamp-config-manager/src/config/settings.yaml
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: INFO:     Started server process [1165028]
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: INFO:     Waiting for application startup.
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165028]: INFO:     Application startup complete.
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     Started server process [1165027]
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     Waiting for application startup.
Nov 22 20:53:04 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     Application startup complete.
Nov 22 20:53:31 archivesmp.site archivesmp-bootstrap-ui[1165028]: INFO:     135.181.212.169:57576 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:53:36 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     127.0.0.1:49458 - "GET /api/dashboard/summary HTTP/1.1" 500 Internal Server Error
Nov 22 20:53:36 archivesmp.site archivesmp-bootstrap-ui[1165027]: INFO:     127.0.0.1:49468 - "GET /api/dashboard/servers HTTP/1.1" 500 Internal Server Error
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,594 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/treefeller: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,599 - agent-hetzner-xeon - ERROR - Failed to register plugin resurrectionchest: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,602 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,602 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/resurrectionchest: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,609 - agent-hetzner-xeon - ERROR - Failed to register plugin quests: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,613 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,613 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/quests: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,616 - agent-hetzner-xeon - ERROR - Failed to register plugin hurricane: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,619 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,619 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/hurricane: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,622 - agent-hetzner-xeon - ERROR - Failed to register plugin qsaddon-displaycontrol: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,622 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,622 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/qsaddon-displaycontrol: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,646 - agent-hetzner-xeon - ERROR - Failed to register plugin elitemobs: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,655 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,655 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/elitemobs: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,662 - agent-hetzner-xeon - ERROR - Failed to register plugin lootin: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,664 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,664 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/lootin: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,673 - agent-hetzner-xeon - ERROR - Failed to register plugin cmi: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,683 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,683 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/cmi: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,688 - agent-hetzner-xeon - ERROR - Failed to register plugin glowingitems: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,689 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,690 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/glowingitems: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,699 - agent-hetzner-xeon - ERROR - Failed to register plugin nightcore: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,708 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,709 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/nightcore: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,718 - agent-hetzner-xeon - ERROR - Failed to register plugin luckperms: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,728 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,729 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/luckperms: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,736 - agent-hetzner-xeon - ERROR - Failed to register plugin vault: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,737 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,737 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/vault: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,785 - agent-hetzner-xeon - ERROR - Failed to register plugin plan: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,820 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,820 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/plan: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,969 - agent-hetzner-xeon - ERROR - Failed to register plugin citizens: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,977 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,977 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/citizens: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,987 - agent-hetzner-xeon - ERROR - Failed to register plugin betterstructures: Python type list cannot be converted
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,998 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:04 archivesmp.site python[1165015]: 2025-11-22 20:53:04,998 - agent-hetzner-xeon - ERROR - Failed to register plugin installation PRI01/betterstructures: 1054 (42S22): Unknown column 'file_path' in 'INSERT INTO'
Nov 22 20:53:05 archivesmp.site python[1165015]: 2025-11-22 20:53:05,001 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'datapack_id' in 'INSERT INTO'
Nov 22 20:53:05 archivesmp.site python[1165015]: 2025-11-22 20:53:05,001 - agent-hetzner-xeon - ERROR - Failed to register datapack installation PRI01/tool-trims-dpplugin-121: 1054 (42S22): Unknown column 'datapack_id' in 'INSERT INTO'
Nov 22 20:53:05 archivesmp.site python[1165015]: 2025-11-22 20:53:05,004 - agent-hetzner-xeon - ERROR - Failed to register datapack more_mob_heads_v2173_mc_121-1219: Python type list cannot be converted
Nov 22 20:53:05 archivesmp.site python[1165015]: 2025-11-22 20:53:05,005 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'datapack_id' in 'INSERT INTO'
Nov 22 20:53:05 archivesmp.site python[1165015]: 2025-11-22 20:53:05,005 - agent-hetzner-xeon - ERROR - Failed to register datapack installation PRI01/more_mob_heads_v2173_mc_121-1219: 1054 (42S22): Unknown column 'datapack_id' in 'INSERT INTO'
Nov 22 20:53:05 archivesmp.site python[1165015]: 2025-11-22 20:53:05,008 - src.database.db_access - ERROR - Query execution error: 1054 (42S22): Unknown column 'datapack_id' in 'INSERT INTO'
Nov 22 20:53:05 archivesmp.site python[1165015]: 2025-11-22 20:53:05,008 - agent-hetzner-xeon - ERROR - Failed to register datapack installation PRI01/tool-trims-dpplugin-121: 1054 (42S22): Unknown column 'datapack_id' in 'INSERT INTO'
webadmin@archivesmp:/opt/archivesmp-config-manager/software/homeamp-config-manager$ ^C
webadmin@archivesmp:/opt/archivesmp-config-manager/software/homeamp-config-manager$ # 4. Verify services are running


