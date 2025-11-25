"""
Scheduled Tasks Runner for ArchiveSMP Config Manager

Manages periodic tasks:
- Plugin version checks
- Configuration drift detection
- Health metrics collection
- Cleanup operations
"""

import mariadb
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional
import json

try:
    import schedule

    HAS_SCHEDULE = True
except ImportError:
    HAS_SCHEDULE = False

logger = logging.getLogger("scheduled_tasks")


class ScheduledTasksRunner:
    """Manages scheduled background tasks"""

    def __init__(self, db_connection, agent_instance=None):
        """
        Initialize scheduled tasks runner

        Args:
            db_connection: MariaDB connection
            agent_instance: Agent instance for running discovery/checks
        """
        self.db = db_connection
        self.cursor = db_connection.cursor(dictionary=True)
        self.agent = agent_instance
        self.running = False
        self.thread = None

        # Task registry
        self.tasks = {}

    def register_task(
        self,
        task_name: str,
        task_function: Callable,
        schedule_type: str,
        schedule_value: str,
        description: str = "",
        enabled: bool = True,
    ):
        """
        Register a scheduled task

        Args:
            task_name: Unique task name
            task_function: Function to execute
            schedule_type: 'interval' or 'cron'
            schedule_value: e.g., '1h', '30m', '0 */6 * * *'
            description: Task description
            enabled: Whether task is enabled
        """
        # Store in database
        query = """
            INSERT INTO scheduled_tasks (
                task_name,
                description,
                schedule_type,
                schedule_value,
                enabled,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
                description = VALUES(description),
                schedule_type = VALUES(schedule_type),
                schedule_value = VALUES(schedule_value),
                enabled = VALUES(enabled)
        """

        self.cursor.execute(query, (task_name, description, schedule_type, schedule_value, enabled))
        self.db.commit()

        # Register in memory
        self.tasks[task_name] = {
            "function": task_function,
            "schedule_type": schedule_type,
            "schedule_value": schedule_value,
            "enabled": enabled,
        }

        logger.info(f"Registered task: {task_name} ({schedule_value})")

    def _schedule_tasks(self):
        """Schedule all registered tasks using schedule library"""
        schedule.clear()

        for task_name, task_info in self.tasks.items():
            if not task_info["enabled"]:
                continue

            func = task_info["function"]
            schedule_value = task_info["schedule_value"]

            # Parse schedule value
            if schedule_value.endswith("m"):
                # Minutes
                minutes = int(schedule_value[:-1])
                schedule.every(minutes).minutes.do(self._run_task, task_name, func)

            elif schedule_value.endswith("h"):
                # Hours
                hours = int(schedule_value[:-1])
                schedule.every(hours).hours.do(self._run_task, task_name, func)

            elif schedule_value.endswith("d"):
                # Days
                days = int(schedule_value[:-1])
                schedule.every(days).days.do(self._run_task, task_name, func)

            else:
                logger.warning(f"Unknown schedule format for {task_name}: {schedule_value}")

        logger.info(f"Scheduled {len(self.tasks)} tasks")

    def _run_task(self, task_name: str, task_function: Callable):
        """
        Execute a task and log results

        Args:
            task_name: Name of task
            task_function: Function to execute
        """
        logger.info(f"Running task: {task_name}")

        start_time = datetime.now()
        status = "success"
        error_message = None
        result_data = None

        try:
            result_data = task_function()
            logger.info(f"Task {task_name} completed successfully")

        except Exception as e:
            status = "failed"
            error_message = str(e)
            logger.error(f"Task {task_name} failed: {e}")

        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()

        # Log execution
        query = """
            UPDATE scheduled_tasks
            SET 
                last_run_at = %s,
                last_run_status = %s,
                last_run_duration_seconds = %s,
                last_run_error = %s,
                last_run_result = %s,
                next_run_at = %s
            WHERE task_name = %s
        """

        # Calculate next run time (approximate)
        next_run = self._calculate_next_run(task_name)

        self.cursor.execute(
            query,
            (
                start_time,
                status,
                duration_seconds,
                error_message,
                json.dumps(result_data) if result_data else None,
                next_run,
                task_name,
            ),
        )
        self.db.commit()

    def _calculate_next_run(self, task_name: str) -> Optional[datetime]:
        """Calculate next run time for a task"""
        if task_name not in self.tasks:
            return None

        schedule_value = self.tasks[task_name]["schedule_value"]

        if schedule_value.endswith("m"):
            minutes = int(schedule_value[:-1])
            return datetime.now() + timedelta(minutes=minutes)

        elif schedule_value.endswith("h"):
            hours = int(schedule_value[:-1])
            return datetime.now() + timedelta(hours=hours)

        elif schedule_value.endswith("d"):
            days = int(schedule_value[:-1])
            return datetime.now() + timedelta(days=days)

        return None

    def start(self):
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler already running")
            return

        self.running = True
        self._schedule_tasks()

        # Run in background thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        logger.info("Scheduled tasks runner started")

    def _run_scheduler(self):
        """Background scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Scheduled tasks runner stopped")

    # ========================================================================
    # DEFAULT TASKS
    # ========================================================================

    def setup_default_tasks(self):
        """Register default scheduled tasks"""

        # Plugin version check every 6 hours
        self.register_task(
            task_name="check_plugin_updates",
            task_function=self._check_plugin_updates,
            schedule_type="interval",
            schedule_value="6h",
            description="Check for plugin updates via CI/CD endpoints",
            enabled=True,
        )

        # Drift detection every 1 hour
        self.register_task(
            task_name="detect_configuration_drift",
            task_function=self._detect_drift,
            schedule_type="interval",
            schedule_value="1h",
            description="Detect configuration drift from baselines",
            enabled=True,
        )

        # Health metrics collection every 15 minutes
        self.register_task(
            task_name="collect_health_metrics",
            task_function=self._collect_health_metrics,
            schedule_type="interval",
            schedule_value="15m",
            description="Collect system health metrics",
            enabled=True,
        )

        # Cleanup old logs/history daily
        self.register_task(
            task_name="cleanup_old_logs",
            task_function=self._cleanup_old_logs,
            schedule_type="interval",
            schedule_value="1d",
            description="Clean up old notification logs and history entries",
            enabled=True,
        )

        # Discovery scan every 30 minutes
        self.register_task(
            task_name="discovery_scan",
            task_function=self._run_discovery,
            schedule_type="interval",
            schedule_value="30m",
            description="Discover and register new instances",
            enabled=True,
        )

    def _check_plugin_updates(self) -> Dict[str, Any]:
        """Check for plugin updates"""
        logger.info("Checking for plugin updates...")

        if not self.agent:
            return {"error": "No agent instance available"}

        # Run plugin update check
        try:
            updates = self.agent.check_plugin_updates()
            return {"updates_found": len(updates), "updates": updates}
        except Exception as e:
            logger.error(f"Plugin update check failed: {e}")
            return {"error": str(e)}

    def _detect_drift(self) -> Dict[str, Any]:
        """Detect configuration drift"""
        logger.info("Detecting configuration drift...")

        if not self.agent:
            return {"error": "No agent instance available"}

        try:
            drift_count = self.agent.detect_drift()
            return {"drift_detections": drift_count}
        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            return {"error": str(e)}

    def _collect_health_metrics(self) -> Dict[str, Any]:
        """Collect system health metrics"""
        logger.info("Collecting health metrics...")

        try:
            # Collect basic metrics
            query = (
                "SELECT COUNT(*) as instance_count FROM instances WHERE last_seen > DATE_SUB(NOW(), INTERVAL 1 HOUR)"
            )
            self.cursor.execute(query)
            active_instances = self.cursor.fetchone()["instance_count"]

            query = "SELECT COUNT(*) as pending_count FROM deployment_queue WHERE status = 'pending'"
            self.cursor.execute(query)
            pending_deployments = self.cursor.fetchone()["pending_count"]

            query = "SELECT COUNT(*) as unread_count FROM notification_log WHERE read_at IS NULL"
            self.cursor.execute(query)
            unread_notifications = self.cursor.fetchone()["unread_count"]

            # DISABLED: Metrics insertion creates millions of records
            # Just log the stats instead of inserting into DB
            logger.info(
                f"Health metrics: instances={active_instances}, deployments={pending_deployments}, notifications={unread_notifications}"
            )

            # # Store metrics
            # query = """
            #     INSERT INTO system_health_metrics (
            #         metric_name,
            #         metric_value,
            #         metric_unit,
            #         recorded_at
            #     ) VALUES
            #     (%s, %s, %s, NOW()),
            #     (%s, %s, %s, NOW()),
            #     (%s, %s, %s, NOW())
            # """
            #
            # self.cursor.execute(query, (
            #     'active_instances', active_instances, 'count',
            #     'pending_deployments', pending_deployments, 'count',
            #     'unread_notifications', unread_notifications, 'count'
            # ))
            # self.db.commit()

            return {
                "active_instances": active_instances,
                "pending_deployments": pending_deployments,
                "unread_notifications": unread_notifications,
            }

        except Exception as e:
            logger.error(f"Health metrics collection failed: {e}")
            return {"error": str(e)}

    def _cleanup_old_logs(self) -> Dict[str, Any]:
        """Clean up old logs and history (older than 90 days)"""
        logger.info("Cleaning up old logs...")

        try:
            # Delete old notification logs
            query = "DELETE FROM notification_log WHERE created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)"
            self.cursor.execute(query)
            deleted_notifications = self.cursor.rowcount

            # Delete old health metrics
            query = "DELETE FROM system_health_metrics WHERE recorded_at < DATE_SUB(NOW(), INTERVAL 90 DAY)"
            self.cursor.execute(query)
            deleted_metrics = self.cursor.rowcount

            self.db.commit()

            return {"deleted_notifications": deleted_notifications, "deleted_metrics": deleted_metrics}

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {"error": str(e)}

    def _run_discovery(self) -> Dict[str, Any]:
        """Run instance discovery"""
        logger.info("Running discovery scan...")

        if not self.agent:
            return {"error": "No agent instance available"}

        try:
            discovered = self.agent.discover_instances()
            return {"instances_discovered": len(discovered), "instances": discovered}
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {"error": str(e)}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_scheduler(db_connection, agent_instance=None) -> ScheduledTasksRunner:
    """
    Factory function to create scheduler instance

    Args:
        db_connection: MariaDB connection
        agent_instance: Optional agent instance

    Returns:
        ScheduledTasksRunner instance
    """
    scheduler = ScheduledTasksRunner(db_connection, agent_instance)
    scheduler.setup_default_tasks()
    return scheduler
