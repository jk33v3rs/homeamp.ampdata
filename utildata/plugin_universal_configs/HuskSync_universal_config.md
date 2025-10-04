# HuskSync - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## General

`cancel_packets` = true

`check_for_updates` = true

`debug_logging` = false

`disabled_commands` = []

`enable_plan_hook` = true

`language` = "en-gb"

## Database

`database.connection_pool.connection_timeout` = 5000

`database.connection_pool.keepalive_time` = 0

`database.connection_pool.maximum_lifetime` = 1800000

`database.connection_pool.maximum_pool_size` = 10

`database.connection_pool.minimum_idle` = 10

`database.create_tables` = true

`database.credentials.database` = "asmp_SQL"

`database.credentials.host` = "135.181.212.169"

`database.credentials.parameters` = "?autoReconnect=true&useSSL=false&useUnicode=true&characterEncoding=UTF-8"

`database.credentials.password` = "SQLdb2024!"

`database.credentials.port` = 3369

`database.credentials.username` = "sqlworkerSMP"

`database.mongo_settings.parameters` = "?retryWrites=true&w=majority&authSource=HuskSync"

`database.mongo_settings.using_atlas` = false

## Redis

`redis.credentials.database` = 0

`redis.credentials.host` = "135.181.212.169"

`redis.credentials.password` = "Fartp0wer69!"

`redis.credentials.port` = 6379

`redis.credentials.use_ssl` = false

`redis.credentials.user` = "default"

`redis.sentinel.master` = ""

`redis.sentinel.nodes` = []

`redis.sentinel.password` = ""

## Synchronization

`synchronization.attributes.ignored_modifiers` = ['minecraft:effect.*', 'minecraft:creative_mode_*']

`synchronization.attributes.synced_attributes` = ['minecraft:generic.max_health', 'minecraft:max_health', 'minecraft:generic.max_absorption', 'minecraft:max_absorption', 'minecraft:generic.luck', 'minecraft:luck', 'minecraft:generic.scale', 'minecraft:scale', 'minecraft:generic.step_height', 'minecraft:step_height', 'minecraft:generic.gravity', 'minecraft:gravity']

`synchronization.auto_pinned_save_causes` = ['INVENTORY_COMMAND', 'ENDERCHEST_COMMAND', 'BACKUP_RESTORE', 'LEGACY_MIGRATION', 'MPDB_MIGRATION']

`synchronization.blacklisted_commands_while_locked` = ['*']

`synchronization.checkin_petitions` = false

`synchronization.compress_data` = true

`synchronization.event_priorities.death_listener` = "NORMAL"

`synchronization.event_priorities.join_listener` = "LOWEST"

`synchronization.event_priorities.quit_listener` = "LOWEST"

`synchronization.features.advancements` = true

`synchronization.features.attributes` = true

`synchronization.features.ender_chest` = true

`synchronization.features.experience` = true

`synchronization.features.flight_status` = true

`synchronization.features.game_mode` = true

`synchronization.features.health` = true

`synchronization.features.hunger` = true

`synchronization.features.inventory` = true

`synchronization.features.location` = true

`synchronization.features.persistent_data` = true

`synchronization.features.potion_effects` = true

`synchronization.features.statistics` = true

`synchronization.max_user_data_snapshots` = 32

`synchronization.mode` = "LOCKSTEP"

`synchronization.network_latency_milliseconds` = 500

`synchronization.notification_display_slot` = "ACTION_BAR"

`synchronization.persist_locked_maps` = true

`synchronization.save_on_death.enabled` = true

`synchronization.save_on_death.items_to_save` = "DROPS"

`synchronization.save_on_death.save_empty_items` = false

`synchronization.save_on_death.sync_dead_players_changing_server` = true

`synchronization.save_on_world_save` = true

`synchronization.snapshot_backup_frequency` = 4

