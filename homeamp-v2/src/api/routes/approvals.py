"""HomeAMP V2.0 - Approval workflow API routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from homeamp_v2.api.dependencies import get_approval_service
from homeamp_v2.core.exceptions import ApprovalError, NotFoundError
from homeamp_v2.data.models.deployment import ApprovalRequest, ApprovalVote
from homeamp_v2.domain.services.approval_service import ApprovalService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])


class CreateApprovalRequest(BaseModel):
    """Request to create approval workflow."""

    entity_type: str
    entity_id: int
    requested_by: str
    description: str
    metadata: dict | None = None
    required_approvals: int = 2


class VoteRequest(BaseModel):
    """Request to vote on approval."""

    voted_by: str
    approved: bool
    comment: str | None = None


class CancelRequest(BaseModel):
    """Request to cancel approval."""

    cancelled_by: str


@router.get("/pending")
async def get_pending_approvals(
    entity_type: str | None = None,
    service: ApprovalService = Depends(get_approval_service),
) -> List[dict]:
    """Get pending approval requests.

    Args:
        entity_type: Optional filter by entity type

    Returns:
        List of pending approval requests
    """
    approvals = service.get_pending_approvals(entity_type=entity_type)

    return [
        {
            "id": approval.id,
            "entity_type": approval.entity_type,
            "entity_id": approval.entity_id,
            "requested_by": approval.requested_by,
            "description": approval.description,
            "status": approval.status,
            "required_approvals": approval.required_approvals,
            "approval_count": approval.approval_count,
            "rejection_count": approval.rejection_count,
            "created_at": approval.created_at.isoformat(),
            "metadata": approval.metadata,
        }
        for approval in approvals
    ]


@router.post("/requests", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_approval_request(
    request: CreateApprovalRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> dict:
    """Create new approval request.

    Args:
        request: Approval request details

    Returns:
        Created approval request
    """
    try:
        approval = service.create_approval_request(
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            requested_by=request.requested_by,
            description=request.description,
            metadata=request.metadata,
            required_approvals=request.required_approvals,
        )

        return {
            "id": approval.id,
            "entity_type": approval.entity_type,
            "entity_id": approval.entity_id,
            "requested_by": approval.requested_by,
            "description": approval.description,
            "status": approval.status,
            "required_approvals": approval.required_approvals,
            "created_at": approval.created_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error creating approval request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating approval: {str(e)}",
        )


@router.get("/{approval_id}", response_model=dict)
async def get_approval_request(
    approval_id: int,
    service: ApprovalService = Depends(get_approval_service),
) -> dict:
    """Get approval request by ID.

    Args:
        approval_id: Approval request ID

    Returns:
        Approval request details

    Raises:
        HTTPException: If not found
    """
    try:
        approval = service.get_approval_request(approval_id)

        return {
            "id": approval.id,
            "entity_type": approval.entity_type,
            "entity_id": approval.entity_id,
            "requested_by": approval.requested_by,
            "description": approval.description,
            "status": approval.status,
            "required_approvals": approval.required_approvals,
            "approval_count": approval.approval_count,
            "rejection_count": approval.rejection_count,
            "created_at": approval.created_at.isoformat(),
            "completed_at": approval.completed_at.isoformat()
            if approval.completed_at
            else None,
            "metadata": approval.metadata,
        }

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{approval_id}/votes")
async def get_approval_votes(
    approval_id: int,
    service: ApprovalService = Depends(get_approval_service),
) -> List[dict]:
    """Get votes for approval request.

    Args:
        approval_id: Approval request ID

    Returns:
        List of votes
    """
    votes = service.get_approval_votes(approval_id)

    return [
        {
            "id": vote.id,
            "voted_by": vote.voted_by,
            "approved": vote.approved,
            "comment": vote.comment,
            "voted_at": vote.voted_at.isoformat(),
        }
        for vote in votes
    ]


@router.post("/{approval_id}/vote", status_code=status.HTTP_201_CREATED)
async def vote_on_approval(
    approval_id: int,
    vote: VoteRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> dict:
    """Add vote to approval request.

    Args:
        approval_id: Approval request ID
        vote: Vote details

    Returns:
        Vote confirmation

    Raises:
        HTTPException: If not found or already voted
    """
    try:
        service.add_approval_vote(
            request_id=approval_id,
            voted_by=vote.voted_by,
            approved=vote.approved,
            comment=vote.comment,
        )

        return {
            "status": "vote_recorded",
            "approval_id": approval_id,
            "voted_by": vote.voted_by,
            "approved": vote.approved,
        }

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ApprovalError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error voting on approval {approval_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording vote: {str(e)}",
        )


@router.post("/{approval_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_approval(
    approval_id: int,
    request: CancelRequest,
    service: ApprovalService = Depends(get_approval_service),
) -> dict:
    """Cancel approval request.

    Args:
        approval_id: Approval request ID
        request: Cancellation request

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: If not found or cannot cancel
    """
    try:
        service.cancel_approval(
            request_id=approval_id,
            cancelled_by=request.cancelled_by,
        )

        return {
            "status": "cancelled",
            "approval_id": approval_id,
            "cancelled_by": request.cancelled_by,
        }

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ApprovalError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error cancelling approval {approval_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling approval: {str(e)}",
        )
