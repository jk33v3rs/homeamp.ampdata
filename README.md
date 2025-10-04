# AMP Server Configuration Repository

This repository is a **production environment mirror** simulating the `/home/amp/.ampdata` directory structure from a live Minecraft server network. It contains exported configuration files, datapacks, and plugins from two high-performance dedicated servers across Europe. The network operates using CubeCoders AMP as the game server management platform with Docker-based server deployments.

## 🔄 Repository Context

**Virtual Path**: `/home/amp/.ampdata` (production mirror)
- **Real Environment**: Live production servers with active player bases
- **Export Timestamp**: ~1 hour ago from production systems
- **Server Software**: Paper 1.21.8 (build 60-29c8822) - verified from actual server configurations
- **Data Scope**: Configuration files, plugins, datapacks (excluding player data, world saves, procedurally generated content)
- **Asset Registry**: Based on June 2025 documentation (some plugin lists may be outdated post-1.21.8)

## 🌐 Server Network Overview

### Production Environment Architecture
- **Network Proxy**: Velocity + Standalone Geyser (hosted on OVH)
- **Primary Gaming Server**: OVH Ryzen (Gravelines, France) 
- **Secondary/Fallback Server**: Hetzner Xeon (Helsinki, Finland)
- **Management Platform**: CubeCoders AMP with Docker containers
- **Operating System**: Debian 12 + Yunohost backend

### Server Specifications

#### **OVH Ryzen** (37.187.143.41) - `archivesmp.online`
- **Location**: Gravelines Data Centre, France
- **CPU**: AMD Ryzen 7 9700X
- **RAM**: 64GB DDR5 (high-speed)
- **Storage**: 2x 500GB NVMe SSDs (Software RAID 1)
- **Network**: Gigabit duplex connection
- **Role**: Primary gaming server hosting main game modes
- **Aliases**: Ryzen, Zen, OVH, (formerly bigNODE)

#### **Hetzner Xeon** (135.181.212.169) - `archivesmp.site`
- **Location**: Helsinki, Finland
- **CPU**: Intel Xeon W-2295 (18 cores)
- **RAM**: 128GB
- **Storage**: 1TB SSD
- **Network**: Gigabit duplex connection
- **Role**: Fallback server for specialized/development game modes
- **Aliases**: HET, Hetzner, Xeon

## 🎮 Game Server Distribution
*Based on authoritative per-server configuration data from live instances*

### **OVH Ryzen** (37.187.143.41) - `archivesmp.online` - **1XXX Port Range**
**Production Game Servers**:

- **CLIP01** (clippycore01) - ClippyCore enhanced hardcore mode [Port: 1179]
- **CSMC01** (csmc01) - CounterStrike: Minecraft minigame [Port: 1180]  
- **EMAD01** (emad01) - EMadventure server [Port: 1181]
- **BENT01** (bent01) - BentoBox ecosystem (Skyblock/OneBlock/Worlds) [Port: 1182]
- **HCRE01** (hardcore01) - Hardcore survival server [Port: 1183]
- **SMP201** (smp201) - Archive SMP Season 2 (Primary SMP) [Port: 1184]
- **HUB01** (hub01) - Central server hub and networking [Port: 1185]
- **MINT01** (minetorio01) - Minetorio (Factorio-inspired automation) [Port: 1186]
- **CREA01** (creative01) - Creative mode server [Port: 1187]
- **GEY01** (geyser01) - Geyser standalone (Bedrock Edition support) [Port: 19132]
- **VEL01** (velocity01) - Velocity proxy server (Network backbone) [Port: XX69]

### **Hetzner Xeon** (135.181.212.169) - `archivesmp.site` - **2XXX Port Range**  
**Specialized & Development Servers**:

- **TOWER01** (tower01) - Eternal Tower Defense minigame [Port: 2171]
- **EV01** (ev01) - Evolution SMP (Modded server development) [Port: 2172]
- **DEV01** (dev01) - Development and testing server [Port: 2173]
- **MINI01** (mini01) - General minigames server [Port: 2174]
- **BIGG01** (bigg01) - BiggerGAMES (Extended minigames collection) [Port: 2175]
- **FORT01** (fort01) - Battle Royale (Fortnite-style battle royale) [Port: 2176]
- **PRIV01** (priv01) - Private server worlds [Port: 2177]
- **SMPS101** (smp101) - SMP Season 1 instance [Port: 2178]

## 📁 Repository Structure

**Mirror of**: `/home/amp/.ampdata` with **additional organizational layer**

