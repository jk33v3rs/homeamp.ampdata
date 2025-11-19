"""
Enhanced API Endpoints for Phase 0 Features

New endpoints for:
- Deployment queue management
- Plugin version tracking
- Tag system
- Config variances
- Server properties management
- Datapack discovery
- Audit logging
- Agent heartbeat monitoring
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import mysql.connector
from mysql.connector import Error

from ..core.settings import get_settings


# Pydantic models for request/response
class DeploymentRequest(BaseModel):
    plugin_name: str
    instance_ids: List[int]
    config_data: Dict[str, Any]
    requested_by: str

class TagCreate(BaseModel):
    name: str
    color: str
    parent_tag_id: Optional[int] = None

class TagAssign(BaseModel):
    tag_id: int
    instance_ids: List[int]

class VarianceUpdate(BaseModel):
    variance_id: int
    is_intentional: bool

class ServerPropertyBaseline(BaseModel):
    property_key: str
    property_value: str
    baseline_type: str = 'global'


# Router setup
router = APIRouter(prefix="/api", tags=["enhanced"])


def get_db_connection():
    """Get database connection"""
    settings = get_settings()
    try:
        conn = mysql.connector.connect(
            host=settings.database.host,
            port=settings.database.port,
            user=settings.database.user,
            password=settings.database.password,
            database=settings.database.database
        )
        return conn
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")


# ============================================
# DEPLOYMENT QUEUE ENDPOINTS
# ============================================

@router.get("/deployment-queue")
async def get_deployment_queue(status: Optional[str] = None, limit: int = 50):
    """
    Get deployment queue entries
    
    **Semantic**: `DeploymentQueueService.getQueue(status?, limit?)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if status:
            query = """
                SELECT * FROM deployment_queue 
                WHERE status = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """
            cursor.execute(query, (status, limit))
        else:
            query = """
                SELECT * FROM deployment_queue 
                ORDER BY created_at DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
        
        results = cursor.fetchall()
        
        # Parse JSON fields
        for row in results:
            if row.get('instance_ids') and isinstance(row['instance_ids'], str):
                import json
                row['instance_ids'] = json.loads(row['instance_ids'])
        
        return {"success": True, "count": len(results), "deployments": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.post("/deployment-queue")
async def create_deployment(deployment: DeploymentRequest):
    """
    Create new deployment request
    
    **Semantic**: `DeploymentQueueService.createDeployment(request)`
    """
    conn = None
    try:
        import json
        import uuid
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        deployment_id = str(uuid.uuid4())
        instance_ids_json = json.dumps(deployment.instance_ids)
        
        query = """
            INSERT INTO deployment_queue 
            (deployment_id, plugin_name, instance_ids, status, requested_by, created_at)
            VALUES (%s, %s, %s, 'pending', %s, %s)
        """
        cursor.execute(query, (
            deployment_id,
            deployment.plugin_name,
            instance_ids_json,
            deployment.requested_by,
            datetime.now()
        ))
        conn.commit()
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "message": f"Deployment queued for {len(deployment.instance_ids)} instances"
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================
# PLUGIN VERSIONS ENDPOINTS
# ============================================

@router.get("/plugin-versions")
async def get_plugin_versions(update_available: Optional[bool] = None):
    """
    Get plugin version information
    
    **Semantic**: `PluginVersionService.getVersions(updateAvailable?)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if update_available is not None:
            query = """
                SELECT pv.*, p.name as plugin_name
                FROM plugin_versions pv
                JOIN plugins p ON pv.plugin_id = p.id
                WHERE pv.update_available = %s
                ORDER BY p.name
            """
            cursor.execute(query, (update_available,))
        else:
            query = """
                SELECT pv.*, p.name as plugin_name
                FROM plugin_versions pv
                JOIN plugins p ON pv.plugin_id = p.id
                ORDER BY p.name
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        return {"success": True, "count": len(results), "versions": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================
# TAG SYSTEM ENDPOINTS
# ============================================

@router.get("/tags")
async def get_tags(parent_tag_id: Optional[int] = None):
    """
    Get all tags or child tags of a parent
    
    **Semantic**: `TagService.getTags(parentTagId?)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if parent_tag_id is not None:
            # Get child tags via hierarchy table
            query = """
                SELECT t.* FROM meta_tags t
                JOIN tag_hierarchy th ON t.id = th.child_tag_id
                WHERE th.parent_tag_id = %s
                ORDER BY t.name
            """
            cursor.execute(query, (parent_tag_id,))
        else:
            # Get all tags
            query = "SELECT * FROM meta_tags ORDER BY name"
            cursor.execute(query)
        
        results = cursor.fetchall()
        return {"success": True, "count": len(results), "tags": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.post("/tags")
async def create_tag(tag: TagCreate):
    """
    Create new tag
    
    **Semantic**: `TagService.createTag(tagData)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO meta_tags (name, color, parent_tag_id, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        now = datetime.now()
        cursor.execute(query, (tag.name, tag.color, tag.parent_tag_id, now, now))
        
        tag_id = cursor.lastrowid
        
        # If parent specified, add to hierarchy table
        if tag.parent_tag_id:
            hierarchy_query = """
                INSERT INTO tag_hierarchy (parent_tag_id, child_tag_id)
                VALUES (%s, %s)
            """
            cursor.execute(hierarchy_query, (tag.parent_tag_id, tag_id))
        
        conn.commit()
        
        return {"success": True, "tag_id": tag_id, "message": f"Tag '{tag.name}' created"}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.post("/tags/assign")
async def assign_tags(assignment: TagAssign):
    """
    Assign tag to multiple instances
    
    **Semantic**: `TagService.assignTag(tagId, instanceIds[])`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Batch insert
        query = """
            INSERT IGNORE INTO tag_instances (tag_id, instance_id)
            VALUES (%s, %s)
        """
        values = [(assignment.tag_id, inst_id) for inst_id in assignment.instance_ids]
        cursor.executemany(query, values)
        conn.commit()
        
        assigned_count = cursor.rowcount
        
        return {
            "success": True,
            "assigned_count": assigned_count,
            "message": f"Tag assigned to {assigned_count} instances"
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/instances/{instance_id}/tags")
async def get_instance_tags(instance_id: int):
    """
    Get all tags for an instance
    
    **Semantic**: `TagService.getInstanceTags(instanceId)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT t.* FROM meta_tags t
            JOIN tag_instances ti ON t.id = ti.tag_id
            WHERE ti.instance_id = %s
            ORDER BY t.name
        """
        cursor.execute(query, (instance_id,))
        results = cursor.fetchall()
        
        return {"success": True, "count": len(results), "tags": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================
# CONFIG VARIANCES ENDPOINTS
# ============================================

@router.get("/config-variances")
async def get_config_variances(
    instance_id: Optional[int] = None,
    plugin_name: Optional[str] = None,
    is_intentional: Optional[bool] = None,
    limit: int = 100
):
    """
    Get config variances with optional filters
    
    **Semantic**: `ConfigVarianceService.getVariances(filters)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Build dynamic query
        where_clauses = []
        params = []
        
        if instance_id is not None:
            where_clauses.append("cv.instance_id = %s")
            params.append(instance_id)
        
        if plugin_name:
            where_clauses.append("cv.plugin_name = %s")
            params.append(plugin_name)
        
        if is_intentional is not None:
            where_clauses.append("cv.is_intentional = %s")
            params.append(is_intentional)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT cv.*, i.name as instance_name
            FROM config_variances cv
            JOIN instances i ON cv.instance_id = i.id
            WHERE {where_sql}
            ORDER BY cv.created_at DESC
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        return {"success": True, "count": len(results), "variances": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.patch("/config-variances/{variance_id}")
async def update_variance(variance_id: int, update: VarianceUpdate):
    """
    Mark variance as intentional/unintentional
    
    **Semantic**: `ConfigVarianceService.updateVariance(varianceId, isIntentional)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            UPDATE config_variances 
            SET is_intentional = %s
            WHERE id = %s
        """
        cursor.execute(query, (update.is_intentional, variance_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Variance not found")
        
        return {"success": True, "message": "Variance updated"}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================
# SERVER PROPERTIES ENDPOINTS
# ============================================

@router.get("/server-properties")
async def get_server_properties(instance_id: Optional[int] = None):
    """
    Get server properties variances
    
    **Semantic**: `ServerPropertiesService.getVariances(instanceId?)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if instance_id is not None:
            query = """
                SELECT spv.*, i.name as instance_name, 
                       spb.property_value as baseline_value
                FROM server_properties_variances spv
                JOIN instances i ON spv.instance_id = i.id
                LEFT JOIN server_properties_baselines spb 
                    ON spv.property_key = spb.property_key
                WHERE spv.instance_id = %s
                ORDER BY spv.property_key
            """
            cursor.execute(query, (instance_id,))
        else:
            query = """
                SELECT spv.*, i.name as instance_name,
                       spb.property_value as baseline_value
                FROM server_properties_variances spv
                JOIN instances i ON spv.instance_id = i.id
                LEFT JOIN server_properties_baselines spb 
                    ON spv.property_key = spb.property_key
                ORDER BY i.name, spv.property_key
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        return {"success": True, "count": len(results), "variances": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/server-properties/baselines")
async def get_server_property_baselines():
    """
    Get all server property baselines
    
    **Semantic**: `ServerPropertiesService.getBaselines()`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM server_properties_baselines ORDER BY property_key"
        cursor.execute(query)
        results = cursor.fetchall()
        
        return {"success": True, "count": len(results), "baselines": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


@router.post("/server-properties/baselines")
async def create_baseline(baseline: ServerPropertyBaseline):
    """
    Create or update server property baseline
    
    **Semantic**: `ServerPropertiesService.setBaseline(propertyKey, value)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            INSERT INTO server_properties_baselines 
            (property_key, property_value, baseline_type, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                property_value = VALUES(property_value),
                baseline_type = VALUES(baseline_type),
                updated_at = VALUES(updated_at)
        """
        now = datetime.now()
        cursor.execute(query, (
            baseline.property_key,
            baseline.property_value,
            baseline.baseline_type,
            now, now
        ))
        conn.commit()
        
        return {"success": True, "message": f"Baseline set for {baseline.property_key}"}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================
# DATAPACK ENDPOINTS
# ============================================

@router.get("/datapacks")
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
                SELECT d.*, i.name as instance_name
                FROM datapacks d
                JOIN instances i ON d.instance_id = i.id
                WHERE d.instance_id = %s
                ORDER BY d.name, d.world_path
            """
            cursor.execute(query, (instance_id,))
        else:
            query = """
                SELECT d.*, i.name as instance_name
                FROM datapacks d
                JOIN instances i ON d.instance_id = i.id
                ORDER BY i.name, d.name
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        return {"success": True, "count": len(results), "datapacks": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================
# AUDIT LOG ENDPOINTS
# ============================================

@router.get("/audit-log")
async def get_audit_log(
    user_id: Optional[str] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = 100
):
    """
    Get audit log entries
    
    **Semantic**: `AuditService.getLogs(filters)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        where_clauses = []
        params = []
        
        if user_id:
            where_clauses.append("user_id = %s")
            params.append(user_id)
        
        if action_type:
            where_clauses.append("action_type = %s")
            params.append(action_type)
        
        if resource_type:
            where_clauses.append("resource_type = %s")
            params.append(resource_type)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT * FROM audit_log
            WHERE {where_sql}
            ORDER BY timestamp DESC
            LIMIT %s
        """
        params.append(limit)
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        # Parse JSON details
        for row in results:
            if row.get('details') and isinstance(row['details'], str):
                import json
                row['details'] = json.loads(row['details'])
        
        return {"success": True, "count": len(results), "logs": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()


# ============================================
# AGENT HEARTBEAT ENDPOINTS
# ============================================

@router.get("/agent-heartbeats")
async def get_agent_heartbeats(status: Optional[str] = None):
    """
    Get agent heartbeat status
    
    **Semantic**: `AgentHeartbeatService.getHeartbeats(status?)`
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if status:
            query = """
                SELECT * FROM agent_heartbeats
                WHERE status = %s
                ORDER BY last_heartbeat DESC
            """
            cursor.execute(query, (status,))
        else:
            query = """
                SELECT * FROM agent_heartbeats
                ORDER BY last_heartbeat DESC
            """
            cursor.execute(query)
        
        results = cursor.fetchall()
        
        # Add time since last heartbeat
        now = datetime.now()
        for row in results:
            if row['last_heartbeat']:
                delta = now - row['last_heartbeat']
                row['seconds_since_heartbeat'] = int(delta.total_seconds())
        
        return {"success": True, "count": len(results), "heartbeats": results}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
