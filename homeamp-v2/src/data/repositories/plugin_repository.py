"""HomeAMP V2.0 - Plugin repository."""

from typing import List, Optional

from sqlalchemy import and_, select

from homeamp_v2.data.models.plugin import InstancePlugin, Plugin, PluginUpdateQueue
from homeamp_v2.data.repositories.base_repository import BaseRepository


class PluginRepository(BaseRepository[Plugin]):
    """Plugin repository with specialized queries."""

    def __init__(self, session):
        """Initialize repository."""
        super().__init__(Plugin, session)

    def get_by_name(self, name: str) -> Optional[Plugin]:
        """Get plugin by name."""
        stmt = select(Plugin).where(Plugin.name == name)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_paid_plugins(self) -> List[Plugin]:
        """Get all paid plugins."""
        stmt = select(Plugin).where(Plugin.is_paid == 1)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_instance_plugins(self, instance_id: int) -> List[InstancePlugin]:
        """Get all plugins for an instance."""
        stmt = select(InstancePlugin).where(InstancePlugin.instance_id == instance_id)
        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_pending_updates(self, instance_id: Optional[int] = None) -> List[PluginUpdateQueue]:
        """Get pending plugin updates."""
        stmt = select(PluginUpdateQueue).where(PluginUpdateQueue.status == "pending")

        if instance_id:
            stmt = stmt.where(PluginUpdateQueue.instance_id == instance_id)

        result = self.session.execute(stmt)
        return list(result.scalars().all())

    def get_plugin_version(self, plugin_id: int, instance_id: int) -> Optional[str]:
        """Get installed plugin version for an instance."""
        stmt = select(InstancePlugin).where(
            and_(InstancePlugin.plugin_id == plugin_id, InstancePlugin.instance_id == instance_id)
        )
        result = self.session.execute(stmt)
        instance_plugin = result.scalar_one_or_none()
        return instance_plugin.version if instance_plugin else None
