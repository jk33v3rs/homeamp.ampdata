"""
Web API for Configuration Management (Database-backed)

FastAPI REST API for viewing and managing configurations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from pathlib import Path

from ..database.db_access import ConfigDatabase

app = FastAPI(
    title="ArchiveSMP Configuration Manager",
    description="Database-backed config management for ArchiveSMP",
    version="2.0.0"
)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection (configured on startup)
db = None

@app.on_event("startup")
async def startup():
    """Initialize database connection"""
    global db
    try:
        db = ConfigDatabase(
            host='135.181.212.169',
            port=3369,
            user='sqlworkerSMP',
            password='SQLdb2024!'
        )
        db.connect()
        print("✓ Database connection established")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("API will run but database endpoints will not work")
        db = None

@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    if db:
        db.disconnect()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Check API and database health"""
    db_status = "connected" if db and db.conn else "disconnected"
    return {
        "status": "running",
        "database": db_status,
        "version": "2.0.0"
    }


# ============================================================================
# INSTANCE ENDPOINTS
# ============================================================================

@app.get("/api/instances")
async def get_instances(server: Optional[str] = None):
    """Get all instances, optionally filtered by server"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    if server:
        instances = db.get_instances_by_server(server)
    else:
        instances = db.get_all_instances()
    return {"instances": instances, "count": len(instances)}


@app.get("/api/instances/{instance_id}")
async def get_instance(instance_id: str):
    """Get single instance details"""
    instance = db.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
    
    # Get groups and tags
    groups = db.get_instance_groups_for_instance(instance_id)
    tags = db.get_instance_tags(instance_id)
    
    return {
        **instance,
        "groups": groups,
        "tags": tags
    }


# ============================================================================
# INSTANCE GROUP ENDPOINTS
# ============================================================================

@app.get("/api/groups")
async def get_groups():
    """Get all instance groups"""
    # Query groups with member counts
    db.cursor.execute("""
        SELECT ig.group_name, ig.group_type, ig.description,
               COUNT(igm.instance_id) as member_count
        FROM instance_groups ig
        LEFT JOIN instance_group_members igm ON ig.group_id = igm.group_id
        GROUP BY ig.group_id
        ORDER BY ig.group_type, ig.group_name
    """)
    groups = db.cursor.fetchall()
    return {"groups": groups}


@app.get("/api/groups/{group_name}")
async def get_group_members(group_name: str):
    """Get all instances in a group"""
    members = db.get_instances_in_group(group_name)
    return {"group_name": group_name, "members": members}


# ============================================================================
# CONFIG RESOLUTION ENDPOINTS
# ============================================================================

@app.get("/api/config/resolve")
async def resolve_config(
    instance_id: str,
    plugin: str,
    config_file: str,
    key: str
):
    """
    Resolve config value for instance using hierarchy
    
    Example: /api/config/resolve?instance_id=SMP201&plugin=LuckPerms&config_file=config.yml&key=server
    """
    try:
        value, priority, scope = db.resolve_config_value(
            instance_id, plugin, config_file, key
        )
        
        # Substitute variables
        if value:
            value = db.substitute_variables(value, instance_id)
        
        return {
            "instance_id": instance_id,
            "plugin": plugin,
            "config_file": config_file,
            "key": key,
            "value": value,
            "priority": priority,
            "scope": scope
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/config/rules")
async def get_config_rules(plugin: Optional[str] = None):
    """Get all config rules, optionally filtered by plugin"""
    rules = db.get_all_config_rules(plugin)
    return {"rules": rules, "count": len(rules)}


# ============================================================================
# VARIANCE ENDPOINTS
# ============================================================================

@app.get("/api/variance")
async def get_variance(classification: Optional[str] = None):
    """
    Get variance report
    
    classification: NONE, VARIABLE, META_TAG, INSTANCE, DRIFT
    """
    variance = db.get_variance_report(classification)
    return {"variance": variance, "count": len(variance)}


@app.get("/api/variance/summary")
async def get_variance_summary():
    """Get variance counts by classification"""
    db.cursor.execute("""
        SELECT variance_classification, COUNT(*) as count
        FROM config_variance_cache
        GROUP BY variance_classification
    """)
    summary = db.cursor.fetchall()
    return {"summary": summary}


# ============================================================================
# META TAG ENDPOINTS
# ============================================================================

@app.get("/api/tags")
async def get_all_tags():
    """Get all meta tags with categories"""
    db.cursor.execute("""
        SELECT mt.tag_name, mt.tag_description, mtc.category_name
        FROM meta_tags mt
        JOIN meta_tag_categories mtc ON mt.category_id = mtc.category_id
        ORDER BY mtc.category_name, mt.tag_name
    """)
    tags = db.cursor.fetchall()
    return {"tags": tags}


@app.get("/api/tags/{tag_name}/instances")
async def get_instances_with_tag(tag_name: str):
    """Get all instances with a specific tag"""
    instances = db.get_instances_with_tag(tag_name)
    return {"tag_name": tag_name, "instances": instances}


# ============================================================================
# SERVER OVERVIEW ENDPOINTS
# ============================================================================

@app.get("/api/servers")
async def get_servers():
    """Get server summary"""
    db.cursor.execute("""
        SELECT server_name, server_host,
               COUNT(*) as instance_count,
               SUM(CASE WHEN is_production THEN 1 ELSE 0 END) as production_count
        FROM instances
        WHERE is_active = true
        GROUP BY server_name, server_host
    """)
    servers = db.cursor.fetchall()
    return {"servers": servers}


@app.get("/api/deviations")
async def get_deviations():
    """Get configuration deviations (drift)"""
    # For now return empty list - drift detection needs config_rules populated
    return []


@app.get("/api/plugins")
async def get_plugins():
    """Get all plugins with metadata"""
    db.cursor.execute("""
        SELECT plugin_id, plugin_name, platform, current_version, latest_version,
               github_repo, modrinth_id, hangar_slug, spigot_id,
               docs_url, wiki_url, plugin_page_url,
               has_cicd, cicd_provider, cicd_url,
               description, author, license, is_premium, is_paid,
               last_checked_at
        FROM plugins
        ORDER BY plugin_name
    """)
    plugins = db.cursor.fetchall()
    
    # Get install count for each plugin
    for plugin in plugins:
        db.cursor.execute("""
            SELECT COUNT(DISTINCT instance_id) as install_count
            FROM instance_plugins
            WHERE plugin_id = %s AND is_enabled = true
        """, (plugin['plugin_id'],))
        result = db.cursor.fetchone()
        plugin['install_count'] = result['install_count'] if result else 0
    
    return {"plugins": plugins, "total": len(plugins)}


@app.get("/api/plugins/{plugin_id}")
async def get_plugin_details(plugin_id: str):
    """Get detailed plugin information"""
    db.cursor.execute("""
        SELECT * FROM plugins WHERE plugin_id = %s
    """, (plugin_id,))
    plugin = db.cursor.fetchone()
    
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Get all instances where this plugin is installed
    db.cursor.execute("""
        SELECT ip.instance_id, i.instance_name, ip.installed_version, 
               ip.is_enabled, ip.installed_at
        FROM instance_plugins ip
        JOIN instances i ON ip.instance_id = i.instance_id
        WHERE ip.plugin_id = %s
        ORDER BY i.instance_name
    """, (plugin_id,))
    plugin['installations'] = db.cursor.fetchall()
    
    return plugin


@app.post("/api/plugins")
async def create_plugin(plugin: Dict[str, Any]):
    """Create a new plugin entry"""
    db.cursor.execute("""
        INSERT INTO plugins 
        (plugin_id, plugin_name, platform, current_version, description, author)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        plugin['plugin_id'],
        plugin['plugin_name'],
        plugin.get('platform', 'paper'),
        plugin.get('current_version', '1.0.0'),
        plugin.get('description', ''),
        plugin.get('author', '')
    ))
    db.commit()
    
    return {'success': True, 'plugin_id': plugin['plugin_id']}