```
datapacksrepo/                        # Production datapacks from EVO01
├── Terralith_1.21.5_v2.5.11.zip
├── DnT Stronghold Overhaul v2.3.1.zip
├── BlazeandCave's Advancements Pack 1.19.1.zip
└── [40+ production datapacks]

pluginsrepo/                          # Production plugins from both servers
├── QuickShop-Hikari-6.2.0.11-SNAPSHOT-6.jar
├── LuckPerms-Bukkit-5.4.145.jar
├── CoreProtect-23.2.jar
└── [100+ production plugins]

HETZNER.135.181.212.169/              # ← Extra organizational layer (not in production)
└── amp_config_snapshot/              # ← THIS = production "instances/" folder
    ├── EVO01/ (Evolution SMP)
    ├── DEV01/ (Development)
    ├── TOWER01/ (Tower Defense)
    └── [6 specialized servers]

OVH.37.187.143.41/                    # ← Extra organizational layer (not in production)  
└── amp_config_snapshot/              # ← THIS = production "instances/" folder
    ├── VEL01/ (Velocity Proxy)
    ├── SMP201/ (Archive SMP S2)
    ├── HUB01/ (Network Hub)
    └── [11 main game servers]
```

### **Structure Differences: Repository vs Production**

| **This Repository** | **Production Environment** |
|---|---|
| `HETZNER.135.181.212.169/amp_config_snapshot/` | `/home/amp/.ampdata/instances/` |
| `OVH.37.187.143.41/amp_config_snapshot/` | `/home/amp/.ampdata/instances/` |

**Key Point**: The `amp_config_snapshot/` folders **ARE** the equivalent of the production `instances/` folder. The server IP directories are an additional organizational layer for this repository that doesn't exist in the live environment.

### Production Export Details
- **Configuration Files**: YAMLs, TOMLs, CONFs, .configs, JSONs, MD, TXT files
- **Plugin Collection**: Direct export from production plugin repositories  
- **Datapack Collection**: Direct export from EVO01 server instance
- **Exclusions**: Player data, world saves, procedurally generated content, map data
- **Structure Note**: Extra IP-based organization layer for multi-server repository management

## 🎮 Datapacks Collection

The `datapacksrepo/` folder contains **production-exported datapacks from EVO01** including:

- **World Generation**: Terralith, Continents, Amplified Nether
- **Structure Overhauls**: DnT series (Dungeons & Towers)
- **Adventure Content**: BlazeandCave's Advancements Pack, Explorify
- **Quality of Life**: Custom villager shops, unlock all recipes
- **Building Enhancements**: Banner bedsheets, mini blocks

### Installing Datapacks

1. Download the desired datapack from the `datapacksrepo/` folder
2. Extract the ZIP file to your world's `datapacks/` folder
3. Reload the world or restart the server
4. Use `/datapack list` to verify installation

## � Plugin Ecosystem
*Based on authoritative per-server deployment matrix*

### **Minimal Build Plugins** (Essential Foundation - "M" Rating)
*Everyone gets these - the absolute essentials*
- **LuckPerms** (5.4.145) - Permission management with per-server vault configurations
- **CoreProtect** (23.2) - Block logging with server-specific SQL tables (co_SERVERNAME_)
- **CMI & CMILib** (9.7.14.2 / 1.5.4.4) - Multi-tool with per-server spawn/database configs
- **PlaceholderAPI** (2.11.6) - Variable system foundation
- **ProtocolLib** (5.3.0) - Packet manipulation library
- **WorldEdit/WorldGuard** (7.3.11 / 7.0.13) - World editing and protection

### **Standard Build Plugins** (Full Server Deployment - "S" Rating)  
*Average server gets these - lowest common denominator especially for world generation*
- **QuickShop-Hikari** (6.2.0.9) - Shop system with per-server databases (qs_hik_SERVERNAME_)
- **mcMMO** (1.4.06) - Skills system with server-specific tables (mcmmo_SERVERNAME_)
- **EliteMobs** (9.4.2) - Boss mobs with world-specific configurations
- **BetterStructures** (1.8.1) - Enhanced structures with per-world naming
- **Citizens** (2.0.38) - NPC framework
- **Pl3xMap** (1.21.4-525) - Live world mapping
- **Quests** - Quest system implementation

### **Bespoke Plugins** (One-Off Specialized)
*Custom solutions for specific server needs*
- **Eternal Tower Defense** (1.4.0) - Multi-map tower defense (TOWER01 only)
- **Minetorio** - Factorio-inspired automation (MINT01 only)  
- **BentoBox Ecosystem** - Skylab suite (BENT01 only)
- **ArmoryCrate** - Advanced weapons system (specific servers)

