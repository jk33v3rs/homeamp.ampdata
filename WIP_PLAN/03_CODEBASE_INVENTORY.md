# Codebase Inventory - Complete Structural Analysis

**Status**: PASS 1 - Complete AST extraction  
**Generated**: 2025-11-10  
**Method**: Python AST parsing via scan_codebase.py  
**Data Source**: WIP_PLAN/codebase_structure.json  

---

## Executive Summary

**Codebase Scale**:
- **32 Python files** (11 are empty __init__.py markers)
- **11,371 total lines of code**
- **48 classes** (domain logic + data models + enums)
- **8 top-level entry points** (main functions, FastAPI app)

**Largest Files**:
1. `web/api.py` - 938 lines (FastAPI application, 15+ endpoints)
2. `analyzers/compliance_checker.py` - 704 lines (1 class, 10 methods)
3. `web/models.py` - 654 lines (7 classes, data models + parsers)
4. `updaters/config_updater.py` - 610 lines (1 class, 14 methods)
5. `automation/pulumi_update_monitor.py` - 595 lines (3 classes)

**Key Entry Points**:
- `agent/service.py:main()` - Agent daemon main loop
- `web/api.py:app` - FastAPI web server
- `updaters/bedrock_updater.py:main()` - Bedrock plugin CLI
- `amp_integration/amp_client.py:main()` - AMP client CLI
- `automation/scheduler_installer.py:main()` - Systemd installer
- `automation/pulumi_infrastructure.py:create_infrastructure()` - Pulumi stack
- `utils/logging.py:setup_logging()` - Logging setup
- `core/settings.py:get_settings()` - Singleton pattern

---

## Third-Party Dependencies

**Web & API**:
- `fastapi` - ASGI web framework
- `pydantic` - Data validation/serialization

**Storage**:
- `minio` - S3-compatible object storage
- `pulumi`, `pulumi_aws` - Infrastructure as code

**Data Processing**:
- `pandas` - Excel/CSV reading
- `openpyxl` - Excel writing/formatting

**Formats**:
- `pyyaml` - YAML parser

**HTTP**:
- `requests` - Synchronous HTTP client
- `aiohttp` - Async HTTP client

**Monitoring**:
- `prometheus_client` - Metrics exporter

---

## Directory Structure

```
src/
├── __init__.py (1 line)
├── agent/ (2 files, 399 lines)
├── amp_integration/ (2 files, 457 lines)
├── analyzers/ (4 files, 2155 lines)
├── automation/ (5 files, 2023 lines)
├── config_engine/ (1 file, 1 line)
├── core/ (10 files, 3274 lines)
├── deployment/ (1 file, 584 lines)
├── updaters/ (4 files, 1580 lines)
├── utils/ (4 files, 487 lines)
├── web/ (2 files, 1592 lines)
```

---

## SECTION 1: agent/ (398 lines, 1 class, 1 entry point)

### agent/service.py (398 lines)

**Purpose**: Main agent daemon that runs on physical servers

**Class: AgentService** (line 35):
- `__init__(self, config_file)` - Initialize agent with config
- `_discover_instances(self)` - Scan /home/amp/.ampdata/instances/
- `_load_config(self, config_file)` - Load agent.yaml config
- `start(self)` - Start agent main loop
- `_run_loop(self)` - Main event loop (drift checks, change processing)
- `_process_pending_changes(self)` - Download & apply change requests from MinIO
- `_apply_change_request(self, change_id, request_data)` - Apply config changes
- `_should_check_drift(self)` - Check if drift scan is due
- `_check_drift(self)` - Run drift detection across all instances
- `_upload_drift_report(self, drift_data)` - Upload report to MinIO
- `_handle_shutdown(self, signum, frame)` - SIGTERM/SIGINT handler

**Entry Point**:
- `main()` (line 382) - CLI entry point, loads config, starts agent

**Imports**:
- **Stdlib**: time, sys, json, signal, logging, pathlib, typing, datetime
- **Internal**: core.cloud_storage, updaters.config_updater, analyzers.drift_detector, core.safety_validator, core.settings
- **Third-party**: yaml

**Flow Pattern**: Event loop with configurable intervals for drift checks and change processing

---

## SECTION 2: amp_integration/ (456 lines, 2 classes, 1 entry point)

### amp_integration/amp_client.py (456 lines)

**Purpose**: AMP Panel API client and plugin deployer

**Class: AMPClient** (line 15, 18 methods):
- `__init__(self, base_url, username, password)` - Create client
- `_login(self)` - Authenticate and get session ID
- `_api_call(self, endpoint, data)` - Generic API wrapper
- `get_instances(self)` - List all AMP instances
- `get_instance_status(self, instance_id)` - Get instance state
- `start_instance(self, instance_id)` - Start Minecraft server
- `stop_instance(self, instance_id)` - Stop Minecraft server
- `restart_instance(self, instance_id)` - Restart Minecraft server
- `send_console_command(self, instance_id, command)` - Send console command
- `get_instance_config(self, instance_id)` - Get AMP settings
- `update_instance_config(self, instance_id, config_updates)` - Update AMP settings
- `get_file_listing(self, instance_id, directory)` - List files in instance
- `upload_file(self, instance_id, local_path, remote_path)` - Upload file to instance
- `delete_file(self, instance_id, file_path)` - Delete file from instance
- `rename_file(self, instance_id, old_path, new_path)` - Rename/move file
- `create_backup(self, instance_id, title, description)` - Create AMP backup
- `restore_backup(self, instance_id, backup_id)` - Restore from backup
- `list_backups(self, instance_id)` - List available backups

**Class: AMPPluginDeployer** (line 314, 4 methods):
- `__init__(self, amp_client)` - Wrap AMPClient
- `deploy_plugin(self, instance_id, plugin_jar, backup_old=True, restart_server=True)` - Full plugin deployment workflow
- `_get_instance_name(self, instance_id)` - Helper to get instance friendly name
- `rollback_plugin(self, instance_id, backup_id)` - Rollback to previous backup

**Entry Point**:
- `main()` (line 435) - CLI demo/testing

