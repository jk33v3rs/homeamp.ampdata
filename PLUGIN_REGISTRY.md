# 🔌 Complete Plugin Registry & CI/CD API Endpoints

**Source**: Per-server configuration matrix from production deployment  
**Purpose**: Automated plugin management and CI/CD scripting  
**Last Updated**: September 29, 2025

## 📋 Plugin Classification

- **M (Minimal)** = Essential foundation plugins - basically everyone gets these
- **S (Standard)** = Full build plugins - average server deployment, lowest common denominator especially for world generation
- **Bespoke** = One-off specialized plugins for specific server needs
- **Version Format**: `current_version [supported_mc_versions]`

---

## 🏗️ **MINIMAL BUILD PLUGINS** (M - Essential Foundation)

### **Permission & Protection**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **LuckPerms-Bukkit** | 5.4.145 [1.21.3-1.21.4] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=28140` |
| **CoreProtect** | 23.2 [1.20.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=8631` |
| **WorldEdit** | 7.3.11 [1.21.4] | EngineHub | `https://builds.enginehub.org/job/worldedit/last-successful/` |
| **WorldGuard-Bukkit** | 7.0.13 [1.21.4] | EngineHub | `https://builds.enginehub.org/job/worldguard/last-successful/` |
| **VaultUnlocked** | 2.10.0 [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=34315` |

### **Multi-Tool & Utilities**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **CMI** | 9.7.14.2 | Zrips | *Premium - Manual Download* |
| **CMILib** | 1.5.4.4 | Zrips | *Premium - Manual Download* |
| **PlaceholderAPI** | 2.11.6 [1.21] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=6245` |
| **ProtocolLib** | 5.3.0 [1.21] | SpigotMC | `https://ci.dmulloy2.net/job/ProtocolLib/lastSuccessfulBuild/` |

### **Performance & Optimization**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **Chunky** | 1.4.36 [1.21.x] | Modrinth | `https://api.modrinth.com/v2/project/fALzjamp/version` |
| **ChunkyBorder** | 1.2.23 | Modrinth | `https://api.modrinth.com/v2/project/84B8RjQs/version` |
| **nightcore** | 2.7.5.2 [1.21.4-1.21.5] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=82648` |
| **packetevents-spigot** | 2.7.0 | SpigotMC | `https://ci.codemc.io/job/retrooper/job/packetevents/lastSuccessfulBuild/` |

### **Cross-Server Networking**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **HuskSync** | 3.8.1 | Modrinth | `https://api.modrinth.com/v2/project/tdUdJmi5/version` |
| **PAPIPProxyBridge-Bukkit** | 1.8.1 [1.21.4-1.21.5] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=81906` |

### **Monitoring & Analytics**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **PLAN** | Latest | Modrinth | `https://api.modrinth.com/v2/project/ftdbN0KK/version` |
| **ImageFrame** | 1.8.2 (build 124) | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=106030` |

### **Building & World Management**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **FreeMinecraftModels** | 1.1.4 | [1.20.4] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=97503` |
| **LibsDisguises** | 11.0.5 | [1.21.5] | SpigotMC | `https://ci.md-5.net/job/LibsDisguises/lastSuccessfulBuild/` |
| **GlowingItems** | Latest | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=94441` |
| **DamageIndicator** | Latest | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=84052` |
| **Craftbook** | Latest | [1.21.x] | EngineHub | `https://builds.enginehub.org/job/craftbook/last-successful/` |

### **Economy & Integration**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **TheNewEconomy** | 0.1.3.4 | [1.21.x] | GitHub | `https://api.github.com/repos/TheNewEconomy/EconomyCore/releases/latest` |
| **economy-bridge** | 1.2.1 | [1.21.5] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=85927` |

### **Bedrock Compatibility**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **Hurricane** | Latest | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=105825` |

---

## 🎯 **STANDARD BUILD PLUGINS** (S - Full Server Deployment)

### **Survival & RPG**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **EliteMobs** | 9.4.2 | [1.21.?] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=40090` |
| **mcMMO** | 1.4.06 | [1.7.10] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=64348` |
| **LevelledMobs** | 4.3.1.1 b114 | [1.21] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=74304` |
| **Citizens** | 2.0.38 | [1.21.x] | SpigotMC | `https://ci.citizensnpcs.co/job/Citizens2/lastSuccessfulBuild/` |
| **CombatPets** | 2.4.1 | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=93310` |

### **Economy & Shopping**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **QuickShop-Hikari** | 6.2.0.9 [1.20-1.21] | CodeMC Jenkins | `https://ci.codemc.io/job/Ghost-chu/job/QuickShop-Hikari/lastSuccessfulBuild/` |
| **Shop Search (QSlimefindItemAddOn)** | 2.0.7.6-RELEASE | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=90766` |

### **World Enhancement**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **BetterStructures** | 1.8.1 [1.21.5] | Modrinth | `https://api.modrinth.com/v2/project/rtafUJC6/version` |
| **Pl3xMap** | 1.21.4-525 [1.21.4] | Modrinth | `https://api.modrinth.com/v2/project/VL9MpOH1/version` |
| **Pl3xMapExtras** | 1.2.0 [1.21.4] | Modrinth | `https://api.modrinth.com/v2/project/pl3xmapextras/version` |
| **Lootin** | 12.1 [1.16-1.21.5] | Modrinth | `https://api.modrinth.com/v2/project/HKuOwJgX/version` |

### **Quest & Job Systems**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **Quests** | Latest | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=3711` |
| **CommunityQuests** | 2.11.5 | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=68423` |
| **JobsReborn** | 5.2.6.0 | [1.20] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=4216` |
| **JobListings** | 2.0.0 | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=88288` |

### **Excellent Series Plugins**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **ExcellentChallenges-Renewed** | 3.1.7 | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=103666` |
| **ExcellentEnchants** | 5.0.0.beta | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=61693` |
| **ExcellentJobs** | 1.11.1 | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=80842` |

### **Utility & Quality of Life**
| Plugin | Version | MC Support | Distribution | API Endpoint |
|--------|---------|------------|--------------|--------------|
| **TreeFeller** | 1.26.1 | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=7234` |
| **VillagerOptimiser** | 1.6.2 | [1.21] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=68517` |
| **WorldBorder** | 1.19 | [1.21.x] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=60905` |
| **ResurrectionChest** | 1.9.0 | [1.19] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=87542` |
| **ResourcePackManager** | 1.3.0 | [1.21] | SpigotMC | `https://api.spigotmc.org/legacy/update.php?resource=63877` |

---

## 🎮 **BESPOKE PLUGINS** (One-Off Specialized Implementations)

### **Server-Specific Custom Solutions**
| Plugin | Version | MC Support | Server(s) | Notes | API Endpoint |
|--------|---------|------------|-----------|-------|--------------|
| **BentoBox** | 3.3.5 | [1.21.4-1.21.5] | BENT01 | Skyblock ecosystem suite | `https://ci.codemc.org/job/BentoBoxWorld/job/BentoBox/lastSuccessfulBuild/` |
| **Axiom** | Latest | [1.21.x] | Creative Servers | Advanced building tool | `https://api.modrinth.com/v2/project/bcOXOlm2/version` |

**Note**: Eternal Tower Defense and ArmoryCrate removed - not in use

---

## 🔧 **QUICKSHOP-HIKARI ADDON ECOSYSTEM** 

**Priority**: CI/CD First → API Fallback → Never GitHub Releases

| Addon | Version | CI/CD (Primary) | CI/CD (Secondary) | API Fallback |
|-------|---------|----------------|-------------------|--------------|
| **Addon-Discount** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |
| **Addon-DisplayControl** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |
| **Addon-Limited** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |
| **Addon-List** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |
| **Addon-Plan** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |
| **Addon-ShopItemOnly** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |
| **Compat-EliteMobs** | 6.2.0.11 | *Per CSV: Use QS Modrinth distribution* | - | Modrinth API |
| **Compat-WorldEdit** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |
| **Compat-WorldGuard** | 6.2.0.11 | CodeMC Jenkins | GitHub Actions | Modrinth (if needed) |

**Endpoints**:
- **CodeMC Jenkins**: `https://ci.codemc.io/job/Ghost-chu/job/QuickShop-Hikari/lastSuccessfulBuild/`
- **GitHub Actions**: `https://api.github.com/repos/Ghost-chu/QuickShop-Hikari/actions/workflows/build.yml/runs`
- **Modrinth Fallback**: `https://api.modrinth.com/v2/project/quickshop-hikari/version`

---

## 🚧 **DEVELOPMENT/TESTING PLUGINS**

| Plugin | Status | Notes |
|--------|--------|-------|
| **DeluxeMenus** | Might be back | Version 1.14.0 [1.21.x] |
| **eShulkerBox** | Testing | CMI implementation testing |
| **LibertyBans** | Skip for now | Build 158 available |
| **PaperTweaks** | In consideration | Version TBD |

---

## 📡 **CI/CD AUTOMATION GUIDELINES**

### **🎯 Update Source Priority Order**
1. **CI/CD Systems** (Most Current)
   - CodeMC Jenkins builds
   - GitHub Actions workflows  
   - Private repository CI/CD
   - EngineHub Jenkins builds

2. **Fallback APIs** (Only when CI/CD unavailable)
   - Modrinth API
   - SpigotMC API
   
3. **Avoid** (Rarely up-to-date)
   - GitHub Releases (often outdated)
   - Manual downloads

### **🤝 CI/CD Etiquette & Best Practices**
- **Be respectful** - These are community-provided services
- **Use reasonable intervals** - Don't hammer CI systems
- **Implement backoff** - Respect 429 rate limit responses  
- **Cache results** - Avoid repeated identical requests
- **User-Agent identification** - Always identify your bot/script
- **Monitor for changes** - Respect if access patterns change
- **Consider donating** - Support infrastructure providers when possible

### **API Rate Limits**
- **SpigotMC**: 120 requests/hour per IP
- **Modrinth**: 300 requests/minute per IP  
- **GitHub**: 5000 requests/hour (authenticated), 60/hour (unauthenticated)
- **GitHub Actions**: Same as GitHub API limits
- **CodeMC Jenkins**: No official limits (be extra respectful)
- **EngineHub**: No official limits (community courtesy applies)
- **Private CI/CD**: Varies - always respect infrastructure owners

### **Version Check Endpoints**
```bash
# SpigotMC
curl -H "User-Agent: ArchiveSMP-UpdateChecker" "https://api.spigotmc.org/legacy/update.php?resource={ID}"

# Modrinth  
curl -H "User-Agent: ArchiveSMP-UpdateChecker" "https://api.modrinth.com/v2/project/{ID}/version"

# GitHub Releases
curl -H "User-Agent: ArchiveSMP-UpdateChecker" "https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"

# GitHub Actions (for automation builds)
curl -H "User-Agent: ArchiveSMP-UpdateChecker" -H "Authorization: token {GITHUB_TOKEN}" \
  "https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_ID}/runs?status=success&per_page=1"

# EngineHub (Jenkins CI)
curl -H "User-Agent: ArchiveSMP-UpdateChecker" "https://builds.enginehub.org/job/{PROJECT}/lastSuccessfulBuild/api/json"

# CodeMC Jenkins (Ghost-chu & others)
curl -H "User-Agent: ArchiveSMP-UpdateChecker" "https://ci.codemc.io/job/{AUTHOR}/job/{PROJECT}/lastSuccessfulBuild/api/json"
```

### **Download Patterns**
```bash
# SpigotMC Direct Download (Premium required for some)
https://api.spigotmc.org/legacy/download.php?resource={ID}&version={VERSION}

# Modrinth Direct Download
https://cdn.modrinth.com/data/{PROJECT_ID}/versions/{VERSION_ID}/{FILENAME}

# GitHub Release Asset
https://github.com/{OWNER}/{REPO}/releases/download/{TAG}/{FILENAME}

# CodeMC Jenkins Artifact Download
https://ci.codemc.io/job/{AUTHOR}/job/{PROJECT}/{BUILD_NUMBER}/artifact/{PATH_TO_JAR}

# GitHub Actions Artifact (requires authentication)
# Use GitHub API to get artifact download URL, then download with token
```

---

## 🏷️ **Per-Server Plugin Deployment Matrix**

**Reference**: Use per-server configuration CSV for exact deployment mappings  
**Database Naming**: Follow pattern `{plugin}_{SERVER_ABBR}_` for SQL tables  
**Port Assignments**: Follow pattern established in ImageFrame (91XX/31XX ranges)  

**Total Plugin Count**: 75+ active plugins across network  
**Update Frequency**: Weekly automated checks recommended  
**Critical Dependencies**: LuckPerms, CoreProtect, CMI, HuskSync for network operations
