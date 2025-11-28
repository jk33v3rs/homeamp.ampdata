# Function Mapping V2.0
**Complete Function-to-Feature-to-Table Mapping**

## Overview

**Target**: ~400 functions (down from 979 in V1.0)
**Reduction**: ~60% fewer functions
**Strategy**: Eliminate duplication, use Repository Pattern, consolidate utilities

---

## 1. Core Layer (src/core/)

### 1.1 Database (`src/core/database.py`)

#### `get_db_session() -> Session`
- **Purpose**: Provide database session via dependency injection
- **Tables**: None (creates session)
- **Feature**: Database connection pooling
- **Lines**: ~5

#### `init_database(url: str) -> Engine`
- **Purpose**: Initialize SQLAlchemy engine with connection pool
- **Tables**: None (infrastructure)
- **Feature**: Database initialization
- **Lines**: ~10

#### `close_database() -> None`
- **Purpose**: Gracefully close all database connections
- **Tables**: None
- **Feature**: Cleanup
- **Lines**: ~5

**Subtotal: 3 functions, ~20 lines**

---

### 1.2 Configuration (`src/core/config.py`)

#### `load_config(path: str) -> Settings`
- **Purpose**: Load application configuration from YAML/ENV
- **Tables**: None
- **Feature**: Configuration management
- **Lines**: ~15

#### `get_settings() -> Settings`
- **Purpose**: Singleton pattern for app settings
- **Tables**: None
- **Feature**: Configuration access
- **Lines**: ~5

#### `validate_config(settings: Settings) -> bool`
- **Purpose**: Validate configuration on startup
- **Tables**: None
- **Feature**: Configuration validation
- **Lines**: ~10

**Subtotal: 3 functions, ~30 lines**

---

### 1.3 Logging (`src/core/logging.py`)

#### `setup_logging(level: str, log_dir: str) -> None`
- **Purpose**: Configure structured logging (JSON + file rotation)
- **Tables**: None
- **Feature**: Observability
- **Lines**: ~20

#### `get_logger(name: str) -> Logger`
- **Purpose**: Get logger instance for module
- **Tables**: None
- **Feature**: Logging
- **Lines**: ~5

#### `log_to_database(event: dict) -> None`
- **Purpose**: Write critical events to audit_log table
- **Tables**: `audit_log`
- **Feature**: Audit trail
- **Lines**: ~10

**Subtotal: 3 functions, ~35 lines**

---

### 1.4 Exceptions (`src/core/exceptions.py`)

#### Custom exception classes (12 classes)
- `ConfigurationError`
- `DatabaseConnectionError`
- `InstanceNotFoundError`
- `PluginNotFoundError`
- `DeploymentError`
- `ValidationError`
- `PermissionDeniedError`
- `ResourceNotFoundError`
- `DuplicateResourceError`
- `VarianceDetectedError`
- `ApprovalRequiredError`
- `BackupFailedError`

**Subtotal: 12 classes, ~60 lines total**

---

## 2. Domain Layer (src/domain/)

### 2.1 Models (`src/domain/models/`)

**Note**: SQLAlchemy ORM models, not functions. ~55 model classes matching schema tables.

---

### 2.2 Domain Services (`src/domain/services/`)

#### Instance Service (`instance_service.py`)

##### `validate_instance(instance_id: str, path: str) -> bool`
- **Purpose**: Validate instance has required files (server.jar, etc.)
- **Tables**: None (filesystem check)
- **Feature**: Instance validation
- **Lines**: ~15

##### `get_instance_platform(path: str) -> str`
- **Purpose**: Detect platform (Paper/Fabric/etc.) from jar filename
- **Tables**: None
- **Feature**: Platform detection
- **Lines**: ~20

##### `calculate_instance_hash(path: str) -> str`
- **Purpose**: Generate hash of instance directory for change detection
- **Tables**: None
- **Feature**: Change detection
- **Lines**: ~10

**Subtotal: 3 functions, ~45 lines**

---

#### Plugin Service (`plugin_service.py`)

##### `parse_plugin_metadata(jar_path: str) -> dict`
- **Purpose**: Extract plugin.yml/fabric.mod.json metadata from JAR
- **Tables**: None
- **Feature**: Plugin discovery
- **Lines**: ~25

##### `calculate_jar_hash(jar_path: str) -> str`
- **Purpose**: SHA-256 hash of plugin JAR file
- **Tables**: None
- **Feature**: Plugin verification
- **Lines**: ~8

##### `compare_versions(v1: str, v2: str) -> int`
- **Purpose**: Semantic version comparison (-1, 0, 1)
- **Tables**: None
- **Feature**: Version management
- **Lines**: ~15

##### `is_update_available(current: str, latest: str) -> bool`
- **Purpose**: Check if update is available
- **Tables**: None
- **Feature**: Update detection
- **Lines**: ~5

**Subtotal: 4 functions, ~53 lines**

---

#### Config Service (`config_service.py`)

##### `parse_yaml_config(file_path: str) -> dict`
- **Purpose**: Parse YAML config file with error handling
- **Tables**: None
- **Feature**: Config parsing
- **Lines**: ~15

##### `parse_json_config(file_path: str) -> dict`
- **Purpose**: Parse JSON config file (fabric mods)
- **Tables**: None
- **Feature**: Config parsing
- **Lines**: ~10

##### `parse_properties_file(file_path: str) -> dict`
- **Purpose**: Parse server.properties format
- **Tables**: None
- **Feature**: Config parsing
- **Lines**: ~12

##### `validate_config_value(value: str, expected_type: str) -> bool`
- **Purpose**: Validate config value matches expected type
- **Tables**: None
- **Feature**: Config validation
- **Lines**: ~20

##### `apply_variable_substitution(value: str, variables: dict) -> str`
- **Purpose**: Replace ${VAR} placeholders with actual values
- **Tables**: `config_variables`
- **Feature**: Config templating
- **Lines**: ~10

**Subtotal: 5 functions, ~67 lines**

---

