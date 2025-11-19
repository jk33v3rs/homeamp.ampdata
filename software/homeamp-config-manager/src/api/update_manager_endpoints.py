"""
Update Manager API Endpoints
Handles plugin update checking, approval, and deployment
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

router = APIRouter(prefix="/api/updates", tags=["updates"])

# ====================
# Pydantic Models
# ====================

class PluginUpdate(BaseModel):
    """Plugin update information"""
    plugin_id: int
    plugin_name: str
    current_version: str
    latest_version: str
    source: str
    release_date: Optional[datetime]
    affected_instances: List[str]
    changelog_url: Optional[str]

class UpdateApprovalRequest(BaseModel):
    """Request to approve plugin updates"""
    plugin_ids: List[int]
    deployment_scope: str  # 'all', 'server', 'tag', 'individual'
    target_instances: Optional[List[str]] = None
    target_server: Optional[str] = None
    target_tag: Optional[int] = None

class UpdateRejectionRequest(BaseModel):
    """Request to reject plugin updates"""
    plugin_ids: List[int]
    skip_version: bool = False  # Skip this version in future checks

class UpdateStatusSchema(BaseModel):
    """Update status for a plugin"""
    plugin_name: str
    status: str  # 'pending', 'downloading', 'deploying', 'completed', 'failed'
    progress: int  # 0-100
    instances_completed: int
    instances_total: int
    message: Optional[str]

class UpdateCheckResult(BaseModel):
    """Result of update check"""
    checked: int
    updates_found: int
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

@router.get("/available", response_model=List[PluginUpdate])
async def get_available_updates():
    """
    Get all available plugin updates
    Returns plugins where latest_version != current_version
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                p.plugin_id,
                p.name as plugin_name,
                pv.current_version,
                pv.latest_version,
                p.source,
                pv.latest_release_date as release_date,
                pv.changelog_url,
                GROUP_CONCAT(DISTINCT i.instance_name) as affected_instances
            FROM plugins p
            INNER JOIN plugin_versions pv ON p.plugin_id = pv.plugin_id
            INNER JOIN plugin_instances pi ON p.plugin_id = pi.plugin_id
            INNER JOIN instances i ON pi.instance_id = i.instance_id
            WHERE pv.update_available = TRUE
            GROUP BY p.plugin_id, p.name, pv.current_version, pv.latest_version, 
                     p.source, pv.latest_release_date, pv.changelog_url
            ORDER BY p.name ASC
        """)

        results = cursor.fetchall()
        
        updates = []
        for row in results:
            updates.append(PluginUpdate(
                plugin_id=row['plugin_id'],
                plugin_name=row['plugin_name'],
                current_version=row['current_version'] or 'Unknown',
                latest_version=row['latest_version'] or 'Unknown',
                source=row['source'] or 'Unknown',
                release_date=row['release_date'],
                affected_instances=row['affected_instances'].split(',') if row['affected_instances'] else [],
                changelog_url=row.get('changelog_url')
            ))
        
        return updates

    finally:
        cursor.close()
        conn.close()


@router.post("/check", response_model=UpdateCheckResult)
async def trigger_update_check():
    """
    Trigger manual update check
    This would normally be handled by the update_checker agent
    For now, just return current state
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Count total plugins
        cursor.execute("SELECT COUNT(*) as total FROM plugins")
        total = cursor.fetchone()['total']

        # Count plugins with updates available
        cursor.execute("""
            SELECT COUNT(*) as updates 
            FROM plugin_versions 
            WHERE update_available = TRUE
        """)
        updates = cursor.fetchone()['updates']

        return UpdateCheckResult(
            checked=total,
            updates_found=updates,
            timestamp=datetime.now()
        )

    finally:
        cursor.close()
        conn.close()