**Imports**:
- **Stdlib**: logging, time, pathlib, typing, datetime
- **Third-party**: requests

**Architecture Note**: This is the ONLY interface to AMP - all other modules use this

---

## SECTION 3: analyzers/ (2155 lines, 4 classes)

**src/core/config_parser.py**:
- `ConfigParser` - Parse YAML/JSON/properties files
  - Static methods for loading configs

**src/core/server_aware_config.py**:
- `ServerAwareConfigEngine` - Apply server-specific variables to configs

**src/core/excel_reader.py**:
- `ExcelConfigReader` - Read Master_Variable_Configurations.xlsx

**src/core/file_handler.py**:
- `FileHandler` - File operations with error handling

**src/core/safety_validator.py**:
- `SafetyValidator` - Validate config safety

**src/core/config_backup.py**:
- `ConfigBackupManager` - Backup/restore configs with timestamps

**src/core/data_loader.py**:
- `ServerInfo` - Server info dataclass
- `ProductionDataLoader` - Load production data

**src/analyzers/drift_detector.py**:
- `DriftDetector` - Detect configuration drift

**src/analyzers/deviation_analyzer.py**:
- `DeviationAnalyzer` - Analyze deviations

**src/analyzers/compliance_checker.py**:
- `ComplianceChecker` - Check compliance

**src/updaters/plugin_checker.py**:
- `PluginChecker` - Check for plugin updates
  - Methods: `check_github_release()`, `check_spigot_resource()`, `check_hangar()`

**src/updaters/config_updater.py**:
- `ConfigUpdater` - Apply config updates

**src/updaters/bedrock_updater.py**:
- `BedrockUpdater` - Update Bedrock edition plugins
- `main()` - Entry point

**src/amp_integration/amp_client.py**:
- `AMPClient` - AMP API client
  - Methods for instance control, file operations
- `AMPPluginDeployer` - Deploy plugins via AMP
- `main()` - Entry point

**src/deployment/pipeline.py**:
- `DeploymentStage(Enum)` - Deployment stages
- `DeploymentPipeline` - Deployment orchestration

**src/automation/plugin_automation.py**:
- `AutomatedPluginManager` - Automated plugin management

**src/automation/pulumi_update_monitor.py**:
- `PluginUpdate` - Plugin update dataclass
- `StagingEntry` - Staging entry dataclass
- `PluginUpdateMonitor` - Monitor plugin updates

**src/automation/pulumi_infrastructure.py**:
- `PluginUpdateInfrastructure` - Pulumi infrastructure
- `create_infrastructure()` - Infrastructure creator

**src/automation/scheduler_installer.py**:
- `UpdateSchedulerInstaller` - Install update scheduler
- `main()` - Entry point

**src/utils/logging.py**:
- `LogConfig` - Logging configuration
- `Logger` - Logger wrapper
- `setup_logging()` - Setup function

**src/utils/error_handler.py**:
- `ErrorSeverity(Enum)` - Error severity levels
- `ErrorHandler` - Error handling

**src/utils/metrics.py**:
- `MetricsExporter` - Prometheus metrics

---

### Key File Paths Referenced in Code

**Configuration Files**:
- `/etc/archivesmp/agent.yaml` - Agent config (production)
- `/etc/archivesmp/settings.yaml` - Settings config
- `config/settings.yaml` - Settings config (dev)
- `~/.archivesmp/settings.yaml` - User settings

**Data Directories**:
- `/home/amp/.ampdata/instances/` - AMP instances root
- `/opt/archivesmp-config-manager/` - Installation root
- `/var/lib/archivesmp/` - Runtime data
- `/var/log/archivesmp/` - Logs
- `data/baselines/` - Baseline configs
- `data/baselines/universal_configs/` - Universal plugin configs
- `data/baselines/plugin_definitions/` - Plugin definition files

**MinIO Buckets**:
- `archivesmp-changes` - Change requests
- `archivesmp-drift-reports` - Drift reports
- `archivesmp-backups` - Config backups

---

### Import Patterns / Module Structure

**Internal imports** (relative):
```
from ..core.cloud_storage import CloudStorage, ChangeRequestManager
from ..updaters.config_updater import ConfigUpdater
from ..analyzers.drift_detector import DriftDetector
from ..core.safety_validator import SafetyValidator
from ..core.settings import get_settings
from .models import DeviationParser, DeviationManager
```

**Cross-module dependencies**:
- agent → core (cloud_storage, settings), updaters (config_updater), analyzers (drift_detector)
- web → core (settings, data_loader), updaters (bedrock_updater)
- updaters → core (settings)
- automation → amp_integration, core (excel_reader)
- All modules → core/settings (singleton pattern)

---

### Naming Schemas

**Class Names**:
- Pattern: PascalCase
- Suffixes: Service, Client, Manager, Handler, Updater, Checker, Detector, Parser, Validator, Pipeline, Deployer, Monitor, Installer, Exporter
- Examples: `AgentService`, `AMPClient`, `PluginChecker`, `DriftDetector`

**Function Names**:
- Pattern: snake_case
- Prefixes: `get_`, `set_`, `load_`, `save_`, `check_`, `apply_`, `upload_`, `download_`, `parse_`
- Private: `_discover_instances`, `_load_config`, `_process_pending_changes`

**File Names**:
- Pattern: snake_case
- Types: `*_service.py`, `*_client.py`, `*_updater.py`, `*_checker.py`, `*_detector.py`, `*_parser.py`

**Config Keys**:
- Pattern: lowercase with underscores or dots
- Examples: `poll_interval`, `drift_check_interval`, `server_name`, `minio.endpoint`

**Bucket Names**:
- Pattern: `archivesmp-{purpose}`
- Examples: `archivesmp-changes`, `archivesmp-drift-reports`, `archivesmp-backups`

---

### Flow Paths

