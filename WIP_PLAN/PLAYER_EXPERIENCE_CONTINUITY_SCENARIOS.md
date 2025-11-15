# Player Experience Continuity Scenarios
## Cross-Server Consistency Requirements for ArchiveSMP Network

**Purpose**: Catalog player experience expectations that require cross-instance coordination or consistent configuration. Mix of specific cases and general rules.

**Schema Design Drivers**: These scenarios define what data must persist in the database to support cross-platform experiences (Paper ↔ Fabric ↔ Modded).

**Key Insight from Fabric Effects Architecture**:
- **william27d8r vat** carries NBT-like custom data cross-platform
- Database must store this vat data to enable effect systems like EliteMobs Fabric mixins
- Every scenario below implies a data sync requirement → database table/column design

**Instructions**: Review and cull to realistic implementation scope. Next phase: identify rule conflicts and design meta-schema hierarchy.

---

## Item & Inventory Continuity (1-30)
**Database Schema Impact**: Item NBT storage, william27d8r vat persistence, inventory snapshots

1. **Netherite sword durability** - THAT specific sword loses durability consistently whether used on SMP101 or DEV01
   - *Schema need*: Item UUID + durability value in player_inventory table
2. **Enchantment behavior** - Sharpness V deals same damage cross-server for THAT weapon
   - *Schema need*: Vanilla enchantments in item_enchantments, NOT in vat (vanilla NBT)
3. **Custom item NBT persistence** - EliteMobs boss weapon retains ALL stats when player travels
   - *Schema need*: **william27d8r vat BLOB column** - this is THE critical requirement
   - *Enables*: Fabric mixin effects, cross-platform custom items
4. **Bundle contents** - Items inside bundles sync exactly, including sub-NBT
   - *Schema need*: Recursive item storage (items within items) - JSON or nested BLOB
5. **Shulker box contents** - All items in THAT shulker persist cross-server
   - *Schema need*: Same as bundles - container_items table with parent_item_id
6. **Anvil renaming** - Player-named items keep exact name with formatting codes
   - *Schema need*: item_display_name TEXT (supports color codes)
7. **Book & quill authorship** - Signed books maintain author UUID cross-server
   - *Schema need*: item_metadata JSON (author_uuid, generation, title)
8. **Map item data** - Exploration maps show same explored chunks everywhere
   - *Schema need*: map_data table (map_id, explored_chunks BLOB, scale, dimension)
9. **Player head ownership** - Custom player heads retain texture UUID
   - *Schema need*: skull_texture_url or skull_texture_value in item_metadata
10. **Firework rocket patterns** - Custom fireworks keep exact NBT cross-server
    - *Schema need*: Firework explosions in vat (colors, fade, shape, trail, flicker)
11. **Suspicious stew effects** - Same stew gives same effect regardless of instance
    - *Schema need*: Potion effects in item_metadata (effect_type, duration, amplifier)
12. **Potion custom effects** - Custom potions from plugins maintain effect list
    - *Schema need*: Same as #11 - supports multiple effects per item
13. **Leather armor dye** - RGB dye values persist exactly
    - *Schema need*: leather_color INT (RGB as single int) in item_metadata
14. **Banner patterns** - Complex banners maintain all layer data
    - *Schema need*: banner_layers JSON array (pattern, color per layer)
15. **Shield decoration** - Banner-decorated shields keep appearance
    - *Schema need*: shield_pattern references banner_layers
16. **Crossbow loaded state** - Loaded crossbows maintain arrow/firework
    - *Schema need*: crossbow_projectiles (projectile_item nested in vat)
17. **Compass lodestone binding** - Lodestone compasses point to same dimension/location concept
    - *Schema need*: lodestone_pos (x, y, z, dimension, tracked BOOLEAN)
18. **Recovery compass binding** - Last death location tracked per-dimension
    - *Schema need*: last_death_location (x, y, z, dimension, timestamp)
19. **Tool damage from specific action** - Mining obsidian costs same durability everywhere
    - *Schema need*: Config table - tool_durability_costs per action (not player data)
