"""
Web API Module

FastAPI-based REST API for the configuration management system.
Provides endpoints for viewing reports, submitting changes, and managing operations.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic import BaseModel
import json
from datetime import datetime

from .models import (
    DeviationParser, DeviationManager, DeviationItem, DeviationStatus,
    ServerView, GlobalView, PluginConfig
)
from ..core.settings import get_settings
from ..updaters.bedrock_updater import BedrockUpdater
import httpx
import asyncio


app = FastAPI(
    title="ArchiveSMP Configuration Manager",
    description="Distributed configuration management for ArchiveSMP Minecraft network",
    version="1.0.0"
)

# Initialize settings - use same config as agent service
config_file = Path("/etc/archivesmp/agent.yaml")
if not config_file.exists():
    config_file = None  # Fall back to search
settings = get_settings(config_file)

BASE_DIR = Path(__file__).parent.parent.parent
REPO_ROOT = BASE_DIR.parent.parent  # Navigate to homeamp.ampdata root
# Use direct paths with fallbacks
DEVIATIONS_FILE = BASE_DIR / "data" / "deviations.json"
UNIVERSAL_FILE = BASE_DIR / "data" / "universal_configs.json"
REVIEWS_DIR = settings.data_dir / "reviews"

parser = DeviationParser(DEVIATIONS_FILE, UNIVERSAL_FILE, REPO_ROOT)
manager = DeviationManager(REVIEWS_DIR)


@app.on_event("startup")
async def startup_event():
    """Load configuration data on startup"""
    parser.load_universal_configs()
    parser.load_deviations()
    manager.load_reviews()


# Pydantic models for request/response
class ChangeRequest(BaseModel):
    """Change request model"""
    plugin: str
    config_file: str
    key_path: str
    expected_value: Any
    new_value: Any
    applies_to_servers: List[str]
    reason: str
    priority: str


class ChangeRequestBatch(BaseModel):
    """Batch of change requests"""
    change_id: str
    created_by: str
    reason: str
    priority: str
    changes: List[ChangeRequest]


class DeviationReview(BaseModel):
    """Deviation review submission"""
    deviation_id: str
    status: DeviationStatus
    replacement_value: Optional[Any] = None
    notes: str = ""
    flagged_by: str


# Serve static frontend
try:
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "src" / "web" / "static")), name="static")
except RuntimeError:
    pass  # Directory doesn't exist yet


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main web UI"""
    html_file = BASE_DIR / "src" / "web" / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return """
    <html>
        <head><title>ArchiveSMP Config Manager</title></head>
        <body>
            <h1>ArchiveSMP Configuration Manager</h1>
            <p>API Documentation: <a href="/docs">/docs</a></p>
            <ul>
                <li><a href="/api/views/global">Global View</a></li>
                <li><a href="/api/deviations">All Deviations</a></li>
                <li><a href="/api/deviations/pending">Pending Review</a></li>
            </ul>
        </body>
    </html>
    """


# ============================================================================
# DEVIATION REVIEW ENDPOINTS
# ============================================================================

@app.get("/api/deviations")
async def get_all_deviations() -> List[DeviationItem]:
    """Get all deviations"""
    return parser.deviations


@app.get("/api/deviations/pending")
async def get_pending_deviations() -> List[DeviationItem]:
    """Get deviations pending review"""
    return parser.get_deviations_by_status(DeviationStatus.PENDING_REVIEW)


@app.get("/api/deviations/flagged-bad")
async def get_flagged_bad_deviations() -> List[DeviationItem]:
    """Get deviations flagged as bad (need fixing)"""
    return parser.get_deviations_by_status(DeviationStatus.FLAGGED_BAD)


@app.get("/api/deviations/server/{server_name}")
async def get_server_deviations(server_name: str) -> List[DeviationItem]:
    """Get deviations for specific server"""
    return parser.get_deviations_by_server(server_name)


@app.get("/api/deviations/plugin/{plugin_name}")
async def get_plugin_deviations(plugin_name: str) -> List[DeviationItem]:
    """Get deviations for specific plugin"""
    return parser.get_deviations_by_plugin(plugin_name)


@app.post("/api/deviations/review")
async def submit_deviation_review(review: DeviationReview) -> Dict[str, str]:
    """
    Flag a deviation as good or bad
    
    If flagged as bad, must provide replacement_value
    """
    if review.status == DeviationStatus.FLAGGED_BAD and review.replacement_value is None:
        raise HTTPException(status_code=400, detail="replacement_value required when flagging as bad")
    
    success = manager.flag_deviation(
        review.deviation_id,
        review.status,
        review.replacement_value,
        review.notes,
        review.flagged_by
    )
    
    if success:
        manager.save_reviews()
        return {"status": "success", "message": "Review saved"}
    else:
        raise HTTPException(status_code=404, detail="Deviation not found")


@app.get("/api/deviations/generate-fixes")
async def generate_fix_changes() -> Dict[str, Any]:
    """
    Generate change request JSON for all flagged bad deviations
    
    Returns expected_changes_template.json format
    """
    return manager.generate_fix_changes()


# ============================================================================
# VIEW ENDPOINTS (Global, Server, Instance)
# ============================================================================

