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
    """Get plugin information"""
    # Query distinct plugins from instances (would need plugin tracking table)
    return []


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


# ============================================================================
# PLUGIN UPDATE TRACKING
# ============================================================================

@app.get("/api/plugins")
async def list_all_plugins():
    """List all plugins with their update status"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT 
            pus.plugin_name,
            pus.latest_version,
            pus.latest_source,
            pus.update_available_count,
            pus.risk_level,
            pus.last_checked,
            COUNT(DISTINCT ip.instance_name) as installed_count,
            GROUP_CONCAT(DISTINCT ip.version_string) as current_versions
        FROM plugin_update_status pus
        LEFT JOIN installed_plugins ip ON pus.plugin_name = ip.plugin_name
        GROUP BY pus.plugin_name
        ORDER BY pus.update_available_count DESC, pus.plugin_name
    """)
    
    plugins = db.cursor.fetchall()
    return {"plugins": plugins, "total": len(plugins)}


@app.get("/api/plugins/{plugin_name}")
async def get_plugin_details(plugin_name: str):
    """Get detailed information about a specific plugin"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    # Get plugin update status
    db.cursor.execute("""
        SELECT * FROM plugin_update_status WHERE plugin_name = %s
    """, (plugin_name,))
    status = db.cursor.fetchone()
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin_name} not found")
    
    # Get all sources
    db.cursor.execute("""
        SELECT * FROM plugin_sources 
        WHERE plugin_name = %s AND is_active = TRUE
        ORDER BY priority
    """, (plugin_name,))
    sources = db.cursor.fetchall()
    
    # Get installed versions
    db.cursor.execute("""
        SELECT 
            ip.*,
            i.server_name
        FROM installed_plugins ip
        JOIN instances i ON ip.instance_name = i.instance_name
        WHERE ip.plugin_name = %s
        ORDER BY i.server_name, ip.instance_name
    """, (plugin_name,))
    installations = db.cursor.fetchall()
    
    # Get version history
    db.cursor.execute("""
        SELECT * FROM plugin_versions
        WHERE plugin_name = %s
        ORDER BY version_major DESC, version_minor DESC, version_patch DESC, discovered_at DESC
        LIMIT 20
    """, (plugin_name,))
    version_history = db.cursor.fetchall()
    
    # Get documentation
    db.cursor.execute("""
        SELECT * FROM plugin_documentation
        WHERE plugin_name = %s
        ORDER BY is_primary DESC, doc_type
    """, (plugin_name,))
    documentation = db.cursor.fetchall()
    
    return {
        "plugin_name": plugin_name,
        "status": status,
        "sources": sources,
        "installations": installations,
        "version_history": version_history,
        "documentation": documentation
    }


@app.get("/api/plugins/outdated")
async def get_outdated_plugins():
    """Get plugins that have updates available"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT 
            pus.*,
            COUNT(DISTINCT ip.instance_name) as instances_needing_update
        FROM plugin_update_status pus
        JOIN installed_plugins ip ON pus.plugin_name = ip.plugin_name
        WHERE pus.update_available_count > 0
        AND ip.version_string != pus.latest_version
        GROUP BY pus.plugin_name
        ORDER BY pus.risk_level DESC, pus.update_available_count DESC
    """)
    
    outdated = db.cursor.fetchall()
    return {"plugins": outdated, "count": len(outdated)}


@app.post("/api/plugins/check-updates")
async def check_plugin_updates():
    """Trigger plugin update check for all configured sources"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    import httpx
    import asyncio
    from datetime import datetime
    
    # Get all active plugin sources
    db.cursor.execute("""
        SELECT DISTINCT plugin_name, source_type, source_identifier
        FROM plugin_sources
        WHERE is_active = TRUE
        ORDER BY plugin_name, priority
    """)
    sources = db.cursor.fetchall()
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for source in sources:
            plugin_name = source['plugin_name']
            source_type = source['source_type']
            identifier = source['source_identifier']
            
            try:
                if source_type == 'github':
                    # GitHub releases
                    url = f"https://api.github.com/repos/{identifier}/releases/latest"
                    response = await client.get(url, headers={"Accept": "application/vnd.github+json"})
                    
                    if response.status_code == 200:
                        data = response.json()
                        version = data['tag_name'].lstrip('v')
                        download_url = None
                        for asset in data.get('assets', []):
                            if asset['name'].endswith('.jar'):
                                download_url = asset['browser_download_url']
                                break
                        
                        # Insert/update version
                        db.cursor.execute("""
                            INSERT INTO plugin_versions 
                            (plugin_name, version_string, source_type, download_url, release_date, changelog, is_prerelease)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                download_url = VALUES(download_url),
                                changelog = VALUES(changelog)
                        """, (plugin_name, version, 'github', download_url, data['published_at'], 
                              data.get('body', ''), data.get('prerelease', False)))
                        
                        results.append({"plugin": plugin_name, "version": version, "source": "github", "success": True})
                
                elif source_type == 'spigot':
                    # SpigotMC API
                    url = f"https://api.spigotmc.org/legacy/update.php?resource={identifier}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        version = response.text.strip()
                        db.cursor.execute("""
                            INSERT INTO plugin_versions 
                            (plugin_name, version_string, source_type, download_url)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE plugin_name = plugin_name
                        """, (plugin_name, version, 'spigot', f"https://www.spigotmc.org/resources/{identifier}/"))
                        
                        results.append({"plugin": plugin_name, "version": version, "source": "spigot", "success": True})
                
                elif source_type == 'modrinth':
                    # Modrinth API
                    url = f"https://api.modrinth.com/v2/project/{identifier}/version"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        versions_data = response.json()
                        if versions_data:
                            latest = versions_data[0]
                            version = latest['version_number']
                            download_url = latest['files'][0]['url'] if latest['files'] else None
                            
                            db.cursor.execute("""
                                INSERT INTO plugin_versions 
                                (plugin_name, version_string, source_type, download_url, release_date, changelog)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE download_url = VALUES(download_url)
                            """, (plugin_name, version, 'modrinth', download_url, 
                                  latest['date_published'], latest.get('changelog', '')))
                            
                            results.append({"plugin": plugin_name, "version": version, "source": "modrinth", "success": True})
                
                elif source_type == 'hangar':
                    # Hangar (Paper plugins)
                    url = f"https://hangar.papermc.io/api/v1/projects/{identifier}/versions"
                    response = await client.get(url, headers={"Accept": "application/json"})
                    
                    if response.status_code == 200:
                        versions_data = response.json()
                        if versions_data.get('result'):
                            latest = versions_data['result'][0]
                            version = latest['name']
                            
                            db.cursor.execute("""
                                INSERT INTO plugin_versions 
                                (plugin_name, version_string, source_type, download_url, release_date, changelog)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE download_url = VALUES(download_url)
                            """, (plugin_name, version, 'hangar',
                                  f"https://hangar.papermc.io/{identifier}/versions/{version}",
                                  latest.get('createdAt'), latest.get('description', '')))
                            
                            results.append({"plugin": plugin_name, "version": version, "source": "hangar", "success": True})
                
            except Exception as e:
                results.append({"plugin": plugin_name, "source": source_type, "success": False, "error": str(e)})
    
    db.commit()
    
    # Update plugin_update_status table
    db.cursor.execute("""
        UPDATE plugin_update_status pus
        JOIN (
            SELECT plugin_name, MAX(CONCAT(version_major, '.', version_minor, '.', version_patch)) as latest
            FROM plugin_versions
            GROUP BY plugin_name
        ) latest ON pus.plugin_name = latest.plugin_name
        SET pus.last_checked = NOW()
    """)
    db.commit()
    
    return {
        "success": True,
        "checked": len(sources),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# CI/CD INTEGRATION
# ============================================================================

@app.get("/api/cicd/endpoints")
async def list_cicd_endpoints():
    """List all configured CI/CD endpoints"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT * FROM ci_cd_endpoints
        WHERE is_active = TRUE
        ORDER BY plugin_name, ci_type
    """)
    
    endpoints = db.cursor.fetchall()
    return {"endpoints": endpoints, "count": len(endpoints)}


