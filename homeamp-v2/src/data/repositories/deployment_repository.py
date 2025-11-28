"""HomeAMP V2.0 - Deployment repository."""

from typing import List, Optional

from sqlalchemy import and_, select

from homeamp_v2.data.models.deployment import (
    ApprovalRequest,
    DeploymentHistory,
    DeploymentQueue,
)
from homeamp_v2.data.repositories.base_repository import BaseRepository


class DeploymentRepository(BaseRepository[DeploymentQueue]):
    """Deployment repository with specialized queries."""

    def __init__(self, session):
        """Initialize repository."""
        super().__init__(DeploymentQueue, session)

    def get_pending(self, instance_id: Optional[int] = None) -> List[DeploymentQueue]:
        """Get pending deployments."""
        stmt = select(DeploymentQueue).where(DeploymentQueue.status == "pending")

        if instance_id:
            stmt = stmt.where(DeploymentQueue.instance_id == instance_id)

        stmt = stmt.order_by(DeploymentQueue.priority.desc(), DeploymentQueue.created_at.asc())

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_deployment_history(
        self, instance_id: Optional[int] = None, limit: int = 100
    ) -> List[DeploymentHistory]:
        """Get deployment history."""
        stmt = select(DeploymentHistory)

        if instance_id:
            stmt = stmt.where(DeploymentHistory.instance_id == instance_id)

        stmt = stmt.order_by(DeploymentHistory.executed_at.desc()).limit(limit)

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_pending_approvals(self, user: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests."""
        stmt = select(ApprovalRequest).where(ApprovalRequest.status == "pending")

        if user:
            stmt = stmt.where(ApprovalRequest.approvers.contains(user))

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_next_deployment(self, instance_id: int) -> Optional[DeploymentQueue]:
        """Get next deployment for an instance."""
        stmt = (
            select(DeploymentQueue)
            .where(and_(DeploymentQueue.instance_id == instance_id, DeploymentQueue.status == "pending"))
            .order_by(DeploymentQueue.priority.desc(), DeploymentQueue.created_at.asc())
            .limit(1)
        )
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
