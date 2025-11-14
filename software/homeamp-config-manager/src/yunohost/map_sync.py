"""
YunoHost Map Tile Sync Service

Downloads map tiles from MinIO and organizes them for LiveAtlas.
Separates public (maps.archivesmp.com) and private (admaps.archivesmp.com) maps.
"""

import os
import time
import shutil
from pathlib import Path
from typing import Dict, Set
from datetime import datetime
import logging
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MapSyncService:
    """Sync map tiles from MinIO to YunoHost filesystem for LiveAtlas"""
    
    def __init__(
        self,
        minio_client: Minio,
        public_dir: str = "/var/www/maps.archivesmp.com/data",
        private_dir: str = "/var/www/admaps.archivesmp.com/data",
        bucket_name: str = "pl3xmap-tiles"
    ):
        """
        Initialize map sync service
        
        Args:
            minio_client: MinIO client instance
            public_dir: Directory for public maps
            private_dir: Directory for private (admin) maps
            bucket_name: MinIO bucket name
        """
        self.minio = minio_client
        self.public_dir = Path(public_dir)
        self.private_dir = Path(private_dir)
        self.bucket_name = bucket_name
        
        # Track synced files for change detection
        self.synced_files: Dict[str, str] = {}  # object_name -> etag
        
        # Ensure directories exist
        self.public_dir.mkdir(parents=True, exist_ok=True)
        self.private_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized map sync service")
        logger.info(f"  Public maps: {self.public_dir}")
        logger.info(f"  Private maps: {self.private_dir}")
        logger.info(f"  MinIO bucket: {self.bucket_name}")
    
    def sync_once(self):
        """Perform one sync cycle"""
        try:
            # Sync public maps
            public_synced = self._sync_prefix('public', self.public_dir)
            
            # Sync private maps
            private_synced = self._sync_prefix('private', self.private_dir)
            
            total = public_synced + private_synced
            logger.info(f"Sync cycle complete: {total} files updated")
            
            return total
            
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return 0
    
    def _sync_prefix(self, prefix: str, target_dir: Path) -> int:
        """
        Sync all objects with given prefix from MinIO
        
        Args:
            prefix: MinIO object prefix (public/private)
            target_dir: Target directory on filesystem
            
        Returns:
            Number of files synced
        """
        synced_count = 0
        
        try:
            # List all objects with prefix
            objects = self.minio.list_objects(
                self.bucket_name,
                prefix=f"{prefix}/",
                recursive=True
            )
            
            current_objects = set()
            
            for obj in objects:
                current_objects.add(obj.object_name)
                
                # Check if file needs update
                if self._needs_update(obj.object_name, obj.etag):
                    local_path = self._get_local_path(obj.object_name, prefix, target_dir)
                    
                    # Download file
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    self.minio.fget_object(
                        self.bucket_name,
                        obj.object_name,
                        str(local_path)
                    )
                    
                    # Update tracking
                    self.synced_files[obj.object_name] = obj.etag
                    synced_count += 1
                    
                    logger.debug(f"Synced: {obj.object_name} -> {local_path}")
            
            # Clean up deleted files
            self._cleanup_deleted_files(prefix, target_dir, current_objects)
            
            logger.info(f"Synced {synced_count} {prefix} map files")
            
        except S3Error as e:
            logger.error(f"MinIO error syncing {prefix}: {e}")
        
        return synced_count
    
    def _needs_update(self, object_name: str, etag: str) -> bool:
        """Check if file needs to be updated"""
        return object_name not in self.synced_files or self.synced_files[object_name] != etag
    
    def _get_local_path(self, object_name: str, prefix: str, base_dir: Path) -> Path:
        """
        Convert MinIO object name to local path
        
        Example: public/bent01/tiles/world_nether/0/0/0.png
                 -> /var/www/maps.archivesmp.com/data/bent01/tiles/world_nether/0/0/0.png
        """
        # Remove prefix (public/ or private/)
        relative_path = object_name[len(prefix) + 1:]  # +1 for trailing /
        
        return base_dir / relative_path
    
    def _cleanup_deleted_files(self, prefix: str, target_dir: Path, current_objects: Set[str]):
        """Remove local files that no longer exist in MinIO"""
        # Get all locally tracked files for this prefix
        local_tracked = {obj for obj in self.synced_files.keys() if obj.startswith(f"{prefix}/")}
        
        # Find files that were deleted from MinIO
        deleted = local_tracked - current_objects
        
        for object_name in deleted:
            local_path = self._get_local_path(object_name, prefix, target_dir)
            
            if local_path.exists():
                try:
                    local_path.unlink()
                    logger.debug(f"Deleted: {local_path}")
                except Exception as e:
                    logger.error(f"Error deleting {local_path}: {e}")
            
            # Remove from tracking
            del self.synced_files[object_name]
    
    def get_instance_list(self, access_level: str) -> list:
        """
        Get list of instances for given access level
        
        Args:
            access_level: 'public' or 'private'
            
        Returns:
            List of instance names
        """
        instances = set()
        
        try:
            objects = self.minio.list_objects(
                self.bucket_name,
                prefix=f"{access_level}/",
                recursive=False
            )
            
            for obj in objects:
                # Extract instance name from path: public/bent01/...
                parts = obj.object_name.split('/')
                if len(parts) >= 2:
                    instances.add(parts[1])
        
        except S3Error as e:
            logger.error(f"Error listing instances: {e}")
        
        return sorted(list(instances))
    
    def generate_liveatlas_config(self, access_level: str, output_file: str):
        """
        Generate LiveAtlas config.json for given access level
        
        Args:
            access_level: 'public' or 'private'
            output_file: Path to save config.json
        """
        instances = self.get_instance_list(access_level)
        
        if access_level == 'public':
            domain = 'maps.archivesmp.com'
            title_suffix = ''
        else:
            domain = 'admaps.archivesmp.com'
            title_suffix = ' 🔒'
        
        # Build server list
        servers = []
        for instance in instances:
            # Convert instance name to title (BENT01 -> Bent World)
            title = self._instance_to_title(instance) + title_suffix
            
            servers.append({
                "id": instance.lower(),
                "name": title,
                "dynmap": False,
                "pl3xmap": True,
                "url": f"https://{domain}/data/{instance.lower()}/"
            })
        
        # Generate config
        config = {
            "servers": servers,
            "ui": {
                "playersAboveMarkers": access_level == 'public',
                "compactPlayerMarkers": access_level == 'private',
                "playersSearch": access_level == 'public',
                "coordinates": {
                    "enabled": True
                }
            },
            "messages": {
                "chatPlayerJoin": "{player} joined",
                "chatPlayerQuit": "{player} left"
            }
        }
        
        # Save config
        import json
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Generated LiveAtlas config: {output_file} ({len(servers)} servers)")
    
    def _instance_to_title(self, instance: str) -> str:
        """Convert instance name to display title"""
        # TODO: Load from instance metadata or config
        titles = {
            'bent01': 'Bent World',
            'big01': 'Bigger Games',
            'clip01': 'Clip World',
            'crea01': 'Creative',
            'csmc01': 'Counter-Strike MC',
            'dev01': 'Development',
            'emad01': 'EMad World',
            'evo01': 'Evolution',
            'hard01': 'Hard Mode',
            'mine01': 'Mining World',
            'min01': 'Mini World',
            'pri01': 'Minigames',
            'roy01': 'Battle Royale',
            'smp101': 'SMP 1.0',
            'smp201': 'SMP 2.0',
            'tow01': 'Towny'
        }
        return titles.get(instance.lower(), instance.upper())
    
    def get_status(self) -> Dict:
        """Get sync service status"""
        public_instances = self.get_instance_list('public')
        private_instances = self.get_instance_list('private')
        
        return {
            'bucket': self.bucket_name,
            'synced_files': len(self.synced_files),
            'public_instances': public_instances,
            'private_instances': private_instances,
            'public_dir': str(self.public_dir),
            'private_dir': str(self.private_dir)
        }


