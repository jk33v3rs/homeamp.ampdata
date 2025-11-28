"""HomeAMP V2.0 - Tag service for meta-tag management."""

import logging
from typing import Dict, List, Optional

from homeamp_v2.core.exceptions import NotFoundError, ValidationError
from homeamp_v2.data.models.tag import MetaTag
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class TagService:
    """Service for meta-tag management and entity tagging."""

    def __init__(self, uow: UnitOfWork):
        """Initialize tag service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def create_tag(
        self, name: str, description: Optional[str] = None, color: Optional[str] = None
    ) -> MetaTag:
        """Create a new meta tag.

        Args:
            name: Tag name (must be unique)
            description: Optional tag description
            color: Optional color hex code

        Returns:
            Created MetaTag

        Raises:
            ValidationError: If tag name already exists
        """
        # Check if tag already exists
        existing = self.uow.tags.get_by_name(name)
        if existing:
            raise ValidationError(f"Tag '{name}' already exists")

        tag = MetaTag(name=name, description=description, color=color)
        self.uow.tags.add(tag)
        self.uow.commit()

        logger.info(f"Created tag: {name}")
        return tag

    def get_tag(self, tag_id: int) -> MetaTag:
        """Get a tag by ID.

        Args:
            tag_id: Tag ID

        Returns:
            MetaTag

        Raises:
            NotFoundError: If tag not found
        """
        tag = self.uow.tags.get_by_id(tag_id)
        if not tag:
            raise NotFoundError(f"Tag {tag_id} not found")
        return tag

    def get_tag_by_name(self, name: str) -> MetaTag:
        """Get a tag by name.

        Args:
            name: Tag name

        Returns:
            MetaTag

        Raises:
            NotFoundError: If tag not found
        """
        tag = self.uow.tags.get_by_name(name)
        if not tag:
            raise NotFoundError(f"Tag '{name}' not found")
        return tag

    def list_tags(self) -> List[MetaTag]:
        """List all tags.

        Returns:
            List of MetaTag objects
        """
        return self.uow.tags.get_all()

    def update_tag(
        self,
        tag_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> MetaTag:
        """Update a tag.

        Args:
            tag_id: Tag ID
            name: Optional new name
            description: Optional new description
            color: Optional new color

        Returns:
            Updated MetaTag

        Raises:
            NotFoundError: If tag not found
            ValidationError: If new name conflicts with existing tag
        """
        tag = self.get_tag(tag_id)

        if name and name != tag.name:
            # Check if new name conflicts
            existing = self.uow.tags.get_by_name(name)
            if existing and existing.id != tag_id:
                raise ValidationError(f"Tag '{name}' already exists")
            tag.name = name

        if description is not None:
            tag.description = description

        if color is not None:
            tag.color = color

        self.uow.commit()
        logger.info(f"Updated tag {tag_id}: {tag.name}")
        return tag

    def delete_tag(self, tag_id: int) -> None:
        """Delete a tag (and all its assignments).

        Args:
            tag_id: Tag ID

        Raises:
            NotFoundError: If tag not found
        """
        tag = self.get_tag(tag_id)
        self.uow.tags.delete(tag)
        self.uow.commit()
        logger.info(f"Deleted tag {tag_id}: {tag.name}")

    def assign_tag_to_entity(
        self, tag_id: int, entity_type: str, entity_id: int
    ) -> Dict:
        """Assign a tag to an entity.

        Args:
            tag_id: Tag ID
            entity_type: Entity type (instance, plugin, datapack, world, region)
            entity_id: Entity ID

        Returns:
            Assignment details

        Raises:
            NotFoundError: If tag not found
            ValidationError: If entity type is invalid
        """
        # Validate tag exists
        tag = self.get_tag(tag_id)

        # Validate entity type
        valid_types = ["instance", "plugin", "datapack", "world", "region"]
        if entity_type not in valid_types:
            raise ValidationError(f"Invalid entity type. Must be one of: {valid_types}")

        # Create assignment
        assignment = self.uow.tags.assign_tag(tag_id, entity_type, entity_id)
        self.uow.commit()

        logger.info(f"Assigned tag '{tag.name}' to {entity_type} {entity_id}")
        return {
            "tag_id": tag_id,
            "tag_name": tag.name,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "assignment_id": assignment.id,
        }

    def remove_tag_from_entity(
        self, tag_id: int, entity_type: str, entity_id: int
    ) -> bool:
        """Remove a tag from an entity.

        Args:
            tag_id: Tag ID
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            True if removed, False if not found

        Raises:
            NotFoundError: If tag not found
        """
        # Validate tag exists
        self.get_tag(tag_id)

        removed = self.uow.tags.remove_tag(tag_id, entity_type, entity_id)
        if removed:
            self.uow.commit()
            logger.info(f"Removed tag {tag_id} from {entity_type} {entity_id}")
        return removed

    def get_entity_tags(self, entity_type: str, entity_id: int) -> List[Dict]:
        """Get all tags for an entity.

        Args:
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            List of tag dictionaries
        """
        tags = self.uow.tags.get_tags_by_entity(entity_type, entity_id)
        return [
            {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
                "color": tag.color,
            }
            for tag in tags
        ]

    def get_entities_by_tag(
        self, tag_id: int, entity_type: Optional[str] = None
    ) -> List[Dict]:
        """Get all entities with a specific tag.

        Args:
            tag_id: Tag ID
            entity_type: Optional entity type filter

        Returns:
            List of entity dictionaries

        Raises:
            NotFoundError: If tag not found
        """
        # Validate tag exists
        tag = self.get_tag(tag_id)

        assignments = self.uow.tags.get_entities_by_tag(tag_id, entity_type)
        return [
            {
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "assigned_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in assignments
        ]

    def create_tag_relationship(self, parent_tag_id: int, child_tag_id: int) -> Dict:
        """Create a parent-child relationship between tags.

        Args:
            parent_tag_id: Parent tag ID
            child_tag_id: Child tag ID

        Returns:
            Relationship details

        Raises:
            NotFoundError: If either tag not found
            ValidationError: If trying to create circular relationship
        """
        # Validate both tags exist
        parent_tag = self.get_tag(parent_tag_id)
        child_tag = self.get_tag(child_tag_id)

        # Prevent self-relationship
        if parent_tag_id == child_tag_id:
            raise ValidationError("Cannot create relationship with self")

        # Create relationship
        relationship = self.uow.tags.create_relationship(parent_tag_id, child_tag_id)
        self.uow.commit()

        logger.info(
            f"Created tag relationship: {parent_tag.name} -> {child_tag.name}"
        )
        return {
            "parent_tag_id": parent_tag_id,
            "parent_tag_name": parent_tag.name,
            "child_tag_id": child_tag_id,
            "child_tag_name": child_tag.name,
            "relationship_id": relationship.id,
        }

    def remove_tag_relationship(self, parent_tag_id: int, child_tag_id: int) -> bool:
        """Remove a tag relationship.

        Args:
            parent_tag_id: Parent tag ID
            child_tag_id: Child tag ID

        Returns:
            True if removed, False if not found
        """
        removed = self.uow.tags.remove_relationship(parent_tag_id, child_tag_id)
        if removed:
            self.uow.commit()
            logger.info(f"Removed tag relationship: {parent_tag_id} -> {child_tag_id}")
        return removed

    def get_tag_hierarchy(self, tag_id: int) -> Dict:
        """Get full tag hierarchy (parents and children).

        Args:
            tag_id: Tag ID

        Returns:
            Dictionary with hierarchy structure

        Raises:
            NotFoundError: If tag not found
        """
        # Validate tag exists
        self.get_tag(tag_id)

        hierarchy = self.uow.tags.get_tag_hierarchy(tag_id)
        return hierarchy

    def get_instance_tags_with_metadata(self, instance_id: int) -> Dict:
        """Get tags for an instance with additional metadata.

        Args:
            instance_id: Instance ID

        Returns:
            Dictionary with tags and metadata
        """
        tags = self.get_entity_tags("instance", instance_id)

        # Get instance info
        instance = self.uow.instances.get_by_id(instance_id)
        if not instance:
            raise NotFoundError(f"Instance {instance_id} not found")

        return {
            "instance_id": instance_id,
            "instance_name": instance.name,
            "tags": tags,
            "tag_count": len(tags),
        }