#### Variance Service (`variance_service.py`)

##### `detect_variance(actual: str, expected: str, key: str) -> dict`
- **Purpose**: Compare actual vs expected value, return variance details
- **Tables**: None (pure logic)
- **Feature**: Variance detection
- **Lines**: ~15

##### `calculate_variance_severity(rule: ConfigRule, variance: dict) -> str`
- **Purpose**: Determine severity based on rule enforcement level
- **Tables**: None
- **Feature**: Variance prioritization
- **Lines**: ~12

##### `should_auto_resolve(variance: dict) -> bool`
- **Purpose**: Determine if variance can be auto-corrected
- **Tables**: None
- **Feature**: Auto-remediation
- **Lines**: ~8

**Subtotal: 3 functions, ~35 lines**

---

#### Update Service (`update_service.py`)

##### `check_modrinth_updates(plugin_id: str) -> list`
- **Purpose**: Query Modrinth API for plugin versions
- **Tables**: `plugin_versions`
- **Feature**: Update checking
- **Lines**: ~30

##### `check_hangar_updates(plugin_id: str) -> list`
- **Purpose**: Query Hangar API for plugin versions
- **Tables**: `plugin_versions`
- **Feature**: Update checking
- **Lines**: ~30

##### `check_github_releases(repo: str) -> list`
- **Purpose**: Query GitHub API for releases
- **Tables**: `plugin_versions`
- **Feature**: Update checking
- **Lines**: ~25

##### `check_spigot_updates(resource_id: int) -> list`
- **Purpose**: Scrape SpigotMC for updates (no API)
- **Tables**: `plugin_versions`
- **Feature**: Update checking
- **Lines**: ~40

##### `parse_changelog(text: str) -> str`
- **Purpose**: Extract and format changelog from release notes
- **Tables**: None
- **Feature**: Changelog parsing
- **Lines**: ~15

**Subtotal: 5 functions, ~140 lines**

---

**Domain Layer Total: 23 functions, ~340 lines**

---

## 3. Data Layer (src/data/)

### 3.1 Base Repository (`src/data/base_repository.py`)

#### `BaseRepository` class (generic CRUD operations)

##### `get_by_id(id: Any) -> Optional[Model]`
- **Purpose**: Retrieve entity by primary key
- **Tables**: Any
- **Feature**: Data access
- **Lines**: ~5

##### `get_all(filters: dict) -> list[Model]`
- **Purpose**: Retrieve all entities matching filters
- **Tables**: Any
- **Feature**: Data access
- **Lines**: ~8

##### `create(entity: Model) -> Model`
- **Purpose**: Insert new entity
- **Tables**: Any
- **Feature**: Data persistence
- **Lines**: ~6

##### `update(entity: Model) -> Model`
- **Purpose**: Update existing entity
- **Tables**: Any
- **Feature**: Data persistence
- **Lines**: ~6

##### `delete(id: Any) -> bool`
- **Purpose**: Delete entity by ID
- **Tables**: Any
- **Feature**: Data persistence
- **Lines**: ~6

##### `exists(id: Any) -> bool`
- **Purpose**: Check if entity exists
- **Tables**: Any
- **Feature**: Data validation
- **Lines**: ~4

**Subtotal: 6 methods, ~35 lines**

---

### 3.2 Instance Repository (`instance_repository.py`)

Extends `BaseRepository[Instance]`

##### `get_by_platform(platform: str) -> list[Instance]`
- **Purpose**: Get all instances of specific platform
- **Tables**: `instances`
- **Feature**: Instance filtering
- **Lines**: ~5

##### `get_active_instances() -> list[Instance]`
- **Purpose**: Get all active instances
- **Tables**: `instances`
- **Feature**: Instance filtering
- **Lines**: ~5

##### `update_last_seen(instance_id: str) -> None`
- **Purpose**: Update last_seen_at timestamp
- **Tables**: `instances`
- **Feature**: Instance tracking
- **Lines**: ~4

##### `get_by_server(server_name: str) -> list[Instance]`
- **Purpose**: Get instances on specific physical server
- **Tables**: `instances`
- **Feature**: Server management
- **Lines**: ~5

**Subtotal: 4 methods, ~19 lines** (+6 inherited = 10 total)

---

### 3.3 Plugin Repository (`plugin_repository.py`)

Extends `BaseRepository[Plugin]`

##### `get_by_modrinth_id(modrinth_id: str) -> Optional[Plugin]`
- **Purpose**: Find plugin by Modrinth ID
- **Tables**: `plugins`
- **Feature**: Plugin lookup
- **Lines**: ~5

##### `get_by_github_repo(repo: str) -> Optional[Plugin]`
- **Purpose**: Find plugin by GitHub repo
- **Tables**: `plugins`
- **Feature**: Plugin lookup
- **Lines**: ~5

##### `search_plugins(query: str) -> list[Plugin]`
- **Purpose**: Search plugins by name/description
- **Tables**: `plugins`
- **Feature**: Plugin search
- **Lines**: ~8

**Subtotal: 3 methods, ~18 lines** (+6 inherited = 9 total)

---

### 3.4 Config Repository (`config_repository.py`)

Extends `BaseRepository[ConfigRule]`

##### `get_rules_for_scope(scope_type: str, scope_id: str) -> list[ConfigRule]`
- **Purpose**: Get all rules for specific scope
- **Tables**: `config_rules`
- **Feature**: Rule retrieval
- **Lines**: ~8

##### `get_rule_by_key(plugin: str, file: str, key: str) -> Optional[ConfigRule]`
- **Purpose**: Find specific config rule
- **Tables**: `config_rules`
- **Feature**: Rule lookup
- **Lines**: ~10

**Subtotal: 2 methods, ~18 lines** (+6 inherited = 8 total)

---

### 3.5 Deployment Repository (`deployment_repository.py`)

Extends `BaseRepository[DeploymentQueue]`

##### `get_pending_deployments() -> list[DeploymentQueue]`
- **Purpose**: Get all pending deployments sorted by priority
- **Tables**: `deployment_queue`
- **Feature**: Deployment management
- **Lines**: ~8

