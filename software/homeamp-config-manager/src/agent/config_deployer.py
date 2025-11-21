"""
Config Deployer - Handles deployment of configurations to instances
Resolves placeholders and writes configs to instance directories
"""

import os
import re
import logging
from typing import Dict, List, Optional
from datetime import datetime
import mysql.connector
from pathlib import Path

from ..core.settings import get_settings
from ..api.db_config import get_db_connection

logger = logging.getLogger(__name__)


class ConfigDeployer:
    """
    Handles config deployment to instances
    - Resolves placeholders (%SERVER_NAME%, %INSTANCE_NAME%, %INSTANCE_SHORT%)
    - Writes configs to instance plugin directories
    - Logs deployment status to database
    """

    def __init__(self):
        self.settings = get_settings()
        self.placeholder_patterns = {
            '%SERVER_NAME%': lambda inst: inst['server_name'],
            '%INSTANCE_NAME%': lambda inst: inst['instance_name'],
            '%INSTANCE_SHORT%': lambda inst: self._get_instance_short(inst['instance_name'])
        }

    def _get_instance_short(self, instance_name: str) -> str:
        """
        Extract short name from instance name
        Example: 'PRI01-Survival' -> 'PRI01'
        """
        return instance_name.split('-')[0] if '-' in instance_name else instance_name

    def _get_db_connection(self):
        """Get database connection"""
        return get_db_connection()

    def receive_deployment(
        self,
        deployment_id: int,
        plugin_name: str,
        config_yaml: str,
        instance_ids: List[int],
        resolve_placeholders: bool = True
    ) -> Dict[str, any]:
        """
        Receive deployment request from API
        Process and deploy to all target instances

        Args:
            deployment_id: Unique deployment ID from deployment_queue
            plugin_name: Name of plugin to deploy config for
            config_yaml: YAML configuration content
            instance_ids: List of instance IDs to deploy to
            resolve_placeholders: Whether to resolve placeholder variables

        Returns:
            Dict with deployment results
        """
        logger.info(f"Received deployment {deployment_id} for {plugin_name} to {len(instance_ids)} instances")

        results = {
            'deployment_id': deployment_id,
            'total_instances': len(instance_ids),
            'successful': 0,
            'failed': 0,
            'results': []
        }

        conn = self._get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Update deployment status to 'processing'
            self.update_deployment_status(deployment_id, 'processing', 'Starting deployment')

            for instance_id in instance_ids:
                try:
                    # Get instance data
                    cursor.execute("""
                        SELECT instance_id, instance_name, server_name, instance_path
                        FROM instances
                        WHERE instance_id = %s
                    """, (instance_id,))

                    instance = cursor.fetchone()
                    if not instance:
                        logger.warning(f"Instance {instance_id} not found, skipping")
                        self.log_deployment_event(
                            deployment_id, instance_id, 'failed', f'Instance not found'
                        )
                        results['failed'] += 1
                        continue

                    # Resolve placeholders if needed
                    if resolve_placeholders:
                        resolved_yaml = self.resolve_placeholders(config_yaml, instance)
                    else:
                        resolved_yaml = config_yaml

                    # Write config to instance
                    success = self.write_config_to_instance(
                        instance, plugin_name, resolved_yaml
                    )

                    if success:
                        results['successful'] += 1
                        self.log_deployment_event(
                            deployment_id, instance_id, 'completed',
                            f'Config deployed successfully'
                        )
                        results['results'].append({
                            'instance_id': instance_id,
                            'instance_name': instance['instance_name'],
                            'status': 'success'
                        })
                    else:
                        results['failed'] += 1
                        results['results'].append({
                            'instance_id': instance_id,
                            'instance_name': instance['instance_name'],
                            'status': 'failed'
                        })

                except Exception as e:
                    logger.error(f"Failed to deploy to instance {instance_id}: {e}")
                    self.log_deployment_event(
                        deployment_id, instance_id, 'failed', str(e)
                    )
                    results['failed'] += 1
                    results['results'].append({
                        'instance_id': instance_id,
                        'status': 'error',
                        'error': str(e)
                    })

            # Update final deployment status
            final_status = 'completed' if results['failed'] == 0 else 'partial'
            self.update_deployment_status(
                deployment_id, final_status,
                f"Deployed to {results['successful']}/{results['total_instances']} instances"
            )

        finally:
            cursor.close()
            conn.close()

        return results

    def resolve_placeholders(self, yaml_content: str, instance_data: Dict) -> str:
        """
        Resolve placeholder variables in YAML content

        Placeholders:
            %SERVER_NAME% -> instance.server_name
            %INSTANCE_NAME% -> instance.instance_name
            %INSTANCE_SHORT% -> first part before '-'

        Args:
            yaml_content: YAML string with placeholders
            instance_data: Dict with instance info (server_name, instance_name, etc.)

        Returns:
            YAML string with placeholders resolved
        """
        resolved = yaml_content

        for placeholder, resolver in self.placeholder_patterns.items():
            try:
                value = resolver(instance_data)
                resolved = resolved.replace(placeholder, str(value))
            except Exception as e:
                logger.warning(f"Failed to resolve {placeholder}: {e}")

        return resolved

    def write_config_to_instance(
        self,
        instance: Dict,
        plugin_name: str,
        config_yaml: str
    ) -> bool:
        """
        Write configuration to instance plugin directory

        Args:
            instance: Instance dict with instance_path
            plugin_name: Plugin name (e.g., 'LevelledMobs')
            config_yaml: Resolved YAML content

        Returns:
            True if successful, False otherwise
        """
        try:
            # Construct target path
            instance_path = Path(instance['instance_path'])
            plugin_dir = instance_path / 'plugins' / plugin_name
            config_file = plugin_dir / 'config.yml'

            # Create plugin directory if it doesn't exist
            plugin_dir.mkdir(parents=True, exist_ok=True)

            # Write config file
            config_file.write_text(config_yaml, encoding='utf-8')

            logger.info(f"Wrote config to {config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to write config to {instance['instance_name']}: {e}")
            return False

    def restart_instance_if_required(self, instance_id: int) -> bool:
        """
        Restart instance if required for config changes
        TODO: Implement AMP API integration for instance restart

        Args:
            instance_id: Instance ID to restart

        Returns:
            True if restart initiated, False otherwise
        """
        logger.warning("Instance restart not yet implemented")
        # TODO: Call AMP API to restart instance
        return False

    def update_deployment_status(
        self,
        deployment_id: int,
        status: str,
        message: str
    ):
        """
        Update deployment queue status

        Args:
            deployment_id: Deployment ID
            status: New status ('pending', 'processing', 'completed', 'failed', 'partial')
            message: Status message
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE deployment_queue
                SET status = %s, updated_at = NOW()
                WHERE id = %s
            """, (status, deployment_id))

            conn.commit()
            logger.info(f"Deployment {deployment_id} status updated to {status}: {message}")

        finally:
            cursor.close()
            conn.close()

    def log_deployment_event(
        self,
        deployment_id: int,
        instance_id: int,
        status: str,
        message: str
    ):
        """
        Log deployment event to deployment_logs table

        Args:
            deployment_id: Deployment ID
            instance_id: Instance ID
            status: Event status ('completed', 'failed', 'skipped')
            message: Event message
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO deployment_logs
                (deployment_id, instance_id, status, message, timestamp)
                VALUES (%s, %s, %s, %s, NOW())
            """, (deployment_id, instance_id, status, message))

            conn.commit()

        except Exception as e:
            logger.error(f"Failed to log deployment event: {e}")

        finally:
            cursor.close()
            conn.close()

    def report_deployment_status(
        self,
        deployment_id: int,
        instance_id: int,
        status: str,
        message: str
    ):
        """
        Report deployment status (alias for log_deployment_event)
        """
        self.log_deployment_event(deployment_id, instance_id, status, message)
