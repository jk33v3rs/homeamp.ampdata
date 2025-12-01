-- ============================================================================
-- Seed Data: Instance Groups
-- Physical, Logical, and Administrative groupings
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- INSTANCE GROUPS
-- ============================================================================

-- Physical Groups (server hardware clustering)
INSERT INTO instance_groups (group_name, group_type, description) VALUES
    ('hetzner-cluster', 'physical', 'All instances on Hetzner Xeon server'),
    ('ovh-cluster', 'physical', 'All instances on OVH Ryzen server');

-- Logical Groups (gameplay mode clustering)
INSERT INTO instance_groups (group_name, group_type, description) VALUES
    ('survival-servers', 'logical', 'Survival gameplay mode servers'),
    ('creative-servers', 'logical', 'Creative building mode servers'),
    ('minigame-servers', 'logical', 'Minigame and event servers'),
    ('utility-servers', 'logical', 'Hub, proxy, and infrastructure servers');

-- Administrative Groups (operational state)
INSERT INTO instance_groups (group_name, group_type, description) VALUES
    ('production', 'administrative', 'Live production servers'),
    ('development', 'administrative', 'Development and testing servers');

-- ============================================================================
-- INSTANCE GROUP MEMBERS
-- ============================================================================

-- Physical: Hetzner Cluster
INSERT INTO instance_group_members (group_id, instance_id) VALUES
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'TOWER01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'EVO01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'DEV01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'MINI01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'BIGG01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'FORT01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'PRIV01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'hetzner-cluster'), 'SMP101');

-- Physical: OVH Cluster
INSERT INTO instance_group_members (group_id, instance_id) VALUES
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'CLIP01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'CSMC01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'EMAD01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'BENT01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'HCRE01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'SMP201'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'HUB01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'MINT01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'CREA01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'GEY01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'ovh-cluster'), 'VEL01');

-- Logical: Survival Servers
INSERT INTO instance_group_members (group_id, instance_id) VALUES
    ((SELECT group_id FROM instance_groups WHERE group_name = 'survival-servers'), 'SMP101'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'survival-servers'), 'SMP201'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'survival-servers'), 'CLIP01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'survival-servers'), 'HCRE01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'survival-servers'), 'EMAD01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'survival-servers'), 'BENT01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'survival-servers'), 'EVO01');

-- Logical: Creative Servers
INSERT INTO instance_group_members (group_id, instance_id) VALUES
    ((SELECT group_id FROM instance_groups WHERE group_name = 'creative-servers'), 'CREA01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'creative-servers'), 'PRIV01');

-- Logical: Minigame Servers
INSERT INTO instance_group_members (group_id, instance_id) VALUES
    ((SELECT group_id FROM instance_groups WHERE group_name = 'minigame-servers'), 'MINI01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'minigame-servers'), 'BIGG01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'minigame-servers'), 'FORT01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'minigame-servers'), 'TOWER01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'minigame-servers'), 'CSMC01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'minigame-servers'), 'MINT01');

-- Logical: Utility Servers
INSERT INTO instance_group_members (group_id, instance_id) VALUES
    ((SELECT group_id FROM instance_groups WHERE group_name = 'utility-servers'), 'HUB01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'utility-servers'), 'VEL01'),
    ((SELECT group_id FROM instance_groups WHERE group_name = 'utility-servers'), 'GEY01');

-- Administrative: Production
INSERT INTO instance_group_members (group_id, instance_id)
SELECT 
    (SELECT group_id FROM instance_groups WHERE group_name = 'production'),
    instance_id
FROM instances
WHERE is_production = true;

-- Administrative: Development
INSERT INTO instance_group_members (group_id, instance_id)
SELECT 
    (SELECT group_id FROM instance_groups WHERE group_name = 'development'),
    instance_id
FROM instances
WHERE is_production = false;

-- ============================================================================
-- Verify
-- ============================================================================

SELECT 'Instance Groups Populated' AS status;
SELECT COUNT(*) AS total_groups FROM instance_groups;
SELECT group_name, group_type, COUNT(igm.instance_id) AS member_count
FROM instance_groups ig
LEFT JOIN instance_group_members igm ON ig.group_id = igm.group_id
GROUP BY ig.group_id, group_name, group_type
ORDER BY group_type, group_name;
