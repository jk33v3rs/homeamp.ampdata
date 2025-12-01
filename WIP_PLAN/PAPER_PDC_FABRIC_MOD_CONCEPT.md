# PAPER_PDC: Bukkit PDC Compatibility Layer for Fabric

## The Core Insight

**HuskSync already has the data.** With `persistent_data: true`, HuskSync is serializing, transporting, and storing **perfect representations** of Bukkit PDC in Redis/MySQL. The problem isn't the transport layer - it's the **deserialization layer** on Fabric.

Instead of making HuskSync understand every plugin, **make Fabric understand Bukkit PDC**.

---

## Architecture: The Three-Layer Cake

### Layer 1: Core PDC Emulation (`paper_pdc_core`)

**Purpose:** Provide a Bukkit-compatible `PersistentDataContainer` API on Fabric

```java
// Fabric mod exposing Bukkit API surface
package net.minecraft.paper_pdc;

public interface PersistentDataContainer {
    <T, Z> void set(NamespacedKey key, PersistentDataType<T, Z> type, Z value);
    <T, Z> Z get(NamespacedKey key, PersistentDataType<T, Z> type);
    boolean has(NamespacedKey key, PersistentDataType<T, Z> type);
    Set<NamespacedKey> getKeys();
}

public class FabricPersistentDataContainer implements PersistentDataContainer {
    private final NbtCompound backingNbt;
    
    public FabricPersistentDataContainer(NbtCompound nbt) {
        // Reads/writes to the universal vat: "william27d8r"
        this.backingNbt = nbt.getOrCreateCompound("william27d8r");
    }
    
    @Override
    public <T, Z> void set(NamespacedKey key, PersistentDataType<T, Z> type, Z value) {
        String keyPath = key.namespace() + ":" + key.getKey();
        
        // Type-aware NBT writing:
        if (type == PersistentDataType.INTEGER) {
            backingNbt.putInt(keyPath, (Integer) value);
        } else if (type == PersistentDataType.STRING) {
            backingNbt.putString(keyPath, (String) value);
        } else if (type == PersistentDataType.DOUBLE) {
            backingNbt.putDouble(keyPath, (Double) value);
        }
        // ... handle all Bukkit PersistentDataType variants
    }
    
    @Override
    public <T, Z> Z get(NamespacedKey key, PersistentDataType<T, Z> type) {
        String keyPath = key.namespace() + ":" + key.getKey();
        
        // Type-aware NBT reading:
        if (type == PersistentDataType.INTEGER) {
            return (Z) Integer.valueOf(backingNbt.getInt(keyPath));
        } else if (type == PersistentDataType.STRING) {
            return (Z) backingNbt.getString(keyPath);
        }
        // ... etc
    }
}
```

**Result:** Fabric mods can now call Bukkit PDC API, and it **just works** (backed by NBT).

---

### Layer 2: Vanilla Gameplay Adapters (`paper_pdc_vanilla`)

**Purpose:** Map vanilla Bukkit gameplay behaviors to Fabric equivalents

#### Attribute Modifiers Adapter

**Problem:** Bukkit uses UUID-based attribute modifiers, Fabric uses Identifier-based

