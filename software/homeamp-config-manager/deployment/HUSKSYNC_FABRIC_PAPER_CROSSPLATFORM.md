# HuskSync Fabric <> Paper Cross-Platform Configuration
## Safe Configuration for Mixed Platform Synchronization

**Warning**: This enables cross-platform sync between Fabric and Paper instances. Test thoroughly before production deployment.

---

## config.yml - Shared Configuration (Both Platforms)

```yaml
# ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃  HuskSync Cross-Platform Sync ┃
# ┃   Fabric <> Paper Compatible  ┃
# ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

# CRITICAL: All servers (Fabric and Paper) must use the SAME cluster_id
cluster_id: 'archivesmp-network'

# Database - MUST be shared across all platforms
database:
  type: MYSQL
  credentials:
    host: 135.181.212.169
    port: 3369
    database: asmp_SQL  # Or your shared database name
    username: sqlworkerSMP
    password: 'your_password_here'
    parameters: ?autoReconnect=true&useSSL=false&useUnicode=true&characterEncoding=UTF-8

# Redis - MUST be shared across all platforms
redis:
  host: cloud.archivesmp.site
  port: 6379
  password: ''
  use_ssl: false
  database: 0

# Data syncing settings
synchronization:
  # Use LOCKSTEP for reliability
  mode: LOCKSTEP
  
  # Snapshot settings
  max_user_data_snapshots: 16
  snapshot_backup_frequency: 4
  auto_pinned_save_causes:
    - INVENTORY_COMMAND
    - ENDERCHEST_COMMAND
    - BACKUP_RESTORE
    - LEGACY_MIGRATION
    - MPDB_MIGRATION
  
  save_on_world_save: true
  
  # Death snapshot handling
  save_on_death:
    enabled: true
    items_to_save: ITEMS_TO_KEEP
    save_empty_items: true
    sync_dead_players_changing_server: true
  
  compress_data: true
  notification_display_slot: ACTION_BAR
  persist_locked_maps: true
  network_latency_milliseconds: 500
  
  # ========================================
  # CRITICAL: Feature Toggles for Cross-Platform
  # ========================================
  features:
    # ✅ SAFE - Vanilla Minecraft data (identical across platforms)
    inventory: true
    ender_chests: true
    health: true
    hunger: true
    experience: true
    potion_effects: true
    advancements: true
    game_mode: true
    statistics: true
    
    # ⚠️ CONDITIONAL - Only enable if worlds are mirrored exactly
    location: false  # Set true only if Fabric and Paper worlds are identical
    
    # ❌ DANGEROUS - Cross-platform incompatibilities
    persistent_data: false  # THE KILLSWITCH - Fabric mod data ≠ Paper plugin data
    
    # ✅ SAFE - Map data can be translated
    locked_maps: true
    
    # ⚠️ SAFE WITH FILTERING - See attributes config below
    attributes: true
    
    # ✅ SAFE - Vanilla flight state
    flight_status: true
  
  # ========================================
  # Attribute Syncing - CRITICAL CONFIGURATION
  # ========================================
  attributes:
    # Only sync vanilla Minecraft attributes (work on both platforms)
    synced_attributes:
      # Health and absorption
      - 'minecraft:generic.max_health'
      - 'minecraft:max_health'
      - 'minecraft:generic.max_absorption'
      - 'minecraft:max_absorption'
      
      # Luck and scale (vanilla)
      - 'minecraft:generic.luck'
      - 'minecraft:luck'
      - 'minecraft:generic.scale'
      - 'minecraft:scale'
      
      # Movement (vanilla only)
      - 'minecraft:generic.movement_speed'
      - 'minecraft:movement_speed'
      - 'minecraft:generic.flying_speed'
      - 'minecraft:flying_speed'
      
      # Attack and defense (vanilla)
      - 'minecraft:generic.attack_damage'
      - 'minecraft:attack_damage'
      - 'minecraft:generic.attack_speed'
      - 'minecraft:attack_speed'
      - 'minecraft:generic.armor'
      - 'minecraft:armor'
      - 'minecraft:generic.armor_toughness'
      - 'minecraft:armor_toughness'
      - 'minecraft:generic.knockback_resistance'
      - 'minecraft:knockback_resistance'
      
      # DO NOT ADD: Step height, gravity (1.21+ only, breaks cross-version)
    
    # IGNORE ALL NON-VANILLA MODIFIERS
    ignored_modifiers:
      # Effects (applied by potions, temporary, shouldn't persist cross-server anyway)
      - 'minecraft:effect.*'
      
      # Creative mode (resets per server)
      - 'minecraft:creative_mode_*'
      
      # ========================================
      # CROSS-PLATFORM SAFETY - IGNORE ALL MODS/PLUGINS
      # ========================================
      # Fabric mods add modifiers with mod namespaces
      - 'fabric:*'
      - 'fabricloader:*'
      - 'modmenu:*'
      - 'cloth-config:*'
      
      # Common Fabric mod namespaces (add yours here)
      - 'create:*'
      - 'ae2:*'
      - 'techreborn:*'
      - 'botania:*'
      - 'mekanism:*'
      
      # Paper plugin modifiers (if plugins add attributes)
      - 'elitemobs:*'
      - 'mmoitems:*'
      - 'mythicmobs:*'
      - 'rpgitems:*'
      - 'itemsadder:*'
      
      # Wildcard catchall for non-minecraft namespaces
      # WARNING: This is aggressive but safe
      # - '*:*'  # Uncomment to ONLY sync vanilla minecraft:* attributes
  
  # Event priorities (default is fine for cross-platform)
  event_priorities:
    quit_listener: LOWEST
    join_listener: LOWEST
    death_listener: NORMAL
  
  # Check-in petitions (leave default unless debugging)
  checkin_petitions: false
```

