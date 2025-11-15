@echo off
REM SSH Tunnel to Hetzner MariaDB
REM Creates local port 3369 tunnel to remote MariaDB

echo Creating SSH tunnel to Hetzner MariaDB...
echo Local: localhost:3369 -> Remote: 135.181.212.169:3369
echo.
echo Press Ctrl+C to close tunnel when done.
echo.

ssh -L 3369:localhost:3369 root@135.181.212.169 -N

