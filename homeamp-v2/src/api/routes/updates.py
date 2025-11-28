"""HomeAMP V2.0 - Updates API routes."""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from homeamp_v2.api.dependencies import get_update_service
from homeamp_v2.data.models.plugin import PluginUpdate
from homeamp_v2.domain.services.update_service import UpdateService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/updates", tags=["updates"])


class UpdateCheckRequest(BaseModel):
    """Request to check for updates."""

    plugin_id: int


class UpdateApprovalRequest(BaseModel):
    """Request to approve an update."""

    update_id: int
    approved_by: str
    notes: str | None = None


@router.get("/available")
async def get_available_updates(
    service: UpdateService = Depends(get_update_service),
) -> List[Dict]:
    """Get all available plugin updates.

    Returns:
        List of available updates with plugin details
    """
    updates = service.get_all_available_updates()

    return [
        {
            "id": update.id,
            "plugin_id": update.plugin_id,
            "plugin_name": update.plugin.name if update.plugin else None,
            "current_version": update.current_version,
            "latest_version": update.latest_version,
            "update_url": update.update_url,
            "release_notes": update.release_notes,
            "severity": update.severity,
            "discovered_at": update.discovered_at.isoformat(),
        }
        for update in updates
    ]


@router.post("/check", response_model=Dict)
async def check_for_updates(
    request: UpdateCheckRequest,
    service: UpdateService = Depends(get_update_service),
) -> Dict:
    """Check for updates for a specific plugin.

    Args:
        request: Update check request with plugin ID

    Returns:
        Update information if available

    Raises:
        HTTPException: If plugin not found
    """
    try:
        update = service.check_plugin_update(request.plugin_id)

        if not update:
            return {"status": "up_to_date", "plugin_id": request.plugin_id}

        return {
            "status": "update_available",
            "plugin_id": request.plugin_id,
            "current_version": update.current_version,
            "latest_version": update.latest_version,
            "update_url": update.update_url,
            "release_notes": update.release_notes,
            "severity": update.severity,
        }

    except Exception as e:
        logger.error(f"Error checking updates for plugin {request.plugin_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking updates: {str(e)}",
        )


@router.post("/approve", status_code=status.HTTP_200_OK)
async def approve_update(
    request: UpdateApprovalRequest,
    service: UpdateService = Depends(get_update_service),
) -> Dict:
    """Approve a plugin update.

    Args:
        request: Update approval request

    Returns:
        Approval confirmation

    Raises:
        HTTPException: If update not found
    """
    try:
        service.approve_update(
            update_id=request.update_id,
            approved_by=request.approved_by,
            notes=request.notes,
        )

        return {
            "status": "approved",
            "update_id": request.update_id,
            "approved_by": request.approved_by,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error approving update {request.update_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error approving update: {str(e)}",
        )


@router.post("/reject", status_code=status.HTTP_200_OK)
async def reject_update(
    request: UpdateApprovalRequest,
    service: UpdateService = Depends(get_update_service),
) -> Dict:
    """Reject a plugin update.

    Args:
        request: Update rejection request (uses approval request model)

    Returns:
        Rejection confirmation

    Raises:
        HTTPException: If update not found
    """
    try:
        service.reject_update(
            update_id=request.update_id,
            rejected_by=request.approved_by,  # Reuse field
            reason=request.notes,
        )

        return {
            "status": "rejected",
            "update_id": request.update_id,
            "rejected_by": request.approved_by,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error rejecting update {request.update_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rejecting update: {str(e)}",
        )


@router.get("/{plugin_id}/status", response_model=Dict)
async def get_plugin_update_status(
    plugin_id: int,
    service: UpdateService = Depends(get_update_service),
) -> Dict:
    """Get update status for a specific plugin.

    Args:
        plugin_id: Plugin ID

    Returns:
        Update status information
    """
    updates = service.get_plugin_updates(plugin_id)

    if not updates:
        return {
            "plugin_id": plugin_id,
            "status": "up_to_date",
            "pending_updates": 0,
        }

    pending = [u for u in updates if u.status == "pending"]
    approved = [u for u in updates if u.status == "approved"]

    return {
        "plugin_id": plugin_id,
        "status": "updates_available",
        "pending_updates": len(pending),
        "approved_updates": len(approved),
        "latest_update": {
            "id": updates[0].id,
            "current_version": updates[0].current_version,
            "latest_version": updates[0].latest_version,
            "severity": updates[0].severity,
            "status": updates[0].status,
        }
        if updates
        else None,
    }