@app.put("/api/plugins/{plugin_id}")
async def update_plugin(plugin_id: str, updates: Dict[str, Any]):
    """Update plugin metadata"""
    allowed_fields = [
        'current_version', 'latest_version', 'description', 'author',
        'github_repo', 'modrinth_id', 'hangar_slug', 'spigot_id',
        'docs_url', 'wiki_url', 'plugin_page_url',
        'has_cicd', 'cicd_provider', 'cicd_url', 'license'
    ]
    
    set_clauses = []
    values = []
    
    for field in allowed_fields:
        if field in updates:
            set_clauses.append(f"{field} = %s")
            values.append(updates[field])
    
    if not set_clauses:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    values.append(plugin_id)
    
    db.cursor.execute(f"""
        UPDATE plugins
        SET {', '.join(set_clauses)}, last_updated_at = NOW()
        WHERE plugin_id = %s
    """, values)
    db.commit()
    
    return {'success': True, 'plugin_id': plugin_id}


@app.delete("/api/plugins/{plugin_id}")
async def delete_plugin(plugin_id: str):
    """Delete a plugin (and all its instance associations)"""
    # Check if plugin exists
    db.cursor.execute("SELECT plugin_id FROM plugins WHERE plugin_id = %s", (plugin_id,))
    if not db.cursor.fetchone():
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    # Delete will cascade to instance_plugins due to foreign key
    db.cursor.execute("DELETE FROM plugins WHERE plugin_id = %s", (plugin_id,))
    db.commit()
    
    return {'success': True, 'plugin_id': plugin_id}


