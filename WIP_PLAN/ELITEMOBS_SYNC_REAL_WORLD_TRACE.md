# EliteMobs Cross-Instance Sync Mechanics: Real World Analysis

## User's Working Journey (All Paper Instances)

### Step-by-Step Data Flow

**1. EMAD01 (Paper, Hetzner) - Guild Hall**
- Full EliteMobs suite installed (dungeons, mobs, guild, NPCs)
- Player buys item with Elite Enchants from NPC
- Player prestiges → gains +2 max hearts (attribute modifier)
- **Data created:**
  ```
  ItemStack: Diamond Sword
    - Material: DIAMOND_SWORD
    - PersistentDataContainer:
        elitemobs:tier = 5
        elitemobs:elite_enchants = {"sharpness_elite": 10, "fire_elite": 5}
        elitemobs:item_id = "elite_boss_sword_tier5"
    - Lore: ["§6Elite Sharpness X", "§cElite Fire V"]
  
  Player Attributes:
    - minecraft:generic.max_health:
        base_value = 20.0
        modifiers = [
          {
            uuid: "elitemobs:prestige_bonus",
            name: "Prestige Heart Bonus",
            amount: 2.0,
            operation: ADD_NUMBER
          }
        ]
        effective_value = 22.0
  
  EliteMobs Database (per-server?):
    - prestige_level = 2
    - currency_balance = 1500 (EliteMobs currency, NOT Vault)
  ```