##### `get_by_status(status: str) -> list[DeploymentQueue]`
- **Purpose**: Filter deployments by status
- **Tables**: `deployment_queue`
- **Feature**: Deployment filtering
- **Lines**: ~5

##### `mark_as_deploying(queue_id: int) -> None`
- **Purpose**: Update status to 'deploying'
- **Tables**: `deployment_queue`
- **Feature**: Deployment lifecycle
- **Lines**: ~6

**Subtotal: 3 methods, ~19 lines** (+6 inherited = 9 total)

---

### 3.6 Unit of Work (`unit_of_work.py`)

#### `UnitOfWork` class

##### `__enter__() -> UnitOfWork`
- **Purpose**: Begin transaction
- **Tables**: None (transaction management)
- **Feature**: ACID transactions
- **Lines**: ~5

##### `__exit__() -> None`
- **Purpose**: Commit or rollback transaction
- **Tables**: None
- **Feature**: ACID transactions
- **Lines**: ~8

##### `commit() -> None`
- **Purpose**: Commit current transaction
- **Tables**: None
- **Feature**: Data persistence
- **Lines**: ~3

##### `rollback() -> None`
- **Purpose**: Rollback current transaction
- **Tables**: None
- **Feature**: Error recovery
- **Lines**: ~3

**Subtotal: 4 methods, ~19 lines**

---

**Data Layer Total: ~22 methods + repository pattern, ~128 lines**

---

## Progress Check

**Created so far:**
- Core Layer: 21 items (functions/classes), ~145 lines
- Domain Layer: 23 functions, ~340 lines  
- Data Layer: 22 methods, ~128 lines

**Total: 66 items, ~613 lines**

**Remaining:**
- Agent Layer (largest section)
- API Layer
- CLI Layer
- Integration Layer

---

## 4. Agent Layer (src/agent/)

### 4.1 Discovery (`src/agent/discovery.py`)

#### `InstanceDiscovery` class

##### `scan_server(server_name: str, base_paths: list[str]) -> list[Instance]`
- **Purpose**: Scan server for AMP instances
- **Tables**: `instances`, `discovery_runs`, `discovery_items`
- **Feature**: Instance discovery
- **Lines**: ~40

##### `detect_platform(instance_path: str) -> str`
- **Purpose**: Identify platform from jar files
- **Tables**: None
- **Feature**: Platform detection
- **Lines**: ~20

##### `extract_instance_metadata(path: str) -> dict`
- **Purpose**: Extract display name, version, etc.
- **Tables**: None
- **Feature**: Metadata extraction
- **Lines**: ~25

##### `discover_plugins(instance_path: str) -> list[dict]`
- **Purpose**: Scan plugins folder, extract metadata
- **Tables**: `plugins`, `instance_plugins`
- **Feature**: Plugin discovery
- **Lines**: ~30

##### `discover_datapacks(instance_path: str) -> list[dict]`
- **Purpose**: Scan world/datapacks folders
- **Tables**: `datapacks`, `instance_datapacks`
- **Feature**: Datapack discovery
- **Lines**: ~25

##### `discover_worlds(instance_path: str) -> list[dict]`
- **Purpose**: Scan for world folders (level.dat)
- **Tables**: `worlds`
- **Feature**: World discovery
- **Lines**: ~20

**Subtotal: 6 methods, ~160 lines**

---

### 4.2 Config Scanner (`src/agent/config_scanner.py`)

#### `ConfigScanner` class

##### `scan_instance_configs(instance_id: str, instance_path: str) -> dict`
- **Purpose**: Scan all config files in instance
- **Tables**: `config_values`, `config_file_metadata`
- **Feature**: Config discovery
- **Lines**: ~35

##### `scan_plugin_config(plugin_path: str) -> dict`
- **Purpose**: Parse plugin's config.yml
- **Tables**: `config_values`
- **Feature**: Config parsing
- **Lines**: ~20

##### `scan_server_properties(path: str) -> dict`
- **Purpose**: Parse server.properties
- **Tables**: `server_properties`
- **Feature**: Server config parsing
- **Lines**: ~15

##### `calculate_file_hash(file_path: str) -> str`
- **Purpose**: SHA-256 hash for change detection
- **Tables**: None
- **Feature**: Change detection
- **Lines**: ~8

**Subtotal: 4 methods, ~78 lines**

---

### 4.3 Variance Detector (`src/agent/variance_detector.py`)

#### `VarianceDetector` class

##### `detect_all_variances(instance_id: str) -> list[Variance]`
- **Purpose**: Compare all configs against rules
- **Tables**: `config_variances`, `config_rules`, `config_values`
- **Feature**: Variance detection
- **Lines**: ~45

##### `check_config_key(instance_id: str, rule: ConfigRule, actual_value: str) -> Optional[Variance]`
- **Purpose**: Check single config key against rule
- **Tables**: `config_variances`
- **Feature**: Variance checking
- **Lines**: ~25

##### `check_server_properties_variance(instance_id: str) -> list[Variance]`
- **Purpose**: Check server.properties against baselines
- **Tables**: `server_properties_variances`
- **Feature**: Server config variance
- **Lines**: ~30

##### `resolve_variance(variance_id: int, notes: str) -> None`
- **Purpose**: Mark variance as resolved
- **Tables**: `config_variances`
- **Feature**: Variance lifecycle
- **Lines**: ~10

**Subtotal: 4 methods, ~110 lines**

---

### 4.4 Update Checker (`src/agent/update_checker.py`)

#### `UpdateChecker` class

##### `check_all_plugin_updates() -> dict`
- **Purpose**: Check updates for all plugins from all sources
- **Tables**: `plugin_update_sources`, `plugin_versions`, `plugin_update_queue`
- **Feature**: Update checking
- **Lines**: ~40

##### `check_plugin_updates(plugin_id: str) -> list[Version]`
- **Purpose**: Check updates for specific plugin
- **Tables**: `plugin_versions`, `plugin_update_sources`
- **Feature**: Update checking
- **Lines**: ~35