# ============================================================================
# CONFIG VARIANCE & DRIFT DETECTION ENDPOINTS
# ============================================================================

@app.get("/api/variance/summary")
async def get_variance_summary():
    """Get variance summary across all plugins"""
    db.cursor.execute("""
        SELECT 
            variance_classification,
            COUNT(*) as count,
            SUM(CASE WHEN is_expected_variance = false THEN 1 ELSE 0 END) as drift_count
        FROM config_variance_cache
        GROUP BY variance_classification
    """)
    
    summary = {
        'by_classification': {},
        'total_configs': 0,
        'total_drift': 0
    }
    
    for row in db.cursor.fetchall():
        classification = row['variance_classification']
        summary['by_classification'][classification] = {
            'total': row['count'],
            'drift': row['drift_count']
        }
        summary['total_configs'] += row['count']
        summary['total_drift'] += row['drift_count']
    
    return summary


@app.get("/api/variance/by-plugin/{plugin_name}")
async def get_plugin_variance(plugin_name: str):
    """Get variance breakdown for a specific plugin"""
    db.cursor.execute("""
        SELECT *
        FROM config_variance_cache
        WHERE plugin_name = %s
        ORDER BY variance_classification, config_key
    """, (plugin_name,))
    
    variances = db.cursor.fetchall()
    
    return {
        'plugin_name': plugin_name,
        'total_configs': len(variances),
        'variances': variances
    }


@app.get("/api/drift/active")
async def get_active_drift():
    """Get all active drift entries needing review"""
    db.cursor.execute("""
        SELECT 
            d.*,
            i.instance_name,
            i.server_name
        FROM config_drift_log d
        JOIN instances i ON d.instance_id = i.instance_id
        WHERE d.status = 'pending'
        ORDER BY d.severity DESC, d.detected_at DESC
        LIMIT 100
    """)
    
    drifts = db.cursor.fetchall()
    
    return {
        'count': len(drifts),
        'drifts': drifts
    }


@app.get("/api/drift/by-instance/{instance_id}")
async def get_instance_drift(instance_id: str):
    """Get drift entries for a specific instance"""
    db.cursor.execute("""
        SELECT *
        FROM config_drift_log
        WHERE instance_id = %s
        AND status IN ('pending', 'reviewed')
        ORDER BY severity DESC, plugin_name, config_key
    """, (instance_id,))
    
    return db.cursor.fetchall()


