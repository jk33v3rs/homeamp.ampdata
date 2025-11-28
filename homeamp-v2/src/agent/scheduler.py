"""HomeAMP V2.0 - Scheduled task runner for periodic operations."""

import logging
import time
from datetime import datetime, timedelta
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler for running periodic tasks."""

    def __init__(self):
        """Initialize task scheduler."""
        self.tasks: List[Dict] = []
        self.running = False

    def add_task(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        run_immediately: bool = False,
    ) -> None:
        """Add a scheduled task.

        Args:
            name: Task name
            func: Function to call
            interval_seconds: Interval between runs in seconds
            run_immediately: Whether to run immediately on start
        """
        task = {
            "name": name,
            "func": func,
            "interval": interval_seconds,
            "last_run": None if run_immediately else datetime.utcnow(),
            "next_run": datetime.utcnow() if run_immediately else datetime.utcnow() + timedelta(seconds=interval_seconds),
            "run_count": 0,
            "error_count": 0,
        }

        self.tasks.append(task)
        logger.info(f"Scheduled task '{name}' every {interval_seconds}s")

    def start(self) -> None:
        """Start the scheduler."""
        logger.info(f"Starting task scheduler with {len(self.tasks)} tasks")
        self.running = True

        try:
            while self.running:
                self._check_tasks()
                time.sleep(1)  # Check every second

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the scheduler."""
        logger.info("Stopping task scheduler")
        self.running = False

    def _check_tasks(self) -> None:
        """Check if any tasks need to run."""
        now = datetime.utcnow()

        for task in self.tasks:
            if now >= task["next_run"]:
                self._run_task(task)

    def _run_task(self, task: Dict) -> None:
        """Run a scheduled task.

        Args:
            task: Task dictionary
        """
        try:
            logger.debug(f"Running scheduled task: {task['name']}")
            task["func"]()
            task["run_count"] += 1
            task["last_run"] = datetime.utcnow()
            task["next_run"] = datetime.utcnow() + timedelta(seconds=task["interval"])

        except Exception as e:
            logger.error(f"Scheduled task '{task['name']}' failed: {e}", exc_info=True)
            task["error_count"] += 1
            task["next_run"] = datetime.utcnow() + timedelta(seconds=task["interval"])

    def get_task_status(self) -> List[Dict]:
        """Get status of all scheduled tasks.

        Returns:
            List of task status dictionaries
        """
        return [
            {
                "name": task["name"],
                "interval": task["interval"],
                "last_run": task["last_run"].isoformat() if task["last_run"] else None,
                "next_run": task["next_run"].isoformat() if task["next_run"] else None,
                "run_count": task["run_count"],
                "error_count": task["error_count"],
            }
            for task in self.tasks
        ]
