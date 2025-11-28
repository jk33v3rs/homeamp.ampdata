"""HomeAMP V2.0 - Core configuration management."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    # Database
    database_url: str = Field(default="mysql+pymysql://homeamp:password@localhost:3369/homeamp_v2")
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=100)
    database_echo: bool = Field(default=False)

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    api_workers: int = Field(default=4, ge=1, le=16)
    api_reload: bool = Field(default=False)
    api_debug: bool = Field(default=False)

    # Security
    secret_key: str = Field(default="change-this-in-production")
    api_key_expiry_days: int = Field(default=90, ge=1)

    # Agent
    agent_enabled: bool = Field(default=True)
    agent_cycle_interval: int = Field(default=300, ge=10)
    agent_heartbeat_interval: int = Field(default=60, ge=10)
    agent_discovery_enabled: bool = Field(default=True)
    agent_variance_enabled: bool = Field(default=True)
    agent_update_check_enabled: bool = Field(default=True)

    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/homeamp.log")
    log_max_bytes: int = Field(default=10485760)
    log_backup_count: int = Field(default=5, ge=0)
    log_format: str = Field(default="json")

    # Backup
    backup_enabled: bool = Field(default=True)
    backup_dir: str = Field(default="backups/")
    backup_retention_days: int = Field(default=30, ge=1)

    # MinIO / S3 Storage
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_secure: bool = Field(default=False)
    minio_region: str = Field(default="us-east-1")
    minio_bucket_tiles: str = Field(default="pl3xmap-tiles")
    minio_bucket_backups: str = Field(default="homeamp-backups")

    # Tile Watcher (Pl3xMap/LiveAtlas)
    tile_watcher_enabled: bool = Field(default=False)
    tile_watcher_sync_interval: int = Field(default=300, ge=60)
    tile_watcher_force_sync: bool = Field(default=False)
    backup_max_count: int = Field(default=10, ge=1)

    # External Integrations
    modrinth_api_url: str = Field(default="https://api.modrinth.com/v2")
    hangar_api_url: str = Field(default="https://hangar.papermc.io/api/v1")
    github_api_url: str = Field(default="https://api.github.com")
    github_token: Optional[str] = Field(default=None)

    # Discord
    discord_webhook_url: Optional[str] = Field(default=None)
    discord_enabled: bool = Field(default=False)

    # Redis
    redis_enabled: bool = Field(default=False)
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Feature Flags
    feature_world_management: bool = Field(default=False)
    feature_region_tracking: bool = Field(default=False)
    feature_rank_management: bool = Field(default=False)
    feature_datapack_management: bool = Field(default=True)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
