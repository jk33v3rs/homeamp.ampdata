"""HomeAMP V2.0 - Instance management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from homeamp_v2.api.dependencies import get_uow
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services import DiscoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/instances", tags=["instances"])


# Pydantic schemas for request/response
class InstanceCreate(BaseModel):
    """Schema for creating an instance."""

    name: str
    base_path: str
    minecraft_version: Optional[str] = None
    server_software: Optional[str] = None
    server_port: Optional[int] = None
    amp_instance_id: Optional[str] = None


class InstanceUpdate(BaseModel):
    """Schema for updating an instance."""

    name: Optional[str] = None
    minecraft_version: Optional[str] = None
    server_software: Optional[str] = None
    server_port: Optional[int] = None
    is_master: Optional[bool] = None


class InstanceResponse(BaseModel):
    """Schema for instance response."""

    id: int
    name: str
    base_path: str
    minecraft_version: Optional[str]
    server_software: Optional[str]
    server_port: Optional[int]
    amp_instance_id: Optional[str]
    is_master: bool
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[InstanceResponse])
def list_instances(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    active_only: bool = Query(True, description="Show only active instances"),
    uow: UnitOfWork = Depends(get_uow),
):
    """List all instances with optional filters.

    Args:
        platform: Filter by platform (optional)
        active_only: Show only active instances
        uow: Unit of Work

    Returns:
        List of instances
    """
    try:
        instances = uow.instances.get_all_instances(active_only=active_only)

        if platform:
            instances = [i for i in instances if i.platform == platform]

        return [
            InstanceResponse(
                id=i.id,
                name=i.name,
                base_path=i.base_path,
                minecraft_version=i.minecraft_version,
                server_software=i.server_software,
                server_port=i.server_port,
                amp_instance_id=i.amp_instance_id,
                is_master=i.is_master or False,
                is_active=i.is_active or True,
                created_at=i.created_at.isoformat() if i.created_at else "",
                updated_at=i.updated_at.isoformat() if i.updated_at else "",
            )
            for i in instances
        ]
    except Exception as e:
        logger.error(f"Error listing instances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}", response_model=InstanceResponse)
def get_instance(instance_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get instance by ID.

    Args:
        instance_id: Instance ID
        uow: Unit of Work

    Returns:
        Instance details
    """
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

        return InstanceResponse(
            id=instance.id,
            name=instance.name,
            base_path=instance.base_path,
            minecraft_version=instance.minecraft_version,
            server_software=instance.server_software,
            server_port=instance.server_port,
            amp_instance_id=instance.amp_instance_id,
            is_master=instance.is_master or False,
            is_active=instance.is_active or True,
            created_at=instance.created_at.isoformat() if instance.created_at else "",
            updated_at=instance.updated_at.isoformat() if instance.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=InstanceResponse, status_code=201)
def create_instance(data: InstanceCreate, uow: UnitOfWork = Depends(get_uow)):
    """Create a new instance.

    Args:
        data: Instance creation data
        uow: Unit of Work

    Returns:
        Created instance
    """
    try:
        from homeamp_v2.data.models.instance import Instance

        instance = Instance(
            name=data.name,
            base_path=data.base_path,
            minecraft_version=data.minecraft_version,
            server_software=data.server_software,
            server_port=data.server_port,
            amp_instance_id=data.amp_instance_id,
        )

        with uow:
            uow.session.add(instance)
            uow.commit()
            uow.session.refresh(instance)

            return InstanceResponse(
                id=instance.id,
                name=instance.name,
                base_path=instance.base_path,
                minecraft_version=instance.minecraft_version,
                server_software=instance.server_software,
                server_port=instance.server_port,
                amp_instance_id=instance.amp_instance_id,
                is_master=instance.is_master or False,
                is_active=instance.is_active or True,
                created_at=instance.created_at.isoformat() if instance.created_at else "",
                updated_at=instance.updated_at.isoformat() if instance.updated_at else "",
            )
    except Exception as e:
        logger.error(f"Error creating instance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{instance_id}", response_model=InstanceResponse)
def update_instance(instance_id: int, data: InstanceUpdate, uow: UnitOfWork = Depends(get_uow)):
    """Update an instance.

    Args:
        instance_id: Instance ID
        data: Instance update data
        uow: Unit of Work

    Returns:
        Updated instance
    """
    try:
        with uow:
            instance = uow.instances.get_by_id(instance_id)
            if not instance:
                raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

            # Update fields
            if data.name is not None:
                instance.name = data.name
            if data.minecraft_version is not None:
                instance.minecraft_version = data.minecraft_version
            if data.server_software is not None:
                instance.server_software = data.server_software
            if data.server_port is not None:
                instance.server_port = data.server_port
            if data.is_master is not None:
                instance.is_master = data.is_master

            uow.commit()
            uow.session.refresh(instance)

            return InstanceResponse(
                id=instance.id,
                name=instance.name,
                base_path=instance.base_path,
                minecraft_version=instance.minecraft_version,
                server_software=instance.server_software,
                server_port=instance.server_port,
                amp_instance_id=instance.amp_instance_id,
                is_master=instance.is_master or False,
                is_active=instance.is_active or True,
                created_at=instance.created_at.isoformat() if instance.created_at else "",
                updated_at=instance.updated_at.isoformat() if instance.updated_at else "",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{instance_id}", status_code=204)
def delete_instance(instance_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Delete an instance (soft delete by marking inactive).

    Args:
        instance_id: Instance ID
        uow: Unit of Work
    """
    try:
        with uow:
            instance = uow.instances.get_by_id(instance_id)
            if not instance:
                raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

            instance.is_active = False
            uow.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{instance_id}/scan", status_code=202)
def scan_instance(instance_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Trigger a discovery scan for an instance.

    Args:
        instance_id: Instance ID
        uow: Unit of Work

    Returns:
        Scan status
    """
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

        # Run discovery scan
        discovery = DiscoveryService(uow)
        discovery.scan_instance(instance_id)

        return {"status": "scanning", "instance_id": instance_id, "instance_name": instance.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{instance_id}/plugins")
def get_instance_plugins(instance_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get all plugins for an instance.

    Args:
        instance_id: Instance ID
        uow: Unit of Work

    Returns:
        List of plugins
    """
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            raise HTTPException(status_code=404, detail=f"Instance {instance_id} not found")

        plugins = uow.plugins.get_by_instance(instance_id)

        return [
            {
                "id": p.id,
                "name": p.name,
                "version": p.version,
                "jar_filename": p.jar_filename,
                "is_active": p.is_active or True,
            }
            for p in plugins
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugins for instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