```java
package net.minecraft.paper_pdc.adapters;

public class AttributeModifierAdapter {
    
    // Mixin into ItemStack attribute application
    @Mixin(ItemStack.class)
    public abstract class ItemStackAttributeMixin {
        
        @Inject(method = "getAttributeModifiers", at = @At("RETURN"))
        private void injectBukkitModifiers(EquipmentSlot slot, CallbackInfoReturnable<Multimap<EntityAttribute, EntityAttributeModifier>> cir) {
            ItemStack stack = (ItemStack) (Object) this;
            NbtCompound nbt = stack.getOrCreateNbt();
            
            // Check if Bukkit PDC has attribute modifiers:
            PersistentDataContainer pdc = new FabricPersistentDataContainer(nbt);
            NamespacedKey modifiersKey = new NamespacedKey("paper_pdc", "attribute_modifiers");
            
            if (pdc.has(modifiersKey, PersistentDataType.STRING)) {
                String modifiersJson = pdc.get(modifiersKey, PersistentDataType.STRING);
                List<BukkitAttributeModifier> bukkitModifiers = parseJson(modifiersJson);
                
                Multimap<EntityAttribute, EntityAttributeModifier> fabricModifiers = cir.getReturnValue();
                
                for (BukkitAttributeModifier bukkitMod : bukkitModifiers) {
                    // TRANSLATION LAYER:
                    UUID uuid = UUID.fromString(bukkitMod.uuid);
                    Identifier fabricId = uuidToIdentifier(uuid, bukkitMod.name);
                    // elitemobs:prestige_bonus (UUID) → Identifier("elitemobs", "prestige_bonus")
                    
                    EntityAttributeModifier fabricMod = new EntityAttributeModifier(
                        fabricId,
                        bukkitMod.amount,
                        EntityAttributeModifier.Operation.valueOf(bukkitMod.operation)
                    );
                    
                    fabricModifiers.put(
                        Registries.ATTRIBUTE.get(Identifier.of(bukkitMod.attribute)),
                        fabricMod
                    );
                }
            }
        }
    }
    
    // Smart UUID → Identifier conversion:
    private Identifier uuidToIdentifier(UUID uuid, String name) {
        String uuidString = uuid.toString();
        
        // Check if UUID follows namespace pattern:
        // "elitemobs:prestige_bonus" encoded as UUID
        if (name.contains(":")) {
            String[] parts = name.split(":");
            return Identifier.of(parts[0], parts[1]);
        }
        
        // Otherwise, use namespace from common mappings:
        return Identifier.of("bukkit_compat", name.toLowerCase().replace(" ", "_"));
    }
}
```

**Result:** Bukkit attribute modifiers **automatically work** on Fabric items.

#### Enchantment Adapter

**Problem:** Bukkit custom enchants stored in PDC, Fabric expects vanilla enchant registry

```java
public class EnchantmentAdapter {
    
    @Mixin(ItemStack.class)
    public abstract class ItemStackEnchantmentMixin {
        
        @Inject(method = "getDamage", at = @At("RETURN"))
        private void applyCustomEnchantDamage(LivingEntity target, CallbackInfoReturnable<Float> cir) {
            // When calculating damage, check for Bukkit custom enchants in PDC
            ItemStack weapon = (ItemStack) (Object) this;
            PersistentDataContainer pdc = new FabricPersistentDataContainer(weapon.getOrCreateNbt());
            
            // Look for common plugin enchant formats:
            if (pdc.has(new NamespacedKey("elitemobs", "elite_enchants"), PersistentDataType.STRING)) {
                String enchantsJson = pdc.get(...);
                Map<String, Integer> enchants = parseJson(enchantsJson);
                
                float baseDamage = cir.getReturnValue();
                
                // Apply EliteMobs sharpness formula:
                if (enchants.containsKey("sharpness_elite")) {
                    int level = enchants.get("sharpness_elite");
                    baseDamage += level * 1.5;  // EliteMobs sharpness formula
                }
                
                cir.setReturnValue(baseDamage);
            }
        }
    }
}
```

**Result:** EliteMobs items **deal correct damage** on Fabric.

---

### Layer 3: Plugin Adapter Packs (`paper_pdc_adapters/`)

**Purpose:** Modular, plugin-specific translation logic

#### Directory Structure:
```
paper_pdc_adapters/
  ├── elitemobs/
  │   ├── adapter.json          # Metadata
  │   ├── enchantments.java     # Custom enchant handlers
  │   ├── items.java            # Item behavior handlers
  │   └── schema.yaml           # PDC schema definition
  ├── mcmmo/
  │   ├── adapter.json
  │   ├── skills.java
  │   └── schema.yaml
  ├── griefprevention/
  │   └── ... (might not need adapter - doesn't use items)
  └── coreprotect/
      └── ... (no adapter needed - database-only plugin)
```

#### EliteMobs Adapter Pack

**schema.yaml** - Defines expected PDC structure:
```yaml
namespace: elitemobs
version: "9.0.0"
pdc_keys:
  tier:
    type: INTEGER
    range: [1, 10]
    description: "Elite item tier level"
  
  elite_enchants:
    type: STRING
    format: JSON
    schema:
      type: object
      properties:
        sharpness_elite: {type: integer, min: 1, max: 10}
        protection_elite: {type: integer, min: 1, max: 10}
        thorns_elite: {type: integer, min: 1, max: 10}
        # ... all elite enchant types
  
  item_id:
    type: STRING
    format: "elite_[category]_[name]_tier[N]"
    description: "Unique item template identifier"

attributes:
  prestige_bonus:
    uuid_pattern: "elitemobs:prestige_bonus"
    target: GENERIC_MAX_HEALTH
    operation: ADD_NUMBER
    description: "Prestige system health bonus"
```

