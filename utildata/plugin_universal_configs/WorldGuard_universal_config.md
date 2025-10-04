# WorldGuard - Universal Configuration

These settings are **identical across all applicable Paper 1.21.8 servers** that use this plugin.

## General

`auto-invincible` = false

`auto-invincible-group` = false

`auto-no-drowning-group` = false

`custom-metrics-charts` = true

`disable-permission-cache` = false

`op-permissions` = true

`summary-on-start` = true

`use-particle-effects` = true

`use-player-move-event` = true

`use-player-teleports` = true

## Blacklist

`blacklist.logging.console.enable` = true

`blacklist.logging.database.dsn` = "jdbc:mysql://localhost:3306/minecraft"

`blacklist.logging.database.enable` = false

`blacklist.logging.database.pass` = ""

`blacklist.logging.database.table` = "blacklist_events"

`blacklist.logging.database.user` = "root"

`blacklist.logging.file.enable` = false

`blacklist.logging.file.open-files` = 10

`blacklist.logging.file.path` = "worldguard/logs/%Y-%m-%d.log"

`blacklist.use-as-whitelist` = false

## Build-Permission-Nodes

`build-permission-nodes.deny-message` = "&eSorry, but you are not permitted to do that here."

`build-permission-nodes.enable` = false

## Crops

`crops.disable-creature-trampling` = true

`crops.disable-player-trampling` = false

## Default

`default.disable-health-regain` = false

`default.pumpkin-scuba` = false

## Dynamics

`dynamics.disable-copper-block-fade` = false

`dynamics.disable-coral-block-fade` = false

`dynamics.disable-crop-growth` = false

`dynamics.disable-grass-growth` = false

`dynamics.disable-ice-formation` = false

`dynamics.disable-ice-melting` = false

`dynamics.disable-leaf-decay` = false

`dynamics.disable-mushroom-spread` = false

`dynamics.disable-mycelium-spread` = false

`dynamics.disable-rock-growth` = false

`dynamics.disable-sculk-growth` = false

`dynamics.disable-snow-formation` = false

`dynamics.disable-snow-melting` = false

`dynamics.disable-soil-dehydration` = false

`dynamics.disable-soil-moisture-change` = false

`dynamics.disable-vine-growth` = false

`dynamics.snow-fall-blocks` = []

## Event-Handling

`event-handling.block-entity-spawns-with-untraceable-cause` = false

`event-handling.break-hoppers-on-denied-move` = true

`event-handling.emit-block-use-at-feet` = []

`event-handling.ignore-hopper-item-move-events` = false

`event-handling.interaction-whitelist` = []

## Fire

`fire.disable-all-fire-spread` = false

`fire.disable-fire-spread-blocks` = []

`fire.disable-lava-fire-spread` = false

`fire.lava-spread-blocks` = []

## Gameplay

`gameplay.block-potions` = []

`gameplay.block-potions-overly-reliably` = false

`gameplay.disable-conduit-effects` = false

## Ignition

`ignition.block-lighter` = false

`ignition.block-tnt` = false

`ignition.block-tnt-block-damage` = false

## Mobs

`mobs.allow-tamed-spawns` = true

`mobs.anti-wolf-dumbness` = false

`mobs.block-above-ground-slimes` = false

`mobs.block-armor-stand-destroy` = false

`mobs.block-creature-spawn` = []

`mobs.block-creeper-block-damage` = true

`mobs.block-creeper-explosions` = false

`mobs.block-enderdragon-block-damage` = false

`mobs.block-enderdragon-portal-creation` = false

`mobs.block-fireball-block-damage` = false

`mobs.block-fireball-explosions` = false

`mobs.block-item-frame-destroy` = false

`mobs.block-other-explosions` = false

`mobs.block-painting-destroy` = false

`mobs.block-plugin-spawning` = true

`mobs.block-vehicle-entry` = false

`mobs.block-windcharge-explosions` = false

`mobs.block-wither-block-damage` = true

`mobs.block-wither-explosions` = false

`mobs.block-wither-skull-block-damage` = true

`mobs.block-wither-skull-explosions` = false

`mobs.block-zombie-door-destruction` = false

`mobs.disable-enderman-griefing` = true

`mobs.disable-snowman-trails` = false

## Physics

`physics.allow-portal-anywhere` = false

`physics.disable-water-damage-blocks` = []

`physics.no-physics-gravel` = false

`physics.no-physics-sand` = false

`physics.vine-like-rope-ladders` = false

## Player-Damage

`player-damage.disable-contact-damage` = false

`player-damage.disable-death-messages` = false

`player-damage.disable-drowning-damage` = false

`player-damage.disable-explosion-damage` = false

`player-damage.disable-fall-damage` = false

`player-damage.disable-fire-damage` = false

`player-damage.disable-lava-damage` = false

`player-damage.disable-lightning-damage` = false

`player-damage.disable-mob-damage` = false

`player-damage.disable-suffocation-damage` = false

`player-damage.disable-void-damage` = false

`player-damage.reset-fall-on-void-teleport` = false

`player-damage.teleport-on-suffocation` = false

`player-damage.teleport-on-void-falling` = false

## Protection

`protection.disable-xp-orb-drops` = false

`protection.item-durability` = true

`protection.remove-infinite-stacks` = false

`protection.use-max-priority-association` = false

## Regions

`regions.announce-bypass-status` = false

`regions.cancel-chat-without-recipients` = true

`regions.claim-only-inside-existing-regions` = false

`regions.disable-bypass-by-default` = false

`regions.enable` = true

`regions.explosion-flags-block-entity-damage` = true

`regions.fake-player-build-override` = true

`regions.high-frequency-flags` = false

`regions.invincibility-removes-mobs` = false

`regions.location-flags-only-inside-regions` = false

`regions.max-claim-volume` = 30000

`regions.max-region-count-per-player.default` = 7

`regions.nether-portal-protection` = true

`regions.protect-against-liquid-flow` = false

`regions.set-parent-on-claim` = ""

`regions.use-creature-spawn-event` = true

`regions.use-paper-entity-origin` = false

`regions.uuid-migration.keep-names-that-lack-uuids` = true

`regions.uuid-migration.perform-on-next-start` = false

`regions.wand` = "minecraft:leather"

## Security

`security.block-in-game-op-command` = false

`security.deop-everyone-on-join` = false

`security.host-keys-allow-forge-clients` = false

## Sniffer-Egg

`sniffer-egg.disable-creature-trampling` = false

`sniffer-egg.disable-player-trampling` = false

## Turtle-Egg

`turtle-egg.disable-creature-trampling` = false

`turtle-egg.disable-player-trampling` = false

## Weather

`weather.always-raining` = false

`weather.always-thundering` = false

`weather.disable-lightning-strike-fire` = false

`weather.disable-pig-zombification` = false

`weather.disable-powered-creepers` = false

`weather.disable-thunderstorm` = false

`weather.disable-villager-witchification` = false

`weather.disable-weather` = false

`weather.prevent-lightning-strike-blocks` = []