@router.post("/approve", response_model=dict)
async def approve_updates(approval: UpdateApprovalRequest):
    """
    Approve plugin updates for deployment
    Creates deployment queue entries
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        approved_count = 0
        queued_deployments = []

        for plugin_id in approval.plugin_ids:
            # Get plugin details
            cursor.execute("""
                SELECT p.name, pv.latest_version
                FROM plugins p
                INNER JOIN plugin_versions pv ON p.plugin_id = pv.plugin_id
                WHERE p.plugin_id = %s
            """, (plugin_id,))
            
            plugin = cursor.fetchone()
            if not plugin:
                continue

            plugin_name, latest_version = plugin

            # Determine target instances based on scope
            target_instances = []
            
            if approval.deployment_scope == 'all':
                cursor.execute("""
                    SELECT instance_id 
                    FROM plugin_instances 
                    WHERE plugin_id = %s
                """, (plugin_id,))
                target_instances = [row[0] for row in cursor.fetchall()]
            
            elif approval.deployment_scope == 'server' and approval.target_server:
                cursor.execute("""
                    SELECT pi.instance_id
                    FROM plugin_instances pi
                    INNER JOIN instances i ON pi.instance_id = i.instance_id
                    WHERE pi.plugin_id = %s AND i.server_name = %s
                """, (plugin_id, approval.target_server))
                target_instances = [row[0] for row in cursor.fetchall()]
            
            elif approval.deployment_scope == 'tag' and approval.target_tag:
                cursor.execute("""
                    SELECT pi.instance_id
                    FROM plugin_instances pi
                    INNER JOIN tag_instances ti ON pi.instance_id = ti.instance_id
                    WHERE pi.plugin_id = %s AND ti.tag_id = %s
                """, (plugin_id, approval.target_tag))
                target_instances = [row[0] for row in cursor.fetchall()]
            
            elif approval.deployment_scope == 'individual' and approval.target_instances:
                target_instances = approval.target_instances

            if not target_instances:
                continue

            # Create deployment queue entry
            cursor.execute("""
                INSERT INTO deployment_queue
                (plugin_name, instance_ids, config_content, status, created_at)
                VALUES (%s, %s, %s, 'pending', NOW())
            """, (
                plugin_name,
                str(target_instances),  # Store as JSON string
                f"Update to version {latest_version}"  # Placeholder for update info
            ))

            queued_deployments.append(cursor.lastrowid)
            approved_count += 1

        conn.commit()

        return {
            'approved': approved_count,
            'queued_for_deployment': queued_deployments
        }

    finally:
        cursor.close()
        conn.close()


@router.post("/reject", response_model=dict)
async def reject_updates(rejection: UpdateRejectionRequest):
    """
    Reject plugin updates
    Optionally skip this version in future checks
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        for plugin_id in rejection.plugin_ids:
            if rejection.skip_version:
                # Mark this version as skipped
                cursor.execute("""
                    UPDATE plugin_versions
                    SET update_available = FALSE
                    WHERE plugin_id = %s
                """, (plugin_id,))
            else:
                # Just dismiss without marking
                pass

        conn.commit()

        return {
            'rejected': len(rejection.plugin_ids)
        }

    finally:
        cursor.close()
        conn.close()


@router.get("/status/{plugin_name}", response_model=UpdateStatusSchema)
async def get_update_status(plugin_name: str):
    """
    Get update status for a specific plugin
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get latest deployment for this plugin
        cursor.execute("""
            SELECT 
                dq.plugin_name,
                dq.status,
                dq.created_at,
                dq.updated_at
            FROM deployment_queue dq
            WHERE dq.plugin_name = %s
            ORDER BY dq.created_at DESC
            LIMIT 1
        """, (plugin_name,))

        deployment = cursor.fetchone()
        
        if not deployment:
            raise HTTPException(status_code=404, detail="No deployment found for plugin")

        # Count deployment progress
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM deployment_logs
            WHERE deployment_id = (
                SELECT id FROM deployment_queue 
                WHERE plugin_name = %s 
                ORDER BY created_at DESC 
                LIMIT 1
            )
        """, (plugin_name,))

        stats = cursor.fetchone()
        total = stats['total'] or 0
        completed = stats['completed'] or 0

        return UpdateStatusSchema(
            plugin_name=plugin_name,
            status=deployment['status'],
            progress=int((completed / total * 100) if total > 0 else 0),
            instances_completed=completed,
            instances_total=total,
            message=None
        )

    finally:
        cursor.close()
        conn.close()
