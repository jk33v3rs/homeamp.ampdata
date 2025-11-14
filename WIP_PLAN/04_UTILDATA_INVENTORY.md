# utildata/ Directory Inventory - Complete Data Snapshot

**Status**: PASS 1 - Data cataloging  
**Generated**: 2025-11-10  
**Purpose**: Document all production data snapshots, Excel configs, and baseline states  

---

## Executive Summary

**Purpose**: utildata/ contains replicated server configuration state from production (Hetzner and OVH bare metal servers). This is snapshot data taken at a specific point in time, NOT live production data.

**Total Size**: ~500MB (estimated, excluding zipped baselines)  
**Server Snapshots**: 23 total (11 Hetzner + 12 OVH)  
**Plugin Configs**: 57 universal config markdown files  
**Excel Databases**: 6 Excel files with deployment/variable data  
**JSON Analysis**: 4 JSON files with config analysis  

---

## Directory Structure

```
utildata/
├── ActualDBs/                          # Deployment matrices
│   ├── deployment_matrix.csv           # Plugin-to-server mapping (CSV)
│   ├── deployment_matrix.xlsx          # Plugin-to-server mapping (Excel)
│   └── desktop.ini
│
├── final-deliverables/                 # Legacy data
│   ├── pluginlist                      # Text file with plugin names
│   └── desktop.ini
│
├── HETZNER/                            # Hetzner server snapshots (11 servers)
│   ├── ADS01/                          # AdventureSMP server
│   ├── BIG01/                          # Big Dig server
│   ├── CAR01/                          # Create Above & Restore server
│   ├── DEV01/                          # Development/testing server
│   ├── EVO01/                          # Evolution server
│   ├── MIN01/                          # Minimalist server
│   ├── PRI01/                          # Primitive server
│   ├── ROY01/                          # Royal server
│   ├── SMP101/                         # SMP 101 server
│   ├── SUNK01/                         # Sunkenland server
│   └── TOW01/                          # Towny server
│
├── OVH/                                # OVH server snapshots (12 servers)
│   ├── ADS01/                          # AdventureSMP (OVH instance)
│   ├── BENT01/                         # Bent server
│   ├── CLIP01/                         # Clip server
│   ├── CREA01/                         # Create server
│   ├── CSMC01/                         # CSMC server
│   ├── EMAD01/                         # Emad server
│   ├── GEY01/                          # Geyser/Bedrock server
│   ├── HARD01/                         # Hardcore server
│   ├── HUB01/                          # Hub/lobby server
│   ├── MINE01/                         # Minecolonies server
│   ├── SMP201/                         # SMP 201 server
│   └── VEL01/                          # Velocity proxy server
│
├── plugin_universal_configs/           # Universal plugin configs (57 files)
│   ├── AxiomPaper_universal_config.md
│   ├── BetterStructures_universal_config.md
│   ├── bStats_universal_config.md
│   ├── Chunky_universal_config.md
│   ├── ChunkyBorder_universal_config.md
│   ├── Citizens_universal_config.md
│   ├── CMI_universal_config.md
│   ├── CMILib_universal_config.md
│   ├── CombatPets_universal_config.md
│   ├── CommunityQuests_universal_config.md
│   ├── CoreProtect_universal_config.md
│   ├── CraftBook5_universal_config.md
│   ├── DamageIndicator_universal_config.md
│   ├── EconomyBridge_universal_config.md
│   ├── EliteMobs_universal_config.md
│   ├── ExcellentChallenges_universal_config.md
│   ├── ExcellentEnchants_universal_config.md
│   ├── ExcellentJobs_universal_config.md
│   ├── FreeMinecraftModels_universal_config.md
│   ├── Geyser-Recipe-Fix_universal_config.md
│   ├── GlowingItems_universal_config.md
│   ├── HuskSync_universal_config.md
│   ├── ImageFrame_universal_config.md
│   ├── JobListings_universal_config.md
│   ├── LightAPI_universal_config.md
│   ├── Lootin_universal_config.md
│   ├── LuckPerms_universal_config.md
│   ├── mcMMO_universal_config.md
│   ├── nightcore_universal_config.md
│   ├── PaperTweaks_universal_config.md
│   ├── Pl3xMap_universal_config.md
│   ├── Pl3xMapExtras_universal_config.md
│   ├── PlaceholderAPI_universal_config.md
│   ├── Plan_universal_config.md
│   ├── ProtocolLib_universal_config.md
│   ├── qsaddon-discount_universal_config.md
│   ├── qsaddon-displaycontrol_universal_config.md
│   ├── qsaddon-list_universal_config.md
│   ├── qsaddon-plan_universal_config.md
│   ├── qsaddon-shopitemonly_universal_config.md
│   ├── qscompat-worldguard_universal_config.md
│   ├── QSFindItemAddOn_universal_config.md
│   ├── qssuite-limited_universal_config.md
│   ├── QualityArmory_universal_config.md
│   ├── Quests_universal_config.md
│   ├── QuickShop-Hikari_universal_config.md
│   ├── ResourcePackManager_universal_config.md
│   ├── ResurrectionChest_universal_config.md
│   ├── TheNewEconomy_universal_config.md
│   ├── TreeFeller_universal_config.md
│   ├── Vault_universal_config.md
│   ├── ViaBackwards_universal_config.md
│   ├── ViaVersion_universal_config.md
│   ├── VillagerOptimizer_universal_config.md
│   ├── WorldBorder_universal_config.md
│   ├── WorldEdit_universal_config.md
│   ├── WorldGuard_universal_config.md
│   └── desktop.ini
│
├── ArchiveSMP_MASTER_WITH_VIEWS.xlsx  # Master database with views
├── Master_Variable_Configurations.xlsx # Server-specific variables (ports, IPs, etc.)
├── Plugin_Configurations.xlsx          # Plugin configuration database
├── Plugin_Detailed_Configurations.xlsx # Detailed plugin configs
├── Plugin_Implementation_Matrix.xlsx   # Plugin implementation matrix
├── Proxy_Configurations.xlsx           # Proxy/network configs
│
├── create_enhanced_version_management.py  # Script for version management
├── plugin_universal_configs_baseline.zip  # Zipped baseline of universal configs
├── prescriptive_network_settings.txt      # Network configuration guide
│
├── universal_configs_analysis.json         # Original universal config analysis
├── universal_configs_analysis_UPDATED.json # Updated universal config analysis
├── variable_configs_analysis.json          # Original variable config analysis
└── variable_configs_analysis_UPDATED.json  # Updated variable config analysis
```

