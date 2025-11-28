"""HomeAMP V2.0 - Dashboard API routes."""

import logging
from typing import Dict

from fastapi import APIRouter, Depends
from homeamp_v2.api.dependencies import get_dashboard_service
from homeamp_v2.domain.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=Dict)
async def get_summary_stats(
    service: DashboardService = Depends(get_dashboard_service),
) -> Dict:
    """Get summary statistics for dashboard.

    Returns:
        Dictionary containing instance, plugin, update, variance, and approval counts
    """
    return service.get_summary_stats()


@router.get("/network-status", response_model=Dict)
async def get_network_status(
    service: DashboardService = Depends(get_dashboard_service),
) -> Dict:
    """Get network status grouped by server.

    Returns:
        Dictionary with server-grouped instance statuses and agent heartbeats
    """
    return service.get_network_status()


@router.get("/plugin-summary", response_model=Dict)
async def get_plugin_summary(
    service: DashboardService = Depends(get_dashboard_service),
) -> Dict:
    """Get plugin distribution summary.

    Returns:
        Dictionary with plugin counts, popular plugins, and update availability
    """
    return service.get_plugin_summary()


@router.get("/recent-activity", response_model=Dict)
async def get_recent_activity(
    limit: int = 10,
    service: DashboardService = Depends(get_dashboard_service),
) -> Dict:
    """Get recent activity from audit logs.

    Args:
        limit: Maximum number of events to return

    Returns:
        Dictionary with recent activity events
    """
    return service.get_recent_activity(limit=limit)


@router.get("/approval-queue", response_model=Dict)
async def get_approval_queue(
    service: DashboardService = Depends(get_dashboard_service),
) -> Dict:
    """Get pending approval queue summary.

    Returns:
        Dictionary with pending approval counts by entity type
    """
    return service.get_approval_queue()


@router.get("/variance-summary", response_model=Dict)
async def get_variance_summary(
    service: DashboardService = Depends(get_dashboard_service),
) -> Dict:
    """Get configuration variance summary.

    Returns:
        Dictionary with variance counts by severity and instance
    """
    return service.get_variance_summary()
