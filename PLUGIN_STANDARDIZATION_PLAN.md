# Plugin Standardization Plan - ArchiveSMP

**Goal**: Standardize configs for unified cross-world/cross-server gameplay while respecting intentional architectural differences.

---

## Architecture Overview

### HuskSync Clusters (Intentional Variation)
- **DEVnet**: Creative/freebuild worlds - Full sync
- **SMPnet**: Adventure survival worlds - Full sync  
- **SMPnet Limited**: Ender chest, perms, achievements, XP, levels, stats only
- **Hardcore**: Achievements and perms only

**Action**: ✅ This variation is CORRECT - different clusters need different sync configs

---

## 🎮 UNIFIED GAMEPLAY PLUGINS (Must Be Identical)

These plugins define the core gameplay experience and **MUST** be standardized across all worlds for consistent player experience:

### 1. mcMMO ✅ ALREADY GOOD
**Current**: 13 variables vs 450 universal (0.029 ratio)
- **Status**: Well-standardized
- **Action**: None needed

### 2. Quests ✅ ALREADY GOOD  
**Current**: 10 variables vs 186 universal (0.054 ratio)
- **Status**: Well-standardized
- **Action**: None needed

### 3. ExcellentQuests ✅ ALREADY GOOD
**Current**: 12 variables vs 1138 universal (0.011 ratio)
- **Status**: Well-standardized
- **Action**: None needed

### 4. CombatPets ✅ GOOD
**Current**: 40 variables vs 165 universal (0.242 ratio)
- **Status**: Acceptable variation
- **Action**: Review 40 variables to ensure they're intentional (pet spawns per world?)

### 5. CommunityQuests ✅ GOOD
**Current**: 50 variables vs 111 universal (0.450 ratio)
- **Status**: Acceptable variation
- **Action**: Review if quest configs should be more universal

### 6. QuickShop-Hikari ✅ GOOD
**Current**: 85 variables vs 180 universal (0.472 ratio)
- **Status**: Acceptable variation
- **Action**: Review shop configs - should pricing be more unified?

### 7. ExcellentChallenges ⚠️ NEEDS REVIEW
**Current**: 150 variables vs 215 universal (0.698 ratio)
- **Status**: Medium priority - review needed
- **Action**: 
  - [ ] Identify which challenge configs should be universal
  - [ ] Standardize challenge rewards/difficulty across worlds
  - [ ] Target: <50 variables (world-specific challenges only)

### 8. JobListings 🔴 NEEDS WORK
**Current**: 100 variables vs 10 universal (10.0 ratio)
- **Status**: HIGH PRIORITY - almost nothing is standardized!
- **Root Cause**: Database credentials varying, timing settings varying
- **Action**:
  - [ ] Centralize database connection (all instances → one DB)
  - [ ] Standardize Mail.ExpireTime, Mail.JoinDelay
  - [ ] Standardize Orders.* timing values
  - [ ] **Expected**: 100+ universal, <10 variables (just server name)

### 9. Jobs (JobsReborn) ✅ ALREADY GOOD
**Current**: 24,658 universal settings, no variables listed
- **Status**: Fully standardized (but massive config!)
- **Action**: None needed (consider optimization to reduce size)

### 10. TheNewEconomy 🔴 NEEDS WORK
**Current**: 51 variables vs 44 universal (1.159 ratio)
- **Status**: HIGH PRIORITY - more variables than universal!
- **Root Cause**: Server names and IDs varying
- **Action**:
  - [ ] Verify economy configs are identical (rates, taxes, etc.)
  - [ ] Allow Core.Server.Name to vary (intentional per-world)
  - [ ] Generate unique Core.ServerID for each instance (currently only 2!)
  - [ ] **Expected**: 80+ universal, 17 variables (server names/IDs only)

---

## 🔧 PARALLEL INFRASTRUCTURE PLUGINS (Near-Universal)

These support gameplay but aren't direct gameplay mechanics. Should be mostly identical:

### 11. CoreProtect ✅ ALREADY GOOD
**Current**: 17 variables vs 47 universal (0.362 ratio)
- **Status**: Well-standardized
- **Action**: Review 17 variables - likely DB credentials (intentional)