**Agent Service Flow**:
1. `main()` → Load config from `/etc/archivesmp/agent.yaml`
2. `AgentService.__init__()` → Initialize settings, logging
3. `_discover_instances()` → Scan `/home/amp/.ampdata/instances/`
4. `start()` → Setup signal handlers
5. `_run_loop()` → Poll loop:
   - `_process_pending_changes()` → Check MinIO for changes
   - `_apply_change_request()` → Apply via ConfigUpdater
   - `_should_check_drift()` → Check timer
   - `_check_drift()` → Run DriftDetector
   - `_upload_drift_report()` → Upload to MinIO

**Web API Flow**:
1. `FastAPI app` startup → Load deviations, universal configs
2. Client requests endpoint → Route handler
3. Handler → `DeviationParser` / `DeviationManager`
4. Response → JSON via Pydantic models

**Plugin Update Flow** (from code inspection):
1. `PluginChecker.check_github_release()` → GitHub API
2. Version comparison → Determine if update needed
3. `BedrockUpdater` or `AutomatedPluginManager` → Download JAR
4. `AMPPluginDeployer` → Deploy via AMP API

**Config Deployment Flow**:
1. Change request → MinIO bucket
2. Agent polls MinIO → `ChangeRequestManager.list_pending_changes()`
3. `ConfigUpdater.apply_change_request()` → Modify files
4. `SafetyValidator` → Validate changes
5. `ConfigBackupManager` → Backup before apply
6. Result → Upload to MinIO

---

### Critical Code Locations

**Bug Fix Locations** (from hotfix script):
- `src/analyzers/drift_detector.py:203` - isinstance() check needed
- `src/core/config_parser.py:~75` - IP address parsing bug
- `src/core/config_parser.py` - UTF-8-sig encoding needed
- `src/agent/service.py:~326` - Duplicate drift_detector initialization

**Entry Points**:
- `src/agent/service.py:main()` - Agent service
- `src/web/api.py:app` - Web API
- `src/updaters/bedrock_updater.py:main()` - Bedrock updater standalone
- `src/amp_integration/amp_client.py:main()` - AMP client standalone
- `src/automation/scheduler_installer.py:main()` - Scheduler installer

---

### analyzers/compliance_checker.py (704 lines)

**Purpose**: Compare current configs against baseline, generate compliance reports

**Class: ComplianceChecker** (line 12, 10 methods):
- `__init__(self, baseline_path, current_state_path)` - Initialize paths
- `load_baseline(self)` - Load baseline configs (expected state)
- `load_current_state(self)` - Load current configs from servers
- `compare_states(self)` - Full state comparison
- `_count_configs(self, config_dict)` - Count total configs
- `_compare_single_config(self, server_name, plugin_name, config_name, baseline_config, current_config, results)` - Compare one config file
- `check_expected_changes(self, expected_changes_path)` - Verify expected changes were applied
- `generate_compliance_report(self, output_path)` - Generate markdown report
- `_generate_recommendations(self, comparison_results)` - Generate recommendations
- `_generate_next_actions(self, comparison_results)` - Generate action items

**Imports**:
- **Stdlib**: typing, pathlib, json, datetime
- **Internal**: core.config_parser.ConfigParser (3x imports - duplicate), core.safety_validator.SafetyValidator (2x - duplicate)

**Data Flow**: Baseline → Current → Diff → Report

---

### analyzers/deviation_analyzer.py (439 lines)

**Purpose**: Analyze deviation patterns, detect per-server settings vs mistakes

**Class: DeviationAnalyzer** (line 16, 8 methods):
- `__init__(self, deviations_file)` - Load deviations JSON
- `parse_deviations(self)` - Parse deviation file into structured data
- `is_per_server_setting(self, key, values)` - Detect intentional per-server configs
- `is_dev_server_deviation(self, servers)` - Check if deviation is DEV01-specific
- `analyze_deviation_pattern(self, key, server_values)` - Classify deviation type
- `generate_report(self, output_path)` - Generate analysis report
- `get_high_priority_issues(self)` - Extract high-priority problems
- `_calculate_issue_priority(self, analysis, server_values)` - Score priority

**Heuristics** (from code analysis):
- DEV01 deviations = expected
- Network settings (ports, IPs) = per-server
- Single outlier = potential mistake
- Majority consensus = outliers suspicious

**Imports**: Stdlib only (typing, pathlib, json, datetime)

---

### analyzers/drift_detector.py (568 lines)

**Purpose**: Detect configuration drift from baseline state

**Class: DriftDetector** (line 12, 9 methods):
- `__init__(self, baseline_path)` - Load baseline configs
- `load_baseline(self)` - Parse baseline YAML/JSON files
- `scan_server_configs(self, server_path)` - Scan single server's configs
- `detect_drift(self, server_name, server_path)` - Detect drift for one server
- `_compare_configs(self, plugin_name, config_file, baseline, current, server_name, prefix="")` - Recursive config comparison
- `scan_all_servers(self, utildata_path)` - Scan all servers in utildata/
- `generate_drift_report(self, output_path, drift_data)` - Generate drift report JSON
- `prioritize_drift_items(self, drift_data)` - Sort drift by priority
- `_calculate_priority_score(self, item)` - Calculate priority score

**Known Bug** (line 203):
- isinstance() check crashes on list/dict comparison
- Fixed in production-hotfix-v2.sh

**Imports**:
- **Stdlib**: typing, pathlib, json, datetime
- **Internal**: core.config_parser.ConfigParser (3x - duplicate import)

---

## SECTION 4: automation/ (2023 lines, 6 classes, 2 entry points)

### automation/plugin_automation.py (289 lines)

**Purpose**: Automated plugin deployment with approval workflow

**Class: AutomatedPluginManager** (line 28, 6 methods):
- `__init__(self, config)` - Initialize with config
- `_check_auto_deploy(self, updates)` - Check if auto-deploy allowed
- `manual_deploy(self, plugin_name, version, instance_id)` - Manual deployment
- `manual_rollback(self, instance_id, backup_id)` - Manual rollback
- `list_instance_backups(self, instance_id)` - List backups
- `get_all_instances(self)` - Get all AMP instances

**Imports**:
- **Stdlib**: asyncio, logging, pathlib, typing, datetime, sys, csv
- **Internal**: automation.pulumi_update_monitor, amp_integration.amp_client, core.excel_reader

