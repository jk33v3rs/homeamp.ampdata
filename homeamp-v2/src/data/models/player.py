"""HomeAMP V2.0 - Player models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from homeamp_v2.core.database import Base


class Player(Base):
    """Player model."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    first_join: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    last_seen: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Player(uuid='{self.uuid}', username='{self.username}')>"


class PlayerConfigOverride(Base):
    """Player-specific config override model."""

    __tablename__ = "player_config_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    plugin_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    config_key: Mapped[str] = mapped_column(String(500), nullable=False)
    override_value: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PlayerConfigOverride(player_id={self.player_id}, plugin='{self.plugin_name}')>"


class PlayerSession(Base):
    """Player session tracking model."""

    __tablename__ = "player_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    session_start: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    session_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<PlayerSession(player_id={self.player_id}, instance_id={self.instance_id})>"
