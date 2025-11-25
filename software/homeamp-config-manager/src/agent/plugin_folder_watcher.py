"""
Plugin Folder Watcher

Watches plugin folders for JAR file changes and triggers immediate agent scans.
Reduces detection latency from 5-minute scan cycle to instant.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, Set, Callable, List
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class PluginChangeHandler(FileSystemEventHandler):
    """Handle file system events for plugin JAR files"""

    def __init__(self, instance_name: str, instance_id: int, scan_callback: Callable):
        """
        Initialize plugin change handler

        Args:
            instance_name: Name of the instance (e.g., 'BENT01')
            instance_id: Database instance ID
            scan_callback: Function to call when plugins change (signature: callback(instance_id, instance_name, change_type, file_path))
        """
        self.instance_name = instance_name
        self.instance_id = instance_id
        self.scan_callback = scan_callback
        self.pending_changes: Set[tuple] = set()  # (change_type, file_path)
        self.last_scan = time.time()
        self.scan_delay = 5  # Batch changes for 5 seconds

    def on_created(self, event: FileSystemEvent):
        """Handle new JAR file"""
        if not event.is_directory and self._is_plugin_jar(event.src_path):
            logger.info(f"[{self.instance_name}] Plugin added: {Path(event.src_path).name}")
            self.pending_changes.add(("created", event.src_path))
            self._maybe_scan()

    def on_deleted(self, event: FileSystemEvent):
        """Handle removed JAR file"""
        if not event.is_directory and self._is_plugin_jar(event.src_path):
            logger.info(f"[{self.instance_name}] Plugin removed: {Path(event.src_path).name}")
            self.pending_changes.add(("deleted", event.src_path))
            self._maybe_scan()

    def on_modified(self, event: FileSystemEvent):
        """Handle modified JAR file (usually updates)"""
        if not event.is_directory and self._is_plugin_jar(event.src_path):
            # Debounce: multiple modify events can fire for single JAR update
            logger.debug(f"[{self.instance_name}] Plugin modified: {Path(event.src_path).name}")
            self.pending_changes.add(("modified", event.src_path))
            self._maybe_scan()

    def _is_plugin_jar(self, path: str) -> bool:
        """Check if file is a plugin JAR"""
        return Path(path).suffix.lower() == ".jar"

    def _maybe_scan(self):
        """Trigger scan if enough time has passed (batch changes)"""
        now = time.time()
        if now - self.last_scan >= self.scan_delay and self.pending_changes:
            # Log all changes
            for change_type, file_path in self.pending_changes:
                logger.info(f"[{self.instance_name}] Detected {change_type}: {Path(file_path).name}")

            # Trigger callback with all changes
            self.scan_callback(self.instance_id, self.instance_name, list(self.pending_changes))

            self.pending_changes.clear()
            self.last_scan = now

    def force_scan(self):
        """Force immediate scan regardless of delay"""
        if self.pending_changes:
            logger.info(f"[{self.instance_name}] Forcing immediate scan for {len(self.pending_changes)} changes")
            self.scan_callback(self.instance_id, self.instance_name, list(self.pending_changes))
            self.pending_changes.clear()
            self.last_scan = time.time()


class PluginFolderWatcher:
    """Watch plugin folders across all instances for changes"""

    def __init__(self, amp_data_path: str = "/home/amp/.ampdata"):
        """
        Initialize plugin folder watcher

        Args:
            amp_data_path: Path to AMP data directory (default: /home/amp/.ampdata)
        """
        self.amp_data_path = Path(amp_data_path)
        self.observers: Dict[str, Observer] = {}  # instance_name -> Observer
        self.handlers: Dict[str, PluginChangeHandler] = {}  # instance_name -> Handler
        self.watched_instances: Dict[str, int] = {}  # instance_name -> instance_id
        self.scan_callback: Callable = None

    def set_scan_callback(self, callback: Callable):
        """
        Set the callback function for plugin changes

        Args:
            callback: Function with signature: callback(instance_id, instance_name, changes: List[tuple])
                     where changes is [(change_type, file_path), ...]
        """
        self.scan_callback = callback

    def start_watching(self, instance_name: str, instance_id: int):
        """
        Start watching an instance's plugin folder

        Args:
            instance_name: Name of the instance (e.g., 'BENT01')
            instance_id: Database instance ID
        """
        if instance_name in self.watched_instances:
            logger.debug(f"Already watching {instance_name}")
            return

        if not self.scan_callback:
            logger.error("Scan callback not set! Call set_scan_callback() first.")
            return

        plugins_dir = self.amp_data_path / "instances" / instance_name / "Minecraft" / "plugins"

        if not plugins_dir.exists():
            logger.warning(f"Plugins directory not found for {instance_name}: {plugins_dir}")
            return

        # Set up file watcher
        event_handler = PluginChangeHandler(instance_name, instance_id, self.scan_callback)
        observer = Observer()
        observer.schedule(event_handler, str(plugins_dir), recursive=False)
        observer.start()

        self.observers[instance_name] = observer
        self.handlers[instance_name] = event_handler
        self.watched_instances[instance_name] = instance_id

        logger.info(f" Started watching plugins for {instance_name} (ID: {instance_id}) at {plugins_dir}")

    def stop_watching(self, instance_name: str):
        """
        Stop watching an instance

        Args:
            instance_name: Name of the instance to stop watching
        """
        if instance_name in self.observers:
            self.observers[instance_name].stop()
            self.observers[instance_name].join()
            del self.observers[instance_name]
            del self.handlers[instance_name]
            del self.watched_instances[instance_name]
            logger.info(f"Stopped watching {instance_name}")

    def trigger_immediate_scan(self, instance_name: str):
        """
        Force immediate scan for an instance (ignore delay)

        Args:
            instance_name: Name of the instance to scan
        """
        if instance_name in self.handlers:
            self.handlers[instance_name].force_scan()
        else:
            logger.warning(f"Cannot trigger scan for unwatched instance: {instance_name}")

    def get_watched_instances(self) -> List[str]:
        """Get list of currently watched instance names"""
        return list(self.watched_instances.keys())

    def get_status(self) -> Dict:
        """Get watcher status"""
        return {
            "watched_count": len(self.watched_instances),
            "instances": [
                {"name": name, "id": instance_id, "observer_alive": self.observers[name].is_alive()}
                for name, instance_id in self.watched_instances.items()
            ],
        }

    def stop_all(self):
        """Stop watching all instances"""
        for instance_name in list(self.watched_instances.keys()):
            self.stop_watching(instance_name)
        logger.info("Stopped all plugin watchers")


# Example callback function for testing
def example_scan_callback(instance_id: int, instance_name: str, changes: List[tuple]):
    """
    Example callback that would be implemented in the agent

    Args:
        instance_id: Database instance ID
        instance_name: Instance name
        changes: List of (change_type, file_path) tuples
    """
    logger.info(f"SCAN TRIGGERED for {instance_name} (ID: {instance_id})")
    for change_type, file_path in changes:
        logger.info(f"  - {change_type}: {Path(file_path).name}")

    # In actual implementation, this would call:
    # agent._analyze_plugin_jar(file_path) for new/modified JARs
    # agent._remove_plugin_from_db(file_path) for deleted JARs
    # agent._discover_plugin_config_files() to update config file tracking


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # Initialize watcher
    watcher = PluginFolderWatcher()
    watcher.set_scan_callback(example_scan_callback)

    # Start watching some instances (example)
    watcher.start_watching("BENT01", 1)
    watcher.start_watching("SMP101", 2)

    # Keep running
    try:
        logger.info("Plugin watcher running. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)
            status = watcher.get_status()
            logger.info(f"Status: {status['watched_count']} instances watched")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        watcher.stop_all()
