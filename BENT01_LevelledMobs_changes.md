# LevelledMobs Config for BENT01 - Standardized to Match Other Servers

## Changes needed in settings.yml:

### 1. rules.default-rule.settings.maxLevel
**Current**: 50
**Change to**: 10

### 2. rules.default-rule.use-preset
**Current**: 
```yaml
use-preset:
  - challenge-silver
  - lvlstrategy-weighted-random
  - lvlstrategy-distance-from-origin
  - lvlmodifier-player-variable
  - lvlmodifier-custom-formula
  - nametag-using-numbers
```

**Change to**:
```yaml
use-preset:
  - challenge-vanilla
  - nametag-using-numbers
  - custom-death-messages
```

### 3. rules.custom-rules (update specific rules)

Find these custom rules and change their `is-enabled` values:

**Nether World Levelling Strategy**:
```yaml
is-enabled: false  # Change from true to false
```

**End World Levelling Strategy**:
```yaml
is-enabled: false  # Change from true to false
```

**Custom Attributes for Specific Mobs**:
```yaml
is-enabled: false  # Change from true to false
```

**Bronze Challenge for Specific Mobs**:
```yaml
is-enabled: false  # Change from true to false
```

**Spawner Cube Entities**:
```yaml
is-enabled: false  # Change from true to false
```

**External Plugins with Vanilla Stats and Minimized Nametags**:
```yaml
is-enabled: false  # Change from true to false
```

### 4. rules.presets (multiple changes)

**lvlmodifier-player-variable.modifiers.player-variable-mod.decrease-output**:
```yaml
decrease-output: false  # Change from true to false
```

**lvlmodifier-player-variable.modifiers.player-variable-mod.recheck-players**:
```yaml
recheck-players: false  # Change from true to false
```

**lvlstrategy-distance-from-origin.strategies.distance-from-origin.enable-height-modifier**:
```yaml
enable-height-modifier: false  # Change from true to false
```

**lvlstrategy-distance-from-origin.strategies.distance-from-origin.scale-increase-downward**:
```yaml
scale-increase-downward: false  # Change from true to false
```

**lvlstrategy-random.strategies.random**:
```yaml
random: false  # Change from true to false
```

---

## Summary
BENT01 currently has advanced levelling features enabled (silver challenge, distance-based scaling, height modifiers). 
This standardizes it to match the other 10 servers which use vanilla challenge mode with simpler settings.
