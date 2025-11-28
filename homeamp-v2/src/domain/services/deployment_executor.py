"""HomeAMP V2.0 - Deployment executor for file operations and rollback."""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from homeamp_v2.core.exceptions import DeploymentError
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class DeploymentExecutor:
    """Executor for performing deployment file operations."""

    def __init__(self, uow: UnitOfWork):
        """Initialize deployment executor.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def install_plugin(
        self, instance_id: int, plugin_file: Path, validate: bool = True
    ) -> Dict:
        """Install a plugin to an instance.

        Args:
            instance_id: Target instance ID
            plugin_file: Path to plugin JAR file
            validate: Whether to validate before installing

        Returns:
            Installation result dictionary

        Raises:
            DeploymentError: If installation fails
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise DeploymentError(f"Instance {instance_id} not found")

            if not plugin_file.exists():
                raise DeploymentError(f"Plugin file not found: {plugin_file}")

            if not plugin_file.suffix == ".jar":
                raise DeploymentError(f"Invalid plugin file type: {plugin_file.suffix}")

            logger.info(f"Installing plugin {plugin_file.name} to {instance.name}")

            # Target plugins directory
            plugins_dir = Path(instance.base_path) / "plugins"
            plugins_dir.mkdir(exist_ok=True)

            target_path = plugins_dir / plugin_file.name

            # Check if plugin already exists
            if target_path.exists():
                logger.warning(f"Plugin {plugin_file.name} already exists, creating backup")
                backup_path = target_path.with_suffix(".jar.backup")
                shutil.copy2(target_path, backup_path)

            # Copy plugin
            shutil.copy2(plugin_file, target_path)

            result = {
                "success": True,
                "instance_id": instance_id,
                "instance_name": instance.name,
                "plugin_file": plugin_file.name,
                "target_path": str(target_path),
                "file_size": target_path.stat().st_size,
                "installed_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Plugin {plugin_file.name} installed successfully")
            return result

        except Exception as e:
            logger.error(f"Plugin installation failed: {e}", exc_info=True)
            raise DeploymentError(f"Plugin installation failed: {e}") from e

    def remove_plugin(self, instance_id: int, plugin_name: str, create_backup: bool = True) -> Dict:
        """Remove a plugin from an instance.

        Args:
            instance_id: Target instance ID
            plugin_name: Plugin JAR filename
            create_backup: Whether to backup before removal

        Returns:
            Removal result dictionary

        Raises:
            DeploymentError: If removal fails
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise DeploymentError(f"Instance {instance_id} not found")

            logger.info(f"Removing plugin {plugin_name} from {instance.name}")

            plugins_dir = Path(instance.base_path) / "plugins"
            plugin_path = plugins_dir / plugin_name

            if not plugin_path.exists():
                raise DeploymentError(f"Plugin not found: {plugin_name}")

            # Create backup if requested
            if create_backup:
                backup_path = plugin_path.with_suffix(".jar.removed")
                shutil.move(plugin_path, backup_path)
                logger.info(f"Plugin backed up to: {backup_path.name}")
            else:
                plugin_path.unlink()
                logger.info(f"Plugin deleted: {plugin_name}")

            result = {
                "success": True,
                "instance_id": instance_id,
                "instance_name": instance.name,
                "plugin_name": plugin_name,
                "backed_up": create_backup,
                "removed_at": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as e:
            logger.error(f"Plugin removal failed: {e}", exc_info=True)
            raise DeploymentError(f"Plugin removal failed: {e}") from e

    def update_plugin(
        self, instance_id: int, plugin_name: str, new_plugin_file: Path
    ) -> Dict:
        """Update a plugin on an instance.

        Args:
            instance_id: Target instance ID
            plugin_name: Current plugin JAR filename
            new_plugin_file: Path to new plugin JAR

        Returns:
            Update result dictionary

        Raises:
            DeploymentError: If update fails
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise DeploymentError(f"Instance {instance_id} not found")

            logger.info(f"Updating plugin {plugin_name} on {instance.name}")

            plugins_dir = Path(instance.base_path) / "plugins"
            current_plugin = plugins_dir / plugin_name
            new_plugin = plugins_dir / new_plugin_file.name

            if not current_plugin.exists():
                raise DeploymentError(f"Current plugin not found: {plugin_name}")

            if not new_plugin_file.exists():
                raise DeploymentError(f"New plugin file not found: {new_plugin_file}")

            # Backup current version
            backup_path = current_plugin.with_suffix(f".jar.backup.{int(datetime.utcnow().timestamp())}")
            shutil.copy2(current_plugin, backup_path)

            # Remove current
            current_plugin.unlink()

            # Install new
            shutil.copy2(new_plugin_file, new_plugin)

            result = {
                "success": True,
                "instance_id": instance_id,
                "instance_name": instance.name,
                "old_plugin": plugin_name,
                "new_plugin": new_plugin_file.name,
                "backup_path": str(backup_path),
                "updated_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Plugin updated: {plugin_name} → {new_plugin_file.name}")
            return result

        except Exception as e:
            logger.error(f"Plugin update failed: {e}", exc_info=True)
            raise DeploymentError(f"Plugin update failed: {e}") from e

    def deploy_config(
        self, instance_id: int, plugin_name: str, config_file: str, config_data: Dict
    ) -> Dict:
        """Deploy configuration changes to an instance.

        Args:
            instance_id: Target instance ID
            plugin_name: Plugin name
            config_file: Config filename
            config_data: Configuration data to write

        Returns:
            Deployment result dictionary

        Raises:
            DeploymentError: If deployment fails
        """
        try:
            import yaml

            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise DeploymentError(f"Instance {instance_id} not found")

            logger.info(f"Deploying config {config_file} for {plugin_name} on {instance.name}")

            # Determine config path
            if plugin_name == "server":
                config_path = Path(instance.base_path) / config_file
            else:
                config_path = Path(instance.base_path) / "plugins" / plugin_name / config_file

            # Create backup of existing config
            if config_path.exists():
                backup_path = config_path.with_suffix(f"{config_path.suffix}.backup")
                shutil.copy2(config_path, backup_path)
                logger.info(f"Config backed up to: {backup_path.name}")

            # Ensure parent directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write new config
            if config_file.endswith((".yml", ".yaml")):
                with open(config_path, "w", encoding="utf-8") as f:
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            elif config_file.endswith(".json"):
                import json
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=2)
            elif config_file.endswith(".properties"):
                with open(config_path, "w", encoding="utf-8") as f:
                    for key, value in config_data.items():
                        f.write(f"{key}={value}\n")
            else:
                raise DeploymentError(f"Unsupported config format: {config_file}")

            result = {
                "success": True,
                "instance_id": instance_id,
                "instance_name": instance.name,
                "plugin_name": plugin_name,
                "config_file": config_file,
                "config_path": str(config_path),
                "deployed_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Config deployed: {config_file}")
            return result

        except Exception as e:
            logger.error(f"Config deployment failed: {e}", exc_info=True)
            raise DeploymentError(f"Config deployment failed: {e}") from e

    def rollback_deployment(self, deployment_id: int) -> Dict:
        """Rollback a deployment to previous state.

        Args:
            deployment_id: Deployment ID to rollback

        Returns:
            Rollback result dictionary

        Raises:
            DeploymentError: If rollback fails
        """
        try:
            # Get deployment history from database
            from homeamp_v2.data.models.advanced import Backup
            from homeamp_v2.data.models.deployment import DeploymentHistory
            from sqlalchemy import select
            
            stmt = select(DeploymentHistory).where(
                DeploymentHistory.queue_id == deployment_id
            ).order_by(DeploymentHistory.completed_at.desc()).limit(1)
            
            result = self.uow.session.execute(stmt)
            history = result.scalar_one_or_none()
            
            if not history:
                raise DeploymentError(f"No history found for deployment {deployment_id}")
            
            # Find backup created before this deployment
            backup_stmt = select(Backup).where(
                Backup.instance_id == history.instance_id,
                Backup.created_at < history.started_at
            ).order_by(Backup.created_at.desc()).limit(1)
            
            backup_result = self.uow.session.execute(backup_stmt)
            backup = backup_result.scalar_one_or_none()
            
            if not backup:
                raise DeploymentError(f"No backup found for rollback")
            
            # Restore from backup files
            from homeamp_v2.domain.services.backup_service import BackupManager
            backup_service = BackupManager(self.uow)
            
            restore_result = backup_service.restore_backup(backup.id)
            
            logger.info(f"Rolling back deployment {deployment_id}")

            result = {
                "success": restore_result["success"],
                "deployment_id": deployment_id,
                "backup_id": backup.id,
                "files_restored": restore_result["files_restored"],
                "rolled_back_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Deployment {deployment_id} rolled back successfully")
            return result

        except Exception as e:
            logger.error(f"Deployment rollback failed: {e}", exc_info=True)
            raise DeploymentError(f"Deployment rollback failed: {e}") from e

    def cleanup_backups(self, instance_id: int, keep_count: int = 5) -> Dict:
        """Clean up old deployment backups.

        Args:
            instance_id: Instance ID
            keep_count: Number of backups to keep per file

        Returns:
            Cleanup result dictionary
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise DeploymentError(f"Instance {instance_id} not found")

            logger.info(f"Cleaning up deployment backups for {instance.name}")

            plugins_dir = Path(instance.base_path) / "plugins"
            deleted_count = 0

            # Find all backup files
            backup_files = list(plugins_dir.glob("*.backup*"))

            # Group by original file
            backup_groups: Dict[str, List[Path]] = {}
            for backup in backup_files:
                # Extract original filename
                original = backup.name.split(".backup")[0]
                if original not in backup_groups:
                    backup_groups[original] = []
                backup_groups[original].append(backup)

            # Keep only newest N backups per file
            for original, backups in backup_groups.items():
                sorted_backups = sorted(backups, key=lambda p: p.stat().st_mtime, reverse=True)
                to_delete = sorted_backups[keep_count:]

                for backup in to_delete:
                    backup.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old backup: {backup.name}")

            result = {
                "success": True,
                "instance_id": instance_id,
                "instance_name": instance.name,
                "deleted_count": deleted_count,
                "keep_count": keep_count,
            }

            logger.info(f"Cleanup complete: {deleted_count} old backups removed")
            return result

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}", exc_info=True)
            raise DeploymentError(f"Backup cleanup failed: {e}") from e