---

## Server Snapshot Contents

Each server directory (HETZNER/*/  and OVH/*/) contains:

```
{SERVER_ID}/
├── .ampdata/                   # AMP instance data
│   └── instances/
│       └── {InstanceID}/       # Minecraft instance
│           ├── Minecraft/
│           │   ├── plugins/    # Plugin JAR files + configs
│           │   ├── world/      # World data
│           │   ├── config/     # Paper/Spigot configs
│           │   └── server.properties
│           └── AMPConfig.json  # AMP instance configuration
└── (Other AMP-related files)
```

**Example Snapshot Timestamp**: October 11, 2025 (based on 11octSNAPSHOTovh/)

---

## Excel Database Details

### 1. deployment_matrix.csv / .xlsx
**Location**: `utildata/ActualDBs/`  
**Purpose**: Maps which plugins are deployed to which servers  
**Format**: CSV and Excel  
**Schema** (inferred):
- Columns: Plugin names
- Rows: Server names
- Values: Version numbers or deployment status

**Usage in Code**: 
- `core/excel_reader.py:load_deployment_matrix()`
- Used by automation to determine deployment targets

---

### 2. Master_Variable_Configurations.xlsx
**Location**: `utildata/`  
**Purpose**: Server-specific configuration variables (ports, IPs, database names, etc.)  
**Format**: Excel with multiple sheets  
**Schema** (inferred):
- Sheet per server OR sheet with server columns
- Variables: SERVER_PORT, SERVER_IP, DATABASE_NAME, WORLD_NAME, etc.

**Usage in Code**:
- `core/excel_reader.py:load_server_variables()`
- `core/excel_reader.py:get_server_variables(server_name)`
- `core/server_aware_config.py:apply_server_variables()` - Variable substitution {{VAR}}

