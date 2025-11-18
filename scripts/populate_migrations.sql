-- Populate known config key migrations
USE asmp_config;

INSERT INTO config_key_migrations 
(plugin_name, old_key_path, new_key_path, from_version, to_version,
 migration_type, value_transform, is_breaking, is_automatic, notes,
 documentation_url, created_by)
VALUES
('ExcellentEnchants', 'enchants.*.id', 'enchantments.*.identifier', '4.x', '5.0.0', 'rename', NULL, TRUE, FALSE, 'Enchant ID system changed in 5.0.0. Causes "Unknown Enchantment" errors on existing items. Requires NBT data migration for player items.', 'https://github.com/nulli0n/ExcellentEnchants-spigot/wiki/Migration-Guide', 'initial_population'),

('BentoBox', 'challenges.*.challenge_id', 'challenges.*.identifier', '1.x', '2.0.0', 'rename', NULL, TRUE, FALSE, 'Challenge ID format changed. Player progress lost if not migrated properly. Requires database update.', NULL, 'initial_population'),

('HandsOffMyBook', 'hotmb.protect', 'handsoffmybook.protect', '1.x', '2.0.0', 'rename', NULL, TRUE, TRUE, 'Permission node format changed from hotmb.* to handsoffmybook.*', NULL, 'initial_population'),

('ResurrectionChest', 'expiry.timer', 'expiry.duration_seconds', '1.x', '2.0.0', 'type_change', 'int(x) * 60', TRUE, TRUE, 'Timer format changed from minutes to seconds. Old configs will expire 60x faster without migration.', NULL, 'initial_population'),

('JobListings', 'storage.type', 'database.enabled', '1.x', '2.0.0', 'remove', 'x == "file" -> False, x == "database" -> True', TRUE, FALSE, 'Storage migrated from config files to database. Old file-based jobs need manual import.', NULL, 'initial_population'),

('LevelledMobs', 'spawn-conditions.*.world', 'spawn-conditions.*.worlds', '3.x', '4.0.0', 'rename', '[x] if isinstance(x, str) else x', FALSE, TRUE, 'Single world string changed to list of worlds. Backward compatible but should migrate.', NULL, 'initial_population'),

('EliteMobs', 'ranks.*.min_level', 'ranks.*.minimum_level', '8.x', '9.0.0', 'rename', NULL, FALSE, TRUE, 'Cosmetic key rename for consistency. Old key still works but deprecated.', 'https://github.com/MagmaGuy/EliteMobs/wiki/Config-Migration', 'initial_population'),

('Pl3xMap', 'settings.zoom.default', 'settings.default-zoom', '1.x', '2.0.0', 'move', NULL, FALSE, TRUE, 'Config restructuring for better organization. Old structure deprecated.', 'https://github.com/pl3xgaming/Pl3xMap/wiki/Configuration', 'initial_population'),

('SimpleVoiceChat', 'port', 'voice_chat.port', '1.x', '2.0.0', 'move', NULL, TRUE, TRUE, 'Port config moved to nested structure. Voice chat will fail to bind without migration.', 'https://github.com/henkelmax/simple-voice-chat/wiki/Config-Migration', 'initial_population'),

('DiscordSRV', 'Experiment_WebhookChatMessageDelivery', 'UseWebhooksForChat', '1.x', '2.0.0', 'rename', NULL, FALSE, TRUE, 'Experimental feature graduated to stable. Old key still works.', NULL, 'initial_population');

-- Show summary
SELECT 
    migration_type,
    COUNT(*) as count,
    SUM(is_breaking) as breaking_count
FROM config_key_migrations
GROUP BY migration_type
ORDER BY count DESC;