@app.get("/api/views/global")
async def get_global_view() -> GlobalView:
    """Get global network view with all servers"""
    # Get server list from settings
    servers = settings.all_servers
    
    server_views = []
    total_deviations = 0
    critical_issues = 0
    active_agents = 0
    
    for server in servers:
        server_view = await get_server_view(server)
        server_views.append(server_view)
        total_deviations += server_view.total_deviations
        critical_issues += server_view.flagged_bad
        if server_view.agent_status == "active":
            active_agents += 1
    
    # Get pending changes count
    pending_dir = BASE_DIR / "data" / "pending_changes"
    pending_changes = len(list(pending_dir.glob("*.json"))) if pending_dir.exists() else 0
    
    return GlobalView(
        total_servers=len(servers),
        active_agents=active_agents,
        total_deviations=total_deviations,
        critical_issues=critical_issues,
        pending_changes=pending_changes,
        servers=server_views
    )


@app.get("/api/views/server/{server_name}")
async def get_server_view(server_name: str) -> ServerView:
    """Get per-server view"""
    # Get deviations for this server
    server_deviations = parser.get_deviations_by_server(server_name)
    
    # Count by status
    pending = len([d for d in server_deviations if d.status == DeviationStatus.PENDING_REVIEW])
    flagged_bad = len([d for d in server_deviations if d.status == DeviationStatus.FLAGGED_BAD])
    approved_good = len([d for d in server_deviations if d.status == DeviationStatus.APPROVED_GOOD])
    
    # Check for out-of-date plugins using PluginChecker
    out_of_date_plugins = []
    try:
        from ..updaters.plugin_checker import PluginChecker
        api_endpoints_path = settings.config_dir / "plugin_api_endpoints.yaml"
        if api_endpoints_path.exists():
            checker = PluginChecker(api_endpoints_path)
            # This would ideally check utildata path, but for now just check if checker works
            # TODO: Integrate with actual server plugin directories when agent provides data
            pass
    except Exception as e:
        # Silently fail - plugin updates are nice-to-have
        pass
    
    # Check agent status via HTTP to agent API
    agent_status = "unknown"
    try:
        # Try to reach agent on this server
        async with httpx.AsyncClient(timeout=2.0) as client:
            agent_url = settings.agent.base_url or f"http://localhost:{settings.agent.port}"
            response = await client.get(f"{agent_url}/api/agent/status")
            if response.status_code == 200:
                agent_status = "online"
            else:
                agent_status = "error"
    except:
        agent_status = "offline"
    
    # Last drift check - check most recent drift_log entry for this server
    last_drift_check = None
    try:
        # Check if we have any deviations for this server
        if server_deviations:
            # Get most recent deviation timestamp
            timestamps = [d.last_seen for d in server_deviations if hasattr(d, 'last_seen') and d.last_seen]
            if timestamps:
                last_drift_check = max(timestamps)
    except Exception as e:
        pass
    
    return ServerView(
        server_name=server_name,
        total_deviations=len(server_deviations),
        pending_review=pending,
        flagged_bad=flagged_bad,
        approved_good=approved_good,
        out_of_date_plugins=out_of_date_plugins,
        last_drift_check=last_drift_check,
        agent_status=agent_status
    )


@app.get("/api/views/instance/{instance_id}")
async def get_instance_view(instance_id: str) -> Dict[str, Any]:
    """
    Get per-Minecraft-instance view (if multiple instances per server)
    
    Currently assumes 1 instance per server, so instance_id == server_name
    """
    # For now, instance == server
    server_view = await get_server_view(instance_id)
    
    return {
        "instance_id": instance_id,
        "server_name": instance_id,
        "view": server_view.dict()
    }


# ============================================================================
# UNIVERSAL CONFIG ENDPOINTS
# ============================================================================

@app.get("/api/configs/universal")
async def get_universal_configs() -> Dict[str, PluginConfig]:
    """Get all universal configurations"""
    return parser.universal_configs


@app.get("/api/configs/universal/{plugin}")
async def get_plugin_universal_config(plugin: str) -> PluginConfig:
    """Get universal configuration for specific plugin"""
    if plugin not in parser.universal_configs:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin} not found in universal configs")
    return parser.universal_configs[plugin]


# ============================================================================
# VARIANCE ANALYSIS ENDPOINTS
# ============================================================================

@app.get("/api/variance/summary")
async def get_variance_summary() -> Dict[str, Any]:
    """
    Get summary of configuration variance across all plugins and instances.
    Analyzes deviations to identify which configs vary and why.
    """
    # Group deviations by plugin and config key
    variance_map = {}
    
    for deviation in parser.deviations:
        plugin = deviation.plugin
        key = deviation.key_path
        
        if plugin not in variance_map:
            variance_map[plugin] = {}
        
        if key not in variance_map[plugin]:
            variance_map[plugin][key] = {
                "values": {},  # value -> list of instances
                "total_instances": 0,
                "variance_type": None
            }
        
        # Track which instances have which value
        value_str = str(deviation.observed_value)
        if value_str not in variance_map[plugin][key]["values"]:
            variance_map[plugin][key]["values"][value_str] = []
        variance_map[plugin][key]["values"][value_str].append(deviation.server_name)
        variance_map[plugin][key]["total_instances"] += 1
    
    # Calculate variance statistics
    for plugin in variance_map:
        for key in variance_map[plugin]:
            num_unique_values = len(variance_map[plugin][key]["values"])
            if num_unique_values == 1:
                variance_map[plugin][key]["variance_type"] = "none"
            elif num_unique_values == variance_map[plugin][key]["total_instances"]:
                variance_map[plugin][key]["variance_type"] = "instance"
            else:
                variance_map[plugin][key]["variance_type"] = "variable"
    
    return {
        "plugins": list(variance_map.keys()),
        "variance_data": variance_map,
        "total_plugins_with_variance": len(variance_map),
        "generated_at": datetime.now().isoformat()
    }