##### `queue_plugin_update(instance_id: str, plugin_id: str, version: str) -> int`
- **Purpose**: Add update to deployment queue
- **Tables**: `plugin_update_queue`
- **Feature**: Update queueing
- **Lines**: ~15

##### `check_datapack_updates() -> dict`
- **Purpose**: Check datapack updates from sources
- **Tables**: `datapack_update_sources`, `datapack_versions`
- **Feature**: Datapack updates
- **Lines**: ~30

**Subtotal: 4 methods, ~120 lines**

---

### 4.5 Deployment Executor (`src/agent/deployment_executor.py`)

#### `DeploymentExecutor` class

##### `execute_deployment(queue_id: int) -> DeploymentHistory`
- **Purpose**: Execute queued deployment
- **Tables**: `deployment_queue`, `deployment_history`, `deployment_changes`, `deployment_logs`
- **Feature**: Deployment execution
- **Lines**: ~60

##### `deploy_config_change(instance_id: str, changes: dict) -> bool`
- **Purpose**: Apply configuration changes to instance
- **Tables**: `config_values`, `config_changes`, `config_file_metadata`
- **Feature**: Config deployment
- **Lines**: ~40

##### `deploy_plugin_update(instance_id: str, plugin_id: str, version: str) -> bool`
- **Purpose**: Download and install plugin update
- **Tables**: `instance_plugins`, `plugin_versions`
- **Feature**: Plugin deployment
- **Lines**: ~50

##### `deploy_datapack(instance_id: str, world: str, datapack_id: str, version: str) -> bool`
- **Purpose**: Deploy datapack to world folder
- **Tables**: `instance_datapacks`, `datapack_versions`
- **Feature**: Datapack deployment
- **Lines**: ~35

##### `rollback_deployment(deployment_id: int) -> bool`
- **Purpose**: Rollback failed deployment using backups
- **Tables**: `deployment_history`, `backups`, `config_file_metadata`
- **Feature**: Deployment rollback
- **Lines**: ~45

**Subtotal: 5 methods, ~230 lines**

---

### 4.6 File Watcher (`src/agent/file_watcher.py`)

**Note**: Single unified watcher (replaces 3 separate watchers in V1)

#### `FileWatcher` class

##### `watch_directory(path: str, file_types: list[str], callback: Callable) -> None`
- **Purpose**: Generic file watcher for plugins/datapacks/configs
- **Tables**: None (triggers callbacks)
- **Feature**: Real-time monitoring
- **Lines**: ~35

##### `on_file_created(event: FileSystemEvent) -> None`
- **Purpose**: Handle new file creation
- **Tables**: Depends on file type
- **Feature**: Auto-discovery
- **Lines**: ~20

##### `on_file_modified(event: FileSystemEvent) -> None`
- **Purpose**: Handle file modification
- **Tables**: Depends on file type
- **Feature**: Change detection
- **Lines**: ~20

##### `on_file_deleted(event: FileSystemEvent) -> None`
- **Purpose**: Handle file deletion
- **Tables**: Depends on file type
- **Feature**: Cleanup
- **Lines**: ~15

**Subtotal: 4 methods, ~90 lines**

---

### 4.7 Backup Manager (`src/agent/backup_manager.py`)

#### `BackupManager` class

##### `create_backup(instance_id: str, backup_type: str) -> Backup`
- **Purpose**: Create instance backup (config/plugins/full)
- **Tables**: `backups`, `config_file_metadata`
- **Feature**: Backup creation
- **Lines**: ~50

##### `restore_backup(backup_id: int) -> bool`
- **Purpose**: Restore from backup
- **Tables**: `backups`
- **Feature**: Backup restoration
- **Lines**: ~40

##### `cleanup_old_backups(retention_days: int) -> int`
- **Purpose**: Delete expired backups
- **Tables**: `backups`
- **Feature**: Backup lifecycle
- **Lines**: ~20

##### `verify_backup_integrity(backup_id: int) -> bool`
- **Purpose**: Verify backup files exist and are valid
- **Tables**: `backups`
- **Feature**: Backup verification
- **Lines**: ~15

**Subtotal: 4 methods, ~125 lines**

---

### 4.8 Agent Main (`src/agent/agent.py`)

#### `Agent` class (orchestrates all agent functionality)

##### `run() -> None`
- **Purpose**: Main agent loop
- **Tables**: `agent_heartbeats`, `scheduled_tasks`
- **Feature**: Agent lifecycle
- **Lines**: ~40

##### `send_heartbeat() -> None`
- **Purpose**: Record agent status in database
- **Tables**: `agent_heartbeats`, `system_metrics`
- **Feature**: Health monitoring
- **Lines**: ~25

##### `execute_scheduled_tasks() -> None`
- **Purpose**: Run scheduled discovery/update checks
- **Tables**: `scheduled_tasks`
- **Feature**: Task scheduling
- **Lines**: ~30

##### `handle_webhook_event(event_id: int) -> None`
- **Purpose**: Process CI/CD webhook
- **Tables**: `webhook_events`, `plugin_update_queue`
- **Feature**: CI/CD integration
- **Lines**: ~35

##### `graceful_shutdown() -> None`
- **Purpose**: Clean shutdown on signal
- **Tables**: None
- **Feature**: Lifecycle management
- **Lines**: ~15

**Subtotal: 5 methods, ~145 lines**

---

**Agent Layer Total: 36 methods, ~1058 lines**

---

## Progress Check #2

**So far:**
- Core: 21 items, ~145 lines
- Domain: 23 functions, ~340 lines
- Data: 22 methods, ~128 lines
- Agent: 36 methods, ~1058 lines

**Total: 102 items, ~1671 lines**

**Remaining:**
- API Layer
- CLI Layer  
- Integration Layer

---

## 5. API Layer (src/api/)

### 5.1 Main API (`src/api/main.py`)

#### FastAPI application setup