---

## server.yml - Platform-Specific Names

### Paper Instances (SMP101, DEV01, etc.):
```yaml
name: 'SMP101-PAPER'
```

### Fabric Instances:
```yaml
name: 'FAB01-FABRIC'
```

**Critical**: Server names MUST be unique across the network, including platform suffix to identify issues.

---

## Deployment Steps

### 1. Database Schema Check
```sql
-- Verify HuskSync tables exist and are accessible from all servers
USE asmp_SQL;
SHOW TABLES LIKE 'husksync_%';

-- Check for existing user data
SELECT COUNT(*) FROM husksync_users;
```

### 2. Install HuskSync on ALL Servers

**Paper Servers**:
```bash
# Download Paper version
wget https://ci.william278.net/job/HuskSync/lastSuccessfulBuild/artifact/target/HuskSync-Paper-3.8.1.jar \
  -O /home/amp/.ampdata/instances/SMP101/plugins/HuskSync.jar
```

**Fabric Servers**:
```bash
# Download Fabric version
wget https://ci.william278.net/job/HuskSync/lastSuccessfulBuild/artifact/target/HuskSync-Fabric-3.8.1.jar \
  -O /home/amp/.ampdata/instances/FAB01/mods/HuskSync.jar

# Ensure Fabric API is installed (required dependency)
# Check for fabric-api-*.jar in mods folder
```

### 3. Configure Each Server

```bash
# Start each server ONCE to generate configs
# Stop each server
# Edit config.yml with above settings
# Edit server.yml with unique name + platform suffix
# Restart
```

### 4. Testing Protocol

**Test 1: Vanilla Data Sync** (Should work):
1. Join Paper server with test account
2. Collect vanilla items (diamonds, sticks, etc.)
3. Set health to half
4. Gain some XP levels
5. Switch to Fabric server
6. **Expected**: All vanilla items, health, XP synced

**Test 2: Mod/Plugin Data Isolation** (Should NOT sync):
1. On Fabric server: Get item from Fabric mod (Create wrench, etc.)
2. Switch to Paper server
3. **Expected**: Mod item DISAPPEARS (not synced due to persistent_data: false)
4. On Paper server: Get EliteMobs custom item
5. Switch to Fabric server
6. **Expected**: EliteMobs item DISAPPEARS

