# Admin Tooling & Builder System Schema

**Purpose**: Define GUI builders, automation tools, and metadata management for network administration.

**Core Principle**: All tools operate on the hierarchical config system (Global → Server → Meta-Tag → Instance) with rank/permission awareness.

---

## Player Rank System (Universal Framework)

### Rank Definitions from EliteMobs
**Source**: `proposed_ranks.md` - Consolidated linguistic ranking system

#### Primary Ranks (0-19) - Progression Tiers
```yaml
ranks:
  0:  name: "Casual"           # Special: Prestige 0 Rank 0 = "Disabled - Disables Elites!"
  1:  name: "Fledgling"
  2:  name: "Novice"
  3:  name: "Pledged"
  4:  name: "Initiate"
  5:  name: "Apprentice"
  6:  name: "Adept"
  7:  name: "Exemplar"
  8:  name: "Superior"
  9:  name: "Master"
  10: name: "Grand Master"
  11: name: "Prime"
  12: name: "Apex"
  13: name: "Eternal"
  14: name: "Epic"
  15: name: "Mythic"
  16: name: "Worshipped"
  17: name: "Immortal"
  18: name: "Omnipotent"
  19: name: "Ultimate"
```

#### Prestige Ranks (0-29) - Mastery Tiers
```yaml
prestiges:
  0:  name: "Bystander"
  1:  name: "Onlooker"
  2:  name: "Wanderer"
  3:  name: "Traveller"
  4:  name: "Vagabond"
  5:  name: "Explorer"
  6:  name: "Adventurer"
  7:  name: "Surveyor"
  8:  name: "Navigator"
  9:  name: "Journeyman"
  10: name: "Pathfinder"
  11: name: "Trailblazer"
  12: name: "Pioneer"
  13: name: "Craftsman"
  14: name: "Specialist"
  15: name: "Artisan"
  16: name: "Veteran"
  17: name: "Sage"
  18: name: "Scholar"
  19: name: "Luminary"
  20: name: "Legend"
  21: name: "Titan"
  22: name: "Sovereign"
  23: name: "Ascendant"
  24: name: "Celestial"
  25: name: "Exalted"
  26: name: "Transcendent"
  27: name: "Divine"
  28: name: "Demigod"
  29: name: "Deity"
```

### Database Schema for Ranks

```sql
-- Universal rank definitions (used by ALL plugins that need ranks)
CREATE TABLE rank_definitions (
    rank_id INT PRIMARY KEY,              -- 0-19 for primary, 0-29 for prestige
    rank_type VARCHAR(16),                -- 'primary' or 'prestige'
    rank_name VARCHAR(32),                -- "Apprentice", "Legend", etc.
    rank_order INT,                       -- Display order in UIs
    
    -- Visual styling
    display_color VARCHAR(16),            -- &a, &e, &6, etc.
    chat_prefix TEXT,                     -- What shows in chat
    tab_prefix TEXT,                      -- What shows in tab list
    
    -- Permissions mapping
    luckperms_group VARCHAR(64),          -- Associated LuckPerms group (optional)
    
    is_active BOOLEAN DEFAULT true
);

-- Player rank assignments
CREATE TABLE player_ranks (
    player_uuid CHAR(36) PRIMARY KEY,
    
    -- Current rank
    current_rank_id INT REFERENCES rank_definitions(rank_id),
    current_prestige_id INT REFERENCES rank_definitions(rank_id),
    
    -- Progression tracking
    total_playtime_seconds BIGINT,
    total_quest_completions INT,
    total_mob_kills INT,
    rank_progress_percent DECIMAL(5,2),   -- % to next rank
    
    -- Timestamps
    last_rank_up TIMESTAMP,
    last_prestige TIMESTAMP,
    first_join TIMESTAMP DEFAULT NOW()
);
```

### Usage Examples

**Any plugin/builder can reference ranks**:
- Jobs: "Unlock job at rank 5 (Apprentice)"
- Quests: "Reward only for prestige 10+ (Pathfinder)"
- Shops: "Discount for rank 15+ (Mythic)"
- Permissions: "Grant fly at prestige 20 (Legend)"

---

## GUI Builder Tools

### 1. Job Builder (ExcellentJobs/JobsReborn)

