"""HomeAMP V2.0 - Validation tools for pre/post deployment checks."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from homeamp_v2.core.exceptions import ValidationError
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class DeploymentValidator:
    """Validator for pre and post deployment checks."""

    def __init__(self, uow: UnitOfWork):
        """Initialize deployment validator.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def validate_pre_deployment(self, instance_id: int, deployment_type: str) -> Dict:
        """Run pre-deployment validation checks.

        Args:
            instance_id: Instance ID
            deployment_type: Type of deployment

        Returns:
            Validation result dictionary

        Raises:
            ValidationError: If validation fails
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise ValidationError(f"Instance {instance_id} not found")

            logger.info(f"Running pre-deployment validation for {instance.name}")

            checks = []

            # Check instance path exists
            checks.append(self._check_instance_path(instance))

            # Check disk space
            checks.append(self._check_disk_space(instance))

            # Check instance is stopped (if required)
            if deployment_type in ["update", "config"]:
                checks.append(self._check_instance_stopped(instance))

            # Check plugin conflicts
            if deployment_type in ["install", "update"]:
                checks.append(self._check_plugin_conflicts(instance))

            # Check permissions
            checks.append(self._check_file_permissions(instance))

            # Determine overall status
            passed = all(check["passed"] for check in checks)
            critical_failures = [c for c in checks if not c["passed"] and c.get("severity") == "critical"]

            result = {
                "instance_id": instance_id,
                "instance_name": instance.name,
                "deployment_type": deployment_type,
                "passed": passed,
                "checks": checks,
                "critical_failures": len(critical_failures),
                "warnings": len([c for c in checks if not c["passed"] and c.get("severity") == "warning"]),
            }

            if passed:
                logger.info(f"Pre-deployment validation passed for {instance.name}")
            else:
                logger.warning(
                    f"Pre-deployment validation failed for {instance.name}: "
                    f"{result['critical_failures']} critical, {result['warnings']} warnings"
                )

            return result

        except Exception as e:
            logger.error(f"Pre-deployment validation error: {e}", exc_info=True)
            raise ValidationError(f"Pre-deployment validation failed: {e}") from e

    def validate_post_deployment(self, instance_id: int, deployment_id: int) -> Dict:
        """Run post-deployment validation checks.

        Args:
            instance_id: Instance ID
            deployment_id: Deployment ID

        Returns:
            Validation result dictionary

        Raises:
            ValidationError: If validation fails
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise ValidationError(f"Instance {instance_id} not found")

            logger.info(f"Running post-deployment validation for {instance.name}")

            checks = []

            # Check files were deployed
            checks.append(self._check_deployment_files(instance, deployment_id))

            # Check file integrity
            checks.append(self._check_file_integrity(instance))

            # Check configuration syntax
            checks.append(self._check_config_syntax(instance))

            # Check for errors in logs
            checks.append(self._check_server_logs(instance))

            # Determine overall status
            passed = all(check["passed"] for check in checks)
            critical_failures = [c for c in checks if not c["passed"] and c.get("severity") == "critical"]

            result = {
                "instance_id": instance_id,
                "instance_name": instance.name,
                "deployment_id": deployment_id,
                "passed": passed,
                "checks": checks,
                "critical_failures": len(critical_failures),
                "warnings": len([c for c in checks if not c["passed"] and c.get("severity") == "warning"]),
            }

            if passed:
                logger.info(f"Post-deployment validation passed for {instance.name}")
            else:
                logger.warning(
                    f"Post-deployment validation failed for {instance.name}: "
                    f"{result['critical_failures']} critical, {result['warnings']} warnings"
                )

            return result

        except Exception as e:
            logger.error(f"Post-deployment validation error: {e}", exc_info=True)
            raise ValidationError(f"Post-deployment validation failed: {e}") from e

    def _check_instance_path(self, instance) -> Dict:
        """Check if instance path exists and is accessible."""
        base_path = Path(instance.base_path)
        passed = base_path.exists() and base_path.is_dir()

        return {
            "check": "instance_path",
            "passed": passed,
            "severity": "critical",
            "message": f"Instance path exists: {base_path}" if passed else f"Instance path not found: {base_path}",
        }

    def _check_disk_space(self, instance, min_gb: float = 1.0) -> Dict:
        """Check if sufficient disk space is available."""
        import shutil

        base_path = Path(instance.base_path)
        
        try:
            stats = shutil.disk_usage(base_path)
            free_gb = stats.free / (1024 ** 3)
            passed = free_gb >= min_gb

            return {
                "check": "disk_space",
                "passed": passed,
                "severity": "critical" if not passed else "info",
                "message": f"Free disk space: {free_gb:.2f} GB" if passed else f"Low disk space: {free_gb:.2f} GB (minimum: {min_gb} GB)",
                "details": {"free_gb": free_gb, "required_gb": min_gb},
            }
        except Exception as e:
            return {
                "check": "disk_space",
                "passed": False,
                "severity": "warning",
                "message": f"Failed to check disk space: {e}",
            }

    def _check_instance_stopped(self, instance) -> Dict:
        """Check if instance is stopped (safe for deployment)."""
        import psutil
        
        passed = True
        
        try:
            # Check for Java processes running from instance directory
            base_path = str(instance.base_path)
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] and 'java' in proc.info['name'].lower():
                        cmdline = proc.info['cmdline']
                        if cmdline and any(base_path in arg for arg in cmdline):
                            passed = False
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        
        except Exception as e:
            logger.warning(f"Failed to check instance status: {e}")
            passed = True  # Assume stopped if check fails

        return {
            "check": "instance_stopped",
            "passed": passed,
            "severity": "critical",
            "message": "Instance is stopped" if passed else "Instance is running - must be stopped for deployment",
        }

    def _check_plugin_conflicts(self, instance) -> Dict:
        """Check for potential plugin conflicts."""
        from homeamp_v2.data.models.plugin import InstancePlugin
        from sqlalchemy import select
        
        conflicts = []
        
        try:
            # Get all plugins for this instance
            stmt = select(InstancePlugin).where(InstancePlugin.instance_id == instance.id)
            result = self.uow.session.execute(stmt)
            instance_plugins = result.scalars().all()
            
            # Check for duplicate plugins (same name, different JAR)
            plugin_names = {}
            for inst_plugin in instance_plugins:
                plugin = self.uow.plugins.get_by_id(inst_plugin.plugin_id)
                if plugin:
                    if plugin.name in plugin_names:
                        conflicts.append(f"Duplicate plugin: {plugin.name}")
                    else:
                        plugin_names[plugin.name] = plugin
            
            # Check for known incompatible plugin combinations
            # Query PluginCompatibility table if it exists
            try:
                from homeamp_v2.data.models.plugin import PluginCompatibility
                from sqlalchemy import or_, select
                
                plugin_ids = [p.id for p in plugin_names.values()]
                
                # Check pairwise incompatibilities
                stmt = select(PluginCompatibility).where(
                    or_(
                        PluginCompatibility.plugin_a_id.in_(plugin_ids),
                        PluginCompatibility.plugin_b_id.in_(plugin_ids)
                    ),
                    PluginCompatibility.compatible == False
                )
                result = self.uow.session.execute(stmt)
                incompatibilities = result.scalars().all()
                
                for incomp in incompatibilities:
                    if incomp.plugin_a_id in plugin_ids and incomp.plugin_b_id in plugin_ids:
                        plugin_a = self.uow.plugins.get_by_id(incomp.plugin_a_id)
                        plugin_b = self.uow.plugins.get_by_id(incomp.plugin_b_id)
                        if plugin_a and plugin_b:
                            reason = f" ({incomp.reason})" if incomp.reason else ""
                            conflicts.append(f"Incompatible: {plugin_a.name} + {plugin_b.name}{reason}")
            
            except ImportError:
                # PluginCompatibility model doesn't exist yet
                logger.debug("PluginCompatibility model not available")
            except Exception as compat_error:
                logger.warning(f"Failed to check plugin compatibility: {compat_error}")
            
        except Exception as e:
            logger.warning(f"Failed to check plugin conflicts: {e}")
        
        passed = len(conflicts) == 0

        return {
            "check": "plugin_conflicts",
            "passed": passed,
            "severity": "warning",
            "message": "No plugin conflicts detected" if passed else f"Conflicts found: {', '.join(conflicts)}",
            "details": {"conflicts": conflicts} if conflicts else {},
        }

    def _check_file_permissions(self, instance) -> Dict:
        """Check if files have correct permissions."""
        base_path = Path(instance.base_path)
        
        try:
            # Check if we can read/write
            test_file = base_path / ".homeamp_test"
            test_file.touch()
            test_file.unlink()
            passed = True
            message = "File permissions OK"
        except Exception as e:
            passed = False
            message = f"Permission error: {e}"

        return {
            "check": "file_permissions",
            "passed": passed,
            "severity": "critical",
            "message": message,
        }

    def _check_deployment_files(self, instance, deployment_id: int) -> Dict:
        """Check if deployment files exist."""
        from homeamp_v2.data.models.deployment import DeploymentQueue
        from sqlalchemy import select
        
        try:
            # Get deployment details
            stmt = select(DeploymentQueue).where(DeploymentQueue.id == deployment_id)
            result = self.uow.session.execute(stmt)
            deployment = result.scalar_one_or_none()
            
            if not deployment:
                return {
                    "check": "deployment_files",
                    "passed": False,
                    "severity": "critical",
                    "message": f"Deployment {deployment_id} not found",
                }
            
            # Verify files based on deployment type
            passed = True
            missing_files = []
            
            if deployment.deployment_type == "plugin":
                plugin = self.uow.plugins.get_by_id(deployment.entity_id)
                if plugin:
                    plugin_path = Path(instance.base_path) / "plugins" / plugin.jar_name
                    if deployment.action in ["update", "remove"] and not plugin_path.exists():
                        passed = False
                        missing_files.append(str(plugin_path))
            
            elif deployment.deployment_type == "datapack":
                # Check datapack files
                from homeamp_v2.data.models.datapack import Datapack, InstanceDatapack
                from sqlalchemy import select
                
                datapack = self.uow.datapacks.get_by_id(deployment.entity_id)
                if datapack:
                    # Check if datapack exists in world's datapacks directory
                    # Datapacks are typically in world/datapacks/
                    stmt = select(InstanceDatapack).where(
                        InstanceDatapack.instance_id == deployment.instance_id,
                        InstanceDatapack.datapack_id == deployment.entity_id
                    )
                    result = self.uow.session.execute(stmt)
                    inst_datapack = result.scalar_one_or_none()
                    
                    if inst_datapack and inst_datapack.world_name:
                        datapack_path = Path(instance.base_path) / inst_datapack.world_name / "datapacks" / datapack.name
                        
                        if deployment.action in ["update", "remove"]:
                            if not datapack_path.exists():
                                passed = False
                                missing_files.append(str(datapack_path))
            
            return {
                "check": "deployment_files",
                "passed": passed,
                "severity": "critical",
                "message": "All deployment files present" if passed else f"Missing files: {', '.join(missing_files)}",
                "details": {"missing_files": missing_files} if missing_files else {},
            }
        
        except Exception as e:
            return {
                "check": "deployment_files",
                "passed": False,
                "severity": "critical",
                "message": f"Failed to check deployment files: {e}",
            }

    def _check_file_integrity(self, instance) -> Dict:
        """Check integrity of deployed files."""
        import hashlib

        from homeamp_v2.data.models.plugin import InstancePlugin
        from sqlalchemy import select
        
        integrity_issues = []
        
        try:
            # Get plugins for this instance
            stmt = select(InstancePlugin).where(InstancePlugin.instance_id == instance.id)
            result = self.uow.session.execute(stmt)
            instance_plugins = result.scalars().all()
            
            for inst_plugin in instance_plugins:
                plugin = self.uow.plugins.get_by_id(inst_plugin.plugin_id)
                if not plugin:
                    continue
                
                plugin_path = Path(instance.base_path) / "plugins" / plugin.jar_name
                
                if not plugin_path.exists():
                    integrity_issues.append(f"{plugin.name}: file not found")
                    continue
                
                # Check file size
                actual_size = plugin_path.stat().st_size
                if actual_size != inst_plugin.jar_size:
                    integrity_issues.append(
                        f"{plugin.name}: size mismatch (expected {inst_plugin.jar_size}, got {actual_size})"
                    )
                
                # Check file hash (SHA-256)
                sha256 = hashlib.sha256()
                with open(plugin_path, "rb") as f:
                    for chunk in iter(lambda: f.read(8192), b""):
                        sha256.update(chunk)
                actual_hash = sha256.hexdigest()
                
                if actual_hash != inst_plugin.jar_hash:
                    integrity_issues.append(
                        f"{plugin.name}: hash mismatch (file may be corrupted or modified)"
                    )
        
        except Exception as e:
            logger.warning(f"Failed to check file integrity: {e}")
        
        passed = len(integrity_issues) == 0

        return {
            "check": "file_integrity",
            "passed": passed,
            "severity": "critical",
            "message": "File integrity verified" if passed else f"Integrity issues: {len(integrity_issues)}",
            "details": {"issues": integrity_issues} if integrity_issues else {},
        }

    def _check_config_syntax(self, instance) -> Dict:
        """Check configuration file syntax."""
        import yaml

        errors = []
        plugins_dir = Path(instance.base_path) / "plugins"

        if plugins_dir.exists():
            for config_file in plugins_dir.rglob("*.yml"):
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        yaml.safe_load(f)
                except Exception as e:
                    errors.append(f"{config_file.name}: {e}")

        passed = len(errors) == 0

        return {
            "check": "config_syntax",
            "passed": passed,
            "severity": "warning" if not passed else "info",
            "message": "All configs valid" if passed else f"{len(errors)} config errors found",
            "details": {"errors": errors} if errors else {},
        }

    def _check_server_logs(self, instance, max_errors: int = 10) -> Dict:
        """Check server logs for errors."""
        logs_dir = Path(instance.base_path) / "logs"
        latest_log = logs_dir / "latest.log"

        errors = []

        if latest_log.exists():
            try:
                with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-100:]  # Check last 100 lines

                for line in lines:
                    if any(keyword in line.lower() for keyword in ["error", "exception", "fatal"]):
                        errors.append(line.strip())
                        if len(errors) >= max_errors:
                            break

            except Exception as e:
                logger.warning(f"Failed to read server log: {e}")

        passed = len(errors) == 0

        return {
            "check": "server_logs",
            "passed": passed,
            "severity": "warning",
            "message": "No errors in logs" if passed else f"{len(errors)} errors found in logs",
            "details": {"errors": errors[:5]} if errors else {},  # Show first 5
        }
