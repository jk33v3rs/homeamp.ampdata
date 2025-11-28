"""HomeAMP V2.0 - Configuration models."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from homeamp_v2.core.database import Base
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from homeamp_v2.data.models.instance import Instance


class ConfigRule(Base):
    """Configuration rule definition model."""

    __tablename__ = "config_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plugin_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    key_path: Mapped[str] = mapped_column(String(500), nullable=False)
    expected_value: Mapped[str] = mapped_column(Text, nullable=False)
    scope_type: Mapped[str] = mapped_column(Enum("global", "instance", "group", "world", "region", "rank", name="scope_type_enum"), default="global", nullable=False, index=True)
    scope_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    enforcement_level: Mapped[str] = mapped_column(Enum("required", "recommended", "optional", name="enforcement_level_enum"), default="recommended", nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    variances: Mapped[list["ConfigVariance"]] = relationship("ConfigVariance", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ConfigRule(id={self.id}, plugin='{self.plugin_name}', file='{self.file_path}', key='{self.key_path}')>"


class ConfigValue(Base):
    """Actual configuration value from instance."""

    __tablename__ = "config_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    plugin_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    key_path: Mapped[str] = mapped_column(String(500), nullable=False)
    actual_value: Mapped[str] = mapped_column(Text, nullable=False)
    value_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    last_scanned: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    instance: Mapped["Instance"] = relationship("Instance", back_populates="config_values")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<ConfigValue(instance_id={self.instance_id}, plugin='{self.plugin_name}', key='{self.key_path}')>"


class ConfigVariance(Base):
    """Configuration variance detection model."""

    __tablename__ = "config_variances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    rule_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    expected_value: Mapped[str] = mapped_column(Text, nullable=False)
    actual_value: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Enum("new", "acknowledged", "resolved", "ignored", name="variance_status_enum"), default="new", nullable=False, index=True)
    auto_resolvable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    rule: Mapped["ConfigRule"] = relationship("ConfigRule", back_populates="variances")

    def __repr__(self) -> str:
        return f"<ConfigVariance(instance_id={self.instance_id}, rule_id={self.rule_id}, severity={self.severity})>"


class ConfigChange(Base):
    """Configuration change history model."""

    __tablename__ = "config_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    config_value_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    old_value: Mapped[str] = mapped_column(Text, nullable=False)
    new_value: Mapped[str] = mapped_column(Text, nullable=False)
    changed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ConfigChange(instance_id={self.instance_id}, changed_by='{self.changed_by}')>"


class ConfigVariable(Base):
    """Configuration template variable model."""

    __tablename__ = "config_variables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    scope_type: Mapped[str] = mapped_column(Enum("global", "instance", "group", name="variable_scope_enum"), default="global", nullable=False, index=True)
    scope_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ConfigVariable(name='{self.name}', scope='{self.scope_type}')>"


class ConfigFileMetadata(Base):
    """Configuration file metadata model."""

    __tablename__ = "config_file_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    file_type: Mapped[str] = mapped_column(Enum("yaml", "json", "properties", "toml", name="file_type_enum"), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    last_modified: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_scanned: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ConfigFileMetadata(instance_id={self.instance_id}, file='{self.file_path}')>"