#### Interface Layout
```
┌──────────────────────────────────────────────────────────────┐
│ Job Builder - Create/Edit Job                     [Template] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Job Name: [Miner___________]  Display Name: [&b&lMiner_____] │
│                                                               │
│ Description:                                                 │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Mine ores and stone to earn money!                    │   │
│ │                                                        │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Requirements:                                                │
│   [x] Min Rank: [Apprentice (5) ▼]                          │
│   [ ] Min Prestige: [None ▼]                                │
│   [ ] Permission: [jobs.join.miner___________]              │
│   [ ] Cost to Join: [1000_] coins                           │
│                                                               │
│ Max Level: [50_] │ XP Curve: [Linear ▼]                     │
│                                                               │
│ ─────────────────── Objectives ────────────────────          │
│                                                               │
│ ┌─ Block Break ─────────────────────────────────────┐       │
│ │ Block: [STONE ▼]                                  │       │
│ │ XP Gain: [5.0_]  │ Money Reward: [0.50_]         │       │
│ │ [+ Add Block] [- Remove]                          │       │
│ └────────────────────────────────────────────────────┘       │
│                                                               │
│ ┌─ Block Break ─────────────────────────────────────┐       │
│ │ Block: [DIAMOND_ORE ▼]                            │       │
│ │ XP Gain: [50.0_] │ Money Reward: [10.00_]        │       │
│ │ [+ Add Block] [- Remove]                          │       │
│ └────────────────────────────────────────────────────┘       │
│                                                               │
│ [+ Add Objective Type ▼]                                     │
│   - Block Break                                              │
│   - Block Place                                              │
│   - Mob Kill                                                 │
│   - Craft Item                                               │
│   - Fish                                                     │
│   - Enchant                                                  │
│                                                               │
│ ─────────────────── Deployment ────────────────────          │
│                                                               │
│ Deploy To:                                                   │
│   [x] All Instances (Global)                                │
│   [ ] Tagged: [survival ▼] [economy-enabled ▼]             │
│   [ ] Specific: [SMP101] [SMP201] [...]                    │
│                                                               │
│ [Save Job] [Test Locally] [Deploy] [Cancel]                 │
└──────────────────────────────────────────────────────────────┘
```

#### Generated Config Structure
```yaml
# Saved to: data/jobs/miner.yml
job:
  name: "Miner"
  display_name: "&b&lMiner"
  description: "Mine ores and stone to earn money!"
  
  requirements:
    min_rank: 5              # References rank_definitions.rank_id
    permission: "jobs.join.miner"
    cost: 1000
  
  max_level: 50
  xp_curve: "linear"
  
  objectives:
    block_break:
      - type: STONE
        xp: 5.0
        money: 0.50
      - type: DIAMOND_ORE
        xp: 50.0
        money: 10.00
  
  deployment:
    scope_type: "GLOBAL"
    # Applies to all instances unless overridden
```

#### Database Schema
```sql
CREATE TABLE job_definitions (
    job_id SERIAL PRIMARY KEY,
    job_name VARCHAR(64) UNIQUE,
    display_name TEXT,
    description TEXT,
    
    -- Requirements
    min_rank_id INT REFERENCES rank_definitions(rank_id),
    min_prestige_id INT REFERENCES rank_definitions(rank_id),
    required_permission VARCHAR(128),
    join_cost DECIMAL(10,2),
    
    -- Progression
    max_level INT DEFAULT 50,
    xp_curve VARCHAR(16) DEFAULT 'linear',  -- linear, exponential, etc.
    
    -- Deployment (uses config_rules hierarchy)
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',
    scope_selector VARCHAR(64),
    
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE job_objectives (
    objective_id SERIAL PRIMARY KEY,
    job_id INT REFERENCES job_definitions(job_id) ON DELETE CASCADE,
    
    objective_type VARCHAR(32),           -- block_break, mob_kill, craft, etc.
    target_material VARCHAR(64),          -- STONE, DIAMOND_ORE, ZOMBIE, etc.
    
    xp_reward DECIMAL(10,2),
    money_reward DECIMAL(10,2),
    
    -- Optional filters
    requires_tool VARCHAR(64),            -- DIAMOND_PICKAXE
    requires_enchant VARCHAR(64),         -- FORTUNE
    world_filter TEXT,                    -- JSON array of allowed worlds
    
    sort_order INT DEFAULT 0
);
```

---

### 2. Quest Builder (Quests Plugin)

