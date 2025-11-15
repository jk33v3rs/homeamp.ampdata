"""
Configuration Management Endpoint Agent (Database-backed)

Runs on each physical server (Hetzner/OVH) to:
1. Discover local AMP instances
2. Scan plugin configurations
3. Report to central database
4. Apply configuration changes from database
"""

import time
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..database.db_access import ConfigDatabase
from ..amp_integration.instance_scanner import AMPInstanceScanner
from ..analyzers.config_reader import PluginConfigReader


class EndpointAgent:
    """
    Lightweight agent that runs on each physical server.
    Reports instance state to central database.
    """
    
    def __init__(self, server_name: str, db_config: Dict[str, Any]):
        """
        Args:
            server_name: Physical server name ('hetzner-xeon' or 'ovh-ryzen')
            db_config: Database connection config (host, port, user, password)
        """
        self.server_name = server_name
        self.db = ConfigDatabase(**db_config)
        
        # Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f'endpoint-agent-{server_name}')
        
        # AMP instance discovery
        self.amp_base_dir = Path("/home/amp/.ampdata/instances")
        self.scanner = AMPInstanceScanner(self.amp_base_dir)
        
        self.running = False
    
    def start(self):
        """Start agent main loop"""
        self.logger.info(f"Starting endpoint agent for {self.server_name}")
        self.db.connect()
        self.running = True
        
        try:
            while self.running:
                self._run_cycle()
                time.sleep(60)  # Run every minute
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("Shutting down agent")
        self.running = False
        self.db.disconnect()
    
    def _run_cycle(self):
        """Execute one agent cycle"""
        try:
            # 1. Discover instances
            discovered = self.scanner.discover_instances()
            self.logger.info(f"Discovered {len(discovered)} instances")
            
            # 2. Get expected instances from database
            expected_instances = self.db.get_instances_by_server(self.server_name)
            expected_ids = {inst['instance_id'] for inst in expected_instances}
            
            # 3. Check for missing instances
            discovered_ids = {inst['name'] for inst in discovered}
            missing = expected_ids - discovered_ids
            unexpected = discovered_ids - expected_ids
            
            if missing:
                self.logger.warning(f"Missing instances: {missing}")
            if unexpected:
                self.logger.info(f"Unexpected instances: {unexpected}")
            
            # 4. Scan configs for each instance
            for instance in discovered:
                if instance['name'] in expected_ids:
                    self._scan_instance_configs(instance)
        
        except Exception as e:
            self.logger.error(f"Error in agent cycle: {e}", exc_info=True)
    
    def _scan_instance_configs(self, instance: Dict[str, Any]):
        """Scan plugin configs for a single instance"""
        instance_id = instance['name']
        plugins_dir = Path(instance['path']) / 'Minecraft' / 'plugins'
        
        if not plugins_dir.exists():
            return
        
        # Scan all plugin config files
        config_reader = PluginConfigReader(plugins_dir)
        configs = config_reader.read_all_configs()
        
        # Compare against database expectations
        self._check_drift(instance_id, configs)
    
    def _check_drift(self, instance_id: str, actual_configs: Dict[str, Dict]):
        """
        Compare actual configs against database rules
        
        Args:
            instance_id: Instance identifier
            actual_configs: {plugin_name: {config_file: {key: value}}}
        """
        # For each plugin config key, resolve expected value from database
        for plugin_name, files in actual_configs.items():
            for config_file, keys in files.items():
                for config_key, actual_value in keys.items():
                    # Resolve expected value using hierarchy
                    expected_value, priority, scope = self.db.resolve_config_value(
                        instance_id, plugin_name, config_file, config_key
                    )
                    
                    # Substitute variables
                    if expected_value:
                        expected_value = self.db.substitute_variables(expected_value, instance_id)
                    
                    # Check for drift
                    if expected_value is not None and actual_value != expected_value:
                        self.logger.warning(
                            f"DRIFT {instance_id}/{plugin_name}/{config_file}:{config_key} "
                            f"- Expected: {expected_value} (from {scope}), "
                            f"Got: {actual_value}"
                        )


def main():
    """Entry point for systemd service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ArchiveSMP Endpoint Agent')
    parser.add_argument('--server', required=True, help='Server name (hetzner-xeon or ovh-ryzen)')
    parser.add_argument('--db-host', required=True, help='Database host')
    parser.add_argument('--db-port', type=int, default=3369, help='Database port')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'port': args.db_port,
        'user': args.db_user,
        'password': args.db_password
    }
    
    agent = EndpointAgent(args.server, db_config)
    agent.start()


if __name__ == '__main__':
    main()
