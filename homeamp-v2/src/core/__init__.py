"""HomeAMP V2.0 Core Layer - Database, Configuration, Logging, Exceptions."""

from homeamp_v2.core.config import Settings, get_settings
from homeamp_v2.core.database import (
    Base,
    get_engine,
    get_session,
    init_db,
    session_scope,
)
from homeamp_v2.core.exceptions import (
    AgentError,
    AuthenticationError,
    BackupError,
    ConfigNotFoundError,
    DatabaseError,
    DeploymentError,
    DiscoveryError,
    HomeAMPException,
    InstanceNotFoundError,
    IntegrationError,
    PluginNotFoundError,
    UpdateCheckError,
    ValidationError,
)
from homeamp_v2.core.logging import audit_log, get_logger, setup_logging

__all__ = [
    # Config
    "Settings",
    "get_settings",
    # Database
    "Base",
    "get_engine",
    "get_session",
    "init_db",
    "session_scope",
    # Logging
    "get_logger",
    "setup_logging",
    "audit_log",
    # Exceptions
    "HomeAMPException",
    "DatabaseError",
    "ValidationError",
    "InstanceNotFoundError",
    "PluginNotFoundError",
    "ConfigNotFoundError",
    "DeploymentError",
    "BackupError",
    "DiscoveryError",
    "UpdateCheckError",
    "AuthenticationError",
    "IntegrationError",
    "AgentError",
]
