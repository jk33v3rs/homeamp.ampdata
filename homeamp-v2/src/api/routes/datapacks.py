"""HomeAMP V2.0 - Datapack API routes."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from homeamp_v2.api.dependencies import get_datapack_service
from homeamp_v2.core.exceptions import NotFoundError, ValidationError
from homeamp_v2.domain.services.datapack_service import DatapackService
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datapacks", tags=["datapacks"])


class DatapackResponse(BaseModel):
    """Datapack response."""

    id: int
    name: str
    description: str | None
    source_url: str | None


class VersionResponse(BaseModel):
    """Datapack version response."""

    id: int
    version: str
    minecraft_version: str
    download_url: str | None
    released_at: str


class InstanceDatapackResponse(BaseModel):
    """Instance datapack response."""

    id: int
    name: str
    description: str | None
    version: str
    enabled: bool
    load_order: int


class AssignDatapackRequest(BaseModel):
    """Request to assign datapack to instance."""

    datapack_id: int
    version: str
    enabled: bool = True
    load_order: int = 0


class CreateDatapackRequest(BaseModel):
    """Request to create datapack."""

    name: str
    description: str | None = None
    source_url: str | None = None


@router.get("/", response_model=List[DatapackResponse])
async def list_datapacks(
    service: DatapackService = Depends(get_datapack_service),
) -> List[DatapackResponse]:
    """List all datapacks.

    Returns:
        List of datapacks
    """
    datapacks = service.get_all_datapacks()

    return [
        DatapackResponse(
            id=dp.id,
            name=dp.name,
            description=dp.description,
            source_url=dp.source_url,
        )
        for dp in datapacks
    ]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=DatapackResponse)
async def create_datapack(
    request: CreateDatapackRequest,
    service: DatapackService = Depends(get_datapack_service),
) -> DatapackResponse:
    """Create new datapack.

    Args:
        request: Datapack creation request

    Returns:
        Created datapack

    Raises:
        HTTPException: If datapack already exists
    """
    try:
        datapack = service.create_datapack(
            name=request.name,
            description=request.description,
            source_url=request.source_url,
        )

        return DatapackResponse(
            id=datapack.id,
            name=datapack.name,
            description=datapack.description,
            source_url=datapack.source_url,
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating datapack: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating datapack: {str(e)}",
        )


@router.get("/{datapack_id}", response_model=DatapackResponse)
async def get_datapack(
    datapack_id: int,
    service: DatapackService = Depends(get_datapack_service),
) -> DatapackResponse:
    """Get datapack by ID.

    Args:
        datapack_id: Datapack ID

    Returns:
        Datapack details

    Raises:
        HTTPException: If not found
    """
    datapack = service.get_datapack(datapack_id)
    if not datapack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Datapack {datapack_id} not found",
        )

    return DatapackResponse(
        id=datapack.id,
        name=datapack.name,
        description=datapack.description,
        source_url=datapack.source_url,
    )


@router.get("/{datapack_id}/versions", response_model=List[VersionResponse])
async def get_datapack_versions(
    datapack_id: int,
    service: DatapackService = Depends(get_datapack_service),
) -> List[VersionResponse]:
    """Get versions for datapack.

    Args:
        datapack_id: Datapack ID

    Returns:
        List of versions
    """
    versions = service.get_datapack_versions(datapack_id)

    return [
        VersionResponse(
            id=v.id,
            version=v.version,
            minecraft_version=v.minecraft_version,
            download_url=v.download_url,
            released_at=v.released_at.isoformat() if v.released_at else None,
        )
        for v in versions
    ]


@router.get("/instances/{instance_id}", response_model=List[InstanceDatapackResponse])
async def get_instance_datapacks(
    instance_id: int,
    service: DatapackService = Depends(get_datapack_service),
) -> List[InstanceDatapackResponse]:
    """Get datapacks for instance.

    Args:
        instance_id: Instance ID

    Returns:
        List of instance datapacks
    """
    datapacks = service.get_instance_datapacks(instance_id)

    return [
        InstanceDatapackResponse(
            id=dp["id"],
            name=dp["name"],
            description=dp["description"],
            version=dp["version"],
            enabled=dp["enabled"],
            load_order=dp["load_order"],
        )
        for dp in datapacks
    ]


@router.post("/instances/{instance_id}", status_code=status.HTTP_201_CREATED)
async def assign_datapack_to_instance(
    instance_id: int,
    request: AssignDatapackRequest,
    service: DatapackService = Depends(get_datapack_service),
) -> dict:
    """Assign datapack to instance.

    Args:
        instance_id: Instance ID
        request: Assignment request

    Returns:
        Success confirmation

    Raises:
        HTTPException: If datapack not found or already assigned
    """
    try:
        service.assign_datapack_to_instance(
            datapack_id=request.datapack_id,
            instance_id=instance_id,
            version=request.version,
            enabled=request.enabled,
            load_order=request.load_order,
        )

        return {
            "status": "assigned",
            "datapack_id": request.datapack_id,
            "instance_id": instance_id,
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
        logger.error(f"Error assigning datapack: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning datapack: {str(e)}",
        )


@router.delete("/instances/{instance_id}/datapacks/{datapack_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_datapack_from_instance(
    instance_id: int,
    datapack_id: int,
    service: DatapackService = Depends(get_datapack_service),
) -> None:
    """Remove datapack from instance.

    Args:
        instance_id: Instance ID
        datapack_id: Datapack ID

    Raises:
        HTTPException: If not found
    """
    try:
        service.remove_datapack_from_instance(datapack_id, instance_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error removing datapack: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error removing datapack: {str(e)}",
        )