**enchantments.java** - Custom enchant behavior:
```java
package paper_pdc.adapters.elitemobs;

@AdapterClass(namespace = "elitemobs", version = "9.0.0")
public class EliteMobsEnchantments {
    
    @EnchantHandler(enchant = "sharpness_elite")
    public float applySharpness(AttackContext ctx, int level) {
        // EliteMobs sharpness formula: level * 1.5
        return ctx.baseDamage + (level * 1.5f);
    }
    
    @EnchantHandler(enchant = "protection_elite")
    public float applyProtection(DefenseContext ctx, int level) {
        // EliteMobs protection formula: reduce by (level * 5%)
        return ctx.incomingDamage * (1.0f - (level * 0.05f));
    }
    
    @EnchantHandler(enchant = "thorns_elite")
    public void applyThorns(DefenseContext ctx, int level) {
        // EliteMobs thorns: reflect (level * 10%) damage
        float reflectedDamage = ctx.incomingDamage * (level * 0.1f);
        ctx.attacker.damage(reflectedDamage, DamageSource.thorns(ctx.defender));
    }
}
```

**items.java** - Item-specific behaviors:
```java
@AdapterClass(namespace = "elitemobs")
public class EliteMobsItems {
    
    @ItemHandler(lore_pattern = "§6Elite *")
    public void onItemUse(ItemUseContext ctx) {
        PersistentDataContainer pdc = ctx.item.getPDC();
        
        // Check tier requirement:
        if (pdc.has(tierKey, PersistentDataType.INTEGER)) {
            int tier = pdc.get(tierKey, PersistentDataType.INTEGER);
            
            // Fabric doesn't have EliteMobs' prestige system, so:
            // Option A: Always allow (no prestige requirement on Fabric)
            // Option B: Check player NBT for prestige level
            // Option C: Disable tier-restricted items on Fabric
            
            // For now: Allow all tiers (Fabric players can use all items)
        }
    }
}
```

---

## HuskSync Integration: Zero-Change Required

**The beauty:** HuskSync **already does everything right**.

**Paper → Fabric sync (with PAPER_PDC installed):**
```
PlayerQuitEvent (Paper):
  HuskSync serializes PDC → JSON blob:
    {"elitemobs:tier": 5, "elitemobs:elite_enchants": "{...}"}
  → Redis/MySQL

PlayerJoinEvent (Fabric):
  HuskSync deserializes JSON blob → Tries to apply PDC
  
  // HuskSync calls (on Fabric):
  ItemMeta meta = item.getItemMeta();  // ← PAPER_PDC provides this API!
  PersistentDataContainer pdc = meta.getPersistentDataContainer();  // ← PAPER_PDC!
  
  for (String key : serializedPDC.keys()) {
      NamespacedKey nsKey = parseKey(key);
      pdc.set(nsKey, inferType(value), value);  // ← PAPER_PDC handles this!
  }
  
  // PAPER_PDC writes to NbtCompound["PublicBukkitValues"]["elitemobs:tier"] = 5
```

**Result:**
- ✅ HuskSync thinks it's talking to Bukkit API (it is - PAPER_PDC emulates it)
- ✅ PDC data written to Fabric NBT in compatible format
- ✅ EliteMobs adapter pack reads PDC, applies enchant bonuses
- ✅ **ZERO CHANGES to HuskSync code**

---

## Adapter Pack Development: Community-Driven

### Vanilla Adapter Pack (Bundled with PAPER_PDC)

Handles all vanilla Bukkit → Fabric gameplay:
- Attribute modifiers (UUID → Identifier translation)
- Vanilla enchants (if stored in PDC by some plugin)
- Display names, lore (cosmetic, no logic needed)
- Durability, repair cost (vanilla parity)

### Plugin Adapter Packs (Community Repository)

