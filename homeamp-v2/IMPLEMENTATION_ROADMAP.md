# HomeAMP V2.0 - Implementation Roadmap

**Version**: 2.0.0  
**Timeline**: 12 weeks (3 months)  
**Start Date**: December 1, 2025  
**Target Release**: February 28, 2026

---

## Overview

This roadmap defines the 12-week development plan for rebuilding HomeAMP from 30,000 lines of duplicated code to 3,536 lines of clean, architected code. The plan is divided into 6 two-week sprints, each delivering working functionality with full test coverage.

### Success Criteria
- ✅ All V1.0 features migrated
- ✅ 80%+ test coverage overall
- ✅ <100ms API response time (p95)
- ✅ <10s agent discovery cycle
- ✅ Zero critical bugs in production
- ✅ Complete documentation

### Risk Mitigation Strategy
- **Parallel Deployment**: Run V1.0 and V2.0 side-by-side initially
- **Data Migration**: Test with V1.0 database copies, not production
- **Rollback Plan**: Keep V1.0 deployable for 4 weeks post-launch
- **External Dependencies**: Mock all external APIs for testing

---

## Sprint 1: Foundation (Weeks 1-2)
**Dates**: Dec 1-14, 2025  
**Goal**: Project infrastructure and core layer

### Week 1: Project Setup
**Focus**: Repository, tooling, database initialization

#### Tasks
- [ ] Initialize Git repository
- [ ] Create directory structure (src/, tests/, migrations/, config/, scripts/, docs/)
- [ ] Configure tooling:
  - [ ] Black (line length 120)
  - [ ] Pylint
  - [ ] pytest + pytest-cov
  - [ ] pre-commit hooks
- [ ] Set up virtual environment (Python 3.11+)
- [ ] Install dependencies:
  - [ ] FastAPI, Uvicorn
  - [ ] SQLAlchemy 2.0
  - [ ] Alembic
  - [ ] Pydantic V2
  - [ ] Typer
  - [ ] pytest, pytest-asyncio, pytest-cov
- [ ] Configure MariaDB connection (localhost:3369)
- [ ] Create `pyproject.toml` with all tool configs
- [ ] Set up GitHub Actions CI/CD (lint, test, coverage)

**Deliverable**: Working development environment, CI/CD passing

---

### Week 2: Core Layer
**Focus**: Database, config, logging, exceptions

#### Tasks
- [ ] Implement `src/core/database.py`:
  - [ ] `get_engine()` - Create SQLAlchemy engine with pooling
  - [ ] `get_session()` - Dependency injection for sessions
  - [ ] `init_db()` - Initialize database connection
- [ ] Implement `src/core/config.py`:
  - [ ] Load settings from environment variables
  - [ ] Pydantic Settings model
  - [ ] Support `.env` files
- [ ] Implement `src/core/logging.py`:
  - [ ] Structured logging (JSON format)
  - [ ] Log to file + console
  - [ ] Audit logging helper
- [ ] Implement `src/core/exceptions.py`:
  - [ ] 12 custom exception classes
  - [ ] HTTP exception mapping
- [ ] Write unit tests (100% coverage target)

**Deliverable**: Core layer complete with tests passing

**Testing Checklist**:
- ✅ Database connection succeeds
- ✅ Connection pooling works (max 10 connections)
- ✅ Settings load from .env
- ✅ Logs written to file
- ✅ Exceptions raise correctly

---

## Sprint 2: Data Layer (Weeks 3-4)
**Dates**: Dec 15-28, 2025  
**Goal**: SQLAlchemy models, repositories, migrations

### Week 3: Database Models
**Focus**: 55 SQLAlchemy models

