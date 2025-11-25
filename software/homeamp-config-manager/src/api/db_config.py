"""
Database Configuration Helper

Provides centralized database connection configuration for both API endpoints and agent modules.
Reads credentials from agent.yaml config file using the SettingsHandler.
"""

import mysql.connector
import os
from pathlib import Path
from typing import Dict, Any

# Try to import settings, fall back to direct yaml loading if not available
try:
    from ..core.settings import SettingsHandler

    _settings = SettingsHandler()
    _USE_SETTINGS = True
except Exception as e:
    _settings = None
    _USE_SETTINGS = False
    # Log the import failure for debugging
    import sys

    print(f"Warning: Could not import SettingsHandler: {e}", file=sys.stderr)


def get_db_config() -> Dict[str, Any]:
    """
    Get database configuration as dictionary.

    Returns dict with keys: host, port, user, password, database
    Useful for passing to classes that need db_config parameter.

    Returns:
        Dictionary with database connection parameters
    """
    if _USE_SETTINGS and _settings:
        return {
            "host": _settings.DB_HOST,
            "port": _settings.DB_PORT,
            "user": _settings.DB_USER,
            "password": _settings.DB_PASSWORD,
            "database": _settings.DB_NAME,
        }
    else:
        # Fallback: try to load from agent.yaml directly
        import yaml

        config_path = Path("/etc/archivesmp/agent.yaml")
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                db_config = config.get("database", {})
                return {
                    "host": db_config.get("host", ""),
                    "port": db_config.get("port", 3369),
                    "user": db_config.get("user", ""),
                    "password": db_config.get("password", ""),
                    "database": db_config.get("database", ""),
                }
        else:
            # Final fallback to environment variables
            return {
                "host": os.getenv("DB_HOST", ""),
                "port": int(os.getenv("DB_PORT", "3369")),
                "user": os.getenv("DB_USER", ""),
                "password": os.getenv("DB_PASSWORD", ""),
                "database": os.getenv("DB_NAME", ""),
            }


def get_db_connection():
    """
    Get database connection using settings from agent.yaml.

    Uses the proper SettingsHandler from core.settings which:
    - Searches multiple config file locations
    - Supports environment variable overrides
    - Handles proper type conversions

    Returns:
        mysql.connector connection object
    """
    config = get_db_config()

    return mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
    )


# Alias for backwards compatibility
get_db = get_db_connection