20. **Unbreaking calculation consistency** - RNG for durability loss uses same algorithm
    - *Schema need*: Config - enchantment_formulas (deterministic calc, no DB needed but config sync)
21. **Mending XP distribution** - Same XP amount repairs same durability amount
    - *Schema need*: Config - mending_ratio (XP to durability conversion)
22. **Curse persistence** - Curse of Binding/Vanishing can't be removed by instance-hopping
    - *Schema need*: Vanilla enchantment sync (already covered by #2)
23. **Attribute modifiers** - +5 attack damage from modifier works identically
    - *Schema need*: **item_attributes table** (attribute_type, operation, amount, slot, uuid)
    - *Critical for*: EliteMobs tier system, custom weapons
24. **Item flags** - HideEnchants flag respected cross-server
    - *Schema need*: item_flags INT (bitfield: HIDE_ENCHANTS, HIDE_ATTRIBUTES, etc.)
25. **Custom model data** - Resource pack custom models display consistently
    - *Schema need*: custom_model_data INT in item_metadata
26. **Item lore** - Multi-line lore with color codes preserved exactly
    - *Schema need*: item_lore JSON array of strings
27. **Damage value on old items** - Legacy items maintain data values for backwards compat
    - *Schema need*: legacy_damage_value INT (for pre-1.13 items)
28. **Skull texture URLs** - Custom skull textures load from same URL
    - *Schema need*: Same as #9 - skull_texture (URL or base64 value)
29. **Trim patterns & materials** - Armor trims look identical cross-server
    - *Schema need*: armor_trim (pattern, material) in item_metadata
30. **Item rarity** - Plugin-assigned rarity tiers (common/rare/epic) persist
    - *Schema need*: **item_rarity in vat** (plugin-specific, part of william27d8r namespace)

## Player Stats & Progression (31-60)
**Database Schema Impact**: Player state tracking, progression systems, cross-platform stat aggregation

31. **XP level total** - Same XP level/points everywhere
    - *Schema need*: player_stats (experience_total, experience_level)
    - *Sync requirement*: HuskSync `experience: true` feature
32. **Advancement completion** - Unlocking advancement on SMP101 shows on DEV01
    - *Schema need*: player_advancements (advancement_id, completed_at timestamp)
    - *Sync requirement*: HuskSync `advancements: true` feature
33. **Recipe unlocks** - Crafting recipe knowledge syncs
    - *Schema need*: player_recipes (recipe_id, unlocked_at timestamp)
    - *Critical for*: Custom crafting plugins cross-platform
34. **Statistics** - Minecraft stats (blocks mined, distance walked) aggregate or per-instance choice
    - *Schema need*: player_statistics (stat_type, value, instance_id if per-instance)
    - *Sync requirement*: HuskSync `statistics: true` OR isolated per-server
35. **Achievement from plugin** - CMI/EssentialsX achievement tracking
    - *Schema need*: player_achievements (achievement_id, plugin_source, completed_at)
    - *Stored in*: william27d8r vat (plugin-specific achievements)
36. **Quest progress** - BetonQuest progress on multi-server questlines
    - *Schema need*: quest_progress (quest_id, stage, objectives JSON, instance_restriction)
    - *Example*: "Kill 100 zombies" counts SMP101+SMP201 combined
37. **Playtime tracking** - Total network playtime vs per-instance
    - *Schema need*: player_playtime (total_seconds, last_seen, per_instance JSON)
38. **Death count** - Total deaths tracked cross-server or isolated by hardcore rules
    - *Schema need*: player_deaths (total_count, deaths_by_instance JSON, last_death timestamp)
39. **Mob kills of specific type** - Kill 100 zombies quest counts all instances
    - *Schema need*: player_mob_kills (mob_type, kill_count, aggregation_scope)
40. **Block break totals** - Job/skill systems count all instances
    - *Schema need*: player_block_stats (block_type, broken_count, placed_count)
41. **Player level in McMMO** - Skills persist exactly
    - *Schema need*: mcmmo_skills (skill_name, level, xp, instance_id if isolated)
    - *Critical*: mcMMO has own DB but needs cross-server sync decision
42. **Skill XP overflow** - If maxed on SMP, still maxed on DEV
    - *Schema need*: Same as #41 - skill level synced via HuskSync persistent_data or mcMMO DB
43. **AureliumSkills stats** - All skill levels and stat bonuses
    - *Schema need*: aurelium_skills (skill_name, level, stat_modifiers JSON)
    - *Stored in*: william27d8r vat (plugin persistent data)
44. **Daily quest reset timing** - Reset at midnight network-wide not per-instance
    - *Schema need*: daily_quests (quest_id, reset_time UTC, completed_by player_uuid)
45. **Weekly challenge progress** - Challenges span entire network
    - *Schema need*: weekly_challenges (challenge_id, progress INT, week_start timestamp)
46. **Seasonal event participation** - Halloween event progress network-wide
    - *Schema need*: event_progress (event_id, progress JSON, event_start, event_end)
47. **Voting streak** - Vote streak maintained even if play different instances
    - *Schema need*: player_votes (total_votes, current_streak, last_vote timestamp)
48. **Playtime rewards** - Cumulative playtime for monthly crates
    - *Schema need*: playtime_rewards (reward_tier, claimed BOOLEAN, eligible_at timestamp)
49. **First join date** - Network join date vs instance join date
    - *Schema need*: player_metadata (first_join_network, first_join_per_instance JSON)
50. **Nickname** - Player-set nickname via Essentials same everywhere
    - *Schema need*: player_nickname TEXT (supports color codes, 16 char limit)
51. **Chat color/formatting** - Purchased chat colors work everywhere
    - *Schema need*: player_chat_format (color, style, prefix_override)
52. **Prefix/suffix** - LuckPerms prefix displays consistently
    - *Schema need*: LuckPerms handles this - no custom DB, but sync via Redis
53. **Tablist format** - Tab list shows same rank/stats everywhere
    - *Schema need*: Same as #52 - LuckPerms + TAB plugin integration
54. **AFK status** - AFK on one instance = AFK on all (or not, configurable)
    - *Schema need*: player_state (is_afk BOOLEAN, afk_since timestamp, sync_afk_status config)
    - *Conflict*: May want AFK isolated per-instance (player mining on SMP, chatting on HUB)
55. **Vanish state** - Staff vanish persists cross-server (or not)
    - *Schema need*: player_state (is_vanished BOOLEAN, vanish_level INT for staff hierarchy)
    - *Security*: Vanish should NOT persist to avoid accidental reveals
56. **Fly permission state** - Flight enabled persists (or reset per instance for survival)
    - *Schema need*: player_state (fly_enabled BOOLEAN, per_instance_override)
    - *Conflict*: Want fly in creative server, NOT in survival
57. **Gamemode enforcement** - Creative on creative server, survival elsewhere
    - *Schema need*: Config - instance_gamemode_override (instance_id, enforced_gamemode)
    - *Sync requirement*: HuskSync `game_mode: false` to NOT sync gamemode
58. **God mode** - Invulnerability state handling cross-server
    - *Schema need*: player_state (god_mode BOOLEAN, granted_by staff_uuid)
59. **Social spy** - Staff chat monitoring cross-instance
    - *Schema need*: player_state (social_spy BOOLEAN) - staff perk
60. **Speed/walk modifiers** - Speed boosts reset or persist
    - *Schema need*: player_attributes (walk_speed FLOAT, fly_speed FLOAT, reset_on_server_switch)

## Economy & Currency (61-90)

61. **Vault balance** - Primary economy balance shared network-wide
62. **Multiple currency tracking** - Premium currency, event tokens, etc.
63. **Negative balance handling** - Debt follows player everywhere
64. **Transaction logging** - All purchases logged to central audit
65. **Shop price consistency** - AdminShop prices same everywhere (or regional economy)
66. **Player shop access** - ChestShop/QuickShop persistence
67. **Auction house listings** - Network-wide auction house vs per-instance
68. **Bank storage** - Money in bank vault separate from carried money
69. **Interest accrual** - Banks pay interest on stored money network-wide
70. **Loan repayment** - Debts tracked centrally
71. **Salary/stipend timing** - Daily login bonus given once network-wide
72. **Tax collection** - Town taxes from Towny collected centrally
73. **Trade transaction verification** - Player-to-player trades logged
74. **Currency conversion** - If multiple economies, conversion rates
75. **Inflation tracking** - Network-wide money supply monitoring
76. **Baltop accuracy** - Richest players list aggregates all sources
77. **Pay command logging** - /pay transactions cross-server
78. **Escrow for trades** - Held funds during player trades
79. **Refund processing** - Refunds for purchases work cross-server
80. **Bounty tracking** - Bounties on players paid from any instance
81. **Lottery participation** - Network lottery pool
82. **Gambling winnings** - Casino/slot machine balance changes
83. **Charity donations** - Track donations for events
84. **Crowdfunding for projects** - Players pool money for builds
85. **Business revenue** - Player-owned business income
86. **Property tax** - Real estate tax on claimed land
87. **Import/export tariffs** - If regional economies, trade costs
88. **Black market pricing** - Underground economy if implemented
89. **Insurance payouts** - Death insurance claims
90. **Inheritance** - Money transfer on account deletion

## Land Claims & Territory (91-120)

91. **Claim ownership** - Land claims tied to player UUID cross-server
92. **Trust permissions** - Trusted players on claim work everywhere
93. **Claim block accrual** - Earn claim blocks network-wide or per-instance
94. **Subclaim permissions** - Nested permission zones
95. **Container access logs** - Track who accessed chests in claims
96. **PvP flag per claim** - PvP allowed/disabled per region
97. **Mob spawning in claims** - Disable hostile mobs in claimed areas
98. **Explosion protection** - TNT/creeper protection settings
99. **Fire spread prevention** - Protect wooden builds
100. **Crop trampling** - Disable farmland grief in claims
101. **Town membership** - Towny town membership persistent
102. **Town rank/role** - Mayor, assistant, resident roles
103. **Town bank** - Shared town treasury
104. **Town spawn point** - Town /t spawn location
105. **Nation membership** - Multi-town nation allegiance
106. **War declaration** - Towny war state cross-server
107. **Ally/enemy status** - Diplomatic relations between towns
108. **Embassy plots** - Foreign town plots in your town
109. **Shop plot permissions** - Commercial zoning in towns
110. **Wilderness protection level** - Unclaimed land rules consistent
111. **Resource world separation** - Mining world not synced, resets weekly
112. **Nether/End claim rules** - Dimension-specific claiming
113. **WorldGuard region flags** - All region flags identical or per-instance
114. **Spawn protection radius** - Same radius everywhere
115. **Border enforcement** - World border at same coords
116. **Chunk loading** - Claimed chunks stay loaded or not
117. **Rent payment for plots** - Rented shop plots paid centrally
118. **Eviction for non-payment** - Automatic unclaim rules
119. **Claim expiration** - Inactive player claim cleanup
120. **Build height limits** - Y-level restrictions per region

## Social & Communication (121-150)

121. **Friend list** - Friends list shared network-wide
122. **Block list** - Blocked players muted everywhere
123. **Party/group membership** - Dungeon parties persist cross-server
124. **Guild membership** - RPG guild affiliation
125. **Alliance chat** - Multi-guild alliances
126. **Private messaging** - /msg works cross-server
127. **Mail system** - Offline messages delivered anywhere
128. **Announcements** - Network broadcasts vs local
129. **Chat channels** - Global/local/trade/help channels
130. **Chat mute status** - Muted players muted everywhere
131. **Report tickets** - Player reports visible to all staff
132. **Warning points** - Moderation warnings accumulate network-wide
133. **Ban synchronization** - Banned on one = banned everywhere
134. **Kick reason logging** - All kicks logged centrally
135. **Jail/prison time** - Jail sentence time decrements everywhere or only when online there
136. **Reputation score** - Player reputation from interactions
137. **Emoji/reaction usage** - Custom chat reactions
138. **Mention notifications** - @playername pings cross-server
139. **Chat filter** - Profanity filter same rules everywhere
140. **Link blocking** - URL posting rules consistent
141. **Spam detection** - Rate limiting cross-server
142. **Caps detection** - ALL CAPS prevention
143. **Language channels** - Non-English chat separation
144. **RP chat modes** - Roleplay /me commands
145. **Staff chat** - Admin-only chat visible everywhere
146. **Builder chat** - Builder team coordination
147. **Donator chat** - Premium chat channel
148. **Minigame chat isolation** - Minigame players separate chat
149. **Trade chat rules** - Trade channel usage consistent
150. **Announcement cooldowns** - Broadcast spam prevention

## Permissions & Ranks (151-180)

151. **Rank synchronization** - LuckPerms rank same everywhere
152. **Permission inheritance** - Group inheritance consistent
153. **Temporary permissions** - Timed perms expire network-wide
154. **Weight/priority** - Permission priority resolution
155. **Context-based perms** - Server-specific permission contexts
156. **Meta fields** - Custom meta like "supporter tier"
157. **Default group** - New player default rank
158. **Rank expiry** - Donator ranks expire at same time
159. **Promotion tracking** - Rank-up requirements
160. **Demotion logging** - Rank removals tracked
161. **Permission check caching** - Cache permissions for performance
162. **Wildcard handling** - Wildcard perms (* nodes)
163. **Negation consistency** - Negative perms (-node) work same
164. **Parent group stacking** - Multiple inheritance
165. **Per-world perms** - Some perms only in certain instances
166. **Command cooldowns** - /home cooldown cross-server or per-instance
167. **Kit eligibility** - Starter kit once per network
168. **Warp access** - Warp permissions consistent
169. **Teleport restrictions** - TP rules same everywhere
170. **Creative mode access** - Creative restricted to specific instances
171. **WorldEdit limits** - Build tool limits per rank
172. **Item spawn limits** - /give restrictions
173. **Entity limits** - Max mobs per player
174. **Redstone limits** - Anti-lag restrictions
175. **Vehicle limits** - Max minecarts/boats
176. **Armor stand limits** - Entity count restrictions
177. **Item frame limits** - Per-chunk or per-player
178. **Sign editing** - Text editing permissions
179. **Dye usage** - Sign/shulker dye perms
180. **Beacon range** - Donator beacon range boost

## Mob & Combat Mechanics (181-200)

181. **EliteMobs boss tracking** - Boss kill credit cross-server
182. **Boss respawn timers** - Centralized boss spawn timing
183. **Mob level scaling** - LevelledMobs consistent formulas
184. **Damage calculations** - Hit damage same everywhere
185. **Critical hit mechanics** - Crit chance/damage identical
186. **Knockback values** - Knockback enchant same effect
187. **Invulnerability frames** - I-frame timing consistent
188. **Armor damage reduction** - Protection calculations
189. **Thorns reflection** - Reflected damage same
190. **Projectile velocity** - Arrow speed/arc identical
191. **Pet ownership** - Tamed wolves/cats follow owner cross-server (if teleporting)
192. **Horse stats** - Tamed horse speed/jump/health
193. **Villager trades** - Trade offers same or randomized per instance
194. **Raid mechanics** - Bad Omen effect cross-server
195. **Pillager patrol spawn** - Consistent spawn rates
196. **Wither boss HP** - Boss health identical
197. **Dragon fight** - End dragon behavior same
198. **Warden spawning** - Deep dark mechanics identical
199. **Phantom spawning** - Insomnia mechanics same
200. **Monster siege** - Village siege spawn rules

---

## Next Steps
1. Review and cull to realistic scope (50-100 actual requirements)
2. Identify conflicting rules (e.g., #54 AFK state vs #56 Fly state per-instance)
3. Design hierarchical rule resolver meta-schema
4. Determine "BECAUSE" relationships (outcome A happens BECAUSE of hierarchical scenario B+C)
5. Build GUI for rule management with conflict detection