#### Tasks
- [ ] Create `src/data/models/` directory
- [ ] Implement models by category:
  - [ ] Infrastructure (6 models): Instance, InstanceGroup, InstanceGroupMember, MetaTag, TagAssignment, TagRelationship
  - [ ] Plugin Management (6 models): Plugin, InstancePlugin, PluginVersion, PluginUpdateQueue, PluginUpdateSource, PluginMigration
  - [ ] Datapack Management (5 models): Datapack, InstanceDatapack, DatapackVersion, DatapackDeploymentQueue, DatapackUpdateSource
  - [ ] Configuration (6 models): ConfigRule, ConfigValue, ConfigVariance, ConfigChange, ConfigVariable, ConfigFileMetadata
  - [ ] Server Properties (2 models): ServerProperty, ServerPropertyVariance
  - [ ] Deployment (6 models): DeploymentQueue, DeploymentHistory, DeploymentChange, DeploymentLog, ApprovalRequest, ApprovalVote
  - [ ] World/Region/Rank (8 models): World, WorldGroup, WorldGroupMember, Region, RegionGroup, RegionGroupMember, Rank, PlayerRank
  - [ ] Players (3 models): Player, PlayerConfigOverride, PlayerSession
  - [ ] Monitoring (8 models): DiscoveryRun, DiscoveryItem, AgentHeartbeat, SystemMetric, AuditLog, NotificationLog, ScheduledTask, WebhookEvent
  - [ ] Advanced (3 models): FeatureFlag, APIKey, Backup
- [ ] Define all relationships (ForeignKey, relationship())
- [ ] Add indexes for performance
- [ ] Create Alembic migration scripts

**Deliverable**: All 55 models defined, migrations generated

**Testing Checklist**:
- ✅ All models create tables successfully
- ✅ Relationships work bidirectionally
- ✅ Indexes created correctly
- ✅ Migrations apply cleanly

---

### Week 4: Repositories & Unit of Work
**Focus**: Data access layer

#### Tasks
- [ ] Implement `src/data/repositories/base_repository.py`:
  - [ ] `get_by_id()`, `get_all()`, `create()`, `update()`, `delete()`, `exists()`
- [ ] Implement specialized repositories:
  - [ ] `InstanceRepository` (4 custom methods + 6 base)
  - [ ] `PluginRepository` (3 custom methods + 6 base)
  - [ ] `ConfigRepository` (2 custom methods + 6 base)
  - [ ] `DeploymentRepository` (3 custom methods + 6 base)
  - [ ] `MonitoringRepository` (2 custom methods + 6 base)
- [ ] Implement `src/data/unit_of_work.py`:
  - [ ] `begin()`, `commit()`, `rollback()`, `close()`
  - [ ] Context manager support
- [ ] Write unit tests with in-memory SQLite

**Deliverable**: Complete data access layer, 100% test coverage

**Testing Checklist**:
- ✅ CRUD operations work for all repositories
- ✅ Unit of Work commits/rolls back correctly
- ✅ Relationships queried efficiently
- ✅ No N+1 query issues

---

## Sprint 3: Domain Layer (Weeks 5-6)
**Dates**: Dec 29, 2025 - Jan 11, 2026  
**Goal**: Business logic services

### Week 5: Core Services
**Focus**: Instance, Plugin, Config services

#### Tasks
- [ ] Implement `src/domain/instance_service.py`:
  - [ ] `validate_instance()` - Check instance validity
  - [ ] `detect_platform()` - Detect Paper/Spigot/Purpur
  - [ ] `get_instance_status()` - Check if running
- [ ] Implement `src/domain/plugin_service.py`:
  - [ ] `parse_plugin_metadata()` - Parse plugin.yml
  - [ ] `calculate_hash()` - SHA256 hash of JAR
  - [ ] `compare_versions()` - Semantic version comparison
  - [ ] `check_compatibility()` - MC version compatibility
- [ ] Implement `src/domain/config_service.py`:
  - [ ] `parse_yaml()` - Parse YAML configs
  - [ ] `parse_json()` - Parse JSON configs
  - [ ] `parse_properties()` - Parse .properties files
  - [ ] `apply_variables()` - Template variable substitution
  - [ ] `validate_config()` - Validate against rules
- [ ] Write unit tests (100% coverage)

**Deliverable**: Core domain services with business logic

**Testing Checklist**:
- ✅ Platform detection works for Paper/Spigot/Purpur
- ✅ Plugin metadata parsed correctly
- ✅ Config parsing handles all formats (YAML/JSON/properties)
- ✅ Variable substitution works with scope hierarchy
- ✅ Version comparison is accurate

---

### Week 6: Variance & Update Services
**Focus**: Drift detection, update checking

#### Tasks
- [ ] Implement `src/domain/variance_service.py`:
  - [ ] `detect_config_variance()` - Compare config to rules
  - [ ] `calculate_severity()` - Severity scoring (0-100)
  - [ ] `auto_resolve_variance()` - Auto-fix safe variances
