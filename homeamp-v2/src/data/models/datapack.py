"""HomeAMP V2.0 - Datapack models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from homeamp_v2.core.database import Base
from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from homeamp_v2.data.models.instance import Instance
    from homeamp_v2.data.models.world import World


class Datapack(Base):
    """Datapack definition model."""

    __tablename__ = "datapacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pack_format: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    instances: Mapped[list["InstanceDatapack"]] = relationship("InstanceDatapack", back_populates="datapack", cascade="all, delete-orphan")
    versions: Mapped[list["DatapackVersion"]] = relationship("DatapackVersion", back_populates="datapack", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Datapack(id={self.id}, name='{self.name}')>"


class InstanceDatapack(Base):
    """Instance-datapack association model."""

    __tablename__ = "instance_datapacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    datapack_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    installed_version: Mapped[str] = mapped_column(String(50), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    instance: Mapped["Instance"] = relationship("Instance", back_populates="datapacks")
    datapack: Mapped["Datapack"] = relationship("Datapack", back_populates="instances")
    world: Mapped["World"] = relationship("World")

    def __repr__(self) -> str:
        return f"<InstanceDatapack(instance_id={self.instance_id}, datapack_id={self.datapack_id})>"


class DatapackVersion(Base):
    """Datapack version catalog model."""

    __tablename__ = "datapack_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datapack_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    pack_format: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minecraft_versions: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    release_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    download_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    datapack: Mapped["Datapack"] = relationship("Datapack", back_populates="versions")

    def __repr__(self) -> str:
        return f"<DatapackVersion(datapack_id={self.datapack_id}, version='{self.version}')>"


class DatapackDeploymentQueue(Base):
    """Datapack deployment queue model."""

    __tablename__ = "datapack_deployment_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_datapack_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_version_id: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Enum("pending", "approved", "rejected", "deployed", "failed", name="datapack_status_enum"), default="pending", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<DatapackDeploymentQueue(id={self.id}, status='{self.status}')>"


class DatapackUpdateSource(Base):
    """Datapack update source configuration model."""

    __tablename__ = "datapack_update_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datapack_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(Enum("github", "modrinth", "manual", name="datapack_source_enum"), nullable=False)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<DatapackUpdateSource(datapack_id={self.datapack_id}, source_type='{self.source_type}')>"