**Example Variables**:
```yaml
{{SERVER_PORT}} → 25565 (DEV01), 25566 (ADS01), etc.
{{SERVER_IP}} → 135.181.212.169 (Hetzner), 37.187.143.41 (OVH)
{{DATABASE_NAME}} → archivesmp_dev01, archivesmp_ads01, etc.
```

---

### 3. ArchiveSMP_MASTER_WITH_VIEWS.xlsx
**Location**: `utildata/`  
**Purpose**: Master database with views (likely comprehensive server/plugin database)  
**Format**: Excel (potentially complex with multiple sheets/views)  
**Status**: Not directly used in code (yet)

---

### 4. Plugin_Configurations.xlsx
**Location**: `utildata/`  
**Purpose**: Plugin configuration database  
**Status**: Legacy? Not referenced in current codebase

---

### 5. Plugin_Detailed_Configurations.xlsx
**Location**: `utildata/`  
**Purpose**: Detailed plugin configurations  
**Status**: Legacy? Not referenced in current codebase

---

### 6. Plugin_Implementation_Matrix.xlsx
**Location**: `utildata/`  
**Purpose**: Plugin implementation matrix  
**Status**: Legacy? Not referenced in current codebase

---

### 7. Proxy_Configurations.xlsx
**Location**: `utildata/`  
**Purpose**: Proxy/network configurations (Velocity/Waterfall)  
**Status**: Not referenced in current codebase

---

## Universal Plugin Configs (57 files)

**Location**: `utildata/plugin_universal_configs/*.md`  
**Format**: Markdown with YAML/JSON embedded  
**Purpose**: Universal (server-agnostic) plugin configurations  

**Structure** (per file):
```markdown
# {PluginName} Universal Config

## config.yml
```yaml
key: value
nested:
  key: {{SERVER_VARIABLE}}
```

## other-config.yml
```yaml
...
```
```

**Usage in Code**:
- `core/data_loader.py:load_universal_plugin_configs()` - Parse markdown
- `core/data_loader.py:_parse_universal_config_file()` - Extract YAML blocks
- `core/server_aware_config.py:load_universal_config()` - Load templates
- `web/models.py:DeviationParser:load_universal_configs()` - Parse for web UI

**Variable Placeholders**:
- `{{SERVER_PORT}}`
- `{{SERVER_IP}}`
- `{{DATABASE_NAME}}`
- `{{WORLD_NAME}}`
- etc.

**Key Plugins with Universal Configs**:
- **LuckPerms** - Permissions
- **CoreProtect** - Logging
- **WorldGuard/WorldEdit** - World management
- **QuickShop-Hikari** - Economy
- **Pl3xMap** - Web map
- **Plan** - Analytics
- **Geyser-Recipe-Fix** - Bedrock compatibility
- **ViaVersion/ViaBackwards** - Multi-version support
- **CMI** - Core server management
- **mcMMO** - Skills system
- **EliteMobs** - Custom mobs
- **Quests** - Quest system
- **Jobs (ExcellentJobs)** - Jobs plugin
- **Vault** - Economy API

---

## JSON Analysis Files

### 1. universal_configs_analysis.json
**Location**: `utildata/`  
**Purpose**: Analysis of which config keys are universal vs per-server  
**Format**: JSON  
**Content** (structure inferred):
```json
{
  "PluginName": {
    "config.yml": {
      "key.path": {
        "universal": true/false,
        "servers": ["DEV01", "ADS01", ...],
        "values": {...}
      }
    }
  }
}
```

---

### 2. universal_configs_analysis_UPDATED.json
**Location**: `utildata/`  
**Purpose**: Updated version of universal config analysis  
**Status**: Newer version with corrections/additions

---

### 3. variable_configs_analysis.json
**Location**: `utildata/`  
**Purpose**: Analysis of variable (per-server) config keys  
**Content**: Keys that vary between servers

---

### 4. variable_configs_analysis_UPDATED.json
**Location**: `utildata/`  
**Purpose**: Updated variable config analysis  

---

## Other Files

### prescriptive_network_settings.txt
**Location**: `utildata/`  
**Purpose**: Network configuration guidelines (ports, IPs, routing)  
**Format**: Plain text documentation

---