#### Interface Layout
```
┌──────────────────────────────────────────────────────────────┐
│ Quest Builder - Create/Edit Quest                 [Template] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Quest ID: [mining_initiation_____] Display: [Mining 101____] │
│                                                               │
│ Category: [Tutorial ▼] │ Repeatable: [Yes ▼] Every: [24h_]  │
│                                                               │
│ Description:                                                 │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Learn the basics of mining! Collect ores to progress. │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Requirements:                                                │
│   [x] Min Rank: [Novice (2) ▼]                              │
│   [ ] Completed Quest: [None ▼]                             │
│   [ ] Permission: [___________________________]             │
│                                                               │
│ ─────────────────── Tasks ─────────────────────              │
│                                                               │
│ ┌─ Task 1: Collect Items ───────────────────────────┐       │
│ │ Item: [COAL ▼] Amount: [64_]                      │       │
│ │ Message: "Collect 64 coal to continue"            │       │
│ │ [▲] [▼] [+ Add Item] [- Remove Task]              │       │
│ └────────────────────────────────────────────────────┘       │
│                                                               │
│ ┌─ Task 2: Break Blocks ────────────────────────────┐       │
│ │ Block: [STONE ▼] Amount: [100_]                   │       │
│ │ Message: "Mine 100 stone blocks"                  │       │
│ │ [▲] [▼] [- Remove Task]                            │       │
│ └────────────────────────────────────────────────────┘       │
│                                                               │
│ [+ Add Task Type ▼]                                          │
│   - Collect Items    - Talk to NPC                          │
│   - Break Blocks     - Kill Mobs                            │
│   - Craft Items      - Reach Location                       │
│                                                               │
│ ─────────────────── Rewards ───────────────────────          │
│                                                               │
│ ┌─ Rank-Based Rewards ──────────────────────────────┐       │
│ │ Default (All Ranks):                              │       │
│ │   Money: [500_]  XP: [100_]                       │       │
│ │   Items: [DIAMOND_PICKAXE x1]                     │       │
│ │                                                    │       │
│ │ Bonus for Rank 10+ (Master):                      │       │
│ │   Money: [750_]  XP: [150_]                       │       │
│ │   Items: [DIAMOND_PICKAXE x1 + FORTUNE II]        │       │
│ │                                                    │       │
│ │ Bonus for Prestige 5+ (Explorer):                │       │
│ │   Money: [1000_] XP: [200_]                       │       │
│ │   Commands: [give {player} elite_pickaxe 1]       │       │
│ │                                                    │       │
│ │ [+ Add Rank Tier]                                 │       │
│ └────────────────────────────────────────────────────┘       │
│                                                               │
│ ─────────────────── Deployment ────────────────────          │
│                                                               │
│ Active In:                                                   │
│   [x] All survival instances                                │
│   [ ] Specific instances: [SMP101_____]                     │
│                                                               │
│ [Save Quest] [Preview] [Deploy] [Cancel]                    │
└──────────────────────────────────────────────────────────────┘
```

#### Database Schema
```sql
CREATE TABLE quest_definitions (
    quest_id VARCHAR(64) PRIMARY KEY,
    display_name TEXT,
    category VARCHAR(64),
    description TEXT,
    
    -- Requirements
    min_rank_id INT REFERENCES rank_definitions(rank_id),
    min_prestige_id INT REFERENCES rank_definitions(rank_id),
    required_quest_id VARCHAR(64) REFERENCES quest_definitions(quest_id),
    required_permission VARCHAR(128),
    
    -- Repeatability
    is_repeatable BOOLEAN DEFAULT false,
    cooldown_seconds INT,                 -- 86400 for daily
    
    -- Deployment
    scope_type VARCHAR(16) DEFAULT 'META_TAG',
    scope_selector VARCHAR(64) DEFAULT 'survival',
    
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE quest_tasks (
    task_id SERIAL PRIMARY KEY,
    quest_id VARCHAR(64) REFERENCES quest_definitions(quest_id) ON DELETE CASCADE,
    
    task_type VARCHAR(32),                -- collect, break, kill, craft, location, npc
    target VARCHAR(64),                   -- Material, EntityType, NPC ID, etc.
    amount INT,
    message TEXT,
    
    task_order INT,
    is_optional BOOLEAN DEFAULT false
);

CREATE TABLE quest_rewards (
    reward_id SERIAL PRIMARY KEY,
    quest_id VARCHAR(64) REFERENCES quest_definitions(quest_id) ON DELETE CASCADE,
    
    -- Rank tier (NULL = default for all)
    min_rank_id INT REFERENCES rank_definitions(rank_id),
    min_prestige_id INT REFERENCES rank_definitions(rank_id),
    
    -- Rewards
    money_reward DECIMAL(10,2),
    xp_reward INT,
    items_json TEXT,                      -- JSON array of ItemStacks
    commands_json TEXT,                   -- JSON array of commands to execute
    
    reward_tier INT DEFAULT 0             -- 0 = default, 1+ = bonus tiers
);
```

---

### 3. Item Worth/Pricing System (QuickShop/Economy)

