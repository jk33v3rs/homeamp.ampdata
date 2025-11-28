# Database Schema Design V2.0
**Consolidated 55-Table Architecture**

## Schema Overview

### Reduction Strategy: 93 → 55 Tables

| Category | V1.0 Tables | V2.0 Tables | Reduction | Strategy |
|----------|-------------|-------------|-----------|----------|
| **Infrastructure** | 8 | 6 | -2 | Merge tag tables |
| **Plugin Management** | 13 | 6 | -7 | Remove over-normalization |
| **Datapack Management** | 5 | 5 | 0 | Keep (appropriate) |
| **Configuration** | 15 | 6 | -9 | Consolidate variance/history |
| **Server Properties** | 3 | 2 | -1 | Merge variance tables |
| **Deployment** | 6 | 6 | 0 | Keep (appropriate) |
| **World/Region/Rank** | 17 | 8 | -9 | Polymorphic scoping |
| **Player Management** | 7 | 3 | -4 | Simplify, use LuckPerms |
| **Monitoring** | 10 | 8 | -2 | Consolidate health metrics |
| **Endpoint Config** | 3 | 2 | -1 | Merge tables |
| **Advanced Features** | 6 | 3 | -3 | Remove unused |
| **TOTAL** | **93** | **55** | **-38** | **41% reduction** |

---

## Complete Schema Definition

### 1. Infrastructure (6 tables)

#### 1.1 `instances`
**Purpose**: Core registry of all Minecraft server instances

