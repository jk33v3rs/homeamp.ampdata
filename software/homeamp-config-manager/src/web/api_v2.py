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
    db = ConfigDatabase(
        host='135.181.212.169',
        port=3369,
        user='sqlworkerSMP',
        password='SQLdb2024!'
    )
    db.connect()

@app.on_event("shutdown")
async def shutdown():
    """Close database connection"""
    if db:
        db.disconnect()


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
    """Get plugin information"""
    # Query distinct plugins from instances (would need plugin tracking table)
    return []


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
    """Serve main web UI"""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
