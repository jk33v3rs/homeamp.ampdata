"""
Pl3xMap Tile Watcher and Sync Service

Watches Pl3xMap tile directories for changes and syncs to MinIO for LiveAtlas.
Separates public and private maps for proper access control.
"""

import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Set, Optional, List
from datetime import datetime
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


# Instance classification for map access control
PRIVATE_INSTANCES = {'ROY01', 'CSMC01', 'PRI01', 'BIG01'}
PUBLIC_INSTANCES = {
    'BENT01', 'BIG01', 'CLIP01', 'CREA01', 'DEV01', 'EMAD01',
    'EVO01', 'HARD01', 'MINE01', 'MIN01', 'SMP101', 'SMP201', 'TOW01'
}


class TileChangeHandler(FileSystemEventHandler):
    """Handle file system events for map tiles"""
    
    def __init__(self, instance_name: str, sync_callback):
        self.instance_name = instance_name
        self.sync_callback = sync_callback
        self.pending_files: Set[Path] = set()
        self.last_sync = time.time()
        self.sync_delay = 10  # Batch changes for 10 seconds
    
    def on_created(self, event: FileSystemEvent):
        if not event.is_directory and self._is_tile_file(event.src_path):
            self.pending_files.add(Path(event.src_path))
            self._maybe_sync()
    
    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory and self._is_tile_file(event.src_path):
            self.pending_files.add(Path(event.src_path))
            self._maybe_sync()
    
    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory and self._is_tile_file(event.src_path):
            # For deletions, we need to sync the deletion to MinIO
            self.pending_files.add(Path(event.src_path))
            self._maybe_sync()
    
    def _is_tile_file(self, path: str) -> bool:
        """Check if file is a map tile or related file"""
        tile_extensions = {'.png', '.json', '.gz', '.webp'}
        return Path(path).suffix.lower() in tile_extensions
    
    def _maybe_sync(self):
        """Sync if enough time has passed (batch changes)"""
        now = time.time()
        if now - self.last_sync >= self.sync_delay and self.pending_files:
            self.sync_callback(self.instance_name, list(self.pending_files))
            self.pending_files.clear()
            self.last_sync = now


