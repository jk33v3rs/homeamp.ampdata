# FUZZY CONCEPTS - Pass 1: Codebase Surface Scan

## INSTRUCTIONS FOR THIS FILE
- Record first impressions without deep analysis
- Note contradictions as subsequent-pass concepts
- Use tags: <!:"N"> for order, <VeryLikely/SomewhatLikely/Unlikely/Contradicts> for confidence
- NO resolution of conflicts in this pass
- Preserve context window for rapid scanning

---

## Meta: What This Codebase Is

- Central config management system for Minecraft server network
(Disambiguation: Not the Minecraft servers themselves, manages their configs)

- Distributed architecture: agent + web API + MinIO storage
(Disambiguation: Agent runs on each physical server, web API runs on one hosting server)

- <Subsequent> <!:"2"> <Contradicts>: May not be distributed, may be centralized on Hetzner only
(Evidence: No evidence of OVH deployment, production-hotfix only mentions Hetzner services)

---

## Physical Topology

- Two physical Debian servers: Hetzner (135.181.212.169), OVH (37.187.143.41)
(Disambiguation: These are bare metal servers, not VMs, not Docker containers)

- Hetzner is hosting server with MinIO, MariaDB, Redis, Web API on ports 3800, 3369, 6379, 8000
(Disambiguation: These are infrastructure services, not Minecraft)

- <Subsequent> <!:"2"> <VeryLikely>: Hetzner has ~11 AMP instances running Minecraft servers
(Evidence: CONNECTION_DETAILS.md says "~11 game servers", utildata/HETZNER has 11 folders)

- <Subsequent> <!:"3"> <SomewhatLikely>: OVH has 9-11 AMP instances
(Evidence: CONNECTION_DETAILS.md says "~9-11", utildata/OVH has 12 folders but some may be inactive)

- AMP Panel runs on both servers at port 8080
(Disambiguation: AMP = Application Management Panel, not the Minecraft servers it manages)

---

## Code Location and Airgap

- Development environment: e:\homeamp.ampdata\ on Windows PC
(Disambiguation: This is where human and AI work together)

- Production installation: /opt/archivesmp-config-manager/ on Debian
(Disambiguation: On Hetzner server, maybe not on OVH yet)

- AMP instances location: /home/amp/.ampdata/instances/ on Debian
(Disambiguation: Each subfolder is one Minecraft server instance)

- AI is airgapped from production
(Disambiguation: Cannot SSH, cannot SFTP, cannot directly modify production files)

- <Subsequent> <!:"2"> <VeryLikely>: Human has SSH and sudo access to both servers
(Evidence: User said "you the developer" and deployment instructions assume SSH)

---

## Services and Systemd

- homeamp-agent.service: Background agent discovering instances, checking drift
(Disambiguation: One per physical server, not per Minecraft instance)

- archivesmp-webapi.service: Web API with FastAPI, uvicorn, 4 workers, port 8000
(Disambiguation: Serves HTTP API and web UI)

- <Subsequent> <!:"2"> <Contradicts>: Service files found in ReturnedData backup dated 2025-11-04
(Evidence: ReturnedData/archivesmp-complete-backup-20251104-133804/)

- <Subsequent> <!:"3"> <Unknown>: Are these services currently running on Hetzner?
(Evidence: No live status, only backup files)

- <Subsequent> <!:"4"> <Unknown>: Are these services deployed to OVH?
(Evidence: No evidence either way)

---

## Known Bugs and Hotfixes

- production-hotfix-v2.sh exists with 4 bug fixes
(Disambiguation: Script to apply fixes to running production code)

- Bug 1: drift_detector.py crashes with list/dict type error
(Disambiguation: Missing isinstance() check before calling .get())

- Bug 2: config_parser.py has UTF-8 BOM handling issue
(Disambiguation: Should use 'utf-8-sig' encoding)

- Bug 3: config_parser.py parses IP addresses as floats
(Disambiguation: "0.0.0.0" becomes float, should stay string)

- Bug 4: agent/service.py has duplicate drift_detector initialization
(Disambiguation: Initialized twice, causes issues)