##### `create_app() -> FastAPI`
- **Purpose**: Initialize FastAPI app with middleware, CORS, etc.
- **Tables**: None
- **Feature**: API initialization
- **Lines**: ~25

##### `startup_event() -> None`
- **Purpose**: Initialize database, load config on startup
- **Tables**: None
- **Feature**: Application lifecycle
- **Lines**: ~15

##### `shutdown_event() -> None`
- **Purpose**: Close database connections on shutdown
- **Tables**: None
- **Feature**: Application lifecycle
- **Lines**: ~10

**Subtotal: 3 functions, ~50 lines**

---

### 5.2 Instance Endpoints (`src/api/routes/instances.py`)

#### `GET /instances`
- **Purpose**: List all instances with filtering
- **Tables**: `instances`
- **Feature**: Instance listing
- **Lines**: ~15

#### `GET /instances/{instance_id}`
- **Purpose**: Get instance details
- **Tables**: `instances`, `instance_plugins`, `worlds`
- **Feature**: Instance details
- **Lines**: ~20

#### `POST /instances`
- **Purpose**: Manually register instance
- **Tables**: `instances`
- **Feature**: Instance registration
- **Lines**: ~25

#### `PUT /instances/{instance_id}`
- **Purpose**: Update instance metadata
- **Tables**: `instances`
- **Feature**: Instance management
- **Lines**: ~20

#### `DELETE /instances/{instance_id}`
- **Purpose**: Delete instance record
- **Tables**: `instances`
- **Feature**: Instance management
- **Lines**: ~15

#### `GET /instances/{instance_id}/plugins`
- **Purpose**: List plugins for instance
- **Tables**: `instance_plugins`, `plugins`
- **Feature**: Plugin listing
- **Lines**: ~15

#### `GET /instances/{instance_id}/configs`
- **Purpose**: Get all config values for instance
- **Tables**: `config_values`
- **Feature**: Config retrieval
- **Lines**: ~15

#### `GET /instances/{instance_id}/variances`
- **Purpose**: Get config variances for instance
- **Tables**: `config_variances`
- **Feature**: Variance reporting
- **Lines**: ~15

**Subtotal: 8 endpoints, ~140 lines**

---

### 5.3 Plugin Endpoints (`src/api/routes/plugins.py`)

#### `GET /plugins`
- **Purpose**: List all plugins with search
- **Tables**: `plugins`
- **Feature**: Plugin catalog
- **Lines**: ~15

#### `GET /plugins/{plugin_id}`
- **Purpose**: Get plugin details
- **Tables**: `plugins`, `plugin_versions`, `plugin_update_sources`
- **Feature**: Plugin details
- **Lines**: ~20

#### `POST /plugins`
- **Purpose**: Register new plugin
- **Tables**: `plugins`
- **Feature**: Plugin registration
- **Lines**: ~25

#### `PUT /plugins/{plugin_id}`
- **Purpose**: Update plugin metadata
- **Tables**: `plugins`
- **Feature**: Plugin management
- **Lines**: ~20

#### `GET /plugins/{plugin_id}/versions`
- **Purpose**: List available versions
- **Tables**: `plugin_versions`
- **Feature**: Version listing
- **Lines**: ~15

#### `POST /plugins/{plugin_id}/check-updates`
- **Purpose**: Manually trigger update check
- **Tables**: `plugin_versions`, `plugin_update_sources`
- **Feature**: Update checking
- **Lines**: ~20

**Subtotal: 6 endpoints, ~115 lines**

---

### 5.4 Config Endpoints (`src/api/routes/configs.py`)

#### `GET /config/rules`
- **Purpose**: List all config rules
- **Tables**: `config_rules`
- **Feature**: Rule management
- **Lines**: ~15

#### `POST /config/rules`
- **Purpose**: Create new config rule
- **Tables**: `config_rules`
- **Feature**: Rule creation
- **Lines**: ~30

#### `PUT /config/rules/{rule_id}`
- **Purpose**: Update config rule
- **Tables**: `config_rules`
- **Feature**: Rule management
- **Lines**: ~25

#### `DELETE /config/rules/{rule_id}`
- **Purpose**: Delete config rule
- **Tables**: `config_rules`
- **Feature**: Rule management
- **Lines**: ~15

#### `GET /config/variances`
- **Purpose**: List all variances (filterable)
- **Tables**: `config_variances`
- **Feature**: Variance dashboard
- **Lines**: ~20

#### `POST /config/variances/{variance_id}/resolve`
- **Purpose**: Mark variance as resolved
- **Tables**: `config_variances`
- **Feature**: Variance lifecycle
- **Lines**: ~20

#### `GET /config/variables`
- **Purpose**: List template variables
- **Tables**: `config_variables`
- **Feature**: Variable management
- **Lines**: ~15

#### `POST /config/variables`
- **Purpose**: Create template variable
- **Tables**: `config_variables`
- **Feature**: Variable management
- **Lines**: ~20

**Subtotal: 8 endpoints, ~160 lines**

---

### 5.5 Deployment Endpoints (`src/api/routes/deployments.py`)

#### `GET /deployments/queue`
- **Purpose**: Get pending deployments
- **Tables**: `deployment_queue`
- **Feature**: Deployment queue
- **Lines**: ~15

#### `POST /deployments/queue`
- **Purpose**: Add deployment to queue
- **Tables**: `deployment_queue`
- **Feature**: Deployment queueing
- **Lines**: ~35

#### `POST /deployments/{queue_id}/approve`
- **Purpose**: Approve queued deployment
- **Tables**: `deployment_queue`, `approval_requests`, `approval_votes`
- **Feature**: Approval workflow
- **Lines**: ~30

#### `POST /deployments/{queue_id}/reject`
- **Purpose**: Reject queued deployment
- **Tables**: `deployment_queue`, `approval_requests`
- **Feature**: Approval workflow
- **Lines**: ~25

#### `POST /deployments/{queue_id}/execute`
- **Purpose**: Execute approved deployment
- **Tables**: `deployment_queue`, `deployment_history`
- **Feature**: Deployment execution
- **Lines**: ~25

