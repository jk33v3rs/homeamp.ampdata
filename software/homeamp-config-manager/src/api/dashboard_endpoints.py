"""
Dashboard API Endpoints

Provides network analytics, approval queue, and status information for the dashboard view.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import mysql.connector
import os

# Database connection helper
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "135.181.212.169"),
        user=os.getenv("DB_USER", "sqlworkerSMP"),
        password=os.getenv("DB_PASSWORD", "2024!SQLdb"),
        database=os.getenv("DB_NAME", "asmp_config"),
        port=int(os.getenv("DB_PORT", "3369"))
    )


# Pydantic models
class ApprovalItem(BaseModel):
    id: int
    type: str  # 'plugin_update', 'config_change'
    plugin_name: str
    current_version: Optional[str] = None
    new_version: Optional[str] = None
    instances: List[str]
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class ApprovalQueueSchema(BaseModel):
    items: List[ApprovalItem]
    count: int

class ServerStatus(BaseModel):
    server_name: str
    online: int
    offline: int
    total: int

class NetworkStatusSchema(BaseModel):
    online: int
    offline: int
    total: int
    servers: List[ServerStatus]
    variance_count: int

class PluginSummarySchema(BaseModel):
    total_plugins: int
    needs_update: int
    up_to_date: int

class ActivityLogEntry(BaseModel):
    timestamp: datetime
    event_type: str
    description: str
    instance_id: Optional[str] = None
    user: Optional[str] = None

class DatapackInfo(BaseModel):
    id: int
    instance_id: int
    instance_name: str
    world_path: str
    datapack_name: str
    version: Optional[str] = None
    file_hash: str
    discovered_at: datetime

class OutdatedPlugin(BaseModel):
    plugin_name: str
    current_version: str
    latest_version: str
    instances: List[str]
    last_checked: datetime

class CICDEndpoint(BaseModel):
    id: int
    name: str
    url: str
    type: str
    is_active: bool


# Router setup
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_db_connection():
    """Get database connection"""
    return get_db()


@router.get("/approval-queue", response_model=ApprovalQueueSchema)
async def get_approval_queue():
    """
    Get pending approvals (plugin updates and config changes)
    
    **Semantic**: `DashboardService.getApprovalQueue()`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get pending plugin updates
        update_query = """
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
        """
        cursor.execute(update_query)
        plugin_updates = cursor.fetchall()
        
        # Get pending deployments
        deployment_query = """
            SELECT 
                deployment_id as id,
                'deployment' as type,
                deployment_notes as plugin_name,
                NULL as current_version,
                NULL as new_version,
                target_instances as instances_json,
                deployed_at as timestamp
            FROM deployment_history
            WHERE deployment_status = 'pending'
            ORDER BY deployed_at DESC
            LIMIT 50
        """
        cursor.execute(deployment_query)
        deployments = cursor.fetchall()
        
        # Combine and process
        items = []
        
        for update in plugin_updates:
            items.append(ApprovalItem(
                id=update['id'],
                type=update['type'],
                plugin_name=update['plugin_name'],
                current_version=update['current_version'],
                new_version=update['new_version'],
                instances=[update['instance_id']],
                timestamp=update['timestamp']
            ))
        
        for deploy in deployments:
            # Parse JSON instances if available
            import json
            instances_str = deploy.get('instances_json', '')
            try:
                instances = json.loads(instances_str) if instances_str else []
            except:
                instances = []
            
            items.append(ApprovalItem(
                id=deploy['id'],
                type=deploy['type'],
                plugin_name=deploy['plugin_name'] or 'Deployment',
                instances=instances,
                timestamp=deploy['timestamp']
            ))
        
        return ApprovalQueueSchema(items=items, count=len(items))
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/network-status", response_model=NetworkStatusSchema)
async def get_network_status():
    """
    Get network status (online/offline instances)
    
    **Semantic**: `DashboardService.getNetworkStatus()`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get overall stats (using actual schema - no online_status column yet)
        stats_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as online,
                SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as offline
            FROM instances
        """
        cursor.execute(stats_query)
        overall = cursor.fetchone()
        
        # Get per-server stats
        server_query = """
            SELECT 
                server_name,
                COUNT(*) as total,
                SUM(CASE WHEN is_active = TRUE THEN 1 ELSE 0 END) as online,
                SUM(CASE WHEN is_active = FALSE THEN 1 ELSE 0 END) as offline
            FROM instances
            GROUP BY server_name
        """
        cursor.execute(server_query)
        servers = cursor.fetchall()
        
        # Variance count - return 0 for now (table doesn't exist yet)
        variance_count = 0
        
        server_statuses = [
            ServerStatus(
                server_name=s['server_name'],
                online=int(s['online'] or 0),
                offline=int(s['offline'] or 0),
                total=int(s['total'])
            )
            for s in servers
        ]
        
        return NetworkStatusSchema(
            online=int(overall['online'] or 0),
            offline=int(overall['offline'] or 0),
            total=int(overall['total']),
            servers=server_statuses,
            variance_count=0
        )
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/plugin-summary", response_model=PluginSummarySchema)
async def get_plugin_summary():
    """
    Get plugin summary statistics
    
    **Semantic**: `DashboardService.getPluginSummary()`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                COUNT(DISTINCT plugin_name) as total_plugins,
                SUM(CASE WHEN update_available = TRUE THEN 1 ELSE 0 END) as needs_update,
                SUM(CASE WHEN update_available = FALSE OR update_available IS NULL THEN 1 ELSE 0 END) as up_to_date
            FROM plugin_versions
        """
        cursor.execute(query)
        result = cursor.fetchone()
        
        return PluginSummarySchema(
            total_plugins=int(result['total_plugins'] or 0),
            needs_update=int(result['needs_update'] or 0),
            up_to_date=int(result['up_to_date'] or 0)
        )
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/recent-activity", response_model=List[ActivityLogEntry])
async def get_recent_activity(limit: int = 10):
    """
    Get recent activity log entries
    
    **Semantic**: `DashboardService.getRecentActivity(limit)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Use config_change_history table which exists
        query = """
            SELECT 
                changed_at as timestamp,
                change_type as event_type,
                CONCAT(change_type, ' - ', plugin_name, ': ', config_key) as description,
                instance_id,
                changed_by as user
            FROM config_change_history
            ORDER BY changed_at DESC
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        activities = [
            ActivityLogEntry(
                timestamp=r['timestamp'],
                event_type=r['event_type'],
                description=r['description'],
                instance_id=r.get('instance_id'),
                user=r.get('user')
            )
            for r in results
        ]
        
        return activities
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/datapacks", response_model=List[DatapackInfo])
async def get_datapacks(instance_id: Optional[int] = None):
    """
    Get discovered datapacks
    
    **Semantic**: `DatapackService.getDatapacks(instanceId?)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if instance_id is not None:
            query = """
                SELECT 
                    d.id,
                    d.instance_id,
                    i.name as instance_name,
                    d.world_path,
                    d.datapack_name,
                    d.version,
                    d.file_hash,
                    d.discovered_at
                FROM instance_datapacks d
                JOIN instances i ON d.instance_id = i.id
                WHERE d.instance_id = %s
                ORDER BY d.datapack_name, d.world_path
            """
            cursor.execute(query, (instance_id,))
        else:
            query = """
                SELECT 
                    d.id,
                    d.instance_id,
                    i.name as instance_name,
                    d.world_path,
                    d.datapack_name,
                    d.version,
                    d.file_hash,
                    d.discovered_at
                FROM instance_datapacks d
                JOIN instances i ON d.instance_id = i.id
                ORDER BY i.name, d.datapack_name
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        return [
            DatapackInfo(
                id=r['id'],
                instance_id=r['instance_id'],
                instance_name=r['instance_name'],
                world_path=r['world_path'],
                datapack_name=r['datapack_name'],
                version=r['version'],
                file_hash=r['file_hash'],
                discovered_at=r['discovered_at']
            )
            for r in results
        ]
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/plugins/outdated", response_model=List[OutdatedPlugin])
async def get_outdated_plugins():
    """
    Get plugins with available updates
    
    **Semantic**: `PluginService.getOutdatedPlugins()`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
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
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        return [
            OutdatedPlugin(
                plugin_name=r['plugin_name'],
                current_version=r['current_version'],
                latest_version=r['latest_version'],
                instances=r['instances'].split(', ') if r['instances'] else [],
                last_checked=r['last_checked']
            )
            for r in results
        ]
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/cicd/endpoints", response_model=List[CICDEndpoint])
async def get_cicd_endpoints():
    """
    Get CI/CD webhook endpoints (placeholder for future implementation)
    
    **Semantic**: `CICDService.getEndpoints()`
    """
    # Return empty list for now - this would query a cicd_endpoints table when implemented
    return []
