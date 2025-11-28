"""HomeAMP V2.0 - Base agent for orchestrating discovery and deployment."""

import logging
import os
import time
from datetime import datetime
from typing import Optional

from homeamp_v2.agent.tile_watcher import TileWatcher
from homeamp_v2.core.config import Settings
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services import (
    ConfigService,
    DeploymentService,
    DiscoveryService,
    UpdateService,
)
from homeamp_v2.integrations.minio import MinIOClient

logger = logging.getLogger(__name__)


class HomeAMPAgent:
    """Main agent for orchestrating HomeAMP operations."""

    def __init__(self, settings: Settings):
        """Initialize agent.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.running = False
        self._heartbeat_interval = 60  # seconds
        
        # Optional tile watcher for Pl3xMap/LiveAtlas
        self.tile_watcher: Optional[TileWatcher] = None
        if settings.tile_watcher_enabled:
            self._initialize_tile_watcher()
        self.running = False
        self._heartbeat_interval = 60  # seconds

    def start(self) -> None:
        """Start the agent."""
        logger.info("Starting HomeAMP Agent")
        self.running = True

        try:
            # Send initial heartbeat
            self._send_heartbeat("starting")

            # Main loop
            while self.running:
                try:
                    self._run_cycle()
                except KeyboardInterrupt:
                    logger.info("Received shutdown signal")
                    break
                except Exception as e:
                    logger.error(f"Error in agent cycle: {e}", exc_info=True)

                # Sleep between cycles
                time.sleep(self.settings.agent_interval)

        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the agent."""
        logger.info("Stopping HomeAMP Agent")
        self.running = False
        self._send_heartbeat("stopped")

    def _run_cycle(self) -> None:
        """Run a single agent cycle."""
        logger.debug("Starting agent cycle")

        with UnitOfWork() as uow:
            # Initialize services
            discovery = DiscoveryService(uow)
            config = ConfigService(uow)
            deployment = DeploymentService(uow)
            update = UpdateService(uow)

            # Send heartbeat
            self._send_heartbeat("running")

            # Discovery phase
            if self.settings.enable_discovery:
                self._run_discovery(discovery)

            # Variance detection phase
            if self.settings.enable_variance_detection:
                self._run_variance_detection(config)

            # Update checking phase
            if self.settings.enable_update_checks:
                self._run_update_checks(update)

            # Deployment phase
            if self.settings.enable_auto_deployment:
                self._run_deployments(deployment)

        logger.debug("Agent cycle complete")

    def _run_discovery(self, discovery: DiscoveryService) -> None:
        """Run discovery phase."""
        try:
            logger.info("Running discovery scan")
            results = discovery.scan_all_instances()
            logger.info(f"Discovery complete: scanned {len(results['instances'])} instances")

            # Store discovery results in database
            import json

            from homeamp_v2.data.models.monitoring import DiscoveryItem, DiscoveryRun
            
            with UnitOfWork() as uow:
                # Create discovery run record
                run = DiscoveryRun(
                    run_type="full_scan",
                    status="completed",
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    items_found=len(results.get('instances', [])) + len(results.get('plugins', [])) + len(results.get('datapacks', [])),
                    errors_count=0
                )
                uow.session.add(run)
                uow.session.flush()  # Get run.id
                
                # Store discovered items
                for instance in results.get('instances', []):
                    item = DiscoveryItem(
                        run_id=run.id,
                        item_type="instance",
                        item_id=instance.get('name', 'unknown'),
                        item_data=json.dumps(instance)
                    )
                    uow.session.add(item)
                
                for plugin in results.get('plugins', []):
                    item = DiscoveryItem(
                        run_id=run.id,
                        item_type="plugin",
                        item_id=plugin.get('name', 'unknown'),
                        item_data=json.dumps(plugin)
                    )
                    uow.session.add(item)
                
                uow.commit()
                logger.debug(f"Discovery results stored in database (run_id={run.id})")

        except Exception as e:
            logger.error(f"Discovery phase failed: {e}", exc_info=True)

    def _run_variance_detection(self, config: ConfigService) -> None:
        """Run variance detection phase."""
        try:
            logger.info("Running variance detection")

            # Get all active instances
            with UnitOfWork() as uow:
                instances = uow.instances.get_active()

            total_variances = 0
            for instance in instances:
                try:
                    variances = config.detect_variances(instance.id)
                    if variances:
                        logger.warning(
                            f"Instance {instance.name}: {len(variances)} variances detected"
                        )
                        total_variances += len(variances)

                        # Store variances in database
                        from homeamp_v2.data.models.config import ConfigVariance
                        
                        for variance in variances:
                            var_record = ConfigVariance(
                                instance_id=instance.id,
                                plugin_name=variance.get('plugin_name', ''),
                                config_file=variance.get('config_file', ''),
                                config_key=variance.get('config_key', ''),
                                expected_value=str(variance.get('expected_value', '')),
                                actual_value=str(variance.get('actual_value', '')),
                                variance_type=variance.get('type', 'unknown'),
                                severity=variance.get('severity', 'info'),
                                detected_at=datetime.utcnow()
                            )
                            uow.session.add(var_record)
                        
                        # Create notifications for critical variances
                        critical_count = sum(1 for v in variances if v.get('severity') == 'critical')
                        if critical_count > 0:
                            if self.notifications:
                                self.notifications.notify_variance(
                                    instance.name,
                                    len(variances),
                                    critical_count
                                )

                except Exception as e:
                    logger.error(f"Variance detection failed for {instance.name}: {e}")

            logger.info(f"Variance detection complete: {total_variances} total variances")

        except Exception as e:
            logger.error(f"Variance detection phase failed: {e}", exc_info=True)

    def _run_update_checks(self, update: UpdateService) -> None:
        """Run update checking phase."""
        try:
            logger.info("Checking for plugin updates")
            updates = update.check_plugin_updates()

            if updates:
                logger.info(f"Found {len(updates)} plugin updates available")

                # Create notifications for available updates
                if self.notifications:
                    for upd in updates[:5]:  # Notify top 5
                        self.notifications.notify_update(
                            upd.get('plugin_name', 'Unknown'),
                            upd.get('current_version', 'unknown'),
                            upd.get('latest_version', 'unknown')
                        )
                
                # Queue auto-updates if configured
                if self.settings.enable_auto_updates:
                    with UnitOfWork() as uow:
                        update_service = UpdateService(uow)
                        
                        for upd in updates:
                            try:
                                # Get instances with this plugin
                                from homeamp_v2.data.models.plugin import InstancePlugin
                                from sqlalchemy import select
                                
                                stmt = select(InstancePlugin).where(
                                    InstancePlugin.plugin_id == upd['plugin_id']
                                )
                                result = uow.session.execute(stmt)
                                instance_plugins = result.scalars().all()
                                
                                # Queue update for each instance
                                for inst_plugin in instance_plugins:
                                    update_service.queue_plugin_update(
                                        upd['plugin_id'],
                                        inst_plugin.instance_id,
                                        upd['latest_version'],
                                        auto_update=True
                                    )
                                
                            except Exception as e:
                                logger.error(f"Failed to queue auto-update for {upd.get('plugin_name')}: {e}")

            else:
                logger.info("All plugins up to date")

        except Exception as e:
            logger.error(f"Update checking phase failed: {e}", exc_info=True)

    def _run_deployments(self, deployment: DeploymentService) -> None:
        """Run deployment phase."""
        try:
            logger.info("Processing pending deployments")
            pending = deployment.get_pending_deployments()

            if not pending:
                logger.debug("No pending deployments")
                return

            logger.info(f"Found {len(pending)} pending deployments")

            # Process deployments by priority
            for deploy in pending[:5]:  # Process up to 5 per cycle
                try:
                    logger.info(
                        f"Executing deployment {deploy['id']}: "
                        f"{deploy['deployment_type']} {deploy['entity_type']}"
                    )

                    result = deployment.execute_deployment(deploy["id"])

                    if result["success"]:
                        logger.info(f"Deployment {deploy['id']} completed successfully")
                    else:
                        logger.error(f"Deployment {deploy['id']} failed: {result['errors']}")

                except Exception as e:
                    logger.error(f"Deployment {deploy['id']} failed: {e}", exc_info=True)

        except Exception as e:
            logger.error(f"Deployment phase failed: {e}", exc_info=True)

    def _send_heartbeat(self, status: str) -> None:
        """Send agent heartbeat.

        Args:
            status: Agent status (starting, running, stopped)
        """
        try:
            import platform

            import psutil

            with UnitOfWork() as uow:
                # Create AgentHeartbeat entry
                import socket

                from homeamp_v2.data.models.monitoring import AgentHeartbeat
                
                # Use unique agent ID: hostname + PID for uniqueness per deployment
                agent_id = f"homeamp-agent-{socket.gethostname()}-{os.getpid()}"
                
                heartbeat = AgentHeartbeat(
                    agent_id=agent_id,
                    status=status,
                    last_discovery_run=self.last_discovery,
                    last_config_check=self.last_config_check,
                    last_update_check=self.last_update_check,
                    cpu_percent=psutil.cpu_percent(),
                    memory_percent=psutil.virtual_memory().percent,
                    heartbeat_at=datetime.utcnow()
                )
                uow.session.add(heartbeat)
                uow.commit()
                
                logger.debug(
                    f"Heartbeat: status={status}, "
                    f"cpu={psutil.cpu_percent()}%, "
                    f"mem={psutil.virtual_memory().percent}%"
                )

        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {e}")

    def _initialize_tile_watcher(self) -> None:
        """Initialize Pl3xMap tile watcher for MinIO sync."""
        try:
            logger.info("Initializing Pl3xMap tile watcher")
            
            # Create MinIO client
            minio_client = MinIOClient(
                endpoint=self.settings.minio_endpoint,
                access_key=self.settings.minio_access_key,
                secret_key=self.settings.minio_secret_key,
                secure=self.settings.minio_secure,
                region=self.settings.minio_region,
            )
            
            # Create tile watcher with UnitOfWork
            uow = UnitOfWork()
            self.tile_watcher = TileWatcher(
                uow=uow,
                minio_client=minio_client,
                bucket_name=self.settings.minio_bucket_tiles,
                sync_interval=self.settings.tile_watcher_sync_interval,
            )
            
            logger.info("Tile watcher initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize tile watcher: {e}", exc_info=True)
            self.tile_watcher = None

    def start_tile_watcher(self) -> None:
        """Start the tile watcher in a separate process/thread.
        
        This should be called after agent initialization if tile watching is enabled.
        The tile watcher runs independently of the main agent loop.
        """
        if not self.tile_watcher:
            logger.warning("Tile watcher not initialized, cannot start")
            return
        
        logger.info("Starting tile watcher loop")
        
        try:
            # Run in foreground (or spawn thread/process for background operation)
            self.tile_watcher.watch_loop()
        except KeyboardInterrupt:
            logger.info("Tile watcher stopped by user")
        except Exception as e:
            logger.error(f"Tile watcher error: {e}", exc_info=True)

    def run_once(self) -> None:
        """Run a single agent cycle (for testing/manual execution)."""
        logger.info("Running single agent cycle")
        self._run_cycle()
        logger.info("Single cycle complete")
