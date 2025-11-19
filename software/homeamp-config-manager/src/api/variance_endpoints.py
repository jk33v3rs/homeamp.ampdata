"""
Variance API Endpoints
Handles configuration variance reporting and management
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime
import mysql.connector

from ..core.settings import get_settings

router = APIRouter(prefix="/api/variances", tags=["variances"])

# ====================
# Pydantic Models
# ====================

class ConfigVariance(BaseModel):
    """Configuration variance model"""
    id: Optional[int] = None
    variance_id: Optional[int] = None
    plugin_name: str
    instance_id: int
    instance_name: Optional[str]
    server_name: Optional[str]
    config_key: str
    baseline_value: Any
    actual_value: Any
    is_intentional: bool = False
    detected_at: Optional[datetime]

# ====================
# Database Helper
# ====================

def get_db_connection():
    """Get MySQL database connection"""
    settings = get_settings()
    return mysql.connector.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name
    )

# ====================
# Endpoints
# ====================

@router.get("/all", response_model=List[ConfigVariance])
async def get_all_variances():
    """
    Get all configuration variances across all plugins and instances
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT 
                cv.id as variance_id,
                cv.plugin_name,
                cv.instance_id,
                i.instance_name,
                i.server_name,
                cv.config_key,
                cv.baseline_value,
                cv.actual_value,
                cv.is_intentional,
                cv.detected_at
            FROM config_variances cv
            LEFT JOIN instances i ON cv.instance_id = i.instance_id
            ORDER BY cv.plugin_name ASC, i.instance_name ASC, cv.config_key ASC
        """)

        results = cursor.fetchall()
        
        variances = []
        for row in results:
            variances.append(ConfigVariance(
                id=row['variance_id'],
                variance_id=row['variance_id'],
                plugin_name=row['plugin_name'],
                instance_id=row['instance_id'],
                instance_name=row['instance_name'],
                server_name=row['server_name'],
                config_key=row['config_key'],
                baseline_value=row['baseline_value'],
                actual_value=row['actual_value'],
                is_intentional=bool(row['is_intentional']),
                detected_at=row['detected_at']
            ))
        
        return variances

    finally:
        cursor.close()
        conn.close()


@router.delete("/{plugin_name}/{instance_id}")
async def remove_variance(plugin_name: str, instance_id: int, config_key: str):
    """
    Remove variance by applying default value
    This deletes the variance record and optionally deploys the baseline value
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete the variance record
        cursor.execute("""
            DELETE FROM config_variances
            WHERE plugin_name = %s 
            AND instance_id = %s 
            AND config_key = %s
        """, (plugin_name, instance_id, config_key))

        deleted_count = cursor.rowcount
        conn.commit()

        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Variance not found")

        return {
            'deleted': True,
            'applied_default': True,
            'message': f'Variance removed for {config_key}'
        }

    finally:
        cursor.close()
        conn.close()
