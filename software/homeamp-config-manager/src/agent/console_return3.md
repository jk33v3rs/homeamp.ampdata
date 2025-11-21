

root@archivesmp /etc/nginx/conf.d # # Check MariaDB status
sudo systemctl status mariadb




# Start MariaDB if it's stopped
sudo systemctl start mariadb
sudo systemctl enable mariadb




# If it fails to start, check logs
sudo journalctl -xeu mariadb -n 50




# Test MariaDB connection
mysql -u root -p -e "SELECT VERSION();"




# Or test with the SQL worker user
mysql -u sqlworkerSMP -p asmp_config -e "SHOW TABLES;"




# Check NoMachine status
sudo systemctl status nxserver




# Start NoMachine if stopped
sudo /etc/NX/nxserver --restart




# Or use systemctl if it has a service
sudo systemctl restart nxserver 2>/dev/null || sudo /etc/NX/nxserver --restart




# Check if NoMachine is listening
sudo netstat -tlnp | grep nx
sudo ss -tlnp | grep 4000




# Check NoMachine logs if there are issues
sudo tail -50 /usr/NX/var/log/nxserver.log
● mariadb.service - MariaDB 10.11.14 database server
     Loaded: loaded (/lib/systemd/system/mariadb.service; enabled; preset: enabled)
     Active: active (running) since Fri 2025-11-21 15:59:43 CET; 33min ago
       Docs: man:mariadbd(8)
             https://mariadb.com/kb/en/library/systemd/
    Process: 86297 ExecStartPre=/usr/bin/install -m 755 -o mysql -g root -d /var/run/mysqld (code=exited, status=0/SUCCESS)
    Process: 86301 ExecStartPre=/bin/sh -c systemctl unset-environment _WSREP_START_POSITION (code=exited, status=0/SUCCESS)
    Process: 86303 ExecStartPre=/bin/sh -c [ ! -e /usr/bin/galera_recovery ] && VAR= ||   VAR=`/usr/bin/galera_recovery`; [>
    Process: 86352 ExecStartPost=/bin/sh -c systemctl unset-environment _WSREP_START_POSITION (code=exited, status=0/SUCCES>
    Process: 86354 ExecStartPost=/etc/mysql/debian-start (code=exited, status=0/SUCCESS)
   Main PID: 86339 (mariadbd)
     Status: "Taking your SQL requests now..."
      Tasks: 8 (limit: 967870)
     Memory: 133.6M
        CPU: 888ms
     CGroup: /system.slice/mariadb.service
             └─86339 /usr/sbin/mariadbd


Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'sqlworkerSMP@172.28.0.1' has>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'sqlworkerTIKI@127.0.0.1' has>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'sqlworkerSMP@45.143.197.247'>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] /usr/sbin/mariadbd: ready for connections.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: Version: '10.11.14-MariaDB-0+deb12u2'  socket: '/run/mysqld/mysqld.sock'  >
Nov 21 15:59:43 archivesmp.site systemd[1]: Started mariadb.service - MariaDB 10.11.14 database server.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 3 [Warning] Access denied for user 'root'@'localhost' >
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Buffer pool(s) load completed at 2511>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 4 [Warning] Access denied for user 'root'@'localhost' >
Nov 21 15:59:43 archivesmp.site debian-start[86373]: ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using p>


Synchronizing state of mariadb.service with SysV service script with /lib/systemd/systemd-sysv-install.
Executing: /lib/systemd/systemd-sysv-install enable mariadb
░░ 
░░ The job identifier is 437868.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] Could not increase number of max_open_file>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] Starting MariaDB 10.11.14-MariaDB-0+deb12u2 s>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Compressed tables use zlib 1.2.13
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Number of transaction pools: 1
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Using crc32 + pclmulqdq instructions
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Using io_uring
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: innodb_buffer_pool_size_max=128m, inn>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Completed initialization of buffer po>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: File system buffers for log disabled >
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: End of log at LSN=22980812179
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: 128 rollback segments are active.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Setting file './ibtmp1' size to 12.00>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: File './ibtmp1' size is now 12.000MiB.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: log sequence number 22980812179; tran>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] Plugin 'FEEDBACK' is disabled.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Loading buffer pool(s) from /var/lib/>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] You need to use --log-bin to make --expire>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] Server socket created on IP: '0.0.0.0', port:>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'root@%' has a wrong 'access'>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'sqlworkerSMP@91.208.92.114' >
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'sqlworkerSMP@172.28.0.1' has>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'sqlworkerTIKI@127.0.0.1' has>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Warning] 'user' entry 'sqlworkerSMP@45.143.197.247'>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] /usr/sbin/mariadbd: ready for connections.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: Version: '10.11.14-MariaDB-0+deb12u2'  socket: '/run/mysqld/mysqld.sock'  >
Nov 21 15:59:43 archivesmp.site systemd[1]: Started mariadb.service - MariaDB 10.11.14 database server.
░░ Subject: A start job for unit mariadb.service has finished successfully
░░ Defined-By: systemd
░░ Support: https://www.debian.org/support
░░ 
░░ A start job for unit mariadb.service has finished successfully.
░░ 
░░ The job identifier is 437868.
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 3 [Warning] Access denied for user 'root'@'localhost' >
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 0 [Note] InnoDB: Buffer pool(s) load completed at 2511>
Nov 21 15:59:43 archivesmp.site mariadbd[86339]: 2025-11-21 15:59:43 4 [Warning] Access denied for user 'root'@'localhost' >
Nov 21 15:59:43 archivesmp.site debian-start[86373]: ERROR 1045 (28000): Access denied for user 'root'@'localhost' (using p>


Enter password: 
+----------------------------+
| VERSION()                  |
+----------------------------+
| 10.11.14-MariaDB-0+deb12u2 |
+----------------------------+
Enter password: 
ERROR 1045 (28000): Access denied for user 'sqlworkerSMP'@'localhost' (using password: NO)
● nxserver.service - NoMachine Server daemon
     Loaded: loaded (/lib/systemd/system/nxserver.service; enabled; preset: enabled)
     Active: active (running) since Fri 2025-11-21 05:34:31 CET; 11h ago
   Main PID: 1555 (nxserver.bin)
      Tasks: 41 (limit: 146647)
     Memory: 157.0M
        CPU: 1min 19.636s
     CGroup: /system.slice/nxserver.service
             ├─1555 /usr/NX/bin/nxserver.bin --daemon
             └─3066 /usr/NX/bin/nxd "-p 4666" "-u 4666"


Nov 21 05:34:31 archivesmp.site systemd[1]: Started nxserver.service - NoMachine Server daemon.
NX> 162 Disabled service: nxd.
NX> 162 Disabled service: nxserver.
NX> 162 Service: nxnode already disabled.
NX> 111 New connections to NoMachine server are enabled.
NX> 161 Enabled service: nxserver.
NX> 162 WARNING: Cannot find X servers running on this machine.
NX> 162 WARNING: A new virtual display will be created on demand.
NX> 161 Enabled service: nxd.
tcp        0      0 0.0.0.0:8078            0.0.0.0:*               LISTEN      89329/nginx: master 
tcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN      89329/nginx: master 
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN      89329/nginx: master 
tcp6       0      0 :::443                  :::*                    LISTEN      89329/nginx: master 
tcp6       0      0 :::80                   :::*                    LISTEN      89329/nginx: master 
tail: cannot open '/usr/NX/var/log/nxserver.log' for reading: No such file or directory
root@archivesmp /etc/nginx/conf.d # 












