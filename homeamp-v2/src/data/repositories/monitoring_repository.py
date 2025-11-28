"""HomeAMP V2.0 - Monitoring repository."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select

from homeamp_v2.data.models.monitoring import (
    AgentHeartbeat,
    AuditLog,
    DiscoveryRun,
    SystemMetric,
)
from homeamp_v2.data.repositories.base_repository import BaseRepository


class MonitoringRepository(BaseRepository[DiscoveryRun]):
    """Monitoring repository with specialized queries."""

    def __init__(self, session):
        """Initialize repository."""
        super().__init__(DiscoveryRun, session)

    def get_recent_discovery_runs(self, limit: int = 10) -> List[DiscoveryRun]:
        """Get recent discovery runs."""
        stmt = select(DiscoveryRun).order_by(DiscoveryRun.started_at.desc()).limit(limit)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_agent_heartbeats(self, minutes: int = 5) -> List[AgentHeartbeat]:
        """Get recent agent heartbeats."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        stmt = select(AgentHeartbeat).where(AgentHeartbeat.last_heartbeat >= cutoff)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_audit_log(
        self,
        entity_type: Optional[str] = None,
        user: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit log entries."""
        stmt = select(AuditLog)

        if entity_type:
            stmt = stmt.where(AuditLog.entity_type == entity_type)

        if user:
            stmt = stmt.where(AuditLog.user == user)

        stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_system_metrics(
        self,
        instance_id: int,
        metric_type: Optional[str] = None,
        hours: int = 24,
    ) -> List[SystemMetric]:
        """Get system metrics."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        stmt = select(SystemMetric).where(
            SystemMetric.instance_id == instance_id, SystemMetric.recorded_at >= cutoff
        )

        if metric_type:
            stmt = stmt.where(SystemMetric.metric_type == metric_type)

        stmt = stmt.order_by(SystemMetric.recorded_at.asc())

        result = self.session.execute(stmt)
        return list(result.scalars().all())