def main():
    """Main service loop"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Initialize MinIO client
    minio_client = Minio(
        os.getenv('MINIO_ENDPOINT', 'minio.archivesmp.internal:9000'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    
    # Initialize sync service
    service = MapSyncService(minio_client)
    
    # Generate initial LiveAtlas configs
    service.generate_liveatlas_config('public', '/var/www/maps.archivesmp.com/config.json')
    service.generate_liveatlas_config('private', '/var/www/admaps.archivesmp.com/config.json')
    
    # Continuous sync loop
    logger.info("Starting map tile sync service...")
    sync_interval = int(os.getenv('SYNC_INTERVAL', '300'))  # Default 5 minutes
    
    try:
        while True:
            start_time = time.time()
            
            # Perform sync
            files_synced = service.sync_once()
            
            # Regenerate configs if instances changed
            if files_synced > 0:
                service.generate_liveatlas_config('public', '/var/www/maps.archivesmp.com/config.json')
                service.generate_liveatlas_config('private', '/var/www/admaps.archivesmp.com/config.json')
            
            # Status report
            status = service.get_status()
            logger.info(f"Status: {status['synced_files']} files tracked, "
                       f"{len(status['public_instances'])} public + "
                       f"{len(status['private_instances'])} private instances")
            
            # Wait for next cycle
            elapsed = time.time() - start_time
            sleep_time = max(0, sync_interval - elapsed)
            
            if sleep_time > 0:
                logger.debug(f"Sleeping {sleep_time:.0f}s until next sync")
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Shutting down map sync service")


if __name__ == '__main__':
    main()