@app.post("/api/drift/{drift_id}/resolve")
async def resolve_drift(drift_id: int, resolution: Dict[str, Any]):
    """Mark drift as resolved"""
    status = resolution.get('status', 'fixed')
    notes = resolution.get('notes', '')
    reviewer = resolution.get('reviewer', 'admin')
    
    db.cursor.execute("""
        UPDATE config_drift_log
        SET status = %s,
            resolution_notes = %s,
            reviewed_by = %s,
            reviewed_at = NOW()
        WHERE drift_id = %s
    """, (status, notes, reviewer, drift_id))
    db.commit()
    
    return {"success": True, "drift_id": drift_id, "status": status}


# ============================================================================
# CONFIG RULES ENDPOINTS
# ============================================================================

@app.get("/api/rules/by-plugin/{plugin_name}")
async def get_plugin_rules(plugin_name: str):
    """Get all config rules for a plugin"""
    db.cursor.execute("""
        SELECT *
        FROM config_rules
        WHERE plugin_name = %s
        AND is_active = true
        ORDER BY priority ASC, config_key
    """, (plugin_name,))
    
    return db.cursor.fetchall()


@app.get("/api/rules/resolve")
async def resolve_config_rule(
    instance_id: str,
    plugin_name: str,
    config_key: str
):
    """
    Resolve final config value for an instance using rule hierarchy
    
    Returns the winning rule and how it was resolved
    """
    # Get instance metadata
    instance = db.get_instance(instance_id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")
    
    # Get instance tags
    db.cursor.execute("""
        SELECT mt.tag_name
        FROM instance_tags it
        JOIN meta_tags mt ON it.tag_id = mt.tag_id
        WHERE it.instance_id = %s
    """, (instance_id,))
    tags = [row['tag_name'] for row in db.cursor.fetchall()]
    
    # Get all applicable rules
    db.cursor.execute("""
        SELECT *
        FROM config_rules
        WHERE plugin_name = %s
        AND config_key = %s
        AND is_active = true
        ORDER BY priority ASC
    """, (plugin_name, config_key))
    
    rules = db.cursor.fetchall()
    
    # Apply hierarchy
    winning_rule = None
    resolution_path = []
    
    for rule in rules:
        scope_type = rule['scope_type']
        scope_selector = rule['scope_selector']
        
        applies = False
        reason = ""
        
        if scope_type == 'GLOBAL':
            applies = True
            reason = "Global default"
        elif scope_type == 'SERVER' and instance['server_name'] == scope_selector:
            applies = True
            reason = f"Server-level override ({scope_selector})"
        elif scope_type == 'META_TAG' and scope_selector in tags:
            applies = True
            reason = f"Meta-tag override (tag:{scope_selector})"
        elif scope_type == 'INSTANCE' and instance_id == scope_selector:
            applies = True
            reason = f"Instance-specific override"
            winning_rule = rule  # Highest priority, stop here
            resolution_path.append({'rule': rule, 'reason': reason, 'final': True})
            break
        
        if applies:
            winning_rule = rule
            resolution_path.append({'rule': rule, 'reason': reason, 'final': False})
    
    if not winning_rule:
        raise HTTPException(status_code=404, detail=f"No rule found for {plugin_name}.{config_key}")
    
    # Mark final rule
    if resolution_path:
        resolution_path[-1]['final'] = True
    
    return {
        'instance_id': instance_id,
        'plugin_name': plugin_name,
        'config_key': config_key,
        'final_value': winning_rule['config_value'],
        'value_type': winning_rule['value_type'],
        'winning_rule_id': winning_rule['rule_id'],
        'scope': winning_rule['scope_type'],
        'resolution_path': resolution_path,
        'instance_tags': tags
    }


@app.post("/api/rules/create")
async def create_config_rule(rule: Dict[str, Any]):
    """Create a new config rule"""
    # Calculate priority based on scope
    scope_priorities = {
        'INSTANCE': 1,
        'META_TAG': 2,
        'SERVER': 3,
        'GLOBAL': 4
    }
    
    priority = scope_priorities.get(rule['scope_type'], 4)
    
    db.cursor.execute("""
        INSERT INTO config_rules 
        (plugin_name, config_file, config_key, scope_type, scope_selector, 
         config_value, value_type, priority, created_by, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        rule['plugin_name'],
        rule.get('config_file', 'config.yml'),
        rule['config_key'],
        rule['scope_type'],
        rule.get('scope_selector'),
        rule['config_value'],
        rule.get('value_type', 'string'),
        priority,
        rule.get('created_by', 'api'),
        rule.get('notes', '')
    ))
    db.commit()
    
    return {
        'success': True,
        'rule_id': db.cursor.lastrowid
    }


@app.put("/api/rules/{rule_id}")
async def update_config_rule(rule_id: int, updates: Dict[str, Any]):
    """Update an existing config rule"""
    # Build UPDATE query dynamically
    allowed_fields = ['config_value', 'value_type', 'notes', 'is_active']
    set_clauses = []
    values = []
    
    for field in allowed_fields:
        if field in updates:
            set_clauses.append(f"{field} = %s")
            values.append(updates[field])
    
    if not set_clauses:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    values.append(rule_id)
    
    db.cursor.execute(f"""
        UPDATE config_rules
        SET {', '.join(set_clauses)}, updated_at = NOW()
        WHERE rule_id = %s
    """, values)
    db.commit()
    
    return {'success': True, 'rule_id': rule_id}


@app.delete("/api/rules/{rule_id}")
async def delete_config_rule(rule_id: int):
    """Soft-delete a config rule"""
    db.cursor.execute("""
        UPDATE config_rules
        SET is_active = false, updated_at = NOW()
        WHERE rule_id = %s
    """, (rule_id,))
    db.commit()
    
    return {'success': True, 'rule_id': rule_id}


@app.get("/api/rules")
async def get_all_config_rules(plugin: str = None, scope: str = None):
    """Get all config rules with optional filters"""
    query = "SELECT * FROM config_rules WHERE is_active = true"
    params = []
    
    if plugin:
        query += " AND plugin_name = %s"
        params.append(plugin)
    
    if scope:
        query += " AND scope_type = %s"
        params.append(scope)
    
    query += " ORDER BY priority ASC, plugin_name, config_key"
    
    db.cursor.execute(query, params)
    rules = db.cursor.fetchall()
    
    return {'rules': rules, 'total': len(rules)}


@app.get("/api/rules/{rule_id}")
async def get_config_rule(rule_id: int):
    """Get a specific config rule"""
    db.cursor.execute("SELECT * FROM config_rules WHERE rule_id = %s", (rule_id,))
    rule = db.cursor.fetchone()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Config rule not found")
    
    return rule


# ============================================================================
# TAG MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/tags/categories")
async def get_tag_categories():
    """Get all tag categories"""
    db.cursor.execute("""
        SELECT * FROM meta_tag_categories
        WHERE is_active = true
        ORDER BY display_order
    """)
    return db.cursor.fetchall()


@app.get("/api/tags/all")
async def get_all_tags():
    """Get all tags organized by category"""
    db.cursor.execute("""
        SELECT mt.*, mtc.category_name
        FROM meta_tags mt
        JOIN meta_tag_categories mtc ON mt.category_id = mtc.category_id
        WHERE mt.is_active = true
        ORDER BY mtc.display_order, mt.tag_name
    """)
    
    tags = db.cursor.fetchall()
    
    # Organize by category
    by_category = {}
    for tag in tags:
        cat = tag['category_name']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(tag)
    
    return {
        'all_tags': tags,
        'by_category': by_category
    }


@app.get("/api/tags/instance/{instance_id}")
async def get_instance_tags_full(instance_id: str):
    """Get all tags assigned to an instance"""
    db.cursor.execute("""
        SELECT mt.*, mtc.category_name
        FROM instance_tags it
        JOIN meta_tags mt ON it.tag_id = mt.tag_id
        JOIN meta_tag_categories mtc ON mt.category_id = mtc.category_id
        WHERE it.instance_id = %s
        ORDER BY mtc.display_order, mt.tag_name
    """, (instance_id,))
    
    return db.cursor.fetchall()


@app.post("/api/tags/assign")
async def assign_tag_to_instance(assignment: Dict[str, Any]):
    """Assign a tag to an instance"""
    instance_id = assignment['instance_id']
    tag_id = assignment['tag_id']
    assigned_by = assignment.get('assigned_by', 'admin')
    
    db.cursor.execute("""
        INSERT INTO instance_tags (instance_id, tag_id, assigned_by)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE assigned_at = NOW(), assigned_by = %s
    """, (instance_id, tag_id, assigned_by, assigned_by))
    db.commit()
    
    return {'success': True, 'instance_id': instance_id, 'tag_id': tag_id}


@app.delete("/api/tags/unassign")
async def unassign_tag_from_instance(instance_id: str, tag_id: int):
    """Remove a tag from an instance"""
    db.cursor.execute("""
        DELETE FROM instance_tags
        WHERE instance_id = %s AND tag_id = %s
    """, (instance_id, tag_id))
    db.commit()
    
    return {'success': True, 'instance_id': instance_id, 'tag_id': tag_id}


@app.post("/api/tags")
async def create_meta_tag(tag: Dict[str, Any]):
    """Create a new meta tag"""
    db.cursor.execute("""
        INSERT INTO meta_tags 
        (tag_name, category_id, display_name, description, color_code, icon)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        tag['tag_name'],
        tag['category_id'],
        tag.get('display_name', tag['tag_name']),
        tag.get('description', ''),
        tag.get('color_code', '#3498db'),
        tag.get('icon', '')
    ))
    db.commit()
    
    return {'success': True, 'tag_id': db.cursor.lastrowid, 'tag_name': tag['tag_name']}


