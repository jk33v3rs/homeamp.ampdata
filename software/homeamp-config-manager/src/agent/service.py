"""
Configuration Management Agent Service

Systemd service that runs on each PHYSICAL DEBIAN SERVER (not per-instance) to:
1. Poll MinIO for pending configuration changes
2. Apply changes to ALL AMP instances on this physical server
3. Upload execution results back to MinIO
4. Monitor for configuration drift across all instances

Architecture:
- One agent per physical server (OVH-Ryzen, Hetzner, etc.)
- Agent runs on Debian host OS, not inside AMP Docker containers
- Manages all instances in /home/amp/.ampdata/instances/
- Discovers and manages instances dynamically
"""

import time
import sys
import json
import signal
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Adjust imports based on installation location
# When installed as systemd service, Python path should be configured
from ..core.cloud_storage import CloudStorage, ChangeRequestManager
from ..updaters.config_updater import ConfigUpdater
from ..analyzers.drift_detector import DriftDetector
from ..core.safety_validator import SafetyValidator
from ..core.settings import get_settings


class AgentService:
    """
    Configuration Management Agent Service
    
    Runs on physical Debian servers to manage ALL AMP instances on that server.
    Each physical server runs ONE agent that discovers and manages all instances
    in /home/amp/.ampdata/instances/
    """
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize agent service
        
        Args:
            config_file: Path to agent configuration YAML (optional, uses settings system)
        
        Note: Agent should be installed on the physical Debian host, not inside
              AMP Docker containers or individual Minecraft instances.
        """
        # Load settings
        self.settings = get_settings(config_file)
        self.agent_config = self.settings.agent_config
        self.minio_config = self.settings.minio_config
        
        # Setup logging FIRST (needed for _discover_instances)
        log_level = getattr(logging, self.settings.log_level.upper(), logging.INFO)
        handlers = []
        
        # Legacy config loading for compatibility
        
        if self.settings.log_to_file:
            log_file = self.settings.get('agent', 'logging', 'log_file', 
                                       default=str(self.settings.data_dir / 'agent.log'))
            handlers.append(logging.FileHandler(log_file))
        
        if self.settings.log_to_console:
            handlers.append(logging.StreamHandler())
        
        logging.basicConfig(
            level=log_level,
            format=self.settings.log_format,
            handlers=handlers
        )
        self.logger = logging.getLogger('archivesmp-agent')
        self.config = self._load_config(config_file) if config_file else {}
        
        # Physical server configuration (NOT Minecraft instance)
        # This agent runs on the physical Debian host (OVH-Ryzen or Hetzner)
        self.physical_server = self.config.get('agent', {}).get('server_name', 'unknown')
        self.server_name = self.physical_server  # Backwards compatibility alias
        
        # Discover all AMP instances on this physical server
        self.managed_instances = self._discover_instances()
        
        self.poll_interval = self.agent_config.change_poll_interval
        self.drift_check_interval = self.agent_config.drift_check_interval
        
        # Initialize cloud storage using settings
        self.storage = CloudStorage(
            endpoint=self.minio_config.endpoint,
            access_key=self.minio_config.access_key,
            secret_key=self.minio_config.secret_key,
            secure=self.minio_config.secure
        )
        
        # Initialize managers with proper paths
        self.change_manager = ChangeRequestManager(self.storage)
        self.updater = ConfigUpdater(self.settings.instances_path)
        self.drift_detector = DriftDetector(self.settings.instances_path)
        
        # Service state
        self.running = False
        self.last_drift_check = 0
    
    def _discover_instances(self) -> List[str]:
        """
        Discover all AMP instances on this physical server by scanning the instances directory.
        
        Returns:
            List of instance IDs (directory names) found in /home/amp/.ampdata/instances/
        """
        instances_dir = Path('/home/amp/.ampdata/instances')
        
        if not instances_dir.exists():
            self.logger.warning(f"Instances directory not found: {instances_dir}")
            return []
        
        instances = []
        for item in instances_dir.iterdir():
            if item.is_dir():
                # Check if it looks like an AMP instance (has Config directory)
                if (item / 'AMPConfig.conf').exists():
                    instances.append(item.name)
                    self.logger.info(f"Discovered instance: {item.name}")
        
        self.logger.info(f"Total instances discovered on {self.physical_server}: {len(instances)}")
        return instances
    
    def _load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load agent configuration"""
        try:
            if not config_file.exists():
                # Create default config
                default_config = {
                    'server': {
                        'name': 'unknown',
                        'path': '/opt/yunohost/minecraft',
                        'type': 'paper'
                    },
                    'minio': {
                        'endpoint': 'localhost:9000',
                        'access_key': 'minioadmin',
                        'secret_key': 'minioadmin',
                        'bucket_name': 'archivesmp-changes',
                        'secure': False
                    },
                    'agent': {
                        'poll_interval': 900,  # 15 minutes
                        'backup_retention_days': 7,
                        'enabled': True,
                        'log_file': str(config_file.parent / 'agent.log'),
                        'server_name': 'unknown',
                        'poll_interval_seconds': 900,  # 15 minutes (was 30 seconds)
                        'drift_check_interval_seconds': 3600  # 1 hour (was 5 minutes)
                    },
                    'storage': {
                        'endpoint': 'localhost:9000',
                        'access_key': 'minioadmin',
                        'secret_key': 'minioadmin',
                        'secure': False
                    }
                }
                
                config_file.parent.mkdir(parents=True, exist_ok=True)
                import yaml
                with open(config_file, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
                
                self.logger.info(f"Created default config at {config_file}")
                return default_config
            
            # Load existing config
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            self.logger.info(f"Loaded config from {config_file}")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def start(self):
        """Start the agent service"""
        self.logger.info(f"Starting ArchiveSMP Config Agent for {self.server_name}")
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
        
        try:
            self._run_loop()
        except Exception as e:
            self.logger.error(f"Fatal error in agent loop: {e}", exc_info=True)
            sys.exit(1)
    
    def _run_loop(self):
        """Main service loop"""
        while self.running:
            try:
                # Check for pending changes
                self._process_pending_changes()
                
                # Periodic drift detection
                if self._should_check_drift():
                    self._check_drift()
                
                # Sleep until next poll
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"Error in service loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)  # Continue after error
    
    def _process_pending_changes(self):
        """Process any pending configuration changes"""
        try:
            # Get pending changes from cloud storage
            pending_changes = self.change_manager.list_pending_changes()
            
            if not pending_changes:
                self.logger.debug("No pending changes found")
                return
            
            self.logger.info(f"Found {len(pending_changes)} pending changes")
            
            for change_request in pending_changes:
                request_id = change_request.get('request_id')
                target_servers = change_request.get('target_servers', [])
                
                # Check if this change applies to this server
                if (target_servers != 'all' and 
                    self.server_name not in target_servers):
                    continue
                
                self.logger.info(f"Processing change request {request_id}")
                
                try:
                    # Apply the change request
                    result = self._apply_change_request(request_id, change_request)
                    
                    # Upload result back to storage
                    self.change_manager.upload_change_result(request_id, result)
                    
                    # Mark as completed if successful
                    if result.get('success'):
                        self.change_manager.mark_change_completed(request_id)
                        self.logger.info(f"Successfully applied change {request_id}")
                    else:
                        self.logger.error(f"Failed to apply change {request_id}: {result.get('error')}")
                
                except Exception as e:
                    error_result = {
                        'success': False,
                        'server_name': self.server_name,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    }
                    self.change_manager.upload_change_result(request_id, error_result)
                    self.logger.error(f"Exception processing change {request_id}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error processing pending changes: {e}")
    
    def _apply_change_request(self, change_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a configuration change request
        
        Args:
            change_id: Change request ID
            request_data: Change request data
            
        Returns:
            Execution result
        """
        try:
            # Initialize config updater with server path
            server_path = Path(self.config['server']['path'])
            self.updater = ConfigUpdater(server_path, dry_run=False)
            
            # Inject change manager for communication
            self.updater.change_manager = self.change_manager
            
            # Apply the change request
            result = self.updater.apply_change_request(request_data)
            
            # Add server info to result
            result.update({
                'server_name': self.server_name,
                'applied_at': datetime.now().isoformat(),
                'agent_version': '1.0.0'
            })
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'request_id': change_id,
                'server_name': self.server_name,
                'error': str(e),
                'applied_at': datetime.now().isoformat()
            }
    
    def _should_check_drift(self) -> bool:
        """Determine if it's time for a drift check"""
        current_time = time.time()
        return (current_time - self.last_drift_check) >= self.drift_check_interval
    
    def _check_drift(self):
        """Perform configuration drift detection"""
        try:
            self.logger.info("Starting drift detection scan")
            
            # Initialize drift detector if not already done
            if not hasattr(self, 'drift_detector') or not self.drift_detector:
                from ..analyzers.drift_detector import DriftDetector
                baseline_path = self.settings.data_dir / "baselines"
                self.drift_detector = DriftDetector(baseline_path)
            
            # Perform drift detection
            # Use instances_path from agent config, or fallback to old server config
            if 'server' in self.config and 'path' in self.config['server']:
                server_path = Path(self.config['server']['path'])
            else:
                server_path = Path('/home/amp/.ampdata/instances')
            drift_results = self.drift_detector.detect_drift(self.server_name, server_path)
            
            # Add metadata
            drift_data = {
                'server_name': self.server_name,
                'scan_timestamp': datetime.now().isoformat(),
                'drift_detected': bool(drift_results.get('drift_items')),
                'results': drift_results
            }
            
            # Upload results
            self._upload_drift_report(drift_data)
            
            # Update last check time
            self.last_drift_check = time.time()
            
            if drift_data['drift_detected']:
                self.logger.warning(f"Configuration drift detected on {self.server_name}")
            else:
                self.logger.info(f"No drift detected on {self.server_name}")
                
        except Exception as e:
            self.logger.error(f"Drift detection failed: {e}")
    
    def _upload_drift_report(self, drift_data: Dict[str, Any]):
        """Upload drift detection results to MinIO"""
        try:
            bucket_name = "archivesmp-drift-reports"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_name = f"{self.server_name}/drift_report_{timestamp}.json"
            
            # Ensure bucket exists and upload
            self.storage.ensure_bucket_exists(bucket_name)
            success = self.storage.upload_json(bucket_name, object_name, drift_data)
            
            if success:
                self.logger.info(f"Uploaded drift report to {bucket_name}/{object_name}")
            else:
                self.logger.error(f"Failed to upload drift report to {bucket_name}/{object_name}")
                
        except Exception as e:
            self.logger.error(f"Error uploading drift report: {e}")
    
    def _handle_shutdown(self, signum, frame):
        """Handle graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False


def main():
    """Service entry point"""
    if len(sys.argv) < 2:
        print("Usage: homeamp-agent <config-file>")
        sys.exit(1)
    
    config_file = Path(sys.argv[1])
    if not config_file.exists():
        print(f"Config file not found: {config_file}")
        sys.exit(1)
    
    agent = AgentService(config_file)
    agent.start()


if __name__ == "__main__":
    main()
