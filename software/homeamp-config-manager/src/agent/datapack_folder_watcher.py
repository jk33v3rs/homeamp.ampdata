"""
Datapack Folder Watcher

Watches datapack folders across all worlds for changes.
Detects when datapacks are added, removed, or modified.
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


class DatapackChangeHandler(FileSystemEventHandler):
    """Handle file system events for datapack folders"""
    
    def __init__(self, instance_name: str, world_name: str, instance_id: int, scan_callback: Callable):
        """
        Initialize datapack change handler
        
        Args:
            instance_name: Name of the instance (e.g., 'BENT01')
            world_name: Name of the world (e.g., 'world', 'world_nether')
            instance_id: Database instance ID
            scan_callback: Function to call when datapacks change
        """
        self.instance_name = instance_name
        self.world_name = world_name
        self.instance_id = instance_id
        self.scan_callback = scan_callback
        self.pending_changes: Set[tuple] = set()  # (change_type, file_path)
        self.last_scan = time.time()
        self.scan_delay = 5  # Batch changes for 5 seconds
    
    def on_created(self, event: FileSystemEvent):
        """Handle new datapack"""
        if event.is_directory or self._is_datapack_file(event.src_path):
            logger.info(f"[{self.instance_name}/{self.world_name}] Datapack added: {Path(event.src_path).name}")
            self.pending_changes.add(('created', event.src_path))
            self._maybe_scan()
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle removed datapack"""
        if event.is_directory or self._is_datapack_file(event.src_path):
            logger.info(f"[{self.instance_name}/{self.world_name}] Datapack removed: {Path(event.src_path).name}")
            self.pending_changes.add(('deleted', event.src_path))
            self._maybe_scan()
    
    def on_modified(self, event: FileSystemEvent):
        """Handle modified datapack"""
        if not event.is_directory and self._is_datapack_file(event.src_path):
            # Only track file modifications (not directory modifications)
            logger.debug(f"[{self.instance_name}/{self.world_name}] Datapack modified: {Path(event.src_path).name}")
            self.pending_changes.add(('modified', event.src_path))
            self._maybe_scan()
    
    def _is_datapack_file(self, path: str) -> bool:
        """
        Check if file is a datapack-related file
        
        Datapacks can be:
        - .zip files (compressed datapacks)
        - Directories with pack.mcmeta
        - .mcfunction files
        - .json files (for advancement, loot tables, recipes, etc.)
        """
        path_obj = Path(path)
        
        # ZIP datapacks
        if path_obj.suffix.lower() == '.zip':
            return True
        
        # Datapack structure files
        if path_obj.suffix.lower() in {'.mcfunction', '.json', '.mcmeta', '.nbt'}:
            return True
        
        return False
    
    def _maybe_scan(self):
        """Trigger scan if enough time has passed (batch changes)"""
        now = time.time()
        if now - self.last_scan >= self.scan_delay and self.pending_changes:
            # Log all changes
            for change_type, file_path in self.pending_changes:
                logger.info(f"[{self.instance_name}/{self.world_name}] Detected {change_type}: {Path(file_path).name}")
            
            # Trigger callback with all changes
            self.scan_callback(self.instance_id, self.instance_name, self.world_name, list(self.pending_changes))
            
            self.pending_changes.clear()
            self.last_scan = now
    
    def force_scan(self):
        """Force immediate scan regardless of delay"""
        if self.pending_changes:
            logger.info(f"[{self.instance_name}/{self.world_name}] Forcing immediate scan for {len(self.pending_changes)} changes")
            self.scan_callback(self.instance_id, self.instance_name, self.world_name, list(self.pending_changes))
            self.pending_changes.clear()
            self.last_scan = time.time()