@app.put("/api/tags/{tag_id}")
async def update_meta_tag(tag_id: int, updates: Dict[str, Any]):
    """Update a meta tag"""
    allowed_fields = ['display_name', 'description', 'color_code', 'icon', 'is_active']
    set_clauses = []
    values = []
    
    for field in allowed_fields:
        if field in updates:
            set_clauses.append(f"{field} = %s")
            values.append(updates[field])
    
    if not set_clauses:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    values.append(tag_id)
    
    db.cursor.execute(f"""
        UPDATE meta_tags
        SET {', '.join(set_clauses)}
        WHERE tag_id = %s
    """, values)
    db.commit()
    
    return {'success': True, 'tag_id': tag_id}


@app.delete("/api/tags/{tag_id}")
async def delete_meta_tag(tag_id: int, force: bool = False):
    """Delete a meta tag (soft delete by default, hard delete if force=True)"""
    # Check if tag exists
    db.cursor.execute("SELECT tag_id, is_system_tag FROM meta_tags WHERE tag_id = %s", (tag_id,))
    tag = db.cursor.fetchone()
    
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    if tag['is_system_tag'] and not force:
        raise HTTPException(status_code=403, detail="Cannot delete system tag without force=True")
    
    if force:
        # Hard delete - will cascade to instance_tags
        db.cursor.execute("DELETE FROM meta_tags WHERE tag_id = %s", (tag_id,))
    else:
        # Soft delete
        db.cursor.execute("UPDATE meta_tags SET is_active = false WHERE tag_id = %s", (tag_id,))
    
    db.commit()
    
    return {'success': True, 'tag_id': tag_id, 'deleted': force}


