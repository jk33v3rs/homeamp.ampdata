# HomeAMP Configuration Manager V2.0
**Clean-Slate Refactor with Architectural Excellence**

## Project Overview

This is a complete architectural refactor of the HomeAMP configuration management system. The V2.0 system maintains the proven conceptual framework from V1.0 but delivers it through clean, maintainable, and professional-grade architecture.

## Goals

1. **Reduce Complexity**: 93 tables → 55 tables (40% reduction)
2. **Eliminate Duplication**: Single implementation per feature (no 3x agents, 4x update checkers)
3. **Professional Architecture**: Repository pattern, dependency injection, proper layering
4. **Maintainability**: Clear separation of concerns, no circular dependencies
5. **Performance**: Connection pooling, caching, async operations
6. **Extensibility**: Plugin architecture for new features

## Key Improvements Over V1.0

| Aspect | V1.0 | V2.0 |
|--------|------|------|
| **Agent Implementations** | 3 (service, endpoint, production) | 1 (unified) |
| **Database Connections** | 12 scattered implementations | 1 connection pool |
| **Update Checkers** | 4 (manual, agent, cicd, lambda) | 1 unified service |
| **File Watchers** | 3 separate implementations | 1 base class + specializations |
| **Discovery Methods** | 5 different approaches | 1 canonical implementation |
| **Database Tables** | 93 tables | 55 tables |
| **Lines of Code** | ~30,000 | ~12,000 (est.) |
| **Code Duplication** | High | Minimal |
| **Architectural Layers** | Unclear | Clean separation |

## Architecture Philosophy

### Layer Structure
```
┌─────────────────────────────────────┐
│         Presentation Layer          │  FastAPI routes, CLI commands
│  (api/, cli/)                       │
├─────────────────────────────────────┤
│         Application Layer           │  Business orchestration
│  (agent/, services/)                │
├─────────────────────────────────────┤
│          Domain Layer               │  Business logic, models
│  (domain/)                          │
├─────────────────────────────────────┤
│        Data Access Layer            │  Repositories, queries
│  (data/)                            │
├─────────────────────────────────────┤
│       Infrastructure Layer          │  Database, logging, config
│  (core/)                            │
└─────────────────────────────────────┘
```

### Design Principles

1. **Dependency Inversion**: High-level modules don't depend on low-level modules
2. **Single Responsibility**: Each class/module has one reason to change
3. **Open/Closed**: Open for extension, closed for modification
4. **Repository Pattern**: Data access abstraction
5. **Service Layer**: Business logic isolated from infrastructure
6. **No Circular Dependencies**: Strict unidirectional flow

## Project Structure

