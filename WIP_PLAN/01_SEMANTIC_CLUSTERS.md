# Semantic Cluster Definitions (Pre-Pass Analysis)

## Purpose
Define the semantic patterns for clustering DEFINITE_FACTS in Pass 3.
NOT for use in Pass 1 (concept surfacing) or Pass 2 (resolution).

---

## Server/Infrastructure Clusters

### ✓ OVH_RESOURCE
**What it is**: Physical/network resources on OVH Debian server (37.187.143.41)
**Why it matters**: Need to know what exists there for deployment planning

### ✓ OVH_SPEC  
**What it is**: Specifications/capabilities of OVH server (CPU, RAM, disk, network)
**Why it matters**: Determines what we can deploy there

### ✓ HETZNER_RESOURCE
**What it is**: Physical/network resources on Hetzner Debian server (135.181.212.169)
**Why it matters**: Current hosting server, need inventory of services

### ✓ HETZNER_SPEC
**What it is**: Specifications/capabilities of Hetzner server
**Why it matters**: Determines what's already deployed and capacity

### ✓ HOST
**What it is**: The server hosting services (currently Hetzner, potentially both)
**Why it matters**: Distinguishes hosting role from client role

### ✓ HOST_RESOURCE
**What it is**: Resources provided BY the host server (MinIO, MariaDB, Redis, Web API)
**Why it matters**: These are shared services client servers consume

### ✓ HOST_SPEC
**What it is**: Host-specific requirements/configurations
**Why it matters**: Different from client requirements

### ✓ CLIENT
**What it is**: Server consuming services from host (currently OVH, potentially both)
**Why it matters**: Distinguishes client role from hosting role

### ✓ CLIENT_RESOURCE
**What it is**: Resources ON the client server (AMP instances, local agent)
**Why it matters**: What client provides vs what it consumes

### ⚠️ PRIMARY / SECONDARY
**Possible meanings**:
- Primary: Hetzner (current prod), Secondary: OVH (pending deployment)
- Primary: Master/active service, Secondary: Backup/standby
- Primary: First deployment target, Secondary: second deployment target
**Why ambiguous**: Multiple valid interpretations, need context to resolve

---

## Data Clusters

### ✓ BASELINE_DATA
**What it is**: Universal configs that should be identical across instances
**Why it matters**: Source of truth for drift detection
**Location**: data/baselines/universal_configs/, utildata/universal_configs_analysis.json

### ✓ UPDATE_DATA
**What it is**: Changes to be deployed, plugin updates, config modifications
**Why it matters**: What we're trying to ship to production

### ✓ UNIVERSAL_PLUGIN_DATA
**What it is**: Plugin configs that are identical for all instances (after cleanup: 82 plugins)
**Why it matters**: These should NOT vary, drift here = bug/mistake

### ✓ VARIANCE_DATA
**What it is**: Configs that SHOULD differ per server/instance (23 plugins with intentional variations)
**Why it matters**: Drift here might be intentional (server-specific) vs mistake

---

## Schema/Example Clusters

### ✓ EXAMPLE_STRICT_SCHEMA
**What it is**: Template with all fields required, strict validation
**Why it matters**: For critical configs where mistakes = crashes

### ✓ EXAMPLE_SCHEMA_SNIPPET
**What it is**: Partial template, flexible, shows pattern not all fields
**Why it matters**: For docs/examples, not production configs

---

## Server Instance Short Names (Placeholder Cluster)

**Pattern**: ADS01, BIG01, CAR01, DEV01, EVO01, MIN01, PRI01, ROY01, SMP101, SUNK01, TOW01 (Hetzner)
**Pattern**: BENT01, CLIP01, CREA01, CSMC01, EMAD01, GEY01, HARD01, HUB01, MINE01, SMP201, VEL01 (OVH)

**What these are**: AMP instance IDs, NOT physical servers
**Why it matters**: Massive confusion source - "server" could mean this OR Debian box

---

## UI/Code Element Clusters

### ✓ UI_ELEMENT_X
**What it is**: Frontend component (button, view, form in web UI)
**Why it matters**: Maps to backend endpoint and Python code

### ✓ ELEMENT_X_PY
**What it is**: Backend Python code implementing UI_ELEMENT_X
**Why it matters**: Implementation of UI feature

### ✓ URL_OURLOC_ELEMENT_X
**What it is**: Our API endpoint URL for ELEMENT_X
**Why it matters**: How frontend calls backend

### ✓ URL_CICD_ELEMENT_X_PRI / _SEC
**What it is**: External CI/CD endpoint for plugin updates (primary/secondary sources)
**Why it matters**: Where we fetch plugin updates from
**Examples**: 
- GitHub Releases API (primary for many plugins)
- SpigotMC API (secondary or primary for some)
- Hangar API (for Paper plugins)

---

## Script/Function Clusters

### ✓ SCRIPT_FUNCTION_PY
**What it is**: Python function in codebase (actual implementation)
**Why it matters**: The code we're auditing

### ✓ SCRIPT_FUNCTION_ENV
**What it is**: Environment where function runs (dev Windows vs prod Debian)
**Why it matters**: Path differences, permissions, available tools

### ✓ SCRIPT_FUNCTION_CFG
**What it is**: Configuration required for function to work
**Why it matters**: Missing config = function crashes

---

## Inferred Additional Clusters

### AIRGAP_BOUNDARY
**What it is**: The separation between dev environment (Windows) and prod (Debian)
**Why it matters**: I cannot directly access prod, must generate commands for human

### TEMPORAL_STATE
**What it is**: Time-dependent facts (as of date X, code was Y)
**Why it matters**: Code changes, bugs get fixed, need timestamps

### SEMANTIC_COLLISION
**What it is**: Terms with multiple meanings ("server", "baseline", "deployment")
**Why it matters**: Disambiguation required before making decisions

### DEPENDENCY_CHAIN
**What it is**: A needs B needs C needs D relationships
**Why it matters**: Can't ship A if B is broken

### CONTAMINATION_RISK
**What it is**: Places where context mixing causes errors
**Why it matters**: Prevention system for cross-context poisoning

---

## Pattern Recognition

**Naming convention detected**:
- `THING_RESOURCE` = what exists on/in THING
- `THING_SPEC` = specifications/requirements of THING
- `URL_WHERE_WHAT` = endpoint location and purpose
- `ELEMENT_X_HOW` = implementation method/language

**Semantic pattern**: Self-explanatory cluster names using underscores to show relationships
