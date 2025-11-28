"""HomeAMP V2.0 - World, Region, and Rank models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from homeamp_v2.core.database import Base
from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from homeamp_v2.data.models.instance import Instance
    from homeamp_v2.data.models.player import Player


class World(Base):
    """Minecraft world model."""

    __tablename__ = "worlds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    world_type: Mapped[str] = mapped_column(String(50), nullable=False)
    seed: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    game_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    folder_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    instance: Mapped["Instance"] = relationship("Instance", back_populates="worlds")
    regions: Mapped[list["Region"]] = relationship("Region", back_populates="world", cascade="all, delete-orphan")
    group_members: Mapped[list["WorldGroupMember"]] = relationship("WorldGroupMember", back_populates="world", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<World(id={self.id}, name='{self.name}', type='{self.world_type}')>"


class WorldGroup(Base):
    """World group model."""

    __tablename__ = "world_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    members: Mapped[list["WorldGroupMember"]] = relationship("WorldGroupMember", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<WorldGroup(id={self.id}, name='{self.name}')>"


class WorldGroupMember(Base):
    """World group membership model."""

    __tablename__ = "world_group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    group: Mapped["WorldGroup"] = relationship("WorldGroup", back_populates="members")
    world: Mapped["World"] = relationship("World", back_populates="group_members")

    def __repr__(self) -> str:
        return f"<WorldGroupMember(group_id={self.group_id}, world_id={self.world_id})>"


class Region(Base):
    """WorldGuard/GriefPrevention region model."""

    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    world_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    region_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region_type: Mapped[str] = mapped_column(String(50), nullable=False)
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    min_x: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_z: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_x: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_z: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    world: Mapped["World"] = relationship("World", back_populates="regions")
    group_members: Mapped[list["RegionGroupMember"]] = relationship("RegionGroupMember", back_populates="region", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Region(id={self.id}, region_id='{self.region_id}', type='{self.region_type}')>"


class RegionGroup(Base):
    """Region group model."""

    __tablename__ = "region_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    members: Mapped[list["RegionGroupMember"]] = relationship("RegionGroupMember", back_populates="group", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<RegionGroup(id={self.id}, name='{self.name}')>"


class RegionGroupMember(Base):
    """Region group membership model."""

    __tablename__ = "region_group_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    region_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    group: Mapped["RegionGroup"] = relationship("RegionGroup", back_populates="members")
    region: Mapped["Region"] = relationship("Region", back_populates="group_members")

    def __repr__(self) -> str:
        return f"<RegionGroupMember(group_id={self.group_id}, region_id={self.region_id})>"


class Rank(Base):
    """LuckPerms rank model."""

    __tablename__ = "ranks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    weight: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    prefix: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    player_ranks: Mapped[list["PlayerRank"]] = relationship("PlayerRank", back_populates="rank", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Rank(id={self.id}, name='{self.name}', weight={self.weight})>"


class PlayerRank(Base):
    """Player rank assignment model."""

    __tablename__ = "player_ranks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    rank_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    is_primary: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    rank: Mapped["Rank"] = relationship("Rank", back_populates="player_ranks")
    player: Mapped["Player"] = relationship("Player")

    def __repr__(self) -> str:
        return f"<PlayerRank(player_id={self.player_id}, rank_id={self.rank_id})>"