class DatapackFolderWatcher:
    """Watch datapack folders across all instances and worlds"""
    
    def __init__(self, amp_data_path: str = "/home/amp/.ampdata"):
        """
        Initialize datapack folder watcher
        
        Args:
            amp_data_path: Path to AMP data directory (default: /home/amp/.ampdata)
        """
        self.amp_data_path = Path(amp_data_path)
        self.observers: Dict[str, Observer] = {}  # "instance_name:world_name" -> Observer
        self.handlers: Dict[str, DatapackChangeHandler] = {}  # "instance_name:world_name" -> Handler
        self.watched_worlds: Dict[str, tuple] = {}  # "instance_name:world_name" -> (instance_id, instance_name, world_name)
        self.scan_callback: Callable = None
    
    def set_scan_callback(self, callback: Callable):
        """
        Set the callback function for datapack changes
        
        Args:
            callback: Function with signature: callback(instance_id, instance_name, world_name, changes: List[tuple])
                     where changes is [(change_type, file_path), ...]
        """
        self.scan_callback = callback
    
    def discover_worlds(self, instance_name: str, instance_id: int) -> List[str]:
        """
        Discover all worlds in an instance
        
        Args:
            instance_name: Name of the instance
            instance_id: Database instance ID
            
        Returns:
            List of world names found
        """
        worlds_base = self.amp_data_path / 'instances' / instance_name / 'Minecraft'
        
        if not worlds_base.exists():
            logger.warning(f"Minecraft directory not found for {instance_name}: {worlds_base}")
            return []
        
        worlds = []
        
        # Common world folders
        for world_candidate in ['world', 'world_nether', 'world_the_end']:
            world_path = worlds_base / world_candidate
            if world_path.exists() and world_path.is_dir():
                worlds.append(world_candidate)
        
        # Check for custom world folders (look for level.dat)
        for item in worlds_base.iterdir():
            if item.is_dir() and item.name not in worlds:
                level_dat = item / 'level.dat'
                if level_dat.exists():
                    worlds.append(item.name)
        
        logger.info(f"Discovered {len(worlds)} worlds for {instance_name}: {worlds}")
        return worlds
    
    def start_watching_world(self, instance_name: str, instance_id: int, world_name: str):
        """
        Start watching a specific world's datapacks folder
        
        Args:
            instance_name: Name of the instance (e.g., 'BENT01')
            instance_id: Database instance ID
            world_name: Name of the world (e.g., 'world')
        """
        watch_key = f"{instance_name}:{world_name}"
        
        if watch_key in self.watched_worlds:
            logger.debug(f"Already watching {watch_key}")
            return
        
        if not self.scan_callback:
            logger.error("Scan callback not set! Call set_scan_callback() first.")
            return
        
        datapacks_dir = self.amp_data_path / 'instances' / instance_name / 'Minecraft' / world_name / 'datapacks'
        
        if not datapacks_dir.exists():
            logger.warning(f"Datapacks directory not found: {datapacks_dir}")
            return
        
        # Set up file watcher
        event_handler = DatapackChangeHandler(instance_name, world_name, instance_id, self.scan_callback)
        observer = Observer()
        observer.schedule(event_handler, str(datapacks_dir), recursive=True)
        observer.start()
        
        self.observers[watch_key] = observer
        self.handlers[watch_key] = event_handler
        self.watched_worlds[watch_key] = (instance_id, instance_name, world_name)
        
        logger.info(f" Started watching datapacks for {watch_key} at {datapacks_dir}")
    
    def watch_all_worlds(self, instance_name: str, instance_id: int):
        """
        Discover and watch all worlds for an instance
        
        Args:
            instance_name: Name of the instance
            instance_id: Database instance ID
        """
        worlds = self.discover_worlds(instance_name, instance_id)
        
        for world_name in worlds:
            self.start_watching_world(instance_name, instance_id, world_name)
        
        logger.info(f"Started watching {len(worlds)} worlds for {instance_name}")
    
    def stop_watching_world(self, instance_name: str, world_name: str):
        """
        Stop watching a specific world
        
        Args:
            instance_name: Name of the instance
            world_name: Name of the world
        """
        watch_key = f"{instance_name}:{world_name}"
        
        if watch_key in self.observers:
            self.observers[watch_key].stop()
            self.observers[watch_key].join()
            del self.observers[watch_key]
            del self.handlers[watch_key]
            del self.watched_worlds[watch_key]
            logger.info(f"Stopped watching {watch_key}")
    
    def stop_watching_instance(self, instance_name: str):
        """
        Stop watching all worlds for an instance
        
        Args:
            instance_name: Name of the instance
        """
        # Find all worlds for this instance
        to_remove = [key for key in self.watched_worlds.keys() if key.startswith(f"{instance_name}:")]
        
        for watch_key in to_remove:
            _, _, world_name = self.watched_worlds[watch_key]
            self.stop_watching_world(instance_name, world_name)
        
        logger.info(f"Stopped watching all worlds for {instance_name}")
    
    def trigger_immediate_scan(self, instance_name: str, world_name: str):
        """
        Force immediate scan for a world (ignore delay)
        
        Args:
            instance_name: Name of the instance
            world_name: Name of the world
        """
        watch_key = f"{instance_name}:{world_name}"
        
        if watch_key in self.handlers:
            self.handlers[watch_key].force_scan()
        else:
            logger.warning(f"Cannot trigger scan for unwatched world: {watch_key}")
    
    def get_watched_worlds(self) -> List[Dict]:
        """Get list of currently watched worlds"""
        return [
            {
                'instance_name': instance_name,
                'instance_id': instance_id,
                'world_name': world_name
            }
            for instance_id, instance_name, world_name in self.watched_worlds.values()
        ]
    
    def get_status(self) -> Dict:
        """Get watcher status"""
        return {
            'watched_count': len(self.watched_worlds),
            'worlds': [
                {
                    'key': key,
                    'instance_id': instance_id,
                    'instance_name': instance_name,
                    'world_name': world_name,
                    'observer_alive': self.observers[key].is_alive()
                }
                for key, (instance_id, instance_name, world_name) in self.watched_worlds.items()
            ]
        }
    
    def stop_all(self):
        """Stop watching all worlds"""
        for watch_key in list(self.watched_worlds.keys()):
            _, instance_name, world_name = self.watched_worlds[watch_key]
            self.stop_watching_world(instance_name, world_name)
        logger.info("Stopped all datapack watchers")


# Example callback function for testing
def example_scan_callback(instance_id: int, instance_name: str, world_name: str, changes: List[tuple]):
    """
    Example callback that would be implemented in the agent
    
    Args:
        instance_id: Database instance ID
        instance_name: Instance name
        world_name: World name
        changes: List of (change_type, file_path) tuples
    """
    logger.info(f"SCAN TRIGGERED for {instance_name}/{world_name} (ID: {instance_id})")
    for change_type, file_path in changes:
        logger.info(f"  - {change_type}: {Path(file_path).name}")
    
    # In actual implementation, this would call:
    # agent._discover_instance_datapacks(instance_name) to update database
    # agent._analyze_datapack(file_path) for new datapacks
    # agent._remove_datapack_from_db(file_path) for deleted datapacks


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Initialize watcher
    watcher = DatapackFolderWatcher()
    watcher.set_scan_callback(example_scan_callback)
    
    # Watch all worlds for some instances
    watcher.watch_all_worlds('BENT01', 1)
    watcher.watch_all_worlds('SMP101', 2)
    
    # Keep running
    try:
        logger.info("Datapack watcher running. Press Ctrl+C to stop.")
        while True:
            time.sleep(60)
            status = watcher.get_status()
            logger.info(f"Status: {status['watched_count']} worlds watched")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        watcher.stop_all()
