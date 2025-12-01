# Plugin Analysis Notes - Experience Continuity Requirements
## Systematic Documentation for Schema Design

**Purpose**: Document EVERY plugin's dual perspectives:
1. **Cross-Server Mechanics** - What breaks or becomes complex when instances talk to each other
2. **Version Control Nightmare** - What happens when discrete copies drift or upgrade separately

**Rule**: Minimum 2 examples per plugin showing both perspectives understood

---

## HuskSync (Cross-Server Player Data Sync)

**What it syncs**:
- Inventories, ender chests, health, hunger, attributes, XP, potion effects
- Advancements, recipes, game mode, flight status, statistics
- Location (if mirrored worlds), persistent data container (custom plugin data)
- Locked maps (special handling - saves pixel canvas to NBT)

**What it explicitly does NOT sync**:
- Unlocked maps (world-file based, can't track across instances)
- Economy balances (recommends cross-server economy plugins instead)

**Key insight**: HuskSync is the FOUNDATION - it handles the "simple" item/NBT sync. Everything ELSE is what we need to manage.

**Configuration toggle per feature**: Each sync feature can be enabled/disabled per synchronization type in config.yml

---

## 1. LuckPerms (Permissions & Ranks)

### Cross-Server Perspective:
- **Problem 1**: Rank on SMP101 should = rank on DEV01, but some perms are instance-specific (creative mode access, worldedit limits)
- **Problem 2**: Context-based permissions - "you can fly in creative world but not survival world" - but creative world exists on 3 different instances

### Version Control Nightmare:
- **Problem 1**: LuckPerms 5.4.145 on SMP101, upgrade to 5.5.x on DEV01 for testing - now permission inheritance calculations might differ
- **Problem 2**: Someone edits default group on Hetzner via /lp, someone else edits on OVH via web editor - which wins? Last write? We need conflict detection.

---

## 2. CoreProtect (Rollback & Logging)

### Cross-Server Perspective:
- **Problem 1**: Player griefs on SMP101, gets banned, joins DEV01 before ban syncs - CoreProtect logs are per-instance, can't correlate player actions network-wide
- **Problem 2**: Rollback "undo player X's last 24 hours" but they played on 3 instances - need cross-instance rollback coordination

### Version Control Nightmare:
- **Problem 1**: CoreProtect 23.2 logs format vs 24.x format - if instances have different versions, log aggregation breaks
- **Problem 2**: Database schema changes between versions - can't query "all breaks of diamond ore network-wide" if schema differs per instance

---

## 3. WorldEdit & WorldGuard (Building & Protection)

### Cross-Server Perspective:
- **Problem 1**: Region "spawn" on SMP101 with flag `pvp: deny` - if we have mirrored coordinates, does same region exist on DEV01? Should it have same flags?
- **Problem 2**: WorldEdit clipboard - player copies build on creative server, can they paste on survival? Cross-instance clipboard sync?

### Version Control Nightmare:
- **Problem 1**: WorldEdit 7.3.11 schematic format vs 7.2.x - if player saves schematic on instance A, loads on instance B with older version, schematic corrupts
- **Problem 2**: WorldGuard region flags gain new options in 7.1.x - old instances don't recognize new flags, protection becomes inconsistent

---

## 4. CMI & CMILib (Multi-Purpose Utility)

### Cross-Server Perspective:
- **Problem 1**: Player sets /sethome on SMP101, teleports to DEV01, runs /home - should it cross-server teleport? Or error "home not on this server"?
- **Problem 2**: Kits - player claims starter kit on SMP101, switches to DEV01 - should kit cooldown be network-wide or per-instance?

### Version Control Nightmare:
- **Problem 1**: CMI 9.7.14.2 on one instance, 9.8.x on another - config.yml structure changes, our parser breaks trying to normalize
- **Problem 2**: CMI stores player data in SQLite - if schema differs between versions, data corruption when player switches instances mid-session

---

## 5. PlaceholderAPI (PAPI - Variable System)

### Cross-Server Perspective:
- **Problem 1**: Placeholder `%player_balance%` - if economy is cross-server, all instances must return same value, but if local economies, needs instance context
- **Problem 2**: `%server_online%` - should this be "players on THIS instance" or "players network-wide"? Depends on placeholder usage context

### Version Control Nightmare:
- **Problem 1**: PAPI 2.11.6 adds new placeholder, expansion depends on it - instances with older PAPI show error instead of value
- **Problem 2**: eCloud expansion versions - one instance has outdated expansion, placeholder returns wrong format, breaks scoreboard displays

---

## 6. QuickShop-Hikari (Player Shops)

### Cross-Server Perspective:
- **Problem 1**: Player creates shop on SMP101 selling diamonds - can players on DEV01 see/buy from it? Network-wide shop discovery vs local-only?
- **Problem 2**: Shop stock sync - if network-wide, buying on one instance must decrement stock everywhere in real-time

### Version Control Nightmare:
- **Problem 1**: QS 6.2.0.9 on SMP101, 6.3.x on DEV01 - database schema for shops changes, shop data corrupts when player accesses from different instance
- **Problem 2**: Addon compatibility - Addon-Discount 6.2.x works on one instance, 6.3.x on another - discount calculations differ, players exploit price differences

---

## 7. EliteMobs (Boss & Custom Items)

### Cross-Server Perspective:
- **Problem 1**: Boss spawns on SMP101, drops custom sword with elite enchants - player takes to DEV01 - do elite enchants still work? Need cross-instance item registry sync
- **Problem 2**: Boss kill quests "kill 10 zombie kings" - if bosses span across instances, quest progress must aggregate, but boss spawn rates differ per instance

### Version Control Nightmare:
- **Problem 1**: EliteMobs 9.4.2 elite enchant IDs vs 9.5.x - enchant ID mapping changes, items from old instance show "Unknown Enchant" on new instance
- **Problem 2**: Custom model data for boss items - if resource pack version differs per instance, items look broken/invisible when transferred

---

## 8. mcMMO (Skills & Levels)

### Cross-Server Perspective:
- **Problem 1**: Mining skill level 500 on SMP101 - does that level persist to DEV01? (Yes via HuskSync persistent data) - but XP gain rates might differ per instance config
- **Problem 2**: Party system - players in mcMMO party across instances - shared XP must sync real-time, but instances have different tick rates/lag

### Version Control Nightmare:
- **Problem 1**: mcMMO 1.4.06 skill cap vs 2.x.x - skill cap increases, players on old instance hit cap, transfer to new instance, suddenly have room to level - exploitable
- **Problem 2**: Ability cooldowns stored in player data - format changes between versions, cooldowns reset or become permanent when switching instances

---

## 9. LevelledMobs (Mob Scaling)

### Cross-Server Perspective:
- **Problem 1**: Mob levels based on distance from spawn - spawn is 0,0 on SMP101 but 1000,1000 on DEV01 - same coordinates = different mob levels per instance
- **Problem 2**: Custom drops from levelled mobs - level 50 zombie drops rare item on SMP101, player takes to DEV01 where level 50 = common - item value inconsistency

### Version Control Nightmare:
- **Problem 1**: LevelledMobs 4.3.x leveling formula vs 4.4.x - formula changes, mob at X,Y,Z is level 30 on one instance, level 45 on another with same config
- **Problem 2**: rules.yml structure change - old instance uses `strategies:` new instance uses `level-modifiers:` - can't apply same config to both

---

## 10. Jobs Reborn (Job System)

### Cross-Server Perspective:
- **Problem 1**: Player is Miner level 20 on SMP101 earning $5/ore - switches to DEV01 - is still level 20 but DEV01 pays $10/ore for testing - exploitable
- **Problem 2**: Daily quests "mine 500 stone" - should stone mined on ANY instance count? Or per-instance isolated quests?

### Version Control Nightmare:
- **Problem 1**: Jobs 5.2.6.0 job config IDs vs 5.3.x - job IDs change, player data references old ID, player loses all job progress on instance upgrade
- **Problem 2**: New job actions added in 5.3.x (sculk mining, etc.) - old instances don't recognize action, don't pay, inconsistent earnings per instance

---

## 11. CommunityQuests (Global Challenges)

### Cross-Server Perspective:
- **Problem 1**: "Everyone collect 10,000 stone NETWORK-WIDE" - must aggregate stone from all instances, all dimensions, all worlds in real-time
- **Problem 2**: Quest completion rewards - if quest completes on SMP101, do players on DEV01 get notified? Do they get rewards on next login?

### Version Control Nightmare:
- **Problem 1**: CommunityQuests 2.11.5 quest format vs 3.x.x - quest file structure changes, can't deploy same quest config to all instances
- **Problem 2**: Reward items with NBT - if EliteMobs versions differ, reward item NBT format incompatible, rewards break cross-instance

---

## 12. Chunky & ChunkyBorder (World Pre-Generation)

### Cross-Server Perspective:
- **Problem 1**: World border at 10k radius on SMP101, 5k on DEV01 (smaller for testing) - player near edge on SMP switches to DEV, spawns outside border, dies
- **Problem 2**: Pre-gen task running on SMP101, high TPS impact - if player switches to DEV01, do they experience lag from remote pre-gen task?

### Version Control Nightmare:
- **Problem 1**: Chunky 1.4.36 chunk format vs 1.5.x - pre-gen on one instance with new format, chunks don't load correctly on instance with old version
- **Problem 2**: Border shape changes (square vs circle) - border.json format incompatible between versions, border resets on instance upgrade

---

## 13. Citizens (NPC System)

### Cross-Server Perspective:
- **Problem 1**: Quest NPC on SMP101 tracks player completion - player talks to "same" NPC on DEV01 (different entity, same name) - does quest state sync?
- **Problem 2**: Shop NPC sells items - stock depletes on SMP101 - does same NPC on DEV01 have separate stock or shared stock?

### Version Control Nightmare:
- **Problem 1**: Citizens 2.0.38 NPC save format vs 2.1.x - NPC data incompatible, copying NPC config from one instance to another corrupts NPCs
- **Problem 2**: Trait system changes - old instance has "sentinel" trait, new instance renames to "combat" - NPC behaviors break after instance upgrade

---

## 14. Vault (Economy API)

### Cross-Server Perspective:
- **Problem 1**: Vault balance - is it a local wrapper for cross-server economy (TNE) or local per-instance balance? Plugins querying Vault get different answers per instance
- **Problem 2**: Permission check via Vault - some perms are cross-server (rank), some are local (worldedit limits) - Vault can't distinguish, returns wrong answer

### Version Control Nightmare:
- **Problem 1**: Vault 2.10.0 vs VaultUnlocked - API differences, plugins coded for one version crash on instance with other version
- **Problem 2**: Economy provider changes (switch from Essentials to TNE) - Vault balance lookup method changes, old configs reference wrong provider

---

## 15. TheNewEconomy (TNE - Cross-Server Economy)

### Cross-Server Perspective:
- **Problem 1**: THIS IS THE SOLUTION for cross-server economy, but configuration must match EXACTLY across instances or balance queries desync
- **Problem 2**: Currency types - if TNE config defines "gems" currency on SMP101 but not on DEV01, player with gems can't spend them there

### Version Control Nightmare:
- **Problem 1**: TNE 0.1.3.4 currency UUID vs 0.2.x - currency identification changes, player balances lost on instance upgrade
- **Problem 2**: Transaction logging format - old instance logs to flat file, new instance to database - can't aggregate transaction history network-wide

---

## 16. HuskTowns (Territory System)

### Cross-Server Perspective:
- **Problem 1**: Town claims - if coordinates are mirrored, town claim at X,Z on SMP101 should exist at X,Z on DEV01 - but what if world shapes differ?
- **Problem 2**: Town bank balance - shared across instances or separate per instance? If shared, must sync in real-time to prevent duplication exploits

### Version Control Nightmare:
- **Problem 1**: HuskTowns version mismatch - claim data schema changes, claims become corrupted when player accesses from different instance version
- **Problem 2**: Level system for towns - level requirements change in update, town loses perks or gains perks unexpectedly when instance upgrades

---

## 17. BetterStructures (Custom Structures)

### Cross-Server Perspective:
- **Problem 1**: Custom structure spawns in SMP101 world gen - if DEV01 has different BetterStructures config, same seed generates different structures, worlds not mirrored
- **Problem 2**: Structure loot tables - rare item in structure on SMP101, player takes to DEV01 where loot tables differ, item value inconsistency

### Version Control Nightmare:
- **Problem 1**: BetterStructures 1.8.1 structure format vs 1.9.x - structure files incompatible, updating one instance breaks structure spawning until all updated
- **Problem 2**: Weight/spawn chance changes - structure that's common in 1.8.x becomes rare in 1.9.x, world generation differs per instance version

---

## 18. Pl3xMap (Web Map)

### Cross-Server Perspective:
- **Problem 1**: Map tiles generated per instance - if worlds are mirrored, tiles should match, but if generation differs, map shows different terrain for "same" world
- **Problem 2**: Player markers - should map show players across all instances or just current instance? Need network-wide player location aggregation

### Version Control Nightmare:
- **Problem 1**: Pl3xMap 1.21.4-525 tile format vs newer - old tiles don't render correctly with new web UI, map appears broken until all tiles regenerated
- **Problem 2**: Config options for renderers - new instance has new renderer features, config can't be copied to old instance without errors

---

## 19. ExcellentEnchants (Custom Enchantments)

### Cross-Server Perspective:
- **Problem 1**: Custom enchant "Explosive Arrows" on item - enchant behavior must be identical across instances or arrow damage differs per instance
- **Problem 2**: Enchant conflicts - some enchants incompatible with vanilla enchants - if rules differ per instance, item becomes unenchantable when transferred

### Version Control Nightmare:
- **Problem 1**: ExcellentEnchants 5.0.0 enchant IDs vs 4.x - enchant ID mapping changes, items show "Unknown Enchantment" when moved between instance versions
- **Problem 2**: Enchant tier/level caps - new version increases cap from V to X, items with level X created on new instance, crash old instance parser

---

## 20. Lootin (Loot Chest Refresh)

### Cross-Server Perspective:
- **Problem 1**: Loot chest at X,Y,Z refreshes on SMP101 - if mirrored to DEV01, does chest at same coords also refresh? Or independent refresh timers?
- **Problem 2**: Player loots chest on SMP101, switches to DEV01, loots "same" chest again - if chest state isn't synced, can farm loot by instance hopping

### Version Control Nightmare:
- **Problem 1**: Lootin 12.1 chest data storage vs 13.x - chest refresh timers stored differently, upgrading instance resets all chest timers
- **Problem 2**: Loot table format changes - custom loot tables written for 12.x don't parse correctly in 13.x, chests give wrong loot

---

## 21. ProtocolLib (Packet Manipulation)

### Cross-Server Perspective:
- **Problem 1**: Other plugins depend on ProtocolLib for packet modification - if ProtocolLib version differs per instance, packet behavior differs, player experience inconsistent
- **Problem 2**: Client-side prediction - packet manipulation affects player movement/combat - if rules differ per instance, combat feels different per server

### Version Control Nightmare:
- **Problem 1**: ProtocolLib 5.3.0 API vs 5.4.x - breaking API changes, plugins compiled against 5.3.x crash on instance with 5.4.x
- **Problem 2**: Minecraft version support - 5.3.0 supports 1.21.1, 5.4.x adds 1.21.4 - instances on different MC versions need different ProtocolLib, plugins break

---

## 22. Quests (Questing Plugin)

### Cross-Server Perspective:
- **Problem 1**: Quest "talk to NPC Bob" - Bob exists on SMP101, player accepts quest, switches to DEV01 where Bob doesn't exist - quest can't be completed
- **Problem 2**: Quest objectives "kill 50 zombies" - should kills on any instance count? Or quest locked to instance where accepted?

### Version Control Nightmare:
- **Problem 1**: Quests plugin version changes quest data format - player has active quest on one instance, quest data corrupts when switching to instance with different version
- **Problem 2**: Reward items with custom NBT - if item format changes between versions, quest rewards become unclaimable or give wrong items

---

## 23. TreeFeller (Tree Cutting)

### Cross-Server Perspective:
- **Problem 1**: TreeFeller breaks entire tree - if enabled on SMP101 but disabled on DEV01 (for building server), player confusion about why feature works differently
- **Problem 2**: Tool damage from TreeFeller - if enabled, axe durability drains faster - if config differs per instance, tool lifespan inconsistent

### Version Control Nightmare:
- **Problem 1**: TreeFeller 1.26.1 tree detection vs 1.27.x - algorithm changes, trees that felled in one version don't in another, player reports "plugin broken"
- **Problem 2**: Config option name changes - `auto-replant` becomes `replant.enabled` - automated config updates break when version mismatch

---

## 24. VillagerOptimiser (Performance)

### Cross-Server Perspective:
- **Problem 1**: Villager AI optimizations differ per instance - trading experience different (faster/slower pathfinding) per instance
- **Problem 2**: Villager restocking times - if optimization changes restock speed, prices fluctuate differently per instance, economy inconsistency

### Version Control Nightmare:
- **Problem 1**: VillagerOptimiser 1.6.2 optimization method vs 1.7.x - behavior changes, villagers on updated instance act differently, players notice discrepancy
- **Problem 2**: Config for optimization levels - new version adds aggressive mode, old instance doesn't support, config can't be synchronized

---

## 25. WorldBorder (Border Management)

### Cross-Server Perspective:
- **Problem 1**: Border radius 10k on SMP101, 5k on DEV01 - player near edge transfers to DEV, spawns outside border, instant death
- **Problem 2**: Border fill task - pre-generating chunks to border - if task running on one instance causes lag, affects players on other instances via shared hardware

### Version Control Nightmare:
- **Problem 1**: WorldBorder 1.19 vs 2.x - border data format changes, border resets when instance upgrades, players lose access to previously accessible areas
- **Problem 2**: Per-world borders - new version supports per-world, old version only supports global - config becomes incompatible

---

## 26. BentoBox (Skyblock Suite)

### Cross-Server Perspective:
- **Problem 1**: Island ownership - if player creates island on BENT01, can they access it from a hypothetical BENT02? Island data must sync cross-instance
- **Problem 2**: Island challenges - if challenge completion tracked per-instance, player can re-complete on each instance for duplicate rewards

### Version Control Nightmare:
- **Problem 1**: BentoBox 3.3.5 addon API vs 3.4.x - breaking changes, addons for one version don't load on other, island features break mid-upgrade
- **Problem 2**: Island schematic format - saved islands on 3.3.x don't import correctly to 3.4.x, island data loss during migration

---

## 27. Axiom (Advanced Building)

### Cross-Server Perspective:
- **Problem 1**: Axiom client-side predictions - if mod required on creative server but not survival, player must disable/enable mod when switching instances
- **Problem 2**: World manipulation tools - if accidentally used on survival instance without proper permissions, can duplicate items/grief

### Version Control Nightmare:
- **Problem 1**: Axiom updates require CLIENT mod update - if server updates but players don't, connection fails, players locked out until they update
- **Problem 2**: Feature additions - new Axiom version adds tool that old version doesn't recognize, builds become incompatible across instance versions

---

## 28. spark (Performance Profiler)

### Cross-Server Perspective:
- **Problem 1**: Profiling one instance affects performance - if sharing hardware, other instances lag during profiling session
- **Problem 2**: Performance comparison - "why does SMP101 lag but DEV01 doesn't" - need cross-instance performance metric aggregation

### Version Control Nightmare:
- **Problem 1**: spark viewer web UI version - old instance generates profile in old format, new web viewer can't parse it, profiling data lost
- **Problem 2**: Heap dump format changes - dumps from different spark versions incompatible, can't compare memory usage across instances

---

## 29. Plan (Analytics & Statistics)

### Cross-Server Perspective:
- **Problem 1**: Player session tracking - if player switches instances mid-session, is it one session or two? Session aggregation across instances complex
- **Problem 2**: Server TPS comparison - Plan dashboard should show ALL instances, but if Plan version differs, can't aggregate into single dashboard

### Version Control Nightmare:
- **Problem 1**: Plan database schema - schema version mismatch between instances breaks data aggregation, can't generate network-wide reports
- **Problem 2**: New metrics added in updates - old instance doesn't track metric, dashboard shows incomplete data when mixing versions

---

## 30. ImageFrame (Image Display)

### Cross-Server Perspective:
- **Problem 1**: Image loaded on SMP101 item frame - if player takes image item to DEV01, does image still render? Needs cross-instance image cache sync
- **Problem 2**: Image map IDs - if map ID collides between instances, wrong image renders when item transferred

### Version Control Nightmare:
- **Problem 1**: ImageFrame 1.8.2 image format vs 1.9.x - image data structure changes, images become corrupted when viewed on different version instance
- **Problem 2**: Cache storage location - old version uses SQLite, new uses MySQL - can't share image cache across versions, all images must be re-uploaded

---

## 31. ResourcePackManager (Resource Pack Distribution)

### Cross-Server Perspective:
- **Problem 1**: Different resource packs per instance - SMP101 uses pack v1, DEV01 uses pack v2 for testing - player switches, must re-download, bandwidth waste
- **Problem 2**: Pack required status - if required on one instance but optional on another, player confusion about why they can't join one server without pack

### Version Control Nightmare:
- **Problem 1**: ResourcePackManager config format changes - pack URL/hash storage format different between versions, packs fail to apply after instance upgrade
- **Problem 2**: Pack version detection - old instance uses SHA1 hash, new uses SHA256, can't determine if player has correct pack when switching

---

## 32. LibsDisguises (Entity Disguises)

### Cross-Server Perspective:
- **Problem 1**: Player disguised as zombie on SMP101 - disguise state syncs via HuskSync persistent data - but if LibsDisguises not on DEV01, disguise breaks
- **Problem 2**: Disguise abilities - if disguised as enderman, can player teleport? If ability rules differ per instance, behavior inconsistent

### Version Control Nightmare:
- **Problem 1**: LibsDisguises 11.0.5 disguise NBT format vs 12.x - disguise data incompatible, disguises break when player switches between version instances
- **Problem 2**: New mob types added - 1.21.4 adds new mob, new LibsDisguises supports it, old version doesn't, disguise as new mob crashes old instance

---

## 33. GlowingItems (Item Highlighting)

### Cross-Server Perspective:
- **Problem 1**: Item glows on SMP101 - glow stored in item NBT - if GlowingItems not installed on DEV01, item still has NBT but doesn't glow, visual inconsistency
- **Problem 2**: Glow color - if color rules differ per instance config, same item glows different colors per instance

### Version Control Nightmare:
- **Problem 1**: GlowingItems NBT format changes - old instance writes glow to NBT one way, new instance reads it differently, glow breaks after transfer
- **Problem 2**: Client-side mod integration - if some instances require Optifine for custom glow, players without mod see broken visuals

---

## 34. DamageIndicator (Combat Feedback)

### Cross-Server Perspective:
- **Problem 1**: Damage numbers appear above mobs - if enabled on SMP101 but disabled on DEV01, combat feedback inconsistent, affects PvP experience
- **Problem 2**: Indicator style config - if one instance shows hearts, another shows numbers, player confusion about actual damage dealt

### Version Control Nightmare:
- **Problem 1**: DamageIndicator packet format - new version changes how damage holograms sent to client, old instance clients see broken indicators
- **Problem 2**: Compatibility with damage-modifying plugins - if EliteMobs version differs, damage calculation differs, indicators show wrong numbers

---

## 35. CraftBook (Mechanics & Features)

### Cross-Server Perspective:
- **Problem 1**: Custom mechanics like elevators - if elevator at X,Y,Z works on SMP101 but not DEV01 (disabled for creative), player confusion
- **Problem 2**: ICs (Integrated Circuits) - if IC config differs per instance, same contraption behaves differently, redstone builds break when copied between instances

### Version Control Nightmare:
- **Problem 1**: CraftBook IC IDs change between versions - IC sign with [MC1000] works on old instance, throws error on new instance with renamed ICs
- **Problem 2**: Mechanic enable/disable flags - new version adds mechanics, old config doesn't have flags, config sync creates errors

---

## 36. FreeMinecraftModels (Custom Models)

### Cross-Server Perspective:
- **Problem 1**: Custom model item on SMP101 - if model data differs per instance, same item looks different or invisible on DEV01
- **Problem 2**: Resource pack requirement - if SMP101 requires pack for models but DEV01 optional, models break for players who join DEV first

### Version Control Nightmare:
- **Problem 1**: FMM 1.1.4 model format vs 1.2.x - model data structure changes, models created on new instance don't render on old instance
- **Problem 2**: Custom model data ID allocation - if IDs assigned differently per instance, model ID collision causes wrong model to render

---

## 37. HandsOffMyBook (Book Protection)

### Cross-Server Perspective:
- **Problem 1**: Written book protected on SMP101 - protection status syncs via item NBT - if plugin not on DEV01, book editable there, protection bypassed
- **Problem 2**: Book signing - if book signed on one instance, signature verification fails on instance without plugin, book appears unsigned

### Version Control Nightmare:
- **Problem 1**: Protection NBT format changes - old instance marks book protected one way, new instance doesn't recognize format, books become unprotected
- **Problem 2**: Permission nodes change - old config uses `hotmb.protect`, new uses `handsoffmybook.protect`, permissions break after upgrade

---

## 38. Hurricane (Bedrock Bridge)

### Cross-Server Perspective:
- **Problem 1**: Bedrock players connect via Floodgate - if Hurricane on SMP101 but not DEV01, Bedrock players can't join DEV01, split player base
- **Problem 2**: Java/Bedrock parity features - if enabled on one instance but not another, Bedrock players experience differs per instance

### Version Control Nightmare:
- **Problem 1**: Hurricane version tied to specific MC version - can't run 1.21.3 Hurricane on 1.21.4 instance, forces all instances to same MC version
- **Problem 2**: Floodgate integration - Hurricane update requires Floodgate update, but Floodgate on shared Geyser proxy, can't update independently

---

## 39. Minetorio (Integration)

### Cross-Server Perspective:
- **Problem 1**: Webhook notifications - if configured per instance, same player action triggers multiple webhooks, spam in Discord
- **Problem 2**: Stats reporting - if each instance reports independently, stats show duplicate player counts, inaccurate network metrics

### Version Control Nightmare:
- **Problem 1**: Webhook URL format changes - old config uses single URL, new uses multiple URLs for different event types, config incompatible
- **Problem 2**: Event trigger names change - event `player.join` becomes `player.connect`, old configs stop working after update

---

## 40. spicord (Discord Integration)

### Cross-Server Perspective:
- **Problem 1**: Discord commands - if `/online` command shows players on current instance only, doesn't reflect network-wide player count
- **Problem 2**: Chat relay - if each instance relays to different Discord channel, chat fragments, players on different instances can't communicate via Discord

### Version Control Nightmare:
- **Problem 1**: Discord bot API version - old spicord uses Discord API v9, new uses v10, bot token format changes, authentication breaks
- **Problem 2**: Command prefix config - old instance uses `!`, new uses `/`, players confused about which command format to use

---

## 41. ViaVersion, ViaBackwards, ViaRewind (Version Compatibility)

### Cross-Server Perspective:
- **Problem 1**: Player on 1.20.1 client joins 1.21.4 instance via ViaVersion - some features unavailable, player experience degraded compared to native client
- **Problem 2**: Protocol translation - if translation rules differ per instance config, same client sees different behaviors per instance

### Version Control Nightmare:
- **Problem 1**: ViaVersion 5.3.0 vs 5.4.x - protocol mappings change, clients on borderline versions (1.21.0) work on one instance, kick on another
- **Problem 2**: Backwards compatibility - ViaBackwards for 1.20 support on one instance, not on another, player confusion about which instances support their version

---

## 42. floodgate (Bedrock Players)

### Cross-Server Perspective:
- **Problem 1**: Bedrock player authentication - if Floodgate on proxy but not all instances, Bedrock players see different features per instance
- **Problem 2**: Username prefix - Bedrock players prefixed with `.` - if some plugins check username exact match, breaks on instances with Floodgate

### Version Control Nightmare:
- **Problem 1**: Floodgate 2.x linked accounts vs 1.x unlinked - account data structure changes, Bedrock players must re-link accounts after upgrade
- **Problem 2**: Skin format - Bedrock skins handled differently per version, player skins break or show default after instance version mismatch

---

## 43. nightcore (Performance Core)

### Cross-Server Perspective:
- **Problem 1**: Tick rate optimizations - if SMP101 runs nightcore optimizations but DEV01 doesn't, TPS differs, player movement/combat feels different
- **Problem 2**: Entity AI changes - if nightcore modifies AI on one instance, mob behaviors inconsistent across instances

### Version Control Nightmare:
- **Problem 1**: nightcore 2.7.5.2 optimization methods vs 2.8.x - method changes, instance with new version has different performance characteristics
- **Problem 2**: Compatibility with other plugins - nightcore update breaks compatibility with LevelledMobs on one instance, mobs stop spawning

---

## 44. packetevents (Packet Library)

### Cross-Server Perspective:
- **Problem 1**: Plugins depend on packetevents - if version differs per instance, dependent plugins behave differently per instance
- **Problem 2**: Packet interception - if rules differ per instance, anti-cheat detections differ, player kicked on one instance but not another

### Version Control Nightmare:
- **Problem 1**: packetevents 2.7.0 API vs 3.x - breaking API changes, plugins compiled for 2.7.0 crash on instance with 3.x
- **Problem 2**: Packet structure changes for MC updates - 1.21.4 packets differ from 1.21.3, version mismatch causes packet parsing errors

---

## 45. Velocity Plugins (papiproxybridge, velocitab, etc.)

### Cross-Server Perspective:
- **Problem 1**: Proxy-level plugins affect all instances - if velocitab shows player list from all instances, but one instance is private test server, leaks info
- **Problem 2**: PAPI placeholder sync - if backend instance updates placeholder, proxy cache stale, shows wrong value to players on other instances

### Version Control Nightmare:
- **Problem 1**: Velocity proxy version vs plugin version - Velocity 3.3.x vs 3.4.x API changes, proxy plugins break, can't connect to any instance
- **Problem 2**: Backend instance version mismatch - papiproxybridge on Velocity expects certain PAPI version on backends, version mismatch breaks placeholder sync

---

## 46. ExcellentJobs (Alternative Jobs Plugin)

### Cross-Server Perspective:
- **Problem 1**: Job levels - if player is Miner 20 on SMP101, should that sync to DEV01? If synced, job action counts must aggregate cross-instance
- **Problem 2**: Job rewards - if reward rates differ per instance config, players farm on high-reward instance, exploit economy

### Version Control Nightmare:
- **Problem 1**: ExcellentJobs 1.11.1 job data format vs 2.x - job progress stored differently, player loses job levels when switching between version instances
- **Problem 2**: Job config structure - old version uses flat config, new uses modular job files, can't deploy same config to both versions

---

## 47. ExcellentChallenges-Renewed (Challenge System)

### Cross-Server Perspective:
- **Problem 1**: Daily challenges - "complete 5 challenges today" - should challenges from all instances count? Or per-instance isolated?
- **Problem 2**: Challenge rewards - if claimed on one instance, should be marked claimed network-wide to prevent duplicate rewards

### Version Control Nightmare:
- **Problem 1**: Challenge data storage - old version uses YAML, new uses database, player challenge progress lost during migration
- **Problem 2**: Challenge ID changes - challenge renamed in update, old progress references old ID, progress lost, player complaints

---

## 48. CombatPets (Pet Combat System)

### Cross-Server Perspective:
- **Problem 1**: Pet ownership - if pet entity spawned on SMP101, player switches to DEV01, pet despawns or orphaned, player loses pet
- **Problem 2**: Pet stats - if pet levels/stats stored in persistent data, HuskSync syncs it, but if CombatPets version differs, stat calculation differs per instance

### Version Control Nightmare:
- **Problem 1**: CombatPets 2.4.1 pet data NBT vs 3.x - pet data structure changes, pet items become invalid when moved between versions
- **Problem 2**: Pet abilities - new version adds abilities old version doesn't support, pets with new abilities crash old instance

---

## 49. EternalTD (Tower Defense Minigame)

### Cross-Server Perspective:
- **Problem 1**: Minigame instance - if running on dedicated instance, player stats (kills, wins) should sync network-wide for leaderboards
- **Problem 2**: Minigame rewards - if rewards given on minigame instance, must sync to main instance or rewards lost when player leaves

### Version Control Nightmare:
- **Problem 1**: EternalTD game version - if minigame mechanics change in update, saved games incompatible, games corrupt mid-match after instance update
- **Problem 2**: Arena schematics - arena format changes, arenas must be rebuilt after update, downtime for minigame

---

## 50. GregoRail (Train System)

### Cross-Server Perspective:
- **Problem 1**: Rail networks - if rail at X,Z on SMP101 connects to station, but DEV01 has different terrain, rail broken, train derails when worlds not mirrored
- **Problem 2**: Train entity - if train crosses chunk border and player switches instances, train entity orphaned, train lost

### Version Control Nightmare:
- **Problem 1**: GregoRail train data format - old version stores train as armor stand, new as display entity, trains disappear after instance upgrade
- **Problem 2**: Rail type additions - new version adds high-speed rail, old version doesn't recognize block type, rail breaks

---

## 51. ResurrectionChest (Death Protection)

### Cross-Server Perspective:
- **Problem 1**: Player dies on SMP101, resurrection chest spawns - player logs to DEV01, can't access chest, items lost if chest expires
- **Problem 2**: Chest location sync - if death location on SMP101, but player on DEV01, how do they know where to return for chest?

### Version Control Nightmare:
- **Problem 1**: Chest data storage - old version stores chest as block entity, new as virtual inventory, chest access breaks after instance upgrade
- **Problem 2**: Expiry timer - timer format changes from minutes to seconds in update, all chests expire immediately after update

---

## 52. JobListings (Job Board)

### Cross-Server Perspective:
- **Problem 1**: Job postings - if posted on SMP101, should be visible on DEV01? Network-wide job board vs per-instance
- **Problem 2**: Job completion verification - if job is "build me a house at X,Z" on SMP101, completion check fails if verifier on DEV01

### Version Control Nightmare:
- **Problem 1**: Job data storage - old version uses config files, new uses database, all job postings lost during migration
- **Problem 2**: Payment integration - old version integrates with Essentials, new with Vault/TNE, payment method changes, jobs become unpayable

---

## 53. CSMC (Custom Server Management)

### Cross-Server Perspective:
- **Problem 1**: Custom commands - if command defined on SMP101 but not DEV01, command fails when player switches, confusion
- **Problem 2**: Server aliases - if alias points to SMP101 IP but player on DEV01, alias broken, navigation fails

### Version Control Nightmare:
- **Problem 1**: Command config format - YAML structure changes between versions, custom commands break after instance upgrade
- **Problem 2**: Permission integration - permission node format changes, all custom commands become unpermissioned

---

## 54. CreativeSuite (Creative Server Tools)

### Cross-Server Perspective:
- **Problem 1**: Creative tools should NOT work on survival instance - if permissions leak via HuskSync, player gets creative abilities on survival, game-breaking
- **Problem 2**: Plot worlds - if creative plots on one instance, player switches to survival, plot data inaccessible, builds unreachable

### Version Control Nightmare:
- **Problem 1**: Plot schematic format - old version saves plots as .schematic, new as .schem, plots can't be imported after instance upgrade
- **Problem 2**: Inventory separation - old version shares inventory between creative/survival, new separates, player loses items after update

---

## 55. BattleRoyale (PvP Minigame)

### Cross-Server Perspective:
- **Problem 1**: Game stats (kills, wins) - should aggregate network-wide for leaderboards, but game instances might be separate
- **Problem 2**: Lobby system - if lobby on one instance, game on another, player inventory must sync between instances during match

### Version Control Nightmare:
- **Problem 1**: Game state storage - active game data format changes, games crash mid-match after instance update
- **Problem 2**: Arena config - new version changes arena format, all arenas must be reconfigured, game downtime

---

## 56. eShulkerBox (Shulker Management)

### Cross-Server Perspective:
- **Problem 1**: Shulker contents - HuskSync syncs inventory including shulkers, but if eShulkerBox features differ per instance, shulker access inconsistent
- **Problem 2**: Shulker naming/searching - if named on SMP101, name should persist to DEV01, but if plugin versions differ, names lost

### Version Control Nightmare:
- **Problem 1**: Shulker NBT format - plugin stores metadata in NBT, format changes, shulkers become unreadable after version mismatch
- **Problem 2**: CMI integration - eShulkerBox integrates with CMI, if CMI version differs per instance, integration breaks, shulkers inaccessible

---

## 57. Geyser-Recipe-Fix (Bedrock Crafting)

### Cross-Server Perspective:
- **Problem 1**: Recipe fixes apply to Bedrock players - if installed on SMP101 but not DEV01, Bedrock players can't craft certain items on DEV01
- **Problem 2**: Custom recipes - if custom recipe fixed on one instance but not another, Bedrock players confused about recipe availability

### Version Control Nightmare:
- **Problem 1**: Recipe fix mappings - Minecraft adds new items, old Geyser-Recipe-Fix doesn't have mappings, new items uncraftable for Bedrock until update
- **Problem 2**: Geyser API version - fix depends on specific Geyser version, version mismatch breaks recipe fixes entirely

---

## 58. autoviaupdater (Velocity Auto-Updater)

### Cross-Server Perspective:
- **Problem 1**: Auto-updates ViaVersion on proxy - if update breaks protocol translation, all instances become inaccessible until rollback
- **Problem 2**: Update timing - if proxy updates during peak hours while instances are active, players kicked during update

### Version Control Nightmare:
- **Problem 1**: Update checks GitHub releases - if release format changes, updater breaks, manual intervention required
- **Problem 2**: Dependency conflicts - ViaVersion update requires packetevents update, auto-updater doesn't handle dependencies, crash loop

---

## Analysis Summary

**Total plugins analyzed**: 58 of 88+
**Cross-server issues identified**: 116+
**Version control issues identified**: 116+

**Key patterns emerging**:

1. **NBT/Persistent Data** - Items with custom NBT break when plugin versions differ
2. **Database Schema** - Schema version mismatches corrupt player data during instance switching
3. **Config Format Evolution** - YAML structure changes make config synchronization impossible
4. **API Breaking Changes** - Plugins depending on libraries break when library versions differ
5. **Coordinate Assumptions** - Plugins assume mirrored worlds, fail when coordinates differ
6. **Real-time Sync Requirements** - Cross-instance features need real-time data sync to prevent exploits
7. **Permission Context** - Some perms must be global, some local, distinction unclear
8. **Resource Packs** - Different packs per instance create visual inconsistencies
9. **Client-side Mods** - Required mods on some instances but not others fragment player base
10. **Event Aggregation** - Quest/job/challenge progress must aggregate across instances or isolate clearly

**Continuing analysis for remaining 30+ plugins...**

---

## HUSKSYNC FABRIC <> PAPER SYNC INVESTIGATION

**Current State** (from GitHub code):
- HuskSync has BOTH `bukkit` and `fabric` modules in the same repository
- They share a `common` module for cross-platform data structures
- Compatibility table shows: "1.21.4 latest 21 Paper, Fabric ✅"
- Developer's claim: "It's enabled, it just breaks things, there's a killswitch"

**Where's the killswitch?**

### Code Evidence:

1. **Platform Detection** (`common/src/main/java/net/william278/husksync/HuskSync.java`):
```java
@NotNull String getPlatformType(); // Returns "bukkit" or "fabric"
```

2. **Data Serialization** (`common/src/main/java/net/william278/husksync/data/SerializerRegistry.java`):
```java
// Lines 61-83: validateDependencies() - checks if required identifiers are enabled
// If dependency not met, DISABLES the identifier
identifier.setEnabled(false);
getPlugin().log(Level.WARNING, "Disabled %s syncing as the following types need to be on: %s"
```

3. **Sync Features Toggle** (`common/src/main/java/net/william278/husksync/config/Settings.java`):
```java
// Lines 301-311: Which data types to synchronize
@Comment({"Which data types to synchronize.", "Docs: https://william278.net/docs/husksync/sync-features"})
private Map<String, Boolean> features = Identifier.getConfigMap();

// Line 379: Check if feature enabled
public boolean isFeatureEnabled(@NotNull Identifier id) {
    return id.isCustom() || features.getOrDefault(id.getKeyValue(), id.isEnabledByDefault());
}
```

4. **Fabric-Specific Data Adapter** (`fabric/src/main/java/net/william278/husksync/data/FabricData.java`):
- Has separate implementations for Fabric vs Bukkit
- Lines 350-364: Fabric advancements sync
- Fabric uses `ServerPlayerEntity` vs Bukkit's `org.bukkit.entity.Player`

5. **Cross-Platform Data** (`common` module):
- Shared data structures in `common/src/main/java/net/william278/husksync/data/`
- `Data.java` interface is platform-agnostic
- Bukkit and Fabric each implement their own serializers

**The "killswitch" appears to be:**

1. **Config-based**: `synchronization.features` map in `config.yml` - each data type can be toggled
2. **Dependency validation**: If platform-specific serializer missing, auto-disables that data type
3. **Platform type check**: Code can branch on `getPlatformType()` returning "fabric" vs "bukkit"

**The "edge cases that break":**

From code structure, the issue is:
- Vanilla game data (inventory, health, XP, advancements) → **WORKS** (shared NBT format)
- Plugin persistent data container → **BREAKS** (Fabric mods store data differently than Bukkit plugins)
- Custom item NBT from mods vs plugins → **DIFFERENT** (no schema to translate)
- Attribute modifiers → **MAYBE BREAKS** (Fabric mod IDs vs Bukkit plugin namespaces)

**What would need to be changed:**

1. **Server name in database** - currently stores ONE platform type per server
   - Need to allow server to be BOTH platforms simultaneously
   - Or: separate server IDs for fabric vs bukkit but shared player UUID

2. **Persistent data container sync** - this is the killer:
```java
// config.yml line ~127
persistent_data: true  // This syncs plugin custom data - would need cross-platform translation
```

3. **Attribute modifier filtering** (`Settings.java` lines 331-343):
```java
ignoredModifiers = new ArrayList<>(List.of(
    "minecraft:effect.*", "minecraft:creative_mode_*"
));
```
   - Need to add: Ignore ALL mod-specific or plugin-specific modifiers that don't exist on other platform

**To enable Fabric <> Paper sync:**

1. Set both servers to use same cluster_id
2. Set both to same database/Redis
3. In `config.yml` on BOTH servers:
```yaml
synchronization:
  features:
    inventory: true
    ender_chests: true
    health: true
    hunger: true
    experience: true
    potion_effects: true
    advancements: true
    game_mode: true
    statistics: true
    location: true  # Only if mirrored worlds
    persistent_data: false  # <-- THE KILLSWITCH - turn OFF to prevent mod/plugin data conflicts
    locked_maps: true
    attributes: true  # But configure ignored_modifiers carefully
```

4. Add to `attributes.ignored_modifiers`:
```yaml
ignored_modifiers:
  - 'minecraft:effect.*'
  - 'minecraft:creative_mode_*'
  - '*:*'  # Nuclear option - ignore ALL non-vanilla modifiers
  # OR be selective:
  - 'fabric:*'  # Ignore all Fabric mod modifiers
  - 'plugin:*'  # Ignore all Bukkit plugin modifiers (if they namespace properly)
```

**The "almost routine" change:**

William278 meant: If you know Java and NBT structures, just:
1. Fork HuskSync
2. Add platform type checks in data sync logic
3. Filter out incompatible data types during serialization
4. Test thoroughly with YOUR specific mod/plugin combo

**Want me to generate a config template that safely enables Fabric <> Paper sync with the dangerous features disabled?**
