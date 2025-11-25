"""
Conflict Detection for ArchiveSMP Config Manager

Detects concurrent configuration changes and conflicts
"""

import mariadb
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger("conflict_detector")


class ConflictDetector:
    """Detects and manages configuration conflicts"""

    def __init__(self, db_connection):
        """
        Initialize conflict detector

        Args:
            db_connection: MariaDB connection
        """
        self.db = db_connection
        self.cursor = db_connection.cursor(dictionary=True)

    def check_concurrent_changes(
        self, instance_id: str, plugin_name: str, config_key: str, window_minutes: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Check for concurrent changes to same config key

        Args:
            instance_id: Instance ID
            plugin_name: Plugin name
            config_key: Config key path
            window_minutes: Time window to check

        Returns:
            List of conflicting changes
        """
        query = """
            SELECT * FROM config_change_history
            WHERE instance_id = %s
            AND plugin_name = %s
            AND config_key = %s
            AND changed_at > DATE_SUB(NOW(), INTERVAL %s MINUTE)
            ORDER BY changed_at DESC
        """

        self.cursor.execute(query, (instance_id, plugin_name, config_key, window_minutes))

        changes = self.cursor.fetchall()

        if len(changes) > 1:
            logger.warning(
                f"Detected {len(changes)} concurrent changes to " f"{plugin_name}/{config_key} on {instance_id}"
            )

        return changes

    def detect_conflicts(self, pending_change: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect if a pending change conflicts with recent changes

        Args:
            pending_change: Change to validate
                - instance_id
                - plugin_name
                - config_key
                - new_value
                - changed_by

        Returns:
            Conflict details or None
        """
        # Check for recent changes
        recent_changes = self.check_concurrent_changes(
            instance_id=pending_change["instance_id"],
            plugin_name=pending_change["plugin_name"],
            config_key=pending_change["config_key"],
            window_minutes=5,
        )

        if not recent_changes:
            return None

        # Check if different user made change
        for change in recent_changes:
            if change["changed_by"] != pending_change.get("changed_by"):
                return {
                    "conflict_type": "concurrent_user",
                    "conflicting_change": change,
                    "pending_change": pending_change,
                    "message": f"User {change['changed_by']} modified this config {self._time_ago(change['changed_at'])} ago",
                }

        # Check if value differs
        if recent_changes[0]["new_value"] != pending_change.get("old_value"):
            return {
                "conflict_type": "stale_value",
                "conflicting_change": recent_changes[0],
                "pending_change": pending_change,
                "message": "Config value changed since you started editing",
            }

        return None

    def check_deployment_conflicts(self, instance_id: str, plugin_name: str) -> List[Dict[str, Any]]:
        """
        Check for conflicting pending deployments

        Args:
            instance_id: Instance ID
            plugin_name: Plugin name

        Returns:
            List of conflicting deployments
        """
        query = """
            SELECT * FROM deployment_queue
            WHERE instance_id = %s
            AND plugin_name = %s
            AND status = 'pending'
            ORDER BY created_at
        """

        self.cursor.execute(query, (instance_id, plugin_name))
        return self.cursor.fetchall()

    def lock_config(
        self, instance_id: str, plugin_name: str, config_key: str, locked_by: str, lock_duration_minutes: int = 10
    ) -> bool:
        """
        Lock a config key for editing

        Args:
            instance_id: Instance ID
            plugin_name: Plugin name
            config_key: Config key to lock
            locked_by: Username acquiring lock
            lock_duration_minutes: How long to hold lock

        Returns:
            True if lock acquired
        """
        # Check existing locks
        query = """
            SELECT * FROM config_locks
            WHERE instance_id = %s
            AND plugin_name = %s
            AND config_key = %s
            AND locked_until > NOW()
        """

        self.cursor.execute(query, (instance_id, plugin_name, config_key))
        existing_lock = self.cursor.fetchone()

        if existing_lock:
            if existing_lock["locked_by"] == locked_by:
                # Extend own lock
                query = """
                    UPDATE config_locks
                    SET locked_until = DATE_ADD(NOW(), INTERVAL %s MINUTE)
                    WHERE lock_id = %s
                """
                self.cursor.execute(query, (lock_duration_minutes, existing_lock["lock_id"]))
                self.db.commit()
                return True
            else:
                logger.warning(
                    f"Config locked by {existing_lock['locked_by']} " f"until {existing_lock['locked_until']}"
                )
                return False

        # Create new lock
        query = """
            INSERT INTO config_locks (
                instance_id,
                plugin_name,
                config_key,
                locked_by,
                locked_at,
                locked_until
            ) VALUES (
                %s, %s, %s, %s, NOW(),
                DATE_ADD(NOW(), INTERVAL %s MINUTE)
            )
        """

        self.cursor.execute(query, (instance_id, plugin_name, config_key, locked_by, lock_duration_minutes))

        self.db.commit()
        logger.info(f"Acquired lock on {plugin_name}/{config_key} for {locked_by}")
        return True

    def release_lock(self, instance_id: str, plugin_name: str, config_key: str, locked_by: str) -> bool:
        """
        Release a config lock

        Args:
            instance_id: Instance ID
            plugin_name: Plugin name
            config_key: Config key
            locked_by: Username releasing lock

        Returns:
            True if lock released
        """
        query = """
            DELETE FROM config_locks
            WHERE instance_id = %s
            AND plugin_name = %s
            AND config_key = %s
            AND locked_by = %s
        """

        self.cursor.execute(query, (instance_id, plugin_name, config_key, locked_by))
        self.db.commit()

        if self.cursor.rowcount > 0:
            logger.info(f"Released lock on {plugin_name}/{config_key}")
            return True

        return False

    def cleanup_expired_locks(self) -> int:
        """
        Remove expired locks

        Returns:
            Number of locks removed
        """
        query = "DELETE FROM config_locks WHERE locked_until < NOW()"
        self.cursor.execute(query)
        self.db.commit()

        count = self.cursor.rowcount
        if count > 0:
            logger.info(f"Cleaned up {count} expired locks")

        return count

    def get_active_locks(self, instance_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get currently active locks

        Args:
            instance_id: Optional filter by instance

        Returns:
            List of active locks
        """
        query = "SELECT * FROM config_locks WHERE locked_until > NOW()"
        params = []

        if instance_id:
            query += " AND instance_id = %s"
            params.append(instance_id)

        query += " ORDER BY locked_at DESC"

        self.cursor.execute(query, params if params else None)
        return self.cursor.fetchall()

    def _time_ago(self, timestamp: datetime) -> str:
        """Format timestamp as relative time"""
        delta = datetime.now() - timestamp

        if delta.days > 0:
            return f"{delta.days} day{'s' if delta.days != 1 else ''}"
        elif delta.seconds >= 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        elif delta.seconds >= 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            return "moments"


# Create table for locks if not exists
CREATE_LOCKS_TABLE = """
CREATE TABLE IF NOT EXISTS config_locks (
    lock_id INT AUTO_INCREMENT PRIMARY KEY,
    instance_id VARCHAR(50) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    locked_by VARCHAR(50) NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    locked_until TIMESTAMP NOT NULL,
    INDEX idx_lock_key (instance_id, plugin_name, config_key),
    INDEX idx_lock_expiry (locked_until)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def create_conflict_detector(db_connection) -> ConflictDetector:
    """Factory function to create conflict detector"""
    cursor = db_connection.cursor()
    cursor.execute(CREATE_LOCKS_TABLE)
    db_connection.commit()
    cursor.close()

    return ConflictDetector(db_connection)
