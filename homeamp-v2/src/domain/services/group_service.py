"""HomeAMP V2.0 - Instance group management service."""

import logging
from typing import List, Optional

from homeamp_v2.core.exceptions import NotFoundError, ValidationError
from homeamp_v2.data.models.instance import (
    Instance,
    InstanceGroup,
    InstanceGroupMembership,
)
from homeamp_v2.data.unit_of_work import UnitOfWork
from sqlalchemy import select

logger = logging.getLogger(__name__)


class GroupService:
    """Service for managing instance groups."""

    def __init__(self, uow: UnitOfWork):
        """Initialize group service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def get_all_groups(self) -> List[InstanceGroup]:
        """Get all instance groups.

        Returns:
            List of instance groups
        """
        stmt = select(InstanceGroup).order_by(InstanceGroup.name)
        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())

    def get_group(self, group_id: int) -> Optional[InstanceGroup]:
        """Get group by ID.

        Args:
            group_id: Group ID

        Returns:
            Instance group or None
        """
        stmt = select(InstanceGroup).where(InstanceGroup.id == group_id)
        result = self.uow.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_group_by_name(self, name: str) -> Optional[InstanceGroup]:
        """Get group by name.

        Args:
            name: Group name

        Returns:
            Instance group or None
        """
        stmt = select(InstanceGroup).where(InstanceGroup.name == name)
        result = self.uow.session.execute(stmt)
        return result.scalar_one_or_none()

    def create_group(
        self,
        name: str,
        description: Optional[str] = None,
        group_type: str = "manual",
    ) -> InstanceGroup:
        """Create new instance group.

        Args:
            name: Group name
            description: Optional description
            group_type: Group type (manual, server, network, etc.)

        Returns:
            Created instance group

        Raises:
            ValidationError: If group already exists
        """
        existing = self.get_group_by_name(name)
        if existing:
            raise ValidationError(f"Group '{name}' already exists")

        group = InstanceGroup(
            name=name,
            description=description,
            group_type=group_type,
        )

        self.uow.session.add(group)
        self.uow.session.flush()

        logger.info(f"Created instance group '{name}'")

        return group

    def delete_group(self, group_id: int) -> None:
        """Delete instance group.

        Args:
            group_id: Group ID

        Raises:
            NotFoundError: If group not found
        """
        group = self.get_group(group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found")

        # Delete memberships first
        self.uow.session.query(InstanceGroupMembership).filter(
            InstanceGroupMembership.group_id == group_id
        ).delete()

        self.uow.session.delete(group)
        self.uow.session.flush()

        logger.info(f"Deleted instance group {group_id}")

    def add_instance_to_group(
        self, group_id: int, instance_id: int
    ) -> InstanceGroupMembership:
        """Add instance to group.

        Args:
            group_id: Group ID
            instance_id: Instance ID

        Returns:
            Created membership

        Raises:
            NotFoundError: If group not found
            ValidationError: If already member
        """
        group = self.get_group(group_id)
        if not group:
            raise NotFoundError(f"Group {group_id} not found")

        # Check if already member
        existing_stmt = select(InstanceGroupMembership).where(
            InstanceGroupMembership.group_id == group_id,
            InstanceGroupMembership.instance_id == instance_id,
        )
        existing = self.uow.session.execute(existing_stmt).scalar_one_or_none()

        if existing:
            raise ValidationError(
                f"Instance {instance_id} already in group {group_id}"
            )

        membership = InstanceGroupMembership(
            group_id=group_id,
            instance_id=instance_id,
        )

        self.uow.session.add(membership)
        self.uow.session.flush()

        logger.info(f"Added instance {instance_id} to group {group_id}")

        return membership

    def remove_instance_from_group(
        self, group_id: int, instance_id: int
    ) -> None:
        """Remove instance from group.

        Args:
            group_id: Group ID
            instance_id: Instance ID

        Raises:
            NotFoundError: If membership not found
        """
        stmt = select(InstanceGroupMembership).where(
            InstanceGroupMembership.group_id == group_id,
            InstanceGroupMembership.instance_id == instance_id,
        )
        membership = self.uow.session.execute(stmt).scalar_one_or_none()

        if not membership:
            raise NotFoundError(
                f"Instance {instance_id} not in group {group_id}"
            )

        self.uow.session.delete(membership)
        self.uow.session.flush()

        logger.info(f"Removed instance {instance_id} from group {group_id}")

    def get_group_instances(self, group_id: int) -> List[Instance]:
        """Get instances in group.

        Args:
            group_id: Group ID

        Returns:
            List of instances
        """
        stmt = (
            select(Instance)
            .join(
                InstanceGroupMembership,
                Instance.id == InstanceGroupMembership.instance_id,
            )
            .where(InstanceGroupMembership.group_id == group_id)
            .order_by(Instance.name)
        )

        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())

    def get_instance_groups(self, instance_id: int) -> List[InstanceGroup]:
        """Get groups containing instance.

        Args:
            instance_id: Instance ID

        Returns:
            List of instance groups
        """
        stmt = (
            select(InstanceGroup)
            .join(
                InstanceGroupMembership,
                InstanceGroup.id == InstanceGroupMembership.group_id,
            )
            .where(InstanceGroupMembership.instance_id == instance_id)
            .order_by(InstanceGroup.name)
        )

        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())
