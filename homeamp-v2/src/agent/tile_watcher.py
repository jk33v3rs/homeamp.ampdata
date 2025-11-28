"""HomeAMP V2.0 - Pl3xMap tile watcher for MinIO sync."""

import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.integrations.minio import MinIOClient

logger = logging.getLogger(__name__)


class TileWatcher:
    """Watch Pl3xMap tile directories and sync to MinIO.
    
    Monitors instance plugin directories for Pl3xMap tile changes and uploads
    them to MinIO for serving via LiveAtlas on separate web servers.
    
    Supports both public and private access levels for tactical gameplay protection.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        minio_client: MinIOClient,
        bucket_name: str = "pl3xmap-tiles",
        sync_interval: int = 300,
    ):
        """Initialize tile watcher.
        
        Args:
            uow: Unit of Work for database access
            minio_client: MinIO client instance
            bucket_name: S3 bucket for tiles (default: "pl3xmap-tiles")
            sync_interval: Seconds between sync cycles (default: 300)
        """
        self.uow = uow
        self.minio = minio_client
        self.bucket_name = bucket_name
        self.sync_interval = sync_interval
        
        # Instance access level configuration
        self.access_levels: Dict[str, List[str]] = {
            "public": [
                "BENT01", "BIG01", "CLIP01", "CREA01", "DEV01",
                "EMAD01", "EVO01", "HARD01", "MINE01", "MIN01",
                "PRI01", "SMP101", "SMP201",
            ],
            "private": [
                "CSMC01",  # Counter-Strike MC (anti-screen camping)
                "ROY01",   # Battle Royale (spectator protection)
                "TOW01",   # Towny PvP (base protection)
            ],
        }
        
        # Track file hashes to detect changes
        self.file_hashes: Dict[str, str] = {}
        
        logger.info("Tile watcher initialized")

    def ensure_bucket(self) -> bool:
        """Ensure MinIO bucket exists.
        
        Returns:
            True if bucket exists or was created
        """
        if not self.minio.bucket_exists(self.bucket_name):
            logger.info(f"Creating bucket: {self.bucket_name}")
            return self.minio.create_bucket(self.bucket_name)
        return True

    def get_access_level(self, instance_name: str) -> str:
        """Determine access level for an instance.
        
        Args:
            instance_name: Instance name (e.g., "BENT01")
            
        Returns:
            "public" or "private"
        """
        instance_upper = instance_name.upper()
        if instance_upper in self.access_levels["private"]:
            return "private"
        return "public"

    def get_pl3xmap_directory(self, instance_base_path: Path) -> Optional[Path]:
        """Get Pl3xMap web directory for an instance.
        
        Args:
            instance_base_path: Instance base directory
            
        Returns:
            Path to Pl3xMap/web directory or None if not found
        """
        pl3xmap_web = instance_base_path / "plugins" / "Pl3xMap" / "web"
        
        if pl3xmap_web.exists():
            return pl3xmap_web
        
        # Try alternate plugin name (case-insensitive search)
        plugins_dir = instance_base_path / "plugins"
        if plugins_dir.exists():
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and plugin_dir.name.lower() == "pl3xmap":
                    web_dir = plugin_dir / "web"
                    if web_dir.exists():
                        return web_dir
        
        return None

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file.
        
        Args:
            file_path: File to hash
            
        Returns:
            Hex digest of file hash
        """
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def has_file_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last sync.
        
        Args:
            file_path: File to check
            
        Returns:
            True if file is new or modified
        """
        file_key = str(file_path)
        current_hash = self.calculate_file_hash(file_path)
        
        if file_key not in self.file_hashes:
            self.file_hashes[file_key] = current_hash
            return True
        
        if self.file_hashes[file_key] != current_hash:
            self.file_hashes[file_key] = current_hash
            return True
        
        return False

    def sync_instance_tiles(
        self,
        instance_id: int,
        instance_name: str,
        base_path: Path,
        force: bool = False,
    ) -> int:
        """Sync tiles for a single instance.
        
        Args:
            instance_id: Instance database ID
            instance_name: Instance name (e.g., "BENT01")
            base_path: Instance base directory
            force: Force sync all files (default: False)
            
        Returns:
            Number of files uploaded
        """
        pl3xmap_dir = self.get_pl3xmap_directory(base_path)
        
        if not pl3xmap_dir:
            logger.debug(f"No Pl3xMap directory found for {instance_name}")
            return 0

        access_level = self.get_access_level(instance_name)
        instance_lower = instance_name.lower()
        uploaded_count = 0

        # Sync all files in web directory
        for file_path in pl3xmap_dir.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip if file hasn't changed (unless force=True)
            if not force and not self.has_file_changed(file_path):
                continue

            # Calculate S3 object name: {access_level}/{instance}/{relative_path}
            relative_path = file_path.relative_to(pl3xmap_dir)
            object_name = f"{access_level}/{instance_lower}/{relative_path}".replace("\\", "/")

            # Upload to MinIO
            if self.minio.upload_file(self.bucket_name, object_name, file_path):
                uploaded_count += 1

        if uploaded_count > 0:
            logger.info(
                f"Synced {uploaded_count} tiles for {instance_name} "
                f"({access_level}) to MinIO"
            )

        return uploaded_count

    def sync_all_instances(self, force: bool = False) -> Dict[str, int]:
        """Sync tiles for all instances with Pl3xMap.
        
        Args:
            force: Force sync all files (default: False)
            
        Returns:
            Dictionary mapping instance names to upload counts
        """
        results: Dict[str, int] = {}

        with self.uow:
            # Query all active instances
            instances = self.uow.instances.list(filters={"is_active": True})

            for instance in instances:
                base_path = Path(instance.base_path)
                
                try:
                    count = self.sync_instance_tiles(
                        instance.id,
                        instance.name,
                        base_path,
                        force=force,
                    )
                    results[instance.name] = count
                    
                except Exception as e:
                    logger.error(f"Error syncing {instance.name}: {e}")
                    results[instance.name] = 0

        total_uploaded = sum(results.values())
        logger.info(f"Sync completed: {total_uploaded} total files uploaded")
        
        return results

    def watch_loop(self):
        """Continuous watch loop for tile changes.
        
        Runs indefinitely, syncing tiles at configured intervals.
        """
        logger.info(f"Starting tile watch loop (interval: {self.sync_interval}s)")

        # Ensure bucket exists
        if not self.ensure_bucket():
            logger.error(f"Failed to create/verify bucket: {self.bucket_name}")
            return

        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                start_time = time.time()
                
                logger.info(f"Starting sync cycle #{cycle_count}")
                results = self.sync_all_instances(force=False)
                
                elapsed = time.time() - start_time
                logger.info(
                    f"Sync cycle #{cycle_count} completed in {elapsed:.2f}s: "
                    f"{sum(results.values())} files uploaded"
                )

                # Sleep until next sync
                time.sleep(self.sync_interval)

            except KeyboardInterrupt:
                logger.info("Tile watcher stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in watch loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retry

    def get_sync_status(self) -> Dict[str, any]:
        """Get current sync status information.
        
        Returns:
            Dictionary with sync statistics
        """
        with self.uow:
            total_instances = len(self.uow.instances.list(filters={"is_active": True}))
            
        return {
            "bucket": self.bucket_name,
            "total_instances": total_instances,
            "public_instances": len(self.access_levels["public"]),
            "private_instances": len(self.access_levels["private"]),
            "sync_interval_seconds": self.sync_interval,
            "tracked_files": len(self.file_hashes),
        }