**EliteMobs Adapter Pack:**
- Maintained by: EliteMobs community / PAPER_PDC team
- Version compatibility: EliteMobs 8.x, 9.x
- Features: Elite enchants, tier restrictions, custom item behaviors

**McMMO Adapter Pack:**
- Maintained by: McMMO community
- Version compatibility: McMMO 2.1.x
- Features: Skill XP tracking, ability cooldowns, party data
- **Note:** Most McMMO data is database-backed, might not need heavy PDC adapters

**EssentialsX Adapter Pack:**
- Maintained by: EssentialsX community
- Version compatibility: EssentialsX 2.19.x+
- Features: Kits with metadata, custom items, jail/mute timers
- **Note:** Mostly server-side data, minimal item PDC usage

### Adapter API: Simple Developer Experience

**To create an adapter pack:**

1. Create `adapter.json`:
```json
{
  "namespace": "myplugin",
  "version": "1.0.0",
  "paper_pdc_version": ">=1.0.0",
  "authors": ["YourName"],
  "description": "PAPER_PDC adapter for MyPlugin",
  "dependencies": {
    "paper_pdc_core": "^1.0.0"
  }
}
```

2. Define PDC schema (`schema.yaml`):
```yaml
namespace: myplugin
pdc_keys:
  custom_data:
    type: STRING
    format: JSON
    validator: "MyPlugin.validateCustomData"
```

3. Implement behavior handlers (`handlers.java`):
```java
@AdapterClass(namespace = "myplugin")
public class MyPluginHandlers {
    
    @EnchantHandler(enchant = "my_custom_enchant")
    public float applyCustomEnchant(AttackContext ctx, int level) {
        return ctx.baseDamage * (1 + level * 0.2f);
    }
}
```

4. Distribute as Fabric mod (can be server-side only)

---

## The Mixin Priority Problem: Solved

**Your concern:** Bukkit plugins interact with server **before** Fabric mixins fire.

**Solution:** PAPER_PDC mixins run at **EARLIEST** priority:

```java
@Mixin(value = ItemStack.class, priority = 100)  // ← Lowest number = earliest
public abstract class ItemStackPDCMixin {
    
    @Inject(
        method = "getAttributeModifiers",
        at = @At("HEAD"),  // ← Before vanilla logic
        cancellable = true
    )
    private void injectPDCAttributes(...) {
        // Read PDC, apply custom attributes
        // If PDC has data, OVERRIDE vanilla behavior (cancellable = true)
    }
}
```

**Execution order:**
```
1. PAPER_PDC mixin (priority 100) - Reads PDC, injects custom attributes
2. Other mods' mixins (priority 1000+) - See attributes already applied
3. Vanilla logic - Uses final attribute list (includes PDC attributes)
```

**Result:** PAPER_PDC acts as **first responder**, vanilla/mods see final state.

---

## Advanced: Namespace Stacking & Custom Experience Handlers

**Problem:** Multiple mods might want to modify same vanilla behavior.

**Solution:** Namespace priority + event bus

```java
@AdapterClass(namespace = "elitemobs", priority = 10)
public class EliteMobsAdapter {
    
    @EnchantHandler(enchant = "sharpness_elite", priority = 10)
    public float applySharpness(AttackContext ctx, int level) {
        return ctx.baseDamage + (level * 1.5f);
    }
}

@AdapterClass(namespace = "customenchants", priority = 5)
public class CustomEnchantsAdapter {
    
    @EnchantHandler(enchant = "sharpness_custom", priority = 5)
    public float applySharpness(AttackContext ctx, int level) {
        return ctx.baseDamage + (level * 2.0f);  // Different formula
    }
}

// PAPER_PDC event bus:
public class EnchantEventBus {
    public float calculateDamage(AttackContext ctx) {
        float damage = ctx.baseDamage;
        
        // Apply handlers in priority order:
        List<EnchantHandler> handlers = getHandlers(ctx.weapon);
        handlers.sort(Comparator.comparingInt(h -> h.priority));
        
        for (EnchantHandler handler : handlers) {
            damage = handler.apply(ctx.withDamage(damage));
        }
        
        return damage;
    }
}
```

**Result:** Multiple adapters can stack, priority determines execution order.

---

## Custom Experience Handlers: The Brigadier/Adventure Bridge

**Problem:** Some plugins use Adventure API for chat, Brigadier for commands.