- [ ] Implement `src/domain/update_service.py`:
  - [ ] `check_modrinth()` - Check Modrinth API
  - [ ] `check_hangar()` - Check Hangar API
  - [ ] `check_github()` - Check GitHub Releases
  - [ ] `check_spigot()` - Scrape SpigotMC (fallback)
  - [ ] `queue_update()` - Add to update queue
- [ ] Write unit tests with mocked APIs

**Deliverable**: Variance detection and update checking

**Testing Checklist**:
- ✅ Variance severity calculated correctly
- ✅ Auto-resolution only fixes safe variances
- ✅ Update checking handles all sources (Modrinth/Hangar/GitHub/Spigot)
- ✅ API rate limits respected
- ✅ Failed API calls retry with exponential backoff

---

## Sprint 4: Agent Layer (Weeks 7-8)
**Dates**: Jan 12-25, 2026  
**Goal**: Unified agent with monitoring

### Week 7: Discovery & Scanning
**Focus**: Discovery engine, config scanner

#### Tasks
- [ ] Implement `src/agent/discovery.py`:
  - [ ] `discover_instances()` - Scan for AMP instances
  - [ ] `discover_plugins()` - Scan plugins folder
  - [ ] `discover_datapacks()` - Scan world/datapacks
  - [ ] `discover_worlds()` - Scan for world folders
  - [ ] `discover_regions()` - Scan WorldGuard regions
  - [ ] `save_discoveries()` - Save to discovery_runs table
- [ ] Implement `src/agent/config_scanner.py`:
  - [ ] `scan_config_files()` - Find all config files
  - [ ] `parse_configs()` - Parse YAML/JSON/properties
  - [ ] `calculate_hashes()` - SHA256 for change detection
  - [ ] `save_config_values()` - Save to database
- [ ] Write integration tests with test fixtures

**Deliverable**: Working discovery engine

**Testing Checklist**:
- ✅ Discovers all instances correctly
- ✅ Plugin metadata extracted accurately
- ✅ Config files parsed without errors
- ✅ Hashes calculated consistently
- ✅ Discovery runs tracked in database

---

### Week 8: Variance Detection & Agent Core
**Focus**: Drift detection, agent orchestration

#### Tasks
- [ ] Implement `src/agent/variance_detector.py`:
  - [ ] `detect_all_variances()` - Run variance detection
  - [ ] `compare_configs()` - Compare to rules
  - [ ] `flag_critical_variances()` - Identify critical drift
  - [ ] `create_variance_records()` - Save to database
- [ ] Implement `src/agent/update_checker.py`:
  - [ ] `check_all_updates()` - Check all sources
  - [ ] `prioritize_updates()` - Critical updates first
  - [ ] `queue_updates()` - Add to deployment queue
  - [ ] `notify_updates()` - Send notifications
- [ ] Implement `src/agent/file_watcher.py`:
  - [ ] `watch_directory()` - Monitor file changes
  - [ ] `on_file_changed()` - Trigger rescan
  - [ ] `debounce_events()` - Avoid spam
  - [ ] Generic watcher (replaces 3 V1.0 watchers)
- [ ] Implement `src/agent/agent.py`:
  - [ ] `run_cycle()` - Main agent loop
  - [ ] `send_heartbeat()` - Update agent_heartbeats
  - [ ] `execute_scheduled_tasks()` - Run scheduled jobs
  - [ ] `shutdown_gracefully()` - Clean shutdown

**Deliverable**: Unified agent running autonomously

**Testing Checklist**:
- ✅ Agent cycle completes in <10 seconds
- ✅ Variances detected accurately
- ✅ Updates queued with correct priority
- ✅ Heartbeats sent every 60 seconds
- ✅ Graceful shutdown works

---

## Sprint 5: Deployment & Backup (Weeks 9-10)
**Dates**: Jan 26 - Feb 8, 2026  
**Goal**: Deployment execution, backup system

### Week 9: Deployment Executor
**Focus**: Atomic deployments with rollback

#### Tasks
- [ ] Implement `src/agent/deployment_executor.py`:
  - [ ] `execute_deployment()` - Execute from queue
  - [ ] `backup_before_deploy()` - Pre-deployment backup
  - [ ] `download_artifact()` - Download JAR/datapack
  - [ ] `verify_integrity()` - SHA256 verification
  - [ ] `deploy_changes()` - Apply changes atomically
  - [ ] `rollback_deployment()` - Restore from backup
  - [ ] `log_deployment()` - Save to deployment_history
