-- ============================================================================
-- Seed Data: Meta Tags and Categories
-- Populate initial classification system for instances
-- ============================================================================

USE asmp_config;

-- ============================================================================
-- META TAG CATEGORIES
-- ============================================================================

INSERT INTO meta_tag_categories (category_name, description, display_order) VALUES
    ('gameplay', 'Primary gameplay mode', 1),
    ('modding', 'Level of modification from vanilla', 2),
    ('intensity', 'Difficulty/competitiveness level', 3),
    ('economy', 'Economic system features', 4),
    ('combat', 'PvP/PvE configuration', 5),
    ('persistence', 'World reset behavior', 6);

-- ============================================================================
-- META TAGS (System Tags)
-- ============================================================================

-- Gameplay Tags
INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag) 
SELECT 'survival', category_id, 'Survival Mode', 'Standard survival gameplay', true
FROM meta_tag_categories WHERE category_name = 'gameplay';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'creative', category_id, 'Creative Mode', 'Creative building mode', true
FROM meta_tag_categories WHERE category_name = 'gameplay';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'minigame', category_id, 'Minigame', 'Minigame/arena server', true
FROM meta_tag_categories WHERE category_name = 'gameplay';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'utility', category_id, 'Utility', 'Hub/lobby/infrastructure', true
FROM meta_tag_categories WHERE category_name = 'gameplay';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'experimental', category_id, 'Experimental', 'Testing/development', true
FROM meta_tag_categories WHERE category_name = 'gameplay';

-- Modding Level Tags
INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'pure-vanilla', category_id, 'Pure Vanilla', 'No plugins, vanilla only', true
FROM meta_tag_categories WHERE category_name = 'modding';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'vanilla-ish', category_id, 'Vanilla-ish', 'Minimal quality-of-life plugins', true
FROM meta_tag_categories WHERE category_name = 'modding';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'lightly-modded', category_id, 'Lightly Modded', 'Standard plugin set', true
FROM meta_tag_categories WHERE category_name = 'modding';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'heavily-modded', category_id, 'Heavily Modded', 'Fabric mods, Origins, Create', true
FROM meta_tag_categories WHERE category_name = 'modding';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'barely-minecraft', category_id, 'Barely Minecraft', 'Heavily customized gameplay', true
FROM meta_tag_categories WHERE category_name = 'modding';

-- Intensity Tags
INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'casual', category_id, 'Casual', 'Relaxed, teleports allowed, keep inventory', true
FROM meta_tag_categories WHERE category_name = 'intensity';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'sweaty', category_id, 'Sweaty', 'Competitive, strict rules', true
FROM meta_tag_categories WHERE category_name = 'intensity';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'hardcore', category_id, 'Hardcore', 'Permadeath or harsh penalties', true
FROM meta_tag_categories WHERE category_name = 'intensity';

-- Economy Tags
INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'economy-enabled', category_id, 'Economy Enabled', 'Full economy system active', true
FROM meta_tag_categories WHERE category_name = 'economy';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'economy-disabled', category_id, 'Economy Disabled', 'No currency/shops', true
FROM meta_tag_categories WHERE category_name = 'economy';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'economy-creative', category_id, 'Creative Economy', 'Limited economy in creative', true
FROM meta_tag_categories WHERE category_name = 'economy';

-- Combat Tags
INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'pvp-enabled', category_id, 'PvP Enabled', 'Player vs Player allowed', true
FROM meta_tag_categories WHERE category_name = 'combat';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'pvp-disabled', category_id, 'PvP Disabled', 'Peaceful, no PvP', true
FROM meta_tag_categories WHERE category_name = 'combat';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'pve-focused', category_id, 'PvE Focused', 'EliteMobs, dungeons, bosses', true
FROM meta_tag_categories WHERE category_name = 'combat';

-- Persistence Tags
INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'persistent', category_id, 'Persistent', 'World never resets', true
FROM meta_tag_categories WHERE category_name = 'persistence';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'resetting', category_id, 'Resetting', 'Periodic resets (weekly/monthly)', true
FROM meta_tag_categories WHERE category_name = 'persistence';

INSERT INTO meta_tags (tag_name, category_id, display_name, description, is_system_tag)
SELECT 'temporary', category_id, 'Temporary', 'Event-only, deleted after', true
FROM meta_tag_categories WHERE category_name = 'persistence';

-- ============================================================================
-- Verify
-- ============================================================================

SELECT 'Meta Tags Populated' AS status;
SELECT COUNT(*) AS total_categories FROM meta_tag_categories;
SELECT COUNT(*) AS total_tags FROM meta_tags;
SELECT category_name, COUNT(*) AS tag_count 
FROM meta_tags t
JOIN meta_tag_categories c ON t.category_id = c.category_id
GROUP BY category_name
ORDER BY c.display_order;
