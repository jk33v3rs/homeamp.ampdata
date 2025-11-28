"""HomeAMP V2.0 - Tag management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from homeamp_v2.api.dependencies import get_uow
from homeamp_v2.core.exceptions import NotFoundError, ValidationError
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services.tag_service import TagService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreateRequest(BaseModel):
    """Schema for tag creation."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TagUpdateRequest(BaseModel):
    """Schema for tag update."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TagResponse(BaseModel):
    """Schema for tag response."""

    id: int
    name: str
    description: Optional[str]
    color: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class TagAssignmentRequest(BaseModel):
    """Schema for tag assignment."""

    entity_type: str = Field(..., pattern="^(instance|plugin|datapack|world|region)$")
    entity_id: int = Field(..., gt=0)


class TagRelationshipRequest(BaseModel):
    """Schema for tag relationship creation."""

    parent_tag_id: int = Field(..., gt=0)
    child_tag_id: int = Field(..., gt=0)


@router.post("/", response_model=TagResponse, status_code=201)
def create_tag(request: TagCreateRequest, uow: UnitOfWork = Depends(get_uow)):
    """Create a new meta tag.

    Args:
        request: Tag creation request
        uow: Unit of Work

    Returns:
        Created tag
    """
    try:
        with uow:
            tag_service = TagService(uow)
            tag = tag_service.create_tag(
                name=request.name,
                description=request.description,
                color=request.color,
            )

        return TagResponse(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            color=tag.color,
            created_at=tag.created_at.isoformat() if tag.created_at else "",
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tag: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[TagResponse])
def list_tags(uow: UnitOfWork = Depends(get_uow)):
    """List all meta tags.

    Args:
        uow: Unit of Work

    Returns:
        List of tags
    """
    try:
        with uow:
            tag_service = TagService(uow)
            tags = tag_service.list_tags()

        return [
            TagResponse(
                id=tag.id,
                name=tag.name,
                description=tag.description,
                color=tag.color,
                created_at=tag.created_at.isoformat() if tag.created_at else "",
            )
            for tag in tags
        ]
    except Exception as e:
        logger.error(f"Error listing tags: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(tag_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get a tag by ID.

    Args:
        tag_id: Tag ID
        uow: Unit of Work

    Returns:
        Tag details
    """
    try:
        with uow:
            tag_service = TagService(uow)
            tag = tag_service.get_tag(tag_id)

        return TagResponse(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            color=tag.color,
            created_at=tag.created_at.isoformat() if tag.created_at else "",
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    except Exception as e:
        logger.error(f"Error getting tag {tag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int, request: TagUpdateRequest, uow: UnitOfWork = Depends(get_uow)
):
    """Update a tag.

    Args:
        tag_id: Tag ID
        request: Tag update request
        uow: Unit of Work

    Returns:
        Updated tag
    """
    try:
        with uow:
            tag_service = TagService(uow)
            tag = tag_service.update_tag(
                tag_id=tag_id,
                name=request.name,
                description=request.description,
                color=request.color,
            )

        return TagResponse(
            id=tag.id,
            name=tag.name,
            description=tag.description,
            color=tag.color,
            created_at=tag.created_at.isoformat() if tag.created_at else "",
        )
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tag {tag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Delete a tag.

    Args:
        tag_id: Tag ID
        uow: Unit of Work
    """
    try:
        with uow:
            tag_service = TagService(uow)
            tag_service.delete_tag(tag_id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    except Exception as e:
        logger.error(f"Error deleting tag {tag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tag_id}/assign", status_code=201)
def assign_tag(
    tag_id: int, request: TagAssignmentRequest, uow: UnitOfWork = Depends(get_uow)
):
    """Assign a tag to an entity.

    Args:
        tag_id: Tag ID
        request: Assignment request
        uow: Unit of Work

    Returns:
        Assignment details
    """
    try:
        with uow:
            tag_service = TagService(uow)
            result = tag_service.assign_tag_to_entity(
                tag_id=tag_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
            )

        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning tag {tag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tag_id}/assign", status_code=204)
def remove_tag_assignment(
    tag_id: int,
    entity_type: str = Query(..., pattern="^(instance|plugin|datapack|world|region)$"),
    entity_id: int = Query(..., gt=0),
    uow: UnitOfWork = Depends(get_uow),
):
    """Remove a tag from an entity.

    Args:
        tag_id: Tag ID
        entity_type: Entity type
        entity_id: Entity ID
        uow: Unit of Work
    """
    try:
        with uow:
            tag_service = TagService(uow)
            removed = tag_service.remove_tag_from_entity(
                tag_id=tag_id, entity_type=entity_type, entity_id=entity_id
            )

        if not removed:
            raise HTTPException(status_code=404, detail="Tag assignment not found")
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error removing tag assignment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tag_id}/entities")
def get_entities_by_tag(
    tag_id: int,
    entity_type: Optional[str] = Query(
        None, pattern="^(instance|plugin|datapack|world|region)$"
    ),
    uow: UnitOfWork = Depends(get_uow),
):
    """Get all entities with a specific tag.

    Args:
        tag_id: Tag ID
        entity_type: Optional entity type filter
        uow: Unit of Work

    Returns:
        List of entities
    """
    try:
        with uow:
            tag_service = TagService(uow)
            entities = tag_service.get_entities_by_tag(
                tag_id=tag_id, entity_type=entity_type
            )

        return {"tag_id": tag_id, "entities": entities, "total": len(entities)}
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    except Exception as e:
        logger.error(f"Error getting entities for tag {tag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tag_id}/hierarchy")
def get_tag_hierarchy(tag_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Get tag hierarchy (parents and children).

    Args:
        tag_id: Tag ID
        uow: Unit of Work

    Returns:
        Tag hierarchy
    """
    try:
        with uow:
            tag_service = TagService(uow)
            hierarchy = tag_service.get_tag_hierarchy(tag_id)

        return hierarchy
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"Tag {tag_id} not found")
    except Exception as e:
        logger.error(f"Error getting tag hierarchy for {tag_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships", status_code=201)
def create_tag_relationship(
    request: TagRelationshipRequest, uow: UnitOfWork = Depends(get_uow)
):
    """Create a parent-child relationship between tags.

    Args:
        request: Relationship request
        uow: Unit of Work

    Returns:
        Relationship details
    """
    try:
        with uow:
            tag_service = TagService(uow)
            result = tag_service.create_tag_relationship(
                parent_tag_id=request.parent_tag_id, child_tag_id=request.child_tag_id
            )

        return result
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating tag relationship: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/relationships", status_code=204)
def remove_tag_relationship(
    parent_tag_id: int = Query(..., gt=0),
    child_tag_id: int = Query(..., gt=0),
    uow: UnitOfWork = Depends(get_uow),
):
    """Remove a tag relationship.

    Args:
        parent_tag_id: Parent tag ID
        child_tag_id: Child tag ID
        uow: Unit of Work
    """
    try:
        with uow:
            tag_service = TagService(uow)
            removed = tag_service.remove_tag_relationship(
                parent_tag_id=parent_tag_id, child_tag_id=child_tag_id
            )

        if not removed:
            raise HTTPException(status_code=404, detail="Tag relationship not found")
    except Exception as e:
        logger.error(f"Error removing tag relationship: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_type}/{entity_id}")
def get_entity_tags(
    entity_type: str, entity_id: int, uow: UnitOfWork = Depends(get_uow)
):
    """Get all tags for a specific entity.

    Args:
        entity_type: Entity type (instance, plugin, datapack, world, region)
        entity_id: Entity ID
        uow: Unit of Work

    Returns:
        List of tags
    """
    try:
        with uow:
            tag_service = TagService(uow)
            tags = tag_service.get_entity_tags(
                entity_type=entity_type, entity_id=entity_id
            )

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "tags": tags,
            "total": len(tags),
        }
    except Exception as e:
        logger.error(
            f"Error getting tags for {entity_type} {entity_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
