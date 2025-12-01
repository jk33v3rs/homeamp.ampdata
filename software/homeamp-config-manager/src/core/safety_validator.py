"""
Safety Validator Module

Validates operations before execution to prevent data loss or corruption.
"""

from typing import Dict, List, Any
from pathlib import Path


class SafetyValidator:
    """Validates operations for safety before execution"""
    
    @staticmethod
    def validate_server_exists(server_name: str, utildata_path: Path) -> bool:
        """
        Verify server directory exists
        
        Args:
            server_name: Name of server
            utildata_path: Root utildata path
            
        Returns:
            True if exists
        """
        try:
            # Check if server directory exists in utildata
            server_path = utildata_path / server_name
            if not server_path.exists():
                print(f"Error: Server directory '{server_name}' not found in {utildata_path}")
                return False
            
            if not server_path.is_dir():
                print(f"Error: '{server_name}' exists but is not a directory")
                return False
            
            # Also check for required server subdirectories (plugins, etc.)
            plugins_path = server_path / "plugins"
            if not plugins_path.exists():
                print(f"Warning: Server '{server_name}' missing plugins directory")
                # Don't fail validation, just warn
            
            return True
            
        except Exception as e:
            print(f"Error validating server existence: {e}")
            return False
    
    @staticmethod
    def validate_plugin_exists(server_name: str, plugin_name: str, utildata_path: Path) -> bool:
        """
        Verify plugin directory exists on server
        
        Args:
            server_name: Name of server
            plugin_name: Name of plugin
            utildata_path: Root utildata path
            
        Returns:
            True if exists
        """
        try:
            # First validate server exists
            if not SafetyValidator.validate_server_exists(server_name, utildata_path):
                return False
            
            # Check plugin directory
            plugin_path = utildata_path / server_name / "plugins" / plugin_name
            if not plugin_path.exists():
                print(f"Error: Plugin '{plugin_name}' not found on server '{server_name}'")
                return False
            
            if not plugin_path.is_dir():
                print(f"Error: Plugin '{plugin_name}' exists but is not a directory")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating plugin existence: {e}")
            return False
    
    @staticmethod
    def validate_config_file_exists(server_name: str, plugin_name: str, 
                                   config_file: str, utildata_path: Path) -> bool:
        """
        Verify config file exists
        
        Args:
            server_name: Name of server
            plugin_name: Name of plugin
            config_file: Config file path
            utildata_path: Root utildata path
            
        Returns:
            True if exists
        """
        try:
            # First validate plugin exists
            if not SafetyValidator.validate_plugin_exists(server_name, plugin_name, utildata_path):
                return False
            
            # Check config file
            config_path = utildata_path / server_name / "plugins" / plugin_name / config_file
            if not config_path.exists():
                print(f"Error: Config file '{config_file}' not found for plugin '{plugin_name}' on server '{server_name}'")
                return False
            
            if not config_path.is_file():
                print(f"Error: Config path '{config_file}' exists but is not a file")
                return False
            
            return True
            
        except Exception as e:
            print(f"Error validating config file existence: {e}")
            return False
    
    @staticmethod
    def validate_expected_value(current_value: Any, expected_value: Any, 
                               strict: bool = True) -> bool:
        """
        Validate current value matches expected (safety check)
        
        Args:
            current_value: Actual current value
            expected_value: Expected current value
            strict: If True, require exact match
            
        Returns:
            True if matches
        """
        try:
            if strict:
                # Exact match required
                if current_value == expected_value:
                    return True
                else:
                    print(f"Strict validation failed: '{current_value}' != '{expected_value}'")
                    return False
            else:
                # Loose comparison - handle type conversions
                # Convert both to strings for comparison
                current_str = str(current_value).strip().lower()
                expected_str = str(expected_value).strip().lower()
                
                if current_str == expected_str:
                    return True
                
                # Try numeric comparison if both can be numbers
                try:
                    current_num = float(current_value)
                    expected_num = float(expected_value)
                    if abs(current_num - expected_num) < 1e-9:  # Handle floating point precision
                        return True
                except (ValueError, TypeError):
                    pass
                
                # Try boolean comparison
                if isinstance(current_value, bool) and isinstance(expected_value, bool):
                    return current_value == expected_value
                
                print(f"Loose validation failed: '{current_value}' != '{expected_value}'")
                return False
                
        except Exception as e:
            print(f"Error validating expected value: {e}")
            return False
    
    @staticmethod
    def validate_change_request_format(change_request: Dict[str, Any]) -> List[str]:
        """
        Validate change request JSON structure
        
        Args:
            change_request: Change request dict
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Required fields
            required_fields = ['server_name', 'plugin_name', 'config_file', 'changes']
            for field in required_fields:
                if field not in change_request:
                    errors.append(f"Missing required field: {field}")
                elif not change_request[field]:
                    errors.append(f"Empty required field: {field}")
            
            # Validate changes structure
            if 'changes' in change_request:
                changes = change_request['changes']
                if not isinstance(changes, list):
                    errors.append("'changes' must be a list")
                else:
                    for i, change in enumerate(changes):
                        if not isinstance(change, dict):
                            errors.append(f"Change {i} must be a dict")
                            continue
                        
                        # Each change must have key_path and new_value
                        if 'key_path' not in change:
                            errors.append(f"Change {i} missing 'key_path'")
                        if 'new_value' not in change:
                            errors.append(f"Change {i} missing 'new_value'")
                        
                        # Optional expected_value validation
                        if 'expected_value' in change and change['expected_value'] is None:
                            errors.append(f"Change {i} has null expected_value (should be omitted if not needed)")
            
            # Validate server_name format
            if 'server_name' in change_request:
                server_name = change_request['server_name']
                if not isinstance(server_name, str) or len(server_name.strip()) == 0:
                    errors.append("server_name must be a non-empty string")
            
            # Validate plugin_name format
            if 'plugin_name' in change_request:
                plugin_name = change_request['plugin_name']
                if not isinstance(plugin_name, str) or len(plugin_name.strip()) == 0:
                    errors.append("plugin_name must be a non-empty string")
            
            return errors
            
        except Exception as e:
            errors.append(f"Error validating change request format: {e}")
            return errors
    
    @staticmethod
    def validate_no_file_locks(file_path: Path) -> bool:
        """
        Check if file is locked by another process
        
        Args:
            file_path: File to check
            
        Returns:
            True if not locked
        """
        import os
        
        try:
            if not file_path.exists():
                # File doesn't exist, so no lock
                return True
            
            # Try to open the file for writing to check if locked
            try:
                with open(file_path, 'r+') as f:
                    # If we can open for reading/writing, it's not locked
                    pass
                return True
            except (IOError, OSError, PermissionError) as e:
                # File is likely locked or we don't have permissions
                if "being used by another process" in str(e) or "Permission denied" in str(e):
                    print(f"File appears to be locked: {file_path} ({e})")
                    return False
                else:
                    # Other error, assume not locked but warn
                    print(f"Warning: Could not verify lock status for {file_path}: {e}")
                    return True
                    
        except Exception as e:
            print(f"Error checking file lock status: {e}")
            return True  # Assume not locked on error
    
    @staticmethod
    def validate_disk_space(path: Path, required_mb: int = 100) -> bool:
        """
        Check if sufficient disk space available
        
        Args:
            path: Path to check
            required_mb: Required space in MB
            
        Returns:
            True if sufficient space
        """
        import shutil
        
        try:
            # Get the parent directory if path is a file
            check_path = path if path.is_dir() else path.parent
            
            # Ensure the directory exists
            if not check_path.exists():
                check_path = check_path.parent
                while not check_path.exists() and check_path != check_path.parent:
                    check_path = check_path.parent
            
            # Get disk usage
            total, used, free = shutil.disk_usage(check_path)
            
            # Convert to MB
            free_mb = free / (1024 * 1024)
            required_mb_float = float(required_mb)
            
            if free_mb >= required_mb_float:
                return True
            else:
                print(f"Insufficient disk space: {free_mb:.1f}MB available, {required_mb}MB required")
                return False
                
        except Exception as e:
            print(f"Error checking disk space: {e}")
            return True  # Assume sufficient space on error to avoid blocking operations
