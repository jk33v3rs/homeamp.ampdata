"""HomeAMP V2.0 - Backup manager for creating and restoring backups."""

import hashlib
import json
import logging
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from homeamp_v2.core.exceptions import BackupError
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class BackupManager:
    """Manager for creating and restoring instance backups."""

    def __init__(self, uow: UnitOfWork, backup_root: str):
        """Initialize backup manager.

        Args:
            uow: Unit of Work for database access
            backup_root: Root directory for storing backups
        """
        self.uow = uow
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def create_backup(
        self,
        instance_id: int,
        backup_type: str = "full",
        compression: str = "gzip",
    ) -> Dict:
        """Create a backup of an instance.

        Args:
            instance_id: Instance ID to backup
            backup_type: Backup type (full, incremental, config_only)
            compression: Compression method (gzip, bzip2, none)

        Returns:
            Backup information dictionary

        Raises:
            BackupError: If backup creation fails
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise BackupError(f"Instance {instance_id} not found")

            logger.info(f"Creating {backup_type} backup for instance: {instance.name}")

            # Create backup directory
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.backup_root / instance.name / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Determine what to backup
            if backup_type == "full":
                paths_to_backup = self._get_full_backup_paths(instance)
            elif backup_type == "config_only":
                paths_to_backup = self._get_config_backup_paths(instance)
            elif backup_type == "incremental":
                paths_to_backup = self._get_incremental_backup_paths(instance)
            else:
                raise BackupError(f"Unknown backup type: {backup_type}")

            # Create archive
            archive_name = f"{instance.name}_{backup_type}_{timestamp}.tar"
            if compression == "gzip":
                archive_name += ".gz"
                mode = "w:gz"
            elif compression == "bzip2":
                archive_name += ".bz2"
                mode = "w:bz2"
            else:
                mode = "w"

            archive_path = backup_dir / archive_name

            with tarfile.open(archive_path, mode) as tar:
                for path in paths_to_backup:
                    if path.exists():
                        arcname = path.relative_to(Path(instance.base_path))
                        tar.add(path, arcname=arcname)
                        logger.debug(f"Added to backup: {arcname}")

            # Calculate file hash
            file_hash = self._calculate_file_hash(archive_path)
            file_size = archive_path.stat().st_size

            # Create backup metadata
            metadata = {
                "instance_id": instance_id,
                "instance_name": instance.name,
                "backup_type": backup_type,
                "compression": compression,
                "file_path": str(archive_path),
                "file_size": file_size,
                "file_hash": file_hash,
                "created_at": datetime.utcnow().isoformat(),
                "paths_backed_up": [str(p) for p in paths_to_backup],
            }

            # Save metadata
            metadata_path = backup_dir / f"{archive_name}.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            # Record in database
            from homeamp_v2.data.models.advanced import Backup
            
            backup_record = Backup(
                instance_id=instance_id,
                backup_type=backup_type,
                file_path=str(archive_path),
                file_size=file_size,
                file_hash=file_hash,
                created_by=metadata.get("created_by", "system"),
                created_at=datetime.utcnow()
            )
            self.uow.session.add(backup_record)
            
            logger.info(
                f"Backup created: {archive_name} ({self._format_size(file_size)}, hash: {file_hash[:8]}...)"
            )

            self.uow.commit()
            return metadata

        except Exception as e:
            self.uow.rollback()
            logger.error(f"Backup creation failed: {e}", exc_info=True)
            raise BackupError(f"Backup creation failed: {e}") from e

    def restore_backup(self, backup_id: int, target_path: Optional[str] = None) -> Dict:
        """Restore a backup.

        Args:
            backup_id: Backup ID to restore
            target_path: Optional custom target path (None = original location)

        Returns:
            Restore result dictionary

        Raises:
            BackupError: If restore fails
        """
        try:
            # Get backup from database
            from homeamp_v2.data.models.advanced import Backup
            from sqlalchemy import select
            
            stmt = select(Backup).where(Backup.id == backup_id)
            result = self.uow.session.execute(stmt)
            backup = result.scalar_one_or_none()
            
            if not backup:
                raise BackupError(f"Backup {backup_id} not found")
            
            logger.info(f"Restoring backup {backup_id}")

            # Verify backup file exists
            backup_path = Path(backup.file_path)
            if not backup_path.exists():
                raise BackupError(f"Backup file not found: {backup_path}")
            
            # Verify integrity
            logger.debug("Verifying backup integrity...")
            actual_hash = self._calculate_file_hash(backup_path)
            if actual_hash != backup.file_hash:
                raise BackupError(f"Backup integrity check failed: hash mismatch")
            
            # Determine target path
            if target_path is None:
                instance = self.uow.instances.get_by_id(backup.instance_id)
                if not instance:
                    raise BackupError(f"Instance {backup.instance_id} not found")
                target_path = instance.base_path
            
            target = Path(target_path)
            target.mkdir(parents=True, exist_ok=True)
            
            # Extract archive
            logger.info(f"Extracting backup to {target}")
            shutil.unpack_archive(backup_path, target)
            
            # Count restored files
            files_restored = sum(1 for _ in target.rglob("*") if _.is_file())

            result = {
                "backup_id": backup_id,
                "success": True,
                "files_restored": files_restored,
                "target_path": str(target),
                "backup_hash": backup.file_hash,
            }

            logger.info(f"Backup {backup_id} restored successfully: {files_restored} files")
            return result

        except Exception as e:
            logger.error(f"Backup restore failed: {e}", exc_info=True)
            raise BackupError(f"Backup restore failed: {e}") from e

    def list_backups(self, instance_id: Optional[int] = None) -> List[Dict]:
        """List available backups.

        Args:
            instance_id: Optional instance ID filter

        Returns:
            List of backup information dictionaries
        """
        backups = []

        try:
            for instance_dir in self.backup_root.iterdir():
                if not instance_dir.is_dir():
                    continue

                for backup_dir in instance_dir.iterdir():
                    if not backup_dir.is_dir():
                        continue

                    # Find metadata files
                    for metadata_file in backup_dir.glob("*.json"):
                        try:
                            with open(metadata_file, "r", encoding="utf-8") as f:
                                metadata = json.load(f)

                            # Filter by instance if specified
                            if instance_id and metadata.get("instance_id") != instance_id:
                                continue

                            backups.append(metadata)

                        except Exception as e:
                            logger.warning(f"Failed to read backup metadata {metadata_file}: {e}")

        except Exception as e:
            logger.error(f"Failed to list backups: {e}")

        return sorted(backups, key=lambda x: x.get("created_at", ""), reverse=True)

    def cleanup_old_backups(self, retention_days: int = 30) -> Dict:
        """Clean up old backups based on retention policy.

        Args:
            retention_days: Number of days to keep backups

        Returns:
            Cleanup result dictionary
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=retention_days)
            logger.info(f"Cleaning up backups older than {retention_days} days")

            deleted_count = 0
            deleted_size = 0

            for instance_dir in self.backup_root.iterdir():
                if not instance_dir.is_dir():
                    continue

                for backup_dir in instance_dir.iterdir():
                    if not backup_dir.is_dir():
                        continue

                    # Check backup age
                    try:
                        backup_time = datetime.strptime(backup_dir.name, "%Y%m%d_%H%M%S")
                        if backup_time < cutoff:
                            # Calculate size
                            dir_size = sum(f.stat().st_size for f in backup_dir.rglob("*") if f.is_file())

                            # Delete backup
                            shutil.rmtree(backup_dir)
                            deleted_count += 1
                            deleted_size += dir_size

                            logger.info(f"Deleted old backup: {backup_dir.name}")

                    except Exception as e:
                        logger.warning(f"Failed to process backup {backup_dir}: {e}")

            result = {
                "deleted_count": deleted_count,
                "deleted_size": deleted_size,
                "retention_days": retention_days,
            }

            logger.info(
                f"Cleanup complete: {deleted_count} backups deleted ({self._format_size(deleted_size)})"
            )
            return result

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            raise BackupError(f"Backup cleanup failed: {e}") from e

    def _get_full_backup_paths(self, instance) -> List[Path]:
        """Get paths for full backup."""
        base = Path(instance.base_path)
        paths = []

        # Important directories
        important_dirs = [
            "plugins",
            "world",
            "world_nether",
            "world_the_end",
            "config",
            "mods",
            "datapacks",
        ]

        for dir_name in important_dirs:
            dir_path = base / dir_name
            if dir_path.exists():
                paths.append(dir_path)

        # Important files
        important_files = [
            "server.properties",
            "bukkit.yml",
            "spigot.yml",
            "paper.yml",
            "pufferfish.yml",
            "purpur.yml",
            "ops.json",
            "whitelist.json",
        ]

        for file_name in important_files:
            file_path = base / file_name
            if file_path.exists():
                paths.append(file_path)

        return paths

    def _get_config_backup_paths(self, instance) -> List[Path]:
        """Get paths for config-only backup."""
        base = Path(instance.base_path)
        paths = []

        # Plugin configs
        plugins_dir = base / "plugins"
        if plugins_dir.exists():
            # Get all config files, skip JAR files
            for config_file in plugins_dir.rglob("*"):
                if config_file.is_file() and config_file.suffix in [".yml", ".yaml", ".json", ".conf", ".properties"]:
                    paths.append(config_file)

        # Server configs
        config_files = [
            "server.properties",
            "bukkit.yml",
            "spigot.yml",
            "paper.yml",
            "pufferfish.yml",
            "purpur.yml",
        ]

        for file_name in config_files:
            file_path = base / file_name
            if file_path.exists():
                paths.append(file_path)

        return paths

    def _get_incremental_backup_paths(self, instance) -> List[Path]:
        """Get paths for incremental backup (modified files only)."""
        from homeamp_v2.data.models.advanced import Backup
        from sqlalchemy import select
        
        base = Path(instance.base_path)
        paths = []
        
        # Get last backup timestamp
        stmt = select(Backup).where(
            Backup.instance_id == instance.id
        ).order_by(Backup.created_at.desc()).limit(1)
        
        result = self.uow.session.execute(stmt)
        last_backup = result.scalar_one_or_none()
        
        if not last_backup:
            # No previous backup, do full backup
            logger.info("No previous backup found, performing full backup")
            return self._get_full_backup_paths(instance)
        
        last_backup_time = last_backup.created_at.timestamp()
        
        # Find files modified since last backup
        important_dirs = [
            "plugins",
            "world",
            "config",
        ]
        
        for dir_name in important_dirs:
            dir_path = base / dir_name
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if file_path.is_file():
                        if file_path.stat().st_mtime > last_backup_time:
                            paths.append(file_path)
        
        # Always include important config files
        config_files = [
            "server.properties",
            "bukkit.yml",
            "spigot.yml",
            "paper.yml",
        ]
        
        for file_name in config_files:
            file_path = base / file_name
            if file_path.exists() and file_path.stat().st_mtime > last_backup_time:
                if file_path not in paths:
                    paths.append(file_path)
        
        logger.info(f"Incremental backup: {len(paths)} files modified since last backup")
        return paths

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        size: float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