@app.post("/api/cicd/endpoints")
async def add_cicd_endpoint(endpoint: Dict[str, Any]):
    """Add a new CI/CD endpoint"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        INSERT INTO ci_cd_endpoints 
        (plugin_name, ci_type, endpoint_url, artifact_pattern, auth_required)
        VALUES (%s, %s, %s, %s, %s)
    """, (endpoint['plugin_name'], endpoint['ci_type'], endpoint['endpoint_url'],
          endpoint.get('artifact_pattern'), endpoint.get('auth_required', False)))
    db.commit()
    
    return {"success": True, "endpoint_id": db.cursor.lastrowid}


@app.get("/api/cicd/builds/{plugin_name}")
async def get_cicd_builds(plugin_name: str, limit: int = 20):
    """Get recent CI/CD builds for a plugin"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT 
            b.*,
            e.ci_type,
            e.endpoint_url
        FROM ci_cd_builds b
        JOIN ci_cd_endpoints e ON b.endpoint_id = e.endpoint_id
        WHERE b.plugin_name = %s
        ORDER BY b.build_timestamp DESC
        LIMIT %s
    """, (plugin_name, limit))
    
    builds = db.cursor.fetchall()
    return {"plugin_name": plugin_name, "builds": builds, "count": len(builds)}


@app.post("/api/cicd/check-builds")
async def check_cicd_builds():
    """Check all CI/CD endpoints for new builds"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    import httpx
    from datetime import datetime
    
    # Get all active CI/CD endpoints
    db.cursor.execute("""
        SELECT * FROM ci_cd_endpoints
        WHERE is_active = TRUE
    """)
    endpoints = db.cursor.fetchall()
    
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for endpoint in endpoints:
            try:
                ci_type = endpoint['ci_type']
                endpoint_url = endpoint['endpoint_url']
                plugin_name = endpoint['plugin_name']
                
                if ci_type == 'github_actions':
                    # GitHub Actions workflow runs
                    # URL format: https://api.github.com/repos/owner/repo/actions/runs
                    response = await client.get(endpoint_url, headers={"Accept": "application/vnd.github+json"})
                    
                    if response.status_code == 200:
                        data = response.json()
                        for run in data.get('workflow_runs', [])[:5]:  # Last 5 runs
                            if run['status'] == 'completed' and run['conclusion'] == 'success':
                                # Insert build record
                                db.cursor.execute("""
                                    INSERT INTO ci_cd_builds
                                    (endpoint_id, plugin_name, build_number, build_url, build_status, 
                                     commit_sha, branch_name, build_timestamp)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    ON DUPLICATE KEY UPDATE build_status = VALUES(build_status)
                                """, (endpoint['endpoint_id'], plugin_name, str(run['id']), 
                                      run['html_url'], 'success', run['head_sha'], 
                                      run['head_branch'], run['created_at']))
                        
                        results.append({"plugin": plugin_name, "ci_type": ci_type, "success": True})
                
                elif ci_type == 'jenkins':
                    # Jenkins API
                    # URL format: http://jenkins.example.com/job/PluginName/api/json
                    response = await client.get(f"{endpoint_url}/api/json")
                    
                    if response.status_code == 200:
                        data = response.json()
                        for build in data.get('builds', [])[:5]:
                            build_url = build['url']
                            build_response = await client.get(f"{build_url}/api/json")
                            build_data = build_response.json()
                            
                            status = 'success' if build_data['result'] == 'SUCCESS' else 'failure'
                            
                            db.cursor.execute("""
                                INSERT INTO ci_cd_builds
                                (endpoint_id, plugin_name, build_number, build_url, build_status, build_timestamp)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE build_status = VALUES(build_status)
                            """, (endpoint['endpoint_id'], plugin_name, str(build_data['number']),
                                  build_url, status, datetime.fromtimestamp(build_data['timestamp']/1000)))
                        
                        results.append({"plugin": plugin_name, "ci_type": ci_type, "success": True})
                
            except Exception as e:
                results.append({"plugin": plugin_name, "ci_type": ci_type, "success": False, "error": str(e)})
    
    db.commit()
    
    return {
        "success": True,
        "checked": len(endpoints),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# DOCUMENTATION TRACKING
# ============================================================================

@app.get("/api/docs/{plugin_name}")
async def get_plugin_documentation(plugin_name: str):
    """Get all documentation sources for a plugin"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT * FROM plugin_documentation
        WHERE plugin_name = %s
        ORDER BY is_primary DESC, doc_type
    """, (plugin_name,))
    
    docs = db.cursor.fetchall()
    return {"plugin_name": plugin_name, "documentation": docs, "count": len(docs)}


@app.post("/api/docs")
async def add_plugin_documentation(doc: Dict[str, Any]):
    """Add a documentation source for a plugin"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        INSERT INTO plugin_documentation
        (plugin_name, doc_type, doc_url, title, is_primary)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            is_primary = VALUES(is_primary),
            updated_at = NOW()
    """, (doc['plugin_name'], doc['doc_type'], doc['doc_url'],
          doc.get('title'), doc.get('is_primary', False)))
    db.commit()
    
    return {"success": True, "doc_id": db.cursor.lastrowid}


@app.get("/api/pages/{plugin_name}")
async def get_plugin_pages(plugin_name: str):
    """Get all tracked plugin pages (Spigot, Modrinth, etc.)"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT * FROM plugin_pages_tracked
        WHERE plugin_name = %s
        ORDER BY page_type
    """, (plugin_name,))
    
    pages = db.cursor.fetchall()
    return {"plugin_name": plugin_name, "pages": pages, "count": len(pages)}


# ============================================================================
# DATAPACK MANAGEMENT
# ============================================================================

@app.get("/api/datapacks")
async def list_datapacks():
    """List all available datapacks"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT 
            d.*,
            COUNT(DISTINCT id.instance_name) as installation_count
        FROM datapacks d
        LEFT JOIN installed_datapacks id ON d.datapack_name = id.datapack_name
        GROUP BY d.datapack_id
        ORDER BY d.datapack_name, d.version_string DESC
    """)
    
    datapacks = db.cursor.fetchall()
    return {"datapacks": datapacks, "total": len(datapacks)}


@app.get("/api/datapacks/{datapack_name}")
async def get_datapack_details(datapack_name: str):
    """Get details about a specific datapack"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT * FROM datapacks WHERE datapack_name = %s
        ORDER BY version_string DESC
    """, (datapack_name,))
    versions = db.cursor.fetchall()
    
    if not versions:
        raise HTTPException(status_code=404, detail=f"Datapack {datapack_name} not found")
    
    # Get installations
    db.cursor.execute("""
        SELECT 
            id.*,
            i.server_name
        FROM installed_datapacks id
        JOIN instances i ON id.instance_name = i.instance_name
        WHERE id.datapack_name = %s
        ORDER BY i.server_name, id.instance_name, id.world_name
    """, (datapack_name,))
    installations = db.cursor.fetchall()
    
    return {
        "datapack_name": datapack_name,
        "versions": versions,
        "installations": installations
    }


@app.post("/api/datapacks")
async def add_datapack(datapack: Dict[str, Any]):
    """Add a new datapack to the registry"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        INSERT INTO datapacks
        (datapack_name, version_string, minecraft_version, source_url, description, author, file_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (datapack['datapack_name'], datapack.get('version_string'), 
          datapack.get('minecraft_version'), datapack.get('source_url'),
          datapack.get('description'), datapack.get('author'), datapack.get('file_hash')))
    db.commit()
    
    return {"success": True, "datapack_id": db.cursor.lastrowid}


