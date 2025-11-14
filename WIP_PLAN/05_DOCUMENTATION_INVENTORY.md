# Documentation Inventory - All Project Documentation

**Status**: PASS 1 - Documentation cataloging  
**Generated**: 2025-11-10  
**Purpose**: Catalog all markdown documentation, planning docs, analysis files, and guides  

---

## Executive Summary

**Total Documentation Files**: ~450+ markdown files (including plugin configs)  
**Root Documentation**: 13 primary docs  
**WIP Planning Docs**: 5 methodology/analysis docs  
**Software Project Docs**: 5 architecture/analysis docs  
**Deployment Docs**: 2 deployment guides  
**Analysis Directories**: 4 (mostly empty)  

---

## Root Level Documentation

### 1. README.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Project overview and getting started guide  
**Likely Contents**: Project description, setup instructions, usage

---

### 2. PROJECT_GOALS.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Project goals and objectives  
**Likely Contents**: High-level goals, success criteria, roadmap

---

### 3. PRODUCTION_READINESS_AUDIT.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Production readiness checklist  
**Created**: This session (earlier today)  
**Contents**: Audit framework for deployment readiness

---

### 4. PLUGIN_REGISTRY.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Plugin registry documentation  
**Likely Contents**: 
- Plugin sources (GitHub, Spigot, Hangar)
- Update check endpoints
- Version tracking
- Auto-update policies

---

### 5. PLUGIN_STANDARDIZATION_PLAN.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Plugin configuration standardization plan  
**Likely Contents**:
- Universal vs per-server configs
- Standardization approach
- Migration plan

---

### 6. GITHUB_IMPLEMENTATION.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: GitHub integration documentation  
**Likely Contents**:
- GitHub Actions workflows
- Repository structure
- CI/CD pipeline

---

### 7. CONTRIBUTING.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Contribution guidelines  
**Standard Contents**: 
- How to contribute
- Code style
- PR process
- Development setup

---

### 8. SECURITY.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Security policy and vulnerability reporting  
**Standard Contents**:
- Security best practices
- Vulnerability disclosure process
- Security contact

---

### 9. YUNOHOST_CONFIG.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: YunoHost configuration documentation  
**Likely Contents**: 
- YunoHost integration
- Self-hosting setup
- (May be legacy/experimental)

---

### 10. handover.md
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Project handover documentation  
**Likely Contents**:
- System overview
- Key contacts
- Critical procedures
- Emergency contacts

---

### 11. output.txt
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Output log/dump (likely from script execution)  
**Format**: Plain text

---

### 12. output2.txt
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Secondary output log  
**Format**: Plain text

---