#### Procedural Worth Definition
**Goal**: Automatically calculate item values based on rarity, usefulness, effort to obtain.

#### Interface
```
┌──────────────────────────────────────────────────────────────┐
│ Item Worth Manager - Global Pricing                         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Pricing Strategy: [Tiered by Rarity ▼]                      │
│                                                               │
│ ─────────────────── Auto-Calculated ───────────────          │
│                                                               │
│ Item              Category    Base Worth   Sell   Buy        │
│ ───────────────────────────────────────────────────────────  │
│ DIRT              Common      $0.10        $0.05  $0.15      │
│ COBBLESTONE       Common      $0.25        $0.13  $0.38      │
│ COAL              Fuel        $2.00        $1.00  $3.00      │
│ IRON_INGOT        Refined     $5.00        $2.50  $7.50      │
│ DIAMOND           Rare        $50.00       $25    $75        │
│ NETHERITE_INGOT   Epic        $500.00      $250   $750       │
│ ENCHANTED_BOOK    Variable    [Calculate▼]                  │
│                                                               │
│ ─────────────────── Manual Overrides ──────────────          │
│                                                               │
│ [+ Add Override]                                             │
│                                                               │
│ ┌─ Override: DIAMOND ────────────────────────────────┐      │
│ │ Global Base: $50.00                                │      │
│ │                                                     │      │
│ │ Instances with tag:economy-creative:               │      │
│ │   Worth: $1.00 (creative is cheap)                 │      │
│ │                                                     │      │
│ │ Instance SMP101 (survival competitive):            │      │
│ │   Worth: $100.00 (harder economy)                  │      │
│ └─────────────────────────────────────────────────────┘      │
│                                                               │
│ ─────────────────── Formula Editor ────────────────          │
│                                                               │
│ Enchanted Books Worth = BASE_BOOK (10) + ENCHANT_COST       │
│                                                               │
│ Enchant Cost Table:                                          │
│   SHARPNESS:     Level * 20                                  │
│   FORTUNE:       Level * 50                                  │
│   MENDING:       500 (flat, rare)                            │
│   PROTECTION:    Level * 30                                  │
│                                                               │
│ [Edit Formula]                                               │
│                                                               │
│ ─────────────────── Bulk Actions ──────────────────          │
│                                                               │
│ [Recalculate All] [Export CSV] [Import Prices] [Deploy]     │
└──────────────────────────────────────────────────────────────┘
```

#### Database Schema
```sql
CREATE TABLE item_worth_base (
    material VARCHAR(64) PRIMARY KEY,     -- Minecraft material name
    
    category VARCHAR(32),                 -- common, fuel, refined, rare, epic
    base_worth DECIMAL(10,2),             -- Calculated base value
    
    -- Multipliers for buy/sell
    sell_multiplier DECIMAL(5,2) DEFAULT 0.50,  -- Sell for 50% of worth
    buy_multiplier DECIMAL(5,2) DEFAULT 1.50,   -- Buy for 150% of worth
    
    -- Formula for dynamic items
    worth_formula TEXT,                   -- SQL expression or script
    
    last_calculated TIMESTAMP,
    is_manually_set BOOLEAN DEFAULT false
);

CREATE TABLE item_worth_overrides (
    override_id SERIAL PRIMARY KEY,
    material VARCHAR(64),
    
    -- Scope (uses hierarchy)
    scope_type VARCHAR(16),               -- GLOBAL, META_TAG, INSTANCE
    scope_selector VARCHAR(64),
    
    override_worth DECIMAL(10,2),
    reason TEXT,                          -- "Creative servers have cheap diamonds"
    
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Cached resolved values for quick lookups
CREATE TABLE item_worth_cache (
    instance_id VARCHAR(16),
    material VARCHAR(64),
    
    final_worth DECIMAL(10,2),            -- Resolved via hierarchy
    final_sell_price DECIMAL(10,2),
    final_buy_price DECIMAL(10,2),
    
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (instance_id, material)
);
```

---

### 4. LuckPerms Integration GUI

