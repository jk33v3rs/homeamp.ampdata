"""
Automated Plugin Update System

Combines:
- Plugin update checking (GitHub, SpigotMC, etc.)
- Excel spreadsheet integration (deployment matrix)
- AMP API integration (actual deployment)
- Config backup/rollback system

This is the ACTUAL automation - runs hourly via cron/systemd timer
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from automation.pulumi_update_monitor import PluginUpdateMonitor, PluginUpdate
from amp_integration.amp_client import AMPClient, AMPPluginDeployer
from ..core.excel_reader import ExcelConfigReader


class AutomatedPluginManager:
    """
    Main automation system that orchestrates:
    1. Check for plugin updates (hourly)
    2. Read deployment matrix from Excel
    3. Stage approved updates
    4. Deploy to DEV01 via AMP API
    5. Backup configs before deployment
    6. Rollback on failure
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize automation system
        
        Args:
            config: Configuration dict with:
                - amp_url: AMP panel URL
                - amp_username: AMP admin username
                - amp_password: AMP admin password
                - plugin_registry_path: Path to plugin_registry.yaml
                - staging_path: Path for staged plugin JARs
                - excel_matrix_path: Path to deployment_matrix.csv
                - dev_instance_id: AMP instance ID for DEV01
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.update_monitor = PluginUpdateMonitor(
            staging_path=Path(config['staging_path']),
            plugin_registry_path=Path(config['plugin_registry_path']),
            excel_output_path=Path(config.get('excel_output_path', '/var/lib/archivesmp/reports/plugin_updates.xlsx'))
        )
        
        self.amp_client = AMPClient(
            base_url=config['amp_url'],
            username=config['amp_username'],
            password=config['amp_password']
        )
        
        self.amp_deployer = AMPPluginDeployer(self.amp_client)
        
        self.dev_instance_id = config.get('dev_instance_id')
        
        # Initialize Excel reader for deployment matrix and server variables
        self.excel_reader = ExcelConfigReader(Path(config.get('reference_data_dir', '/var/lib/archivesmp/data/reference_data')))
    
    async def run_hourly_cycle(self):
        """
        Main hourly automation cycle:
        1. Check for plugin updates
        2. Stage updates
        3. Write to Excel
        4. Check for approved updates
        5. Deploy to DEV01 if approved
        """
        self.logger.info("=== Starting hourly automation cycle ===")
        
        try:
            # Step 1: Check for updates
            self.logger.info("Checking for plugin updates...")
            updates = await self.update_monitor.check_all_updates()
            
            if not updates:
                self.logger.info("No plugin updates available")
                return
            
            self.logger.info(f"Found {len(updates)} plugin updates")
            
            # Step 2: Stage updates
            self.logger.info("Staging plugin updates...")
            staged_entries = await self.update_monitor.stage_all_updates(updates)
            
            # Step 3: Write to Excel
            self.logger.info("Writing results to Excel...")
            self.update_monitor.write_to_excel(updates, staged_entries)
            
            # Step 4: Check deployment matrix for auto-deploy flags
            self.logger.info("Checking deployment matrix for auto-deploy...")
            auto_deploy_plugins = self._check_auto_deploy(updates)
            
            if not auto_deploy_plugins:
                self.logger.info("No plugins marked for auto-deploy")
                return
            
            # Step 5: Deploy to DEV01 if configured
            if self.dev_instance_id:
                self.logger.info(f"Deploying {len(auto_deploy_plugins)} plugins to DEV01...")
                await self._deploy_to_dev01(auto_deploy_plugins)
            else:
                self.logger.warning("DEV01 instance ID not configured - skipping deployment")
            
            self.logger.info("=== Hourly cycle complete ===")
        
        except Exception as e:
            self.logger.error(f"Hourly cycle failed: {e}", exc_info=True)
    
    def _check_auto_deploy(self, updates: List[PluginUpdate]) -> List[PluginUpdate]:
        """
        Check deployment matrix CSV to see which plugins are marked for auto-update
        
        Args:
            updates: List of available updates
            
        Returns:
            List of updates marked for auto-deployment
        """
        import csv
        
        matrix_path = Path(self.config.get('excel_matrix_path', '/var/lib/archivesmp/deployment_matrix.csv'))
        
        if not matrix_path.exists():
            self.logger.warning(f"Deployment matrix not found: {matrix_path}")
            return []
        
        try:
            auto_deploy_plugins = set()
            
            with open(matrix_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    plugin_name = row.get('plugin_name', '')
                    auto_update = row.get('auto_update', 'False').lower() == 'true'
                    
                    if auto_update:
                        auto_deploy_plugins.add(plugin_name.lower())
            
            # Filter updates for auto-deploy plugins
            result = [u for u in updates if u.plugin_name.lower() in auto_deploy_plugins]
            
            self.logger.info(f"Found {len(result)} plugins marked for auto-deploy")
            return result
        
        except Exception as e:
            self.logger.error(f"Failed to read deployment matrix: {e}")
            return []
    
    async def _deploy_to_dev01(self, updates: List[PluginUpdate]):
        """
        Deploy updates to DEV01 instance
        
        Args:
            updates: List of plugin updates to deploy
        """
        for update in updates:
            try:
                self.logger.info(f"Deploying {update.plugin_name} {update.latest_version} to DEV01...")
                
                # Find staged plugin JAR
                staging_path = Path(self.config['staging_path'])
                plugin_jar = staging_path / f"{update.plugin_name}-{update.latest_version}.jar"
                
                if not plugin_jar.exists():
                    self.logger.error(f"Staged plugin not found: {plugin_jar}")
                    continue
                
                # Deploy via AMP API
                success = self.amp_deployer.deploy_plugin(
                    instance_id=self.dev_instance_id,
                    plugin_jar=plugin_jar,
                    backup_old=True,
                    restart_server=True
                )
                
                if success:
                    self.logger.info(f"Successfully deployed {update.plugin_name}")
                else:
                    self.logger.error(f"Failed to deploy {update.plugin_name}")
            
            except Exception as e:
                self.logger.error(f"Deployment error for {update.plugin_name}: {e}")
    
    def manual_deploy(self, plugin_name: str, version: str, instance_id: str) -> bool:
        """
        Manually deploy a specific plugin version to an instance
        
        Args:
            plugin_name: Plugin name
            version: Plugin version
            instance_id: AMP instance ID
            
        Returns:
            True if successful
        """
        try:
            staging_path = Path(self.config['staging_path'])
            plugin_jar = staging_path / f"{plugin_name}-{version}.jar"
            
            if not plugin_jar.exists():
                self.logger.error(f"Plugin JAR not found: {plugin_jar}")
                return False
            
            return self.amp_deployer.deploy_plugin(
                instance_id=instance_id,
                plugin_jar=plugin_jar,
                backup_old=True,
                restart_server=True
            )
        
        except Exception as e:
            self.logger.error(f"Manual deployment failed: {e}")
            return False
    
    def manual_rollback(self, instance_id: str, backup_id: str) -> bool:
        """
        Manually rollback an instance to a previous backup
        
        Args:
            instance_id: AMP instance ID
            backup_id: Backup ID to restore
            
        Returns:
            True if successful
        """
        return self.amp_deployer.rollback_plugin(instance_id, backup_id)
    
    def list_instance_backups(self, instance_id: str) -> List[Dict[str, Any]]:
        """List all backups for an instance"""
        return self.amp_client.list_backups(instance_id)
    
    def get_all_instances(self) -> List[Dict[str, Any]]:
        """Get all AMP instances"""
        return self.amp_client.get_instances()


async def main():
    """
    Main entry point for automation system
    
    Run this via systemd timer or cron for hourly updates
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/var/log/archivesmp/plugin-automation.log'),
            logging.StreamHandler()
        ]
    )
    
    # Load configuration
    config = {
        'amp_url': 'http://localhost:8080',  # AMP panel URL
        'amp_username': 'admin',  # AMP admin username  
        'amp_password': 'password',  # AMP admin password
        'plugin_registry_path': '/etc/archivesmp/plugin_registry.yaml',
        'staging_path': '/var/lib/archivesmp/plugin-staging',
        'excel_matrix_path': '/var/lib/archivesmp/deployment_matrix.csv',
        'excel_output_path': '/var/lib/archivesmp/reports/plugin_updates.xlsx',
        'dev_instance_id': None  # Set to DEV01's AMP instance ID
    }
    
    # Initialize automation
    automation = AutomatedPluginManager(config)
    
    # Run hourly cycle
    await automation.run_hourly_cycle()


if __name__ == "__main__":
    asyncio.run(main())
