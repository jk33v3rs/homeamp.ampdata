"""
Audit Log API Endpoints
Provides access to system audit events and activity history
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import mysql.connector
import csv
import io
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

router = APIRouter(prefix="/api/audit-log", tags=["audit-log"])

# ====================
# Models
# ====================

class AuditEvent(BaseModel):
    event_id: int
    event_type: str
    instance_id: Optional[int]
    instance_name: Optional[str]
    user: Optional[str]
    description: str
    details: Optional[Dict[str, Any]]
    timestamp: datetime

class AuditEventsResponse(BaseModel):
    events: List[AuditEvent]
    total: int
    page: int
    page_size: int
    total_pages: int

# ====================
# Endpoints
# ====================

@router.get("/events", response_model=AuditEventsResponse)
async def get_audit_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    event_type: Optional[str] = None,
    instance_id: Optional[int] = None,
    user: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Get paginated audit events with optional filtering
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if event_type:
            where_conditions.append("al.event_type = %s")
            params.append(event_type)
        
        if instance_id:
            where_conditions.append("al.instance_id = %s")
            params.append(instance_id)
        
        if user:
            where_conditions.append("al.user = %s")
            params.append(user)
        
        if start_date:
            where_conditions.append("al.timestamp >= %s")
            params.append(start_date)
        
        if end_date:
            # Include the entire end date
            where_conditions.append("al.timestamp < DATE_ADD(%s, INTERVAL 1 DAY)")
            params.append(end_date)
        
        where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"""
            SELECT COUNT(*) as total
            FROM audit_log al
            WHERE 1=1{where_clause}
        """
        
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Calculate pagination
        offset = (page - 1) * page_size
        total_pages = (total + page_size - 1) // page_size
        
        # Get events with instance info
        query = f"""
            SELECT 
                al.event_id,
                al.event_type,
                al.instance_id,
                i.instance_name,
                al.user,
                al.description,
                al.details,
                al.timestamp
            FROM audit_log al
            LEFT JOIN instances i ON al.instance_id = i.instance_id
            WHERE 1=1{where_clause}
            ORDER BY al.timestamp DESC
            LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, params + [page_size, offset])
        events = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return AuditEventsResponse(
            events=events,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching audit events: {str(e)}")


@router.get("/export")
async def export_audit_log(
    event_type: Optional[str] = None,
    instance_id: Optional[int] = None,
    user: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Export audit log to CSV with optional filtering
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if event_type:
            where_conditions.append("al.event_type = %s")
            params.append(event_type)
        
        if instance_id:
            where_conditions.append("al.instance_id = %s")
            params.append(instance_id)
        
        if user:
            where_conditions.append("al.user = %s")
            params.append(user)
        
        if start_date:
            where_conditions.append("al.timestamp >= %s")
            params.append(start_date)
        
        if end_date:
            where_conditions.append("al.timestamp < DATE_ADD(%s, INTERVAL 1 DAY)")
            params.append(end_date)
        
        where_clause = " AND " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get all matching events
        query = f"""
            SELECT 
                al.event_id,
                al.timestamp,
                al.event_type,
                i.instance_name,
                al.user,
                al.description
            FROM audit_log al
            LEFT JOIN instances i ON al.instance_id = i.instance_id
            WHERE 1=1{where_clause}
            ORDER BY al.timestamp DESC
        """
        
        cursor.execute(query, params)
        events = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(['Event ID', 'Timestamp', 'Event Type', 'Instance', 'User', 'Description'])
        
        # Data
        for event in events:
            writer.writerow([
                event['event_id'],
                event['timestamp'],
                event['event_type'],
                event['instance_name'] or 'N/A',
                event['user'] or 'System',
                event['description']
            ])
        
        # Return CSV as download
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_log_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
        
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting audit log: {str(e)}")