@app.get("/api/datapacks/installed/{instance_name}")
async def get_installed_datapacks(instance_name: str):
    """Get all datapacks installed on an instance"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT 
            id.*,
            d.description,
            d.author,
            d.source_url
        FROM installed_datapacks id
        LEFT JOIN datapacks d ON id.datapack_name = d.datapack_name 
            AND id.version_string = d.version_string
        WHERE id.instance_name = %s
        ORDER BY id.world_name, id.datapack_name
    """, (instance_name,))
    
    datapacks = db.cursor.fetchall()
    return {"instance_name": instance_name, "datapacks": datapacks, "count": len(datapacks)}


# ============================================================================
# PLUGIN DEPLOYMENT
# ============================================================================

@app.post("/api/plugins/deploy")
async def deploy_plugin_update(deployment: Dict[str, Any]):
    """Deploy a plugin update to specified instances"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    import json
    
    plugin_name = deployment['plugin_name']
    to_version = deployment['to_version']
    target_instances = deployment['target_instances']
    initiated_by = deployment.get('initiated_by', 'admin')
    
    # Create deployment record
    db.cursor.execute("""
        INSERT INTO plugin_deployments
        (plugin_name, to_version, target_instances, initiated_by, deployment_status)
        VALUES (%s, %s, %s, %s, 'pending')
    """, (plugin_name, to_version, json.dumps(target_instances), initiated_by))
    deployment_id = db.cursor.lastrowid
    db.commit()
    
    return {
        "success": True,
        "deployment_id": deployment_id,
        "message": f"Deployment initiated for {plugin_name} version {to_version}",
        "target_instances": target_instances
    }


@app.get("/api/plugins/deployments")
async def list_plugin_deployments(limit: int = 50):
    """List recent plugin deployments"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not connected")
    
    db.cursor.execute("""
        SELECT * FROM plugin_deployments
        ORDER BY started_at DESC
        LIMIT %s
    """, (limit,))
    
    deployments = db.cursor.fetchall()
    return {"deployments": deployments, "count": len(deployments)}


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