- <Subsequent> <!:"2"> <Unknown>: Are these bugs fixed in current src/ code?
(Evidence: Hotfix script exists, but haven't verified src/ has fixes applied)

- <Subsequent> <!:"3"> <Unknown>: Was production-hotfix-v2.sh deployed to Hetzner?
(Evidence: Todo list shows "[-] Deploy hotfix + test fixes" = partial/in-progress)

---

## File Structure - Source Code

- src/web/api.py: FastAPI app, 939 lines, many endpoints
(Disambiguation: Main web API implementation)

- src/web/models.py: Pydantic models for API
(Disambiguation: Data validation, deviation parsing)

- src/agent/service.py: Agent main loop, 399 lines
(Disambiguation: Discovers instances, polls for changes, applies configs)

- src/analyzers/drift_detector.py: Drift detection, 569 lines
(Disambiguation: Compares current configs to baseline)

- src/updaters/plugin_checker.py: Plugin update checking, 444 lines
(Disambiguation: GitHub/Spigot/Hangar API integration)

- src/updaters/bedrock_updater.py: Updates Bedrock edition plugins
(Disambiguation: Separate from Java edition)

- src/core/settings.py: Settings management, 489 lines
(Disambiguation: Centralized config loading)

- src/core/config_parser.py: Parse YAML/JSON/properties configs
(Disambiguation: Has bugs per hotfix script)

- src/core/excel_reader.py: Read Master_Variable_Configurations.xlsx
(Disambiguation: Server-specific variables)

- src/amp_integration/amp_client.py: AMP API client
(Disambiguation: Start/stop instances, file operations)

- <Subsequent> <!:"2"> <VeryLikely>: 104 total Python files in src/
(Evidence: file_search returned "104 total results")

---

## File Structure - Data

- data/baselines/universal_configs/: Plugin configs as JSON
(Disambiguation: Was utildata/universal_configs_analysis.json, now in data/)

- data/baselines/plugin_definitions/: Native YAML/JSON plugin definition files
(Disambiguation: Just extracted today, bulk definitions like Jobs jobs/, EliteMobs bosses/)

- utildata/HETZNER/: Snapshot of Hetzner configs
(Disambiguation: Archive from past, not live data)

- utildata/OVH/: Snapshot of OVH configs
(Disambiguation: Archive from past, not live data)

- ReturnedData/: Backup from 2025-11-04
(Disambiguation: Production backup, may show what was deployed then)

---

## Dependencies - External Packages

- requests: Used in plugin_checker.py, amp_client.py, bedrock_updater.py
(Disambiguation: HTTP client for API calls)

- fastapi: Used in web/api.py
(Disambiguation: Web framework)

- pydantic: Used in web/api.py, web/models.py
(Disambiguation: Data validation)

- <Subsequent> <!:"2"> <Unknown>: Is PyYAML used?
(Evidence: Config files are YAML, likely imported somewhere)

- <Subsequent> <!:"3"> <Unknown>: Is minio package used?
(Evidence: CloudStorage class mentioned, probably needs minio client)

- <Subsequent> <!:"4"> <Unknown>: Is openpyxl used?
(Evidence: excel_reader.py exists, needs Excel library)

- <Subsequent> <!:"5"> <Blocker>: No requirements.txt file exists
(Evidence: file_search for requirements.txt returned "No files found")

---

## Dependencies - External Services

- MinIO: Object storage at 135.181.212.169:3800
(Disambiguation: S3-compatible, stores change requests and results)

- MariaDB: Database at 135.181.212.169:3369
(Disambiguation: Stores persistent data, asmp_SQL database)

- Redis: Job queue at 135.181.212.169:6379
(Disambiguation: Coordinates work between services)

- AMP API: Management at :8080 on both servers
(Disambiguation: Control Minecraft instances)

- <Subsequent> <!:"2"> <Unknown>: Are credentials configured anywhere?
(Evidence: CONNECTION_DETAILS.md mentions "<from environment>" for passwords)

---

## Plugin Update CI/CD

- plugin_checker.py has methods for: check_github_release(), check_spigot_resource(), check_hangar()
(Disambiguation: Three different plugin distribution platforms)

- GitHub API: /repos/{owner}/{repo}/releases/latest
(Disambiguation: Rate limited: 60/hr without token, 5000/hr with token)

- SpigotMC API: /legacy/update.php?resource={id}
(Disambiguation: Returns version string only, no download URL)

- Hangar API: /v1/projects/{slug}/versions
(Disambiguation: Paper plugin repository)

- <Subsequent> <!:"2"> <Blocker>: No plugin_api_endpoints.yaml file exists
(Evidence: Code creates default if missing, but no evidence it exists)

- <Subsequent> <!:"3"> <Blocker>: No plugin registry mapping 89 plugins to sources
(Evidence: Default config in code only has ~20 plugins)

- <Subsequent> <!:"4"> <Unknown>: Where are GitHub API tokens stored?
(Evidence: No evidence of token configuration)

---

## Baseline Configs - Universal vs Variable

- 82 plugins have universal configs (should be identical everywhere)
(Disambiguation: After extracting definitions and removing locales)

- 23 plugins have variable configs (intentional differences per server/instance)
(Disambiguation: Server names, IPs, passwords, intentional cluster variations)

- Jobs: 2,641 settings in universal config, 2,250 are job definitions now extracted
(Disambiguation: Just moved to plugin_definitions/jobs/jobs/)

- HuskSync: 4 cluster types (DEVnet, SMPnet, SMPnet Limited, Hardcore) - INTENTIONAL variation
(Disambiguation: NOT drift, NOT bugs, designed to be different)

- <Subsequent> <!:"2"> <Unknown>: Does drift detector know about intentional variations?
(Evidence: Need to check if it has allowlist for HuskSync clusters)

---

## Temporal States - What Happened When

- 2025-11-04: Backup created (ReturnedData folder)
(Disambiguation: Snapshot of production state 6 days ago)

- 2025-11-04 or earlier: Bugs discovered, production-hotfix-v2.sh created
(Disambiguation: Hotfix script creation date unknown)

- 2025-11-10 (today): Plugin definitions extracted, locale cleanup completed
(Disambiguation: This is current work, just finished)

- <Subsequent> <!:"2"> <Unknown>: When was last deployment to Hetzner?
(Evidence: No deployment logs in workspace)

- <Subsequent> <!:"3"> <Unknown>: Has OVH ever had any deployment?
(Evidence: No evidence either way)

---

## Installation and Deployment

- <Missing> <!:"1"> <Blocker>: No install.sh script exists
(Evidence: file_search found no install.sh in deployment/)

- <Missing> <!:"2"> <Blocker>: No systemd service files in deployment/
(Evidence: file_search found services only in ReturnedData backup)

- production-hotfix-v2.sh: Patches existing installation
(Disambiguation: Assumes installation already exists at /opt/archivesmp-config-manager/)

- <Subsequent> <!:"3"> <Unknown>: How was initial installation done?
(Evidence: No install script, no docs describing process)

---

## Web UI

- src/web/static/: Frontend files location
(Disambiguation: HTML/JS/CSS for web interface)

- <Subsequent> <!:"2"> <Unknown>: Does src/web/static/ directory exist?
(Evidence: api.py has try/except for mounting static files, suggests might not exist)

- FastAPI serves /docs automatically (Swagger UI)
(Disambiguation: Auto-generated API documentation)

- Endpoints exist for: deviations, server views, plugin views, drift reports
(Disambiguation: Read api.py to see ~15 endpoints defined)

- <Subsequent> <!:"3"> <SomewhatLikely>: Web UI filtering broken
(Evidence: Earlier context mentioned "server/instance views show all instances")

---

## Ambiguous Terms Needing Disambiguation

- "server" could mean:
  * Physical Debian box (Hetzner or OVH)
  * AMP instance (DEV01, SMP101, etc)
  * Minecraft server process
  * Web server (uvicorn)
  * Generic variable name in code

- "baseline" could mean:
  * Universal configs (data/baselines/universal_configs/)
  * DEV01 instance configs (used as template)
  * Expected state for drift detection
  * Plugin definition files (data/baselines/plugin_definitions/)

- "deployment" could mean:
  * Deploy config changes to instances
  * Deploy plugin updates
  * Deploy this software to Hetzner/OVH
  * Deploy new Minecraft server instance

- "config" could mean:
  * Plugin configuration files (.yml, .json, .properties)
  * System configuration (agent.yaml, settings.yaml)
  * AMP configuration (AMPConfig.conf)
  * Build configuration (pyrightconfig.json)

---

## Questions That Need Answering (Not Answered in This Pass)

- Are hotfixes applied to current src/ code?
- Is anything currently running on Hetzner?
- Is anything deployed to OVH?
- Does requirements.txt need to be created?
- Does install.sh need to be created?
- Where are credentials stored/configured?
- Does web UI actually work?
- Can we ship anything right now?

(These are for Pass 2: Resolution)
