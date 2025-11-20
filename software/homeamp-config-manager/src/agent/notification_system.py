"""
Notification System for ArchiveSMP Config Manager

Handles notifications for:
- Configuration drift detection
- Plugin version updates available
- Deployment approvals needed
- System health alerts
- Deployment completion
"""

import mariadb
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import json
import logging

logger = logging.getLogger("notification_system")


class NotificationType(Enum):
    """Notification types"""
    DRIFT_DETECTED = "drift_detected"
    UPDATE_AVAILABLE = "update_available"
    APPROVAL_NEEDED = "approval_needed"
    DEPLOYMENT_SUCCESS = "deployment_success"
    DEPLOYMENT_FAILURE = "deployment_failure"
    HEALTH_ALERT = "health_alert"
    CONFIG_CHANGE = "config_change"


class NotificationPriority(Enum):
    """Notification priorities"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Notification delivery channels"""
    DATABASE = "database"  # Always stored
    WEBHOOK = "webhook"    # Future: Discord/Slack webhooks
    EMAIL = "email"        # Future: Email notifications
    WEB_UI = "web_ui"      # Real-time UI updates


class NotificationSystem:
    """Manages notification creation, storage, and delivery"""
    
    def __init__(self, db_connection):
        """
        Initialize notification system
        
        Args:
            db_connection: MariaDB connection object
        """
        self.db = db_connection
        self.cursor = db_connection.cursor(dictionary=True)
    
    def create_notification(
        self,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        channels: List[NotificationChannel] = None
    ) -> int:
        """
        Create a new notification
        
        Args:
            notification_type: Type of notification
            title: Short notification title
            message: Detailed notification message
            priority: Notification priority level
            related_entity_type: Type of related entity (instance, plugin, deployment, etc.)
            related_entity_id: ID of related entity
            metadata: Additional structured data
            channels: Delivery channels (defaults to [DATABASE, WEB_UI])
        
        Returns:
            Notification ID
        """
        if channels is None:
            channels = [NotificationChannel.DATABASE, NotificationChannel.WEB_UI]
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        query = """
            INSERT INTO notification_log (
                notification_type,
                title,
                message,
                priority,
                related_entity_type,
                related_entity_id,
                metadata,
                channels,
                status,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
        """
        
        self.cursor.execute(query, (
            notification_type.value,
            title,
            message,
            priority.value,
            related_entity_type,
            related_entity_id,
            metadata_json,
            ','.join([c.value for c in channels])
        ))
        
        self.db.commit()
        notification_id = self.cursor.lastrowid
        
        logger.info(f"Created notification {notification_id}: {title}")
        
        # Mark as sent (since we're only storing in DB for now)
        self._mark_sent(notification_id)
        
        return notification_id
    
    def _mark_sent(self, notification_id: int):
        """Mark notification as sent"""
        query = """
            UPDATE notification_log
            SET status = 'sent', sent_at = NOW()
            WHERE id = %s
        """
        self.cursor.execute(query, (notification_id,))
        self.db.commit()
    
    def mark_read(self, notification_id: int, read_by: str):
        """
        Mark notification as read
        
        Args:
            notification_id: Notification ID
            read_by: Username who read the notification
        """
        query = """
            UPDATE notification_log
            SET read_at = NOW(), read_by = %s
            WHERE id = %s
        """
        self.cursor.execute(query, (read_by, notification_id))
        self.db.commit()
        logger.info(f"Notification {notification_id} marked as read by {read_by}")
    
    def get_unread_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get unread notifications
        
        Args:
            limit: Maximum number of notifications to return
        
        Returns:
            List of unread notifications
        """
        query = """
            SELECT * FROM notification_log
            WHERE read_at IS NULL
            ORDER BY created_at DESC
            LIMIT %s
        """
        self.cursor.execute(query, (limit,))
        return self.cursor.fetchall()
    
    def get_notifications_by_type(
        self,
        notification_type: NotificationType,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notifications by type
        
        Args:
            notification_type: Type of notification
            limit: Maximum number to return
        
        Returns:
            List of notifications
        """
        query = """
            SELECT * FROM notification_log
            WHERE notification_type = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        self.cursor.execute(query, (notification_type.value, limit))
        return self.cursor.fetchall()
    
    def get_notifications_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get notifications related to a specific entity
        
        Args:
            entity_type: Type of entity (instance, plugin, deployment, etc.)
            entity_id: Entity ID
            limit: Maximum number to return
        
        Returns:
            List of notifications
        """
        query = """
            SELECT * FROM notification_log
            WHERE related_entity_type = %s AND related_entity_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        self.cursor.execute(query, (entity_type, entity_id, limit))
        return self.cursor.fetchall()
    
    # ========================================================================
    # CONVENIENCE METHODS FOR COMMON NOTIFICATIONS
    # ========================================================================
    
    def notify_drift_detected(
        self,
        instance_id: str,
        plugin_name: str,
        drift_count: int,
        variance_details: Dict[str, Any]
    ) -> int:
        """Notify about configuration drift detection"""
        return self.create_notification(
            notification_type=NotificationType.DRIFT_DETECTED,
            title=f"Config drift detected: {plugin_name} on {instance_id}",
            message=f"Detected {drift_count} configuration variances from baseline",
            priority=NotificationPriority.MEDIUM,
            related_entity_type="instance",
            related_entity_id=instance_id,
            metadata={
                "plugin_name": plugin_name,
                "drift_count": drift_count,
                "variances": variance_details
            }
        )
    
    def notify_update_available(
        self,
        plugin_name: str,
        current_version: str,
        latest_version: str,
        affected_instances: List[str]
    ) -> int:
        """Notify about plugin update availability"""
        return self.create_notification(
            notification_type=NotificationType.UPDATE_AVAILABLE,
            title=f"Update available: {plugin_name} {latest_version}",
            message=f"New version {latest_version} available (currently on {current_version})",
            priority=NotificationPriority.LOW,
            related_entity_type="plugin",
            related_entity_id=plugin_name,
            metadata={
                "current_version": current_version,
                "latest_version": latest_version,
                "affected_instances": affected_instances,
                "instance_count": len(affected_instances)
            }
        )
    
    def notify_approval_needed(
        self,
        change_type: str,
        change_description: str,
        requested_by: str,
        approval_id: int
    ) -> int:
        """Notify about pending approval request"""
        return self.create_notification(
            notification_type=NotificationType.APPROVAL_NEEDED,
            title=f"Approval needed: {change_type}",
            message=change_description,
            priority=NotificationPriority.HIGH,
            related_entity_type="approval",
            related_entity_id=str(approval_id),
            metadata={
                "change_type": change_type,
                "requested_by": requested_by,
                "approval_id": approval_id
            }
        )
    
    def notify_deployment_success(
        self,
        deployment_id: int,
        deployment_type: str,
        target_instances: List[str]
    ) -> int:
        """Notify about successful deployment"""
        return self.create_notification(
            notification_type=NotificationType.DEPLOYMENT_SUCCESS,
            title=f"Deployment completed: {deployment_type}",
            message=f"Successfully deployed to {len(target_instances)} instance(s)",
            priority=NotificationPriority.MEDIUM,
            related_entity_type="deployment",
            related_entity_id=str(deployment_id),
            metadata={
                "deployment_id": deployment_id,
                "deployment_type": deployment_type,
                "target_instances": target_instances,
                "instance_count": len(target_instances)
            }
        )
    
    def notify_deployment_failure(
        self,
        deployment_id: int,
        deployment_type: str,
        error_message: str,
        failed_instances: List[str]
    ) -> int:
        """Notify about deployment failure"""
        return self.create_notification(
            notification_type=NotificationType.DEPLOYMENT_FAILURE,
            title=f"Deployment failed: {deployment_type}",
            message=f"Deployment failed on {len(failed_instances)} instance(s): {error_message}",
            priority=NotificationPriority.CRITICAL,
            related_entity_type="deployment",
            related_entity_id=str(deployment_id),
            metadata={
                "deployment_id": deployment_id,
                "deployment_type": deployment_type,
                "error_message": error_message,
                "failed_instances": failed_instances,
                "instance_count": len(failed_instances)
            }
        )
    
    def notify_health_alert(
        self,
        alert_type: str,
        alert_message: str,
        severity: NotificationPriority = NotificationPriority.HIGH,
        system_component: Optional[str] = None
    ) -> int:
        """Notify about system health alert"""
        return self.create_notification(
            notification_type=NotificationType.HEALTH_ALERT,
            title=f"Health alert: {alert_type}",
            message=alert_message,
            priority=severity,
            related_entity_type="system",
            related_entity_id=system_component,
            metadata={
                "alert_type": alert_type,
                "system_component": system_component
            }
        )
    
    def notify_config_change(
        self,
        instance_id: str,
        plugin_name: str,
        config_key: str,
        old_value: Any,
        new_value: Any,
        changed_by: str
    ) -> int:
        """Notify about manual configuration change"""
        return self.create_notification(
            notification_type=NotificationType.CONFIG_CHANGE,
            title=f"Config changed: {plugin_name}/{config_key}",
            message=f"Changed by {changed_by} on {instance_id}",
            priority=NotificationPriority.LOW,
            related_entity_type="instance",
            related_entity_id=instance_id,
            metadata={
                "plugin_name": plugin_name,
                "config_key": config_key,
                "old_value": str(old_value),
                "new_value": str(new_value),
                "changed_by": changed_by
            }
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_notification_system(db_connection) -> NotificationSystem:
    """
    Factory function to create notification system instance
    
    Args:
        db_connection: MariaDB connection
    
    Returns:
        NotificationSystem instance
    """
    return NotificationSystem(db_connection)
