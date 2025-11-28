"""HomeAMP V2.0 - Pl3xMap Tile Watcher Entry Point.

Standalone service for watching and syncing Pl3xMap tiles to MinIO.
Can be run independently of the main agent.

Usage:
    python -m homeamp_v2.agent.tile_watcher_service

Environment Variables:
    MINIO_ENDPOINT: MinIO server endpoint (default: localhost:9000)
    MINIO_ACCESS_KEY: MinIO access key (default: minioadmin)
    MINIO_SECRET_KEY: MinIO secret key (default: minioadmin)
    MINIO_SECURE: Use HTTPS (default: False)
    TILE_SYNC_INTERVAL: Sync interval in seconds (default: 300)
"""

import logging
import sys

from homeamp_v2.agent.tile_watcher import TileWatcher
from homeamp_v2.core.config import Settings
from homeamp_v2.core.logging import setup_logging
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.integrations.minio import MinIOClient

logger = logging.getLogger(__name__)


def main():
    """Run the tile watcher service."""
    # Setup logging
    settings = Settings()
    setup_logging(settings.log_level, settings.log_file, settings.log_format)

    logger.info("=" * 60)
    logger.info("HomeAMP Pl3xMap Tile Watcher Service")
    logger.info("=" * 60)

    if not settings.tile_watcher_enabled:
        logger.error("Tile watcher is disabled in settings (TILE_WATCHER_ENABLED=False)")
        logger.error("Set TILE_WATCHER_ENABLED=true in .env to enable")
        sys.exit(1)

    try:
        # Create MinIO client
        logger.info(f"Connecting to MinIO: {settings.minio_endpoint}")
        minio_client = MinIOClient(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            region=settings.minio_region,
        )

        # Create Unit of Work for database access
        uow = UnitOfWork()

        # Create tile watcher
        tile_watcher = TileWatcher(
            uow=uow,
            minio_client=minio_client,
            bucket_name=settings.minio_bucket_tiles,
            sync_interval=settings.tile_watcher_sync_interval,
        )

        # Print status
        status = tile_watcher.get_sync_status()
        logger.info("Tile Watcher Configuration:")
        logger.info(f"  Bucket: {status['bucket']}")
        logger.info(f"  Total Instances: {status['total_instances']}")
        logger.info(f"  Public Instances: {status['public_instances']}")
        logger.info(f"  Private Instances: {status['private_instances']}")
        logger.info(f"  Sync Interval: {status['sync_interval_seconds']}s")
        logger.info("")

        # Start watch loop (runs indefinitely)
        logger.info("Starting continuous tile sync...")
        tile_watcher.watch_loop()

    except KeyboardInterrupt:
        logger.info("Tile watcher stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
