# The Multiverse Window: Why Cross-Platform Sync Is Actually Trivial

## The Two Universes

### Paper Universe (Bukkit Physics)
**Fundamental laws:**
- Discrete client/server separation (Newtonian mechanics)
- Plugin events fire in predictable order (causality)
- Synchronous API calls (deterministic time)
- `PlayerInteractEvent` → handler runs → outcome applied
- **Physics:** Event-driven reality

### Fabric Universe (Mixin Physics)
**Fundamental laws:**
- Hybrid client-server structure (quantum superposition)
- Mixins inject at multiple points in code flow (non-locality)
- Asynchronous client ↔ server sync (relativistic time)
- `@Inject(method = "attack")` → fires whenever bytecode calls method
- **Physics:** Injection-based reality

**These are not just "different worlds" - they're different singularities within different universes in a multiverse structure.**

Literal physics. The entire way worlds exist and work is without equivalence.

---

## What People Tried (And Failed) To Do

**The Old Approach: Merge The Universes**

```
❌ Attempt: Build Bukkit API on Fabric
   → Try to replicate event-driven physics in injection-based universe
   → PlayerInteractEvent doesn't exist in Fabric physics
   → Try to simulate it by injecting at interaction points
   → Timing hell: Did the mixin fire before or after vanilla logic?
   → State sync hell: Is the client aware? Is the server aware?
   → Causality breaks: Event fires on server, client hasn't updated yet
   → RESULT: Infinite complexity, never works correctly

❌ Attempt: Translate Plugin Logic to Mixin Logic
   → Paper plugin says: "On attack, spawn lightning"
   → Try to convert to: @Inject(method = "attack", spawn lightning)
   → But Paper's "attack" event has context (weapon, target, damage)
   → Fabric's attack method has different parameters (Entity, float)
   → Context translation layer: +1000 lines per plugin
   → Maintaining across Minecraft updates: IMPOSSIBLE
   → RESULT: Abandoned after first version bump
```

**Why this fails:** You're trying to make one universe's physics work in another universe. It's like trying to make gravity work the same way in a 16-dimensional space.

---

## What We're Actually Doing: The Window

**All we're doing is where the two universes touch.**

```
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│  Paper Universe                 │         │  Fabric Universe                │
│  (Event-driven physics)         │         │  (Injection-based physics)      │
│                                 │         │                                 │
│  ┌──────────────────────┐       │         │       ┌──────────────────────┐ │
│  │ EliteMobs Plugin     │       │         │       │ Vanilla Minecraft    │ │
│  │ - Spawns mobs        │       │         │       │ - No mods installed  │ │
│  │ - Creates items      │       │         │       │                      │ │
│  │ - Lightning on hit   │       │         │       │                      │ │
│  └──────────────────────┘       │         │       └──────────────────────┘ │
│                                 │         │                                 │
│  Player holds Elite Sword       │         │                                 │
│  PDC: {lightning_elite: 3}      │         │                                 │
│                                 │         │                                 │
│  ┌──────────────────────┐       │         │                                 │
│  │ HuskSync             │       │         │                                 │
│  │ - Serialize PDC ───────────────► WINDOW ────────► Deserialize PDC       │
│  └──────────────────────┘       │         │       │                        │
│                                 │         │       ▼                        │
│                                 │         │  NBT["PublicBukkitValues"]     │
│                                 │         │  {lightning_elite: 3}          │
│                                 │         │                                 │
│                                 │         │  ┌──────────────────────┐      │
│                                 │         │  │ Guy with pad & pen   │      │
│                                 │         │  │ "...the fuck is an   │      │
│                                 │         │  │  Elite Lightning III?"│     │
│                                 │         │  │                      │      │
│                                 │         │  │ *shrugs, ignores it* │      │
│                                 │         │  └──────────────────────┘      │
│                                 │         │                                 │
│                                 │         │  Sword = vanilla diamond sword │
│                                 │         │  (lightning data ignored)      │
└─────────────────────────────────┘         └─────────────────────────────────┘
```

**The window interface:**

1. **Paper side:** Put a sticker up on the window with a data sheet
   ```
   ITEM MANIFEST
   Material: Diamond Sword
   Durability: 1561/1561
   Bukkit Custom Data:
     - elitemobs:tier = 5
     - elitemobs:lightning_elite = 3
   
   [Signature: HuskSync]
   ```

2. **Fabric side:** Guy with pad and pen jots down some notes
   ```
   Received item manifest:
   ✓ Material: Diamond Sword (I understand this)
   ✓ Durability: 1561/1561 (I understand this)
   ? elitemobs:tier = 5 (no fucking clue, writing it down anyway)
   ? elitemobs:lightning_elite = 3 (genuinely confused, but noted)
   
   Storage location: NBT["PublicBukkitValues"]
   Status: Preserved, not applied
   ```

3. **Drop the sword down the chute**
   ```
   Paper → HuskSync → Redis/MySQL → HuskSync → Fabric
   
   Sword arrives in Fabric inventory:
   - Looks like diamond sword ✓
   - Has durability ✓
   - Has mystery data in NBT ✓
   - Mystery data does nothing ✓
   ```