#### Interface Concept
```
┌──────────────────────────────────────────────────────────────┐
│ Permissions Manager - LuckPerms Integration        [Web UI] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Mode: [Sync with LuckPerms Web Editor ▼]                    │
│   Options:                                                   │
│   - Read-Only View (display LuckPerms data)                 │
│   - Two-Way Sync (edit here, push to LuckPerms)            │
│   - Import from LuckPerms (one-time import)                 │
│                                                               │
│ ─────────────────── Rank → Group Mapping ──────────          │
│                                                               │
│ Our Rank         LuckPerms Group      Sync Status           │
│ ───────────────────────────────────────────────────────────  │
│ Casual (0)    →  default              ✓ Synced             │
│ Novice (2)    →  novice               ✓ Synced             │
│ Apprentice (5)→  member               ✓ Synced             │
│ Master (9)    →  trusted              ✓ Synced             │
│ Legend (P20)  →  legend               ⚠ Not in LuckPerms   │
│                                                               │
│ [Auto-Create Missing Groups]                                │
│                                                               │
│ ─────────────────── Permission Templates ──────────          │
│                                                               │
│ ┌─ Rank 5 (Apprentice) Permissions ──────────────────┐      │
│ │ Inherited from: default, novice                    │      │
│ │                                                     │      │
│ │ Granted Permissions:                               │      │
│ │   ✓ jobs.join.*                                    │      │
│ │   ✓ quests.start.tutorial                          │      │
│ │   ✓ homes.set.3                                    │      │
│ │   ✓ warp.use                                       │      │
│ │                                                     │      │
│ │ [Edit in LuckPerms Web Editor]                     │      │
│ └─────────────────────────────────────────────────────┘      │
│                                                               │
│ [Fetch from LuckPerms API] [Push Changes] [Open Web Editor] │
└──────────────────────────────────────────────────────────────┘
```

#### Integration Strategy

**Option A: Read-Only Display**
- Query LuckPerms MySQL database directly
- Display group/permission structure
- "Edit" button opens LuckPerms web editor
- Refresh to sync changes made externally

**Option B: API Integration**
- Use LuckPerms REST API (if available)
- Two-way sync: Create groups, assign permissions
- Validate before pushing to avoid conflicts

**Option C: Database Sync**
- Map our `rank_definitions` table to LuckPerms groups
- Automated sync job: Create missing groups, update permissions
- Conflict resolution: LuckPerms is source of truth for perms, we're source of truth for rank progression

---

### 5. Command Builder (Complex Task Automation)

#### Interface
```
┌──────────────────────────────────────────────────────────────┐
│ Command Builder - Complex Task Creator                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Task Name: [Weekly Server Cleanup___________________]       │
│                                                               │
│ Trigger:                                                     │
│   [x] Schedule: Every [Sunday_] at [03:00_] server time     │
│   [ ] Manual: Create /admin command                         │
│   [ ] Event: On [player_join ▼]                            │
│                                                               │
│ ─────────────────── Command Sequence ───────────────         │
│                                                               │
│ Step 1: [Announce to players_____________________________▼]  │
│   Command: broadcast &eServer maintenance in 5 minutes!      │
│   Delay:   [0] seconds                                       │
│   [▲] [▼] [- Remove]                                         │
│                                                               │
│ Step 2: [Execute console command_________________________▼]  │
│   Command: save-all                                          │
│   Delay:   [300] seconds (5 minutes)                        │
│   [▲] [▼] [- Remove]                                         │
│                                                               │
│ Step 3: [Run Python script_______________________________▼]  │
│   Script:  scripts/cleanup_old_claims.py                     │
│   Args:    --inactive-days 90                                │
│   Delay:   [10] seconds                                      │
│   [▲] [▼] [- Remove]                                         │
│                                                               │
│ Step 4: [Execute on specific instances__________________▼]  │
│   Instances: [SMP101] [SMP201] [EMAD01]                     │
│   Command:   CoreProtect purge t:90d r:#global              │
│   Delay:     [60] seconds                                    │
│   [▲] [▼] [- Remove]                                         │
│                                                               │
│ [+ Add Step ▼]                                               │
│   - Broadcast Message                                        │
│   - Console Command                                          │
│   - Run Script                                               │
│   - HTTP Request (webhook)                                   │
│   - Conditional (if/else)                                    │
│                                                               │
│ ─────────────────── Error Handling ────────────────          │
│                                                               │
│ On Failure:                                                  │
│   [x] Log to database                                        │
│   [x] Send Discord notification to [#admin-alerts_____]     │
│   [ ] Retry [3] times with [60] second delay                │
│   [ ] Rollback previous steps                               │
│                                                               │
│ [Save Task] [Test Run] [Enable Schedule] [Cancel]           │
└──────────────────────────────────────────────────────────────┘
```