### 12. PAPIProxyBridge 🔴 NEEDS WORK
**Current**: 34 variables vs 6 universal (5.667 ratio)
- **Status**: HIGH PRIORITY - barely any universal configs!
- **Root Cause**: Redis credentials varying
- **Analysis**: 
  - settings.redis.credentials.host (2 values) → Likely Hetzner vs OVH
  - settings.redis.credentials.password (2 values)
- **Action**:
  - [ ] Document Redis topology: Which server hosts which Redis instance?
  - [ ] Decision: Unify to 1 Redis, or keep 2 Redis clusters intentionally?
  - [ ] If 2 Redis (Hetzner + OVH): Document and accept 4 variables
  - [ ] If 1 Redis: Standardize all instances to single connection
  - [ ] **Expected**: 34+ universal, ~4 variables (if 2 Redis) or 40 universal, 0 variables (if 1 Redis)

### 13. VillagerOptimizer ✅ GOOD
**Current**: 20 variables vs 55 universal (0.364 ratio)
- **Status**: Acceptable
- **Action**: None needed

---

## 🌐 HOSTING/WEB PLUGINS (Intentional Variation)

These have legitimate per-instance variation:

### 14. Pl3xMap - Public (Outside Firewall) ⚠️ NEEDS REVIEW
**Current**: 45 variables vs 44 universal (1.023 ratio)
- **Used For**: SMP worlds (public access)
- **Root Cause**: 
  - settings.internal-webserver.port (7 values)
  - settings.web-address (7 values)
- **Action**:
  - [ ] Document port allocation per instance
  - [ ] Standardize world display names ("Overworld", "Nether", "End")
  - [ ] **Expected**: Ports/addresses vary (intentional), rest universal

### 15. Pl3xMap - Private (Behind YunoHost Auth) ⚠️ NEEDS REVIEW
**Used For**: CS:MC (anti-screen camping), Royale, etc.
- **Same analysis as public Pl3xMap**
- **Action**: Ensure auth configs are correct per security policy

### 16. Plan (All Instances) ✅ GOOD
**Current**: 51 variables vs 143 universal (0.357 ratio)
- **Behind YunoHost auth wall**
- **Status**: Acceptable variation
- **Action**: Review variables - likely DB/web configs (intentional)

---

## 🚫 PLUGINS TO IGNORE

### bStats
**Status**: Not used, ignore completely
- **Action**: Consider removing from all instances if truly unused

---

## ✅ ALREADY WELL-CONFIGURED (No Action Needed)

These plugins are properly standardized:
- LuckPerms (0.337 ratio)
- CraftBook5 (0.258 ratio)
- LevelledMobs (0.190 ratio)
- CMI (0.087 ratio)
- LibsDisguises (0.005 ratio)
- ImageFrame (0.879 ratio) - likely per-world artwork
- HuskSync (1.645 ratio) - **INTENTIONAL** cluster variation
- floodgate (0.667 ratio) - Bedrock integration, acceptable

---

## 🎯 PRIORITY ACTION ITEMS

### Phase 1: Critical Gameplay Standardization (Week 1)

#### 1. JobListings (Immediate)
**Impact**: HIGH - Economy/job system inconsistency  
**Complexity**: MEDIUM
```
Current: 100 variables vs 10 universal (10x ratio)
Target:  10 variables vs 100 universal (0.1x ratio)
```
**Steps**:
- [ ] Audit current DB connections (which instances use which DB?)
- [ ] Decision: Centralize to 1 DB or keep separate DBs per network?
- [ ] Standardize timing values (ExpireTime, JoinDelay, OrderDeadline)
- [ ] Deploy standardized configs to all 10 instances
- [ ] Test job listings work identically across worlds

#### 2. TheNewEconomy (Immediate)
**Impact**: HIGH - Core economy inconsistency  
**Complexity**: LOW
```
Current: 51 variables vs 44 universal (1.16x ratio)
Target:  17 variables vs 80 universal (0.21x ratio)
```
**Steps**:
- [ ] Generate unique Core.ServerID for all 17 instances
- [ ] Verify economy rates/taxes/features are identical
- [ ] Allow Core.Server.Name to vary (per-world identity)
- [ ] Deploy standardized configs
- [ ] Test economy balances sync correctly