#### `GET /deployments/history`
- **Purpose**: Get deployment history
- **Tables**: `deployment_history`, `deployment_changes`
- **Feature**: Deployment audit
- **Lines**: ~20

#### `GET /deployments/{deployment_id}`
- **Purpose**: Get deployment details
- **Tables**: `deployment_history`, `deployment_changes`, `deployment_logs`
- **Feature**: Deployment details
- **Lines**: ~25

#### `POST /deployments/{deployment_id}/rollback`
- **Purpose**: Rollback deployment
- **Tables**: `deployment_history`, `backups`
- **Feature**: Deployment rollback
- **Lines**: ~30

**Subtotal: 8 endpoints, ~205 lines**

---

### 5.6 Tag Endpoints (`src/api/routes/tags.py`)

#### `GET /tags`
- **Purpose**: List all tags
- **Tables**: `meta_tags`
- **Feature**: Tag management
- **Lines**: ~15

#### `POST /tags`
- **Purpose**: Create new tag
- **Tables**: `meta_tags`
- **Feature**: Tag creation
- **Lines**: ~20

#### `POST /tags/assign`
- **Purpose**: Assign tag to entity
- **Tables**: `tag_assignments`
- **Feature**: Tag assignment
- **Lines**: ~25

#### `DELETE /tags/assign/{assignment_id}`
- **Purpose**: Remove tag assignment
- **Tables**: `tag_assignments`
- **Feature**: Tag management
- **Lines**: ~15

#### `GET /tags/{tag_id}/entities`
- **Purpose**: Get all entities with specific tag
- **Tables**: `tag_assignments`
- **Feature**: Tag filtering
- **Lines**: ~20

**Subtotal: 5 endpoints, ~95 lines**

---

### 5.7 Monitoring Endpoints (`src/api/routes/monitoring.py`)

#### `GET /monitoring/health`
- **Purpose**: API health check
- **Tables**: None
- **Feature**: Health monitoring
- **Lines**: ~10

#### `GET /monitoring/agents`
- **Purpose**: Get agent status
- **Tables**: `agent_heartbeats`
- **Feature**: Agent monitoring
- **Lines**: ~15

#### `GET /monitoring/metrics`
- **Purpose**: Get system metrics
- **Tables**: `system_metrics`
- **Feature**: Metrics dashboard
- **Lines**: ~20

#### `GET /monitoring/audit-log`
- **Purpose**: Get audit trail
- **Tables**: `audit_log`
- **Feature**: Audit reporting
- **Lines**: ~20

#### `GET /monitoring/discovery-runs`
- **Purpose**: Get discovery run history
- **Tables**: `discovery_runs`, `discovery_items`
- **Feature**: Discovery monitoring
- **Lines**: ~20

**Subtotal: 5 endpoints, ~85 lines**

---

### 5.8 Dashboard Endpoints (`src/api/routes/dashboard.py`)

#### `GET /dashboard/stats`
- **Purpose**: Get dashboard statistics
- **Tables**: `instances`, `plugins`, `config_variances`, `deployment_queue`
- **Feature**: Dashboard overview
- **Lines**: ~40

#### `GET /dashboard/recent-activity`
- **Purpose**: Get recent changes/deployments
- **Tables**: `deployment_history`, `config_changes`, `audit_log`
- **Feature**: Activity feed
- **Lines**: ~30

#### `GET /dashboard/alerts`
- **Purpose**: Get critical variances/issues
- **Tables**: `config_variances`, `server_properties_variances`, `agent_heartbeats`
- **Feature**: Alert dashboard
- **Lines**: ~35

**Subtotal: 3 endpoints, ~105 lines**

---

**API Layer Total: 46 endpoints, ~955 lines**

---

## Progress Check #3

**So far:**
- Core: 21 items, ~145 lines
- Domain: 23 functions, ~340 lines
- Data: 22 methods, ~128 lines
- Agent: 36 methods, ~1058 lines
- API: 46 endpoints, ~955 lines

**Total: 148 items, ~2626 lines**

**Remaining:**
- CLI Layer
- Integration Layer

---

## 6. CLI Layer (src/cli/)

### 6.1 Main CLI (`src/cli/main.py`)

#### Typer CLI application

##### `app: Typer()`
- **Purpose**: Main CLI app using Typer
- **Lines**: ~5

**Subtotal: 1 app definition, ~5 lines**

---

### 6.2 Instance Commands (`src/cli/instance_commands.py`)

#### `list_instances(server: str = None, platform: str = None)`
- **Purpose**: List instances with filters
- **Tables**: `instances`
- **Feature**: Instance listing
- **Lines**: ~20

#### `show_instance(instance_id: str)`
- **Purpose**: Show detailed instance info
- **Tables**: `instances`, `instance_plugins`, `config_variances`
- **Feature**: Instance details
- **Lines**: ~30

#### `register_instance(instance_id: str, path: str, platform: str)`
- **Purpose**: Manually register instance
- **Tables**: `instances`
- **Feature**: Instance registration
- **Lines**: ~25

#### `scan_instance(instance_id: str)`
- **Purpose**: Trigger immediate instance scan
- **Tables**: `instances`, `instance_plugins`, `config_values`
- **Feature**: Manual discovery
- **Lines**: ~20

**Subtotal: 4 commands, ~95 lines**

---

### 6.3 Config Commands (`src/cli/config_commands.py`)

#### `list_rules(scope_type: str = None)`
- **Purpose**: List config rules
- **Tables**: `config_rules`
- **Feature**: Rule management
- **Lines**: ~20

#### `create_rule(plugin: str, key: str, value: str, scope: str, enforcement: str)`
- **Purpose**: Create config rule
- **Tables**: `config_rules`
- **Feature**: Rule creation
- **Lines**: ~30

#### `list_variances(instance_id: str = None, severity: str = None)`
- **Purpose**: List config variances
- **Tables**: `config_variances`
- **Feature**: Variance reporting
- **Lines**: ~25