#### Database Schema
```sql
CREATE TABLE automated_tasks (
    task_id SERIAL PRIMARY KEY,
    task_name VARCHAR(128),
    description TEXT,
    
    -- Trigger
    trigger_type VARCHAR(32),             -- schedule, manual, event
    schedule_cron VARCHAR(64),            -- "0 3 * * 0" for Sunday 3am
    manual_command VARCHAR(64),           -- /admin cleanup
    event_trigger VARCHAR(64),            -- player_join, server_start, etc.
    
    -- Execution scope
    scope_type VARCHAR(16),               -- GLOBAL, META_TAG, INSTANCE
    scope_selector VARCHAR(64),
    
    -- Error handling
    on_failure_action VARCHAR(16),        -- log, notify, retry, rollback
    retry_count INT DEFAULT 0,
    retry_delay_seconds INT,
    
    is_enabled BOOLEAN DEFAULT true,
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE task_steps (
    step_id SERIAL PRIMARY KEY,
    task_id INT REFERENCES automated_tasks(task_id) ON DELETE CASCADE,
    
    step_order INT,
    step_type VARCHAR(32),                -- broadcast, command, script, http, conditional
    
    -- Command/Script details
    command_text TEXT,
    script_path VARCHAR(256),
    script_args TEXT,
    http_url VARCHAR(512),
    http_method VARCHAR(16),
    http_payload TEXT,
    
    -- Conditional logic
    condition_expression TEXT,            -- "if player_count > 10"
    on_true_step_id INT,                  -- Go to step X if true
    on_false_step_id INT,                 -- Go to step Y if false
    
    delay_seconds INT DEFAULT 0,
    is_critical BOOLEAN DEFAULT false     -- Fail entire task if this step fails
);

CREATE TABLE task_execution_log (
    execution_id SERIAL PRIMARY KEY,
    task_id INT REFERENCES automated_tasks(task_id),
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(16),                   -- success, failed, partial
    
    steps_executed INT,
    steps_failed INT,
    
    error_message TEXT,
    full_log TEXT                         -- Complete execution transcript
);
```

---

## Meta-Tag Management GUI

### Instance Tagging Interface

```
┌──────────────────────────────────────────────────────────────┐
│ Instance Tags Manager - Configure Server Categories         │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Select Instance: [SMP101 ▼]                                  │
│                                                               │
│ ─────────────────── Physical Server ────────────────         │
│ Server: [x] hetzner-xeon  [ ] ovh-ryzen                      │
│                                                               │
│ ─────────────────── Gameplay Tags ──────────────────         │
│ Mode:                                                        │
│   [x] survival      [ ] creative      [ ] minigame          │
│   [ ] utility       [ ] experimental                        │
│                                                               │
│ Modding:                                                     │
│   [ ] pure-vanilla  [x] vanilla-ish   [ ] lightly-modded   │
│   [ ] heavily-modded [ ] barely-minecraft                   │
│                                                               │
│ Intensity:                                                   │
│   [ ] casual        [x] sweaty        [ ] hardcore          │
│                                                               │
│ Economy:                                                     │
│   [x] economy-enabled                                       │
│                                                               │
│ Combat:                                                      │
│   [ ] pvp-enabled   [x] pve-focused                         │
│                                                               │
│ Persistence:                                                 │
│   [x] persistent    [ ] resetting     [ ] temporary         │
│                                                               │
│ ─────────────────── Custom Tags ────────────────────         │
│ Current: [elitemobs-enabled] [mcmmo-enabled] [quests-active]│
│ [+ Add Custom Tag_______________________] [Add]             │
│                                                               │
│ ─────────────────── Applied Rules ──────────────────         │
│                                                               │
│ This instance inherits 47 config rules from:                │
│   - GLOBAL (baseline): 35 rules                             │
│   - server:hetzner-xeon: 5 rules                            │
│   - tag:survival: 4 rules                                   │
│   - tag:economy-enabled: 2 rules                            │
│   - tag:pve-focused: 1 rule                                 │
│                                                               │
│ [View All Rules] [Test Config Resolution]                   │
│                                                               │
│ [Save Tags] [Copy Tags From...] [Reset to Default] [Cancel] │
└──────────────────────────────────────────────────────────────┘
```

### Bulk Tag Assignment

```
┌──────────────────────────────────────────────────────────────┐
│ Bulk Tag Operations - Apply Tags to Multiple Instances      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│ Select Instances:                                            │
│   [x] SMP101      [x] SMP201      [ ] EMAD01                │
│   [x] EVO01       [ ] CREA01      [ ] DEV01                 │
│   [ ] HUB01       ... (11 total)                            │
│                                                               │
│ Action: [Add Tags ▼]                                         │
│   Options: Add Tags, Remove Tags, Replace All Tags          │
│                                                               │
│ Tags to Apply:                                               │
│   [x] economy-enabled                                       │
│   [x] pve-focused                                           │
│   [ ] pvp-enabled                                           │
│                                                               │
│ Preview Changes:                                             │
│   SMP101: +economy-enabled, +pve-focused                    │
│   SMP201: +economy-enabled, +pve-focused                    │
│   EVO01:  +economy-enabled, +pve-focused                    │
│                                                               │
│ This will affect 23 config rules for these instances.       │
│                                                               │
│ [Apply Changes] [Cancel]                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Complete Database Schema Summary

```sql
-- ============================================================
-- RANK SYSTEM (Universal Framework)
-- ============================================================

