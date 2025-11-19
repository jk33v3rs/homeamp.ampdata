"""
Deployment API Endpoints
Handles config deployment requests from GUI to agent
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
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

from ..agent.config_deployer import ConfigDeployer

router = APIRouter(prefix="/api/deployment", tags=["deployment"])

# ====================
# Pydantic Models
# ====================

class AgentDeploymentRequest(BaseModel):
    """Request to deploy config via agent"""
    plugin_name: str
    config_yaml: str
    instance_ids: List[int]
    resolve_placeholders: bool = True

class DeploymentStatus(BaseModel):
    """Deployment status for single instance"""
    instance_id: int
    instance_name: Optional[str]
    status: str
    message: Optional[str]

class AgentDeploymentResponse(BaseModel):
    """Response from deployment request"""
    deployment_id: int
    queued_instances: List[int]
    status: str
    message: str

class DeploymentQueueItem(BaseModel):
    """Deployment queue entry"""
    id: int
    deployment_id: int
    plugin_name: str
    instance_count: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

class DeploymentLogEntry(BaseModel):
    """Deployment log entry"""
    id: int
    deployment_id: int
    instance_id: int
    instance_name: Optional[str]
    status: str
    message: str
    timestamp: datetime

# ====================
# Database Helper
# ====================

def get_db_connection():
    """Get MySQL database connection"""
    return get_db()

# ====================
# Endpoints
# ====================

@router.post("/deploy-config", response_model=AgentDeploymentResponse)
async def deploy_config_to_agent(deployment: AgentDeploymentRequest):
    """
    Queue config deployment to agent
    Creates deployment_queue entry and triggers agent processing
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Create deployment_queue entry
        cursor.execute("""
            INSERT INTO deployment_queue
            (plugin_name, instance_ids, config_content, status, created_at)
            VALUES (%s, %s, %s, 'pending', NOW())
        """, (
            deployment.plugin_name,
            str(deployment.instance_ids),  # Store as JSON string
            deployment.config_yaml
        ))

        deployment_id = cursor.lastrowid
        conn.commit()

        # Trigger deployment via ConfigDeployer
        deployer = ConfigDeployer()
        results = deployer.receive_deployment(
            deployment_id=deployment_id,
            plugin_name=deployment.plugin_name,
            config_yaml=deployment.config_yaml,
            instance_ids=deployment.instance_ids,
            resolve_placeholders=deployment.resolve_placeholders
        )

        return AgentDeploymentResponse(
            deployment_id=deployment_id,
            queued_instances=deployment.instance_ids,
            status='processing',
            message=f"Deployment queued for {len(deployment.instance_ids)} instances"
        )

    finally:
        cursor.close()
        conn.close()


@router.get("/queue", response_model=List[DeploymentQueueItem])
async def get_deployment_queue(
    status: Optional[str] = None,
    limit: int = 50
):
    """
    Get deployment queue entries
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
            SELECT 
                id,
                id as deployment_id,
                plugin_name,
                JSON_LENGTH(instance_ids) as instance_count,
                status,
                created_at,
                updated_at
            FROM deployment_queue
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()

        return [DeploymentQueueItem(**row) for row in results]

    finally:
        cursor.close()
        conn.close()


@router.get("/logs/{deployment_id}", response_model=List[DeploymentLogEntry])
async def get_deployment_logs(deployment_id: int):
    """
    Get deployment logs for specific deployment
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                dl.id,
                dl.deployment_id,
                dl.instance_id,
                i.instance_name,
                dl.status,
                dl.message,
                dl.timestamp
            FROM deployment_logs dl
            LEFT JOIN instances i ON dl.instance_id = i.instance_id
            WHERE dl.deployment_id = %s
            ORDER BY dl.timestamp ASC
        """, (deployment_id,))

        results = cursor.fetchall()
        return [DeploymentLogEntry(**row) for row in results]

    finally:
        cursor.close()
        conn.close()


@router.get("/status/{deployment_id}")
async def get_deployment_status(deployment_id: int):
    """
    Get overall deployment status
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get queue entry
        cursor.execute("""
            SELECT id, plugin_name, status, created_at, updated_at
            FROM deployment_queue
            WHERE id = %s
        """, (deployment_id,))

        queue_entry = cursor.fetchone()
        if not queue_entry:
            raise HTTPException(status_code=404, detail="Deployment not found")

        # Get log statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM deployment_logs
            WHERE deployment_id = %s
        """, (deployment_id,))

        stats = cursor.fetchone()

        return {
            'deployment_id': deployment_id,
            'plugin_name': queue_entry['plugin_name'],
            'status': queue_entry['status'],
            'created_at': queue_entry['created_at'],
            'updated_at': queue_entry['updated_at'],
            'total_instances': stats['total'],
            'completed': stats['completed'],
            'failed': stats['failed'],
            'progress': (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        }

    finally:
        cursor.close()
        conn.close()
