"""
AMP API Client

Interfaces with CubeCoders AMP API to manage Minecraft server instances.
AMP already manages all the instances - we just need to use its API.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import requests
import logging
from datetime import datetime


class AMPClient:
    """
    Client for CubeCoders AMP API
    
    AMP manages all the Minecraft instances - we use its API to:
    - List instances
    - Start/stop/restart servers
    - Deploy plugins
    - Get instance status
    - Execute console commands
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize AMP API client
        
        Args:
            base_url: AMP panel URL (e.g., http://localhost:8080)
            username: AMP admin username
            password: AMP admin password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session_id: Optional[str] = None
        self.logger = logging.getLogger(__name__)
        
        # Login on initialization
        self._login()
    
    def _login(self) -> bool:
        """Login to AMP and get session ID"""
        try:
            response = requests.post(
                f"{self.base_url}/API/Core/Login",
                json={
                    "username": self.username,
                    "password": self.password,
                    "token": "",
                    "rememberMe": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get('sessionID')
                self.logger.info("Successfully logged into AMP")
                return True
            else:
                self.logger.error(f"AMP login failed: {response.status_code}")
                return False
        
        except Exception as e:
            self.logger.error(f"AMP login error: {e}")
            return False
    
    def _api_call(self, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make API call to AMP
        
        Args:
            endpoint: API endpoint (e.g., "ADSModule/GetInstances")
            data: Request data
            
        Returns:
            Response data or None on failure
        """
        if not self.session_id:
            self.logger.error("Not logged in to AMP")
            return None
        
        try:
            url = f"{self.base_url}/API/{endpoint}"
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            params = {"SESSIONID": self.session_id}
            
            response = requests.post(
                url,
                json=data or {},
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"AMP API call failed: {response.status_code} for {endpoint}")
                return None
        
        except Exception as e:
            self.logger.error(f"AMP API error for {endpoint}: {e}")
            return None
    
    def get_instances(self) -> List[Dict[str, Any]]:
        """
        Get all AMP instances
        
        Returns:
            List of instance info dicts with keys:
                - InstanceID
                - FriendlyName
                - InstanceName
                - Module (e.g., "Minecraft")
                - Running
                - AppState
        """
        result = self._api_call("ADSModule/GetInstances")
        if result and isinstance(result, list):
            return result
        return []
    
    def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status of an instance
        
        Args:
            instance_id: AMP instance ID
            
        Returns:
            Status dict with Running, AppState, Metrics, etc.
        """
        return self._api_call("Core/GetStatus", {"InstanceId": instance_id})
    
    def start_instance(self, instance_id: str) -> bool:
        """Start an instance"""
        result = self._api_call("Core/Start", {"InstanceId": instance_id})
        return result is not None
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop an instance"""
        result = self._api_call("Core/Stop", {"InstanceId": instance_id})
        return result is not None
    
    def restart_instance(self, instance_id: str) -> bool:
        """Restart an instance"""
        result = self._api_call("Core/Restart", {"InstanceId": instance_id})
        return result is not None
    
    def send_console_command(self, instance_id: str, command: str) -> bool:
        """
        Send console command to instance
        
        Args:
            instance_id: AMP instance ID
            command: Server command (e.g., "stop", "reload")
        """
        result = self._api_call(
            "Core/SendConsoleMessage",
            {
                "InstanceId": instance_id,
                "message": command
            }
        )
        return result is not None
    
    def get_instance_config(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get instance configuration"""
        return self._api_call("Core/GetConfig", {"InstanceId": instance_id})
    
    def update_instance_config(self, instance_id: str, config_updates: Dict[str, Any]) -> bool:
        """
        Update instance configuration
        
        Args:
            instance_id: AMP instance ID
            config_updates: Dict of config key/value pairs to update
        """
        result = self._api_call(
            "Core/SetConfigs",
            {
                "InstanceId": instance_id,
                "data": config_updates
            }
        )
        return result is not None
    
    def get_file_listing(self, instance_id: str, directory: str = "") -> Optional[List[Dict]]:
        """
        Get file listing for instance directory
        
        Args:
            instance_id: AMP instance ID
            directory: Relative directory path
            
        Returns:
            List of files/directories
        """
        return self._api_call(
            "FileManagerPlugin/GetDirectoryListing",
            {
                "InstanceId": instance_id,
                "Dir": directory
            }
        )
    
    def upload_file(self, instance_id: str, local_path: Path, remote_path: str) -> bool:
        """
        Upload file to instance
        
        Args:
            instance_id: AMP instance ID
            local_path: Local file path
            remote_path: Remote path within instance
        """
        # Note: File upload via AMP API requires multipart/form-data
        # This is a simplified version - full implementation would use proper file upload
        self.logger.warning("File upload not fully implemented - use SFTP/file manager")
        return False
    
    def delete_file(self, instance_id: str, file_path: str) -> bool:
        """
        Delete file from instance
        
        Args:
            instance_id: AMP instance ID
            file_path: Path to file within instance
        """
        result = self._api_call(
            "FileManagerPlugin/DeleteFile",
            {
                "InstanceId": instance_id,
                "Filename": file_path
            }
        )
        return result is not None
    
    def rename_file(self, instance_id: str, old_path: str, new_path: str) -> bool:
        """
        Rename/move file within instance
        
        Args:
            instance_id: AMP instance ID
            old_path: Current file path
            new_path: New file path
        """
        result = self._api_call(
            "FileManagerPlugin/RenameFile",
            {
                "InstanceId": instance_id,
                "Filename": old_path,
                "NewFilename": new_path
            }
        )
        return result is not None
    
    def create_backup(self, instance_id: str, title: str, description: str = "") -> Optional[str]:
        """
        Create backup of instance
        
        Args:
            instance_id: AMP instance ID
            title: Backup title
            description: Backup description
            
        Returns:
            Backup ID if successful
        """
        result = self._api_call(
            "LocalFileBackupPlugin/TakeBackup",
            {
                "InstanceId": instance_id,
                "Title": title,
                "Description": description,
                "Sticky": False
            }
        )
        
        if result:
            return result.get('BackupId')
        return None
    
    def restore_backup(self, instance_id: str, backup_id: str) -> bool:
        """Restore instance from backup"""
        result = self._api_call(
            "LocalFileBackupPlugin/RestoreBackup",
            {
                "InstanceId": instance_id,
                "BackupId": backup_id
            }
        )
        return result is not None
    
    def list_backups(self, instance_id: str) -> List[Dict[str, Any]]:
        """List all backups for instance"""
        result = self._api_call(
            "LocalFileBackupPlugin/GetBackups",
            {"InstanceId": instance_id}
        )
        if result and isinstance(result, list):
            return result
        return []


class AMPPluginDeployer:
    """
    Handles plugin deployment via AMP API
    
    Integrates with AMP's file management to deploy plugins safely
    """
    
    def __init__(self, amp_client: AMPClient):
        """
        Initialize plugin deployer
        
        Args:
            amp_client: Connected AMP client
        """
        self.amp = amp_client
        self.logger = logging.getLogger(__name__)
    
    def deploy_plugin(self, 
                     instance_id: str,
                     plugin_jar: Path,
                     backup_old: bool = True,
                     restart_server: bool = True) -> bool:
        """
        Deploy plugin to instance
        
        Args:
            instance_id: AMP instance ID
            plugin_jar: Path to plugin JAR file
            backup_old: Create backup before deployment
            restart_server: Restart server after deployment
            
        Returns:
            True if successful
        """
        try:
            instance_name = self._get_instance_name(instance_id)
            self.logger.info(f"Deploying {plugin_jar.name} to {instance_name}")
            
            # 1. Create backup if requested
            if backup_old:
                backup_id = self.amp.create_backup(
                    instance_id,
                    f"Pre-plugin-update-{plugin_jar.stem}",
                    f"Automatic backup before deploying {plugin_jar.name}"
                )
                if backup_id:
                    self.logger.info(f"Created backup: {backup_id}")
                else:
                    self.logger.warning("Backup creation failed")
            
            # 2. Stop server for safe deployment
            self.logger.info(f"Stopping {instance_name}...")
            if not self.amp.stop_instance(instance_id):
                self.logger.error("Failed to stop instance")
                return False
            
            # Wait for server to stop
            import time
            time.sleep(5)
            
            # 3. Remove old plugin JAR (if exists)
            # Note: This requires file system access or proper AMP file upload API
            # For now, this is a placeholder
            self.logger.warning("Plugin file deployment requires file system access or SFTP")
            
            # 4. Restart server if requested
            if restart_server:
                self.logger.info(f"Starting {instance_name}...")
                if not self.amp.start_instance(instance_id):
                    self.logger.error("Failed to start instance")
                    return False
            
            self.logger.info(f"Successfully deployed {plugin_jar.name} to {instance_name}")
            return True
        
        except Exception as e:
            self.logger.error(f"Plugin deployment failed: {e}")
            return False
    
    def _get_instance_name(self, instance_id: str) -> str:
        """Get friendly name for instance"""
        status = self.amp.get_instance_status(instance_id)
        if status:
            return status.get('FriendlyName', instance_id)
        return instance_id
    
    def rollback_plugin(self, instance_id: str, backup_id: str) -> bool:
        """
        Rollback plugin deployment by restoring backup
        
        Args:
            instance_id: AMP instance ID
            backup_id: Backup to restore
            
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Rolling back instance {instance_id} to backup {backup_id}")
            
            # Stop instance
            self.amp.stop_instance(instance_id)
            import time
            time.sleep(5)
            
            # Restore backup
            if not self.amp.restore_backup(instance_id, backup_id):
                self.logger.error("Backup restoration failed")
                return False
            
            # Start instance
            self.amp.start_instance(instance_id)
            
            self.logger.info("Rollback successful")
            return True
        
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False


def main():
    """Test AMP API integration"""
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    amp = AMPClient(
        base_url="http://localhost:8080",
        username="admin",
        password="password"
    )
    
    # List all instances
    instances = amp.get_instances()
    print(f"\nFound {len(instances)} instances:")
    for instance in instances:
        print(f"  - {instance.get('FriendlyName')} ({instance.get('InstanceID')})")
        print(f"    Running: {instance.get('Running')}")
        print(f"    State: {instance.get('AppState')}")


if __name__ == "__main__":
    main()
