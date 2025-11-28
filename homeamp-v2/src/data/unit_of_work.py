"""HomeAMP V2.0 - Unit of Work pattern implementation."""

from typing import Optional

from homeamp_v2.core.database import session_scope
from homeamp_v2.core.exceptions import DatabaseError
from homeamp_v2.data.repositories.config_repository import ConfigRepository
from homeamp_v2.data.repositories.deployment_repository import DeploymentRepository
from homeamp_v2.data.repositories.instance_repository import InstanceRepository
from homeamp_v2.data.repositories.monitoring_repository import MonitoringRepository
from homeamp_v2.data.repositories.plugin_repository import PluginRepository
from homeamp_v2.data.repositories.tag_repository import TagRepository
from sqlalchemy.orm import Session


class UnitOfWork:
    """Unit of Work manages database transactions and repository access.

    Usage:
        with UnitOfWork() as uow:
            instance = uow.instances.get_by_name("survival")
            instance.friendly_name = "Survival Server"
            uow.commit()
    """

    def __init__(self, session: Optional[Session] = None):
        """Initialize Unit of Work.

        Args:
            session: Optional existing session (creates new if not provided)
        """
        self._session = session
        self._context_manager = None
        self._instances: Optional[InstanceRepository] = None
        self._plugins: Optional[PluginRepository] = None
        self._configs: Optional[ConfigRepository] = None
        self._deployments: Optional[DeploymentRepository] = None
        self._monitoring: Optional[MonitoringRepository] = None
        self._tags: Optional[TagRepository] = None

    def __enter__(self) -> "UnitOfWork":
        """Enter context manager."""
        if self._session is None:
            self._context_manager = session_scope()
            self._session = self._context_manager.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._context_manager is not None:
            self._context_manager.__exit__(exc_type, exc_val, exc_tb)
            self._context_manager = None
            self._session = None

    @property
    def instances(self) -> InstanceRepository:
        """Get instance repository."""
        if self._instances is None:
            self._instances = InstanceRepository(self._session)
        return self._instances

    @property
    def plugins(self) -> PluginRepository:
        """Get plugin repository."""
        if self._plugins is None:
            self._plugins = PluginRepository(self._session)
        return self._plugins

    @property
    def configs(self) -> ConfigRepository:
        """Get config repository."""
        if self._configs is None:
            self._configs = ConfigRepository(self._session)
        return self._configs

    @property
    def deployments(self) -> DeploymentRepository:
        """Get deployment repository."""
        if self._deployments is None:
            self._deployments = DeploymentRepository(self._session)
        return self._deployments

    @property
    def monitoring(self) -> MonitoringRepository:
        """Get monitoring repository."""
        if self._monitoring is None:
            self._monitoring = MonitoringRepository(self._session)
        return self._monitoring

    @property
    def tags(self) -> TagRepository:
        """Get tag repository."""
        if self._tags is None:
            self._tags = TagRepository(self._session)
        return self._tags

    @property
    def session(self) -> Session:
        """Get the current session."""
        return self._session

    def commit(self) -> None:
        """Commit the transaction."""
        try:
            self._session.commit()
        except Exception as e:
            self._session.rollback()
            raise DatabaseError(f"Failed to commit transaction: {e}") from e

    def rollback(self) -> None:
        """Rollback the transaction."""
        self._session.rollback()

    def flush(self) -> None:
        """Flush pending changes to database."""
        try:
            self._session.flush()
        except Exception as e:
            self._session.rollback()
            raise DatabaseError(f"Failed to flush session: {e}") from e
