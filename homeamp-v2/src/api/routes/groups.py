"""HomeAMP V2.0 - Instance group API routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from homeamp_v2.api.dependencies import get_group_service
from homeamp_v2.core.exceptions import NotFoundError, ValidationError
from homeamp_v2.domain.services.group_service import GroupService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    """Request to create instance group."""

    name: str
    description: str | None = None
    group_type: str = "manual"


class AddInstanceRequest(BaseModel):
    """Request to add instance to group."""

    instance_id: int


class GroupResponse(BaseModel):
    """Instance group response."""

    id: int
    name: str
    description: str | None
    group_type: str
    instance_count: int | None = None


class InstanceResponse(BaseModel):
    """Instance response."""

    id: int
    name: str
    server_name: str
    instance_type: str
    status: str


@router.get("/", response_model=List[GroupResponse])
async def list_groups(
    service: GroupService = Depends(get_group_service),
) -> List[GroupResponse]:
    """List all instance groups.

    Returns:
        List of instance groups
    """
    groups = service.get_all_groups()

    return [
        GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
        )
        for group in groups
    ]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    """Create new instance group.

    Args:
        request: Group creation request

    Returns:
        Created group

    Raises:
        HTTPException: If group already exists
    """
    try:
        group = service.create_group(
            name=request.name,
            description=request.description,
            group_type=request.group_type,
        )

        return GroupResponse(
            id=group.id,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating group: {str(e)}",
        )


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    """Get instance group by ID.

    Args:
        group_id: Group ID

    Returns:
        Instance group

    Raises:
        HTTPException: If not found
    """
    group = service.get_group(group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group {group_id} not found",
        )

    instances = service.get_group_instances(group_id)

    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        group_type=group.group_type,
        instance_count=len(instances),
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
) -> None:
    """Delete instance group.

    Args:
        group_id: Group ID

    Raises:
        HTTPException: If not found
    """
    try:
        service.delete_group(group_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error deleting group {group_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting group: {str(e)}",
        )


@router.get("/{group_id}/instances", response_model=List[InstanceResponse])
async def get_group_instances(
    group_id: int,
    service: GroupService = Depends(get_group_service),
) -> List[InstanceResponse]:
    """Get instances in group.

    Args:
        group_id: Group ID

    Returns:
        List of instances
    """
    instances = service.get_group_instances(group_id)

    return [
        InstanceResponse(
            id=instance.id,
            name=instance.name,
            server_name=instance.server_name,
            instance_type=instance.instance_type,
            status=instance.status,
        )
        for instance in instances
    ]


@router.post("/{group_id}/instances", status_code=status.HTTP_201_CREATED)
async def add_instance_to_group(
    group_id: int,
    request: AddInstanceRequest,
    service: GroupService = Depends(get_group_service),
) -> dict:
    """Add instance to group.

    Args:
        group_id: Group ID
        request: Add instance request

    Returns:
        Success confirmation

    Raises:
        HTTPException: If group/instance not found or already member
    """
    try:
        service.add_instance_to_group(group_id, request.instance_id)

        return {
            "status": "added",
            "group_id": group_id,
            "instance_id": request.instance_id,
        }

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error adding instance to group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding instance: {str(e)}",
        )


@router.delete("/{group_id}/instances/{instance_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_instance_from_group(
    group_id: int,
    instance_id: int,
    service: GroupService = Depends(get_group_service),
) -> None:
    """Remove instance from group.

    Args:
        group_id: Group ID
        instance_id: Instance ID

    Raises:
        HTTPException: If not found
    """
    try:
        service.remove_instance_from_group(group_id, instance_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error removing instance from group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing instance: {str(e)}",
        )