### plugin_universal_configs_baseline.zip
**Location**: `utildata/`  
**Purpose**: Zipped backup of plugin_universal_configs/ directory  
**Timestamp**: Unknown (check file metadata)  
**Status**: Baseline snapshot for comparison

---

### create_enhanced_version_management.py
**Location**: `utildata/`  
**Purpose**: Script for version management (duplicate from root?)  
**Status**: Python script

---

### final-deliverables/pluginlist
**Location**: `utildata/final-deliverables/`  
**Purpose**: Text file with list of plugin names  
**Format**: Plain text (one plugin per line?)  
**Status**: Legacy data

---

## Server Naming Convention

**Hetzner Servers** (11 total):
- **ADS01** - AdventureSMP
- **BIG01** - Big Dig (modded)
- **CAR01** - Create Above & Restore (modded)
- **DEV01** - Development/Testing server
- **EVO01** - Evolution (modded)
- **MIN01** - Minimalist
- **PRI01** - Primitive
- **ROY01** - Royal
- **SMP101** - SMP 101 (vanilla+)
- **SUNK01** - Sunkenland (modded)
- **TOW01** - Towny

**OVH Servers** (12 total):
- **ADS01** - AdventureSMP (duplicate name - different instance)
- **BENT01** - Bent
- **CLIP01** - Clip
- **CREA01** - Create
- **CSMC01** - CSMC (Create SMP Classic?)
- **EMAD01** - Emad
- **GEY01** - Geyser/Bedrock gateway
- **HARD01** - Hardcore
- **HUB01** - Hub/Lobby
- **MINE01** - Minecolonies
- **SMP201** - SMP 201
- **VEL01** - Velocity (proxy server)

**Naming Pattern**: `{TYPE}{NUMBER}` (e.g., ADS01, SMP101)

---

## Data Relationship Map

```
Excel (Master_Variable_Configurations.xlsx)
  ↓ provides variables
Universal Configs (plugin_universal_configs/*.md)
  ↓ with {{VARIABLE}} placeholders
Server-Aware Config Engine (core/server_aware_config.py)
  ↓ generates
Server-Specific Configs
  ↓ deployed to
Production Servers (via AMP)
```

---

## Critical Data Dependencies

**Code REQUIRES these files to function**:
1. ✅ `ActualDBs/deployment_matrix.csv` - Plugin deployment targets
2. ✅ `Master_Variable_Configurations.xlsx` - Server variables
3. ✅ `plugin_universal_configs/*.md` - Universal config templates

**Code CAN USE but not required**:
4. `universal_configs_analysis*.json` - Config analysis (optimization data)
5. `variable_configs_analysis*.json` - Variable detection (heuristics)

**Legacy/Unused**:
6. `ArchiveSMP_MASTER_WITH_VIEWS.xlsx` - Not referenced in code
7. `Plugin_*.xlsx` (3 files) - Not referenced in code
8. `Proxy_Configurations.xlsx` - Not referenced in code
9. `final-deliverables/` - Legacy data

---

## Snapshot Metadata

**Server Snapshots Timestamp**: October 11, 2025 (based on 11octSNAPSHOTovh/)  
**Source**: Physical Debian servers  
  - Hetzner Xeon: 135.181.212.169 (archivesmp.site)
  - OVH Ryzen: 37.187.143.41 (archivesmp.online)

**Snapshot Method**: Likely rsync or manual copy of `/home/amp/.ampdata/`

**Snapshot Coverage**:
- ✅ Plugin JARs
- ✅ Plugin configs
- ✅ AMP instance configs
- ✅ Server properties
- ❌ World data (too large - excluded?)
- ❌ Player data (excluded?)
- ❌ Logs (excluded?)

---

## Known Issues / Questions

1. **Duplicate ADS01**: Both HETZNER/ADS01/ and OVH/ADS01/ exist - are these different instances or mirrors?
2. **Excel file usage**: Only deployment_matrix and Master_Variable_Configurations are used in code - what about the others?
3. **Snapshot freshness**: Is October 11, 2025 snapshot still current? (Today is Nov 10, 2025)
4. **Missing servers**: Are all production servers captured? Check against production reality.
5. **VEL01 special case**: Velocity proxy server - different structure than Minecraft instances?

---

*Inventory complete. This data forms the baseline/reference state for drift detection and config management.*
