"""HomeAMP V2.0 - Plugin management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from homeamp_v2.api.dependencies import get_uow
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services import UpdateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginResponse(BaseModel):
    """Schema for plugin response."""

    id: int
    instance_id: int
    name: str
    version: Optional[str]
    jar_filename: str
    file_size: Optional[int]
    is_active: bool
    modrinth_id: Optional[str]
    hangar_id: Optional[str]
    github_repo: Optional[str]
    spigot_id: Optional[int]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UpdateCheckResponse(BaseModel):
    """Schema for update check response."""

    plugin_id: int
    plugin_name: str
    current_version: str
    latest_version: str
    update_available: bool
    changelog: Optional[str]
    download_url: Optional[str]
    source: str


@router.get("/", response_model=List[PluginResponse])
def list_plugins(
    instance_id: Optional[int] = Query(None, description="Filter by instance"),
    active_only: bool = Query(True, description="Show only active plugins"),
    uow: UnitOfWork = Depends(get_uow),
):
    """List all plugins with optional filters.

    Args:
        instance_id: Filter by instance ID (optional)
        active_only: Show only active plugins
        uow: Unit of Work

    Returns:
        List of plugins
    """
    try:
        if instance_id:
            plugins = uow.plugins.get_by_instance(instance_id)
        else:
            plugins = uow.session.query(uow.plugins.model).all()

        if active_only:
            plugins = [p for p in plugins if p.is_active]

        return [
            PluginResponse(
                id=p.id,
                instance_id=p.instance_id,
                name=p.name,
                version=p.version,
                jar_filename=p.jar_filename,
                file_size=p.file_size,
                is_active=p.is_active or True,
                modrinth_id=p.modrinth_id,
                hangar_id=p.hangar_id,
                github_repo=p.github_repo,
                spigot_id=p.spigot_id,
                created_at=p.created_at.isoformat() if p.created_at else "",
                updated_at=p.updated_at.isoformat() if p.updated_at else "",
            )
            for p in plugins
        ]
    except Exception as e:
        logger.error(f"Error listing plugins: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_id}", response_model=PluginResponse)
def get_plugin(plugin_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get plugin by ID.

    Args:
        plugin_id: Plugin ID
        uow: Unit of Work

    Returns:
        Plugin details
    """
    try:
        plugin = uow.plugins.get_by_id(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")

        return PluginResponse(
            id=plugin.id,
            instance_id=plugin.instance_id,
            name=plugin.name,
            version=plugin.version,
            jar_filename=plugin.jar_filename,
            file_size=plugin.file_size,
            is_active=plugin.is_active or True,
            modrinth_id=plugin.modrinth_id,
            hangar_id=plugin.hangar_id,
            github_repo=plugin.github_repo,
            spigot_id=plugin.spigot_id,
            created_at=plugin.created_at.isoformat() if plugin.created_at else "",
            updated_at=plugin.updated_at.isoformat() if plugin.updated_at else "",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting plugin {plugin_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{plugin_id}/check-update", response_model=UpdateCheckResponse)
def check_plugin_update(plugin_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Check for updates for a specific plugin.

    Args:
        plugin_id: Plugin ID
        uow: Unit of Work

    Returns:
        Update check result
    """
    try:
        plugin = uow.plugins.get_by_id(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")

        # Run update check
        update_service = UpdateService(uow)
        updates = update_service.check_plugin_updates(plugin.instance_id)

        # Find update for this plugin
        plugin_update = None
        for update in updates:
            if update.get("plugin_id") == plugin_id:
                plugin_update = update
                break

        if not plugin_update:
            # No update available
            return UpdateCheckResponse(
                plugin_id=plugin.id,
                plugin_name=plugin.name,
                current_version=plugin.version or "unknown",
                latest_version=plugin.version or "unknown",
                update_available=False,
                changelog=None,
                download_url=None,
                source="none",
            )

        return UpdateCheckResponse(
            plugin_id=plugin.id,
            plugin_name=plugin.name,
            current_version=plugin.version or "unknown",
            latest_version=plugin_update.get("latest_version", "unknown"),
            update_available=True,
            changelog=plugin_update.get("changelog"),
            download_url=plugin_update.get("download_url"),
            source=plugin_update.get("source", "unknown"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking update for plugin {plugin_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{plugin_id}/configs")
def get_plugin_configs(plugin_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get all configuration files for a plugin.

    Args:
        plugin_id: Plugin ID
        uow: Unit of Work

    Returns:
        List of config files
    """
    try:
        plugin = uow.plugins.get_by_id(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")

        configs = uow.configs.get_by_plugin(plugin_id)

        return [
            {
                "id": c.id,
                "plugin_name": c.plugin_name,
                "config_path": c.config_path,
                "config_key": c.config_key,
                "config_value": c.config_value,
                "config_type": c.config_type,
            }
            for c in configs
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting configs for plugin {plugin_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{plugin_id}", status_code=204)
def delete_plugin(plugin_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Delete a plugin (soft delete by marking inactive).

    Args:
        plugin_id: Plugin ID
        uow: Unit of Work
    """
    try:
        with uow:
            plugin = uow.plugins.get_by_id(plugin_id)
            if not plugin:
                raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")

            plugin.is_active = False
            uow.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plugin {plugin_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