@app.post("/api/tags/categories")
async def create_tag_category(category: Dict[str, Any]):
    """Create a new tag category"""
    db.cursor.execute("""
        INSERT INTO meta_tag_categories 
        (category_name, description, display_order)
        VALUES (%s, %s, %s)
    """, (
        category['category_name'],
        category.get('description', ''),
        category.get('display_order', 0)
    ))
    db.commit()
    
    return {'success': True, 'category_id': db.cursor.lastrowid}


# ============================================================================
# STATIC FILES & ROOT
# ============================================================================

# Serve static frontend files
BASE_DIR = Path(__file__).parent.parent.parent
static_dir = BASE_DIR / "src" / "web" / "static"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main dashboard UI"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return html_file.read_text()
    return """
    <html>
        <head><title>ArchiveSMP Config Manager</title></head>
        <body>
            <h1>ArchiveSMP Configuration Manager</h1>
            <p>Web GUI not deployed. API is running.</p>
            <h2>API Endpoints:</h2>
            <ul>
                <li><a href="/docs">/docs</a> - Interactive API documentation</li>
                <li><a href="/api/instances">/api/instances</a> - List all instances</li>
                <li><a href="/api/variance">/api/variance</a> - Configuration variance report</li>
                <li><a href="/api/groups">/api/groups</a> - Instance groups</li>
                <li><a href="/api/servers">/api/servers</a> - Server summary</li>
            </ul>
        </body>
    </html>
    """