```
homeamp-v2/
├── README.md                          # This file
├── SCHEMA_DESIGN.md                   # Complete 55-table schema design
├── FUNCTION_MAPPING.md                # All functions mapped to features/tables
├── FEATURE_LIST.md                    # Exhaustive feature specifications
├── IMPLEMENTATION_ROADMAP.md          # Phase-by-phase implementation plan
├── MIGRATION_GUIDE.md                 # V1 → V2 migration strategy
│
├── docs/                              # Additional documentation
│   ├── architecture/                  # Architecture decision records
│   ├── api/                           # API documentation
│   └── deployment/                    # Deployment guides
│
├── src/                               # Source code
│   ├── core/                          # Infrastructure layer
│   │   ├── __init__.py
│   │   ├── database.py                # Connection pool, session management
│   │   ├── settings.py                # Configuration loading
│   │   ├── logging.py                 # Structured logging
│   │   └── exceptions.py              # Custom exceptions
│   │
│   ├── domain/                        # Domain layer
│   │   ├── __init__.py
│   │   ├── models/                    # Domain models (NOT ORM models)
│   │   │   ├── instance.py            # Instance aggregate
│   │   │   ├── plugin.py              # Plugin entity
│   │   │   ├── config.py              # Configuration value objects
│   │   │   ├── deployment.py          # Deployment aggregate
│   │   │   └── world.py               # World/region/rank entities
│   │   │
│   │   └── services/                  # Domain services (business logic)
│   │       ├── discovery_service.py   # Instance/plugin discovery
│   │       ├── update_service.py      # Update checking (all sources)
│   │       ├── deployment_service.py  # Deployment orchestration
│   │       ├── drift_service.py       # Configuration drift detection
│   │       ├── approval_service.py    # Approval workflow
│   │       └── tagging_service.py     # Meta-tagging logic
│   │
│   ├── data/                          # Data access layer
│   │   ├── __init__.py
│   │   ├── models.py                  # SQLAlchemy ORM models
│   │   ├── repositories/              # Repository pattern
│   │   │   ├── base.py                # Base repository
│   │   │   ├── instance_repository.py
│   │   │   ├── plugin_repository.py
│   │   │   ├── config_repository.py
│   │   │   ├── deployment_repository.py
│   │   │   └── audit_repository.py
│   │   │
│   │   └── unit_of_work.py            # Transaction management
│   │
│   ├── agent/                         # Agent runtime (thin orchestration)
│   │   ├── __init__.py
│   │   ├── agent.py                   # Main agent class
│   │   ├── schedulers.py              # Scheduled task management
│   │   ├── watchers/                  # File system watchers
│   │   │   ├── base_watcher.py        # Base watcher class
│   │   │   ├── plugin_watcher.py      # Plugin folder watcher
│   │   │   ├── datapack_watcher.py    # Datapack folder watcher
│   │   │   └── tile_watcher.py        # Map tile watcher
│   │   │
│   │   └── handlers/                  # Event handlers
│   │       ├── discovery_handler.py
│   │       ├── update_handler.py
│   │       └── webhook_handler.py
│   │
│   ├── api/                           # FastAPI web interface
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application
│   │   ├── dependencies.py            # Shared dependencies (auth, db)
│   │   ├── routers/                   # Endpoint groups
│   │   │   ├── instances.py           # Instance management
│   │   │   ├── plugins.py             # Plugin endpoints
│   │   │   ├── configs.py             # Configuration endpoints
│   │   │   ├── deployments.py         # Deployment endpoints
│   │   │   ├── approvals.py           # Approval workflow
│   │   │   ├── monitoring.py          # Health/metrics
│   │   │   └── webhooks.py            # CI/CD webhooks
│   │   │
│   │   └── schemas/                   # Pydantic models
│   │       ├── instance.py
│   │       ├── plugin.py
│   │       ├── config.py
│   │       └── deployment.py
│   │
│   ├── cli/                           # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py                    # CLI entry point
│   │   └── commands/                  # Command modules
│   │       ├── agent.py               # Agent management
│   │       ├── deploy.py              # Deployment commands
│   │       ├── scan.py                # Manual scans
│   │       └── migrate.py             # Migration utilities
│   │
│   └── integrations/                  # External integrations
│       ├── __init__.py
│       ├── amp.py                     # AMP API integration
│       ├── modrinth.py                # Modrinth API
│       ├── hangar.py                  # Hangar API
│       ├── github.py                  # GitHub API
│       └── minio.py                   # MinIO/S3 storage
│
├── tests/                             # Test suite
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── e2e/                           # End-to-end tests
│
├── migrations/                        # Database migrations
│   ├── alembic.ini
│   └── versions/
│
├── config/                            # Configuration files
│   ├── agent.yaml.example
│   ├── api.yaml.example
│   └── database.yaml.example
│
├── scripts/                           # Utility scripts
│   ├── setup_dev.sh
│   ├── migrate_from_v1.py
│   └── seed_database.py
│
├── pyproject.toml                     # Python project config
├── requirements.txt                   # Python dependencies
└── docker-compose.yml                 # Development environment
```

## Documentation Files

This blueprint consists of several interconnected documents:

1. **SCHEMA_DESIGN.md** - Complete database schema (55 tables)
   - Table definitions with columns, indexes, foreign keys
   - Rationale for consolidation from 93 → 55 tables
   - Migration notes from V1 schema

2. **FUNCTION_MAPPING.md** - Every function mapped to purpose
   - Function name → Purpose → Tables accessed → Feature
   - Organized by layer (core, domain, data, agent, api)
   - Estimated line counts

3. **FEATURE_LIST.md** - Exhaustive feature specifications
   - User stories for each feature
   - Technical requirements
   - Dependencies and prerequisites
   - Testing criteria

4. **IMPLEMENTATION_ROADMAP.md** - Phase-by-phase plan
   - 12-week development timeline
   - Weekly milestones
   - Testing and deployment strategy
   - Risk mitigation

5. **MIGRATION_GUIDE.md** - V1 → V2 transition
   - Data migration scripts
   - Parallel deployment strategy
   - Rollback procedures
   - Validation tests

## Technology Stack

### Core Technologies
- **Python 3.11+**: Primary language
- **FastAPI**: Web framework (async, OpenAPI docs)
- **SQLAlchemy 2.0**: ORM and query builder
- **Alembic**: Database migrations
- **Pydantic V2**: Data validation and serialization
- **Typer**: CLI framework

### Database
- **MariaDB 10.11+**: Primary database
- **Redis**: Caching layer (optional)

### Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Code coverage
- **httpx**: Async HTTP client for API testing

### Development Tools
- **Black**: Code formatting
- **Ruff**: Linting (replaces Pylint + isort)
- **mypy**: Static type checking
- **pre-commit**: Git hooks

### Deployment
- **systemd**: Service management (Linux)
- **Docker**: Containerization (optional)
- **Nginx**: Reverse proxy

## Development Workflow

### Setup Development Environment
```bash
# Clone repository
cd homeamp-v2

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup pre-commit hooks
pre-commit install

# Initialize database
alembic upgrade head

# Seed test data
python scripts/seed_database.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

### Running Development Server
```bash
# Start API server
uvicorn src.api.main:app --reload --port 8000

# Start agent (separate terminal)
python -m src.cli.main agent start --config config/agent.yaml
```

## Key Design Decisions

### 1. Repository Pattern
**Why**: Abstracts data access, enables testing without database, allows swapping storage backends.

**Implementation**: Each aggregate root (Instance, Plugin, Deployment) has a repository.

### 2. Unit of Work
**Why**: Manages transactions across multiple repositories, ensures data consistency.

**Implementation**: Context manager that commits or rolls back all changes.

### 3. Domain-Driven Design
**Why**: Complex business logic needs clear organization separate from infrastructure.

**Implementation**: Domain models contain business rules, services orchestrate operations.

### 4. Dependency Injection
**Why**: Loose coupling, easier testing, flexible configuration.

**Implementation**: FastAPI dependencies, constructor injection in services.

### 5. SQLAlchemy 2.0 (not raw SQL)
**Why**: Type safety, query building, automatic migrations.

**Trade-off**: Slight performance overhead vs. maintainability gain.

### 6. Async/Await
**Why**: Better performance for I/O-bound operations (API calls, database queries).

**Implementation**: FastAPI endpoints and service methods are async.

## Success Criteria

### Functional Requirements
- ✅ All V1.0 features preserved
- ✅ Zero data loss during migration
- ✅ Backward-compatible API (where possible)
- ✅ Improved performance (< 100ms API response times)

### Non-Functional Requirements
- ✅ 80%+ test coverage
- ✅ < 10 seconds agent cycle time
- ✅ Handles 100+ instances per server
- ✅ < 1 hour full discovery scan

### Code Quality
- ✅ No circular dependencies
- ✅ All functions < 50 lines
- ✅ All modules < 500 lines
- ✅ Type hints on all public APIs
- ✅ Docstrings on all classes/functions

## Migration Strategy

### Phase 1: Parallel Development (Weeks 1-10)
- Build V2.0 alongside V1.0
- No changes to V1.0 (read-only)
- Share database (V2 writes to new tables)

### Phase 2: Testing (Weeks 11-12)
- Full feature parity verification
- Performance benchmarking
- Load testing

### Phase 3: Deployment (Week 13)
- Deploy V2.0 agent alongside V1.0 agent
- Switch API traffic to V2.0
- Monitor for 1 week

### Phase 4: Cutover (Week 14)
- Shut down V1.0 agent
- Migrate old tables to new schema
- Archive V1.0 codebase

### Phase 5: Cleanup (Week 15)
- Delete redundant V1 tables
- Remove V1 code
- Final documentation

## Next Steps

1. **Review SCHEMA_DESIGN.md** - Understand the 55-table structure
2. **Review FUNCTION_MAPPING.md** - See how functions map to features
3. **Review FEATURE_LIST.md** - Understand complete feature set
4. **Review IMPLEMENTATION_ROADMAP.md** - Understand the build plan
5. **Start Phase 1** - Core infrastructure (database, settings, logging)

## Questions & Decisions Needed

### Before Starting Implementation

- [ ] Confirm MariaDB version (10.11+ required for SQLAlchemy 2.0)
- [ ] Decide on caching strategy (Redis vs. in-memory)
- [ ] Confirm Python version (3.11+ for best async performance)
- [ ] Choose deployment method (systemd vs. Docker vs. both)
- [ ] Decide on authentication method (API keys vs. OAuth vs. none)

### During Implementation

- [ ] Define API versioning strategy (URL prefix vs. header)
- [ ] Decide on webhook authentication (shared secret vs. signatures)
- [ ] Choose file watcher library (watchdog vs. inotify)
- [ ] Define metric collection strategy (Prometheus vs. StatsD vs. custom)

## License & Attribution

Based on HomeAMP Configuration Manager V1.0 (2024-2025)
Refactored architecture by AI-assisted design (2025)

---

**Ready to build professional-grade infrastructure management software.**
