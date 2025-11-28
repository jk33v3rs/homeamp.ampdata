"""HomeAMP V2.0 - Deployment models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from homeamp_v2.core.database import Base


class DeploymentQueue(Base):
    """Deployment queue model."""

    __tablename__ = "deployment_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    deployment_type: Mapped[str] = mapped_column(Enum("plugin", "datapack", "config", "server_property", name="deployment_type_enum"), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(Enum("install", "update", "remove", "configure", name="deployment_action_enum"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Enum("pending", "approved", "rejected", "in_progress", "completed", "failed", name="deployment_status_enum"), default="pending", nullable=False, index=True)
    requires_approval: Mapped[bool] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<DeploymentQueue(id={self.id}, type='{self.deployment_type}', status='{self.status}')>"


class DeploymentHistory(Base):
    """Deployment execution history model."""

    __tablename__ = "deployment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    queue_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    instance_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    deployment_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(Enum("success", "failed", "rolled_back", name="history_status_enum"), nullable=False, index=True)
    executed_by: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DeploymentHistory(id={self.id}, status='{self.status}', duration={self.duration_ms}ms)>"


class DeploymentChange(Base):
    """Deployment change details model."""

    __tablename__ = "deployment_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    history_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<DeploymentChange(history_id={self.history_id}, type='{self.change_type}')>"


class DeploymentLog(Base):
    """Deployment execution log model."""

    __tablename__ = "deployment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    history_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    log_level: Mapped[str] = mapped_column(Enum("debug", "info", "warning", "error", name="log_level_enum"), default="info", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<DeploymentLog(history_id={self.history_id}, level='{self.log_level}')>"


class ApprovalRequest(Base):
    """Approval request model."""

    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    queue_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(255), nullable=False)
    required_approvals: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(Enum("pending", "approved", "rejected", "expired", name="approval_status_enum"), default="pending", nullable=False, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ApprovalRequest(queue_id={self.queue_id}, status='{self.status}')>"


class ApprovalVote(Base):
    """Approval vote model."""

    __tablename__ = "approval_votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    approval_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    approver: Mapped[str] = mapped_column(String(255), nullable=False)
    vote: Mapped[str] = mapped_column(Enum("approve", "reject", name="vote_enum"), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ApprovalVote(approval_id={self.approval_id}, approver='{self.approver}', vote='{self.vote}')>"