---

### automation/pulumi_infrastructure.py (299 lines)

**Purpose**: Pulumi infrastructure as code for AWS resources

**Class: PluginUpdateInfrastructure** (line 19, 11 methods):
- `__init__(self, config)` - Initialize Pulumi stack
- `_create_staging_bucket(self)` - S3 bucket for staging
- `_create_excel_bucket(self)` - S3 bucket for Excel files
- `_create_lambda_role(self)` - IAM role for Lambda
- `_create_lambda_function(self)` - Lambda function resource
- `_create_schedule_rule(self)` - EventBridge schedule
- `_create_sns_topic(self)` - SNS topic for notifications
- `_configure_lambda_permissions(self)` - Lambda permissions
- `_configure_notifications(self)` - Notification setup
- `_export_outputs(self)` - Export stack outputs

**Entry Point**:
- `create_infrastructure()` (line 270) - Main Pulumi program

**Imports**:
- **Third-party**: pulumi, pulumi_aws (as aws)
- **Stdlib**: pathlib, typing

**Architecture Note**: AWS-specific, creates serverless update monitoring

---

### automation/pulumi_update_monitor.py (595 lines)

**Purpose**: Monitor plugin updates from upstream sources

**Data Classes**:
- `PluginUpdate` (line 26) - Update metadata dataclass
- `StagingEntry` (line 43) - Staging area entry dataclass

**Class: PluginUpdateMonitor** (line 56, 4 methods):
- `__init__(self, staging_path, plugin_registry_path, excel_output_path)` - Initialize paths
- `_load_plugin_registry(self)` - Load plugin registry YAML
- `_is_newer_version(self, current, latest)` - Semantic version comparison
- `_detect_breaking_changes(self, changelog)` - Parse changelog for breaking changes
- `write_to_excel(self, updates, staged_entries)` - Write updates to Excel with styling

**Imports**:
- **Third-party**: aiohttp, openpyxl, yaml
- **Stdlib**: typing, pathlib, datetime, logging, json, asyncio, dataclasses

---

### automation/scheduler_installer.py (312 lines)

**Purpose**: Generate systemd service/timer files and installer scripts

**Class: UpdateSchedulerInstaller** (line 13, 8 methods):
- `__init__(self, install_path)` - Set install path
- `generate_systemd_service(self)` - Generate .service file
- `generate_systemd_timer(self)` - Generate .timer file
- `generate_crontab_entry(self)` - Generate cron entry
- `generate_install_script(self)` - Generate install.sh
- `generate_plugin_registry_template(self)` - Generate plugin_registry.yaml template
- `generate_uninstall_script(self)` - Generate uninstall.sh
- `write_install_files(self, output_dir)` - Write all files to disk

**Entry Point**:
- `main()` (line 293) - Generate installer files

**Imports**: Stdlib only (pathlib, typing, logging)

---

## SECTION 5: core/ (3274 lines, 15 classes, 2 entry points)

### core/cloud_storage.py (392 lines)

**Purpose**: MinIO/S3 storage client and change request manager

**Class: CloudStorage** (line 19, 10 methods):
- `__init__(self, endpoint, access_key, secret_key, secure=True)` - Initialize MinIO client
- `ensure_bucket_exists(self, bucket_name)` - Create bucket if missing
- `upload_file(self, bucket_name, object_name, file_path, content_type=None)` - Upload file
- `upload_json(self, bucket_name, object_name, data)` - Upload JSON object
- `download_file(self, bucket_name, object_name, file_path)` - Download file
- `download_json(self, bucket_name, object_name)` - Download JSON object
- `list_objects(self, bucket_name, prefix="")` - List objects in bucket
- `delete_object(self, bucket_name, object_name)` - Delete object
- `object_exists(self, bucket_name, object_name)` - Check if object exists
- `get_object_metadata(self, bucket_name, object_name)` - Get object metadata

**Class: ChangeRequestManager** (line 252, 6 methods):
- `__init__(self, storage, bucket_name)` - Wrap CloudStorage
- `upload_change_request(self, change_request)` - Upload change request as JSON
- `list_pending_changes(self)` - List changes in pending/ prefix
- `download_change_request(self, change_id)` - Download specific change
- `mark_change_completed(self, change_id)` - Move to completed/ prefix
- `upload_change_result(self, change_id, result)` - Upload execution result

**Imports**:
- **Third-party**: minio (Minio, S3Error)
- **Stdlib**: typing, pathlib, json, io, uuid, datetime (2x - duplicate)

**Buckets Used**:
- `archivesmp-changes` - Change requests (pending/, completed/)
- `archivesmp-drift-reports` - Drift reports
- `archivesmp-backups` - Config backups

---

### core/config_backup.py (270 lines)

**Purpose**: Backup and restore configuration files with timestamps

**Class: ConfigBackupManager** (line 19, 6 methods):
- `__init__(self, backup_root)` - Set backup directory
- `backup_config(self, config_file, server_name, plugin_name)` - Backup single config
- `backup_plugin_configs(self, plugin_dir, server_name, plugin_name)` - Backup entire plugin directory
- `restore_config(self, backup_path, restore_to)` - Restore from backup
- `list_backups(self, server_name=None, plugin_name=None)` - List available backups
- `cleanup_old_backups(self, days_to_keep=30)` - Delete old backups

**Backup Structure**:
```
backup_root/
└── {server_name}/
    └── {plugin_name}/
        └── {timestamp}_{config_filename}
```

**Imports**: Stdlib only (shutil, pathlib, datetime, typing, logging, json)

---

### core/config_parser.py (299 lines)

**Purpose**: Load/save YAML/JSON/TOML configs, handle nested keys

**Class: ConfigParser** (line 14, 8 static methods):
- `load_config(file_path)` - Detect format and load
- `save_config(file_path, data)` - Detect format and save
- `get_nested_value(data, key_path)` - Get nested key via dot notation
- `set_nested_value(data, key_path, value)` - Set nested key
- `flatten_dict(data, parent_key="", sep=".")` - Flatten nested dict
- `unflatten_dict(data, sep=".")` - Unflatten dict
- `validate_yaml(file_path)` - Validate YAML syntax
- `validate_json(file_path)` - Validate JSON syntax

