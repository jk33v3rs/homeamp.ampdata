"""
Enhanced Discovery Integration for Agent Service

Integrates variance detection, server properties scanning, and datapack discovery
into the agent's main loop.
"""

import logging
import mysql.connector
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from ..api.db_config import get_db_connection
from .variance_detector import VarianceDetector
from .server_properties_scanner import ServerPropertiesScanner
from .datapack_discovery import DatapackDiscovery


class EnhancedDiscovery:
    """
    Enhanced discovery integration for agent service
    
    Runs periodic scans for:
    - Config variances (instance configs vs baselines)
    - Server properties differences
    - Datapack presence and versions
    """
    
    def __init__(self, db_config: Dict[str, Any], logger: logging.Logger = None):
        """
        Initialize enhanced discovery
        
        Args:
            db_config: Database connection parameters (host, port, user, password, database)
            logger: Optional logger instance
        """
        self.db_config = db_config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize discovery modules
        self.variance_detector = VarianceDetector(db_config, logger)
        self.server_props_scanner = ServerPropertiesScanner(db_config, logger)
        self.datapack_discovery = DatapackDiscovery(db_config, logger)
    
    def run_full_discovery(self, instances: List[Dict[str, Any]], plugins: List[str]) -> Dict[str, Any]:
        """
        Run complete enhanced discovery scan
        
        Args:
            instances: List of instance dictionaries with keys: id, name, instance_path, online_status
            plugins: List of plugin names to scan
            
        Returns:
            Dictionary with discovery results and counts
        """
        self.logger.info("Starting enhanced discovery scan...")
        results = {
            'started_at': datetime.now().isoformat(),
            'instance_count': len(instances),
            'plugin_count': len(plugins),
            'variances_found': 0,
            'server_props_scanned': 0,
            'datapacks_found': 0,
            'errors': []
        }
        
        try:
            # Phase 1: Config variance detection
            self.logger.info("Phase 1: Scanning config variances...")
            variance_count = self.variance_detector.scan_and_register_all(instances, plugins)
            results['variances_found'] = variance_count
            self.logger.info(f"Found {variance_count} config variances")
            
        except Exception as e:
            error_msg = f"Config variance detection failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        try:
            # Phase 2: Server properties scanning
            self.logger.info("Phase 2: Scanning server properties...")
            props_count = self.server_props_scanner.scan_all_instances(instances)
            results['server_props_scanned'] = props_count
            self.logger.info(f"Scanned {props_count} server.properties files")
            
        except Exception as e:
            error_msg = f"Server properties scan failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        try:
            # Phase 3: Datapack discovery
            self.logger.info("Phase 3: Discovering datapacks...")
            datapack_count = self.datapack_discovery.scan_and_register_all(instances)
            results['datapacks_found'] = datapack_count
            self.logger.info(f"Found {datapack_count} datapacks")
            
        except Exception as e:
            error_msg = f"Datapack discovery failed: {e}"
            self.logger.error(error_msg, exc_info=True)
            results['errors'].append(error_msg)
        
        results['completed_at'] = datetime.now().isoformat()
        results['success'] = len(results['errors']) == 0
        
        self.logger.info(f"Enhanced discovery complete: {variance_count} variances, "
                        f"{props_count} properties, {datapack_count} datapacks")
        
        return results
    
    def update_heartbeat(self, agent_id: str, server_name: str, status: str = 'online'):
        """
        Update agent heartbeat in database
        
        Args:
            agent_id: Unique agent identifier (e.g., 'hetzner-xeon')
            server_name: Human-readable server name
            status: Agent status ('online' or 'offline')
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Upsert heartbeat
            query = """
                INSERT INTO agent_heartbeats (agent_id, server_name, last_heartbeat, status)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    server_name = VALUES(server_name),
                    last_heartbeat = VALUES(last_heartbeat),
                    status = VALUES(status)
            """
            cursor.execute(query, (agent_id, server_name, datetime.now(), status))
            conn.commit()
            
            self.logger.debug(f"Updated heartbeat for agent {agent_id}")
            
        except mysql.connector.Error as e:
            self.logger.error(f"Failed to update heartbeat: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()


class HeartbeatMonitor:
    """
    Standalone heartbeat monitor for agent service
    
    Can be used to just update heartbeats without running full discovery
    """
    
    def __init__(self, db_config: Dict[str, Any], agent_id: str, server_name: str, 
                 logger: logging.Logger = None):
        """
        Initialize heartbeat monitor
        
        Args:
            db_config: Database connection parameters
            agent_id: Unique agent identifier
            server_name: Human-readable server name
            logger: Optional logger instance
        """
        self.db_config = db_config
        self.agent_id = agent_id
        self.server_name = server_name
        self.logger = logger or logging.getLogger(__name__)
    
    def update(self, status: str = 'online'):
        """
        Update heartbeat timestamp
        
        Args:
            status: Agent status ('online' or 'offline')
        """
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                INSERT INTO agent_heartbeats (agent_id, server_name, last_heartbeat, status)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    last_heartbeat = VALUES(last_heartbeat),
                    status = VALUES(status)
            """
            cursor.execute(query, (self.agent_id, self.server_name, datetime.now(), status))
            conn.commit()
            
            self.logger.debug(f"Heartbeat updated: {self.agent_id} - {status}")
            
        except mysql.connector.Error as e:
            self.logger.error(f"Heartbeat update failed: {e}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()