### **Cross-Server Synchronization**
- **HuskSync** (3.8.1) - Player data sync with network groupings (SMPnet/DEVnet)
- **PLAN Analytics** (Portal: plan.archivesmp.com) - Network statistics with port 817X
- **Pl3xMap** (1.21.4-525) - Live world maps with server-specific ports (31XX)

## �🔧 Server Configurations

### **Hetzner Xeon** (135.181.212.169) - `archivesmp.site`
**Live production configurations** from the Helsinki-based Xeon server, including:
- Specialized minigame server configurations (active game modes)
- Development server templates (DEV server - live development environment)
- Fallback service configurations (production backup services)
- Experimental and modded server configs (EVO server development)

### **OVH Ryzen** (37.187.143.41) - `archivesmp.online`  
**Live production configurations** from the Gravelines-based Ryzen server, including:
- Main SMP world configurations (active player environment)
- BentoBox plugin configurations (live skyblock ecosystem)
- Network proxy configurations (Velocity/Geyser production setup)
- High-performance server optimizations (tuned for 64GB DDR5)
- Multi-language localization files (active translations)
- Primary gameplay server templates (battle-tested configurations)

## 🛠️ Setup Instructions

### Prerequisites
- AMP (Application Management Panel) installed
- Minecraft server instance configured  
- Appropriate server permissions
- **Understanding**: This is a production mirror - configurations are from live servers

### Initial Setup (Development/Testing)
1. Clone this repository to your development environment
2. Navigate to your local AMP `.ampdata` directory (typically `/home/amp/.ampdata`)
3. Copy relevant configurations from the appropriate server folder
4. **Test thoroughly** before applying to any production environment
5. Restart AMP services to apply changes

### Production Deployment (Advanced Users Only)
⚠️ **Warning**: These are live production configurations. Deploy with extreme caution.

### Configuration Deployment
```bash
# For Hetzner Xeon server (archivesmp.site)
cp -r HETZNER.135.181.212.169/amp_config_snapshot/* /path/to/amp/config/

# For OVH Ryzen server (archivesmp.online)
cp -r OVH.37.187.143.41/amp_config_snapshot/* /path/to/amp/config/
```

### Network Infrastructure Notes
- **Proxy Layer**: Velocity proxy runs on OVH Ryzen for load balancing
- **Bedrock Support**: Standalone Geyser enables cross-platform play
- **Domain Routing**: 
  - `archivesmp.online` → OVH Ryzen (primary services)
  - `archivesmp.site` → Hetzner Xeon (specialized services)

## 📦 Plugin Management

The `pluginsrepo/` contains **production-exported plugins** from the live server network. To install:

1. Download the desired `.jar` file
2. Place in your server's `plugins/` directory
3. Restart the server
4. Configure plugin settings as needed

### Featured Plugins (Asset Registry Verified - June 2025)

#### **Core Infrastructure & Management**
- **CMI/CMILib** (9.7.14.2/1.5.4.4) - 300+ commands, comprehensive server management
- **LuckPerms** - Advanced permission management system  
- **CoreProtect** - Block logging and rollback protection
- **Plan** - Advanced server analytics and player statistics
- **HuskSync** - Cross-server player data synchronization
- **Vault** - Economy and permission API foundation

#### **Economy & Commerce System**
- **TheNewEconomy (TNE)** - Core economy system across network
- **QuickShop-Hikari** (6.2.0.9+) - Advanced player shop system
- **QS Suite Addons**: Discount, DisplayControl, Limited, List, Plan, ShopItemOnly
- **ExcellentJobs** - Advanced job system (replaces Jobs Reborn)
- **Quests** + **CommunityQuests** (2.11.5) - Individual and server-wide quest systems

#### **Gameplay Enhancement Suite**  
- **mcMMO** - RPG skill progression system
- **EliteMobs** - Custom bosses, dungeons, arenas (EMadventure server)
- **ExcellentEnchants** - Custom enchantment system
- **LevelledMobs** - Dynamic mob scaling with distance
- **CombatPets** - Pet binding/resurrection system
- **Citizens** (2.0.38) - NPC creation and quest giving

#### **Cross-Platform & Network Infrastructure**
- **Velocity** (3.4.0) - Main proxy with extensive plugin ecosystem:
  - VelocityDiscordWhitelist, CMIV, Velocitab, PAPIProxyBridge  
  - VaultUnlocked, Spicord + addons, ViaVersion/ViaBackwards
- **Geyser + Floodgate** - Bedrock Edition support with Xbox broadcasting
- **mcxboxbroadcast** - Xbox Live integration for Bedrock players