#### `resolve_variance(variance_id: int, notes: str)`
- **Purpose**: Mark variance as resolved
- **Tables**: `config_variances`
- **Feature**: Variance resolution
- **Lines**: ~20

**Subtotal: 4 commands, ~95 lines**

---

### 6.4 Deployment Commands (`src/cli/deployment_commands.py`)

#### `queue_deployment(type: str, target: str, payload_file: str)`
- **Purpose**: Add deployment to queue
- **Tables**: `deployment_queue`
- **Feature**: Deployment queueing
- **Lines**: ~30

#### `list_deployments(status: str = None)`
- **Purpose**: List queued deployments
- **Tables**: `deployment_queue`
- **Feature**: Deployment listing
- **Lines**: ~20

#### `approve_deployment(queue_id: int)`
- **Purpose**: Approve deployment
- **Tables**: `deployment_queue`, `approval_requests`
- **Feature**: Approval workflow
- **Lines**: ~25

#### `execute_deployment(queue_id: int)`
- **Purpose**: Execute deployment
- **Tables**: `deployment_queue`, `deployment_history`
- **Feature**: Deployment execution
- **Lines**: ~25

#### `deployment_history(limit: int = 20)`
- **Purpose**: Show recent deployments
- **Tables**: `deployment_history`
- **Feature**: Deployment audit
- **Lines**: ~20

**Subtotal: 5 commands, ~120 lines**

---

### 6.5 Plugin Commands (`src/cli/plugin_commands.py`)

#### `list_plugins(search: str = None)`
- **Purpose**: List plugins
- **Tables**: `plugins`
- **Feature**: Plugin listing
- **Lines**: ~20

#### `show_plugin(plugin_id: str)`
- **Purpose**: Show plugin details
- **Tables**: `plugins`, `plugin_versions`, `instance_plugins`
- **Feature**: Plugin details
- **Lines**: ~30

#### `check_updates(plugin_id: str = None)`
- **Purpose**: Check for plugin updates
- **Tables**: `plugin_versions`, `plugin_update_sources`
- **Feature**: Update checking
- **Lines**: ~25

#### `queue_update(instance_id: str, plugin_id: str, version: str)`
- **Purpose**: Queue plugin update
- **Tables**: `plugin_update_queue`
- **Feature**: Update queueing
- **Lines**: ~25

**Subtotal: 4 commands, ~100 lines**

---

### 6.6 Agent Commands (`src/cli/agent_commands.py`)

#### `start_agent(server: str)`
- **Purpose**: Start agent service
- **Tables**: None (process management)
- **Feature**: Agent control
- **Lines**: ~15

#### `stop_agent()`
- **Purpose**: Stop agent service
- **Tables**: None
- **Feature**: Agent control
- **Lines**: ~10

#### `agent_status()`
- **Purpose**: Show agent status
- **Tables**: `agent_heartbeats`
- **Feature**: Agent monitoring
- **Lines**: ~20

#### `trigger_discovery()`
- **Purpose**: Trigger immediate discovery run
- **Tables**: `discovery_runs`
- **Feature**: Manual discovery
- **Lines**: ~15

**Subtotal: 4 commands, ~60 lines**

---

### 6.7 Backup Commands (`src/cli/backup_commands.py`)

#### `create_backup(instance_id: str, type: str)`
- **Purpose**: Create instance backup
- **Tables**: `backups`
- **Feature**: Backup creation
- **Lines**: ~25

#### `list_backups(instance_id: str = None)`
- **Purpose**: List backups
- **Tables**: `backups`
- **Feature**: Backup listing
- **Lines**: ~20

#### `restore_backup(backup_id: int)`
- **Purpose**: Restore from backup
- **Tables**: `backups`
- **Feature**: Backup restoration
- **Lines**: ~30

#### `cleanup_backups(days: int = 30)`
- **Purpose**: Delete old backups
- **Tables**: `backups`
- **Feature**: Backup maintenance
- **Lines**: ~20

**Subtotal: 4 commands, ~95 lines**

---

**CLI Layer Total: 30 commands, ~570 lines**

---

## 7. Integration Layer (src/integrations/)

### 7.1 Modrinth Client (`src/integrations/modrinth.py`)

#### `ModrinthClient` class

##### `search_project(query: str) -> list[dict]`
- **Purpose**: Search Modrinth for projects
- **Tables**: None (external API)
- **Feature**: Plugin discovery
- **Lines**: ~20

##### `get_project(project_id: str) -> dict`
- **Purpose**: Get project details
- **Tables**: None
- **Feature**: Plugin metadata
- **Lines**: ~15

##### `get_versions(project_id: str) -> list[dict]`
- **Purpose**: Get project versions
- **Tables**: None
- **Feature**: Version listing
- **Lines**: ~15

##### `download_version(version_id: str, dest_path: str) -> str`
- **Purpose**: Download specific version
- **Tables**: None
- **Feature**: Plugin download
- **Lines**: ~20

**Subtotal: 4 methods, ~70 lines**

---

### 7.2 Hangar Client (`src/integrations/hangar.py`)

#### `HangarClient` class

##### `search_project(query: str) -> list[dict]`
- **Purpose**: Search Hangar (PaperMC)
- **Tables**: None
- **Feature**: Plugin discovery
- **Lines**: ~20

##### `get_project(slug: str) -> dict`
- **Purpose**: Get project details
- **Tables**: None
- **Feature**: Plugin metadata
- **Lines**: ~15

##### `get_versions(slug: str) -> list[dict]`
- **Purpose**: Get versions
- **Tables**: None
- **Feature**: Version listing
- **Lines**: ~15

##### `download_version(slug: str, version: str, dest_path: str) -> str`
- **Purpose**: Download version
- **Tables**: None
- **Feature**: Plugin download
- **Lines**: ~20

**Subtotal: 4 methods, ~70 lines**

---

### 7.3 GitHub Client (`src/integrations/github.py`)

#### `GitHubClient` class

