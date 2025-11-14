# VillagerOptimizer - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## General

`config-version` = 1.0

## Gameplay

`gameplay.level-optimized-profession.level-check-cooldown-seconds` = 5

`gameplay.level-optimized-profession.notify-player` = true

`gameplay.outline-optimized-villagers.enable` = false

`gameplay.prevent-damage-to-optimized.damage-causes-to-cancel` = ['BLOCK_EXPLOSION', 'CAMPFIRE', 'CONTACT', 'CRAMMING', 'CUSTOM', 'DRAGON_BREATH', 'DROWNING', 'DRYOUT', 'ENTITY_ATTACK', 'ENTITY_EXPLOSION', 'ENTITY_SWEEP_ATTACK', 'FALL', 'FALLING_BLOCK', 'FIRE', 'FIRE_TICK', 'FLY_INTO_WALL', 'FREEZE', 'HOT_FLOOR', 'KILL', 'LAVA', 'LIGHTNING', 'MAGIC', 'MELTING', 'POISON', 'PROJECTILE', 'SONIC_BOOM', 'STARVATION', 'SUFFOCATION', 'SUICIDE', 'THORNS', 'VOID', 'WITHER', 'WORLD_BORDER']

`gameplay.prevent-damage-to-optimized.enable` = true

`gameplay.prevent-damage-to-optimized.prevent-knockback-from-entity` = true

`gameplay.prevent-entities-from-targeting-optimized.enable` = true

`gameplay.prevent-trading-with-unoptimized.enable` = false

`gameplay.prevent-trading-with-unoptimized.notify-player` = true

`gameplay.rename-optimized-villagers.enable` = false

`gameplay.restock-optimized-trades.delay-in-ticks` = 1000

`gameplay.restock-optimized-trades.log` = false

`gameplay.restock-optimized-trades.notify-player` = true

`gameplay.unoptimize-on-job-loose.enable` = true

`gameplay.villagers-can-be-leashed.enable` = false

`gameplay.villagers-can-be-leashed.log` = false

`gameplay.villagers-can-be-leashed.only-optimized` = false

`gameplay.villagers-spawn-as-adults.enable` = false

## General

`general.auto-language` = true

`general.cache-keep-time-seconds` = 30

`general.default-language` = "en_us"

`general.support-avl-villagers` = false

## Optimization-Methods

`optimization-methods.block-optimization.enable` = false

`optimization-methods.block-optimization.log` = false

`optimization-methods.block-optimization.materials` = ['LAPIS_BLOCK', 'GLOWSTONE', 'IRON_BLOCK']

`optimization-methods.block-optimization.notify-player` = true

`optimization-methods.block-optimization.only-when-sneaking` = true

`optimization-methods.block-optimization.optimize-cooldown-seconds` = 600

`optimization-methods.block-optimization.search-radius-in-blocks` = 2.0

`optimization-methods.commands.optimizevillagers.cooldown-seconds` = 600

`optimization-methods.commands.optimizevillagers.max-block-radius` = 100

`optimization-methods.commands.unoptimizevillagers.max-block-radius` = 100

`optimization-methods.nametag-optimization.enable` = true

`optimization-methods.nametag-optimization.log` = false

`optimization-methods.nametag-optimization.notify-player` = true

`optimization-methods.nametag-optimization.optimize-cooldown-seconds` = 600

`optimization-methods.workstation-optimization.check-linger-duration-ticks` = 100

`optimization-methods.workstation-optimization.enable` = false

`optimization-methods.workstation-optimization.log` = false

`optimization-methods.workstation-optimization.notify-player` = true

`optimization-methods.workstation-optimization.only-when-sneaking` = true

`optimization-methods.workstation-optimization.optimize-cooldown-seconds` = 600

`optimization-methods.workstation-optimization.search-radius-in-blocks` = 2.0

## Villager-Chunk-Limit

`villager-chunk-limit.check-period-in-ticks` = 600

`villager-chunk-limit.chunk-check-cooldown-seconds` = 5

`villager-chunk-limit.enable` = false

`villager-chunk-limit.log-removals` = true

`villager-chunk-limit.optimized.max-per-chunk` = 60

`villager-chunk-limit.optimized.removal-priority` = ['NONE', 'NITWIT', 'SHEPHERD', 'FISHERMAN', 'BUTCHER', 'CARTOGRAPHER', 'LEATHERWORKER', 'FLETCHER', 'MASON', 'FARMER', 'ARMORER', 'TOOLSMITH', 'WEAPONSMITH', 'CLERIC', 'LIBRARIAN']

`villager-chunk-limit.skip-not-fully-loaded-chunks` = true

`villager-chunk-limit.unoptimized.max-per-chunk` = 20

`villager-chunk-limit.unoptimized.removal-priority` = ['NONE', 'NITWIT', 'SHEPHERD', 'FISHERMAN', 'BUTCHER', 'CARTOGRAPHER', 'LEATHERWORKER', 'FLETCHER', 'MASON', 'FARMER', 'ARMORER', 'TOOLSMITH', 'WEAPONSMITH', 'CLERIC', 'LIBRARIAN']

`villager-chunk-limit.whitelist.enable` = false

`villager-chunk-limit.whitelist.professions` = ['NONE', 'NITWIT']

