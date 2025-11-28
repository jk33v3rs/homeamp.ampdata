"""HomeAMP V2.0 - FastAPI dependency injection."""

from typing import Generator

from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services import (
    ApprovalService,
    AuditService,
    DashboardService,
    DatapackService,
    GroupService,
    UpdateService,
)


def get_uow() -> Generator[UnitOfWork, None, None]:
    """Get Unit of Work instance for dependency injection.

    Yields:
        UnitOfWork instance
    """
    uow = UnitOfWork()
    try:
        yield uow
    finally:
        uow.close()


def get_approval_service(uow: UnitOfWork = get_uow()) -> ApprovalService:
    """Get ApprovalService instance.

    Args:
        uow: Unit of Work

    Returns:
        ApprovalService instance
    """
    return ApprovalService(uow)


def get_audit_service(uow: UnitOfWork = get_uow()) -> AuditService:
    """Get AuditService instance.

    Args:
        uow: Unit of Work

    Returns:
        AuditService instance
    """
    return AuditService(uow)


def get_dashboard_service(uow: UnitOfWork = get_uow()) -> DashboardService:
    """Get DashboardService instance.

    Args:
        uow: Unit of Work

    Returns:
        DashboardService instance
    """
    return DashboardService(uow)


def get_datapack_service(uow: UnitOfWork = get_uow()) -> DatapackService:
    """Get DatapackService instance.

    Args:
        uow: Unit of Work

    Returns:
        DatapackService instance
    """
    return DatapackService(uow)


def get_group_service(uow: UnitOfWork = get_uow()) -> GroupService:
    """Get GroupService instance.

    Args:
        uow: Unit of Work

    Returns:
        GroupService instance
    """
    return GroupService(uow)


def get_update_service(uow: UnitOfWork = get_uow()) -> UpdateService:
    """Get UpdateService instance.

    Args:
        uow: Unit of Work

    Returns:
        UpdateService instance
    """
    return UpdateService(uow)
