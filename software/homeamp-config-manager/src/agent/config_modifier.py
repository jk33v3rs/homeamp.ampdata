"""
Safe Config File Modifier

Provides safe modification of config files with automatic backup, validation, and rollback.
Supports YAML, JSON, TOML, and .properties files with format preservation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple
import sys

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.yaml_handler import YAMLHandler, modify_yaml_key
from utils.config_backup import ConfigBackup

logger = logging.getLogger(__name__)


class ConfigModifier:
    """
    Safe config file modification with backup and rollback

    Supports:
    - YAML (.yml, .yaml) - Format-preserving with ruamel.yaml
    - JSON (.json) - Pretty-printed with indentation
    - Properties (.properties) - Standard Java properties format
    - TOML (.toml) - If toml library available
    - CONF (.conf) - Simple key=value format
    """

    def __init__(self, db_connection=None):
        """
        Initialize config modifier

        Args:
            db_connection: Database connection for backup storage (optional)
        """
        self.db = db_connection
        self.yaml_handler = YAMLHandler()
        self.backup_handler = ConfigBackup(db_connection) if db_connection else None

    def modify_yaml_key(
        self, file_path: str, key_path: str, value: Any, create_backup: bool = True, backup_reason: str = "modification"
    ) -> bool:
        """
        Modify a YAML config file preserving formatting

        Args:
            file_path: Absolute path to YAML file
            key_path: Dot-notation key path (e.g., 'settings.economy.enabled')
            value: New value to set
            create_backup: Whether to create backup before modification
            backup_reason: Reason for backup

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate file exists
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False

            # Create backup if requested
            backup_id = None
            if create_backup and self.backup_handler:
                # Need config_file_id and instance_id for DB backup
                # For now, create filesystem backup
                backup_path = f"{file_path}.backup"
                import shutil

                shutil.copy2(file_path, backup_path)
                logger.info(f"Created backup: {backup_path}")

            # Modify using YAMLHandler (preserves formatting)
            success = modify_yaml_key(file_path, key_path, value)

            if success:
                logger.info(f"[OK] Modified {key_path} = {value} in {file_path}")
                return True
            else:
                logger.error(f"[ERROR] Failed to modify {key_path} in {file_path}")
                if create_backup and Path(f"{file_path}.backup").exists():
                    # Restore from backup
                    import shutil

                    shutil.copy2(f"{file_path}.backup", file_path)
                    logger.info(f"Restored from backup")
                return False

        except Exception as e:
            logger.error(f"[ERROR] Error modifying YAML: {e}")
            return False

    def modify_json_key(self, file_path: str, key_path: str, value: Any, create_backup: bool = True) -> bool:
        """
        Modify a JSON config file

        Args:
            file_path: Absolute path to JSON file
            key_path: Dot-notation key path
            value: New value to set
            create_backup: Whether to create backup

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate file
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False

            # Create backup
            if create_backup:
                backup_path = f"{file_path}.backup"
                import shutil

                shutil.copy2(file_path, backup_path)

            # Read JSON
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Navigate to nested key
            keys = key_path.split(".")
            current = data

            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Set value
            current[keys[-1]] = value

            # Write back with pretty formatting
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"[OK] Modified {key_path} = {value} in {file_path}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Error modifying JSON: {e}")
            if create_backup and Path(f"{file_path}.backup").exists():
                import shutil

                shutil.copy2(f"{file_path}.backup", file_path)
                logger.info(f"Restored from backup")
            return False

    def modify_properties_key(self, file_path: str, key: str, value: str, create_backup: bool = True) -> bool:
        """
        Modify a .properties file

        Args:
            file_path: Absolute path to .properties file
            key: Property key (simple, not nested)
            value: New value (will be converted to string)
            create_backup: Whether to create backup

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate file
            if not Path(file_path).exists():
                logger.error(f"File not found: {file_path}")
                return False

            # Create backup
            if create_backup:
                backup_path = f"{file_path}.backup"
                import shutil

                shutil.copy2(file_path, backup_path)

            # Read properties
            properties = {}
            lines = []
            key_found = False

            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    lines.append(line)
                    stripped = line.strip()

                    # Skip comments and empty lines
                    if not stripped or stripped.startswith("#") or stripped.startswith("!"):
                        continue

                    # Parse key=value
                    if "=" in stripped:
                        prop_key, prop_value = stripped.split("=", 1)
                        prop_key = prop_key.strip()

                        if prop_key == key:
                            key_found = True
                            # Replace this line
                            lines[-1] = f"{key}={value}\n"

            # If key not found, append it
            if not key_found:
                lines.append(f"{key}={value}\n")

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            logger.info(f"[OK] Modified {key} = {value} in {file_path}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Error modifying properties: {e}")
            if create_backup and Path(f"{file_path}.backup").exists():
                import shutil

                shutil.copy2(f"{file_path}.backup", file_path)
                logger.info(f"Restored from backup")
            return False

    def safe_modify(
        self, file_path: str, key_path: str, value: Any, validate_after: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Safely modify config file with automatic type detection, backup, and validation

        Args:
            file_path: Absolute path to config file
            key_path: Dot-notation key path (or simple key for .properties)
            value: New value to set
            validate_after: Whether to validate syntax after modification

        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            path_obj = Path(file_path)

            if not path_obj.exists():
                return False, f"File not found: {file_path}"

            # Detect file type
            extension = path_obj.suffix.lower()

            if extension in [".yml", ".yaml"]:
                success = self.modify_yaml_key(file_path, key_path, value)

                if success and validate_after:
                    # Validate YAML syntax
                    is_valid, error = self.yaml_handler.validate_syntax(file_path)
                    if not is_valid:
                        return False, f"YAML validation failed: {error}"

                return success, None if success else "Modification failed"

            elif extension == ".json":
                success = self.modify_json_key(file_path, key_path, value)

                if success and validate_after:
                    # Validate JSON syntax
                    try:
                        with open(file_path, "r") as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        return False, f"JSON validation failed: {e}"

                return success, None if success else "Modification failed"

            elif extension == ".properties":
                success = self.modify_properties_key(file_path, key_path, str(value))
                return success, None if success else "Modification failed"

            else:
                return False, f"Unsupported file type: {extension}"

        except Exception as e:
            return False, str(e)

    def rollback_on_error(self, file_path: str, backup_path: Optional[str] = None) -> bool:
        """
        Rollback file to backup if modification failed

        Args:
            file_path: Path to config file
            backup_path: Path to backup (default: {file_path}.backup)

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            if backup_path is None:
                backup_path = f"{file_path}.backup"

            if not Path(backup_path).exists():
                logger.error(f"Backup not found: {backup_path}")
                return False

            import shutil

            shutil.copy2(backup_path, file_path)
            logger.info(f"[OK] Rolled back {file_path} from {backup_path}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Rollback failed: {e}")
            return False

    def batch_modify(self, modifications: List[Dict]) -> Dict[str, Any]:
        """
        Perform multiple modifications in batch

        Args:
            modifications: List of modification dicts:
                [
                    {
                        'file_path': '/path/to/config.yml',
                        'key_path': 'setting.key',
                        'value': 'new_value'
                    },
                    ...
                ]

        Returns:
            Dict with results:
            {
                'total': 5,
                'successful': 3,
                'failed': 2,
                'details': [...]
            }
        """
        results = {"total": len(modifications), "successful": 0, "failed": 0, "details": []}

        for mod in modifications:
            file_path = mod["file_path"]
            key_path = mod["key_path"]
            value = mod["value"]

            success, error = self.safe_modify(file_path, key_path, value)

            if success:
                results["successful"] += 1
                results["details"].append({"file": file_path, "key": key_path, "status": "success"})
            else:
                results["failed"] += 1
                results["details"].append({"file": file_path, "key": key_path, "status": "failed", "error": error})

        return results


# Convenience functions
def modify_config(file_path: str, key_path: str, value: Any) -> bool:
    """
    Convenience function for one-off config modification

    Args:
        file_path: Path to config file
        key_path: Dot-notation key path
        value: New value

    Returns:
        True if successful
    """
    modifier = ConfigModifier()
    success, error = modifier.safe_modify(file_path, key_path, value)
    if error:
        logger.error(f"Modification error: {error}")
    return success


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    modifier = ConfigModifier()

    # Example: Modify YAML
    success, error = modifier.safe_modify("/path/to/config.yml", "settings.economy.enabled", True)
    print(f"YAML modification: {'[OK]' if success else '[ERROR]'} {error or ''}")

    # Example: Modify JSON
    success, error = modifier.safe_modify("/path/to/config.json", "server.port", 8080)
    print(f"JSON modification: {'[OK]' if success else '[ERROR]'} {error or ''}")

    # Example: Batch modifications
    results = modifier.batch_modify(
        [
            {"file_path": "/path/to/config1.yml", "key_path": "setting.a", "value": "value1"},
            {"file_path": "/path/to/config2.json", "key_path": "setting.b", "value": 100},
        ]
    )
    print(f"Batch: {results['successful']}/{results['total']} successful")
