"""HomeAMP V2.0 - Dashboard service for aggregated statistics."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from homeamp_v2.data.models.config import ConfigVariance
from homeamp_v2.data.models.deployment import ApprovalRequest
from homeamp_v2.data.models.instance import Instance
from homeamp_v2.data.models.monitoring import AgentHeartbeat, AuditLog
from homeamp_v2.data.models.plugin import Plugin, PluginUpdateQueue
from homeamp_v2.data.unit_of_work import UnitOfWork
from sqlalchemy import func, select

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for dashboard statistics and summaries."""

    def __init__(self, uow: UnitOfWork):
        """Initialize dashboard service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def get_summary_stats(self) -> Dict:
        """Get summary statistics for dashboard.

        Returns:
            Dictionary of summary statistics
        """
        # Instance stats
        total_instances_stmt = select(func.count()).select_from(Instance)
        total_instances = self.uow.session.execute(total_instances_stmt).scalar()

        active_instances_stmt = (
            select(func.count())
            .select_from(Instance)
            .where(Instance.status == "active")
        )
        active_instances = self.uow.session.execute(active_instances_stmt).scalar()

        # Plugin stats
        total_plugins_stmt = select(func.count()).select_from(Plugin)
        total_plugins = self.uow.session.execute(total_plugins_stmt).scalar()

        # Update queue
        pending_updates_stmt = (
            select(func.count())
            .select_from(PluginUpdateQueue)
            .where(PluginUpdateQueue.status == "pending")
        )
        pending_updates = self.uow.session.execute(pending_updates_stmt).scalar()

        # Variances
        variances_stmt = select(func.count()).select_from(ConfigVariance)
        total_variances = self.uow.session.execute(variances_stmt).scalar()

        # Pending approvals
        approvals_stmt = (
            select(func.count())
            .select_from(ApprovalRequest)
            .where(ApprovalRequest.status == "pending")
        )
        pending_approvals = self.uow.session.execute(approvals_stmt).scalar()

        return {
            "total_instances": total_instances,
            "active_instances": active_instances,
            "total_plugins": total_plugins,
            "pending_updates": pending_updates,
            "total_variances": total_variances,
            "pending_approvals": pending_approvals,
        }

    def get_network_status(self) -> Dict:
        """Get network-wide status overview.

        Returns:
            Network status dictionary
        """
        # Group instances by server
        stmt = (
            select(
                Instance.server_name,
                func.count(Instance.id).label("instance_count"),
                func.sum(func.case((Instance.status == "active", 1), else_=0)).label(
                    "active_count"
                ),
            )
            .group_by(Instance.server_name)
        )

        result = self.uow.session.execute(stmt)
        servers = []

        for row in result:
            servers.append(
                {
                    "server_name": row.server_name,
                    "total_instances": row.instance_count,
                    "active_instances": row.active_count,
                    "status": "healthy"
                    if row.active_count == row.instance_count
                    else "degraded",
                }
            )

        # Get agent heartbeats
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        heartbeat_stmt = select(AgentHeartbeat).where(
            AgentHeartbeat.last_heartbeat >= cutoff
        )
        heartbeats = self.uow.session.execute(heartbeat_stmt).scalars().all()

        return {
            "servers": servers,
            "active_agents": len(heartbeats),
            "last_check": datetime.utcnow().isoformat(),
        }

    def get_plugin_summary(self) -> Dict:
        """Get plugin distribution summary.

        Returns:
            Plugin summary dictionary
        """
        # Plugin version distribution
        stmt = (
            select(
                Plugin.name,
                Plugin.current_version,
                func.count().label("instance_count"),
            )
            .group_by(Plugin.name, Plugin.current_version)
            .order_by(func.count().desc())
            .limit(20)
        )

        result = self.uow.session.execute(stmt)
        popular_plugins = []

        for row in result:
            popular_plugins.append(
                {
                    "name": row.name,
                    "version": row.current_version,
                    "instance_count": row.instance_count,
                }
            )

        # Plugins with updates
        updates_stmt = (
            select(func.count())
            .select_from(PluginUpdateQueue)
            .where(PluginUpdateQueue.status == "pending")
        )
        plugins_with_updates = self.uow.session.execute(updates_stmt).scalar()

        return {
            "total_unique_plugins": len(popular_plugins),
            "plugins_with_updates": plugins_with_updates,
            "popular_plugins": popular_plugins,
        }

    def get_recent_activity(self, limit: int = 50) -> List[Dict]:
        """Get recent activity from audit log.

        Args:
            limit: Maximum number of entries

        Returns:
            List of recent activity entries
        """
        stmt = (
            select(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )

        result = self.uow.session.execute(stmt)
        activities = []

        for log in result.scalars():
            activities.append(
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "user": log.user,
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "description": log.description,
                }
            )

        return activities

    def get_approval_queue(self) -> Dict:
        """Get pending approval queue.

        Returns:
            Approval queue summary
        """
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.status == "pending")
            .order_by(ApprovalRequest.created_at.desc())
        )

        result = self.uow.session.execute(stmt)
        pending = []

        for request in result.scalars():
            pending.append(
                {
                    "id": request.id,
                    "entity_type": request.entity_type,
                    "entity_id": request.entity_id,
                    "requested_by": request.requested_by,
                    "description": request.description,
                    "created_at": request.created_at.isoformat(),
                    "required_approvals": request.required_approvals,
                }
            )

        return {
            "total_pending": len(pending),
            "requests": pending,
        }

    def get_variance_summary(self) -> Dict:
        """Get configuration variance summary.

        Returns:
            Variance summary dictionary
        """
        # Total variances
        total_stmt = select(func.count()).select_from(ConfigVariance)
        total = self.uow.session.execute(total_stmt).scalar()

        # By severity
        severity_stmt = (
            select(
                ConfigVariance.severity,
                func.count().label("count"),
            )
            .group_by(ConfigVariance.severity)
        )

        result = self.uow.session.execute(severity_stmt)
        by_severity = {row.severity: row.count for row in result}

        # By instance
        instance_stmt = (
            select(
                ConfigVariance.instance_id,
                func.count().label("variance_count"),
            )
            .group_by(ConfigVariance.instance_id)
            .order_by(func.count().desc())
            .limit(10)
        )

        result = self.uow.session.execute(instance_stmt)
        top_instances = [
            {"instance_id": row.instance_id, "variance_count": row.variance_count}
            for row in result
        ]

        return {
            "total_variances": total,
            "by_severity": by_severity,
            "top_instances": top_instances,
        }
