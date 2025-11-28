"""HomeAMP V2.0 - Tag models for polymorphic tagging system."""

from datetime import datetime
from typing import Optional

from homeamp_v2.core.database import Base
from sqlalchemy import DateTime, Enum, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class MetaTag(Base):
    """Meta tag definition model."""

    __tablename__ = "meta_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    assignments: Mapped[list["TagAssignment"]] = relationship("TagAssignment", back_populates="tag", cascade="all, delete-orphan")
    parent_relationships: Mapped[list["TagRelationship"]] = relationship("TagRelationship", foreign_keys="TagRelationship.parent_tag_id", back_populates="parent_tag", cascade="all, delete-orphan")
    child_relationships: Mapped[list["TagRelationship"]] = relationship("TagRelationship", foreign_keys="TagRelationship.child_tag_id", back_populates="child_tag", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<MetaTag(id={self.id}, name='{self.name}')>"


class TagAssignment(Base):
    """Polymorphic tag assignment model."""

    __tablename__ = "tag_assignments"
    __table_args__ = (UniqueConstraint("tag_id", "entity_type", "entity_id", name="uq_tag_entity"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tag_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(Enum("instance", "plugin", "datapack", "world", "region", name="entity_type_enum"), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    tag: Mapped["MetaTag"] = relationship("MetaTag", back_populates="assignments")

    def __repr__(self) -> str:
        return f"<TagAssignment(tag_id={self.tag_id}, entity_type='{self.entity_type}', entity_id={self.entity_id})>"


class TagRelationship(Base):
    """Tag hierarchy relationship model."""

    __tablename__ = "tag_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_tag_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    child_tag_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    parent_tag: Mapped["MetaTag"] = relationship("MetaTag", foreign_keys=[parent_tag_id], back_populates="parent_relationships")
    child_tag: Mapped["MetaTag"] = relationship("MetaTag", foreign_keys=[child_tag_id], back_populates="child_relationships")

    def __repr__(self) -> str:
        return f"<TagRelationship(parent_tag_id={self.parent_tag_id}, child_tag_id={self.child_tag_id})>"
