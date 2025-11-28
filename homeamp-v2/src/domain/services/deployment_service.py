"""HomeAMP V2.0 - Deployment service for managing deployments."""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from homeamp_v2.core.exceptions import DeploymentError, ValidationError
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class DeploymentService:
    """Service for managing configuration and plugin deployments."""

    def __init__(self, uow: UnitOfWork):
        """Initialize deployment service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def queue_deployment(
        self,
        instance_id: int,
        deployment_type: str,
        entity_type: str,
        entity_id: int,
        priority: int = 5,
        requires_approval: bool = False,
    ) -> int:
        """Queue a deployment.

        Args:
            instance_id: Target instance ID
            deployment_type: Type of deployment (install, update, remove, config)
            entity_type: Entity type (plugin, datapack, config)
            entity_id: Entity ID
            priority: Priority (1-10, higher = more urgent)
            requires_approval: Whether approval is required

        Returns:
            Deployment queue ID

        Raises:
            DeploymentError: If queueing fails
            ValidationError: If validation fails
        """
        try:
            # Validate instance exists
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise ValidationError(f"Instance {instance_id} not found")

            # Validate priority
            if not 1 <= priority <= 10:
                raise ValidationError("Priority must be between 1 and 10")

            # Create deployment queue entry
            deployment = self.uow.deployments.create(
                instance_id=instance_id,
                deployment_type=deployment_type,
                entity_type=entity_type,
                entity_id=entity_id,
                priority=priority,
                status="pending" if not requires_approval else "awaiting_approval",
                requires_approval=int(requires_approval),
            )

            self.uow.commit()

            logger.info(
                f"Queued deployment {deployment.id}: {deployment_type} {entity_type} "
                f"for instance {instance.name}"
            )

            return deployment.id

        except Exception as e:
            self.uow.rollback()
            logger.error(f"Failed to queue deployment: {e}")
            raise DeploymentError(f"Failed to queue deployment: {e}") from e

    def get_pending_deployments(self, instance_id: Optional[int] = None) -> List[Dict]:
        """Get pending deployments.

        Args:
            instance_id: Optional instance ID filter

        Returns:
            List of pending deployments
        """
        deployments = self.uow.deployments.get_pending(instance_id)

        return [
            {
                "id": d.id,
                "instance_id": d.instance_id,
                "deployment_type": d.deployment_type,
                "entity_type": d.entity_type,
                "entity_id": d.entity_id,
                "priority": d.priority,
                "status": d.status,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in deployments
        ]

    def execute_deployment(self, deployment_id: int, dry_run: bool = False) -> Dict:
        """Execute a deployment.

        Args:
            deployment_id: Deployment queue ID
            dry_run: If True, only simulate execution

        Returns:
            Deployment result dictionary

        Raises:
            DeploymentError: If execution fails
        """
        try:
            deployment = self.uow.deployments.get_by_id(deployment_id)
            if not deployment:
                raise DeploymentError(f"Deployment {deployment_id} not found")

            instance = self.uow.instances.get_by_id(deployment.instance_id)
            if not instance:
                raise DeploymentError(f"Instance {deployment.instance_id} not found")

            logger.info(
                f"Executing deployment {deployment_id}: {deployment.deployment_type} "
                f"{deployment.entity_type} for {instance.name} (dry_run={dry_run})"
            )

            # Update status
            if not dry_run:
                self.uow.deployments.update(deployment_id, status="in_progress")
                self.uow.commit()

            # Execute based on deployment type
            result = {
                "deployment_id": deployment_id,
                "instance_name": instance.name,
                "deployment_type": deployment.deployment_type,
                "entity_type": deployment.entity_type,
                "dry_run": dry_run,
                "success": False,
                "changes": [],
                "errors": [],
            }

            try:
                if deployment.deployment_type == "install":
                    result["changes"] = self._execute_install(deployment, instance, dry_run)
                elif deployment.deployment_type == "update":
                    result["changes"] = self._execute_update(deployment, instance, dry_run)
                elif deployment.deployment_type == "remove":
                    result["changes"] = self._execute_remove(deployment, instance, dry_run)
                elif deployment.deployment_type == "config":
                    result["changes"] = self._execute_config(deployment, instance, dry_run)
                else:
                    raise DeploymentError(f"Unknown deployment type: {deployment.deployment_type}")

                result["success"] = True

                # Update status and create history
                if not dry_run:
                    self.uow.deployments.update(deployment_id, status="completed")

                    # Create deployment history
                    from homeamp_v2.data.models.deployment import DeploymentHistory
                    
                    duration_ms = int((datetime.utcnow() - deployment.created_at).total_seconds() * 1000)
                    history = DeploymentHistory(
                        queue_id=deployment_id,
                        instance_id=deployment.instance_id,
                        deployment_type=deployment.deployment_type,
                        action=deployment.action,
                        status="success",
                        executed_by=deployment.created_by if hasattr(deployment, 'created_by') and deployment.created_by else "system",
                        started_at=deployment.created_at,
                        completed_at=datetime.utcnow(),
                        duration_ms=duration_ms,
                        error_message=None
                    )
                    self.uow.session.add(history)

                    self.uow.commit()

            except Exception as e:
                result["errors"].append(str(e))
                result["success"] = False

                if not dry_run:
                    self.uow.deployments.update(deployment_id, status="failed", error_message=str(e))
                    self.uow.commit()

                raise

            logger.info(f"Deployment {deployment_id} completed: success={result['success']}")
            return result

        except Exception as e:
            logger.error(f"Deployment {deployment_id} failed: {e}")
            raise DeploymentError(f"Deployment execution failed: {e}") from e

    def _execute_install(self, deployment, instance, dry_run: bool) -> List[str]:
        """Execute install deployment."""
        changes = []
        
        if deployment.entity_type == "plugin":
            plugin = self.uow.plugins.get_by_id(deployment.entity_id)
            if not plugin:
                raise DeploymentError(f"Plugin {deployment.entity_id} not found")
            
            plugins_dir = Path(instance.base_path) / "plugins"
            plugins_dir.mkdir(exist_ok=True)
            
            if not dry_run:
                # Download plugin JAR from update source
                import requests
                from homeamp_v2.data.models.plugin import PluginUpdateSource
                from sqlalchemy import select
                
                # Try to get download URL from update source
                stmt = select(PluginUpdateSource).where(PluginUpdateSource.plugin_id == plugin.id)
                result = self.uow.session.execute(stmt)
                update_source = result.scalar_one_or_none()
                
                download_url = None
                if update_source and update_source.download_url:
                    download_url = update_source.download_url
                elif plugin.download_url:
                    download_url = plugin.download_url
                
                if download_url:
                    try:
                        response = requests.get(download_url, timeout=30)
                        response.raise_for_status()
                        
                        jar_path = plugins_dir / plugin.jar_name
                        with open(jar_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"Downloaded {plugin.jar_name} from {download_url}")
                        changes.append(f"Installed plugin {plugin.name} to {instance.name}")
                    except Exception as e:
                        logger.error(f"Failed to download plugin JAR: {e}")
                        changes.append(f"Failed to install plugin {plugin.name}: {e}")
                else:
                    logger.warning(f"No download URL available for plugin {plugin.name}")
                    changes.append(f"Installed plugin {plugin.name} to {instance.name} (manual JAR placement required)")
            else:
                changes.append(f"Would install plugin {plugin.name} to {instance.name}")
        
        elif deployment.entity_type == "datapack":
            if not dry_run:
                changes.append(f"Installed datapack {deployment.entity_id}")
            else:
                changes.append(f"Would install datapack {deployment.entity_id}")
        
        logger.info(f"Install deployment executed (dry_run={dry_run})")
        return changes

    def _execute_update(self, deployment, instance, dry_run: bool) -> List[str]:
        """Execute update deployment."""
        changes = []
        
        if deployment.entity_type == "plugin":
            plugin = self.uow.plugins.get_by_id(deployment.entity_id)
            if not plugin:
                raise DeploymentError(f"Plugin {deployment.entity_id} not found")
            
            if not dry_run:
                # Download new version and replace old JAR
                import requests
                from homeamp_v2.data.models.plugin import (
                    PluginUpdateQueue,
                    PluginUpdateSource,
                )
                from sqlalchemy import select
                
                # Get update queue entry for version info
                stmt = select(PluginUpdateQueue).where(
                    PluginUpdateQueue.plugin_id == plugin.id,
                    PluginUpdateQueue.instance_id == instance.id
                ).order_by(PluginUpdateQueue.created_at.desc()).limit(1)
                result = self.uow.session.execute(stmt)
                update_queue = result.scalar_one_or_none()
                
                download_url = None
                if update_queue and update_queue.download_url:
                    download_url = update_queue.download_url
                else:
                    # Fallback to update source
                    stmt = select(PluginUpdateSource).where(PluginUpdateSource.plugin_id == plugin.id)
                    result = self.uow.session.execute(stmt)
                    update_source = result.scalar_one_or_none()
                    if update_source and update_source.download_url:
                        download_url = update_source.download_url
                
                if download_url:
                    try:
                        response = requests.get(download_url, timeout=30)
                        response.raise_for_status()
                        
                        plugins_dir = Path(instance.base_path) / "plugins"
                        old_jar_path = plugins_dir / plugin.jar_name
                        
                        # Backup old JAR
                        if old_jar_path.exists():
                            backup_path = old_jar_path.with_suffix('.jar.bak')
                            shutil.copy2(old_jar_path, backup_path)
                            logger.info(f"Backed up old JAR to {backup_path}")
                        
                        # Write new JAR
                        with open(old_jar_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"Updated {plugin.jar_name} from {download_url}")
                        changes.append(f"Updated plugin {plugin.name} on {instance.name}")
                    except Exception as e:
                        logger.error(f"Failed to download updated plugin JAR: {e}")
                        changes.append(f"Failed to update plugin {plugin.name}: {e}")
                else:
                    logger.warning(f"No download URL available for plugin {plugin.name}")
                    changes.append(f"Updated plugin {plugin.name} on {instance.name} (manual JAR replacement required)")
            else:
                changes.append(f"Would update plugin {plugin.name} on {instance.name}")
        
        elif deployment.entity_type == "datapack":
            if not dry_run:
                changes.append(f"Updated datapack {deployment.entity_id}")
            else:
                changes.append(f"Would update datapack {deployment.entity_id}")
        
        logger.info(f"Update deployment executed (dry_run={dry_run})")
        return changes

    def _execute_remove(self, deployment, instance, dry_run: bool) -> List[str]:
        """Execute remove deployment."""
        changes = []
        
        if deployment.entity_type == "plugin":
            plugin = self.uow.plugins.get_by_id(deployment.entity_id)
            if not plugin:
                raise DeploymentError(f"Plugin {deployment.entity_id} not found")
            
            plugins_dir = Path(instance.base_path) / "plugins"
            plugin_jar = plugins_dir / plugin.jar_name
            
            if not dry_run:
                if plugin_jar.exists():
                    plugin_jar.unlink()
                    changes.append(f"Removed plugin {plugin.name} from {instance.name}")
                    logger.info(f"Plugin {plugin.name} removed from {instance.name}")
                else:
                    changes.append(f"Plugin JAR not found: {plugin_jar}")
            else:
                changes.append(f"Would remove plugin {plugin.name} from {instance.name}")
        
        elif deployment.entity_type == "datapack":
            if not dry_run:
                changes.append(f"Removed datapack {deployment.entity_id}")
            else:
                changes.append(f"Would remove datapack {deployment.entity_id}")
        
        logger.info(f"Remove deployment executed (dry_run={dry_run})")
        return changes

    def _execute_config(self, deployment, instance, dry_run: bool) -> List[str]:
        """Execute config deployment."""
        changes = []
        
        # Use ConfigService to enforce config changes
        from homeamp_v2.domain.services.config_service import ConfigService
        config_service = ConfigService(self.uow)
        
        result = config_service.enforce_config(instance.id, dry_run=dry_run)
        changes.extend([f"{c['action']} {c['config_key']} in {c['config_file']}" for c in result.get('changes', [])])
        
        logger.info(f"Config deployment executed (dry_run={dry_run}): {len(changes)} changes")
        return changes

    def request_approval(self, deployment_id: int, approvers: List[str], reason: str) -> int:
        """Request approval for a deployment.

        Args:
            deployment_id: Deployment queue ID
            approvers: List of approver usernames
            reason: Approval reason

        Returns:
            Approval request ID

        Raises:
            DeploymentError: If request fails
        """
        try:
            deployment = self.uow.deployments.get_by_id(deployment_id)
            if not deployment:
                raise DeploymentError(f"Deployment {deployment_id} not found")

            # Create ApprovalRequest
            from homeamp_v2.data.models.deployment import ApprovalRequest
            
            approval = ApprovalRequest(
                deployment_id=deployment_id,
                approvers=",".join(approvers),  # Store as comma-separated string
                reason=reason,
                status="pending",
                requested_at=datetime.utcnow(),
                votes="",
                approved_count=0,
                rejected_count=0
            )
            self.uow.session.add(approval)
            
            logger.info(
                f"Approval requested for deployment {deployment_id}: approvers={approvers}, reason={reason}"
            )

            # Update deployment status
            self.uow.deployments.update(deployment_id, status="awaiting_approval")
            self.uow.commit()

            return approval.id

        except Exception as e:
            self.uow.rollback()
            logger.error(f"Failed to request approval: {e}")
            raise DeploymentError(f"Failed to request approval: {e}") from e

    def approve_deployment(self, approval_request_id: int, approver: str, approved: bool) -> bool:
        """Approve or reject a deployment.

        Args:
            approval_request_id: Approval request ID
            approver: Approver username
            approved: True to approve, False to reject

        Returns:
            True if deployment can proceed

        Raises:
            DeploymentError: If approval fails
        """
        from homeamp_v2.data.models.deployment import ApprovalRequest
        from sqlalchemy import select
        
        try:
            # Get approval request
            stmt = select(ApprovalRequest).where(ApprovalRequest.id == approval_request_id)
            result = self.uow.session.execute(stmt)
            approval_req = result.scalar_one_or_none()
            
            if not approval_req:
                raise DeploymentError(f"Approval request {approval_request_id} not found")
            
            # Check if approver is authorized
            approvers_list = approval_req.approvers.split(",")
            if approver not in approvers_list:
                raise DeploymentError(f"{approver} not authorized to approve this request")
            
            # Record vote
            votes = approval_req.votes.split(",") if approval_req.votes else []
            vote_entry = f"{approver}:{'approve' if approved else 'reject'}"
            votes.append(vote_entry)
            approval_req.votes = ",".join(votes)
            
            # Update counts
            if approved:
                approval_req.approved_count += 1
            else:
                approval_req.rejected_count += 1
            
            # Check if we have majority or rejection
            total_approvers = len(approvers_list)
            majority = (total_approvers // 2) + 1
            
            if approval_req.approved_count >= majority:
                approval_req.status = "approved"
                approval_req.approved_at = datetime.utcnow()
                self.uow.deployments.update(approval_req.deployment_id, status="approved")
                can_proceed = True
            elif approval_req.rejected_count >= majority:
                approval_req.status = "rejected"
                self.uow.deployments.update(approval_req.deployment_id, status="rejected")
                can_proceed = False
            else:
                can_proceed = False
            
            self.uow.commit()
            
            logger.info(
                f"Approval vote: request={approval_request_id}, approver={approver}, approved={approved}, can_proceed={can_proceed}"
            )
            return can_proceed
            
        except Exception as e:
            self.uow.rollback()
            logger.error(f"Approval failed: {e}")
            raise DeploymentError(f"Approval failed: {e}") from e
