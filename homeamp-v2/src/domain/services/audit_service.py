"""HomeAMP V2.0 - Audit log service."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from homeamp_v2.data.models.monitoring import AuditLog
from homeamp_v2.data.unit_of_work import UnitOfWork
from sqlalchemy import select

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging."""

    def __init__(self, uow: UnitOfWork):
        """Initialize audit service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def log_event(
        self,
        action: str,
        entity_type: str,
        entity_id: int,
        user: str,
        description: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> AuditLog:
        """Log an audit event.

        Args:
            action: Action performed (create, update, delete, etc.)
            entity_type: Type of entity
            entity_id: Entity ID
            user: User performing action
            description: Optional description
            metadata: Additional metadata

        Returns:
            Created audit log entry
        """
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user=user,
            description=description,
            metadata=metadata or {},
        )

        self.uow.session.add(log)
        self.uow.session.flush()

        logger.debug(
            f"Audit log: {action} {entity_type} {entity_id} by {user}"
        )

        return log

    def get_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """Get audit logs with filters.

        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            user: Filter by user
            action: Filter by action
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results
            offset: Result offset

        Returns:
            List of audit log entries
        """
        stmt = select(AuditLog)

        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)

        if entity_id is not None:
            stmt = stmt.where(AuditLog.entity_id == entity_id)

        if user:
            stmt = stmt.where(AuditLog.user == user)

        if action:
            stmt = stmt.where(AuditLog.action == action)

        if start_date:
            stmt = stmt.where(AuditLog.timestamp >= start_date)

        if end_date:
            stmt = stmt.where(AuditLog.timestamp <= end_date)

        stmt = stmt.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)

        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())

    def get_entity_history(
        self, entity_type: str, entity_id: int, limit: int = 50
    ) -> List[AuditLog]:
        """Get history for specific entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID
            limit: Maximum results

        Returns:
            List of audit log entries
        """
        return self.get_logs(
            entity_type=entity_type, entity_id=entity_id, limit=limit
        )

    def get_user_activity(self, user: str, limit: int = 100) -> List[AuditLog]:
        """Get activity for specific user.

        Args:
            user: Username
            limit: Maximum results

        Returns:
            List of audit log entries
        """
        return self.get_logs(user=user, limit=limit)