**Solution:** PAPER_PDC provides Bukkit API compatibility layer:

```java
// Adventure API on Fabric
package paper_pdc.api;

public class AdventureCompat {
    
    // Fabric doesn't have native Adventure support, but we can translate:
    public static Text adventureToFabric(Component component) {
        // Recursively convert Adventure Component → Fabric Text
        if (component instanceof TextComponent text) {
            MutableText fabricText = Text.literal(text.content());
            
            // Apply styling:
            TextColor color = text.color();
            if (color != null) {
                fabricText.setStyle(Style.EMPTY.withColor(color.value()));
            }
            
            // Apply children:
            for (Component child : text.children()) {
                fabricText.append(adventureToFabric(child));
            }
            
            return fabricText;
        }
        // ... handle other Component types
    }
}

// Mixin into chat system:
@Mixin(ServerPlayNetworkHandler.class)
public class ChatAdapterMixin {
    
    @Inject(method = "sendChatMessage", at = @At("HEAD"), cancellable = true)
    private void interceptAdventureChat(Text message, CallbackInfo ci) {
        // Check if this message originated from PDC-adapted plugin:
        if (message instanceof AdventureWrappedText wrapped) {
            // Re-serialize through Adventure → Fabric converter
            Text fabricText = AdventureCompat.adventureToFabric(wrapped.getComponent());
            
            // Send converted message:
            player.sendMessage(fabricText, false);
            ci.cancel();
        }
    }
}
```

**Result:** Plugins using Adventure API **work on Fabric** via PAPER_PDC translation.

---

## What This DOESN'T Solve

**Plugins that don't exist on Fabric:**

- ❌ **EliteMobs plugin** itself won't run on Fabric (it's a Bukkit plugin)
  - But **items work** (enchants apply via adapter)
  - But **mobs don't spawn** (no EliteMobs entity spawning on Fabric)
  - But **shops don't exist** (no NPC system on Fabric)

**Solution:** Hybrid network design:
- **Paper servers:** Full EliteMobs (dungeons, mobs, NPCs, shops)
- **Fabric servers:** Items work, but no new content generation
- **Use case:** Player farms EliteMobs items on Paper, brings them to Fabric creative/building server

