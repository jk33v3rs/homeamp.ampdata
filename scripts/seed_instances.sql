-- ============================================================================
-- Seed Data: Instances (20 Minecraft Servers)
-- Insert all production instances from both physical servers
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- OVH RYZEN INSTANCES (37.187.143.41 - archivesmp.online)
-- ============================================================================

INSERT INTO instances (instance_id, instance_name, server_name, server_host, port, platform, minecraft_version, is_active, is_production, description) VALUES
    ('CLIP01', 'ClippyCore Enhanced Hardcore', 'ovh-ryzen', '37.187.143.41', 1179, 'paper', '1.21.8', true, true, 'ClippyCore enhanced hardcore mode'),
    ('CSMC01', 'CounterStrike: Minecraft', 'ovh-ryzen', '37.187.143.41', 1180, 'paper', '1.21.8', true, true, 'CounterStrike-style minigame'),
    ('EMAD01', 'EMadventure Server', 'ovh-ryzen', '37.187.143.41', 1181, 'paper', '1.21.8', true, true, 'Adventure-focused gameplay'),
    ('BENT01', 'BentoBox Ecosystem', 'ovh-ryzen', '37.187.143.41', 1182, 'paper', '1.21.8', true, true, 'Skyblock/OneBlock/Worlds suite'),
    ('HCRE01', 'Hardcore Survival', 'ovh-ryzen', '37.187.143.41', 1183, 'paper', '1.21.8', true, true, 'Hardcore survival server'),
    ('SMP201', 'Archive SMP Season 2', 'ovh-ryzen', '37.187.143.41', 1184, 'paper', '1.21.8', true, true, 'Primary SMP server'),
    ('HUB01', 'Network Hub', 'ovh-ryzen', '37.187.143.41', 1185, 'paper', '1.21.8', true, true, 'Central server hub'),
    ('MINT01', 'Minetorio', 'ovh-ryzen', '37.187.143.41', 1186, 'paper', '1.21.8', true, true, 'Factorio-inspired automation'),
    ('CREA01', 'Creative Server', 'ovh-ryzen', '37.187.143.41', 1187, 'paper', '1.21.8', true, true, 'Creative building mode'),
    ('GEY01', 'Geyser Standalone', 'ovh-ryzen', '37.187.143.41', 19132, 'geyser', '1.21.8', true, true, 'Bedrock Edition support'),
    ('VEL01', 'Velocity Proxy', 'ovh-ryzen', '37.187.143.41', 25565, 'velocity', '1.21.8', true, true, 'Network backbone proxy');

-- ============================================================================
-- HETZNER XEON INSTANCES (135.181.212.169 - archivesmp.site)
-- ============================================================================

INSERT INTO instances (instance_id, instance_name, server_name, server_host, port, platform, minecraft_version, is_active, is_production, description) VALUES
    ('TOWER01', 'Eternal Tower Defense', 'hetzner-xeon', '135.181.212.169', 2171, 'paper', '1.21.8', true, true, 'Tower defense minigame'),
    ('EVO01', 'Evolution SMP', 'hetzner-xeon', '135.181.212.169', 2172, 'paper', '1.21.8', true, true, 'Modded server development'),
    ('DEV01', 'Development Server', 'hetzner-xeon', '135.181.212.169', 2173, 'paper', '1.21.8', true, false, 'Testing environment'),
    ('MINI01', 'Minigames Server', 'hetzner-xeon', '135.181.212.169', 2174, 'paper', '1.21.8', true, true, 'General minigames'),
    ('BIGG01', 'BiggerGAMES', 'hetzner-xeon', '135.181.212.169', 2175, 'paper', '1.21.8', true, true, 'Extended minigames collection'),
    ('FORT01', 'Battle Royale', 'hetzner-xeon', '135.181.212.169', 2176, 'paper', '1.21.8', true, true, 'Fortnite-style battle royale'),
    ('PRIV01', 'Private Worlds', 'hetzner-xeon', '135.181.212.169', 2177, 'paper', '1.21.8', true, true, 'Private server worlds'),
    ('SMP101', 'Archive SMP Season 1', 'hetzner-xeon', '135.181.212.169', 2178, 'paper', '1.21.8', true, true, 'SMP Season 1 instance');

-- ============================================================================
-- Verify
-- ============================================================================

SELECT 'Instances Populated' AS status;
SELECT COUNT(*) AS total_instances FROM instances;
SELECT server_name, COUNT(*) AS instance_count 
FROM instances
GROUP BY server_name;
SELECT instance_id, instance_name, server_name, port, platform
FROM instances
ORDER BY server_name, port;
