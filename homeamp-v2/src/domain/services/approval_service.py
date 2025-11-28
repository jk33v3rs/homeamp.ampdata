"""HomeAMP V2.0 - Approval workflow service."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from homeamp_v2.core.exceptions import ApprovalError, NotFoundError
from homeamp_v2.data.models.deployment import ApprovalRequest, ApprovalVote
from homeamp_v2.data.unit_of_work import UnitOfWork
from sqlalchemy import select

logger = logging.getLogger(__name__)


class ApprovalService:
    """Service for managing approval workflows."""

    def __init__(self, uow: UnitOfWork):
        """Initialize approval service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def create_approval_request(
        self,
        entity_type: str,
        entity_id: int,
        requested_by: str,
        description: str,
        metadata: Optional[Dict] = None,
        required_approvals: int = 1,
    ) -> ApprovalRequest:
        """Create new approval request.

        Args:
            entity_type: Type of entity requiring approval
            entity_id: ID of entity
            requested_by: User requesting approval
            description: Approval description
            metadata: Additional metadata
            required_approvals: Number of approvals required

        Returns:
            Created approval request
        """
        approval = ApprovalRequest(
            entity_type=entity_type,
            entity_id=entity_id,
            requested_by=requested_by,
            description=description,
            metadata=metadata or {},
            required_approvals=required_approvals,
            status="pending",
        )

        self.uow.session.add(approval)
        self.uow.session.flush()

        logger.info(
            f"Created approval request #{approval.id} for {entity_type} {entity_id} "
            f"by {requested_by}"
        )

        return approval

    def add_approval_vote(
        self,
        request_id: int,
        voted_by: str,
        approved: bool,
        comment: Optional[str] = None,
    ) -> ApprovalRequest:
        """Add approval vote to request.

        Args:
            request_id: Approval request ID
            voted_by: User voting
            approved: Whether approved or rejected
            comment: Optional comment

        Returns:
            Updated approval request

        Raises:
            NotFoundError: If request not found
            ApprovalError: If already voted or request not pending
        """
        stmt = select(ApprovalRequest).where(ApprovalRequest.id == request_id)
        result = self.uow.session.execute(stmt)
        request = result.scalar_one_or_none()

        if not request:
            raise NotFoundError(f"Approval request {request_id} not found")

        if request.status != "pending":
            raise ApprovalError(
                f"Cannot vote on {request.status} approval request"
            )

        # Check if user already voted
        existing_vote_stmt = select(ApprovalVote).where(
            ApprovalVote.approval_id == request_id,
            ApprovalVote.voted_by == voted_by,
        )
        existing_vote = self.uow.session.execute(existing_vote_stmt).scalar_one_or_none()

        if existing_vote:
            raise ApprovalError(
                f"User {voted_by} has already voted on this request"
            )

        # Add vote
        vote = ApprovalVote(
            approval_id=request_id,
            voted_by=voted_by,
            approved=approved,
            comment=comment,
        )

        self.uow.session.add(vote)
        self.uow.session.flush()

        # Update request status
        self._update_approval_status(request)

        logger.info(
            f"Added {'approval' if approved else 'rejection'} vote from {voted_by} "
            f"to request #{request_id}"
        )

        return request

    def get_pending_approvals(self, entity_type: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests.

        Args:
            entity_type: Optional filter by entity type

        Returns:
            List of pending approval requests
        """
        stmt = select(ApprovalRequest).where(ApprovalRequest.status == "pending")

        if entity_type:
            stmt = stmt.where(ApprovalRequest.entity_type == entity_type)

        stmt = stmt.order_by(ApprovalRequest.created_at.desc())

        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())

    def get_approval_request(self, request_id: int) -> Optional[ApprovalRequest]:
        """Get approval request by ID.

        Args:
            request_id: Request ID

        Returns:
            Approval request or None
        """
        stmt = select(ApprovalRequest).where(ApprovalRequest.id == request_id)
        result = self.uow.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_approval_votes(self, request_id: int) -> List[ApprovalVote]:
        """Get votes for approval request.

        Args:
            request_id: Request ID

        Returns:
            List of votes
        """
        stmt = select(ApprovalVote).where(ApprovalVote.approval_id == request_id)
        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())

    def _update_approval_status(self, request: ApprovalRequest) -> None:
        """Update approval request status based on votes.

        Args:
            request: Approval request to update
        """
        votes = self.get_approval_votes(request.id)

        approvals = sum(1 for v in votes if v.approved)
        rejections = sum(1 for v in votes if not v.approved)

        if rejections > 0:
            request.status = "rejected"
            request.resolved_at = datetime.utcnow()
        elif approvals >= request.required_approvals:
            request.status = "approved"
            request.resolved_at = datetime.utcnow()

        self.uow.session.flush()

    def cancel_approval(self, request_id: int, cancelled_by: str) -> ApprovalRequest:
        """Cancel approval request.

        Args:
            request_id: Request ID
            cancelled_by: User cancelling

        Returns:
            Cancelled request

        Raises:
            NotFoundError: If request not found
            ApprovalError: If already resolved
        """
        request = self.get_approval_request(request_id)

        if not request:
            raise NotFoundError(f"Approval request {request_id} not found")

        if request.status != "pending":
            raise ApprovalError(f"Cannot cancel {request.status} request")

        request.status = "cancelled"
        request.resolved_at = datetime.utcnow()

        self.uow.session.flush()

        logger.info(
            f"Cancelled approval request #{request_id} by {cancelled_by}"
        )

        return request
