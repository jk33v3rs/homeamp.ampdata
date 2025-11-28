"""HomeAMP V2.0 - Instance Group model."""

from datetime import datetime
from typing import Optional

from homeamp_v2.core.database import Base
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class InstanceGroup(Base):
    """Instance group model for organizing instances."""

    __tablename__ = "instance_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    members: Mapped[list["InstanceGroupMember"]] = relationship("InstanceGroupMember", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<InstanceGroup(id={self.id}, name='{self.name}')>"


class InstanceGroupMember(Base):
    """Instance group membership model."""

    __tablename__ = "instance_group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    group: Mapped["InstanceGroup"] = relationship("InstanceGroup", back_populates="members")
    instance: Mapped["Instance"] = relationship("Instance", back_populates="group_members")

    def __repr__(self) -> str:
        return f"<InstanceGroupMember(group_id={self.group_id}, instance_id={self.instance_id})>"
