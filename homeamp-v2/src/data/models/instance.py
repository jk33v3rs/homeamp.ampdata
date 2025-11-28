"""HomeAMP V2.0 - Instance model."""

from datetime import datetime
from typing import Optional

from homeamp_v2.core.database import Base
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Instance(Base):
    """AMP instance model."""

    __tablename__ = "instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    friendly_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    minecraft_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    base_path: Mapped[str] = mapped_column(String(500), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_master: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    plugins: Mapped[list["InstancePlugin"]] = relationship("InstancePlugin", back_populates="instance", cascade="all, delete-orphan")
    datapacks: Mapped[list["InstanceDatapack"]] = relationship("InstanceDatapack", back_populates="instance", cascade="all, delete-orphan")
    config_values: Mapped[list["ConfigValue"]] = relationship("ConfigValue", back_populates="instance", cascade="all, delete-orphan")
    server_properties: Mapped[list["ServerProperty"]] = relationship("ServerProperty", back_populates="instance", cascade="all, delete-orphan")
    worlds: Mapped[list["World"]] = relationship("World", back_populates="instance", cascade="all, delete-orphan")
    group_members: Mapped[list["InstanceGroupMember"]] = relationship("InstanceGroupMember", back_populates="instance", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Instance(id={self.id}, name='{self.name}', platform='{self.platform}')>"
