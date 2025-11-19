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
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "asmp_admin"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "asmp_config"),
        port=int(os.getenv("DB_PORT", "3306"))
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
                pv.id,
                'plugin_update' as type,
                p.name as plugin_name,
                pv.current_version,
                pv.latest_version as new_version,
                GROUP_CONCAT(DISTINCT i.name) as instances,
                pv.checked_at as timestamp
            FROM plugin_versions pv
            JOIN plugins p ON pv.plugin_id = p.id
            JOIN plugin_instances pi ON p.id = pi.plugin_id
            JOIN instances i ON pi.instance_id = i.id
            WHERE pv.update_available = TRUE
            GROUP BY pv.id, p.name, pv.current_version, pv.latest_version, pv.checked_at
        """
        cursor.execute(update_query)
        plugin_updates = cursor.fetchall()
        
        # Get pending deployments
        deployment_query = """
            SELECT 
                id,
                'config_change' as type,
                plugin_name,
                NULL as current_version,
                NULL as new_version,
                instance_ids as instances,
                created_at as timestamp
            FROM deployment_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """
        cursor.execute(deployment_query)
        deployments = cursor.fetchall()
        
        # Combine and process
        items = []
        
        for update in plugin_updates:
            instances_str = update.get('instances', '')
            items.append(ApprovalItem(
                id=update['id'],
                type=update['type'],
                plugin_name=update['plugin_name'],
                current_version=update['current_version'],
                new_version=update['new_version'],
                instances=instances_str.split(',') if instances_str else [],
                timestamp=update['timestamp']
            ))
        
        for deploy in deployments:
            import json
            instance_ids = json.loads(deploy['instances']) if isinstance(deploy['instances'], str) else deploy['instances']
            items.append(ApprovalItem(
                id=deploy['id'],
                type=deploy['type'],
                plugin_name=deploy['plugin_name'],
                instances=instance_ids,
                timestamp=deploy['timestamp']
            ))
        
        # Sort by timestamp descending
        items.sort(key=lambda x: x.timestamp, reverse=True)
        
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
        
        # Get overall stats
        stats_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN online_status = TRUE THEN 1 ELSE 0 END) as online,
                SUM(CASE WHEN online_status = FALSE THEN 1 ELSE 0 END) as offline
            FROM instances
        """
        cursor.execute(stats_query)
        overall = cursor.fetchone()
        
        # Get per-server stats
        server_query = """
            SELECT 
                server_name,
                COUNT(*) as total,
                SUM(CASE WHEN online_status = TRUE THEN 1 ELSE 0 END) as online,
                SUM(CASE WHEN online_status = FALSE THEN 1 ELSE 0 END) as offline
            FROM instances
            GROUP BY server_name
        """
        cursor.execute(server_query)
        servers = cursor.fetchall()
        
        # Get variance count
        variance_query = "SELECT COUNT(*) as count FROM config_variances WHERE is_intentional = FALSE"
        cursor.execute(variance_query)
        variance_result = cursor.fetchone()
        
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
            variance_count=int(variance_result['count'] or 0)
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
                COUNT(DISTINCT p.id) as total_plugins,
                SUM(CASE WHEN pv.update_available = TRUE THEN 1 ELSE 0 END) as needs_update,
                SUM(CASE WHEN pv.update_available = FALSE OR pv.id IS NULL THEN 1 ELSE 0 END) as up_to_date
            FROM plugins p
            LEFT JOIN plugin_versions pv ON p.id = pv.plugin_id
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
        
        query = """
            SELECT 
                timestamp,
                action_type as event_type,
                CONCAT(action_type, ' - ', resource_type, ' ID:', resource_id) as description,
                resource_id as instance_id,
                user_id as user
            FROM audit_log
            ORDER BY timestamp DESC
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