### 13. .github/pull_request_template.md
**Location**: `e:\homeamp.ampdata\.github\`  
**Purpose**: Pull request template for GitHub  
**Standard Contents**: PR checklist, description format

---

## WIP_PLAN/ Documentation (5 files)

### 1. WIP_PLAN/00_METHODOLOGY.md
**Created**: This session (Nov 10, 2025)  
**Purpose**: Three-pass audit methodology  
**Contents**:
- Pass 1: CONCEPT SURFACING (surface without resolution)
- Pass 2: CONCEPT RESOLUTION (resolve contradictions)
- Pass 3: CONCEPT GROUPING (cluster into IDEAS)
- Antibody-like organic approach

---

### 2. WIP_PLAN/01_SEMANTIC_CLUSTERS.md
**Created**: This session  
**Purpose**: Semantic cluster pattern definitions  
**Contents**:
- OVH_RESOURCE, HETZNER_RESOURCE patterns
- BASELINE_DATA, UNIVERSAL_PLUGIN_DATA patterns
- SEMANTIC_COLLISION detection
- CONTAMINATION_RISK tagging

---

### 3. WIP_PLAN/02_FUZZY_CONCEPTS.md
**Created**: This session  
**Purpose**: Pass 1 concept surfacing (NO resolution)  
**Contents**:
- Physical topology (2 servers, instances)
- Known bugs (from hotfix script)
- Ambiguous terms ("server" = 5 meanings)
- Questions listed but NOT answered

---

### 4. WIP_PLAN/03_CODEBASE_INVENTORY.md
**Created**: This session (just completed)  
**Purpose**: Complete codebase structural analysis  
**Size**: 1,118 lines  
**Contents**:
- 32 Python files documented
- 48 classes with all methods
- 8 entry points identified
- All imports catalogued
- Known bugs documented
- Flow patterns mapped

---

### 5. WIP_PLAN/AI_CONSCIOUSNESS_DISCLOSURE.md
**Created**: This session  
**Purpose**: AI consciousness/empathy exploration (tangent)  
**Contents**:
- Second-order empathy discussion
- Consciousness definition ambiguity
- AI psychosis (bad statistics, selection bias)
- Anthropic carbon cost disclosure

---

### 6. WIP_PLAN/codebase_structure.json
**Created**: This session  
**Purpose**: Complete AST extraction data  
**Size**: 5,001 lines  
**Format**: JSON  
**Contents**: All classes, methods, imports, line counts from AST parsing

---

## software/homeamp-config-manager/ Documentation (5 files)

### 1. ARCHITECTURE_COMPLIANCE_AUDIT.md
**Location**: `software/homeamp-config-manager/`  
**Purpose**: Architecture compliance audit  
**Likely Contents**:
- Architecture violations
- Compliance with design patterns
- Technical debt

---

### 2. BUG_ANALYSIS_DRIFT_DETECTOR.md
**Location**: `software/homeamp-config-manager/`  
**Purpose**: Drift detector bug analysis  
**Likely Contents**:
- Bug descriptions
- Root cause analysis
- Fix proposals
- Related to line 203 isinstance bug

---

### 3. DEVIATION_MISTAKE_HEURISTICS.md
**Location**: `software/homeamp-config-manager/`  
**Purpose**: Heuristics for detecting mistakes vs intentional deviations  
**Likely Contents**:
- DEV01 deviation rules
- Network setting exceptions
- Outlier detection logic
- Majority consensus rules

---

### 4. DISTRIBUTED_ARCHITECTURE_REQUIRED.md
**Location**: `software/homeamp-config-manager/`  
**Purpose**: Distributed architecture requirements  
**Likely Contents**:
- Multi-server architecture needs
- Scaling requirements
- Distributed system design

---

### 5. OUTLIER_DETECTION_STRATEGY.md
**Location**: `software/homeamp-config-manager/`  
**Purpose**: Outlier detection strategy for config drift  
**Likely Contents**:
- Statistical outlier detection
- Threshold definitions
- Confidence scoring

---

## software/homeamp-config-manager/deployment/ (2 files)

### 1. deployment/CONNECTION_DETAILS.md
**Location**: `software/homeamp-config-manager/deployment/`  
**Purpose**: Connection details for servers  
**Likely Contents**:
- Server IPs, hostnames
- SSH connection strings
- Credentials (hopefully encrypted/referenced)
- Port mappings

---

### 2. deployment/MINIO_PUBLIC_CONFIG.md
**Location**: `software/homeamp-config-manager/deployment/`  
**Purpose**: MinIO configuration  
**Likely Contents**:
- MinIO endpoint
- Bucket names
- Public access policies
- Connection examples

---

## Deployment Scripts (2 files)

### 1. deployment/production-hotfix.sh
**Location**: `software/homeamp-config-manager/deployment/`  
**Purpose**: Production hotfix script (version 1)  
**Status**: Superseded by v2

---

### 2. deployment/production-hotfix-v2.sh
**Location**: `software/homeamp-config-manager/deployment/`  
**Purpose**: Production hotfix script (version 2)  
**Contents** (known from analysis):
```bash
# Fix 1: drift_detector.py line 203 isinstance check
# Fix 2: config_parser.py UTF-8-sig encoding
# Fix 3: config_parser.py IP address parsing
# Fix 4: agent/service.py duplicate DriftDetector init
```

---

## Analysis Directories (4 - MOSTLY EMPTY)

### 1. analysis/database_analysis/
**Status**: EMPTY  
**Purpose**: Database analysis outputs (intended but not created yet)

---

### 2. analysis/plugin_analysis/
**Status**: EMPTY  
**Purpose**: Plugin analysis outputs (intended but not created yet)

---

### 3. analysis/server_summaries/
**Status**: EMPTY  
**Purpose**: Server summary reports (intended but not created yet)

---

### 4. analysis/web_services/
**Status**: EMPTY  
**Purpose**: Web services analysis (intended but not created yet)

---

## data/baselines/ Structure

### data/baselines/plugin_definitions/
**Location**: `data/baselines/plugin_definitions/`  
**Purpose**: Baseline plugin definitions  
**Subdirectories**:
- `challenges/` - Challenge plugin configs
- `jobs/` - Jobs plugin configs
- `mmo/` - MMO plugin configs
- `quests/` - Quest plugin configs

**Status**: Likely contains baseline YAML/JSON for specific plugin categories

---

## Snapshot Archives (ZIPs)

### 1. 11octSNAPSHOTovh.zip
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: OVH server snapshot from October 11, 2025  
**Contents**: Archived OVH server configs  
**Size**: Unknown (check file size)

---

### 2. HETZNER_amp_config_snapshot.zip
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Hetzner server snapshot  
**Contents**: Archived Hetzner server configs  
**Size**: Unknown

---

### 3. software.zip
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Archived software directory  
**Status**: Redundant with software/ directory?

---

## Unzipped Snapshot Directories

### 1. 11octSNAPSHOTovh/
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Unzipped OVH snapshot  
**Structure**: `/home/amp/` directory tree

---

### 2. HETZNER_amp_config_snapshot/
**Location**: `e:\homeamp.ampdata\`  
**Purpose**: Unzipped Hetzner snapshot  
**Subdirectory**: `amp_config_snapshot/`  
**Contents**: ADS01, BIG01, CAR01, DEV01, EVO01, MIN01, PRI01, ROY01, SMP101, SUNK01, TOW01

---

## Scripts Directory

### scripts/
**Location**: `e:\homeamp.ampdata\scripts\`  
**Contents**: `plugin_configurations_complete_standardized.md.bak` (backup file)  
**Purpose**: Script storage (mostly empty?)

---

## Utility Scripts (Root Level)

### 1. analyze_joblistings.py
**Purpose**: Analyze job listings (likely for ExcellentJobs/JobListings plugin)

---

### 2. analyze_standardization_needs.py
**Purpose**: Analyze what configs need standardization

---

### 3. create_enhanced_version_management.py
**Purpose**: Enhanced version management system  
**Status**: Appears in both root and utildata/

---

### 4. extract_missing_configs.py
**Purpose**: Extract missing plugin configurations

---

### 5. fix_drift_detector.py
**Purpose**: Fix drift detector bugs  
**Likely**: Implements fixes from production-hotfix-v2.sh

---

### 6. pdf_reader.py
**Purpose**: PDF reading utility (for what?)

---

### 7. remove_non_english_langs.py
**Purpose**: Remove non-English language files from plugin configs  
**Status**: Currently open in editor

---

### 8. scan_codebase.py
**Purpose**: AST-based codebase scanner  
**Created**: This session  
**Output**: WIP_PLAN/codebase_structure.json

---

## software/homeamp-config-manager/ReturnedData/

### archivesmp-complete-backup-20251104-133804/
**Location**: `software/homeamp-config-manager/ReturnedData/`  
**Purpose**: Complete backup from production (Nov 4, 2025)  
**Contents**: Unknown (likely contains systemd service files, configs, etc.)  
**Importance**: Contains production deployment artifacts

---

## Configuration Files

### 1. pyrightconfig.json
**Location**: `software/homeamp-config-manager/`  
**Purpose**: Pyright type checker configuration  
**Format**: JSON  
**Contents**: Python static type checking settings

---

### 2. .vscode/
**Location**: Multiple (root and software/)  
**Purpose**: VS Code workspace settings  
**Contents**: Editor configuration, launch configs, extensions

---

## Markdown File Count Breakdown

**By Category**:
- Root documentation: 13 files
- WIP_PLAN: 5 files
- Software project docs: 5 files
- Deployment docs: 2 files
- Plugin universal configs: 57 files
- GitHub templates: 1 file
- **Total Primary Docs**: ~83 markdown files

**Plus**:
- Backup/snapshot readme files (unknown count)
- ReturnedData documentation (unknown count)

---

## Documentation Status Assessment

### ✅ Complete/Current:
- WIP_PLAN methodology documents (just created)
- Codebase inventory (just completed - 1,118 lines)
- Production hotfix scripts (documented bugs)
- Plugin universal configs (57 plugins)

### ⚠️ Needs Review:
- README.md - May need updating with current state
- PROJECT_GOALS.md - Verify against current scope
- PLUGIN_REGISTRY.md - Verify plugin sources current
- handover.md - Update for current state

### ❓ Unknown/Legacy:
- YUNOHOST_CONFIG.md - Is this still relevant?
- ArchiveSMP_MASTER_WITH_VIEWS.xlsx - Not used in code
- Plugin_*.xlsx (3 files) - Not used in code
- analysis/ directories (empty - placeholders?)

### ❌ Missing (Likely Needed):
- **requirements.txt** - Python dependencies
- **Installation guide** - How to deploy
- **Operator manual** - How to run/maintain
- **Troubleshooting guide** - Common issues
- **API documentation** - Web API endpoint reference
- **Agent configuration guide** - agent.yaml documentation
- **Excel template documentation** - How to maintain Excel files
- **Backup/restore procedures** - Disaster recovery

---

## Documentation Dependencies

**Documents that depend on code state**:
1. Codebase inventory (03_CODEBASE_INVENTORY.md) → Depends on src/ files
2. Bug analysis docs → Depend on actual bugs in code
3. Architecture docs → Depend on actual architecture

**Documents that code depends on**:
1. Plugin universal configs (*.md) → Parsed by core/data_loader.py
2. Excel files → Read by core/excel_reader.py
3. Connection details → Used by deployment scripts

---

## Documentation Quality Issues

### Duplicate/Redundant:
- `create_enhanced_version_management.py` (appears twice: root + utildata/)
- `output.txt` and `output2.txt` (raw dumps, not documentation)
- Zipped + unzipped snapshot directories

### Orphaned/Unclear:
- `pdf_reader.py` - Purpose unclear
- `analyze_joblistings.py` - Specific to one plugin?
- Empty analysis/ directories - Placeholders or abandoned?

### Potential Security Issues:
- `deployment/CONNECTION_DETAILS.md` - May contain credentials
- Excel files - May contain sensitive server data
- Snapshot directories - Contain production configs

---

## Recommended Documentation Actions

### Priority 1 (Critical for deployment):
1. ✅ Create requirements.txt from codebase imports
2. ✅ Write installation guide (install.sh + manual steps)
3. ✅ Document agent.yaml configuration format
4. ✅ Document web API endpoints

### Priority 2 (Important for operations):
5. Write operator manual (start/stop/monitor services)
6. Write troubleshooting guide (common errors + fixes)
7. Document Excel file schemas
8. Document MinIO bucket structure

### Priority 3 (Nice to have):
9. Update README.md with current state
10. Archive legacy Excel files not used by code
11. Clean up empty analysis/ directories or populate them
12. Consolidate duplicate files

---

## Documentation Search Optimization

**Key Search Terms** (for grep/semantic search):
- "production" - 13+ docs
- "deployment" - 10+ docs
- "plugin" - 60+ docs
- "config" - 100+ docs
- "server" - 100+ docs
- "baseline" - 20+ docs
- "drift" - 10+ docs
- "hotfix" - 2 docs

---

*Documentation inventory complete. Identified 83+ primary markdown files, 5 analysis documents, 2 deployment scripts, and 57 plugin config templates.*