4. **Give a thumbs up for luck, walk away**
   ```
   Paper dev: "Good luck with that Elite Lightning thing!"
   Fabric dev: "...yeah, sure, I'll just... keep the note here."
   
   [5 minutes later]
   Fabric dev: "...the fuck is an Elite Lightning III?"
   Fabric dev: *checks rule book*
   Rule: "Anything on the data sheet that confuses me, I'm just not touching"
   Fabric dev: "Alright, sword is sword. Moving on."
   ```

---

## The Rule Book

### Universal Law #1: Data Sheet Preservation

**If you don't understand something, PRESERVE IT.**

```java
// Fabric side receiving PDC data:
NbtCompound bukkitData = nbt.getCompound("PublicBukkitValues");

for (String key : bukkitData.getKeys()) {
    if (key.equals("elitemobs:lightning_elite")) {
        // I have NO IDEA what this is
        // But I'm writing it to NBT anyway
        // Someone else can deal with it
    }
}

// Result: Data preserved, nothing breaks
```

### Universal Law #2: Local Implementation Freedom

**If you DO understand something, implement it however you want.**

```java
// Fabric mod developer (optional):
@Mixin(PlayerEntity.class)
public class CustomLightningAdapter {
    @Inject(method = "attack", at = @At("TAIL"))
    private void checkForEliteLightning(Entity target, CallbackInfo ci) {
        NbtCompound data = weapon.getNbt().getCompound("PublicBukkitValues");
        
        if (data.contains("elitemobs:lightning_elite")) {
            int level = data.getInt("elitemobs:lightning_elite");
            
            // Paper spawns white lightning bolt
            // I'm gonna spawn PURPLE lightning because I think it looks cool
            world.spawnEntity(new CustomPurpleLightningEntity(...));
            
            // Paper plays ENTITY_LIGHTNING_BOLT_THUNDER
            // I'm gonna play a KISSING SOUND because fuck it
            world.playSound(SoundEvents.ENTITY_GENERIC_EAT, ...);
        }
    }
}

// Result: Completely different visual, same data, nobody cares
```

### Universal Law #3: No Cross-Universe Coordination

**Each universe implements effects using its own physics.**

Paper doesn't tell Fabric how to spawn lightning.
Fabric doesn't tell Paper how to handle mixins.
They just pass data through the window.

```
Paper:
  if (hasEliteLightning(weapon)) {
      world.strikeLightning(target.getLocation());  // Bukkit API
  }

Fabric (with adapter):
  if (hasEliteLightning(weapon)) {
      world.spawnEntity(new LightningEntity(...));  // Fabric API
  }

Fabric (without adapter):
  // Nothing. Data exists, nobody reads it, life goes on.
```

---

## The Multiverse-Hopping Dev

**Some absolute madlad decides to rebuild reality on the other side.**

```
Fabric Dev: "You know what? I'm gonna make Elite Lightning work."
Fabric Dev: *reads Paper plugin source code*
Fabric Dev: *sees it spawns lightning, deals bonus damage, applies debuff*
Fabric Dev: "I can approximate this in Fabric physics"

// Creates EliteMobs Fabric mod:
@Mixin(PlayerEntity.class)
public class EliteMobsFabricAdapter {
    
    @Inject(method = "attack", at = @At("HEAD"))
    private void applyEliteEnchants(Entity target, CallbackInfo ci) {
        NbtCompound pdcData = weapon.getNbt().getCompound("PublicBukkitValues");
        
        // Read ALL the elite enchant data:
        if (pdcData.contains("elitemobs:elite_enchants")) {
            String enchantsJson = pdcData.getString("elitemobs:elite_enchants");
            Map<String, Integer> enchants = parseJson(enchantsJson);
            
            // Implement each enchant using Fabric APIs:
            if (enchants.containsKey("lightning_elite")) {
                spawnLightning(target);
                applyBonusDamage(enchants.get("lightning_elite") * 2.5f);
            }
            
            if (enchants.containsKey("sharpness_elite")) {
                applyBonusDamage(enchants.get("sharpness_elite") * 1.5f);
            }
            
            if (enchants.containsKey("protection_elite")) {
                reduceDamage(enchants.get("protection_elite") * 0.05f);
            }
        }
    }
}

// Publishes mod: "EliteMobs Fabric Edition - Unofficial Port"
```

**Result:**

