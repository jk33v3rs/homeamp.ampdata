"""HomeAMP V2.0 - Tag repository."""

from typing import List, Optional

from homeamp_v2.data.models.tag import MetaTag, TagAssignment, TagRelationship
from homeamp_v2.data.repositories.base_repository import BaseRepository
from sqlalchemy import and_, select


class TagRepository(BaseRepository[MetaTag]):
    """Tag repository with specialized queries."""

    def __init__(self, session):
        """Initialize repository."""
        super().__init__(MetaTag, session)

    def get_by_name(self, name: str) -> Optional[MetaTag]:
        """Get tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            MetaTag or None
        """
        stmt = select(MetaTag).where(MetaTag.name == name)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_tags_by_entity(self, entity_type: str, entity_id: int) -> List[MetaTag]:
        """Get all tags assigned to an entity.
        
        Args:
            entity_type: Entity type (instance, plugin, datapack, world, region)
            entity_id: Entity ID
            
        Returns:
            List of MetaTag objects
        """
        stmt = (
            select(MetaTag)
            .join(TagAssignment, TagAssignment.tag_id == MetaTag.id)
            .where(
                and_(
                    TagAssignment.entity_type == entity_type,
                    TagAssignment.entity_id == entity_id,
                )
            )
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_entities_by_tag(self, tag_id: int, entity_type: Optional[str] = None) -> List[TagAssignment]:
        """Get all entities assigned to a tag.
        
        Args:
            tag_id: Tag ID
            entity_type: Optional entity type filter
            
        Returns:
            List of TagAssignment objects
        """
        stmt = select(TagAssignment).where(TagAssignment.tag_id == tag_id)
        
        if entity_type:
            stmt = stmt.where(TagAssignment.entity_type == entity_type)
            
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def assign_tag(self, tag_id: int, entity_type: str, entity_id: int) -> TagAssignment:
        """Assign a tag to an entity.
        
        Args:
            tag_id: Tag ID
            entity_type: Entity type
            entity_id: Entity ID
            
        Returns:
            Created TagAssignment
        """
        # Check if assignment already exists
        stmt = select(TagAssignment).where(
            and_(
                TagAssignment.tag_id == tag_id,
                TagAssignment.entity_type == entity_type,
                TagAssignment.entity_id == entity_id,
            )
        )
        existing = self.session.execute(stmt).scalar_one_or_none()
        
        if existing:
            return existing
            
        # Create new assignment
        assignment = TagAssignment(
            tag_id=tag_id,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self.session.add(assignment)
        self.session.flush()
        return assignment

    def remove_tag(self, tag_id: int, entity_type: str, entity_id: int) -> bool:
        """Remove a tag from an entity.
        
        Args:
            tag_id: Tag ID
            entity_type: Entity type
            entity_id: Entity ID
            
        Returns:
            True if removed, False if not found
        """
        stmt = select(TagAssignment).where(
            and_(
                TagAssignment.tag_id == tag_id,
                TagAssignment.entity_type == entity_type,
                TagAssignment.entity_id == entity_id,
            )
        )
        assignment = self.session.execute(stmt).scalar_one_or_none()
        
        if assignment:
            self.session.delete(assignment)
            self.session.flush()
            return True
        return False

    def get_child_tags(self, parent_tag_id: int) -> List[MetaTag]:
        """Get all child tags of a parent tag.
        
        Args:
            parent_tag_id: Parent tag ID
            
        Returns:
            List of child MetaTag objects
        """
        stmt = (
            select(MetaTag)
            .join(TagRelationship, TagRelationship.child_tag_id == MetaTag.id)
            .where(TagRelationship.parent_tag_id == parent_tag_id)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_parent_tags(self, child_tag_id: int) -> List[MetaTag]:
        """Get all parent tags of a child tag.
        
        Args:
            child_tag_id: Child tag ID
            
        Returns:
            List of parent MetaTag objects
        """
        stmt = (
            select(MetaTag)
            .join(TagRelationship, TagRelationship.parent_tag_id == MetaTag.id)
            .where(TagRelationship.child_tag_id == child_tag_id)
        )
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def create_relationship(self, parent_tag_id: int, child_tag_id: int) -> TagRelationship:
        """Create a parent-child relationship between tags.
        
        Args:
            parent_tag_id: Parent tag ID
            child_tag_id: Child tag ID
            
        Returns:
            Created TagRelationship
        """
        relationship = TagRelationship(
            parent_tag_id=parent_tag_id,
            child_tag_id=child_tag_id,
        )
        self.session.add(relationship)
        self.session.flush()
        return relationship

    def remove_relationship(self, parent_tag_id: int, child_tag_id: int) -> bool:
        """Remove a parent-child relationship.
        
        Args:
            parent_tag_id: Parent tag ID
            child_tag_id: Child tag ID
            
        Returns:
            True if removed, False if not found
        """
        stmt = select(TagRelationship).where(
            and_(
                TagRelationship.parent_tag_id == parent_tag_id,
                TagRelationship.child_tag_id == child_tag_id,
            )
        )
        relationship = self.session.execute(stmt).scalar_one_or_none()
        
        if relationship:
            self.session.delete(relationship)
            self.session.flush()
            return True
        return False

    def get_tag_hierarchy(self, tag_id: int, max_depth: int = 5) -> dict:
        """Get full tag hierarchy (parents and children) for a tag.
        
        Args:
            tag_id: Tag ID
            max_depth: Maximum depth to traverse
            
        Returns:
            Dictionary with parents and children hierarchies
        """
        tag = self.get_by_id(tag_id)
        if not tag:
            return {}
            
        def get_children_recursive(tid: int, depth: int = 0) -> List[dict]:
            if depth >= max_depth:
                return []
            children = self.get_child_tags(tid)
            return [
                {
                    "id": child.id,
                    "name": child.name,
                    "description": child.description,
                    "children": get_children_recursive(child.id, depth + 1),
                }
                for child in children
            ]
            
        def get_parents_recursive(tid: int, depth: int = 0) -> List[dict]:
            if depth >= max_depth:
                return []
            parents = self.get_parent_tags(tid)
            return [
                {
                    "id": parent.id,
                    "name": parent.name,
                    "description": parent.description,
                    "parents": get_parents_recursive(parent.id, depth + 1),
                }
                for parent in parents
            ]
        
        return {
            "tag": {
                "id": tag.id,
                "name": tag.name,
                "description": tag.description,
            },
            "parents": get_parents_recursive(tag_id),
            "children": get_children_recursive(tag_id),
        }