@app.get("/api/variance/plugin/{plugin_name}")
async def get_plugin_variance(plugin_name: str) -> Dict[str, Any]:
    """Get detailed variance analysis for a specific plugin"""
    plugin_deviations = [d for d in parser.deviations if d.plugin == plugin_name]
    
    if not plugin_deviations:
        raise HTTPException(status_code=404, detail=f"No variance data for plugin {plugin_name}")
    
    # Build detailed variance breakdown
    variance_details = {}
    for deviation in plugin_deviations:
        key = deviation.key_path
        if key not in variance_details:
            variance_details[key] = {
                "instances": {},
                "expected_value": deviation.expected_value,
                "file": getattr(deviation, 'config_file', 'unknown')
            }
        
        variance_details[key]["instances"][deviation.server_name] = {
            "value": deviation.observed_value,
            "status": deviation.status.value if hasattr(deviation.status, 'value') else str(deviation.status),
            "last_seen": deviation.last_seen if hasattr(deviation, 'last_seen') else None
        }
    
    return {
        "plugin": plugin_name,
        "config_keys": variance_details,
        "total_keys": len(variance_details),
        "total_instances": len(plugin_deviations)
    }


@app.get("/api/variance/detail/{plugin_name}/{config_key:path}")
async def get_variance_detail(plugin_name: str, config_key: str) -> Dict[str, Any]:
    """
    Get instance-by-instance breakdown for a specific plugin config key.
    Shows which instances have which values and why.
    """
    # Find all deviations for this plugin + config key
    matching_deviations = [
        d for d in parser.deviations 
        if d.plugin == plugin_name and d.key_path == config_key
    ]
    
    if not matching_deviations:
        raise HTTPException(
            status_code=404, 
            detail=f"No variance data for {plugin_name}::{config_key}"
        )
    
    # Build instance breakdown
    instance_breakdown = []
    for deviation in matching_deviations:
        instance_breakdown.append({
            "instance": deviation.server_name,
            "value": deviation.observed_value,
            "expected": deviation.expected_value,
            "status": deviation.status.value if hasattr(deviation.status, 'value') else str(deviation.status),
            "differs": deviation.observed_value != deviation.expected_value,
            "last_seen": deviation.last_seen if hasattr(deviation, 'last_seen') else None,
            "config_file": getattr(deviation, 'config_file', 'unknown')
        })
    
    # Calculate variance statistics
    unique_values = {}
    for item in instance_breakdown:
        val = str(item["value"])
        if val not in unique_values:
            unique_values[val] = []
        unique_values[val].append(item["instance"])
    
    return {
        "plugin": plugin_name,
        "config_key": config_key,
        "instances": instance_breakdown,
        "unique_values": unique_values,
        "total_instances": len(instance_breakdown),
        "variance_count": len(unique_values)
    }


@app.get("/api/configs/universal/{plugin}")
async def get_plugin_universal_config(plugin: str) -> PluginConfig:
    """Get universal config for specific plugin"""
    if plugin not in parser.universal_configs:
        raise HTTPException(status_code=404, detail=f"Plugin {plugin} not found")
    return parser.universal_configs[plugin]


# ============================================================================
# CHANGE REQUEST UPLOAD ENDPOINT
# ============================================================================