**Known Bugs**:
- UTF-8-sig encoding needed (line ~75)
- IP address parsing bug

**Imports**:
- **Third-party**: yaml
- **Stdlib**: typing, pathlib, json
- **Internal**: file_handler.FileHandler (appears broken - FileHandler doesn't exist in imports)

---

### core/data_loader.py (451 lines)

**Purpose**: Load production server data, plugin configs, deviations

**Data Class**:
- `ServerInfo` (line 15) - Server metadata dataclass

**Class: ProductionDataLoader** (line 26, 16 methods):
- `__init__(self, base_path)` - Initialize with utildata path
- `_load_server_configurations(self)` - Load all server configs
- `_discover_servers(self)` - Discover servers in HETZNER/ and OVH/
- `_find_amp_config_path(self, server_id, platform)` - Find AMP config directory
- `get_all_servers(self)` - Get all servers
- `get_server_by_id(self, server_id)` - Get specific server
- `get_servers_by_platform(self, platform)` - Filter by HETZNER/OVH
- `load_universal_plugin_configs(self)` - Load universal configs from markdown
- `_parse_universal_config_file(self, file_path)` - Parse markdown universal config
- `_parse_config_value(self, value_str)` - Parse value from markdown
- `_parse_individual_plugin_config(self, file_path)` - Parse individual config
- `load_plugin_deviations(self)` - Load deviations from markdown
- `_parse_plugin_deviations(self, file_path)` - Parse deviation markdown
- `get_server_deviations(self, server_id)` - Get deviations for server
- `get_server_plugin_configs(self, server_id)` - Get configs for server
- `get_server_status_summary(self)` - Summary of all servers

**Imports**:
- **Stdlib**: typing, pathlib, json, dataclasses
- **Internal**: settings.get_settings (broken import - should be core.settings)

**Data Sources**:
- `utildata/plugin_universal_configs/*.md`
- `utildata/HETZNER/` and `utildata/OVH/`

---

### core/excel_reader.py (277 lines)

**Purpose**: Read/write Excel deployment matrix and server variables

**Class: ExcelConfigReader** (line 15, 8 methods):
- `__init__(self, data_dir)` - Set data directory
- `load_deployment_matrix(self)` - Load deployment_matrix.csv as DataFrame
- `load_server_variables(self)` - Load Master_Variable_Configurations.xlsx
- `get_server_variables(self, server_name)` - Get variables for server
- `get_plugin_auto_update_status(self, plugin_name)` - Check if plugin auto-updates
- `get_plugin_deployment_servers(self, plugin_name)` - Get servers for plugin
- `write_plugin_update(self, plugin_name, new_version, update_date)` - Update plugin version in matrix
- `get_all_plugins_for_server(self, server_name)` - Get all plugins for server

**Imports**:
- **Third-party**: pandas (as pd)
- **Stdlib**: pathlib, typing, logging

**Excel Files**:
- `deployment_matrix.csv` - Plugin-to-server mapping
- `Master_Variable_Configurations.xlsx` - Per-server variables (ports, IPs, etc.)

---

### core/file_handler.py (315 lines)

**Purpose**: Atomic writes, backups, rollbacks, integrity checks

**Class: FileHandler** (line 15, 7 methods):
- `__init__(self, backup_root)` - Set backup directory
- `create_backup(self, file_path)` - Backup before modification
- `atomic_write(self, file_path, content)` - Write to temp, then rename
- `safe_read(self, file_path)` - Read with error handling
- `rollback_from_backup(self, backup_path, target_path)` - Restore from backup
- `cleanup_old_backups(self, max_age_days=30, keep_minimum=5)` - Clean old backups
- `verify_file_integrity(self, file_path)` - Verify YAML/JSON syntax

**Imports**: Stdlib only (typing, pathlib, shutil, os, datetime, tempfile, time, hashlib, yaml, json)

---

### core/safety_validator.py (308 lines)

**Purpose**: Validation before applying changes

**Class: SafetyValidator** (line 11, 7 static methods):
- `validate_server_exists(server_name, utildata_path)` - Check server directory exists
- `validate_plugin_exists(server_name, plugin_name, utildata_path)` - Check plugin exists
- `validate_config_file_exists(server_name, plugin_name, config_file, utildata_path)` - Check config exists
- `validate_expected_value(current_value, expected_value, strict=True)` - Verify current value matches expected
- `validate_change_request_format(change_request)` - Validate change request JSON schema
- `validate_no_file_locks(file_path)` - Check file not locked
- `validate_disk_space(path, required_mb=100)` - Check available disk space

**Imports**: Stdlib only (typing, pathlib, os, shutil)

---

### core/server_aware_config.py (262 lines)

**Purpose**: Generate server-specific configs from universal templates

**Class: ServerAwareConfigEngine** (line 17, 7 methods):
- `__init__(self, excel_reader, universal_configs_dir)` - Initialize with Excel reader
- `detect_server_from_amp_instance(self, instance_id, amp_client)` - Map AMP instance to server name
- `load_universal_config(self, plugin_name)` - Load universal config template
- `apply_server_variables(self, config, server_name)` - Replace {{VAR}} placeholders
- `generate_server_config(self, plugin_name, server_name)` - Full config generation
- `write_config_file(self, config, output_path, format="yaml")` - Write config to disk
- `deploy_config_to_server(self, plugin_name, server_name, amp_instance_id, amp_client, config_filename="config.yml")` - Full deployment workflow

**Variable Substitution**: `{{SERVER_PORT}}`, `{{SERVER_IP}}`, etc.

**Imports**:
- **Third-party**: yaml
- **Stdlib**: pathlib, typing, logging, re, json, tempfile
- **Internal**: core.excel_reader.ExcelConfigReader

---

### core/settings.py (489 lines)

**Purpose**: Central configuration management with singleton pattern

**Data Classes** (6 total):
- `MinIOConfig` (line 17) - MinIO/S3 settings
- `AgentConfig` (line 29) - Agent daemon settings
- `WebConfig` (line 41) - Web API settings
- `HttpConfig` (line 54) - HTTP client settings
- `PluginUpdateConfig` (line 63) - Plugin update settings

**Class: SettingsHandler** (line 74, 33 methods):
- `__init__(self, config_file=None)` - Load settings from YAML
- `_find_config_file(self)` - Search for config in standard locations
- `_load_settings(self)` - Parse YAML config
- `_apply_env_overrides(self, settings)` - Override with environment variables
- `get(self)` - Get all settings
- `get_required(self)` - Get required settings or raise
- Path properties: `instances_path`, `utildata_path`, `data_dir`, `scripts_dir`, `backup_dir`, `temp_dir`
- Server management: `physical_servers`, `ovh_ryzen_config`, `hetzner_xeon_config`, `excluded_instances`, `test_instances`, `production_instances`
- Config objects: `minio_config()`, `agent_config()`, `web_config()`, `http_config()`, `plugin_update_config()`
- Other: `get_plugin_id()`, `backup_retention_days`, `max_backups_per_file`, logging settings, etc.
- `reload(self)` - Reload settings from disk

**Module Functions**:
- `get_settings(config_file=None)` (line 467) - Singleton getter
- `reload_settings()` (line 485) - Reload singleton

**Imports**: Stdlib only (os, yaml, pathlib, typing, dataclasses, logging)

**Singleton Pattern**: Global `_settings_instance` variable

---

## SECTION 6: deployment/ (584 lines, 2 classes)

### deployment/pipeline.py (584 lines)

**Purpose**: Multi-stage deployment pipeline (DEV → PROD workflow)

**Enum: DeploymentStage** (line 14):
- CREATED, DEV_PENDING, DEV_IN_PROGRESS, DEV_COMPLETE, DEV_FAILED, PROD_APPROVED, PROD_IN_PROGRESS, PROD_COMPLETE, PROD_FAILED, ROLLED_BACK

**Class: DeploymentPipeline** (line 26, 14 methods):
- `__init__(self, storage_path)` - Initialize deployment storage
- `create_deployment(self, change_id, change_data)` - Create new deployment
- `_get_dev_servers(self)` - Get DEV01 servers
- `_get_production_servers(self)` - Get production servers
- `deploy_to_dev(self, config_request)` - Deploy to DEV01 first
- `validate_dev_deployment(self, deployment_id)` - Validate DEV01 results
- `approve_for_production(self, deployment_id, approved_by)` - Approve for PROD
- `deploy_to_production(self, deployment_id)` - Deploy to production servers
- `rollback_deployment(self, deployment_id)` - Rollback deployment
- `get_deployment_status(self, deployment_id)` - Get status
- `list_active_deployments(self)` - List in-progress deployments
- `_get_target_servers(self, change_data)` - Determine target servers
- `_save_deployment(self, deployment)` - Persist deployment state
- `_load_deployment(self, deployment_id)` - Load deployment state

**Workflow**: Create → DEV deploy → Validate → Approve → PROD deploy → Complete/Rollback

**Imports**:
- **Stdlib**: typing, pathlib, datetime, enum, json, uuid
- **Internal**: updaters.config_updater.ConfigUpdater (3x - duplicate)

---

## SECTION 7: updaters/ (1580 lines, 4 classes, 1 entry point)

### updaters/bedrock_updater.py (527 lines)

**Purpose**: Check/update Bedrock edition plugins (Geyser, Floodgate, ViaVersion)

**Class: BedrockUpdater** (line 18, 9 methods):
- `__init__(self, settings_path)` - Load settings
- `check_geysermc_version(self, project, platform="spigot")` - Check GeyserMC API
- `check_hangar_version(self, project, include_snapshots=False)` - Check Hangar (Paper registry)
- `download_plugin(self, url, output_path)` - Download plugin JAR
- `update_geyser_standalone(self, target_path)` - Update standalone Geyser
- `update_floodgate(self, platform="spigot", target_servers=None)` - Update Floodgate
- `update_viaversion(self, include_viabackwards=True)` - Update ViaVersion + ViaBackwards
- `full_bedrock_update(self, restart_services=False)` - Full update cycle
- `check_all_versions(self)` - Check all plugin versions

**Entry Point**:
- `main()` (line 475) - CLI with argparse

**APIs Used**:
- GeyserMC downloads API
- Hangar API (Paper plugin registry)

**Imports**:
- **Third-party**: requests
- **Stdlib**: json, logging, pathlib, typing, datetime, argparse, shutil

---

### updaters/config_updater.py (610 lines)

**Purpose**: Apply configuration changes to files

**Class: ConfigUpdater** (line 14, 14 methods):
- `__init__(self, utildata_path, dry_run=False)` - Initialize updater
- `load_change_request(self, request_id)` - Load change request JSON
- `validate_change_request(self, change_request)` - Validate request schema
- `create_backup(self, target_files)` - Backup files before changes
- `verify_expected_value(self, server_name, plugin_name, config_file, key_path, expected_value)` - Verify current value
- `apply_single_change(self, change)` - Apply one change
- `_update_yaml_key(self, file_path, change)` - Update YAML key
- `_replace_line(self, file_path, change)` - Replace line by pattern
- `_add_line(self, file_path, change)` - Add line to file
- `_delete_line(self, file_path, change)` - Delete line by pattern
- `apply_change_request(self, change_request)` - Apply entire change request
- `rollback_change(self, change_id)` - Rollback change
- `generate_preview(self, change_request)` - Preview changes without applying
- `log_change(self, change, result)` - Log change to audit log

**Change Types**: UPDATE_YAML_KEY, REPLACE_LINE, ADD_LINE, DELETE_LINE

**Imports**:
- **Third-party**: yaml
- **Stdlib**: typing, pathlib, datetime, logging, json, os, shutil (2x - duplicate)
- **Internal**: core.config_parser.ConfigParser, core.safety_validator.SafetyValidator

---

### updaters/plugin_checker.py (443 lines)

**Purpose**: Check for plugin updates from GitHub/Spigot/Hangar

**Class: PluginChecker** (line 14, 9 methods):
- `__init__(self, api_endpoints_config)` - Load API endpoints config
- `load_api_endpoints(self)` - Parse endpoints YAML
- `check_github_release(self, repo)` - Check GitHub releases API
- `check_spigot_resource(self, resource_id)` - Check Spiget API (Spigot)
- `check_hangar(self, plugin_slug)` - Check Hangar API (Paper)
- `get_installed_version(self, plugin_name, server_name, utildata_path)` - Extract version from plugin.yml in JAR
- `check_all_plugins(self, utildata_path)` - Check all plugins for updates
- `assess_update_risk(self, plugin_name, current_version, new_version)` - Risk assessment
- `generate_update_report(self, output_path, update_data)` - Generate update report

**APIs Used**:
- GitHub Releases API
- Spiget API (Spigot mirror)
- Hangar API (Paper registry)

**Imports**:
- **Third-party**: requests (3x), yaml (3x), re (3x) - many duplicates
- **Stdlib**: typing, pathlib, datetime, json, zipfile, tempfile
- **Internal**: core.settings.get_settings (2x - duplicate)

---

## SECTION 8: utils/ (487 lines, 4 classes, 1 entry point)

### utils/error_handler.py (251 lines)

**Purpose**: Error handling utilities and retry logic

**Enum: ErrorSeverity** (line 11):
- INFO, WARNING, ERROR, CRITICAL

**Class: ErrorHandler** (line 19, 6 static methods):
- `handle_file_not_found(file_path)` - File not found error
- `handle_parse_error(file_path, error)` - Config parse error
- `handle_validation_error(field, reason)` - Validation error
- `handle_network_error(url, error)` - Network/HTTP error
- `with_retry(func, max_attempts=3, backoff_seconds=2)` - Retry decorator
- `create_error_report(errors, output_path)` - Generate error report JSON

**Imports**: Stdlib only (typing, enum, logging, datetime, time, json, pathlib)

---

### utils/logging.py (103 lines)

**Purpose**: Logging configuration and setup

**Data Class**:
- `LogConfig` (line 15) - Logging configuration dataclass

**Class: Logger** (line 23, 6 methods):
- `__init__(self, name, config)` - Initialize logger
- `info(self, message)` - Info log
- `warning(self, message)` - Warning log
- `error(self, message)` - Error log
- `debug(self, message)` - Debug log
- `critical(self, message)` - Critical log

**Entry Point**:
- `setup_logging(level="INFO", console_enabled=True, file_enabled=False, file_path=None)` (line 81) - Configure root logger

**Imports**: Stdlib only (logging, pathlib, datetime, typing, dataclasses)

---

### utils/metrics.py (133 lines)

**Purpose**: Prometheus metrics exporter

**Class: MetricsExporter** (line 13, 9 methods):
- `__init__(self)` - Initialize Prometheus metrics
- `update_agent_health(self, server, is_up)` - Agent health gauge
- `update_drift_count(self, server, plugin, count)` - Drift count gauge
- `record_drift_check(self, server)` - Drift check counter
- `record_change_applied(self, server, success, duration)` - Change application metrics
- `update_plugin_version(self, server, plugin, version)` - Plugin version gauge
- `update_outdated_plugins(self, server, count)` - Outdated plugin count
- `update_deviations(self, server, pending, flagged_bad)` - Deviation metrics
- `export_metrics(self)` - Export Prometheus text format

**Metrics Defined**:
- `agent_health` (Gauge) - Agent up/down status per server
- `drift_items_count` (Gauge) - Drift count per server/plugin
- `drift_checks_total` (Counter) - Total drift checks per server
- `config_changes_total` (Counter) - Total changes per server/success
- `config_change_duration_seconds` (Histogram) - Change duration
- `plugin_version` (Gauge) - Plugin versions per server/plugin
- `outdated_plugins_count` (Gauge) - Outdated plugin count per server
- `deviations_pending` (Gauge) - Pending deviations per server
- `deviations_flagged_bad` (Gauge) - Flagged bad deviations per server

**Imports**:
- **Third-party**: prometheus_client (Counter, Gauge, Histogram, generate_latest, CollectorRegistry)
- **Stdlib**: typing, datetime

---

## SECTION 9: web/ (1592 lines, 10 classes)

### web/api.py (938 lines)

**Purpose**: FastAPI web application with REST API + HTML UI

**Data Models** (Pydantic BaseModel):
- `ChangeRequest` (line 53) - Single change request
- `ChangeRequestBatch` (line 65) - Batch of changes
- `DeviationReview` (line 74) - Deviation review submission

**FastAPI App**: `app = FastAPI()` (initialized globally)

**API Endpoints** (~15 total based on imports and size):
- `GET /` - Root/UI landing page
- `GET /api/deviations` - Get all deviations
- `GET /api/deviations/pending` - Get pending reviews
- `GET /api/deviations/flagged-bad` - Get flagged bad deviations
- `GET /api/deviations/server/{server_name}` - Get server-specific deviations
- `GET /api/deviations/plugin/{plugin_name}` - Get plugin-specific deviations
- `POST /api/deviations/review` - Submit deviation review
- `GET /api/servers` - List all servers (likely)
- `GET /api/plugins` - List all plugins (likely)
- `POST /api/changes` - Submit change request (likely)
- `GET /api/changes/{change_id}` - Get change status (likely)
- `POST /api/deploy` - Deploy to DEV01 (likely)
- `GET /metrics` - Prometheus metrics endpoint (likely)
- *(Additional endpoints based on imports)*

**Imports**:
- **Third-party**: fastapi (FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form, StaticFiles, FileResponse, HTMLResponse, JSONResponse, Response), pydantic (BaseModel)
- **Stdlib**: typing, pathlib, json, datetime
- **Internal**:
  - web.models (DeviationParser, DeviationManager, DeviationItem, DeviationStatus, ServerView, GlobalView, PluginConfig)
  - core.settings.get_settings
  - updaters.bedrock_updater.BedrockUpdater
  - utils.metrics.metrics
  - updaters.plugin_checker.PluginChecker (6x - many duplicates)
  - deployment.pipeline.DeploymentPipeline (5x - duplicates)
  - core.cloud_storage (CloudStorage, ChangeRequestManager) (3x - duplicates)
  - updaters.config_updater.ConfigUpdater

**Architecture**: Web UI + REST API in single file

---

### web/models.py (654 lines)

**Purpose**: Data models, parsers, and managers for web API

**Enum: DeviationStatus** (line 16):
- PENDING_REVIEW, FLAGGED_GOOD, FLAGGED_BAD, APPROVED, REJECTED

**Pydantic Models**:
- `DeviationItem` (line 24) - Deviation data
- `PluginConfig` (line 39) - Plugin config data
- `ServerView` (line 46) - Server view data
- `GlobalView` (line 58) - Global view data

**Class: DeviationParser** (line 68, 9 methods):
- `__init__(self, deviations_file, universal_file, base_repo_path)` - Initialize paths
- `load_universal_configs(self)` - Load universal configs from markdown
- `_save_universal_config(self, configs, plugin, config_file, content)` - Save parsed universal config
- `load_deviations(self)` - Load deviations from markdown
- `_parse_value(self, value_str)` - Parse value string to Python type
- `get_deviations_by_server(self, server_name)` - Filter by server
- `get_deviations_by_plugin(self, plugin_name)` - Filter by plugin
- `get_deviations_by_status(self, status)` - Filter by status
- `get_universal_config(self, plugin, config_file, key_path)` - Get universal config value

**Class: DeviationManager** (line 411, 6 methods):
- `__init__(self, storage_path)` - Initialize storage
- `flag_deviation(self, server_name, plugin_name, config_path, reason)` - Flag deviation as bad
- `get_flagged_bad_deviations(self)` - Get all flagged bad
- `generate_fix_changes(self)` - Generate change requests to fix flagged deviations
- `save_reviews(self)` - Persist reviews to JSON
- `load_reviews(self)` - Load reviews from JSON

**Imports**:
- **Third-party**: pydantic (BaseModel, Field), yaml (3x - duplicate)
- **Stdlib**: typing, pathlib, enum, json (5x - many duplicates), datetime (2x), uuid
- **Internal**: core.data_loader (ProductionDataLoader, ServerInfo)

---

## Known Issues from production-hotfix-v2.sh

1. **drift_detector.py line 203**: isinstance() check crashes when comparing lists/dicts
2. **config_parser.py ~line 75**: UTF-8-sig encoding needed for BOM handling
3. **config_parser.py**: IP address parsing bug (unspecified line)
4. **agent/service.py ~line 326**: Duplicate DriftDetector initialization

---

## Import Duplication Analysis

**Files with duplicate imports** (same module imported multiple times):
- `agent/service.py` - yaml (2x), analyzers.drift_detector.DriftDetector (2x)
- `analyzers/compliance_checker.py` - core.config_parser.ConfigParser (5x), core.safety_validator.SafetyValidator (2x)
- `analyzers/drift_detector.py` - core.config_parser.ConfigParser (3x)
- `core/cloud_storage.py` - datetime.datetime (2x)
- `updaters/config_updater.py` - datetime.datetime (2x), shutil (2x)
- `updaters/plugin_checker.py` - core.settings.get_settings (2x), datetime.datetime (2x), requests (3x), yaml (3x), re (3x)
- `deployment/pipeline.py` - datetime.datetime (2x), json (2x), updaters.config_updater.ConfigUpdater (3x)
- `web/api.py` - updaters.plugin_checker.PluginChecker (6x), deployment.pipeline.DeploymentPipeline (5x), core.cloud_storage (CloudStorage + ChangeRequestManager) (3x)
- `web/models.py` - json (5x), datetime (2x), yaml (3x)
- `utils/error_handler.py` - logging (4x), datetime.datetime (4x)

**Impact**: Code smell but not functional bug. May indicate copy/paste or merge conflicts.

---

## Naming Schemas

**Classes**:
- Domain classes: `{Noun}{Action}` (e.g., DriftDetector, ConfigUpdater, DeploymentPipeline)
- Data classes: `{Noun}Config` (e.g., MinIOConfig, AgentConfig)
- Enums: `{Noun}Status` or `{Noun}Stage` (e.g., DeviationStatus, DeploymentStage)
- Managers: `{Noun}Manager` (e.g., ChangeRequestManager, ConfigBackupManager)

**Functions**:
- Public methods: `{verb}_{noun}` (e.g., load_config, apply_change, check_drift)
- Private methods: `_{verb}_{noun}` (e.g., _load_settings, _compare_configs)
- Static/class methods: Same as public
- Entry points: `main()`

**Files**:
- Module pattern: `{noun}_{noun}.py` (e.g., config_parser.py, cloud_storage.py, drift_detector.py)
- Entry point scripts: `{noun}_updater.py`, `{noun}_installer.py`

**Constants**: UPPERCASE_WITH_UNDERSCORES (in Enum and dataclass defaults)

---

## Flow Patterns

**Agent Flow**:
1. Load config → Discover instances → Start loop
2. Loop: Check drift (periodic) → Process pending changes (MinIO) → Sleep
3. On SIGTERM: Upload final drift report → Exit

**Web API Flow**:
1. FastAPI startup → Load settings → Initialize storage
2. Request: Parse → Validate → Query data/trigger action → Response
3. Background tasks: Deployment pipeline, plugin updates

**Deployment Pipeline Flow**:
1. Create deployment → Deploy to DEV01 → Validate
2. Manual approval → Deploy to PROD → Verify
3. On failure: Rollback

**Config Update Flow**:
1. Load change request → Validate schema → Backup files
2. Verify expected values → Apply changes → Verify results
3. On failure: Rollback from backup

**Drift Detection Flow**:
1. Load baseline → Scan server configs → Compare
2. Calculate drift → Prioritize → Generate report → Upload to MinIO

---

*Scan complete. 32 files, 11,371 lines, 48 classes documented. Ready for Pass 2: Concept Resolution.*

