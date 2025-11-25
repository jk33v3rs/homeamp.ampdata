"""
Config File Backup System
Purpose: Create, manage, and restore backups of config files before modifications
Author: AI Assistant
Date: 2025-01-04
Related Todos: #34, #35, #36, #37, #38

Provides automatic backup before config changes with rollback capability.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import shutil
import logging
import mysql.connector

logger = logging.getLogger(__name__)


class ConfigBackup:
    """
    Manages config file backups with database tracking.

    Example usage:
        backup = ConfigBackup(db_connection)
        backup_id = backup.create_backup(
            config_file_id=123,
            instance_id='BENT01',
            file_path='/path/to/config.yml',
            reason='before_change'
        )
        # ... make changes ...
        if something_went_wrong:
            backup.restore_backup(backup_id)
    """

    def __init__(self, db_connection):
        """
        Initialize backup manager.

        Args:
            db_connection: mysql.connector connection object
        """
        self.conn = db_connection

    def create_backup(
        self,
        config_file_id: int,
        instance_id: str,
        file_path: str,
        reason: str = "manual",
        backed_up_by: Optional[str] = "system",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        Create a full snapshot backup of a config file.

        Args:
            config_file_id: ID from endpoint_config_files table
            instance_id: Instance ID
            file_path: Absolute path to config file
            reason: 'before_change', 'scheduled', 'manual', 'pre_migration', 'pre_deployment'
            backed_up_by: User or system identifier
            metadata: Optional JSON metadata

        Returns:
            backup_id if successful, None on error
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            logger.error(f"Cannot backup - file not found: {file_path}")
            return None

        try:
            # Read file content
            with open(file_path_obj, "r", encoding="utf-8") as f:
                content = f.read()

            # Calculate hash
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Extract plugin_id from config_file record
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("SELECT plugin_id FROM endpoint_config_files WHERE id = %s", (config_file_id,))
            result = cursor.fetchone()
            plugin_id = result["plugin_id"] if result else None

            # Insert backup
            import json

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute(
                """
                INSERT INTO endpoint_config_backups 
                (config_file_id, instance_id, plugin_id, config_file_path, 
                 file_content, file_hash, backed_up_by, backup_reason, backup_metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    config_file_id,
                    instance_id,
                    plugin_id,
                    str(file_path),
                    content,
                    file_hash,
                    backed_up_by,
                    reason,
                    metadata_json,
                ),
            )

            self.conn.commit()
            backup_id = cursor.lastrowid
            cursor.close()

            logger.info(f"Created backup {backup_id} for {file_path} (reason: {reason})")
            return backup_id

        except Exception as e:
            logger.error(f"Error creating backup for {file_path}: {e}")
            self.conn.rollback()
            return None

    def restore_backup(self, backup_id: int, restore_to_path: Optional[str] = None) -> bool:
        """
        Restore a config file from backup.

        Args:
            backup_id: ID from endpoint_config_backups table
            restore_to_path: Optional different path (default: original path)

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT config_file_path, file_content, file_hash
                FROM endpoint_config_backups
                WHERE backup_id = %s
            """,
                (backup_id,),
            )

            backup = cursor.fetchone()
            cursor.close()

            if not backup:
                logger.error(f"Backup {backup_id} not found")
                return False

            # Determine restore path
            target_path = Path(restore_to_path) if restore_to_path else Path(backup["config_file_path"])

            # Create parent directories
            target_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(backup["file_content"])

            # Verify hash
            with open(target_path, "r", encoding="utf-8") as f:
                restored_content = f.read()
            restored_hash = hashlib.sha256(restored_content.encode("utf-8")).hexdigest()

            if restored_hash != backup["file_hash"]:
                logger.error(f"Hash mismatch after restore! Expected {backup['file_hash']}, got {restored_hash}")
                return False

            logger.info(f"Successfully restored backup {backup_id} to {target_path}")
            return True

        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}")
            return False

    def list_backups(
        self,
        config_file_id: Optional[int] = None,
        instance_id: Optional[str] = None,
        plugin_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        List backups with optional filtering.

        Args:
            config_file_id: Filter by specific config file
            instance_id: Filter by instance
            plugin_id: Filter by plugin
            limit: Maximum results (default 50)

        Returns:
            List of backup records
        """
        try:
            cursor = self.conn.cursor(dictionary=True)

            query = """
                SELECT 
                    backup_id, config_file_id, instance_id, plugin_id,
                    config_file_path, file_hash, backed_up_at, backed_up_by,
                    backup_reason, backup_metadata,
                    LENGTH(file_content) as file_size_bytes
                FROM endpoint_config_backups
                WHERE 1=1
            """
            params = []

            if config_file_id:
                query += " AND config_file_id = %s"
                params.append(config_file_id)

            if instance_id:
                query += " AND instance_id = %s"
                params.append(instance_id)

            if plugin_id:
                query += " AND plugin_id = %s"
                params.append(plugin_id)

            query += " ORDER BY backed_up_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, tuple(params))
            backups = cursor.fetchall()
            cursor.close()

            return backups

        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []

    def get_latest_backup(self, config_file_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the most recent backup for a config file.

        Args:
            config_file_id: Config file ID

        Returns:
            Backup record dict or None
        """
        backups = self.list_backups(config_file_id=config_file_id, limit=1)
        return backups[0] if backups else None

    def prune_old_backups(self, config_file_id: int, keep_count: int = 10, keep_days: int = 30) -> int:
        """
        Delete old backups to save space.

        Strategy:
        - Keep last {keep_count} backups
        - Keep all backups from last {keep_days} days
        - Delete everything else

        Args:
            config_file_id: Config file to prune
            keep_count: Number of recent backups to keep
            keep_days: Days of backups to keep

        Returns:
            Number of backups deleted
        """
        try:
            cursor = self.conn.cursor()

            # Delete old backups not in the keep set
            cutoff_date = datetime.now() - timedelta(days=keep_days)

            cursor.execute(
                """
                DELETE FROM endpoint_config_backups
                WHERE config_file_id = %s
                  AND backed_up_at < %s
                  AND backup_id NOT IN (
                      SELECT backup_id FROM (
                          SELECT backup_id
                          FROM endpoint_config_backups
                          WHERE config_file_id = %s
                          ORDER BY backed_up_at DESC
                          LIMIT %s
                      ) AS recent_backups
                  )
            """,
                (config_file_id, cutoff_date, config_file_id, keep_count),
            )

            deleted_count = cursor.rowcount
            self.conn.commit()
            cursor.close()

            if deleted_count > 0:
                logger.info(f"Pruned {deleted_count} old backups for config_file {config_file_id}")

            return deleted_count

        except Exception as e:
            logger.error(f"Error pruning backups: {e}")
            self.conn.rollback()
            return 0

    def prune_all_old_backups(self, keep_count: int = 10, keep_days: int = 30) -> int:
        """
        Prune old backups for all config files.

        Args:
            keep_count: Recent backups to keep per file
            keep_days: Days to keep

        Returns:
            Total backups deleted
        """
        try:
            # Get all unique config_file_ids
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT config_file_id FROM endpoint_config_backups")
            config_file_ids = [row[0] for row in cursor.fetchall()]
            cursor.close()

            total_deleted = 0
            for config_file_id in config_file_ids:
                deleted = self.prune_old_backups(config_file_id, keep_count, keep_days)
                total_deleted += deleted

            logger.info(f"Pruned {total_deleted} total old backups across all files")
            return total_deleted

        except Exception as e:
            logger.error(f"Error in bulk backup pruning: {e}")
            return 0


# Convenience functions
def create_backup(
    db_connection, config_file_id: int, instance_id: str, file_path: str, reason: str = "manual"
) -> Optional[int]:
    """Create a backup and return backup_id."""
    backup_mgr = ConfigBackup(db_connection)
    return backup_mgr.create_backup(config_file_id, instance_id, file_path, reason)


def restore_backup(db_connection, backup_id: int) -> bool:
    """Restore a backup by ID."""
    backup_mgr = ConfigBackup(db_connection)
    return backup_mgr.restore_backup(backup_id)
