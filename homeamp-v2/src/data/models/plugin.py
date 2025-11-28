"""HomeAMP V2.0 - Plugin models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from homeamp_v2.core.database import Base
from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from homeamp_v2.data.models.instance import Instance


class Plugin(Base):
    """Plugin definition model."""

    __tablename__ = "plugins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    jar_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    update_source: Mapped[Optional[str]] = mapped_column(Enum("modrinth", "hangar", "github", "spigot", "manual", name="update_source_enum"), nullable=True, index=True)
    update_source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    instances: Mapped[list["InstancePlugin"]] = relationship("InstancePlugin", back_populates="plugin", cascade="all, delete-orphan")
    versions: Mapped[list["PluginVersion"]] = relationship("PluginVersion", back_populates="plugin", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Plugin(id={self.id}, name='{self.name}')>"


class InstancePlugin(Base):
    """Instance-plugin association model with version tracking."""

    __tablename__ = "instance_plugins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    plugin_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    installed_version: Mapped[str] = mapped_column(String(50), nullable=False)
    jar_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    jar_size: Mapped[int] = mapped_column(Integer, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    instance: Mapped["Instance"] = relationship("Instance", back_populates="plugins")
    plugin: Mapped["Plugin"] = relationship("Plugin", back_populates="instances")

    def __repr__(self) -> str:
        return f"<InstancePlugin(instance_id={self.instance_id}, plugin_id={self.plugin_id}, version='{self.installed_version}')>"


class PluginVersion(Base):
    """Plugin version catalog model."""

    __tablename__ = "plugin_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plugin_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    minecraft_versions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    plugin: Mapped["Plugin"] = relationship("Plugin", back_populates="versions")

    def __repr__(self) -> str:
        return f"<PluginVersion(plugin_id={self.plugin_id}, version='{self.version}')>"


class PluginUpdateQueue(Base):
    """Plugin update queue model."""

    __tablename__ = "plugin_update_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_plugin_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_version_id: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Enum("pending", "approved", "rejected", "deployed", "failed", name="update_status_enum"), default="pending", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PluginUpdateQueue(id={self.id}, status='{self.status}', priority={self.priority})>"


class PluginUpdateSource(Base):
    """Plugin update source configuration model."""

    __tablename__ = "plugin_update_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plugin_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(Enum("modrinth", "hangar", "github", "spigot", name="source_type_enum"), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PluginUpdateSource(plugin_id={self.plugin_id}, source_type='{self.source_type}')>"


class PluginMigration(Base):
    """Plugin migration tracking model."""

    __tablename__ = "plugin_migrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_plugin_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    to_plugin_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PluginMigration(from_plugin_id={self.from_plugin_id}, to_plugin_id={self.to_plugin_id})>"
