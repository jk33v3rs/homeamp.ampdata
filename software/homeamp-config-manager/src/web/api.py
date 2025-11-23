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
from ..api.enhanced_endpoints import router as enhanced_router
from ..api.dashboard_endpoints import router as dashboard_router
from ..api.plugin_configurator_endpoints import router as plugin_configurator_router
from ..api.deployment_endpoints import router as deployment_router
from ..api.update_manager_endpoints import router as update_manager_router
from ..api.variance_endpoints import router as variance_router
from ..api.audit_log_endpoints import router as audit_log_router
from ..api.tag_manager_endpoints import router as tag_manager_router

app = FastAPI(
    title="ArchiveSMP Configuration Manager",
    description="Database-backed config management for ArchiveSMP",
    version="2.0.0"
)

# Include Phase 0 enhanced endpoints
app.include_router(enhanced_router)
# Include Phase 2 dashboard endpoints
app.include_router(dashboard_router)
# Include Phase 2 plugin configurator endpoints
app.include_router(plugin_configurator_router)
# Include deployment endpoints
app.include_router(deployment_router)
# Include update manager endpoints
app.include_router(update_manager_router)
# Include variance endpoints
app.include_router(variance_router)
app.include_router(audit_log_router)
app.include_router(tag_manager_router)

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
agent = None  # Reference to running agent (if any)

@app.on_event("startup")
async def startup():
    """Initialize database connection"""
    global db
    from ..api.db_config import get_db_config
    
    db_config = get_db_config()
    db = ConfigDatabase(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password']
    )
    db.connect()

@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    if db:
        db.disconnect()


# ============================================================================
# AGENT CONTROL ENDPOINTS
# ============================================================================

@app.post("/api/agent/trigger-scan")
async def trigger_manual_scan():
    """
    Trigger immediate full scan of all instances
    Normally scans run on schedule (configurable interval)
    This forces an immediate scan for manual refresh
    """
    # Check if agent is running and accessible
    if agent is None:
        # Agent not running in same process - trigger via file signal
        import os
        signal_file = Path("/var/run/archivesmp/trigger_scan")
        signal_file.parent.mkdir(parents=True, exist_ok=True)
        signal_file.write_text(str(datetime.now()))
        
        return {
            "status": "triggered",
            "message": "Scan signal sent to agent (will execute on next cycle)",
            "note": "Agent runs independently - check logs for scan results"
        }
    
    # Agent running in same process - trigger directly
    try:
        result = agent.trigger_manual_scan()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


# ============================================================================
# INSTANCE ENDPOINTS
# ============================================================================

@app.get("/api/instances")
async def get_instances(server: Optional[str] = None):
    """Get all instances, optionally filtered by server"""
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
    """Get all plugins with metadata and install counts"""
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


@app.get("/api/plugins/discovered")
async def get_discovered_plugins():
    """
    Get all dynamically discovered plugins from agent scans
    NO HARDCODING - returns whatever the agent found
    """
    db.cursor.execute("""
        SELECT 
            p.plugin_id,
            p.plugin_name,
            p.platform,
            p.description,
            p.author,
            p.current_version,
            p.latest_version,
            COUNT(DISTINCT ip.instance_id) as instance_count,
            COUNT(DISTINCT cr.rule_id) as config_key_count
        FROM plugins p
        LEFT JOIN instance_plugins ip ON p.plugin_id = ip.plugin_id
        LEFT JOIN config_rules cr ON p.plugin_name = cr.plugin_name
        GROUP BY p.plugin_id
        ORDER BY instance_count DESC, p.plugin_name
    """)
    
    plugins = db.cursor.fetchall()
    
    return {
        'plugins': plugins,
        'total': len(plugins),
        'discovery_note': 'Auto-discovered from agent scans - no hardcoded plugin list'
    }


@app.get("/api/plugins/{plugin_id}")
async def get_plugin_details(plugin_id: str):
    """Get detailed plugin information including all installations"""
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