```sql
CREATE TABLE instances (
    instance_id VARCHAR(64) PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    server_name VARCHAR(64) NOT NULL,          -- Physical server (hetzner-xeon, ovh-ryzen)
    platform ENUM('paper', 'fabric', 'neoforge', 'geyser', 'velocity') NOT NULL,
    minecraft_version VARCHAR(32),
    instance_path VARCHAR(512) NOT NULL,
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    metadata JSON,                              -- Flexible storage for instance-specific data
    
    INDEX idx_server (server_name),
    INDEX idx_platform (platform),
    INDEX idx_status (status),
    INDEX idx_last_seen (last_seen_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Merged `instance_meta_tags` relationships into separate junction table
- Added JSON metadata field for flexibility
- Removed redundant `amp_instance_id` (not used)

---

#### 1.2 `instance_groups`
**Purpose**: Logical grouping of instances (SMP, Creative, Test, etc.)

```sql
CREATE TABLE instance_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_name (group_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 1.3 `instance_group_members`
**Purpose**: Many-to-many relationship between instances and groups

```sql
CREATE TABLE instance_group_members (
    instance_id VARCHAR(64),
    group_id INT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (instance_id, group_id),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES instance_groups(group_id) ON DELETE CASCADE,
    
    INDEX idx_group (group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 1.4 `meta_tags`
**Purpose**: Reusable tags for categorization (e.g., "production", "modded", "public")

```sql
CREATE TABLE meta_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(128) NOT NULL UNIQUE,
    tag_category VARCHAR(64),                   -- Optional category (environment, access, purpose)
    color VARCHAR(7),                           -- Hex color for UI (#FF5733)
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_name (tag_name),
    INDEX idx_category (tag_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Removed `meta_tag_categories` table (category is now a column)
- Added color field for UI consistency

---

#### 1.5 `tag_assignments`
**Purpose**: Polymorphic tagging - assign tags to any entity type

```sql
CREATE TABLE tag_assignments (
    assignment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tag_id INT NOT NULL,
    entity_type ENUM('instance', 'plugin', 'world', 'region', 'rank', 'player') NOT NULL,
    entity_id VARCHAR(255) NOT NULL,            -- ID of the tagged entity
    assigned_by VARCHAR(64),                    -- User who assigned tag
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_tag_entity (tag_id, entity_type, entity_id),
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_tag (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `instance_tags`, `instance_meta_tags`, `world_tags`, `region_tags`, `rank_tags`, `player_tags`, `server_tags`, `group_tags`
- Polymorphic design reduces 8+ tables to 1

---

#### 1.6 `tag_relationships`
**Purpose**: Tag dependencies, conflicts, and hierarchy

```sql
CREATE TABLE tag_relationships (
    relationship_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_id INT NOT NULL,
    related_tag_id INT NOT NULL,
    relationship_type ENUM('depends_on', 'conflicts_with', 'parent_of') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_relationship (tag_id, related_tag_id, relationship_type),
    FOREIGN KEY (tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    FOREIGN KEY (related_tag_id) REFERENCES meta_tags(tag_id) ON DELETE CASCADE,
    
    INDEX idx_tag (tag_id),
    INDEX idx_related (related_tag_id),
    INDEX idx_type (relationship_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `tag_dependencies`, `tag_conflicts`, `tag_hierarchy`
- Single table with relationship_type discriminator

---

### 2. Plugin Management (6 tables)

#### 2.1 `plugins`
**Purpose**: Global plugin registry

```sql
CREATE TABLE plugins (
    plugin_id VARCHAR(128) PRIMARY KEY,         -- Normalized name (lowercase, no spaces)
    display_name VARCHAR(255) NOT NULL,         -- Actual plugin name
    description TEXT,
    author VARCHAR(255),
    website_url VARCHAR(512),
    documentation_url VARCHAR(512),
    current_stable_version VARCHAR(64),
    
    -- Update sources
    modrinth_id VARCHAR(128),
    hangar_slug VARCHAR(255),
    github_repo VARCHAR(255),                   -- Format: owner/repo
    spigot_id INT,
    jenkins_url VARCHAR(512),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_display_name (display_name),
    INDEX idx_modrinth (modrinth_id),
    INDEX idx_github (github_repo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **REMOVED**: `plugin_developers`, `plugin_developer_links` (consolidated into author field)
- **REMOVED**: `plugin_documentation_pages` (single URL field sufficient)
- **REMOVED**: `plugin_cicd_builds` (scope creep, not needed)

---

#### 2.2 `instance_plugins`
**Purpose**: Track which plugins are installed on which instances

```sql
CREATE TABLE instance_plugins (
    installation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    installed_version VARCHAR(64) NOT NULL,
    jar_filename VARCHAR(255) NOT NULL,
    jar_hash VARCHAR(64),                       -- SHA-256 hash
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_instance_plugin (instance_id, plugin_id),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_id),
    INDEX idx_version (installed_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 2.3 `plugin_versions`
**Purpose**: Track available versions and updates

```sql
CREATE TABLE plugin_versions (
    version_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(128) NOT NULL,
    version_number VARCHAR(64) NOT NULL,
    release_date TIMESTAMP,
    download_url VARCHAR(1024),
    changelog TEXT,
    is_prerelease BOOLEAN DEFAULT FALSE,
    minecraft_versions JSON,                    -- Array of supported MC versions
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_plugin_version (plugin_id, version_number),
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    INDEX idx_plugin (plugin_id),
    INDEX idx_release_date (release_date),
    INDEX idx_prerelease (is_prerelease)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **REMOVED**: `plugin_version_history` (duplicate of this table)
- Added minecraft_versions JSON field

---

#### 2.4 `plugin_update_queue`
**Purpose**: Queue of pending plugin updates

```sql
CREATE TABLE plugin_update_queue (
    queue_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    plugin_id VARCHAR(128) NOT NULL,
    from_version VARCHAR(64) NOT NULL,
    to_version VARCHAR(64) NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'deployed', 'failed') DEFAULT 'pending',
    priority INT DEFAULT 5,                     -- 1-10 (1=highest)
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_at TIMESTAMP NULL,
    notes TEXT,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    INDEX idx_status (status),
    INDEX idx_instance (instance_id),
    INDEX idx_priority (priority, queued_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 2.5 `plugin_update_sources`
**Purpose**: Track update check URLs and last check times

```sql
CREATE TABLE plugin_update_sources (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(128) NOT NULL,
    source_type ENUM('modrinth', 'hangar', 'github', 'spigot', 'jenkins', 'custom') NOT NULL,
    source_url VARCHAR(1024) NOT NULL,
    last_checked_at TIMESTAMP NULL,
    check_interval_hours INT DEFAULT 12,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    INDEX idx_plugin (plugin_id),
    INDEX idx_type (source_type),
    INDEX idx_next_check (last_checked_at, check_interval_hours, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 2.6 `plugin_migrations`
**Purpose**: Track config key renames/migrations during plugin updates

```sql
CREATE TABLE plugin_migrations (
    migration_id INT AUTO_INCREMENT PRIMARY KEY,
    plugin_id VARCHAR(128) NOT NULL,
    from_version VARCHAR(64) NOT NULL,
    to_version VARCHAR(64) NOT NULL,
    file_path VARCHAR(512),
    old_key VARCHAR(255) NOT NULL,
    new_key VARCHAR(255) NOT NULL,
    migration_type ENUM('rename', 'remove', 'transform') DEFAULT 'rename',
    transformation_rule TEXT,                   -- Lua/Python script for complex transforms
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id) ON DELETE CASCADE,
    
    INDEX idx_plugin_version (plugin_id, from_version, to_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Renamed from `config_key_migrations`
- Added transformation_rule for complex migrations

---

### 3. Datapack Management (5 tables)

#### 3.1 `datapacks`
**Purpose**: Global datapack registry

```sql
CREATE TABLE datapacks (
    datapack_id VARCHAR(128) PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    author VARCHAR(255),
    website_url VARCHAR(512),
    current_version VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_display_name (display_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 3.2 `instance_datapacks`
**Purpose**: Track datapacks installed in world folders

```sql
CREATE TABLE instance_datapacks (
    installation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    datapack_id VARCHAR(128) NOT NULL,
    world_path VARCHAR(512) NOT NULL,           -- e.g., "world", "world_nether"
    installed_version VARCHAR(64),
    file_hash VARCHAR(64),
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    
    INDEX idx_instance_world (instance_id, world_path),
    INDEX idx_datapack (datapack_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 3.3 `datapack_versions`
**Purpose**: Track available datapack versions

```sql
CREATE TABLE datapack_versions (
    version_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    datapack_id VARCHAR(128) NOT NULL,
    version_number VARCHAR(64) NOT NULL,
    release_date TIMESTAMP,
    download_url VARCHAR(1024),
    changelog TEXT,
    minecraft_versions JSON,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_datapack_version (datapack_id, version_number),
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    
    INDEX idx_datapack (datapack_id),
    INDEX idx_release_date (release_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 3.4 `datapack_deployment_queue`
**Purpose**: Queue for datapack deployments

```sql
CREATE TABLE datapack_deployment_queue (
    queue_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    world_path VARCHAR(512) NOT NULL,
    datapack_id VARCHAR(128) NOT NULL,
    target_version VARCHAR(64) NOT NULL,
    status ENUM('pending', 'deployed', 'failed') DEFAULT 'pending',
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_at TIMESTAMP NULL,
    notes TEXT,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    
    INDEX idx_status (status),
    INDEX idx_instance (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 3.5 `datapack_update_sources`
**Purpose**: Track datapack update sources

```sql
CREATE TABLE datapack_update_sources (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    datapack_id VARCHAR(128) NOT NULL,
    source_type ENUM('github', 'planetminecraft', 'custom') NOT NULL,
    source_url VARCHAR(1024) NOT NULL,
    last_checked_at TIMESTAMP NULL,
    check_interval_hours INT DEFAULT 24,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (datapack_id) REFERENCES datapacks(datapack_id) ON DELETE CASCADE,
    
    INDEX idx_datapack (datapack_id),
    INDEX idx_type (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

### 4. Configuration Management (6 tables)

#### 4.1 `config_rules`
**Purpose**: Define configuration rules and expected values

```sql
CREATE TABLE config_rules (
    rule_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    
    -- Scope (what does this rule apply to?)
    scope_type ENUM('global', 'instance', 'plugin', 'world', 'region', 'rank') NOT NULL,
    scope_id VARCHAR(255),                      -- NULL for global, specific ID otherwise
    
    -- Target (which config file/key?)
    plugin_name VARCHAR(255),                   -- NULL for server.properties
    file_path VARCHAR(512),                     -- Relative path within plugin folder
    config_key VARCHAR(255) NOT NULL,
    
    -- Expected value
    expected_value TEXT,
    value_type ENUM('string', 'int', 'float', 'boolean', 'list', 'json') DEFAULT 'string',
    
    -- Enforcement
    enforcement_level ENUM('required', 'recommended', 'optional') DEFAULT 'recommended',
    allow_override BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    
    INDEX idx_scope (scope_type, scope_id),
    INDEX idx_plugin (plugin_name),
    INDEX idx_key (config_key),
    INDEX idx_enforcement (enforcement_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `world_config_rules`, `rank_config_rules`, separate scope tables
- Polymorphic scope design
- Added value_type for proper validation

---

#### 4.2 `config_values`
**Purpose**: Store actual configuration values from scans

```sql
CREATE TABLE config_values (
    value_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    plugin_name VARCHAR(255),
    file_path VARCHAR(512),
    config_key VARCHAR(255) NOT NULL,
    config_value TEXT,
    value_type VARCHAR(32),
    file_hash VARCHAR(64),                      -- Hash of entire config file
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Track last verification
    last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_instance_plugin (instance_id, plugin_name),
    INDEX idx_key (config_key),
    INDEX idx_discovered (discovered_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Renamed from `instance_config_values`
- Added value_type for consistency

---

#### 4.3 `config_variances`
**Purpose**: Track configuration drift/variances from rules

```sql
CREATE TABLE config_variances (
    variance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    rule_id BIGINT,                             -- NULL if no rule defined
    plugin_name VARCHAR(255),
    file_path VARCHAR(512),
    config_key VARCHAR(255) NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    variance_type ENUM('missing_key', 'wrong_value', 'extra_key', 'missing_file') NOT NULL,
    severity ENUM('critical', 'high', 'medium', 'low') DEFAULT 'medium',
    
    -- Lifecycle
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    resolution_notes TEXT,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES config_rules(rule_id) ON DELETE SET NULL,
    
    INDEX idx_instance (instance_id),
    INDEX idx_severity (severity),
    INDEX idx_resolved (resolved_at),
    INDEX idx_detected (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `config_variance_cache`, `config_variance_detected`, `config_variances`
- Added severity and resolution tracking
- Single source of truth for variances

---

#### 4.4 `config_changes`
**Purpose**: Audit trail of all configuration changes

```sql
CREATE TABLE config_changes (
    change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    plugin_name VARCHAR(255),
    file_path VARCHAR(512),
    config_key VARCHAR(255) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    change_type ENUM('add', 'modify', 'remove') NOT NULL,
    
    -- Context
    changed_by VARCHAR(64),                     -- User or 'system'
    change_reason TEXT,
    deployment_id BIGINT,                       -- Link to deployment if applicable
    
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_instance (instance_id),
    INDEX idx_plugin (plugin_name),
    INDEX idx_key (config_key),
    INDEX idx_changed (changed_at),
    INDEX idx_deployment (deployment_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `config_change_history`, `config_history`, `config_rule_history`
- Renamed to `config_changes` for clarity
- Added deployment_id foreign key

---

#### 4.5 `config_variables`
**Purpose**: Template variables for configuration (e.g., ${SERVER_IP})

```sql
CREATE TABLE config_variables (
    variable_id INT AUTO_INCREMENT PRIMARY KEY,
    variable_name VARCHAR(128) NOT NULL UNIQUE,
    variable_value TEXT NOT NULL,
    description TEXT,
    scope_type ENUM('global', 'server', 'instance') DEFAULT 'global',
    scope_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_scope (scope_type, scope_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 4.6 `config_file_metadata`
**Purpose**: Track config file metadata for endpoint-managed configs

```sql
CREATE TABLE config_file_metadata (
    file_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    file_size INT,
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    backup_path VARCHAR(512),                   -- Path to latest backup
    is_managed BOOLEAN DEFAULT FALSE,           -- TRUE if managed by agent
    
    UNIQUE KEY uniq_instance_file (instance_id, file_path),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_instance (instance_id),
    INDEX idx_modified (last_modified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `endpoint_config_files`, `endpoint_config_backups`
- Backup path stored as column instead of separate table

---

### 5. Server Properties (2 tables)

#### 5.1 `server_properties`
**Purpose**: Track server.properties values

```sql
CREATE TABLE server_properties (
    property_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    property_key VARCHAR(255) NOT NULL,
    property_value TEXT,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_instance_property (instance_id, property_key),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_instance (instance_id),
    INDEX idx_key (property_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Renamed from `instance_server_properties`
- Simplified structure

---

#### 5.2 `server_properties_variances`
**Purpose**: Track server.properties drift

```sql
CREATE TABLE server_properties_variances (
    variance_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    property_key VARCHAR(255) NOT NULL,
    expected_value TEXT,
    actual_value TEXT,
    severity ENUM('critical', 'high', 'medium', 'low') DEFAULT 'medium',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_instance (instance_id),
    INDEX idx_severity (severity),
    INDEX idx_detected (detected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `server_properties_baselines` (baseline is now in config_rules)
- Mirrors structure of config_variances

---

### 6. Deployment (6 tables)

#### 6.1 `deployment_queue`
**Purpose**: Queue of pending deployments

```sql
CREATE TABLE deployment_queue (
    queue_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    deployment_type ENUM('config', 'plugin', 'datapack', 'batch') NOT NULL,
    target_instances JSON,                      -- Array of instance IDs
    payload JSON,                               -- Type-specific deployment data
    status ENUM('pending', 'approved', 'deploying', 'completed', 'failed') DEFAULT 'pending',
    priority INT DEFAULT 5,
    
    -- Lifecycle
    queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP NULL,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    
    -- Context
    queued_by VARCHAR(64),
    approved_by VARCHAR(64),
    notes TEXT,
    
    INDEX idx_status (status),
    INDEX idx_priority (priority, queued_at),
    INDEX idx_queued (queued_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Added JSON payload for flexible deployment types
- Streamlined status tracking

---

#### 6.2 `deployment_history`
**Purpose**: Historical record of all deployments

```sql
CREATE TABLE deployment_history (
    deployment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    queue_id BIGINT,                            -- Link to original queue item
    deployment_type ENUM('config', 'plugin', 'datapack', 'batch') NOT NULL,
    target_instances JSON,
    deployment_summary TEXT,
    status ENUM('success', 'partial', 'failed') NOT NULL,
    
    -- Timing
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    duration_seconds INT,
    
    -- Context
    deployed_by VARCHAR(64),
    notes TEXT,
    error_log TEXT,
    
    FOREIGN KEY (queue_id) REFERENCES deployment_queue(queue_id) ON DELETE SET NULL,
    
    INDEX idx_status (status),
    INDEX idx_started (started_at),
    INDEX idx_type (deployment_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Added duration tracking
- Linked to queue for traceability

---

#### 6.3 `deployment_changes`
**Purpose**: Detailed changes per deployment

```sql
CREATE TABLE deployment_changes (
    change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    deployment_id BIGINT NOT NULL,
    instance_id VARCHAR(64) NOT NULL,
    change_type ENUM('config_update', 'plugin_install', 'plugin_update', 'datapack_install') NOT NULL,
    target VARCHAR(512),                        -- Config key, plugin name, etc.
    old_value TEXT,
    new_value TEXT,
    status ENUM('success', 'failed', 'skipped') NOT NULL,
    error_message TEXT,
    
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_deployment (deployment_id),
    INDEX idx_instance (instance_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 6.4 `deployment_logs`
**Purpose**: Detailed execution logs for deployments

```sql
CREATE TABLE deployment_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    deployment_id BIGINT NOT NULL,
    instance_id VARCHAR(64),
    log_level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR') DEFAULT 'INFO',
    message TEXT NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (deployment_id) REFERENCES deployment_history(deployment_id) ON DELETE CASCADE,
    
    INDEX idx_deployment (deployment_id),
    INDEX idx_level (log_level),
    INDEX idx_logged (logged_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 6.5 `approval_requests`
**Purpose**: Approval workflow for deployments

```sql
CREATE TABLE approval_requests (
    request_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    queue_id BIGINT NOT NULL,
    request_type ENUM('deployment', 'plugin_update', 'config_change') NOT NULL,
    requested_by VARCHAR(64) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    required_approvals INT DEFAULT 1,
    status ENUM('pending', 'approved', 'rejected', 'expired') DEFAULT 'pending',
    expires_at TIMESTAMP,
    notes TEXT,
    
    FOREIGN KEY (queue_id) REFERENCES deployment_queue(queue_id) ON DELETE CASCADE,
    
    INDEX idx_status (status),
    INDEX idx_requested (requested_at),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Renamed from `change_approval_requests`
- Added expiration support

---

#### 6.6 `approval_votes`
**Purpose**: Track individual approval votes

```sql
CREATE TABLE approval_votes (
    vote_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    request_id BIGINT NOT NULL,
    voter VARCHAR(64) NOT NULL,
    vote ENUM('approve', 'reject') NOT NULL,
    comment TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_request_voter (request_id, voter),
    FOREIGN KEY (request_id) REFERENCES approval_requests(request_id) ON DELETE CASCADE,
    
    INDEX idx_request (request_id),
    INDEX idx_voter (voter),
    INDEX idx_voted (voted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

### 7. World/Region/Rank Management (8 tables)

#### 7.1 `worlds`
**Purpose**: Minecraft world tracking

```sql
CREATE TABLE worlds (
    world_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    world_name VARCHAR(255) NOT NULL,           -- Folder name (world, world_nether, etc.)
    display_name VARCHAR(255),
    world_type ENUM('overworld', 'nether', 'end', 'custom') DEFAULT 'overworld',
    seed BIGINT,
    game_mode ENUM('survival', 'creative', 'adventure', 'spectator'),
    difficulty ENUM('peaceful', 'easy', 'normal', 'hard'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_instance_world (instance_id, world_name),
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_instance (instance_id),
    INDEX idx_type (world_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Simplified from V1 (removed unused fields)
- Added world_type for clarity

---

#### 7.2 `world_groups`
**Purpose**: Group worlds together (e.g., all survival worlds)

```sql
CREATE TABLE world_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_name (group_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 7.3 `world_group_members`
**Purpose**: Many-to-many world grouping

```sql
CREATE TABLE world_group_members (
    world_id BIGINT,
    group_id INT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (world_id, group_id),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES world_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 7.4 `regions`
**Purpose**: WorldGuard/GriefPrevention regions

```sql
CREATE TABLE regions (
    region_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    world_id BIGINT NOT NULL,
    region_name VARCHAR(255) NOT NULL,
    region_type ENUM('worldguard', 'griefprevention', 'towny', 'custom'),
    owner VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uniq_world_region (world_id, region_name),
    FOREIGN KEY (world_id) REFERENCES worlds(world_id) ON DELETE CASCADE,
    
    INDEX idx_world (world_id),
    INDEX idx_owner (owner)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: Simplified structure

---

#### 7.5 `region_groups`
**Purpose**: Group regions (e.g., all spawn regions)

```sql
CREATE TABLE region_groups (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(128) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 7.6 `region_group_members`
**Purpose**: Many-to-many region grouping

```sql
CREATE TABLE region_group_members (
    region_id BIGINT,
    group_id INT,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (region_id, group_id),
    FOREIGN KEY (region_id) REFERENCES regions(region_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES region_groups(group_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 7.7 `ranks`
**Purpose**: LuckPerms rank definitions

```sql
CREATE TABLE ranks (
    rank_id INT AUTO_INCREMENT PRIMARY KEY,
    rank_name VARCHAR(128) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    priority INT DEFAULT 0,                     -- Higher = more important
    parent_rank_id INT,                         -- For rank hierarchy
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_rank_id) REFERENCES ranks(rank_id) ON DELETE SET NULL,
    
    INDEX idx_priority (priority),
    INDEX idx_parent (parent_rank_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Renamed from `rank_definitions`
- **REMOVED**: `rank_subranks`, `player_subrank_progress` (over-engineered, LuckPerms handles this)

---

#### 7.8 `player_ranks`
**Purpose**: Track player rank assignments

```sql
CREATE TABLE player_ranks (
    assignment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    player_uuid VARCHAR(36) NOT NULL,
    rank_id INT NOT NULL,
    instance_id VARCHAR(64),                    -- NULL for global rank
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,                  -- NULL for permanent
    
    FOREIGN KEY (rank_id) REFERENCES ranks(rank_id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_player (player_uuid),
    INDEX idx_rank (rank_id),
    INDEX idx_instance (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: Simplified (LuckPerms is source of truth, this is cache)

---

### 8. Player Management (3 tables)

#### 8.1 `players`
**Purpose**: Player registry (minimal - LuckPerms is source of truth)

```sql
CREATE TABLE players (
    player_uuid VARCHAR(36) PRIMARY KEY,
    player_name VARCHAR(16) NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_name (player_name),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **REMOVED**: `player_role_categories`, `player_roles`, `player_role_assignments` (use LuckPerms)
- Minimal table for reference only

---

#### 8.2 `player_config_overrides`
**Purpose**: Player-specific configuration overrides

```sql
CREATE TABLE player_config_overrides (
    override_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    player_uuid VARCHAR(36) NOT NULL,
    instance_id VARCHAR(64),
    plugin_name VARCHAR(255),
    config_key VARCHAR(255) NOT NULL,
    override_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(64),
    notes TEXT,
    
    FOREIGN KEY (player_uuid) REFERENCES players(player_uuid) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_player (player_uuid),
    INDEX idx_instance (instance_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: Simplified (only essential overrides)

---

#### 8.3 `player_sessions`
**Purpose**: Track player login sessions (for analytics)

```sql
CREATE TABLE player_sessions (
    session_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    player_uuid VARCHAR(36) NOT NULL,
    instance_id VARCHAR(64) NOT NULL,
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_at TIMESTAMP NULL,
    duration_minutes INT,
    
    FOREIGN KEY (player_uuid) REFERENCES players(player_uuid) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_player (player_uuid),
    INDEX idx_instance (instance_id),
    INDEX idx_login (login_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: New table for analytics (optional feature)

---

### 9. Monitoring & Operations (8 tables)

#### 9.1 `discovery_runs`
**Purpose**: Track agent discovery scan runs

```sql
CREATE TABLE discovery_runs (
    run_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) NOT NULL,
    run_type ENUM('full', 'incremental', 'manual') DEFAULT 'incremental',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    duration_seconds INT,
    instances_discovered INT DEFAULT 0,
    plugins_discovered INT DEFAULT 0,
    errors_count INT DEFAULT 0,
    status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    
    INDEX idx_server (server_name),
    INDEX idx_started (started_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 9.2 `discovery_items`
**Purpose**: Individual items discovered in each run

```sql
CREATE TABLE discovery_items (
    item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    run_id BIGINT NOT NULL,
    item_type ENUM('instance', 'plugin', 'datapack', 'world') NOT NULL,
    item_identifier VARCHAR(512) NOT NULL,
    action_taken ENUM('new', 'updated', 'unchanged', 'removed') NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (run_id) REFERENCES discovery_runs(run_id) ON DELETE CASCADE,
    
    INDEX idx_run (run_id),
    INDEX idx_type (item_type),
    INDEX idx_action (action_taken)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 9.3 `agent_heartbeats`
**Purpose**: Track agent health/status

```sql
CREATE TABLE agent_heartbeats (
    heartbeat_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) NOT_ NULL,
    agent_version VARCHAR(32),
    status ENUM('healthy', 'degraded', 'error') DEFAULT 'healthy',
    uptime_seconds BIGINT,
    cpu_percent DECIMAL(5,2),
    memory_mb INT,
    last_discovery_run TIMESTAMP NULL,
    last_update_check TIMESTAMP NULL,
    heartbeat_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_server (server_name),
    INDEX idx_heartbeat (heartbeat_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 9.4 `system_metrics`
**Purpose**: System performance metrics

```sql
CREATE TABLE system_metrics (
    metric_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    server_name VARCHAR(64) NOT NULL,
    metric_type VARCHAR(64) NOT NULL,           -- cpu_usage, memory_usage, disk_usage, etc.
    metric_value DECIMAL(10,2) NOT NULL,
    unit VARCHAR(32),                           -- percent, MB, GB, etc.
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_server_type (server_name, metric_type),
    INDEX idx_recorded (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: `system_health_metrics` and other metric tables
- Generic metric storage

---

#### 9.5 `audit_log`
**Purpose**: Comprehensive audit trail of all actions

```sql
CREATE TABLE audit_log (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,            -- config_change, deployment, approval, etc.
    entity_type VARCHAR(64),                    -- instance, plugin, config, etc.
    entity_id VARCHAR(255),
    action VARCHAR(64) NOT NULL,                -- create, update, delete, approve, etc.
    actor VARCHAR(64),                          -- User or 'system'
    details JSON,                               -- Event-specific details
    ip_address VARCHAR(45),
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_event_type (event_type),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_actor (actor),
    INDEX idx_occurred (occurred_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Added JSON details for flexibility
- Added IP address tracking

---

#### 9.6 `notification_log`
**Purpose**: Track sent notifications (Discord, email, etc.)

```sql
CREATE TABLE notification_log (
    notification_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    notification_type ENUM('discord', 'email', 'webhook') NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(512),
    message TEXT NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    status ENUM('pending', 'sent', 'failed') DEFAULT 'pending',
    sent_at TIMESTAMP NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_type (notification_type),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 9.7 `scheduled_tasks`
**Purpose**: Track scheduled background tasks

```sql
CREATE TABLE scheduled_tasks (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(128) NOT NULL UNIQUE,
    task_type VARCHAR(64) NOT NULL,             -- discovery, update_check, cleanup, etc.
    schedule_cron VARCHAR(128),                 -- Cron expression
    is_enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP NULL,
    next_run_at TIMESTAMP NULL,
    last_status ENUM('success', 'failed', 'skipped'),
    last_error TEXT,
    
    INDEX idx_enabled (is_enabled),
    INDEX idx_next_run (next_run_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: None, already appropriate

---

#### 9.8 `webhook_events`
**Purpose**: Track CI/CD webhook events

```sql
CREATE TABLE webhook_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source ENUM('github', 'modrinth', 'hangar', 'jenkins', 'custom') NOT NULL,
    event_type VARCHAR(64) NOT NULL,            -- release, push, build_complete, etc.
    payload JSON NOT NULL,
    signature VARCHAR(512),                     -- Webhook signature for verification
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_source (source),
    INDEX idx_processed (processed),
    INDEX idx_received (received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- Renamed from `cicd_webhook_events`
- Added signature field for security

---

### 10. Advanced Features (3 tables)

#### 10.1 `feature_flags`
**Purpose**: Runtime feature toggles

```sql
CREATE TABLE feature_flags (
    flag_id INT AUTO_INCREMENT PRIMARY KEY,
    flag_name VARCHAR(128) NOT NULL UNIQUE,
    is_enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INT DEFAULT 100,         -- Gradual rollout (0-100)
    enabled_for JSON,                           -- Array of instance IDs or user IDs
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- New table (replaces hardcoded feature flags)

---

#### 10.2 `api_keys`
**Purpose**: API authentication keys

```sql
CREATE TABLE api_keys (
    key_id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(128) NOT NULL,
    key_hash VARCHAR(128) NOT NULL UNIQUE,      -- Hashed API key
    key_prefix VARCHAR(16),                     -- First 8 chars for identification
    permissions JSON,                           -- Array of allowed operations
    expires_at TIMESTAMP NULL,
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_hash (key_hash),
    INDEX idx_active (is_active),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- New table for API authentication

---

#### 10.3 `backups`
**Purpose**: Track configuration backups

```sql
CREATE TABLE backups (
    backup_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(64) NOT NULL,
    backup_type ENUM('full', 'config_only', 'plugins_only') DEFAULT 'config_only',
    backup_path VARCHAR(1024) NOT NULL,
    backup_size_mb DECIMAL(10,2),
    file_count INT,
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,                  -- Auto-deletion date
    
    FOREIGN KEY (instance_id) REFERENCES instances(instance_id) ON DELETE CASCADE,
    
    INDEX idx_instance (instance_id),
    INDEX idx_type (backup_type),
    INDEX idx_created (created_at),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

**Changes from V1**: 
- **CONSOLIDATES**: Various backup tracking tables
- Added expiration for auto-cleanup

---

## Schema Statistics

### Table Count by Category
```
Infrastructure:        6 tables
Plugins:              6 tables
Datapacks:            5 tables
Configuration:        6 tables
Server Properties:    2 tables
Deployment:           6 tables
World/Region/Rank:    8 tables
Players:              3 tables
Monitoring:           8 tables
Advanced Features:    3 tables
------------------------
TOTAL:               55 tables
```

### Total Columns
- Estimated: ~450 columns (vs. ~650 in V1.0)
- Reduction: ~30% fewer columns

### Indexes
- Primary Keys: 55
- Foreign Keys: ~70
- Additional Indexes: ~120
- Total: ~245 indexes

---

## Migration Notes

### Critical Changes for Data Migration

1. **Tag System Consolidation**
   - Migrate `instance_tags`, `instance_meta_tags`, etc. → `tag_assignments`
   - Preserve all tag relationships

2. **Configuration Consolidation**
   - Merge `config_variance_cache`, `config_variance_detected`, `config_variances` → `config_variances`
   - Deduplicate entries

3. **Plugin Management**
   - Merge developer info into `plugins` table
   - Drop `plugin_cicd_builds` (not essential)

4. **Scope Tables**
   - Migrate `world_config_rules`, `rank_config_rules` → `config_rules` (with scope_type)
   - Update scope references

5. **Player Management**
   - Drop role tables (use LuckPerms)
   - Keep only config overrides

---

## Schema Validation Queries

```sql
-- Check all foreign keys are valid
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'asmp_config_v2'
  AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Check for orphaned records (example)
SELECT i.instance_id
FROM instances i
LEFT JOIN instance_plugins ip ON i.instance_id = ip.instance_id
WHERE ip.installation_id IS NULL;

-- Verify index coverage
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS indexed_columns
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'asmp_config_v2'
GROUP BY TABLE_NAME, INDEX_NAME;
```

---

## Next Steps

1. **Review this schema** - Ensure all requirements are met
2. **Generate migration scripts** - Alembic migrations from scratch
3. **Create SQLAlchemy models** - ORM models matching this schema
4. **Write data migration** - V1 → V2 data transfer script
5. **Test with sample data** - Verify relationships and constraints

---

**Schema design complete. Ready for implementation.**