@app.post("/api/changes/upload")
async def upload_change_request(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload change request JSON file (expected_changes_template.json format)
    
    Does NOT auto-apply - requires explicit approval
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files accepted")
    
    try:
        content = await file.read()
        change_data = json.loads(content)
        
        # Validate format
        required_fields = ['change_id', 'created_by', 'reason', 'priority', 'changes']
        for field in required_fields:
            if field not in change_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Store in pending changes
        pending_dir = BASE_DIR / "data" / "pending_changes"
        pending_dir.mkdir(parents=True, exist_ok=True)
        
        change_file = pending_dir / f"{change_data['change_id']}.json"
        with open(change_file, 'w') as f:
            json.dump(change_data, f, indent=2)
        
        return {
            "status": "success",
            "message": "Change request uploaded",
            "change_id": change_data['change_id'],
            "changes_count": len(change_data['changes']),
            "preview_url": f"/api/changes/{change_data['change_id']}/preview"
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


# ============================================================================
# METRICS ENDPOINT
# ============================================================================

@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint
    
    Exports metrics for monitoring via Grafana
    """
    from ..utils.metrics import metrics
    from fastapi.responses import Response
    
    return Response(
        content=metrics.export_metrics(),
        media_type="text/plain; version=0.0.4"
    )


# ============================================================================
# EXISTING REPORT ENDPOINTS
# ============================================================================

@app.get("/api/reports/deviations")
async def get_deviations_report():
    """Get deviation analysis report"""
    report_file = BASE_DIR / settings.get_file_path("deviation_report")
    if report_file.exists():
        return FileResponse(report_file)
    raise HTTPException(status_code=404, detail="Deviation report not found")


@app.get("/api/reports/drift")
async def get_drift_report():
    """Get configuration drift report"""
    # Will be generated by drift_detector
    drift_reports = BASE_DIR / "data" / "reports" / "drift"
    if not drift_reports.exists():
        raise HTTPException(status_code=404, detail="No drift reports available")
    
    # Get most recent report
    reports = sorted(drift_reports.glob("*.json"), reverse=True)
    if not reports:
        raise HTTPException(status_code=404, detail="No drift reports found")
    
    return FileResponse(reports[0])


@app.get("/api/reports/plugin-updates")
async def get_plugin_updates():
    """Get available plugin updates"""
    from ..updaters.plugin_checker import PluginChecker
    
    # Initialize plugin checker
    checker = PluginChecker(BASE_DIR / "config" / settings.get_file_path("plugin_endpoints"))
    
    # Check for updates
    instances_path = settings.instances_path
    update_info = checker.check_all_plugins(instances_path)
    
    return update_info


@app.get("/api/plugins")
async def list_plugins():
    """List all plugins with their current versions and update status"""
    from ..updaters.plugin_checker import PluginChecker
    
    checker = PluginChecker(BASE_DIR / "config" / settings.get_file_path("plugin_endpoints"))
    instances_path = settings.instances_path
    
    # Get all plugin information
    plugin_info = checker.check_all_plugins(instances_path)
    
    # Format for UI display
    plugins = []
    for plugin_name, info in plugin_info.items():
        plugin_data = {
            "name": plugin_name,
            "current_versions": info["current_versions"],
            "latest_version": info["latest_version"],
            "update_available": info["update_available"],
            "source": info["source"],
            "download_url": info["download_url"],
            "changelog": info["changelog"],
            "risk_level": info["risk_level"],
            "servers": list(info["current_versions"].keys())
        }
        plugins.append(plugin_data)
    
    return {"plugins": plugins, "total": len(plugins)}


@app.get("/api/plugins/{plugin_name}")
async def get_plugin_details(plugin_name: str):
    """Get detailed information about a specific plugin"""
    from ..updaters.plugin_checker import PluginChecker
    
    checker = PluginChecker(BASE_DIR / "config" / settings.get_file_path("plugin_endpoints"))
    instances_path = settings.instances_path
    
    plugin_info = checker.check_all_plugins(instances_path)
    
    if plugin_name not in plugin_info:
        raise HTTPException(status_code=404, detail="Plugin not found")
    
    return plugin_info[plugin_name]


@app.get("/api/plugins/outdated")
async def get_outdated_plugins():
    """Get plugins that have available updates"""
    from ..updaters.plugin_checker import PluginChecker
    
    checker = PluginChecker(BASE_DIR / "config" / settings.get_file_path("plugin_endpoints"))
    instances_path = settings.instances_path
    
    plugin_info = checker.check_all_plugins(instances_path)
    
    # Filter to only outdated plugins
    outdated = {name: info for name, info in plugin_info.items() if info["update_available"]}
    
    return {"plugins": outdated, "count": len(outdated)}


@app.get("/api/instances/settings")
async def get_all_instance_settings():
    """Get settings for all instances"""
    from ..core.instance_settings import InstanceSettingsManager
    
    manager = InstanceSettingsManager(settings.data_dir)
    all_settings = manager.get_all_settings()
    
    return JSONResponse(content={
        name: settings_obj.dict()
        for name, settings_obj in all_settings.items()
    })


@app.get("/api/instances/{instance_name}/settings")
async def get_instance_settings(instance_name: str):
    """Get settings for a specific instance"""
    from ..core.instance_settings import InstanceSettingsManager
    
    manager = InstanceSettingsManager(settings.data_dir)
    instance_settings = manager.get_settings(instance_name)
    
    return JSONResponse(content=instance_settings.dict())


@app.post("/api/instances/{instance_name}/settings")
async def update_instance_settings(instance_name: str, updates: Dict[str, Any]):
    """
    Update settings for a specific instance
    
    Request body example:
    {
        "update_mode": "semi_auto",
        "auto_deploy_low_risk": true,
        "excluded_plugins": ["CMI", "CMILib"]
    }
    """
    from ..core.instance_settings import InstanceSettingsManager
    
    manager = InstanceSettingsManager(settings.data_dir)
    updated_settings = manager.update_settings(instance_name, updates)
    
    return JSONResponse(content={
        "success": True,
        "settings": updated_settings.dict()
    })


@app.get("/api/servers")
async def list_servers():
    """List all servers"""
    try:
        # Look for server directories in instances
        servers = []
        instances_path = settings.instances_path
        
        for server_dir in instances_path.iterdir():
            if server_dir.is_dir() and not server_dir.name.startswith('.'):
                server_info = {
                    'name': server_dir.name,
                    'path': str(server_dir),
                    'status': 'unknown'
                }
                
                # Check for specific config files to determine server type
                if (server_dir / 'paper.yml').exists():
                    server_info['type'] = 'paper'
                elif (server_dir / 'bukkit.yml').exists():
                    server_info['type'] = 'bukkit'
                else:
                    server_info['type'] = 'unknown'
                
                servers.append(server_info)
        
        return {"servers": servers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/servers/{server_name}/config")
async def get_server_config(server_name: str):
    """Get server configuration"""
    try:
        instances_path = settings.instances_path
        server_path = instances_path / server_name
        
        if not server_path.exists():
            raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
        
        config_files = {}
        
        # Common config files to check
        config_patterns = [
            "*.yml", "*.yaml", "*.properties", "*.json", "*.conf", "*.cfg"
        ]
        
        for pattern in config_patterns:
            for config_file in server_path.rglob(pattern):
                if config_file.is_file():
                    relative_path = config_file.relative_to(server_path)
                    
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        config_files[str(relative_path)] = {
                            'content': content,
                            'size': len(content),
                            'modified': config_file.stat().st_mtime
                        }
                    except Exception as e:
                        config_files[str(relative_path)] = {
                            'error': f"Could not read file: {e}"
                        }
        
        return {
            "server_name": server_name,
            "server_path": str(server_path),
            "config_files": config_files
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/plugins")
async def list_plugins():
    """List all plugins"""
    from ..updaters.plugin_checker import PluginChecker
    
    try:
        checker = PluginChecker(BASE_DIR / "config" / settings.get_file_path("plugin_endpoints"))
        instances_path = settings.instances_path
        
        # Get all plugin information
        plugin_info = checker.check_all_plugins(instances_path)
        
        # Transform to list format for API
        plugins = []
        for plugin_name, info in plugin_info.items():
            plugins.append({
                'name': plugin_name,
                'installed_versions': info.get('installed_versions', {}),
                'latest_version': info.get('latest_version', 'unknown'),
                'update_available': info.get('update_available', False),
                'servers': list(info.get('installed_versions', {}).keys())
            })
        
        return {"plugins": plugins, "total": len(plugins)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list plugins: {str(e)}")


@app.post("/api/changes/submit")
async def submit_changes(request: dict):
    """Submit configuration changes"""
    try:
        from ..core.cloud_storage import CloudStorage, ChangeRequestManager
        
        # Initialize cloud storage and change manager
        cloud_storage = CloudStorage()
        change_manager = ChangeRequestManager(cloud_storage)
        
        # Upload the change request
        request_id = change_manager.upload_change_request(request)
        
        return {
            "success": True,
            "request_id": request_id,
            "message": "Change request submitted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/changes/{change_id}/approve")
async def approve_changes(change_id: str, approved_by: str = Form(...)):
    """Approve pending change request and start deployment pipeline"""
    from ..deployment.pipeline import DeploymentPipeline
    
    # Load change request
    pending_file = BASE_DIR / "data" / "pending_changes" / f"{change_id}.json"
    if not pending_file.exists():
        raise HTTPException(status_code=404, detail="Change request not found")
    
    with open(pending_file, 'r') as f:
        change_data = json.load(f)
    
    # Create deployment
    pipeline = DeploymentPipeline(BASE_DIR / "data" / "deployments")
    deployment_id = pipeline.create_deployment(change_id, change_data)
    
    # Start deployment to DEV
    try:
        pipeline.deploy_to_dev(deployment_id)
        
        return {
            "status": "deployment_started",
            "deployment_id": deployment_id,
            "message": "Change approved and deployed to DEV01 for testing",
            "status_url": f"/api/deployments/{deployment_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@app.get("/api/changes/{change_id}/preview")
async def preview_changes(change_id: str):
    """Generate preview of changes"""
    pending_file = BASE_DIR / "data" / "pending_changes" / f"{change_id}.json"
    if not pending_file.exists():
        raise HTTPException(status_code=404, detail="Change request not found")
    
    with open(pending_file, 'r') as f:
        change_data = json.load(f)
    
    return change_data


# ============================================================================
# DEPLOYMENT ENDPOINTS
# ============================================================================

@app.get("/api/deployments/{deployment_id}")
async def get_deployment_status(deployment_id: str):
    """Get deployment status"""
    from ..deployment.pipeline import DeploymentPipeline
    
    pipeline = DeploymentPipeline(BASE_DIR / "data" / "deployments")
    try:
        return pipeline.get_deployment_status(deployment_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Deployment not found")


@app.get("/api/deployments")
async def list_deployments():
    """List all active deployments"""
    from ..deployment.pipeline import DeploymentPipeline
    
    pipeline = DeploymentPipeline(BASE_DIR / "data" / "deployments")
    return pipeline.list_active_deployments()


@app.post("/api/deployments/{deployment_id}/approve")
async def approve_deployment(deployment_id: str, approved_by: str = Form(...)):
    """Approve deployment for production rollout"""
    from ..deployment.pipeline import DeploymentPipeline
    
    pipeline = DeploymentPipeline(BASE_DIR / "data" / "deployments")
    try:
        pipeline.approve_for_production(deployment_id, approved_by)
        pipeline.deploy_to_production(deployment_id)
        
        return {
            "status": "deploying_to_production",
            "deployment_id": deployment_id,
            "message": "Deployment approved and rolling out to production"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@app.post("/api/deployments/{deployment_id}/rollback")
async def rollback_deployment(deployment_id: str, reason: str = Form(...)):
    """Rollback a deployment"""
    from ..deployment.pipeline import DeploymentPipeline
    
    pipeline = DeploymentPipeline(BASE_DIR / "data" / "deployments")
    try:
        pipeline.rollback_deployment(deployment_id, reason)
        
        return {
            "status": "rolled_back",
            "deployment_id": deployment_id,
            "message": "Deployment rolled back successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@app.post("/api/changes/{change_id}/rollback")
async def rollback_changes(change_id: str):
    """Rollback configuration changes"""
    try:
        from ..updaters.config_updater import ConfigUpdater
        
        # Initialize config updater
        instances_path = settings.instances_path
        updater = ConfigUpdater(instances_path, dry_run=False)
        
        # Perform rollback
        result = updater.rollback_change(change_id)
        
        if result.get('success'):
            return {
                "success": True,
                "change_id": change_id,
                "message": "Changes rolled back successfully",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Rollback failed: {result.get('error', 'Unknown error')}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/changes/history")
async def get_change_history():
    """Get change history"""
    try:
        from ..core.cloud_storage import CloudStorage, ChangeRequestManager
        
        # Initialize cloud storage and change manager
        cloud_storage = CloudStorage()
        change_manager = ChangeRequestManager(cloud_storage)
        
        # Get pending and completed changes
        pending_changes = change_manager.list_pending_changes()
        
        # Get completed changes from completed/ directory
        bucket_name = settings.minio_config.bucket_name
        completed_objects = cloud_storage.list_objects(bucket_name, "completed/")
        completed_changes = []
        
        for object_name in completed_objects:
            if object_name.endswith('.json'):
                change_data = cloud_storage.download_json(bucket_name, object_name)
                if change_data:
                    completed_changes.append(change_data)
        
        return {
            "pending_changes": pending_changes,
            "completed_changes": completed_changes,
            "total_pending": len(pending_changes),
            "total_completed": len(completed_changes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/operations/scan-drift")
async def trigger_drift_scan(background_tasks: BackgroundTasks):
    """Trigger configuration drift scan"""
    try:
        from ..core.cloud_storage import CloudStorage, ChangeRequestManager
        
        # Create a drift scan request
        scan_request = {
            'action': 'drift_scan',
            'timestamp': datetime.now().isoformat(),
            'target_servers': 'all',
            'scan_type': 'full'
        }
        
        cloud_storage = CloudStorage()
        change_manager = ChangeRequestManager(cloud_storage)
        
        # Upload as a change request (will be processed by agents)
        request_id = change_manager.upload_change_request(scan_request)
        
        return {
            "success": True,
            "request_id": request_id,
            "message": "Drift scan triggered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/operations/check-updates")
async def trigger_update_check(background_tasks: BackgroundTasks):
    """Trigger plugin update check"""
    try:
        from ..updaters.plugin_checker import PluginChecker
        
        instances_path = settings.instances_path
        plugin_checker = PluginChecker(instances_path)
        
        # Load API endpoints and check for updates
        plugin_checker.load_api_endpoints()
        update_results = plugin_checker.check_all_plugins()
        
        return {
            "success": True,
            "message": "Plugin update check completed",
            "results": update_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BEDROCK COMPATIBILITY ENDPOINTS
# ============================================================================

@app.get("/api/bedrock/versions")
async def check_bedrock_versions():
    """
    Check current versions of all Bedrock-related plugins.
    
    Returns version info for:
    - Geyser (standalone & spigot)
    - Floodgate (standalone & spigot)
    - ViaVersion (Hangar snapshots)
    - ViaBackwards (Hangar snapshots)
    """
    try:
        updater = BedrockUpdater()
        versions = updater.check_all_versions()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "versions": versions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bedrock/update/full")
async def bedrock_full_update(
    background_tasks: BackgroundTasks,
    restart_services: bool = False
):
    """
    Perform a complete Bedrock compatibility update.
    
    Updates in priority order:
    1. ViaVersion + ViaBackwards (Velocity proxy)
    2. Geyser Standalone
    3. Floodgate (proxy + network)
    
    Args:
        restart_services: Whether to restart affected services after update
    """
    try:
        updater = BedrockUpdater()
        
        # Run update in background
        def run_update():
            return updater.full_bedrock_update(restart_services=restart_services)
        
        # If it's a quick operation, run synchronously
        # Otherwise, could use background_tasks.add_task()
        results = run_update()
        
        return {
            "success": results['overall_success'],
            "message": "Bedrock compatibility update completed",
            "results": results,
            "restart_required": not restart_services
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bedrock/update/geyser")
async def bedrock_update_geyser():
    """Update only Geyser Standalone on the proxy."""
    try:
        updater = BedrockUpdater()
        result = updater.update_geyser_standalone()
        
        return {
            "success": result['success'],
            "message": result.get('message', result.get('error')),
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bedrock/update/via")
async def bedrock_update_via(include_viabackwards: bool = True):
    """
    Update ViaVersion and optionally ViaBackwards on Velocity proxy.
    
    Args:
        include_viabackwards: Also update ViaBackwards (default: True)
    """
    try:
        updater = BedrockUpdater()
        result = updater.update_viaversion(include_viabackwards=include_viabackwards)
        
        return {
            "success": result['success'],
            "message": f"Updated {len(result['plugins'])} plugin(s)",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bedrock/update/floodgate")
async def bedrock_update_floodgate(platform: str = "both"):
    """
    Update Floodgate on proxy and/or network servers.
    
    Args:
        platform: 'standalone', 'spigot', or 'both' (default: 'both')
    """
    try:
        if platform not in ['standalone', 'spigot', 'both']:
            raise HTTPException(
                status_code=400,
                detail="Platform must be 'standalone', 'spigot', or 'both'"
            )
        
        updater = BedrockUpdater()
        result = updater.update_floodgate(platform=platform)
        
        return {
            "success": result['success'],
            "message": f"Floodgate update completed for {platform}",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONFIG DEPLOYMENT ENDPOINTS
# ============================================================================

class ConfigDeploymentRequest(BaseModel):
    """Request to deploy configs to selected instances"""
    configs: Dict[str, Dict[str, Any]]  # {instance_name: {plugin_name: config_data}}
    target_servers: List[str]  # Physical server names: ["Hetzner", "OVH"]
    requester: str


class RestartRequest(BaseModel):
    """Request to restart instances"""
    instances: List[str]  # Instance shortnames
    restart_all: bool = False
    server: str  # "Hetzner", "OVH", or "Both"


# Agent URLs (configured in deployment)
AGENT_URLS = {
    "Hetzner": "http://localhost:8001",  # Agent on Hetzner
    "OVH": "http://37.187.143.41:8001"   # Agent on OVH
}


@app.post("/api/deploy")
async def deploy_configs(request: ConfigDeploymentRequest) -> Dict[str, Any]:
    """
    Deploy configurations to selected instances across servers.
    
    This endpoint:
    1. Groups instances by physical server (Hetzner vs OVH)
    2. Calls each agent's /api/agent/deploy-configs endpoint
    3. Returns consolidated deployment results
    """
    try:
        # Group instances by server
        hetzner_instances = {}
        ovh_instances = {}
        
        for instance_name, plugins_config in request.configs.items():
            # Determine which server this instance is on
            server = _get_instance_server(instance_name)
            
            if server == "Hetzner":
                hetzner_instances[instance_name] = plugins_config
            elif server == "OVH":
                ovh_instances[instance_name] = plugins_config
        
        results = {}
        
        # Deploy to Hetzner instances
        if hetzner_instances and "Hetzner" in request.target_servers:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{AGENT_URLS['Hetzner']}/api/agent/deploy-configs",
                        json={
                            "configs": hetzner_instances,
                            "requester": request.requester,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    response.raise_for_status()
                    results["Hetzner"] = response.json()
            except Exception as e:
                results["Hetzner"] = {"success": False, "error": str(e)}
        
        # Deploy to OVH instances
        if ovh_instances and "OVH" in request.target_servers:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{AGENT_URLS['OVH']}/api/agent/deploy-configs",
                        json={
                            "configs": ovh_instances,
                            "requester": request.requester,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    response.raise_for_status()
                    results["OVH"] = response.json()
            except Exception as e:
                results["OVH"] = {"success": False, "error": str(e)}
        
        # Check overall success
        all_success = all(
            result.get("success", False) 
            for result in results.values()
        )
        
        return {
            "success": all_success,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/restart")
async def restart_instances(request: RestartRequest) -> Dict[str, Any]:
    """
    Restart instances on selected servers.
    
    Executes: sudo -u amp sudo ampinstmgr restart <shortname>
    Or: sudo ampinstmgr restartAll
    """
    try:
        results = {}
        
        # Determine which servers to restart on
        servers_to_restart = []
        if request.server == "Both":
            servers_to_restart = ["Hetzner", "OVH"]
        else:
            servers_to_restart = [request.server]
        
        # Group instances by server
        hetzner_instances = []
        ovh_instances = []
        
        for instance in request.instances:
            server = _get_instance_server(instance)
            if server == "Hetzner":
                hetzner_instances.append(instance)
            elif server == "OVH":
                ovh_instances.append(instance)
        
        # Restart Hetzner instances
        if "Hetzner" in servers_to_restart:
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:  # 5 min timeout
                    response = await client.post(
                        f"{AGENT_URLS['Hetzner']}/api/agent/restart",
                        json={
                            "instances": hetzner_instances if not request.restart_all else [],
                            "restart_all": request.restart_all
                        }
                    )
                    response.raise_for_status()
                    results["Hetzner"] = response.json()
            except Exception as e:
                results["Hetzner"] = {"success": False, "error": str(e)}
        
        # Restart OVH instances
        if "OVH" in servers_to_restart:
            try:
                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        f"{AGENT_URLS['OVH']}/api/agent/restart",
                        json={
                            "instances": ovh_instances if not request.restart_all else [],
                            "restart_all": request.restart_all
                        }
                    )
                    response.raise_for_status()
                    results["OVH"] = response.json()
            except Exception as e:
                results["OVH"] = {"success": False, "error": str(e)}
        
        all_success = all(
            result.get("success", False)
            for result in results.values()
        )
        
        return {
            "success": all_success,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/instances/status")
async def get_instances_status() -> Dict[str, Any]:
    """
    Get status of all instances across both servers.
    
    Returns which instances need restart.
    """
    try:
        results = {}
        
        # Get status from Hetzner
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{AGENT_URLS['Hetzner']}/api/agent/status")
                response.raise_for_status()
                results["Hetzner"] = response.json()
        except Exception as e:
            results["Hetzner"] = {"error": str(e)}
        
        # Get status from OVH
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{AGENT_URLS['OVH']}/api/agent/status")
                response.raise_for_status()
                results["OVH"] = response.json()
        except Exception as e:
            results["OVH"] = {"error": str(e)}
        
        # Consolidate needs_restart lists
        all_needs_restart = []
        if "Hetzner" in results and "needs_restart" in results["Hetzner"]:
            all_needs_restart.extend(results["Hetzner"]["needs_restart"])
        if "OVH" in results and "needs_restart" in results["OVH"]:
            all_needs_restart.extend(results["OVH"]["needs_restart"])
        
        return {
            "servers": results,
            "all_needs_restart": all_needs_restart,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_instance_server(instance_name: str) -> str:
    """
    Determine which physical server an instance is on.
    
    Hetzner instances: BENT01, BIG01, CLIP01, CREA01, DEV01, EVO01, HARD01, 
                       HUB01, MIN01, SMP101, SMP201
    OVH instances: CSMC01, EMAD01, MINE01, PRI01, ROY01, TOW01, etc.
    """
    # Known Hetzner instances (11 instances)
    hetzner_instances = {
        "BENT01", "BIG01", "CLIP01", "CREA01", "DEV01", 
        "EVO01", "HARD01", "HUB01", "MIN01", "SMP101", "SMP201"
    }
    
    if instance_name in hetzner_instances:
        return "Hetzner"
    else:
        return "OVH"


# Pl3xMap tile sync endpoints
@app.post("/api/maps/start-sync")
async def start_tile_sync(request: dict):
    """Start tile sync service on specified server"""
    server = request.get("server", "").lower()
    
    if server == "hetzner":
        agent_url = AGENT_URLS["Hetzner"]
    elif server == "ovh":
        agent_url = AGENT_URLS["OVH"]
    else:
        raise HTTPException(status_code=400, detail="Invalid server. Use 'hetzner' or 'ovh'")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{agent_url}/api/agent/start-tile-sync")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start tile sync: {str(e)}")


@app.post("/api/maps/start-yunohost-sync")
async def start_yunohost_sync():
    """Start YunoHost map sync service"""
    # This would require SSH access to YunoHost or a YunoHost agent
    # For now, return manual instructions
    return {
        "message": "Manual action required",
        "instructions": "SSH to YunoHost and run: sudo systemctl start yunohost-map-sync"
    }


@app.get("/api/maps/status")
async def get_map_sync_status():
    """Get status of all map sync services"""
    status = {
        "hetzner": {"status": "Unknown"},
        "ovh": {"status": "Unknown"},
        "yunohost": {"status": "Unknown"},
        "synced_files": 0,
        "last_sync": None,
        "running": False
    }
    
    try:
        # Check Hetzner
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{AGENT_URLS['Hetzner']}/api/agent/tile-sync-status")
            if response.status_code == 200:
                status["hetzner"] = response.json()
    except:
        pass
    
    try:
        # Check OVH
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{AGENT_URLS['OVH']}/api/agent/tile-sync-status")
            if response.status_code == 200:
                status["ovh"] = response.json()
    except:
        pass
    
    # Determine if any service is running
    status["running"] = (
        status["hetzner"].get("status") == "running" or 
        status["ovh"].get("status") == "running"
    )
    
    return status


@app.get("/api/maps/health")
async def get_map_health():
    """Check health of map system"""
    health = {
        "total_services": 3,
        "services_running": 0,
        "total_instances": 16,
        "instances_syncing": 0,
        "public_maps": 12,
        "private_maps": 4,
        "issues": []
    }
    
    try:
        status = await get_map_sync_status()
        
        if status["hetzner"].get("status") == "running":
            health["services_running"] += 1
        else:
            health["issues"].append("Hetzner tile sync not running")
        
        if status["ovh"].get("status") == "running":
            health["services_running"] += 1
        else:
            health["issues"].append("OVH tile sync not running")
        
        if status["yunohost"].get("status") == "running":
            health["services_running"] += 1
        else:
            health["issues"].append("YunoHost sync not running")
        
        # Count syncing instances
        health["instances_syncing"] = (
            len(status["hetzner"].get("instances", [])) +
            len(status["ovh"].get("instances", []))
        )
    
    except Exception as e:
        health["issues"].append(f"Health check error: {str(e)}")
    
    return health


@app.get("/api/maps/logs")
async def get_map_logs(lines: int = 50):
    """Get recent map sync logs"""
    # This would require access to systemd logs or log files
    return {
        "logs": [
            "Map sync logs not yet implemented",
            "Use: journalctl -u pl3xmap-tile-sync -n 50",
            "Or: journalctl -u yunohost-map-sync -n 50"
        ]
    }


@app.post("/api/maps/stop-all")
async def stop_all_map_sync():
    """Stop all map sync services"""
    results = {}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{AGENT_URLS['Hetzner']}/api/agent/stop-tile-sync")
            results["hetzner"] = response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        results["hetzner"] = {"error": str(e)}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{AGENT_URLS['OVH']}/api/agent/stop-tile-sync")
            results["ovh"] = response.json() if response.status_code == 200 else {"error": response.text}
    except Exception as e:
        results["ovh"] = {"error": str(e)}
    
    return {
        "message": "Stop commands sent to all servers",
        "results": results
    }


# Serve static files for web UI
# app.mount("/static", StaticFiles(directory="static"), name="static")