#### **Specialized Server Systems**
- **BentoBox** (3.3.5) - Complete skyblock ecosystem (BENT01):
  - AcidIsland, OneBlock, Boxed, BSkyBlock, CaveBlock, SkyGrid  
  - 20+ addons including Challenges, Warps, Level, Likes, Limits
- **Axiom** - Advanced building tools (Creative server)  
- **WorldEdit/WorldGuard** - World management and protection
- **Creative-Sandbox** - Creative mode utilities and restrictions
- **BetterStructures** (1.8.1) - Enhanced world generation structures

#### **Minigame & Special Features**
- **CSMC + QualityArmory** - CounterStrike implementation  
- **PhantomWorlds** - Multi-world management for games
- **Minetorio** - Factorio-style automation gameplay
- **EternalTD** - Tower defense minigame system

## 🔄 Backup & Restore

### Asset Registry Information
**Source Documentation**: `Asset Registry ArSMP - Jun25.xlsx` and PDF exports
- **Most Current**: Per-server configurations and datapacks-in-use  
- **Paper Version**: 1.21.8 (build 60-29c8822)
- **Export Date**: June 2025
- **Accuracy Notes**: 
  - Per-server configs: ✅ Current (most authoritative)
  - Datapacks-in-use: ✅ Current 
  - Plugins-in-use: ⚠️ May be outdated (deprecated since 1.21.8 launch)
  - Velocity plugins: ⚠️ May be outdated (fell out of maintenance)
  - Permission/Command nodes: ✅ Mostly current (captured at 1.21.5)

### Creating Backups  
The `OG ZIP/` folder contains original backup archives:
- `datapacks-to-be-copied.zip`: Core datapack collection
- `HETZNER_amp_config_snapshot.zip`: Hetzner server backup  
- `OVH_amp_config_snapshot.zip`: OVH server backup
- `plugins.zip`: Plugin collection backup

### Restoring from Backup
1. Extract the appropriate ZIP file for your target server
2. **For OVH Ryzen**: Use configurations for primary game modes and high-traffic services
3. **For Hetzner Xeon**: Use configurations for specialized and development servers  
4. Follow the setup instructions for your target server
5. Verify all configurations are properly applied and optimized for the hardware

## 🌐 Multi-Language Support

The repository includes localization files for BentoBox plugin in multiple languages:
- English (en-US)
- German (de)
- Spanish (es)
- French (fr)
- Hungarian (hu)
- Indonesian (id)
- Japanese (ja)
- Latvian (lv)
- Polish (pl)
- Romanian (ro)
- Chinese Simplified (zh-CN)
- Croatian (hr)

## 🔧 Configuration Templates

The repository includes deployment templates for various application types:
- Node.js applications
- Python applications
- Deno applications
- Bun applications
- TeamSpeak 6 server
- Rising World server

## 📋 File Naming Conventions

- Server-specific folders use IP addresses for identification
- Configuration files maintain original AMP structure
- Datapacks retain their original version numbers
- Plugins follow standard Minecraft naming conventions

## ⚠️ Important Notes

### Production Environment Considerations
- **⚠️ CRITICAL**: These are **live production configurations** from active servers with real players
- **Always backup existing configurations** before applying changes to any environment
- **Test on DEV server first** (Hetzner Xeon) before deploying to production
- **Production Mirror**: Configurations exported ~1 hour ago from live environment
- **Resource allocation**: OVH Ryzen handles high-load servers, Hetzner Xeon for specialized use
- **Network dependencies**: Velocity proxy configurations affect all connected servers
- **Cross-platform compatibility**: Geyser configs impact active Bedrock Edition players

### Data Privacy & Exclusions
- **Player data**: Excluded from this export
- **World saves**: Not included (too large, privacy concerns)
- **Generated content**: Procedural generation data excluded
- **Configuration only**: Pure server configuration and plugin/datapack collections

### Hardware-Specific Considerations  
- **OVH Ryzen**: Optimized for high concurrent player counts and intensive gameplay
- **Hetzner Xeon**: Better suited for CPU-intensive tasks and development workloads
- **Storage**: RAID 1 setup on OVH requires different backup strategies than single SSD on Hetzner

## 🤝 Contributing

To contribute to this repository:

1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request with detailed description
5. Include any necessary documentation updates

## 📞 Support

For issues related to:
- **AMP Configuration**: Check AMP documentation
- **Datapacks**: Verify Minecraft version compatibility
- **Plugins**: Consult plugin-specific documentation
- **Server Setup**: Review hosting provider guidelines

## 📄 License

This repository contains configuration files and collected resources. Please respect individual datapack and plugin licenses.

---

*Last updated: September 29, 2025*