CREATE TABLE rank_definitions (
    rank_id INT PRIMARY KEY,
    rank_type VARCHAR(16),                -- 'primary' or 'prestige'
    rank_name VARCHAR(32),
    rank_order INT,
    display_color VARCHAR(16),
    chat_prefix TEXT,
    tab_prefix TEXT,
    luckperms_group VARCHAR(64),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE player_ranks (
    player_uuid CHAR(36) PRIMARY KEY,
    current_rank_id INT REFERENCES rank_definitions(rank_id),
    current_prestige_id INT REFERENCES rank_definitions(rank_id),
    total_playtime_seconds BIGINT,
    total_quest_completions INT,
    total_mob_kills INT,
    rank_progress_percent DECIMAL(5,2),
    last_rank_up TIMESTAMP,
    last_prestige TIMESTAMP,
    first_join TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- CONFIG HIERARCHY (from CONFIG_HIERARCHY_PATTERNS.md)
-- ============================================================

CREATE TABLE instances (
    instance_id VARCHAR(16) PRIMARY KEY,
    server_name VARCHAR(32),              -- hetzner-xeon, ovh-ryzen
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE instance_tags (
    instance_id VARCHAR(16) REFERENCES instances(instance_id),
    tag_name VARCHAR(64),
    tag_category VARCHAR(32),
    PRIMARY KEY (instance_id, tag_name)
);

CREATE TABLE config_rules (
    rule_id SERIAL PRIMARY KEY,
    plugin_name VARCHAR(64),
    config_key VARCHAR(256),
    scope_type VARCHAR(16),               -- GLOBAL, SERVER, META_TAG, INSTANCE
    scope_selector VARCHAR(64),
    config_value TEXT,
    value_type VARCHAR(16),
    priority INT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(64),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE config_variables (
    instance_id VARCHAR(16) REFERENCES instances(instance_id),
    variable_name VARCHAR(64),
    variable_value TEXT,
    PRIMARY KEY (instance_id, variable_name)
);

-- ============================================================
-- JOB BUILDER
-- ============================================================

CREATE TABLE job_definitions (
    job_id SERIAL PRIMARY KEY,
    job_name VARCHAR(64) UNIQUE,
    display_name TEXT,
    description TEXT,
    min_rank_id INT REFERENCES rank_definitions(rank_id),
    min_prestige_id INT REFERENCES rank_definitions(rank_id),
    required_permission VARCHAR(128),
    join_cost DECIMAL(10,2),
    max_level INT DEFAULT 50,
    xp_curve VARCHAR(16) DEFAULT 'linear',
    scope_type VARCHAR(16) DEFAULT 'GLOBAL',
    scope_selector VARCHAR(64),
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE job_objectives (
    objective_id SERIAL PRIMARY KEY,
    job_id INT REFERENCES job_definitions(job_id) ON DELETE CASCADE,
    objective_type VARCHAR(32),
    target_material VARCHAR(64),
    xp_reward DECIMAL(10,2),
    money_reward DECIMAL(10,2),
    requires_tool VARCHAR(64),
    requires_enchant VARCHAR(64),
    world_filter TEXT,
    sort_order INT DEFAULT 0
);

-- ============================================================
-- QUEST BUILDER
-- ============================================================

CREATE TABLE quest_definitions (
    quest_id VARCHAR(64) PRIMARY KEY,
    display_name TEXT,
    category VARCHAR(64),
    description TEXT,
    min_rank_id INT REFERENCES rank_definitions(rank_id),
    min_prestige_id INT REFERENCES rank_definitions(rank_id),
    required_quest_id VARCHAR(64) REFERENCES quest_definitions(quest_id),
    required_permission VARCHAR(128),
    is_repeatable BOOLEAN DEFAULT false,
    cooldown_seconds INT,
    scope_type VARCHAR(16) DEFAULT 'META_TAG',
    scope_selector VARCHAR(64) DEFAULT 'survival',
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE quest_tasks (
    task_id SERIAL PRIMARY KEY,
    quest_id VARCHAR(64) REFERENCES quest_definitions(quest_id) ON DELETE CASCADE,
    task_type VARCHAR(32),
    target VARCHAR(64),
    amount INT,
    message TEXT,
    task_order INT,
    is_optional BOOLEAN DEFAULT false
);

CREATE TABLE quest_rewards (
    reward_id SERIAL PRIMARY KEY,
    quest_id VARCHAR(64) REFERENCES quest_definitions(quest_id) ON DELETE CASCADE,
    min_rank_id INT REFERENCES rank_definitions(rank_id),
    min_prestige_id INT REFERENCES rank_definitions(rank_id),
    money_reward DECIMAL(10,2),
    xp_reward INT,
    items_json TEXT,
    commands_json TEXT,
    reward_tier INT DEFAULT 0
);

-- ============================================================
-- ITEM WORTH / PRICING
-- ============================================================

CREATE TABLE item_worth_base (
    material VARCHAR(64) PRIMARY KEY,
    category VARCHAR(32),
    base_worth DECIMAL(10,2),
    sell_multiplier DECIMAL(5,2) DEFAULT 0.50,
    buy_multiplier DECIMAL(5,2) DEFAULT 1.50,
    worth_formula TEXT,
    last_calculated TIMESTAMP,
    is_manually_set BOOLEAN DEFAULT false
);

CREATE TABLE item_worth_overrides (
    override_id SERIAL PRIMARY KEY,
    material VARCHAR(64),
    scope_type VARCHAR(16),
    scope_selector VARCHAR(64),
    override_worth DECIMAL(10,2),
    reason TEXT,
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE item_worth_cache (
    instance_id VARCHAR(16),
    material VARCHAR(64),
    final_worth DECIMAL(10,2),
    final_sell_price DECIMAL(10,2),
    final_buy_price DECIMAL(10,2),
    last_updated TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (instance_id, material)
);

-- ============================================================
-- COMMAND BUILDER / AUTOMATION
-- ============================================================

CREATE TABLE automated_tasks (
    task_id SERIAL PRIMARY KEY,
    task_name VARCHAR(128),
    description TEXT,
    trigger_type VARCHAR(32),
    schedule_cron VARCHAR(64),
    manual_command VARCHAR(64),
    event_trigger VARCHAR(64),
    scope_type VARCHAR(16),
    scope_selector VARCHAR(64),
    on_failure_action VARCHAR(16),
    retry_count INT DEFAULT 0,
    retry_delay_seconds INT,
    is_enabled BOOLEAN DEFAULT true,
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE task_steps (
    step_id SERIAL PRIMARY KEY,
    task_id INT REFERENCES automated_tasks(task_id) ON DELETE CASCADE,
    step_order INT,
    step_type VARCHAR(32),
    command_text TEXT,
    script_path VARCHAR(256),
    script_args TEXT,
    http_url VARCHAR(512),
    http_method VARCHAR(16),
    http_payload TEXT,
    condition_expression TEXT,
    on_true_step_id INT,
    on_false_step_id INT,
    delay_seconds INT DEFAULT 0,
    is_critical BOOLEAN DEFAULT false
);

CREATE TABLE task_execution_log (
    execution_id SERIAL PRIMARY KEY,
    task_id INT REFERENCES automated_tasks(task_id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(16),
    steps_executed INT,
    steps_failed INT,
    error_message TEXT,
    full_log TEXT
);
```

---

## Implementation Priority

### Phase 1: Foundation (Week 1-2)
1. **Rank System**
   - Import EliteMobs rank data into `rank_definitions`
   - Create player rank tracking
   - Map to LuckPerms groups

2. **Config Hierarchy** (already designed)
   - Instance tagging interface
   - Rule resolution algorithm
   - Variance detection

### Phase 2: Builders (Week 3-4)
3. **Job Builder**
   - GUI mockup → real interface
   - Job definition storage
   - Deploy to ExcellentJobs config files

4. **Quest Builder**
   - Task/reward GUI
   - Rank-based reward tiers
   - Deploy to Quests plugin

### Phase 3: Automation (Week 5-6)
5. **Item Worth System**
   - Auto-calculation formulas
   - Override management
   - Cache for quick lookups

6. **Command Builder**
   - Task scheduling interface
   - Step sequencing logic
   - Error handling & logging

### Phase 4: Integration (Week 7-8)
7. **LuckPerms Integration**
   - API connection
   - Group sync
   - Web editor embedding

8. **Testing & Refinement**
   - End-to-end workflow testing
   - Performance optimization
   - Documentation

This gives you the complete **admin tooling foundation** built on the hierarchical config system with universal rank support.