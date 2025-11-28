"""HomeAMP V2.0 - Audit log API routes."""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from homeamp_v2.api.dependencies import get_audit_service
from homeamp_v2.domain.services.audit_service import AuditService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogEntry(BaseModel):
    """Audit log entry response model."""

    id: int
    action: str
    entity_type: str
    entity_id: int
    user: str
    description: str | None
    timestamp: datetime
    metadata: dict


@router.get("/events", response_model=List[AuditLogEntry])
async def get_audit_events(
    entity_type: str | None = None,
    entity_id: int | None = None,
    user: str | None = None,
    action: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    service: AuditService = Depends(get_audit_service),
) -> List[AuditLogEntry]:
    """Get audit log events with filters.

    Args:
        entity_type: Filter by entity type
        entity_id: Filter by entity ID
        user: Filter by user
        action: Filter by action
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum results (max 1000)
        offset: Result offset
        service: Audit service

    Returns:
        List of audit log entries
    """
    logs = service.get_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        user=user,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    return [
        AuditLogEntry(
            id=log.id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            user=log.user,
            description=log.description,
            timestamp=log.timestamp,
            metadata=log.metadata or {},
        )
        for log in logs
    ]


@router.get("/recent", response_model=List[AuditLogEntry])
async def get_recent_events(
    limit: int = Query(50, le=100),
    service: AuditService = Depends(get_audit_service),
) -> List[AuditLogEntry]:
    """Get recent audit events.

    Args:
        limit: Maximum results (max 100)
        service: Audit service

    Returns:
        List of recent audit log entries
    """
    logs = service.get_logs(limit=limit)

    return [
        AuditLogEntry(
            id=log.id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            user=log.user,
            description=log.description,
            timestamp=log.timestamp,
            metadata=log.metadata or {},
        )
        for log in logs
    ]


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogEntry])
async def get_entity_history(
    entity_type: str,
    entity_id: int,
    limit: int = Query(50, le=200),
    service: AuditService = Depends(get_audit_service),
) -> List[AuditLogEntry]:
    """Get audit history for specific entity.

    Args:
        entity_type: Entity type
        entity_id: Entity ID
        limit: Maximum results (max 200)
        service: Audit service

    Returns:
        List of audit log entries for entity
    """
    logs = service.get_entity_history(
        entity_type=entity_type, entity_id=entity_id, limit=limit
    )

    return [
        AuditLogEntry(
            id=log.id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            user=log.user,
            description=log.description,
            timestamp=log.timestamp,
            metadata=log.metadata or {},
        )
        for log in logs
    ]


@router.get("/user/{username}", response_model=List[AuditLogEntry])
async def get_user_activity(
    username: str,
    limit: int = Query(100, le=500),
    service: AuditService = Depends(get_audit_service),
) -> List[AuditLogEntry]:
    """Get activity for specific user.

    Args:
        username: Username
        limit: Maximum results (max 500)
        service: Audit service

    Returns:
        List of audit log entries for user
    """
    logs = service.get_user_activity(user=username, limit=limit)

    return [
        AuditLogEntry(
            id=log.id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            user=log.user,
            description=log.description,
            timestamp=log.timestamp,
            metadata=log.metadata or {},
        )
        for log in logs
    ]