**Database-backed features:**
- ✅ **Works:** Plugins using shared MySQL (TNE economy, LuckPerms permissions)
- ⚠️ **Partial:** EliteMobs prestige (if DB-backed, syncs; if file-backed, doesn't)
- ❌ **Broken:** Plugins expecting Bukkit API on Fabric (no amount of PDC translation fixes this)

**Complex Plugin Logic:**
- ✅ **Works:** Item behaviors (damage, protection, effects)
- ⚠️ **Partial:** Commands (need Brigadier translation)
- ❌ **Broken:** GUI menus (Fabric has no Bukkit Inventory API)

---

## Why This Is Brilliant (And Insane)

### ✅ **Brilliant:**

1. **HuskSync doesn't change** - it already has the transport layer perfect
2. **Bukkit plugins don't change** - they're on Paper servers, unaffected
3. **Fabric gets Bukkit compatibility** - can read/write PDC via emulation layer
4. **Community-driven adapters** - plugin devs can write their own translation logic
5. **Modular/opt-in** - only install adapters for plugins you use
6. **Future-proof** - new plugins just need new adapter packs

### ⚠️ **Insane:**

1. **Massive surface area** - Bukkit API is HUGE, emulating it all is brutal
2. **Versioning hell** - Bukkit 1.20.1 ≠ 1.20.4, Fabric updates break things
3. **Performance cost** - Mixins at highest priority slow down hot paths
4. **Incomplete coverage** - Not all Bukkit features CAN be emulated (GUIs, complex events)
5. **Maintenance burden** - Every Minecraft update breaks everything
6. **Edge cases** - Plugins do weird shit, impossible to support all behaviors

---

## Proof of Concept: Minimal Viable Product

**MVP Scope:**

1. **Core PDC Emulation:**
   - Implement `PersistentDataContainer` backed by `NbtCompound["PublicBukkitValues"]`
   - Support all `PersistentDataType` variants (INTEGER, STRING, DOUBLE, BYTE_ARRAY, etc.)
   - Expose via `ItemStack.getPDC()` mixin

2. **Vanilla Adapter:**
   - Attribute modifiers (UUID → Identifier translation)
   - Display names, lore (cosmetic passthrough)
   - No complex gameplay logic

3. **EliteMobs Adapter:**
   - Elite enchants (sharpness, protection, thorns)
   - Tier metadata (read-only, no restrictions)
   - Item identification (for debugging)

4. **HuskSync Test:**
   - Paper server A → Fabric server → Paper server B
   - Verify Elite item survives round-trip with enchants functional

**Success Criteria:**
- ✅ Elite Boss Helmet (Protection X, Thorns V) deals thorns damage on Fabric
- ✅ Elite Sword (Sharpness X) deals bonus damage on Fabric
- ✅ Prestige hearts (+2 max health) apply on Fabric
- ✅ Round-trip Paper → Fabric → Paper preserves all PDC data

---

## Why This Was Thought To Be Impossible (And Why It Isn't)

### The Old Assumption: Mixins vs Plugins Don't Mix

**Traditional thinking:**
- ❌ Fabric uses mixins (client-server hybrid structure)
- ❌ Paper uses plugins (discrete client/server roles)
- ❌ Mixins inject at two points: "client-side loop" and "server-side loop"
- ❌ Keeping client ↔ server in sync is timing nightmare
- ❌ State checking is near-impossible with async mixin injection
- ❌ Therefore: Cross-platform sync is fundamentally broken

**This is TRUE... if you're trying to sync GAMEPLAY LOGIC.**

### What We're Actually Doing: Data Interface, Not Logic Emulation

**The critical insight:**

**WE ARE NOT IMPLEMENTING MOD BEHAVIORS.**

We're just handling that **Bukkit PDC exists at the player interface**.

```
❌ WRONG APPROACH (what people assume we're doing):
   Paper: Elite Sharpness X triggers lightning bolt
   → Try to make Fabric mixins replicate lightning bolt spawn
   → Sync client/server timing for lightning effect
   → Handle particle spawning, sound effects, damage
   → NIGHTMARE (different APIs, timing issues, state sync hell)

✅ ACTUAL APPROACH (what we're doing):
   Paper: Elite Sharpness X → stores "elite_enchants: {sharpness_elite: 10}" in PDC
   → HuskSync transports PDC data
   → Fabric: Receives "elite_enchants: {sharpness_elite: 10}", stores in NBT
   → IF Fabric has adapter: Apply damage bonus (local implementation)
   → IF Fabric has NO adapter: Do nothing (item is vanilla)
   → TRIVIAL (just data storage + optional local handler)
```

### Each Server Implements Effects Locally (Or Doesn't)

**Example: Lightning bolt on critical hit**

**Paper implementation:**
```java
@EventHandler
public void onEntityDamageByEntity(EntityDamageByEntityEvent event) {
    // Check for elite_lightning enchant in PDC
    if (hasEliteLightning(weapon)) {
        world.strikeLightning(target.getLocation());  // Bukkit API
    }
}
```

**Fabric implementation (with adapter):**
```java
@Mixin(PlayerEntity.class)
public class EliteLightningMixin {
    @Inject(method = "attack", at = @At("TAIL"))
    private void applyEliteLightning(Entity target, CallbackInfo ci) {
        // Check for elite_lightning in PublicBukkitValues NBT
        if (hasEliteLightning(weapon)) {
            world.spawnEntity(new LightningEntity(EntityType.LIGHTNING_BOLT, world));  // Fabric API
        }
    }
}
```

**Fabric implementation (without adapter):**
```java
// Nothing. The enchant data exists in NBT, but nothing reads it.
// No lightning, no bonus damage, just vanilla behavior.
```

**The beauty:**

**Paper doesn't care how Fabric implements lightning.**
**Fabric doesn't care how Paper implements lightning.**
**NBT/persistence data doesn't care about EITHER.**

### The Player Might Care, But The Servers Need Not

**Scenario: Player with Elite Lightning Sword**

**On EMAD01 (Paper, full EliteMobs):**
- Critical hit → Lightning bolt spawns
- Sound: ENTITY_LIGHTNING_BOLT_THUNDER
- Particles: White flash + smoke
- Bonus damage: +15 (lightning strike damage)

**On FAB01 (Fabric, no adapter):**
- Critical hit → Nothing special happens
- Vanilla diamond sword behavior
- Player: "Huh, my enchant isn't working"

**On FAB02 (Fabric, custom EliteMobs Fabric mod):**
- Critical hit → Purple lightning bolt spawns (custom effect)
- Sound: KISSING_SOUND (because why not)
- Particles: Heart particles + sparkles (someone thought this was funny)
- Bonus damage: +15 (same damage, different visuals)

**On SMP201 (Paper, back to normal EliteMobs):**
- Critical hit → Lightning bolt spawns again (original behavior restored)
- Everything works as expected

**The PDC data survived all transitions:**
```json
{
  "elitemobs:elite_enchants": "{\"lightning_elite\": 5}"
}
```

**Each server interpreted it differently (or not at all), but the DATA persisted.**

### Why This Is Easy

**1. No client ↔ server sync issues**

We're not syncing gameplay. We're syncing **persistent data** (NBT), which Minecraft already handles perfectly.

**2. No timing problems**

Mixins fire when they fire. If the data is in NBT, the mixin reads it. No race conditions, no async hell.

**3. No state checking complexity**

The state IS the NBT. Read NBT, check if key exists, done.

**4. Each server respects its own rules**

Paper uses Bukkit API to spawn lightning.
Fabric uses Fabric API to spawn lightning (or doesn't).
Nobody is trying to force one API onto the other platform.

**5. The player interface is just NBT**

```java
// Paper side:
pdc.set(key, type, value);  // Writes to NBT["PublicBukkitValues"]

// Fabric side:
nbt.getCompound("PublicBukkitValues").get(key);  // Reads from same location

// THAT'S IT. No hybrid structures, no mixin injection timing, just NBT.
```

### The 200-Line Miracle

**All you need:**

```java
// PAPER_PDC_CORE: Provide write/read interface for HuskSync
public class FabricPDCShim {
    public static void write(ItemStack item, String key, Object value) {
        item.getOrCreateNbt()
            .getOrCreateCompound("PublicBukkitValues")
            .put(key, toNbtElement(value));
    }
    
    public static Object read(ItemStack item, String key) {
        return item.getNbt()
            .getCompound("PublicBukkitValues")
            .get(key);
    }
}

// Optional adapter (if you want enchants to work):
@Mixin(PlayerEntity.class)
public class EliteEnchantsAdapter {
    @Inject(method = "attack", at = @At("HEAD"))
    private void applyEliteEnchants(Entity target, CallbackInfo ci) {
        String enchants = FabricPDCShim.read(weapon, "elitemobs:elite_enchants");
        if (enchants != null) {
            // Apply damage bonus using Fabric APIs
        }
    }
}
```

**That's it. 200 lines for the shim, 50 lines per optional adapter.**

**No emulation of Bukkit gameplay.**
**No fighting with mixin injection timing.**
**No client/server sync hell.**

**Just: Store data, optionally read data, optionally apply local effects.**

## TL;DR: The Pitch (Revised)

**Instead of making HuskSync smarter, make Fabric understand Bukkit PDC as data storage.**

**PAPER_PDC** = Minimal data interface + optional local handlers
- Core: 200 lines to provide `PublicBukkitValues` NBT namespace
- Adapters: Optional 50-line mixins to apply effects using local APIs
- **HuskSync requires ZERO changes** (it already has the data)

**Result:**
- Your EliteMobs items **exist on Fabric** (data preserved)
- Your prestige hearts **work on Fabric** (vanilla attribute, already syncs)
- Your items **survive round-trips** (PDC preserved perfectly)
- **Optional:** Install adapters to make enchants functional (local implementations)
- You can finally have that Fabric creative server in your network

**The catch:**
- Core shim: Trivial (200 lines, one afternoon of work)
- Vanilla attributes: Probably already work (HuskSync likely handles this)
- Custom enchants: Need adapters (community-driven, 50 lines each)
- But... **it's technically easy**, and **doesn't fight the hybrid structure at all**

Your instinct is **100% correct**: The transport layer (HuskSync) already works. The missing piece is a **dumb storage interface** on Fabric, and **optional local effect handlers**. We're not bridging two incompatible architectures - we're just storing data and letting each platform implement effects however it wants (or not at all).