@app.get("/api/datapacks")
async def get_datapacks(instance_id: Optional[int] = None):
    """Get discovered datapacks"""
    query = """
        SELECT 
            d.id,
            d.instance_id,
            i.instance_name,
            d.world_name,
            d.datapack_name,
            d.version,
            d.file_hash,
            d.installed_at
        FROM instance_datapacks d
        JOIN instances i ON d.instance_id = i.instance_id
    """
    
    if instance_id is not None:
        query += " WHERE d.instance_id = %s ORDER BY d.datapack_name, d.world_name"
        db.cursor.execute(query, (instance_id,))
    else:
        query += " ORDER BY i.instance_name, d.datapack_name"
        db.cursor.execute(query)
    
    results = db.cursor.fetchall()
    return {"datapacks": results, "count": len(results)}


# ============================================================================
# HISTORY & AUDIT TRAIL ENDPOINTS
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


@app.get("/api/stats/changes")
async def get_change_statistics():
    """Get statistics about config changes"""
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


# ============================================================================
# MIGRATIONS TRACKING ENDPOINTS
# ============================================================================

@app.get("/api/migrations")
async def list_all_migrations():
    """List all known config key migrations"""
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


# ============================================================================
# UNIVERSAL CONFIG MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/config/plugin/{plugin_id}")
async def get_plugin_config(plugin_id: str, scope: str = 'universal'):
    """
    Get all config keys for a plugin at specified scope
    Returns current values, hierarchy source, and metadata
    
    Args:
        plugin_id: Plugin identifier
        scope: universal|server|group|instance
    """
    try:
        # Get plugin name from ID
        db.cursor.execute("SELECT plugin_name FROM plugins WHERE plugin_id = %s", (plugin_id,))
        plugin = db.cursor.fetchone()
        
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        plugin_name = plugin['plugin_name']
        
        # Get all config keys for this plugin
        db.cursor.execute("""
            SELECT DISTINCT
                cr.config_file,
                cr.config_key,
                cr.scope_type,
                cr.scope_selector,
                cr.config_value,
                cr.value_type,
                cr.priority,
                cr.notes
            FROM config_rules cr
            WHERE cr.plugin_name = %s
            AND cr.is_active = true
            ORDER BY cr.config_file, cr.config_key, cr.priority
        """, (plugin_name,))
        
        rules = db.cursor.fetchall()
        
        # Organize by file and key
        config_structure = {}
        
        for rule in rules:
            file = rule['config_file']
            key = rule['config_key']
            full_key = f"{file}:{key}"
            
            if full_key not in config_structure:
                config_structure[full_key] = {
                    'file': file,
                    'key': key,
                    'value': None,
                    'source': 'default',
                    'source_description': 'No value set',
                    'hierarchy': []
                }
            
            # Add to hierarchy
            config_structure[full_key]['hierarchy'].append({
                'scope': rule['scope_type'],
                'selector': rule['scope_selector'],
                'value': rule['config_value'],
                'priority': rule['priority']
            })
            
            # Determine effective value based on scope filter
            if scope == 'universal' and rule['scope_type'] == 'GLOBAL':
                config_structure[full_key]['value'] = rule['config_value']
                config_structure[full_key]['source'] = 'universal'
                config_structure[full_key]['source_description'] = 'Universal default (applies to all)'
            elif rule['scope_type'] in ['SERVER', 'META_TAG', 'INSTANCE']:
                # Higher priority override
                if config_structure[full_key]['value'] is None or rule['priority'] < config_structure[full_key].get('effective_priority', 999):
                    config_structure[full_key]['value'] = rule['config_value']
                    config_structure[full_key]['source'] = rule['scope_type'].lower()
                    config_structure[full_key]['effective_priority'] = rule['priority']
                    
                    if rule['scope_selector']:
                        config_structure[full_key]['source_description'] = f"Override: {rule['scope_type']} = {rule['scope_selector']}"
        
        return {
            'plugin_id': plugin_id,
            'plugin_name': plugin_name,
            'scope': scope,
            'keys': config_structure,
            'total_keys': len(config_structure)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/config/universal")
async def set_universal_config(config: Dict[str, Any]):
    """
    Set a universal config value (applies to ALL instances)
    Creates or updates a GLOBAL scope rule
    
    Body:
        plugin_id: Plugin identifier
        config_key: Full key path (e.g., "config.yml:server.max-players")
        value: The value to set
        notes: Optional notes about why this was set
    """
    try:
        plugin_id = config['plugin_id']
        config_key = config['config_key']
        value = config['value']
        notes = config.get('notes', 'Set via Universal Config UI')
        
        # Get plugin name
        db.cursor.execute("SELECT plugin_name FROM plugins WHERE plugin_id = %s", (plugin_id,))
        plugin = db.cursor.fetchone()
        
        if not plugin:
            raise HTTPException(status_code=404, detail="Plugin not found")
        
        plugin_name = plugin['plugin_name']
        
        # Parse file and key from full key
        if ':' in config_key:
            file, key = config_key.split(':', 1)
        else:
            file = 'config.yml'
            key = config_key
        
        # Check if universal rule already exists
        db.cursor.execute("""
            SELECT rule_id FROM config_rules
            WHERE plugin_name = %s
            AND config_file = %s
            AND config_key = %s
            AND scope_type = 'GLOBAL'
        """, (plugin_name, file, key))
        
        existing = db.cursor.fetchone()
        
        if existing:
            # Update existing
            db.cursor.execute("""
                UPDATE config_rules
                SET config_value = %s,
                    notes = %s,
                    updated_at = NOW()
                WHERE rule_id = %s
            """, (value, notes, existing['rule_id']))
            
            rule_id = existing['rule_id']
            action = 'updated'
        else:
            # Create new
            db.cursor.execute("""
                INSERT INTO config_rules 
                (plugin_name, config_file, config_key, scope_type, scope_selector, 
                 config_value, value_type, priority, created_by, notes)
                VALUES (%s, %s, %s, 'GLOBAL', NULL, %s, 'string', 4, 'web_ui', %s)
            """, (plugin_name, file, key, value, notes))
            
            rule_id = db.cursor.lastrowid
            action = 'created'
        
        db.commit()
        
        return {
            'success': True,
            'action': action,
            'rule_id': rule_id,
            'plugin_name': plugin_name,
            'config_key': f"{file}:{key}",
            'value': value
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/config/bulk-update")
async def bulk_update_configs(updates: Dict[str, Any]):
    """
    Bulk update multiple config values at once
    
    Body:
        scope: universal|server|group|instance
        changes: {plugin_id: {config_key: value}}
    """
    try:
        scope = updates.get('scope', 'universal')
        changes = updates.get('changes', {})
        
        results = []
        errors = []
        
        for plugin_id, config_changes in changes.items():
            for config_key, value in config_changes.items():
                try:
                    # Use the set_universal_config logic
                    result = await set_universal_config({
                        'plugin_id': plugin_id,
                        'config_key': config_key,
                        'value': value,
                        'notes': f'Bulk update via API (scope: {scope})'
                    })
                    results.append(result)
                except Exception as e:
                    errors.append({
                        'plugin_id': plugin_id,
                        'config_key': config_key,
                        'error': str(e)
                    })
        
        return {
            'success': len(errors) == 0,
            'total_changes': len(results),
            'successful': results,
            'errors': errors
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")



async def get_outdated_plugins():
    """Get plugins with available updates"""
    db.cursor.execute("""
        SELECT 
            pv.plugin_name,
            pv.installed_version as current_version,
            pv.latest_version,
            GROUP_CONCAT(i.name SEPARATOR ', ') as instances,
            MAX(pv.last_checked) as last_checked
        FROM plugin_versions pv
        JOIN instances i ON pv.instance_id = i.id
        WHERE pv.update_available = TRUE
        GROUP BY pv.plugin_name, pv.installed_version, pv.latest_version
        ORDER BY pv.plugin_name
    """)
    results = db.cursor.fetchall()
    
    # Split instances string into array
    for r in results:
        if r.get('instances'):
            r['instances'] = r['instances'].split(', ')
        else:
            r['instances'] = []
    
    return {"outdated": results, "count": len(results)}


@app.get("/api/cicd/endpoints")
async def get_cicd_endpoints():
    """Get CI/CD webhook endpoints"""
    # Returns empty - CICD webhooks not currently configured
    # Future: query cicd_endpoints table when GitHub/GitLab webhooks are set up
    return {"endpoints": [], "count": 0}


@app.get("/dashboard/approval-queue")
async def get_approval_queue():
    """Get pending approvals (plugin updates and config changes)"""
    db.cursor.execute("""
        SELECT 
            pv.version_id as id,
            'plugin_update' as type,
            pv.plugin_name,
            pv.installed_version as current_version,
            pv.latest_version as new_version,
            pv.instance_id,
            pv.last_checked as timestamp
        FROM plugin_versions pv
        WHERE pv.update_available = TRUE
        ORDER BY pv.last_checked DESC
    """)
    results = db.cursor.fetchall()
    return {"items": results, "count": len(results)}


@app.get("/dashboard/network-status")
async def get_network_status():
    """Get network status across all servers"""
    db.cursor.execute("""
        SELECT 
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as online,
            SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as offline,
            COUNT(*) as total
        FROM instances
    """)
    overall = db.cursor.fetchone()
    
    db.cursor.execute("""
        SELECT 
            server_name,
            SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as online,
            SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as offline,
            COUNT(*) as total
        FROM instances
        GROUP BY server_name
    """)
    servers = db.cursor.fetchall()
    
    return {
        "online": int(overall['online'] or 0),
        "offline": int(overall['offline'] or 0),
        "total": int(overall['total']),
        "servers": servers,
        "variance_count": 0
    }


@app.get("/dashboard/plugin-summary")
async def get_plugin_summary():
    """Get plugin summary statistics"""
    db.cursor.execute("""
        SELECT 
            COUNT(DISTINCT plugin_name) as total_plugins,
            SUM(CASE WHEN update_available = TRUE THEN 1 ELSE 0 END) as needs_update,
            SUM(CASE WHEN update_available = FALSE OR update_available IS NULL THEN 1 ELSE 0 END) as up_to_date
        FROM plugin_versions
    """)
    result = db.cursor.fetchone()
    
    return {
        "total_plugins": int(result['total_plugins'] or 0),
        "needs_update": int(result['needs_update'] or 0),
        "up_to_date": int(result['up_to_date'] or 0)
    }


@app.get("/dashboard/recent-activity")
async def get_recent_activity(limit: int = 10):
    """Get recent activity log entries"""
    db.cursor.execute("""
        SELECT 
            changed_at as timestamp,
            change_type as event_type,
            CASE 
                WHEN change_type = 'plugin_lifecycle' THEN 
                    CONCAT(instance_id, ': ', plugin_name, ' lifecycle event')
                WHEN config_key IS NOT NULL AND config_key != '' THEN 
                    CONCAT(instance_id, ': ', change_type, ' - ', plugin_name, '.', config_key)
                ELSE 
                    CONCAT(instance_id, ': ', change_type, ' - ', plugin_name)
            END as description,
            instance_id,
            changed_by as user
        FROM config_change_history
        ORDER BY changed_at DESC
        LIMIT %s
    """, (limit,))
    results = db.cursor.fetchall()
    
    return {"activities": results, "count": len(results)}


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
async def create_tag(tag: Dict[str, Any]):
    """Create a new meta tag"""
    db.cursor.execute("""
        INSERT INTO meta_tags 
        (tag_name, tag_description, category_id, created_by)
        VALUES (%s, %s, %s, %s)
    """, (
        tag['tag_name'],
        tag.get('tag_description', ''),
        tag.get('category_id', 1),  # Default to first category
        tag.get('created_by', 'admin')
    ))
    db.commit()
    
    return {'success': True, 'tag_id': db.cursor.lastrowid, 'tag_name': tag['tag_name']}


@app.put("/api/tags/{tag_id}")
async def update_tag(tag_id: int, updates: Dict[str, Any]):
    """Update tag metadata"""
    allowed_fields = ['tag_name', 'tag_description', 'category_id']
    
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
async def delete_tag(tag_id: int):
    """Soft-delete a tag"""
    # Check if tag exists
    db.cursor.execute("SELECT tag_id FROM meta_tags WHERE tag_id = %s", (tag_id,))
    if not db.cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tag not found")
    
    # Soft delete
    db.cursor.execute("""
        UPDATE meta_tags
        SET is_active = false
        WHERE tag_id = %s
    """, (tag_id,))
    db.commit()
    
    return {'success': True, 'tag_id': tag_id}


@app.post("/api/tags/categories")
async def create_tag_category(category: Dict[str, Any]):
    """Create a new tag category"""
    # Get max display_order
    db.cursor.execute("SELECT MAX(display_order) as max_order FROM meta_tag_categories")
    result = db.cursor.fetchone()
    next_order = (result['max_order'] or 0) + 1
    
    db.cursor.execute("""
        INSERT INTO meta_tag_categories 
        (category_name, description, display_order)
        VALUES (%s, %s, %s)
    """, (
        category['category_name'],
        category.get('description', ''),
        category.get('display_order', next_order)
    ))
    db.commit()
    
    return {'success': True, 'category_id': db.cursor.lastrowid}


# ============================================================================
# STATIC FILES & ROOT
# ============================================================================

# ============================================================================
# HISTORY & TRACKING ENDPOINTS
# ============================================================================

@app.get("/api/history/changes")
async def get_change_history(
    instance_id: str = None,
    plugin_name: str = None,
    changed_by: str = None,
    change_type: str = None,
    limit: int = 100,
    offset: int = 0
):
    """Get config change history with filters"""
    query = "SELECT * FROM config_change_history WHERE 1=1"
    params = []
    
    if instance_id:
        query += " AND instance_id = %s"
        params.append(instance_id)
    
    if plugin_name:
        query += " AND plugin_name = %s"
        params.append(plugin_name)
    
    if changed_by:
        query += " AND changed_by = %s"
        params.append(changed_by)
    
    if change_type:
        query += " AND change_type = %s"
        params.append(change_type)
    
    query += " ORDER BY changed_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    db.cursor.execute(query, params)
    changes = db.cursor.fetchall()
    
    # Get total count
    count_query = query.replace("SELECT *", "SELECT COUNT(*)").split(" ORDER BY")[0]
    db.cursor.execute(count_query, params[:-2])
    total = db.cursor.fetchone()[0]
    
    return {
        "changes": changes,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/history/deployments")
async def get_deployment_history(
    deployed_by: str = None,
    status: str = None,
    deployment_type: str = None,
    limit: int = 50,
    offset: int = 0
):
    """Get deployment history with filters"""
    query = "SELECT * FROM deployment_history WHERE 1=1"
    params = []
    
    if deployed_by:
        query += " AND deployed_by = %s"
        params.append(deployed_by)
    
    if status:
        query += " AND deployment_status = %s"
        params.append(status)
    
    if deployment_type:
        query += " AND deployment_type = %s"
        params.append(deployment_type)
    
    query += " ORDER BY deployed_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])
    
    db.cursor.execute(query, params)
    deployments = db.cursor.fetchall()
    
    # Get total count
    count_query = query.replace("SELECT *", "SELECT COUNT(*)").split(" ORDER BY")[0]
    db.cursor.execute(count_query, params[:-2])
    total = db.cursor.fetchone()[0]
    
    return {
        "deployments": deployments,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/migrations")
async def get_all_migrations():
    """Get all config key migrations"""
    db.cursor.execute("""
        SELECT * FROM config_key_migrations
        ORDER BY plugin_name, from_version, to_version
    """)
    migrations = db.cursor.fetchall()
    return {"migrations": migrations, "total": len(migrations)}


@app.get("/api/migrations/{plugin_name}")
async def get_plugin_migrations(plugin_name: str):
    """Get known migrations for a specific plugin"""
    db.cursor.execute("""
        SELECT * FROM config_key_migrations
        WHERE plugin_name = %s
        ORDER BY from_version, to_version
    """, (plugin_name,))
    
    migrations = db.cursor.fetchall()
    
    return {
        "plugin": plugin_name,
        "migrations": migrations,
        "total": len(migrations)
    }


@app.get("/api/variance/history")
async def get_variance_history(
    instance_id: str = None,
    plugin_name: str = None,
    config_key: str = None,
    limit: int = 100
):
    """Get historical variance snapshots"""
    query = "SELECT * FROM config_variance_history WHERE 1=1"
    params = []
    
    if instance_id:
        query += " AND instance_id = %s"
        params.append(instance_id)
    
    if plugin_name:
        query += " AND plugin_name = %s"
        params.append(plugin_name)
    
    if config_key:
        query += " AND config_key = %s"
        params.append(config_key)
    
    query += " ORDER BY snapshot_at DESC LIMIT %s"
    params.append(limit)
    
    db.cursor.execute(query, params)
    history = db.cursor.fetchall()
    
    return {"history": history, "total": len(history)}


@app.get("/api/notifications")
async def get_notification_log(
    notification_type: str = None,
    status: str = None,
    limit: int = 50
):
    """Get notification log"""
    query = "SELECT * FROM notification_log WHERE 1=1"
    params = []
    
    if notification_type:
        query += " AND notification_type = %s"
        params.append(notification_type)
    
    if status:
        query += " AND status = %s"
        params.append(status)
    
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)
    
    db.cursor.execute(query, params)
    notifications = db.cursor.fetchall()
    
    return {"notifications": notifications, "total": len(notifications)}


@app.post("/api/notifications/{notification_id}/mark-read")
async def mark_notification_read(notification_id: int, read_by: str = "web_user"):
    """Mark notification as read"""
    db.cursor.execute("""
        UPDATE notification_log
        SET read_at = NOW(), read_by = %s
        WHERE id = %s
    """, (read_by, notification_id))
    db.commit()
    return {"success": True}


@app.get("/api/templates")
async def get_config_templates(plugin_name: str = None):
    """Get config templates"""
    query = "SELECT * FROM config_templates WHERE 1=1"
    params = []
    
    if plugin_name:
        query += " AND plugin_name = %s"
        params.append(plugin_name)
    
    query += " ORDER BY created_at DESC"
    
    db.cursor.execute(query, params)
    templates = db.cursor.fetchall()
    
    return {"templates": templates, "total": len(templates)}


@app.get("/api/metrics/performance")
async def get_performance_metrics(hours: int = 24):
    """Get performance metrics summary"""
    db.cursor.execute("""
        SELECT 
            metric_name,
            component,
            AVG(metric_value) as avg_value,
            MIN(metric_value) as min_value,
            MAX(metric_value) as max_value,
            COUNT(*) as sample_count
        FROM system_health_metrics
        WHERE recorded_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
        GROUP BY metric_name, component
        ORDER BY metric_name
    """, (hours,))
    
    metrics = db.cursor.fetchall()
    return {"metrics": metrics, "hours": hours}


@app.get("/api/approval/pending")
async def get_pending_approvals():
    """Get pending approval requests"""
    db.cursor.execute("""
        SELECT * FROM change_approval_requests
        WHERE status = 'pending'
        ORDER BY created_at DESC
    """)
    
    requests = db.cursor.fetchall()
    return {"pending_requests": requests, "total": len(requests)}


@app.post("/api/approval/{request_id}/vote")
async def vote_on_approval(request_id: int, approved: bool, voted_by: str, comment: str = ""):
    """Vote on an approval request"""
    from ..agent.approval_workflow import create_approval_workflow
    
    workflow = create_approval_workflow(db.conn)
    result = workflow.add_approval(request_id, voted_by, approved, comment)
    
    return {"success": True, "status": result}


# ============================================================================
# UI ENDPOINTS
# ============================================================================

# Serve static frontend files
BASE_DIR = Path(__file__).parent.parent.parent
static_dir = BASE_DIR / "src" / "web" / "static"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main web UI - redirect to dashboard"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return html_file.read_text()
    return """
    <html>
        <head><title>ArchiveSMP Config Manager</title></head>
        <body>
            <h1>ArchiveSMP Configuration Manager</h1>
            <p>Web GUI not yet deployed. API is running.</p>
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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_ui():
    """Serve dashboard UI"""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return html_file.read_text()
    raise HTTPException(status_code=404, detail="Dashboard UI not found")

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
