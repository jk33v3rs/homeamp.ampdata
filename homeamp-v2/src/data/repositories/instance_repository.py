"""HomeAMP V2.0 - Instance repository."""

from typing import List, Optional

from sqlalchemy import select

from homeamp_v2.data.models.instance import Instance
from homeamp_v2.data.repositories.base_repository import BaseRepository


class InstanceRepository(BaseRepository[Instance]):
    """Instance repository with specialized queries."""

    def __init__(self, session):
        """Initialize repository."""
        super().__init__(Instance, session)

    def get_by_name(self, name: str) -> Optional[Instance]:
        """Get instance by name."""
        stmt = select(Instance).where(Instance.name == name)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_active(self) -> List[Instance]:
        """Get all active instances."""
        stmt = select(Instance).where(Instance.is_active == 1)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_by_platform(self, platform: str) -> List[Instance]:
        """Get instances by platform."""
        stmt = select(Instance).where(Instance.platform == platform)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_master_servers(self) -> List[Instance]:
        """Get all master servers."""
        stmt = select(Instance).where(Instance.is_master == 1)
        result = self.session.execute(stmt)
        return list(result.scalars().all())