- [ ] Implement approval workflow:
  - [ ] `check_approval_status()` - Verify approvals
  - [ ] `count_votes()` - Tally approval votes
  - [ ] `enforce_approval_rules()` - Require N approvers
- [ ] Write integration tests with rollback scenarios

**Deliverable**: Working deployment system with rollback

**Testing Checklist**:
- ✅ Deployments execute atomically
- ✅ Rollback restores exact previous state
- ✅ Approval workflow enforced
- ✅ Failed deployments don't break instances
- ✅ Deployment logs complete and accurate

---

### Week 10: Backup Manager
**Focus**: Automated backups, restoration

#### Tasks
- [ ] Implement `src/agent/backup_manager.py`:
  - [ ] `create_backup()` - Create backup archive
  - [ ] `restore_backup()` - Restore from archive
  - [ ] `verify_backup()` - Integrity check
  - [ ] `cleanup_old_backups()` - Delete expired backups
- [ ] Implement backup strategies:
  - [ ] Pre-deployment backups (automatic)
  - [ ] Scheduled backups (daily/weekly)
  - [ ] Manual backups (on-demand)
  - [ ] Retention policies (30 days, 10 backups max)
- [ ] Write integration tests with backup/restore cycles

**Deliverable**: Complete backup/restore system

**Testing Checklist**:
- ✅ Backups created successfully
- ✅ Restoration works correctly
- ✅ Integrity verification detects corruption
- ✅ Old backups cleaned up automatically
- ✅ Backup metadata tracked in database

---

## Sprint 6: API/CLI & Integration (Weeks 11-12)
**Dates**: Feb 9-22, 2026  
**Goal**: User interfaces, external integrations

### Week 11: FastAPI & CLI
**Focus**: REST API and command-line interface

#### Tasks
- [ ] Implement `src/api/main.py`:
  - [ ] Configure FastAPI app
  - [ ] Enable CORS
  - [ ] Add exception handlers
  - [ ] Add dependency injection
- [ ] Implement API routes (46 endpoints total):
  - [ ] `src/api/routes/instances.py` (8 endpoints)
  - [ ] `src/api/routes/plugins.py` (6 endpoints)
  - [ ] `src/api/routes/configs.py` (8 endpoints)
  - [ ] `src/api/routes/deployments.py` (8 endpoints)
  - [ ] `src/api/routes/tags.py` (5 endpoints)
  - [ ] `src/api/routes/monitoring.py` (5 endpoints)
  - [ ] `src/api/routes/dashboard.py` (3 endpoints)
  - [ ] `src/api/routes/auth.py` (3 endpoints)
- [ ] Implement `src/cli/main.py` with Typer
- [ ] Implement CLI commands (30 commands total):
  - [ ] `src/cli/instance_commands.py` (4 commands)
  - [ ] `src/cli/config_commands.py` (4 commands)
  - [ ] `src/cli/deployment_commands.py` (5 commands)
  - [ ] `src/cli/plugin_commands.py` (4 commands)
  - [ ] `src/cli/agent_commands.py` (4 commands)
  - [ ] `src/cli/backup_commands.py` (4 commands)
  - [ ] `src/cli/tag_commands.py` (5 commands)
- [ ] Write API integration tests (80% coverage)

**Deliverable**: Complete API and CLI

**Testing Checklist**:
- ✅ All 46 API endpoints respond correctly
- ✅ API response time <100ms (p95)
- ✅ All 30 CLI commands work
- ✅ Authentication enforced
- ✅ Error handling returns proper HTTP codes

---

### Week 12: External Integrations & Polish
**Focus**: Modrinth/Hangar/GitHub/Discord

#### Tasks
- [ ] Implement `src/integrations/modrinth.py`:
  - [ ] `search_projects()`, `get_versions()`, `download_version()`
- [ ] Implement `src/integrations/hangar.py`:
  - [ ] `search_projects()`, `get_versions()`, `download_version()`
- [ ] Implement `src/integrations/github.py`:
  - [ ] `get_releases()`, `download_asset()`
- [ ] Implement `src/integrations/discord.py`:
  - [ ] `send_notification()`, `send_embed()`
- [ ] Implement `src/integrations/luckperms.py`:
  - [ ] `sync_ranks()`, `get_player_ranks()`