**Test 3: Attribute Modifier Safety**:
1. On Fabric server with mods that add attribute modifiers:
2. Get modded armor with +20 max health from mod
3. Switch to Paper server
4. **Expected**: Base max health syncs (vanilla 20), mod bonus DOES NOT (+20 stripped)

**Test 4: Location Sync** (If enabled):
1. Stand at X=100, Y=64, Z=200 on Paper server
2. Switch to Fabric server
3. **Expected**: Spawn at X=100, Y=64, Z=200 (if worlds are mirrored)
4. If worlds differ, player may spawn in void/lava - DISABLE location sync

---

## Troubleshooting

### "Player data not syncing at all"
- Check `cluster_id` matches on ALL servers
- Verify database connection from ALL servers
- Check Redis connection from ALL servers
- Look for "Failed to fetch data" errors in logs

### "Items disappearing when switching platforms"
**Expected behavior** with `persistent_data: false`:
- Fabric mod items with custom NBT → Will disappear on Paper
- Paper plugin items with custom NBT → Will disappear on Fabric
- **Solution**: This is INTENTIONAL to prevent crashes. Items with only vanilla NBT will sync.

### "Attributes reset when switching"
Check `ignored_modifiers` list includes the mod/plugin namespace:
```bash
# On Fabric server console
/husksync debug
# Look for attribute modifier IDs in log
# Add those namespaces to ignored_modifiers
```

### "Player spawns in wrong location"
Worlds are NOT mirrored between Fabric and Paper:
```yaml
synchronization:
  features:
    location: false  # Disable location sync
```

### "Advancements not syncing"
Fabric and Paper have identical advancement systems - should work:
```yaml
synchronization:
  features:
    advancements: true
```
If still broken, check for advancement-granting mods/plugins conflicting.

---

## Advanced: Selective Persistent Data Sync

**WARNING: EXPERIMENTAL - Not recommended without code changes**

If you need SPECIFIC mod/plugin data to sync (e.g., economy balance from a cross-platform plugin):

1. Fork HuskSync
2. Modify `FabricData.java` and `BukkitData.java` serializers
3. Add whitelist for specific PDC keys:
```java
// Example: Only sync "economy:balance" key
if (persistentData && key.getNamespace().equals("economy") && key.getKey().equals("balance")) {
    // Sync this key
} else {
    // Skip this key
}
```

**This requires Java development expertise - hire a developer if needed.**

---

## What You CANNOT Sync (Fundamental Incompatibilities)

❌ **Mod-specific items**: Create wrench, AE2 drives, Mekanism pipes
❌ **Plugin-specific items**: MMOItems customs, EliteMobs boss drops, RPGItems
❌ **Mod-added enchantments**: Apotheosis enchants, Simply Swords enchants
❌ **Plugin-added enchantments**: ExcellentEnchants, CustomEnchants
❌ **Mod GUIs/inventories**: Create contraptions, refined storage, etc.
❌ **Plugin GUIs/inventories**: Shop inventories, quest GUIs, etc.
❌ **Different world generation**: Fabric with Terralith vs Paper with vanilla

## What WILL Sync (Vanilla Minecraft)

✅ **Vanilla items**: Diamonds, netherite, shulker boxes (with vanilla contents)
✅ **Vanilla enchantments**: Sharpness, Protection, Mending, etc.
✅ **Player stats**: Health, hunger, XP, levels
✅ **Vanilla effects**: Potion effects, status effects
✅ **Advancements**: All vanilla advancements
✅ **Ender chest**: If contents are vanilla items
✅ **Game mode**: Survival, creative, adventure, spectator
✅ **Flight status**: Can fly / is flying

---

## The Bottom Line

**This configuration makes Fabric and Paper instances behave like a "vanilla-only" sync network.**

Players can freely switch between platforms, but:
- Only vanilla Minecraft data transfers
- Mod/plugin-specific items/data stay isolated per platform
- Prevents crashes from incompatible NBT structures
- Prevents attribute modifier conflicts

**If you need mod/plugin data to sync cross-platform:**
You're implementing a custom data translation layer - that's a multi-month development project, not a config change.

**William was right**: The feature works, it just breaks things if you sync incompatible data. The killswitch (`persistent_data: false`) keeps you safe.
