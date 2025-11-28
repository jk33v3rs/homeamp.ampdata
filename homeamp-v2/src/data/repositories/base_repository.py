"""HomeAMP V2.0 - Base repository with generic CRUD operations."""

from typing import Any, Generic, List, Optional, Type, TypeVar

from homeamp_v2.core.database import Base
from homeamp_v2.core.exceptions import DatabaseError
from sqlalchemy import select
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with CRUD operations."""

    def __init__(self, model: Type[ModelType], session: Session):
        """Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Database session
        """
        self.model = model
        self.session = session

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get entity by ID.

        Args:
            id: Entity ID

        Returns:
            Entity or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.session.get(self.model, id)
        except Exception as e:
            raise DatabaseError(f"Failed to get {self.model.__name__} by id={id}: {e}") from e

    def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """Get all entities.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            stmt = select(self.model).limit(limit).offset(offset)
            result = self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(f"Failed to get all {self.model.__name__}: {e}") from e

    def create(self, **kwargs: Any) -> ModelType:
        """Create new entity.

        Args:
            **kwargs: Entity attributes

        Returns:
            Created entity

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            entity = self.model(**kwargs)
            self.session.add(entity)
            self.session.flush()
            return entity
        except Exception as e:
            raise DatabaseError(f"Failed to create {self.model.__name__}: {e}") from e

    def update(self, id: int, **kwargs: Any) -> Optional[ModelType]:
        """Update entity.

        Args:
            id: Entity ID
            **kwargs: Attributes to update

        Returns:
            Updated entity or None if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            entity = self.get_by_id(id)
            if entity is None:
                return None

            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            self.session.flush()
            return entity
        except Exception as e:
            raise DatabaseError(f"Failed to update {self.model.__name__} id={id}: {e}") from e

    def delete(self, id: int) -> bool:
        """Delete entity.

        Args:
            id: Entity ID

        Returns:
            True if deleted, False if not found

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            entity = self.get_by_id(id)
            if entity is None:
                return False

            self.session.delete(entity)
            self.session.flush()
            return True
        except Exception as e:
            raise DatabaseError(f"Failed to delete {self.model.__name__} id={id}: {e}") from e

    def count(self) -> int:
        """Count all entities.

        Returns:
            Number of entities

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            stmt = select(self.model)
            result = self.session.execute(stmt)
            return len(list(result.scalars().all()))
        except Exception as e:
            raise DatabaseError(f"Failed to count {self.model.__name__}: {e}") from e

    def exists(self, id: int) -> bool:
        """Check if entity exists.

        Args:
            id: Entity ID

        Returns:
            True if exists, False otherwise

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            return self.get_by_id(id) is not None
        except Exception as e:
            raise DatabaseError(f"Failed to check if {self.model.__name__} id={id} exists: {e}") from e