##### `get_releases(repo: str) -> list[dict]`
- **Purpose**: Get GitHub releases
- **Tables**: None
- **Feature**: Version discovery
- **Lines**: ~20

##### `get_latest_release(repo: str) -> dict`
- **Purpose**: Get latest release
- **Tables**: None
- **Feature**: Update checking
- **Lines**: ~15

##### `download_release_asset(url: str, dest_path: str) -> str`
- **Purpose**: Download release asset
- **Tables**: None
- **Feature**: Plugin download
- **Lines**: ~20

**Subtotal: 3 methods, ~55 lines**

---

### 7.4 Discord Notifier (`src/integrations/discord.py`)

#### `DiscordNotifier` class

##### `send_notification(message: str, severity: str) -> bool`
- **Purpose**: Send Discord webhook notification
- **Tables**: `notification_log`
- **Feature**: Notifications
- **Lines**: ~25

##### `send_embed(title: str, description: str, fields: list, color: str) -> bool`
- **Purpose**: Send rich embed notification
- **Tables**: `notification_log`
- **Feature**: Rich notifications
- **Lines**: ~30

##### `send_deployment_notification(deployment: dict) -> bool`
- **Purpose**: Send deployment status to Discord
- **Tables**: `notification_log`
- **Feature**: Deployment alerts
- **Lines**: ~25

**Subtotal: 3 methods, ~80 lines**

---

### 7.5 LuckPerms Integration (`src/integrations/luckperms.py`)

#### `LuckPermsClient` class

##### `get_player_rank(player_uuid: str, instance_id: str) -> str`
- **Purpose**: Get player's primary rank
- **Tables**: `player_ranks` (cache)
- **Feature**: Rank retrieval
- **Lines**: ~20

##### `sync_ranks_to_db() -> None`
- **Purpose**: Sync LuckPerms ranks to database
- **Tables**: `ranks`, `player_ranks`
- **Feature**: Rank synchronization
- **Lines**: ~30

##### `get_rank_permissions(rank: str) -> list[str]`
- **Purpose**: Get permissions for rank
- **Tables**: None (LuckPerms API)
- **Feature**: Permission checking
- **Lines**: ~15

**Subtotal: 3 methods, ~65 lines**

---

**Integration Layer Total: 17 methods, ~340 lines**

---

## Final Summary

### Function Count by Layer

| Layer | Functions/Methods/Endpoints | Lines of Code |
|-------|----------------------------|---------------|
| **Core** | 21 | ~145 |
| **Domain** | 23 | ~340 |
| **Data** | 22 | ~128 |
| **Agent** | 36 | ~1058 |
| **API** | 46 | ~955 |
| **CLI** | 30 | ~570 |
| **Integration** | 17 | ~340 |
| **TOTAL** | **195** | **~3536** |

### Comparison to V1.0

| Metric | V1.0 | V2.0 | Reduction |
|--------|------|------|-----------|
| **Functions** | 979 | 195 | **-80%** |
| **Lines of Code** | ~30,000 | ~3,536 | **-88%** |
| **Database Tables** | 93 | 55 | **-41%** |
| **Agent Implementations** | 3 | 1 | **-67%** |
| **DB Connection Points** | 12 | 1 | **-92%** |
| **Update Checkers** | 4 | 1 | **-75%** |
| **File Watchers** | 3 | 1 | **-67%** |

### Key Architectural Wins

1. **Single Agent** - One unified agent replacing 3 separate implementations
2. **Repository Pattern** - All database access through 6 repositories (vs. 12+ scattered connections)
3. **Unit of Work** - Transactional integrity across all operations
4. **Unified File Watcher** - Single generic watcher vs. 3 duplicates
5. **Polymorphic Scoping** - One `tag_assignments` table vs. 8 separate tag tables
6. **Service Layer** - Business logic separated from data access
7. **Dependency Injection** - Loose coupling throughout

### Feature Mapping

| Feature | Functions | Key Tables |
|---------|-----------|-----------|
| **Instance Discovery** | 6 | `instances`, `discovery_runs`, `discovery_items` |
| **Plugin Management** | 12 | `plugins`, `instance_plugins`, `plugin_versions` |
| **Config Management** | 15 | `config_rules`, `config_values`, `config_variances` |
| **Deployment** | 13 | `deployment_queue`, `deployment_history`, `deployment_changes` |
| **Update Checking** | 9 | `plugin_update_sources`, `plugin_versions`, `plugin_update_queue` |
| **Variance Detection** | 7 | `config_variances`, `server_properties_variances` |
| **Monitoring** | 8 | `agent_heartbeats`, `system_metrics`, `audit_log` |
| **Tagging** | 5 | `meta_tags`, `tag_assignments`, `tag_relationships` |
| **Backup/Restore** | 4 | `backups`, `config_file_metadata` |
| **Approval Workflow** | 6 | `approval_requests`, `approval_votes` |
| **API** | 46 | All (REST interface) |
| **CLI** | 30 | All (CLI interface) |
| **Integrations** | 17 | External APIs (Modrinth, Hangar, GitHub, Discord, LuckPerms) |

---

## Implementation Notes

### Function Complexity Guidelines

- **Simple functions** (<15 lines): CRUD operations, getters, validators
- **Medium functions** (15-30 lines): Business logic, API endpoints, parsing
- **Complex functions** (30-60 lines): Discovery scans, deployment execution, integrations
- **No function >60 lines**: Break into smaller helper functions

### Testing Strategy

- **Unit tests**: All domain services, repositories (100% coverage target)
- **Integration tests**: API endpoints, agent workflows (80% coverage target)
- **E2E tests**: Full deployment workflows (critical paths only)

### Migration Strategy

Each function maps to V1.0 functions as follows:

1. **Direct ports** (~20%): Functions that work as-is
2. **Refactored** (~50%): Same logic, better structure
3. **Consolidated** (~20%): Multiple V1 functions → 1 V2 function
4. **New** (~10%): Previously missing functionality

---

**Function mapping complete. Ready for feature list creation.**