#### 3. PAPIProxyBridge (Immediate)
**Impact**: MEDIUM - Cross-server placeholder sync  
**Complexity**: LOW
```
Current: 34 variables vs 6 universal (5.67x ratio)
Target:  4 variables vs 36 universal (0.11x ratio) OR 0 variables vs 40 universal
```
**Steps**:
- [ ] Document Redis topology (Hetzner Redis + OVH Redis?)
- [ ] If 2 Redis: Accept 4 variables (host + password × 2)
- [ ] If 1 Redis: Standardize all to single connection
- [ ] Deploy configs
- [ ] Test placeholder sync works

---

### Phase 2: Gameplay Polish (Week 2)

#### 4. ExcellentChallenges
**Impact**: MEDIUM - Challenge consistency  
**Complexity**: MEDIUM
```
Current: 150 variables vs 215 universal (0.70x ratio)
Target:  50 variables vs 300 universal (0.17x ratio)
```
**Steps**:
- [ ] Review 150 variable settings
- [ ] Identify world-specific challenges (keep variable)
- [ ] Standardize challenge rewards/requirements/cooldowns
- [ ] Deploy and test

#### 5. CommunityQuests & CombatPets
**Impact**: LOW - Minor gameplay consistency  
**Complexity**: LOW
- [ ] Review variable settings
- [ ] Standardize where appropriate
- [ ] Test and deploy

---

### Phase 3: Infrastructure Optimization (Week 3)

#### 6. Pl3xMap Configuration
**Impact**: LOW - Visual/UX consistency  
**Complexity**: LOW
- [ ] Document port allocation (avoid conflicts)
- [ ] Standardize world display names
- [ ] Verify auth configs correct for private instances
- [ ] Update web-address URLs if needed

#### 7. Plan Configuration
**Impact**: LOW - Analytics consistency  
**Complexity**: LOW
- [ ] Review 51 variables
- [ ] Ensure DB configs are correct
- [ ] Verify auth integration works

---

## 📋 IMPLEMENTATION CHECKLIST

### Pre-Work
- [x] Analyze all plugin configs (DONE - this document)
- [ ] Document HuskSync cluster architecture
- [ ] Document Redis topology (PAPIProxyBridge)
- [ ] Document database architecture (JobListings, CoreProtect)

### Automation Tools Needed
- [ ] `scripts/standardize_job_listings.py` - Centralize DB, standardize timing
- [ ] `scripts/standardize_economy.py` - Generate unique ServerIDs, verify rates
- [ ] `scripts/standardize_papi_bridge.py` - Redis connection standardization
- [ ] `scripts/validate_gameplay_configs.py` - Verify gameplay plugins identical

### Testing Strategy
- [ ] Deploy to DEV01 first
- [ ] Test economy, jobs, quests work correctly
- [ ] Verify cross-server sync (HuskSync, PAPIProxyBridge)
- [ ] Roll out to production gradually (1 server at a time)

---

## 📊 EXPECTED OUTCOMES

**Before Standardization**:
- 10 core gameplay plugins
- 3 plugins with ratio > 1.0 (more variables than universal)
- Inconsistent player experience across worlds
- Economy/jobs potentially broken across networks

**After Standardization**:
- All gameplay plugins with ratio < 0.5 (mostly universal)
- Consistent player experience (mcMMO, quests, economy, jobs)
- Clear documentation of intentional variations (HuskSync clusters, server names)
- Automated validation to prevent config drift

---

## 🎮 GAMEPLAY IMPACT SUMMARY

### Unified Across All Worlds ✅
- mcMMO skill progression & rates
- Quest definitions & rewards  
- Combat pet mechanics
- Shop economics (QuickShop)
- Challenge definitions
- Job definitions & pay rates
- Economy rates & taxes
- Server optimization settings

### Intentionally Different Per-World/Network 📍
- HuskSync clusters (DEVnet, SMPnet, SMPnet Limited, Hardcore)
- Server names/IDs (world identity)
- Pl3xMap ports/URLs (hosting infrastructure)
- Plan/CoreProtect DB connections (infrastructure)
- World display names (per-world branding)

---

**Document Status**: ✅ READY FOR IMPLEMENTATION  
**Priority**: 🔴 HIGH - JobListings, TheNewEconomy, PAPIProxyBridge  
**Owner**: Configuration Manager System  
**Last Updated**: 2025-11-09