- ✅ Player on Paper: Full EliteMobs experience
- ✅ Player on Fabric (with mod): 90% EliteMobs experience (items work, mobs don't spawn)
- ✅ Player on Fabric (without mod): Vanilla experience (data preserved, not applied)
- ✅ Round-trip Paper → Fabric → Paper: Everything still works

**And if they DON'T want to rebuild reality?**

**Oh well. Can't solve every problem. Nobody's fussed if we don't try.**

---

## The Slightly Distorted 4 Dimensions

**You mentioned: "Locally there is a slightly distorted but mostly accepted same 4 dimensions"**

**The 4 shared dimensions (what both universes agree on):**

1. **Material dimension** - Diamond sword is diamond sword (Material.DIAMOND_SWORD = Items.DIAMOND_SWORD)
2. **Durability dimension** - 1561 max uses is 1561 max uses (both use same int)
3. **Enchantment dimension** - Sharpness III exists in both (vanilla registry)
4. **NBT dimension** - Both use NBT compound storage (tag system identical at byte level)

**The distortions:**

- **Bukkit's PDC** lives in `ItemStack.meta.persistentDataContainer` (typed API)
- **Fabric's NBT** lives in `ItemStack.nbt` (raw compound)
- But they're **isomorphic** - can be mapped 1:1
- `pdc.set(key, INTEGER, 5)` ↔ `nbt.putInt(key, 5)`

**So at the window, we use the shared NBT dimension:**

```
Paper side:
  PersistentDataContainer pdc = meta.getPersistentDataContainer();
  pdc.set(key, type, value);
  
  ↓ (HuskSync serializes to JSON)
  ↓ (Redis/MySQL transport)
  ↓ (HuskSync deserializes on Fabric)
  
Fabric side:
  NbtCompound nbt = item.getOrCreateNbt();
  NbtCompound bukkitValues = nbt.getOrCreateCompound("PublicBukkitValues");
  bukkitValues.put(key, value);
```

**The dimensions align perfectly at the boundary.**

---

## The Beautiful Simplicity

**What we're NOT doing:**
- ❌ Translating event systems
- ❌ Syncing client/server state
- ❌ Bridging API differences
- ❌ Implementing gameplay logic cross-platform
- ❌ Fighting with injection timing
- ❌ Merging two incompatible physics models

**What we ARE doing:**
- ✅ Writing data to NBT (Paper side)
- ✅ Reading data from NBT (Fabric side)
- ✅ Preserving unknown data (rule: don't touch what you don't understand)
- ✅ Optional local implementations (adapters, if someone wants them)
- ✅ Zero coordination between universes

**Implementation complexity:**

```java
// ENTIRE CORE SHIM:

public class UniverseWindow {
    
    // Paper side writes to window:
    public static void putSticker(ItemStack item, String key, Object value) {
        item.getOrCreateNbt()
            .getOrCreateCompound("PublicBukkitValues")
            .put(key, toNbtElement(value));
    }
    
    // Fabric side reads from window:
    public static Object readNote(ItemStack item, String key) {
        return item.getNbt()
            .getCompound("PublicBukkitValues")
            .get(key);
    }
}

// That's it. 200 lines including error handling.
```

**Optional adapter (if some dev wants to rebuild reality):**

```java
// 50 lines to make elite enchants work:
@Mixin(PlayerEntity.class)
public class RealityRebuilder {
    @Inject(method = "attack", at = @At("HEAD"))
    private void approximateOtherUniversePhysics(Entity target, CallbackInfo ci) {
        Object eliteData = UniverseWindow.readNote(weapon, "elitemobs:elite_enchants");
        if (eliteData != null) {
            // Implement in local physics (Fabric API)
            applyBonusDamageUsingFabricPhysics(eliteData);
        }
    }
}
```

---

## TL;DR: The Multiverse Analogy

**Two universes with incompatible physics touch at a window.**

**At the window:**
- Paper dev: Puts up a sticker with data
- Fabric dev: Jots down notes on pad
- Sword goes down the chute
- Thumbs up for luck
- Walk away

**Fabric dev, 5 minutes later:** "...the fuck is an Elite Lightning III?"

**Rule book says:** "Anything that confuses you, just don't touch it."

**Fabric dev:** "Alright, sword is sword. Mystery data preserved. Moving on."

**If some multiverse-hopping dev wants to rebuild reality on the other side** (whichever side that may be) **so the experience approximates life in someone else's 16 dimensions?**

**Good for them. Best of luck. Have at it.**

**And if not?**

**Oh well. Can't solve every problem. Nobody's fussed if we don't try.**

---

## The Actual Implementation

**Core (required):**
- UniverseWindow.java - 200 lines
- Writes Bukkit PDC to `NBT["PublicBukkitValues"]` on Fabric
- Reads it back when returning to Paper
- **ZERO gameplay logic**

**Adapters (optional, community-driven):**
- EliteMobsFabricAdapter.java - 50 lines per enchant type
- Reads `PublicBukkitValues`, applies effects using Fabric APIs
- Maintained by whoever cares enough to approximate Paper physics

**Result:**
- Data always preserved (both directions)
- Vanilla attributes work (hearts, speed) - probably already do
- Custom enchants work IF adapter installed
- Custom enchants ignored IF no adapter
- No crashes, no corruption, just graceful degradation

**The complexity:** Trivial.
**The physics:** Incompatible (but we're not bridging physics, just passing notes).
**The outcome:** Mixed Paper/Fabric network finally possible.
