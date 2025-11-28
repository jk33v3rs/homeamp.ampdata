"""HomeAMP V2.0 - Server properties models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from homeamp_v2.core.database import Base


class ServerProperty(Base):
    """Server.properties value model."""

    __tablename__ = "server_properties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    property_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    property_value: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    last_scanned: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    instance: Mapped["Instance"] = relationship("Instance", back_populates="server_properties")

    def __repr__(self) -> str:
        return f"<ServerProperty(instance_id={self.instance_id}, key='{self.property_key}')>"


class ServerPropertyVariance(Base):
    """Server properties variance model."""

    __tablename__ = "server_properties_variances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    property_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expected_value: Mapped[str] = mapped_column(Text, nullable=False)
    actual_value: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ServerPropertyVariance(instance_id={self.instance_id}, key='{self.property_key}')>"
