-- ============================================================================
-- Grant Remote Access to sqlworkerSMP User
-- Run this on Hetzner MariaDB server to allow remote connections
-- ============================================================================

-- Connect as root/admin user first:
-- mysql -u root -p

-- Option 1: Grant access from specific hostname (your current connection)
-- This is from the error: n1-40-254-94.mas21.nsw.optusnet.com.au
GRANT ALL PRIVILEGES ON asmp_SQL.* TO 'sqlworkerSMP'@'n1-40-254-94.mas21.nsw.optusnet.com.au' IDENTIFIED BY 'SQLdb2024!';
GRANT ALL PRIVILEGES ON asmp_config.* TO 'sqlworkerSMP'@'n1-40-254-94.mas21.nsw.optusnet.com.au' IDENTIFIED BY 'SQLdb2024!';

-- Option 2: Grant access from any hostname (less secure but works)
GRANT ALL PRIVILEGES ON asmp_SQL.* TO 'sqlworkerSMP'@'%' IDENTIFIED BY 'SQLdb2024!';
GRANT ALL PRIVILEGES ON asmp_config.* TO 'sqlworkerSMP'@'%' IDENTIFIED BY 'SQLdb2024!';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify grants
SHOW GRANTS FOR 'sqlworkerSMP'@'%';
SHOW GRANTS FOR 'sqlworkerSMP'@'n1-40-254-94.mas21.nsw.optusnet.com.au';

-- ============================================================================
-- Check existing permissions
-- ============================================================================
SELECT user, host FROM mysql.user WHERE user = 'sqlworkerSMP';
