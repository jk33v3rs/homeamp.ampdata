"""HomeAMP V2.0 - Deployment management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from homeamp_v2.api.dependencies import get_uow
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services import DeploymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/deployments", tags=["deployments"])


class DeploymentCreate(BaseModel):
    """Schema for creating a deployment."""

    instance_id: int
    deployment_type: str
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    target_version: Optional[str] = None
    priority: int = 5
    notes: Optional[str] = None


class DeploymentResponse(BaseModel):
    """Schema for deployment response."""

    id: int
    instance_id: int
    deployment_type: str
    target_name: Optional[str]
    target_version: Optional[str]
    status: str
    priority: int
    scheduled_for: Optional[str]
    executed_at: Optional[str]
    notes: Optional[str]
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class ApprovalRequest(BaseModel):
    """Schema for approval request."""

    approved: bool
    notes: Optional[str] = None


@router.get("/", response_model=List[DeploymentResponse])
def list_deployments(
    instance_id: Optional[int] = Query(None, description="Filter by instance"),
    status: Optional[str] = Query(None, description="Filter by status"),
    uow: UnitOfWork = Depends(get_uow),
):
    """List all deployments with optional filters.

    Args:
        instance_id: Filter by instance ID (optional)
        status: Filter by status (optional)
        uow: Unit of Work

    Returns:
        List of deployments
    """
    try:
        if status == "pending":
            deployments = DeploymentService(uow).get_pending_deployments(instance_id)
        else:
            # Get all deployments
            query = uow.session.query(uow.deployments.model)
            if instance_id:
                query = query.filter(uow.deployments.model.instance_id == instance_id)
            if status:
                query = query.filter(uow.deployments.model.status == status)
            deployments = query.all()

        return [
            DeploymentResponse(
                id=d.id,
                instance_id=d.instance_id,
                deployment_type=d.deployment_type,
                target_name=d.target_name,
                target_version=d.target_version,
                status=d.status,
                priority=d.priority or 5,
                scheduled_for=d.scheduled_for.isoformat() if d.scheduled_for else None,
                executed_at=d.executed_at.isoformat() if d.executed_at else None,
                notes=d.notes,
                error_message=d.error_message,
                created_at=d.created_at.isoformat() if d.created_at else "",
            )
            for d in deployments
        ]
    except Exception as e:
        logger.error(f"Error listing deployments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{deployment_id}", response_model=DeploymentResponse)
def get_deployment(deployment_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get deployment by ID.

    Args:
        deployment_id: Deployment ID
        uow: Unit of Work

    Returns:
        Deployment details
    """
    try:
        deployment = uow.deployments.get_by_id(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

        return DeploymentResponse(
            id=deployment.id,
            instance_id=deployment.instance_id,
            deployment_type=deployment.deployment_type,
            target_name=deployment.target_name,
            target_version=deployment.target_version,
            status=deployment.status,
            priority=deployment.priority or 5,
            scheduled_for=deployment.scheduled_for.isoformat() if deployment.scheduled_for else None,
            executed_at=deployment.executed_at.isoformat() if deployment.executed_at else None,
            notes=deployment.notes,
            error_message=deployment.error_message,
            created_at=deployment.created_at.isoformat() if deployment.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting deployment {deployment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=DeploymentResponse, status_code=201)
def create_deployment(data: DeploymentCreate, uow: UnitOfWork = Depends(get_uow)):
    """Queue a new deployment.

    Args:
        data: Deployment creation data
        uow: Unit of Work

    Returns:
        Created deployment
    """
    try:
        # Verify instance exists
        instance = uow.instances.get_by_id(data.instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {data.instance_id} not found")

        # Queue deployment
        deployment_service = DeploymentService(uow)
        deployment_id = deployment_service.queue_deployment(
            instance_id=data.instance_id,
            deployment_type=data.deployment_type,
            target_id=data.target_id,
            target_name=data.target_name,
            target_version=data.target_version,
            priority=data.priority,
            notes=data.notes,
        )

        # Retrieve created deployment
        deployment = uow.deployments.get_by_id(deployment_id)

        return DeploymentResponse(
            id=deployment.id,
            instance_id=deployment.instance_id,
            deployment_type=deployment.deployment_type,
            target_name=deployment.target_name,
            target_version=deployment.target_version,
            status=deployment.status,
            priority=deployment.priority or 5,
            scheduled_for=deployment.scheduled_for.isoformat() if deployment.scheduled_for else None,
            executed_at=deployment.executed_at.isoformat() if deployment.executed_at else None,
            notes=deployment.notes,
            error_message=deployment.error_message,
            created_at=deployment.created_at.isoformat() if deployment.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating deployment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{deployment_id}/approve", response_model=DeploymentResponse)
def approve_deployment(deployment_id: int, data: ApprovalRequest, uow: UnitOfWork = Depends(get_uow)):
    """Approve or reject a deployment.

    Args:
        deployment_id: Deployment ID
        data: Approval decision
        uow: Unit of Work

    Returns:
        Updated deployment
    """
    try:
        deployment = uow.deployments.get_by_id(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

        deployment_service = DeploymentService(uow)
        deployment_service.approve_deployment(deployment_id, data.approved, data.notes)

        # Refresh deployment
        uow.session.refresh(deployment)

        return DeploymentResponse(
            id=deployment.id,
            instance_id=deployment.instance_id,
            deployment_type=deployment.deployment_type,
            target_name=deployment.target_name,
            target_version=deployment.target_version,
            status=deployment.status,
            priority=deployment.priority or 5,
            scheduled_for=deployment.scheduled_for.isoformat() if deployment.scheduled_for else None,
            executed_at=deployment.executed_at.isoformat() if deployment.executed_at else None,
            notes=deployment.notes,
            error_message=deployment.error_message,
            created_at=deployment.created_at.isoformat() if deployment.created_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving deployment {deployment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{deployment_id}/execute", status_code=202)
def execute_deployment(deployment_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Execute a deployment.

    Args:
        deployment_id: Deployment ID
        uow: Unit of Work

    Returns:
        Execution status
    """
    try:
        deployment = uow.deployments.get_by_id(deployment_id)
        if not deployment:
            raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

        deployment_service = DeploymentService(uow)
        result = deployment_service.execute_deployment(deployment_id)

        return {
            "status": "executing",
            "deployment_id": deployment_id,
            "success": result.get("success", False),
            "message": result.get("message", "Deployment started"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing deployment {deployment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{deployment_id}", status_code=204)
def delete_deployment(deployment_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Cancel/delete a deployment.

    Args:
        deployment_id: Deployment ID
        uow: Unit of Work
    """
    try:
        with uow:
            deployment = uow.deployments.get_by_id(deployment_id)
            if not deployment:
                raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

            # Can only cancel pending deployments
            if deployment.status not in ["pending", "awaiting_approval"]:
                raise HTTPException(
                    status_code=400, detail=f"Cannot cancel deployment with status: {deployment.status}"
                )

            deployment.status = "cancelled"
            uow.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling deployment {deployment_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
