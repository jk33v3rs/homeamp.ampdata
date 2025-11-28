"""HomeAMP V2.0 - Datapack management service."""

import logging
from typing import Dict, List, Optional

from homeamp_v2.core.exceptions import NotFoundError, ValidationError
from homeamp_v2.data.models.datapack import Datapack, DatapackVersion, InstanceDatapack
from homeamp_v2.data.unit_of_work import UnitOfWork
from sqlalchemy import select

logger = logging.getLogger(__name__)


class DatapackService:
    """Service for managing datapacks."""

    def __init__(self, uow: UnitOfWork):
        """Initialize datapack service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def get_all_datapacks(self) -> List[Datapack]:
        """Get all datapacks.

        Returns:
            List of datapacks
        """
        stmt = select(Datapack).order_by(Datapack.name)
        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())

    def get_datapack(self, datapack_id: int) -> Optional[Datapack]:
        """Get datapack by ID.

        Args:
            datapack_id: Datapack ID

        Returns:
            Datapack or None
        """
        stmt = select(Datapack).where(Datapack.id == datapack_id)
        result = self.uow.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_datapack_by_name(self, name: str) -> Optional[Datapack]:
        """Get datapack by name.

        Args:
            name: Datapack name

        Returns:
            Datapack or None
        """
        stmt = select(Datapack).where(Datapack.name == name)
        result = self.uow.session.execute(stmt)
        return result.scalar_one_or_none()

    def get_instance_datapacks(self, instance_id: int) -> List[Dict]:
        """Get datapacks for instance.

        Args:
            instance_id: Instance ID

        Returns:
            List of instance datapacks with details
        """
        stmt = (
            select(InstanceDatapack, Datapack)
            .join(Datapack, InstanceDatapack.datapack_id == Datapack.id)
            .where(InstanceDatapack.instance_id == instance_id)
        )

        result = self.uow.session.execute(stmt)
        datapacks = []

        for instance_dp, datapack in result:
            datapacks.append(
                {
                    "id": datapack.id,
                    "name": datapack.name,
                    "description": datapack.description,
                    "version": instance_dp.version,
                    "enabled": instance_dp.enabled,
                    "load_order": instance_dp.load_order,
                }
            )

        return datapacks

    def assign_datapack_to_instance(
        self,
        datapack_id: int,
        instance_id: int,
        version: str,
        enabled: bool = True,
        load_order: int = 0,
    ) -> InstanceDatapack:
        """Assign datapack to instance.

        Args:
            datapack_id: Datapack ID
            instance_id: Instance ID
            version: Datapack version
            enabled: Whether enabled
            load_order: Load order

        Returns:
            Created instance datapack

        Raises:
            NotFoundError: If datapack not found
            ValidationError: If already assigned
        """
        # Check datapack exists
        datapack = self.get_datapack(datapack_id)
        if not datapack:
            raise NotFoundError(f"Datapack {datapack_id} not found")

        # Check if already assigned
        existing_stmt = select(InstanceDatapack).where(
            InstanceDatapack.datapack_id == datapack_id,
            InstanceDatapack.instance_id == instance_id,
        )
        existing = self.uow.session.execute(existing_stmt).scalar_one_or_none()

        if existing:
            raise ValidationError(
                f"Datapack {datapack_id} already assigned to instance {instance_id}"
            )

        instance_datapack = InstanceDatapack(
            datapack_id=datapack_id,
            instance_id=instance_id,
            version=version,
            enabled=enabled,
            load_order=load_order,
        )

        self.uow.session.add(instance_datapack)
        self.uow.session.flush()

        logger.info(
            f"Assigned datapack {datapack_id} to instance {instance_id}"
        )

        return instance_datapack

    def remove_datapack_from_instance(
        self, datapack_id: int, instance_id: int
    ) -> None:
        """Remove datapack from instance.

        Args:
            datapack_id: Datapack ID
            instance_id: Instance ID

        Raises:
            NotFoundError: If assignment not found
        """
        stmt = select(InstanceDatapack).where(
            InstanceDatapack.datapack_id == datapack_id,
            InstanceDatapack.instance_id == instance_id,
        )
        instance_dp = self.uow.session.execute(stmt).scalar_one_or_none()

        if not instance_dp:
            raise NotFoundError(
                f"Datapack {datapack_id} not assigned to instance {instance_id}"
            )

        self.uow.session.delete(instance_dp)
        self.uow.session.flush()

        logger.info(
            f"Removed datapack {datapack_id} from instance {instance_id}"
        )

    def get_datapack_versions(self, datapack_id: int) -> List[DatapackVersion]:
        """Get versions for datapack.

        Args:
            datapack_id: Datapack ID

        Returns:
            List of versions
        """
        stmt = (
            select(DatapackVersion)
            .where(DatapackVersion.datapack_id == datapack_id)
            .order_by(DatapackVersion.released_at.desc())
        )

        result = self.uow.session.execute(stmt)
        return list(result.scalars().all())

    def create_datapack(
        self,
        name: str,
        description: Optional[str] = None,
        source_url: Optional[str] = None,
    ) -> Datapack:
        """Create new datapack.

        Args:
            name: Datapack name
            description: Optional description
            source_url: Optional source URL

        Returns:
            Created datapack

        Raises:
            ValidationError: If datapack already exists
        """
        existing = self.get_datapack_by_name(name)
        if existing:
            raise ValidationError(f"Datapack '{name}' already exists")

        datapack = Datapack(
            name=name,
            description=description,
            source_url=source_url,
        )

        self.uow.session.add(datapack)
        self.uow.session.flush()

        logger.info(f"Created datapack '{name}'")

        return datapack