class TileWatcher:
    """Watch and sync Pl3xMap tiles to MinIO"""
    
    def __init__(self, minio_client, amp_data_path: str = "/home/amp/.ampdata"):
        """
        Initialize tile watcher
        
        Args:
            minio_client: MinIO client instance
            amp_data_path: Path to AMP data directory
        """
        self.minio = minio_client
        self.amp_data_path = Path(amp_data_path)
        self.bucket_name = 'pl3xmap-tiles'
        self.observers: Dict[str, Observer] = {}
        self.watched_instances: Set[str] = set()
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Create MinIO bucket if it doesn't exist"""
        try:
            if not self.minio.bucket_exists(self.bucket_name):
                self.minio.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Error creating bucket: {e}")
    
    def get_instance_access_level(self, instance_name: str) -> str:
        """Determine if instance maps are public or private"""
        if instance_name in PRIVATE_INSTANCES:
            return 'private'
        return 'public'
    
    def discover_map_instances(self) -> List[str]:
        """Find all instances with Pl3xMap installed"""
        instances = []
        instances_dir = self.amp_data_path / 'instances'
        
        if not instances_dir.exists():
            logger.warning(f"Instances directory not found: {instances_dir}")
            return instances
        
        for instance_dir in instances_dir.iterdir():
            if not instance_dir.is_dir():
                continue
            
            pl3xmap_web = instance_dir / 'plugins' / 'Pl3xMap' / 'web'
            if pl3xmap_web.exists():
                instances.append(instance_dir.name)
                logger.info(f"Found Pl3xMap on {instance_dir.name}")
        
        return instances
    
    def start_watching(self, instance_name: str):
        """Start watching an instance's map tiles"""
        if instance_name in self.watched_instances:
            logger.debug(f"Already watching {instance_name}")
            return
        
        web_dir = self.amp_data_path / 'instances' / instance_name / 'plugins' / 'Pl3xMap' / 'web'
        
        if not web_dir.exists():
            logger.warning(f"Pl3xMap web directory not found for {instance_name}: {web_dir}")
            return
        
        # Initial full sync
        logger.info(f"Starting initial sync for {instance_name}...")
        self.sync_full_directory(instance_name)
        
        # Set up file watcher
        event_handler = TileChangeHandler(instance_name, self.sync_changed_files)
        observer = Observer()
        observer.schedule(event_handler, str(web_dir), recursive=True)
        observer.start()
        
        self.observers[instance_name] = observer
        self.watched_instances.add(instance_name)
        
        logger.info(f"✓ Started watching tiles for {instance_name} ({self.get_instance_access_level(instance_name)})")
    
    def stop_watching(self, instance_name: str):
        """Stop watching an instance"""
        if instance_name in self.observers:
            self.observers[instance_name].stop()
            self.observers[instance_name].join()
            del self.observers[instance_name]
            self.watched_instances.discard(instance_name)
            logger.info(f"Stopped watching {instance_name}")
    
    def sync_full_directory(self, instance_name: str):
        """Perform full sync of instance's map tiles to MinIO"""
        web_dir = self.amp_data_path / 'instances' / instance_name / 'plugins' / 'Pl3xMap' / 'web'
        access_level = self.get_instance_access_level(instance_name)
        
        if not web_dir.exists():
            logger.error(f"Web directory not found: {web_dir}")
            return
        
        synced_count = 0
        error_count = 0
        
        for file_path in web_dir.rglob('*'):
            if file_path.is_file():
                try:
                    self._upload_file(instance_name, file_path, access_level)
                    synced_count += 1
                except Exception as e:
                    logger.error(f"Error syncing {file_path}: {e}")
                    error_count += 1
        
        logger.info(f"Full sync complete for {instance_name}: {synced_count} files, {error_count} errors")
    
    def sync_changed_files(self, instance_name: str, changed_files: List[Path]):
        """Sync specific changed files to MinIO"""
        access_level = self.get_instance_access_level(instance_name)
        
        for file_path in changed_files:
            try:
                if file_path.exists():
                    self._upload_file(instance_name, file_path, access_level)
                else:
                    # File was deleted
                    self._delete_file(instance_name, file_path, access_level)
            except Exception as e:
                logger.error(f"Error syncing {file_path}: {e}")
        
        logger.debug(f"Synced {len(changed_files)} changed files for {instance_name}")
    
    def _upload_file(self, instance_name: str, file_path: Path, access_level: str):
        """Upload a single file to MinIO"""
        web_dir = self.amp_data_path / 'instances' / instance_name / 'plugins' / 'Pl3xMap' / 'web'
        relative_path = file_path.relative_to(web_dir)
        
        # Object path: {access_level}/{instance_lowercase}/{relative_path}
        object_name = f"{access_level}/{instance_name.lower()}/{relative_path}"
        
        # Upload to MinIO
        self.minio.fput_object(
            self.bucket_name,
            object_name,
            str(file_path),
            content_type=self._get_content_type(file_path)
        )
        
        logger.debug(f"Uploaded: {object_name}")
    
    def _delete_file(self, instance_name: str, file_path: Path, access_level: str):
        """Delete a file from MinIO"""
        web_dir = self.amp_data_path / 'instances' / instance_name / 'plugins' / 'Pl3xMap' / 'web'
        relative_path = file_path.relative_to(web_dir)
        object_name = f"{access_level}/{instance_name.lower()}/{relative_path}"
        
        try:
            self.minio.remove_object(self.bucket_name, object_name)
            logger.debug(f"Deleted: {object_name}")
        except Exception as e:
            logger.warning(f"Could not delete {object_name}: {e}")
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type for file"""
        extension = file_path.suffix.lower()
        content_types = {
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.json': 'application/json',
            '.gz': 'application/gzip',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript'
        }
        return content_types.get(extension, 'application/octet-stream')
    
    def get_sync_status(self) -> Dict[str, any]:
        """Get status of all watched instances"""
        return {
            'watched_instances': list(self.watched_instances),
            'public_instances': [i for i in self.watched_instances if i not in PRIVATE_INSTANCES],
            'private_instances': [i for i in self.watched_instances if i in PRIVATE_INSTANCES],
            'bucket': self.bucket_name
        }
    
    def stop_all(self):
        """Stop watching all instances"""
        for instance_name in list(self.watched_instances):
            self.stop_watching(instance_name)
        logger.info("Stopped all tile watchers")


class TileSyncService:
    """Service to manage tile watching and syncing"""
    
    def __init__(self, minio_client):
        self.watcher = TileWatcher(minio_client)
        self.running = False
    
    def start(self):
        """Start the tile sync service"""
        logger.info("Starting Pl3xMap tile sync service...")
        
        # Discover and watch all instances with Pl3xMap
        instances = self.watcher.discover_map_instances()
        
        if not instances:
            logger.warning("No instances with Pl3xMap found")
            return
        
        for instance_name in instances:
            self.watcher.start_watching(instance_name)
        
        self.running = True
        logger.info(f"✓ Tile sync service started - watching {len(instances)} instances")
        
        # Keep service running
        try:
            while self.running:
                time.sleep(60)  # Status check every minute
                status = self.watcher.get_sync_status()
                logger.debug(f"Sync status: {len(status['watched_instances'])} instances active")
        except KeyboardInterrupt:
            logger.info("Shutting down tile sync service...")
            self.stop()
    
    def stop(self):
        """Stop the tile sync service"""
        self.running = False
        self.watcher.stop_all()
        logger.info("Tile sync service stopped")
    
    def get_status(self):
        """Get service status"""
        return {
            'running': self.running,
            **self.watcher.get_sync_status()
        }


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    from minio import Minio
    
    # Initialize MinIO client
    minio_client = Minio(
        os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    
    # Start service
    service = TileSyncService(minio_client)
    service.start()
