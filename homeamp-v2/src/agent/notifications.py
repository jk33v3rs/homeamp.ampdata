"""HomeAMP V2.0 - Notification handler for alerts and events."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class NotificationHandler:
    """Handler for sending notifications via various channels."""

    def __init__(self, settings):
        """Initialize notification handler.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.enabled_channels = []

        # Configure enabled channels
        if settings.discord_webhook_url:
            self.enabled_channels.append("discord")
        if settings.slack_webhook_url:
            self.enabled_channels.append("slack")
        if settings.email_enabled:
            self.enabled_channels.append("email")

        logger.info(f"Notification channels enabled: {self.enabled_channels}")

    def send(
        self,
        message: str,
        severity: str = "info",
        channels: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """Send a notification.

        Args:
            message: Notification message
            severity: Severity level (info, warning, error, critical)
            channels: Specific channels to use (None = all enabled)
            metadata: Additional metadata

        Returns:
            True if at least one channel succeeded
        """
        if channels is None:
            channels = self.enabled_channels

        if not channels:
            logger.debug("No notification channels configured")
            return False

        logger.info(f"Sending {severity} notification: {message}")

        success = False
        for channel in channels:
            try:
                if channel == "discord":
                    self._send_discord(message, severity, metadata)
                    success = True
                elif channel == "slack":
                    self._send_slack(message, severity, metadata)
                    success = True
                elif channel == "email":
                    self._send_email(message, severity, metadata)
                    success = True
                else:
                    logger.warning(f"Unknown notification channel: {channel}")

            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")

        return success

    def _send_discord(self, message: str, severity: str, metadata: Optional[Dict]) -> None:
        """Send Discord notification.

        Args:
            message: Message text
            severity: Severity level
            metadata: Additional metadata
        """
        import httpx

        # Map severity to color
        color_map = {
            "info": 0x3498DB,  # Blue
            "warning": 0xF39C12,  # Orange
            "error": 0xE74C3C,  # Red
            "critical": 0x992D22,  # Dark red
        }

        embed = {
            "title": f"HomeAMP {severity.upper()}",
            "description": message,
            "color": color_map.get(severity, 0x95A5A6),
            "timestamp": datetime.utcnow().isoformat(),
        }

        if metadata:
            fields = []
            for key, value in metadata.items():
                fields.append({"name": key, "value": str(value), "inline": True})
            embed["fields"] = fields

        payload = {"embeds": [embed]}

        response = httpx.post(self.settings.discord_webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.debug("Discord notification sent")

    def _send_slack(self, message: str, severity: str, metadata: Optional[Dict]) -> None:
        """Send Slack notification.

        Args:
            message: Message text
            severity: Severity level
            metadata: Additional metadata
        """
        import httpx

        # Map severity to color
        color_map = {
            "info": "#3498DB",
            "warning": "#F39C12",
            "error": "#E74C3C",
            "critical": "#992D22",
        }

        attachment = {
            "title": f"HomeAMP {severity.upper()}",
            "text": message,
            "color": color_map.get(severity, "#95A5A6"),
            "ts": int(datetime.utcnow().timestamp()),
        }

        if metadata:
            fields = []
            for key, value in metadata.items():
                fields.append({"title": key, "value": str(value), "short": True})
            attachment["fields"] = fields

        payload = {"attachments": [attachment]}

        response = httpx.post(self.settings.slack_webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        logger.debug("Slack notification sent")

    def _send_email(self, message: str, severity: str, metadata: Optional[Dict]) -> None:
        """Send email notification.

        Args:
            message: Message text
            severity: Severity level
            metadata: Additional metadata
        """
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        try:
            if not self.settings.email_enabled:
                logger.debug("Email notifications not enabled")
                return
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{severity.upper()}] HomeAMP Alert"
            msg['From'] = self.settings.email_from
            msg['To'] = self.settings.email_to
            
            # Create plain text and HTML versions
            text_content = f"""
HomeAMP Alert
=============

Severity: {severity.upper()}

Message:
{message}

"""
            
            if metadata:
                text_content += "Details:\n"
                for key, value in metadata.items():
                    text_content += f"  {key}: {value}\n"
            
            html_content = f"""
<html>
  <head></head>
  <body>
    <h2>HomeAMP Alert</h2>
    <p><strong>Severity:</strong> <span style="color: {'red' if severity == 'critical' else 'orange' if severity == 'warning' else 'blue'}">{severity.upper()}</span></p>
    <p><strong>Message:</strong></p>
    <p>{message}</p>
"""
            
            if metadata:
                html_content += "<p><strong>Details:</strong></p><ul>"
                for key, value in metadata.items():
                    html_content += f"<li><strong>{key}:</strong> {value}</li>"
                html_content += "</ul>"
            
            html_content += "</body></html>"
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.settings.email_smtp_host, self.settings.email_smtp_port) as server:
                if self.settings.email_smtp_tls:
                    server.starttls()
                if self.settings.email_smtp_user and self.settings.email_smtp_password:
                    server.login(self.settings.email_smtp_user, self.settings.email_smtp_password)
                server.send_message(msg)
            
            logger.debug(f"Email notification sent to {self.settings.email_to}")
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    def notify_variance(self, instance_name: str, variance_count: int, critical_count: int) -> None:
        """Send configuration variance notification.

        Args:
            instance_name: Instance name
            variance_count: Total variance count
            critical_count: Critical variance count
        """
        severity = "critical" if critical_count > 0 else "warning"
        message = (
            f"Configuration variances detected on {instance_name}: "
            f"{variance_count} total ({critical_count} critical)"
        )

        self.send(
            message,
            severity=severity,
            metadata={
                "instance": instance_name,
                "total_variances": variance_count,
                "critical_variances": critical_count,
            },
        )

    def notify_update_available(self, plugin_name: str, current: str, latest: str) -> None:
        """Send update available notification.

        Args:
            plugin_name: Plugin name
            current: Current version
            latest: Latest version
        """
        message = f"Update available for {plugin_name}: {current} → {latest}"

        self.send(
            message,
            severity="info",
            metadata={
                "plugin": plugin_name,
                "current_version": current,
                "latest_version": latest,
            },
        )

    def notify_deployment_complete(
        self, instance_name: str, deployment_type: str, success: bool
    ) -> None:
        """Send deployment completion notification.

        Args:
            instance_name: Instance name
            deployment_type: Deployment type
            success: Whether deployment succeeded
        """
        severity = "info" if success else "error"
        status = "completed successfully" if success else "failed"
        message = f"Deployment {status} on {instance_name}: {deployment_type}"

        self.send(
            message,
            severity=severity,
            metadata={"instance": instance_name, "deployment_type": deployment_type, "success": success},
        )
