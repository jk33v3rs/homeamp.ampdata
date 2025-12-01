"""
Settings Handler

Centralized configuration management for ArchiveSMP Configuration Manager.
Loads settings from YAML files and provides typed access to configuration values.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging


@dataclass
class MinIOConfig:
    """MinIO storage configuration"""
    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str
    secure: bool
    timeout: int
    retry_attempts: int


@dataclass
class AgentConfig:
    """Agent service configuration"""
    change_poll_interval: int
    drift_check_interval: int
    health_check_interval: int
    max_concurrent_changes: int
    change_timeout_minutes: int
    restart_on_failure: bool
    max_restart_attempts: int


@dataclass
class WebConfig:
    """Web API configuration"""
    host: str
    port: int
    workers: int
    reload: bool
    max_file_size_mb: int
    max_request_size_mb: int
    request_timeout_seconds: int
    max_concurrent_requests: int


@dataclass
class HttpConfig:
    """HTTP client configuration"""
    timeout_seconds: int
    max_retries: int
    backoff_seconds: int
    user_agent: str


@dataclass
class PluginUpdateConfig:
    """Plugin update checking configuration"""
    check_interval_hours: int
    risk_assessment_enabled: bool
    spigot_base_url: str
    bukkit_base_url: str
    github_base_url: str
    timeout: int
    rate_limit_delay: int


class SettingsHandler:
    """Central settings management for ArchiveSMP Configuration Manager"""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize settings handler
        
        Args:
            config_file: Path to settings YAML file. If None, searches standard locations.
        """
        self.logger = logging.getLogger(__name__)
        
        if config_file is None:
            config_file = self._find_config_file()
        
        self.config_file = Path(config_file)
        self.settings = self._load_settings()
        
    def _find_config_file(self) -> Path:
        """Find settings file in standard locations"""
        possible_locations = [
            Path(__file__).parent.parent / "config" / "settings.yaml",
            Path.cwd() / "config" / "settings.yaml",
            Path.cwd() / "settings.yaml",
            Path("/etc/archivesmp/settings.yaml"),
            Path("~/.archivesmp/settings.yaml").expanduser()
        ]
        
        for location in possible_locations:
            if location.exists():
                self.logger.info(f"Found settings file at {location}")
                return location
        
        # Create default if none found
        default_location = Path(__file__).parent.parent / "config" / "settings.yaml"
        self.logger.warning(f"No settings file found, using default location: {default_location}")
        return default_location
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from YAML file"""
        try:
            if not self.config_file.exists():
                self.logger.error(f"Settings file not found: {self.config_file}")
                return {}
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_settings = yaml.safe_load(f)
                settings: Dict[str, Any] = loaded_settings if loaded_settings else {}
            
            # Apply environment variable overrides
            settings = self._apply_env_overrides(settings)
            
            self.logger.info(f"Loaded settings from {self.config_file}")
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")
            return {}
    
    def _apply_env_overrides(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to settings"""
        # Environment variable mapping
        env_mappings = {
            'ARCHIVESMP_MINIO_ENDPOINT': ('storage', 'minio', 'endpoint'),
            'ARCHIVESMP_MINIO_ACCESS_KEY': ('storage', 'minio', 'access_key'),
            'ARCHIVESMP_MINIO_SECRET_KEY': ('storage', 'minio', 'secret_key'),
            'ARCHIVESMP_MINIO_BUCKET': ('storage', 'minio', 'bucket_name'),
            'ARCHIVESMP_MINIO_SECURE': ('storage', 'minio', 'secure'),
            'ARCHIVESMP_WEB_HOST': ('web', 'server', 'host'),
            'ARCHIVESMP_WEB_PORT': ('web', 'server', 'port'),
            'ARCHIVESMP_LOG_LEVEL': ('agent', 'logging', 'level'),
            'ARCHIVESMP_POLL_INTERVAL': ('agent', 'polling', 'change_poll_interval'),
            'ARCHIVESMP_DRIFT_INTERVAL': ('agent', 'polling', 'drift_check_interval'),
        }
        
        for env_var, path in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion
                if env_var.endswith('_PORT') or env_var.endswith('_INTERVAL'):
                    value = int(value)
                elif env_var.endswith('_SECURE'):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                
                # Set nested value
                current = settings
                for key in path[:-1]:
                    current = current.setdefault(key, {})
                current[path[-1]] = value
                
                self.logger.info(f"Applied environment override: {env_var} = {value}")
        
        return settings
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get configuration value by nested keys
        
        Args:
            *keys: Nested keys to traverse
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        current = self.settings
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get_required(self, *keys: str) -> Any:
        """
        Get required configuration value by nested keys
        
        Args:
            *keys: Nested keys to traverse
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If required setting is not found
        """
        value = self.get(*keys)
        if value is None:
            raise ValueError(f"Required setting not found: {'.'.join(keys)}")
        return value
    
    # System Configuration
    @property
    def instances_path(self) -> Path:
        """Get instances path"""
        return Path(self.get('system', 'paths', 'instances_path', default='/home/amp/.ampdata/instances'))
    
    @property
    def utildata_path(self) -> Path:
        """Legacy: Get utildata path (now instances path)"""
        return self.instances_path
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path"""
        path_str = self.get('system', 'paths', 'data_dir', default='/var/lib/archivesmp')
        return Path(path_str)
    
    @property
    def scripts_dir(self) -> Path:
        """Get scripts directory path"""
        return Path(self.get('system', 'paths', 'scripts_dir', default='scripts'))
    
    @property
    def backup_dir(self) -> Path:
        """Get backup directory path"""
        return Path(self.get('system', 'paths', 'backup_root', default='./data/backups'))
    
    @property
    def temp_dir(self) -> Path:
        """Get temporary directory path"""
        return Path(self.get('system', 'paths', 'temp_dir', default='/tmp/archivesmp'))
    
    # File paths and names
    def get_file_path(self, file_key: str) -> str:
        """Get file path by key from system.files"""
        return self.get('system', 'files', file_key, default=file_key)
    
    @property
    def config_extensions(self) -> List[str]:
        """Get allowed configuration file extensions"""
        return self.get('system', 'file_formats', 'config_extensions', 
                       default=['.yml', '.yaml', '.json', '.properties', '.cfg', '.conf'])
    
    @property
    def backup_extension(self) -> str:
        """Get backup file extension"""
        return self.get('system', 'file_formats', 'backup_extension', default='.bak')
    
    # Physical Server Configuration
    @property
    def physical_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get physical server configurations"""
        return self.get('network', 'physical_servers', default={})
    
    @property
    def ovh_ryzen_config(self) -> Dict[str, Any]:
        """Get OVH Ryzen server configuration"""
        return self.get('network', 'physical_servers', 'ovh_ryzen', default={})
    
    @property
    def hetzner_xeon_config(self) -> Dict[str, Any]:
        """Get Hetzner Xeon server configuration"""
        return self.get('network', 'physical_servers', 'hetzner_xeon', default={})
    
    # Minecraft Instance Configuration  
    @property
    def excluded_instances(self) -> List[str]:
        """Get list of excluded Minecraft instances"""
        return self.get('network', 'minecraft_instances', 'excluded', default=[])
    
    @property
    def test_instances(self) -> List[str]:
        """Get list of test Minecraft instances"""
        return self.get('network', 'minecraft_instances', 'test_instances', default=[])
    
    @property
    def production_instances(self) -> List[str]:
        """Get list of production Minecraft instances"""
        return self.get('network', 'minecraft_instances', 'production_instances', default=[])
    
    @property
    def all_instances(self) -> List[str]:
        """Get all Minecraft instance names (test + production)"""
        return list(set(self.test_instances + self.production_instances))
    
    # Legacy compatibility properties
    @property
    def excluded_servers(self) -> List[str]:
        """Legacy: Get list of excluded servers (now instances)"""
        return self.excluded_instances
    
    @property
    def test_servers(self) -> List[str]:
        """Legacy: Get list of test servers (now instances)"""
        return self.test_instances
    
    @property
    def production_servers(self) -> List[str]:
        """Legacy: Get list of production servers (now instances)"""
        return self.production_instances
    
    @property
    def all_servers(self) -> List[str]:
        """Legacy: Get all server names (now instances)"""
        return self.all_instances
    
    # MinIO Configuration
    @property
    def minio_config(self) -> MinIOConfig:
        """Get MinIO configuration"""
        config = self.get('storage', 'minio', default={})
        return MinIOConfig(
            endpoint=config.get('endpoint', 'localhost:9000'),
            access_key=config.get('access_key', 'minioadmin'),
            secret_key=config.get('secret_key', 'minioadmin'),
            bucket_name=config.get('bucket_name', 'archivesmp-changes'),
            secure=config.get('secure', False),
            timeout=config.get('timeout', 30),
            retry_attempts=config.get('retry_attempts', 3)
        )
    
    # Agent Configuration
    @property
    def agent_config(self) -> AgentConfig:
        """Get agent configuration"""
        polling = self.get('agent', 'polling', default={})
        safety = self.get('safety', default={})
        
        return AgentConfig(
            change_poll_interval=polling.get('change_poll_interval', 900),
            drift_check_interval=polling.get('drift_check_interval', 3600),
            health_check_interval=polling.get('health_check_interval', 300),
            max_concurrent_changes=safety.get('max_concurrent_changes', 5),
            change_timeout_minutes=safety.get('change_timeout_minutes', 30),
            restart_on_failure=safety.get('restart_on_failure', True),
            max_restart_attempts=safety.get('max_restart_attempts', 3)
        )
    
    # Web API Configuration
    @property
    def web_config(self) -> WebConfig:
        """Get web API configuration"""
        server = self.get('web', 'server', default={})
        limits = self.get('web', 'limits', default={})
        
        return WebConfig(
            host=server.get('host', '0.0.0.0'),
            port=server.get('port', 8000),
            workers=server.get('workers', 4),
            reload=server.get('reload', False),
            max_file_size_mb=limits.get('max_file_size_mb', 10),
            max_request_size_mb=limits.get('max_request_size_mb', 16),
            request_timeout_seconds=limits.get('request_timeout_seconds', 30),
            max_concurrent_requests=limits.get('max_concurrent_requests', 100)
        )
    
    # HTTP Configuration
    @property
    def http_config(self) -> HttpConfig:
        """Get HTTP client configuration"""
        config = self.get('http', default={})
        return HttpConfig(
            timeout_seconds=config.get('timeout_seconds', 10),
            max_retries=config.get('max_retries', 3),
            backoff_seconds=config.get('backoff_seconds', 2),
            user_agent=config.get('user_agent', 'ArchiveSMP-ConfigManager/1.0')
        )
    
    # Plugin Update Configuration
    @property
    def plugin_update_config(self) -> PluginUpdateConfig:
        """Get plugin update configuration"""
        updates = self.get('plugin_updates', default={})
        
        return PluginUpdateConfig(
            check_interval_hours=updates.get('check_interval_hours', 24),
            risk_assessment_enabled=updates.get('risk_assessment_enabled', True),
            spigot_base_url=updates.get('spigot_base_url', 
                                        'https://api.spigotmc.org/simple/0.1/index.php'),
            bukkit_base_url=updates.get('bukkit_base_url',
                                        'https://servermods.forgesvc.net/servermods'),
            github_base_url=updates.get('github_base_url',
                                        'https://api.github.com'),
            timeout=updates.get('timeout', 10),
            rate_limit_delay=updates.get('rate_limit_delay', 1)
        )
    
    # Known Plugin IDs
    def get_plugin_id(self, plugin_name: str, source: str = 'spigot') -> Optional[str]:
        """Get plugin ID for update checking"""
        return self.get('plugins', 'known_plugins', plugin_name, source)
    
    # Safety Configuration
    @property
    def backup_retention_days(self) -> int:
        """Get backup retention period in days"""
        return self.get('safety', 'backup_retention_days', default=30)
    
    @property
    def max_backups_per_file(self) -> int:
        """Get maximum backups per file"""
        return self.get('storage', 'backup', 'max_backups_per_file', default=10)
    
    @property
    def require_backup_before_change(self) -> bool:
        """Check if backup is required before changes"""
        return self.get('safety', 'change_validation', 'require_backup', default=True)
    
    @property
    def dry_run_by_default(self) -> bool:
        """Check if dry run mode is enabled by default"""
        return self.get('safety', 'dry_run_by_default', default=True)
    
    @property
    def min_disk_space_mb(self) -> int:
        """Get minimum required disk space in MB"""
        return self.get('safety', 'system_validation', 'min_disk_space_mb', default=100)
    
    # Database Configuration
    @property
    def production_db_host(self) -> str:
        """Get production database host"""
        return self.get('database', 'production_db_host', default='localhost:3306')
    
    @property
    def production_db_name(self) -> str:
        """Get production database name"""
        return self.get('database', 'production_db_name', default='asmp_SQL')
    
    @property
    def DB_HOST(self) -> str:
        """Get database host (backwards compat)"""
        host_port = self.production_db_host
        return host_port.split(':')[0] if ':' in host_port else host_port
    
    @property
    def DB_PORT(self) -> int:
        """Get database port (backwards compat)"""
        host_port = self.production_db_host
        return int(host_port.split(':')[1]) if ':' in host_port else 3306
    
    @property
    def DB_NAME(self) -> str:
        """Get database name (backwards compat)"""
        return self.production_db_name
    
    @property
    def DB_USER(self) -> str:
        """Get database user"""
        return self.get('database', 'user', default='archivesmp')
    
    @property
    def DB_PASSWORD(self) -> str:
        """Get database password"""
        return self.get('database', 'password', default='')
    
    # Logging Configuration
    @property
    def log_level(self) -> str:
        """Get logging level"""
        return self.get('agent', 'logging', 'level', default='INFO')
    
    @property
    def log_format(self) -> str:
        """Get logging format"""
        return self.get('agent', 'logging', 'log_format', 
                       default='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @property
    def log_to_file(self) -> bool:
        """Check if file logging is enabled"""
        return self.get('agent', 'logging', 'log_to_file', default=True)
    
    @property
    def log_to_console(self) -> bool:
        """Check if console logging is enabled"""
        return self.get('agent', 'logging', 'log_to_console', default=True)
    
    def reload(self) -> None:
        """Reload settings from file"""
        self.settings = self._load_settings()
        self.logger.info("Settings reloaded")


# Global settings instance
_settings_instance: Optional[SettingsHandler] = None


def get_settings(config_file: Optional[Path] = None) -> SettingsHandler:
    """
    Get global settings instance
    
    Args:
        config_file: Path to settings file (only used on first call)
        
    Returns:
        Global settings handler instance
    """
    global _settings_instance
    
    if _settings_instance is None:
        _settings_instance = SettingsHandler(config_file)
    
    return _settings_instance


def reload_settings() -> None:
    """Reload global settings"""
    global _settings_instance
    if _settings_instance:
        _settings_instance.reload()

# Global settings instance
settings = get_settings()