@app.get("/variance", response_class=HTMLResponse)
async def variance_ui():
    """Serve variance dashboard UI"""
    html_file = static_dir / "variance.html"
    if html_file.exists():
        return html_file.read_text()
    raise HTTPException(status_code=404, detail="Variance UI not found")

@app.get("/deploy", response_class=HTMLResponse)
async def deploy_ui():
    """Serve deployment UI"""
    html_file = static_dir / "deploy.html"
    if html_file.exists():
        return html_file.read_text()
    raise HTTPException(status_code=404, detail="Deploy UI not found")

@app.get("/history", response_class=HTMLResponse)
async def history_ui():
    """Serve change history UI"""
    html_file = static_dir / "history.html"
    if html_file.exists():
        return html_file.read_text()
    raise HTTPException(status_code=404, detail="History UI not found")

@app.get("/migrations", response_class=HTMLResponse)
async def migrations_ui():
    """Serve migrations UI"""
    html_file = static_dir / "migrations.html"
    if html_file.exists():
        return html_file.read_text()
    raise HTTPException(status_code=404, detail="Migrations UI not found")


# ============================================================================
# HISTORY & TRACKING ENDPOINTS (NEW - Option C Implementation)
# ============================================================================

@app.get("/api/history/changes")
async def get_change_history(
    instance_id: Optional[str] = None,
    plugin_name: Optional[str] = None,
    changed_by: Optional[str] = None,
    change_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get config change history with filters
    
    Query Parameters:
    - instance_id: Filter by instance
    - plugin_name: Filter by plugin
    - changed_by: Filter by user
    - change_type: Filter by type (manual, automated, drift_fix, rule_based)
    - limit: Max results (default 100)
    - offset: Pagination offset
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        changes = db.get_change_history(
            instance_id=instance_id,
            plugin_name=plugin_name,
            changed_by=changed_by,
            change_type=change_type,
            limit=limit,
            offset=offset
        )
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM config_change_history WHERE 1=1"
        params = []
        
        if instance_id:
            count_query += " AND instance_id = %s"
            params.append(instance_id)
        if plugin_name:
            count_query += " AND plugin_name = %s"
            params.append(plugin_name)
        if changed_by:
            count_query += " AND changed_by = %s"
            params.append(changed_by)
        if change_type:
            count_query += " AND change_type = %s"
            params.append(change_type)
        
        db.cursor.execute(count_query, params)
        total = db.cursor.fetchone()['total']
        
        return {
            'changes': changes,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + len(changes)) < total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/history/changes/{change_id}")
async def get_change_detail(change_id: int):
    """Get detailed information about a specific change"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        db.cursor.execute("""
            SELECT * FROM config_change_history
            WHERE change_id = %s
        """, (change_id,))
        
        change = db.cursor.fetchone()
        
        if not change:
            raise HTTPException(status_code=404, detail=f"Change {change_id} not found")
        
        return change
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/history/deployments")
async def get_deployment_history(
    deployed_by: Optional[str] = None,
    deployment_status: Optional[str] = None,
    limit: int = 50
):
    """
    Get deployment history
    
    Query Parameters:
    - deployed_by: Filter by user
    - deployment_status: Filter by status (pending, in_progress, completed, failed, rolled_back)
    - limit: Max results (default 50)
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        query = "SELECT * FROM deployment_history WHERE 1=1"
        params = []
        
        if deployed_by:
            query += " AND deployed_by = %s"
            params.append(deployed_by)
        
        if deployment_status:
            query += " AND deployment_status = %s"
            params.append(deployment_status)
        
        query += " ORDER BY deployed_at DESC LIMIT %s"
        params.append(limit)
        
        db.cursor.execute(query, params)
        deployments = db.cursor.fetchall()
        
        return {
            'deployments': deployments,
            'total': len(deployments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/history/deployments/{deployment_id}")
async def get_deployment_detail(deployment_id: int):
    """Get detailed deployment information including all changes"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Get deployment record
        db.cursor.execute("""
            SELECT * FROM deployment_history
            WHERE deployment_id = %s
        """, (deployment_id,))
        
        deployment = db.cursor.fetchone()
        
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
        
        # Get associated changes
        db.cursor.execute("""
            SELECT dc.*, cch.*
            FROM deployment_changes dc
            JOIN config_change_history cch ON dc.change_id = cch.change_id
            WHERE dc.deployment_id = %s
            ORDER BY cch.changed_at
        """, (deployment_id,))
        
        changes = db.cursor.fetchall()
        
        deployment['changes'] = changes
        deployment['changes_count'] = len(changes)
        
        return deployment
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/migrations")
async def list_all_migrations():
    """List all known config key migrations"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        db.cursor.execute("""
            SELECT plugin_name, COUNT(*) as migration_count,
                   SUM(is_breaking) as breaking_count
            FROM config_key_migrations
            GROUP BY plugin_name
            ORDER BY plugin_name
        """)
        
        summary = db.cursor.fetchall()
        
        return {
            'plugins': summary,
            'total_plugins': len(summary)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/migrations/{plugin_name}")
async def get_plugin_migrations(plugin_name: str):
    """Get known config key migrations for a specific plugin"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        migrations = db.get_plugin_migrations(plugin_name)
        
        if not migrations:
            # Not an error - plugin just has no migrations
            return {
                'plugin': plugin_name,
                'migrations': [],
                'total': 0
            }
        
        return {
            'plugin': plugin_name,
            'migrations': migrations,
            'total': len(migrations),
            'breaking_count': sum(1 for m in migrations if m.get('is_breaking')),
            'automatic_count': sum(1 for m in migrations if m.get('is_automatic'))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/history/variance")
async def get_variance_history(
    plugin_name: Optional[str] = None,
    config_key: Optional[str] = None,
    limit: int = 100
):
    """
    Get historical variance snapshots
    
    Query Parameters:
    - plugin_name: Filter by plugin
    - config_key: Filter by config key
    - limit: Max results (default 100)
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        query = "SELECT * FROM config_variance_history WHERE 1=1"
        params = []
        
        if plugin_name:
            query += " AND plugin_name = %s"
            params.append(plugin_name)
        
        if config_key:
            query += " AND config_key = %s"
            params.append(config_key)
        
        query += " ORDER BY snapshot_time DESC LIMIT %s"
        params.append(limit)
        
        db.cursor.execute(query, params)
        history = db.cursor.fetchall()
        
        return {
            'variance_history': history,
            'total': len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/stats/changes")
async def get_change_statistics():
    """Get statistics about config changes"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    try:
        # Changes by type
        db.cursor.execute("""
            SELECT change_type, COUNT(*) as count
            FROM config_change_history
            GROUP BY change_type
            ORDER BY count DESC
        """)
        by_type = db.cursor.fetchall()
        
        # Changes by user
        db.cursor.execute("""
            SELECT changed_by, COUNT(*) as count
            FROM config_change_history
            GROUP BY changed_by
            ORDER BY count DESC
            LIMIT 10
        """)
        by_user = db.cursor.fetchall()
        
        # Recent changes (last 7 days)
        db.cursor.execute("""
            SELECT DATE(changed_at) as date, COUNT(*) as count
            FROM config_change_history
            WHERE changed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(changed_at)
            ORDER BY date DESC
        """)
        recent = db.cursor.fetchall()
        
        # Total counts
        db.cursor.execute("SELECT COUNT(*) as total FROM config_change_history")
        total = db.cursor.fetchone()['total']
        
        return {
            'total_changes': total,
            'by_type': by_type,
            'by_user': by_user,
            'last_7_days': recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