- [ ] End-to-end testing:
  - [ ] Full discovery → variance detection → deployment cycle
  - [ ] API → agent → database workflow
  - [ ] Backup → restore → verify cycle
- [ ] Performance optimization:
  - [ ] Database query optimization (eliminate N+1)
  - [ ] API response caching (Redis optional)
  - [ ] Agent cycle optimization (<10s target)
- [ ] Documentation:
  - [ ] API documentation (OpenAPI/Swagger)
  - [ ] CLI help text
  - [ ] Installation guide
  - [ ] Migration guide (V1→V2)

**Deliverable**: Production-ready V2.0

**Testing Checklist**:
- ✅ All integrations work with real APIs
- ✅ E2E tests pass (critical paths)
- ✅ Performance targets met (<100ms API, <10s agent)
- ✅ Documentation complete
- ✅ Zero critical bugs

---

## Testing Strategy

### Test Pyramid
- **Unit Tests (60%)**: Fast, isolated, 100% domain layer coverage
- **Integration Tests (30%)**: Test layer interactions, 80% API coverage
- **E2E Tests (10%)**: Critical paths, real workflows

### Coverage Targets
| Layer | Target Coverage | Notes |
|-------|----------------|-------|
| Core | 100% | Database, config, logging |
| Data | 100% | Repositories, models |
| Domain | 100% | Business logic services |
| Agent | 80% | Agent workflows |
| API | 80% | REST endpoints |
| CLI | 70% | Command-line interface |
| Integrations | 60% | External APIs (mocked) |
| **Overall** | **80%+** | |

### Testing Tools
- **pytest**: Test runner
- **pytest-cov**: Coverage reporting
- **pytest-asyncio**: Async test support
- **httpx**: API testing
- **responses**: Mock HTTP requests
- **freezegun**: Time mocking
- **factory_boy**: Test data factories

---

## Migration Strategy

### Phase 1: Parallel Deployment (Week 13-14)
- Deploy V2.0 to separate server
- Run V1.0 and V2.0 side-by-side
- Compare outputs for consistency
- Route 10% of traffic to V2.0

### Phase 2: Data Migration (Week 15)
- Export V1.0 database (93 tables)
- Run migration scripts (93→55 tables)
- Validate data integrity
- Test with V2.0 agent

### Phase 3: Gradual Cutover (Week 16)
- Route 50% of traffic to V2.0
- Monitor error rates
- Compare performance metrics
- Increase to 100% if stable

### Phase 4: V1.0 Decommission (Week 17)
- Full cutover to V2.0
- Keep V1.0 deployable for 4 weeks (rollback safety)
- Archive V1.0 codebase
- Update documentation

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| External API changes | High | Medium | Mock APIs in tests, version pinning |
| Database migration failure | Critical | Low | Test with copies, rollback plan |
| Performance degradation | High | Medium | Load testing, profiling, caching |
| Agent crashes in production | Critical | Low | Heartbeat monitoring, auto-restart |
| Incomplete V1 feature parity | High | Medium | Feature checklist, acceptance tests |
| Developer knowledge gaps | Medium | High | Comprehensive documentation, code comments |

---

## Success Metrics

### Functional Metrics
- ✅ All 24 MVP features working
- ✅ V1.0 feature parity achieved
- ✅ Zero data loss during migration

### Non-Functional Metrics
- ✅ 80%+ test coverage
- ✅ <100ms API response time (p95)
- ✅ <10s agent discovery cycle
- ✅ Zero critical production bugs

### Code Quality Metrics
- ✅ All functions <50 lines
- ✅ All modules <500 lines
- ✅ Pylint score >9.0
- ✅ Zero code duplication (DRY violations)

---

## Post-Launch Roadmap (V2.1+)

### V2.1 Features (March-April 2026)
- Instance tagging advanced filters
- Config variable templating
- Variance auto-resolution
- Deployment metrics dashboard
- Backup restoration UI
- Datapack management
- Discord notifications
- CI/CD webhook integration
- Feature flags

### V2.2 Features (May-June 2026)
- World discovery and management
- Region tracking (WorldGuard)
- Rank management (LuckPerms)
- Advanced search and filtering
- API rate limiting enhancements

### Future Features (Backlog)
- World grouping
- Region-scoped config rules
- Rank-scoped config rules
- Gradual feature rollout

---

**Roadmap complete. Ready for implementation starting December 1, 2025.**