**2. CMI Portal (Still EMAD01)**
- Teleport within same instance
- No HuskSync involvement
- All data remains in memory (player hasn't logged out)

**3. `/server hub` → HUB01 (Paper, location unknown)**

**HuskSync Sync Sequence:**

```
EMAD01 - PlayerQuitEvent fired:
  ↓
HuskSync BukkitEventListener.onPlayerQuit():
  ↓
BukkitData.Items.Inventory.from(player.getInventory()):
  for each ItemStack:
    - Serialize material, amount, damage
    - Serialize ItemMeta (display name, lore, etc.)
    - Serialize PersistentDataContainer:
        for each (NamespacedKey, value) in PDC:
          json["pdc"][key.namespace() + ":" + key.key()] = value
    Result: Complete JSON representation of item WITH EliteMobs NBT
  
BukkitData.Attributes.from(player):
  for each Attribute:
    - Get base value
    - Get all AttributeModifiers
    - Serialize modifiers:
        for each modifier:
          json["modifiers"].add({
            "uuid": modifier.getUniqueId().toString(),
            "name": modifier.getName(),
            "amount": modifier.getAmount(),
            "operation": modifier.getOperation().name(),
            "slot": modifier.getSlot()
          })
  Result: Complete attribute state including EliteMobs prestige bonus
  
BukkitData.PersistentData.from(player):
  PersistentDataContainer playerPDC = player.getPersistentDataContainer();
  for each (NamespacedKey, value) in playerPDC:
    json["player_pdc"][key.toString()] = value
  Result: Any player-level EliteMobs data (if EM stores any here)

DataSnapshot.pack():
  {
    "inventory": [...items with elitemobs:* PDC keys...],
    "attributes": [...including elitemobs:prestige_bonus...],
    "persistent_data": {...player PDC...},
    "health": 22.0,
    "hunger": 20,
    "experience": 50,
    ...
  }
  ↓
Compress with Snappy (if enabled)
  ↓
RedisManager.setData(player.uuid, compressedData, 60 seconds TTL)
  ↓
Database.saveData(player.uuid, compressedData, timestamp)
```

**Redis State:**
```
KEY: "husksync:player:00000000-0000-0000-0000-000000000001"
VALUE: <gzipped binary blob>
EXPIRY: 60 seconds
```

**MySQL State:**
```sql
INSERT INTO husksync_users (uuid, username) VALUES (...);
INSERT INTO husksync_data (
  player_uuid,
  version_uuid,
  timestamp,
  save_cause,
  data_blob
) VALUES (
  '00000000-0000-0000-0000-000000000001',
  '12345678-...',
  '2025-11-15 12:34:56',
  'DISCONNECT',
  <gzipped binary blob>
);
```

**HUB01 - PlayerJoinEvent fired:**
```
HuskSync BukkitEventListener.onPlayerJoin():
  ↓
RedisManager.getData(player.uuid):
  - Check Redis for key
  - Found! (within 60s window)
  - Decompress Snappy
  - Parse JSON to DataSnapshot
  ↓
DataSnapshot.unpack():
  {
    "inventory": [...],
    "attributes": [...],
    ...
  }
  ↓
BukkitData.Items.apply(player):
  player.getInventory().clear();
  for each serialized_item in data["inventory"]:
    ItemStack item = new ItemStack(serialized_item.material);
    ItemMeta meta = item.getItemMeta();
    
    // Apply basic meta
    meta.setDisplayName(serialized_item.display_name);
    meta.setLore(serialized_item.lore);
    
    // Apply PersistentDataContainer (THE CRITICAL PART)
    PersistentDataContainer pdc = meta.getPersistentDataContainer();
    for each (key_string, value) in serialized_item.pdc:
      String[] parts = key_string.split(":");
      NamespacedKey key = new NamespacedKey(parts[0], parts[1]);
      // "elitemobs:tier" → NamespacedKey("elitemobs", "tier")
      pdc.set(key, PersistentDataType.INTEGER, value);
    
    item.setItemMeta(meta);
    player.getInventory().addItem(item);
  ↓
BukkitData.Attributes.apply(player):
  for each serialized_attribute in data["attributes"]:
    Attribute attr = player.getAttribute(serialized_attribute.type);
    attr.setBaseValue(serialized_attribute.base_value);
    
    for each serialized_modifier in serialized_attribute.modifiers:
      AttributeModifier modifier = new AttributeModifier(
        UUID.fromString(serialized_modifier.uuid),
        serialized_modifier.name,
        serialized_modifier.amount,
        AttributeModifier.Operation.valueOf(serialized_modifier.operation),
        EquipmentSlot.valueOf(serialized_modifier.slot)
      );
      attr.addModifier(modifier);
      // EliteMobs prestige bonus re-applied: +2 hearts
```

**Result on HUB01:**
- ✅ Diamond sword with `elitemobs:tier`, `elitemobs:elite_enchants` PDC intact
- ✅ Lore displays correctly (§6Elite Sharpness X, etc.)
- ✅ Max health = 22 (20 base + 2 prestige modifier)
- ✅ Elite Enchants **WORK** because HUB01 has EliteMobs plugin installed

**EliteMobs Plugin on HUB01:**
```java
// When player attacks with elite sword:
@EventHandler
public void onEntityDamageByEntity(EntityDamageByEntityEvent event) {
    if (event.getDamager() instanceof Player player) {
        ItemStack weapon = player.getInventory().getItemInMainHand();
        ItemMeta meta = weapon.getItemMeta();
        
        // Check for EliteMobs data in PDC
        PersistentDataContainer pdc = meta.getPersistentDataContainer();
        NamespacedKey enchantKey = new NamespacedKey("elitemobs", "elite_enchants");
        
        if (pdc.has(enchantKey, PersistentDataType.STRING)) {
            String enchantsJson = pdc.get(enchantKey, PersistentDataType.STRING);
            Map<String, Integer> enchants = parseJson(enchantsJson);
            
            if (enchants.containsKey("sharpness_elite")) {
                int level = enchants.get("sharpness_elite");
                double bonusDamage = level * 1.5;  // Elite sharpness formula
                event.setDamage(event.getDamage() + bonusDamage);
            }
        }
    }
}
```

**4. HUB01 → Buy Helmet with Elite Enchants**
- HUB01 has EliteMobs plugin (base installation, no dungeons)
- Shop NPC creates new ItemStack with PDC
- New helmet now in inventory with its own `elitemobs:*` data

**5. HUB01 → SMP201 (Paper, potentially OVH server)**

Same HuskSync process repeats:
- Serialize inventory (now has 2 EliteMobs items)
- Serialize attributes (prestige bonus still there)
- Redis/MySQL sync
- SMP201 deserializes and applies
- ✅ Both items work because SMP201 has EliteMobs plugin

**6. SMP201 → EVO01 (Paper, OVH, different physical server)**

**Cross-Physical-Server Sync:**
- Both servers connect to **SAME Redis** (cloud.archivesmp.site:6379)
- Both servers connect to **SAME MySQL** (135.181.212.169:3369)
- Physical location **IRRELEVANT** - data is centralized

```
SMP201 (Hetzner):
  PlayerQuitEvent → HuskSync → Redis/MySQL
    ↓
  [Network: Redis at cloud.archivesmp.site]
  [Network: MySQL at 135.181.212.169]
    ↓
EVO01 (OVH):
  PlayerJoinEvent → HuskSync ← Redis/MySQL
```

**Why It Works:**
- Redis is network-accessible from both Hetzner and OVH
- MySQL is network-accessible from both Hetzner and OVH
- All servers use **identical HuskSync configuration**
- All servers use **identical EliteMobs plugin version**

---

## What About EliteMobs Currency/Prestige?

**Why it might NOT sync:**

EliteMobs likely has its own database config:
```yaml
# EliteMobs config.yml (hypothetical):
database:
  enabled: true
  type: SQLITE  # Or per-server database
  # OR
  type: MYSQL
  host: localhost  # ← Per-server, not shared
```

**If EliteMobs uses per-server database:**
- Prestige level stored in `localhost` MySQL on EMAD01
- HUB01 queries `localhost` MySQL on HUB01 (different database)
- Prestige data NOT FOUND → defaults to 0

**If EliteMobs uses shared central database:**
- All instances query 135.181.212.169:3369
- Prestige data syncs automatically (not via HuskSync, via EM's own DB)

**User observation: "Prestige lost sometimes"**
- Likely means EliteMobs DB is NOT centralized
- Or EliteMobs stores prestige in player file (not synced by HuskSync)

---

## NOW: Add Fabric Instance to the Mix

**Scenario: EMAD01 (Paper) → FAB01 (Fabric) → SMP201 (Paper)**

### EMAD01 → FAB01 Transition

**HuskSync serialization on EMAD01:** (Same as before)
```json
{
  "inventory": [
    {
      "material": "DIAMOND_SWORD",
      "pdc": {
        "elitemobs:tier": 5,
        "elitemobs:elite_enchants": "{\"sharpness_elite\": 10}"
      }
    }
  ],
  "attributes": [
    {
      "type": "GENERIC_MAX_HEALTH",
      "base_value": 20.0,
      "modifiers": [
        {
          "uuid": "elitemobs:prestige_bonus",
          "amount": 2.0
        }
      ]
    }
  ]
}
```

**HuskSync deserialization on FAB01 (Fabric):**

```java
// FabricData.Items.apply(player):
ServerPlayerEntity player = ...;
PlayerInventory inventory = player.getInventory();

for (SerializedItem serializedItem : data.inventory) {
    // Create Fabric ItemStack
    ItemStack fabricItem = new ItemStack(
        Registries.ITEM.get(Identifier.of(serializedItem.material))
    );
    
    // Try to apply PDC data:
    // ❌ PROBLEM: Fabric has NO PersistentDataContainer API
    
    // Fabric uses NbtCompound instead:
    NbtCompound nbt = fabricItem.getOrCreateNbt();
    
    // HuskSync tries to translate Bukkit PDC → Fabric NBT:
    for (Map.Entry<String, Object> entry : serializedItem.pdc.entrySet()) {
        String key = entry.getKey();  // "elitemobs:tier"
        Object value = entry.getValue();  // 5
        
        // ❌ PROBLEM: No standard translation
        // Bukkit PDC uses typed storage (PersistentDataType.INTEGER)
        // Fabric NBT uses untyped storage (putInt, putString, etc.)
        
        // HuskSync's OPTIONS:
        // A) Skip PDC entirely (persistent_data: false)
        // B) Try to guess types and convert:
        if (value instanceof Integer) {
            nbt.putInt(key, (Integer) value);
        } else if (value instanceof String) {
            nbt.putString(key, (String) value);
        }
        // But this LOSES type information
        // EliteMobs on Fabric (if it existed) wouldn't find the data
    }
    
    inventory.setStack(slot, fabricItem);
}

// Try to apply attributes:
for (SerializedAttribute attr : data.attributes) {
    EntityAttribute fabricAttr = Registries.ATTRIBUTE.get(
        Identifier.of("minecraft", attr.type)
    );
    
    EntityAttributeInstance instance = player.getAttributeInstance(fabricAttr);
    instance.setBaseValue(attr.baseValue);  // ✅ This works (base value)
    
    for (SerializedModifier mod : attr.modifiers) {
        // ❌ PROBLEM: Bukkit uses UUID, Fabric uses Identifier
        // Bukkit: UUID.fromString("elitemobs:prestige_bonus")
        //   → UUID: "????????-????-????-????-????????????"
        // Fabric: Identifier.of("elitemobs", "prestige_bonus")
        //   → Identifier: ResourceLocation{namespace=elitemobs, path=prestige_bonus}
        
        // Can't convert UUID string to Identifier without ambiguity
        // HuskSync's OPTIONS:
        // A) Skip non-vanilla modifiers (ignored_modifiers: ['elitemobs:*'])
        // B) Try to parse UUID as Identifier (fragile, breaks often)
        
        EntityAttributeModifier fabricMod = new EntityAttributeModifier(
            ??? // Can't create valid Identifier from Bukkit UUID
        );
    }
}
```

**Result on FAB01:**
- ✅ Diamond sword exists (material synced)
- ❌ `elitemobs:*` NBT data lost or malformed
- ❌ Elite Enchants don't work (data not in expected format)
- ❌ Lore might display but enchants don't trigger
- ✅ Base max health = 20
- ❌ Prestige bonus (+2 hearts) lost (modifier couldn't be applied)

**Even if EliteMobs existed for Fabric:**
```java
// Hypothetical Fabric EliteMobs mod:
@Override
public void onAttack(LivingEntity target, ItemStack weapon) {
    NbtCompound nbt = weapon.getNbt();
    
    // Looking for elite enchant data:
    if (nbt.contains("elitemobs:elite_enchants")) {
        // ❌ HuskSync stored it as putString("elitemobs:tier", "5")
        // But Fabric EliteMobs expects nested compound:
        // NbtCompound eliteMobs = nbt.getCompound("elitemobs");
        // int tier = eliteMobs.getInt("tier");
        
        // Data structure mismatch → can't find enchants → no bonus damage
    }
}
```

### FAB01 → SMP201 Transition

**Player now has "broken" items on Fabric:**
- Diamond sword with missing/malformed NBT
- No prestige hearts

**HuskSync serialization on FAB01:**
```java
// FabricData.Items.from(player):
for (ItemStack fabricItem : inventory) {
    NbtCompound nbt = fabricItem.getNbt();
    
    // Serialize to JSON:
    Map<String, Object> serializedNbt = new HashMap<>();
    for (String key : nbt.getKeys()) {
        // ❌ PROBLEM: Can't tell if this was originally Bukkit PDC or Fabric NBT
        // Just serialize whatever NBT exists
        serializedNbt.put(key, nbt.get(key).toString());
    }
    
    // Store in data snapshot
}
```

**HuskSync deserialization on SMP201 (Paper):**
```java
// BukkitData.Items.apply(player):
ItemStack paperItem = new ItemStack(Material.DIAMOND_SWORD);
ItemMeta meta = paperItem.getItemMeta();
PersistentDataContainer pdc = meta.getPersistentDataContainer();

for (Map.Entry<String, Object> entry : serializedNbt.entrySet()) {
    String key = entry.getKey();
    Object value = entry.getValue();
    
    // Try to restore to PDC:
    // ❌ PROBLEM: Data was corrupted going Paper → Fabric
    // Now restoring Fabric→Paper, but original structure lost
    
    // "elitemobs:tier" might be there, but with wrong type
    // "elitemobs:elite_enchants" might be there, but malformed
    
    // EliteMobs plugin tries to read:
    if (pdc.has(eliteMobsTierKey, PersistentDataType.INTEGER)) {
        // ❌ Might fail if type was changed to STRING by Fabric NBT
    }
}
```

**Result on SMP201 after Fabric detour:**
- ⚠️ Diamond sword exists but Elite Enchants might be broken
- ❌ Prestige hearts likely still lost (attribute modifier never restored)
- ❌ Item might need to be repaired/recrafted

---

## The Fundamental Incompatibility

**Bukkit PersistentDataContainer:**
```java
// Typed, namespaced, API-enforced structure:
pdc.set(
    new NamespacedKey("elitemobs", "tier"),
    PersistentDataType.INTEGER,
    5
);
// Stored internally as: {elitemobs:{tier:5}}
```

**Fabric NbtCompound:**
```java
// Untyped, freeform, no namespace enforcement:
nbt.putInt("elitemobs:tier", 5);
// Stored as: {"elitemobs:tier": 5}
// OR
NbtCompound eliteMobs = new NbtCompound();
eliteMobs.putInt("tier", 5);
nbt.put("elitemobs", eliteMobs);
// Stored as: {elitemobs: {tier: 5}}
```

**HuskSync can't know which structure to use** without plugin/mod-specific translation logic for EVERY mod and plugin.

---

## The Killswitch Explained

```yaml
# config.yml:
synchronization:
  features:
    persistent_data: false  # ← THE KILLSWITCH
```

**What this does:**
```java
// HuskSync serialization with persistent_data: false
public Data serialize(Player player) {
    Data data = new Data();
    data.inventory = serializeInventory(player);  // Items synced
    data.health = player.getHealth();  // Health synced
    
    // Skip PDC entirely:
    if (settings.isFeatureEnabled("persistent_data")) {
        data.pdc = serializePDC(player);  // ← NEVER EXECUTES
    }
    
    return data;
}
```

**Result:**
- ✅ Vanilla items sync (diamond sword syncs)
- ❌ Elite Enchant NBT NOT synced (PDC skipped)
- ✅ Item doesn't corrupt (no incompatible data)
- ❌ Item becomes vanilla diamond sword (loses Elite properties)

**Safe cross-platform behavior:**
- Player goes Paper → Fabric: Elite items become vanilla items
- Player goes Fabric → Paper: Vanilla items stay vanilla
- No crashes, no corruption, just data loss for modded/plugin items

---

## TL;DR: What Allows It (Paper-Only) vs What Breaks It (Fabric)

### ✅ **What Makes Paper → Paper Work:**

1. **HuskSync `persistent_data: true`** - Syncs item and player PDC
2. **Bukkit PersistentDataContainer API** - Universal across all Paper servers
3. **EliteMobs plugin on all instances** - Understands `elitemobs:*` PDC keys
4. **Shared Redis/MySQL** - Centralized data storage across physical servers
5. **Identical data structures** - Bukkit API guarantees compatibility

### ❌ **What Breaks Paper → Fabric:**

1. **No PersistentDataContainer on Fabric** - Uses raw NBT instead
2. **PDC ≠ NBT** - Different structure, different type system
3. **UUID ≠ Identifier** - Attribute modifiers use incompatible ID systems
4. **No EliteMobs for Fabric** - Plugin doesn't exist, can't read Paper data anyway
5. **No automatic translation** - HuskSync can't convert without custom code per mod/plugin

### 🔪 **The Killswitch:**

`persistent_data: false` → Vanilla data syncs, mod/plugin data doesn't

**Your EliteMobs journey would survive Paper→Paper across 2 physical servers, but break the instant a Fabric instance entered the path.**
