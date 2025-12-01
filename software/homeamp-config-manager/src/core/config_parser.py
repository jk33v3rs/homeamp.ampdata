"""
Config Parser Module

Handles parsing of various configuration file formats (YAML, JSON, properties, etc.)
with robust error handling and type preservation.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import yaml
import json


class ConfigParser:
    """Parse and manipulate configuration files"""
    
    @staticmethod
    def load_config(file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load configuration file with automatic format detection
        
        Args:
            file_path: Path to config file
            
        Returns:
            Parsed config dict or None if failed
        """
        try:
            if not file_path.exists():
                print(f"Config file does not exist: {file_path}")
                return None
            
            # Read file content with BOM handling
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                content = file.read().strip()
            
            if not content:
                print(f"Config file is empty: {file_path}")
                return {}
            
            # Detect format by extension
            file_ext = file_path.suffix.lower()
            
            if file_ext in ['.yml', '.yaml']:
                try:
                    return yaml.safe_load(content) or {}
                except yaml.YAMLError as e:
                    print(f"YAML parsing error in {file_path}: {e}")
                    return None
                    
            elif file_ext == '.json':
                try:
                    # Handle empty JSON files
                    if not content or content == '{}':
                        return {}
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error in {file_path}: {e}")
                    return None
                    
            elif file_ext in ['.properties', '.cfg', '.conf']:
                # Parse properties format
                config = {}
                for line_num, line in enumerate(content.splitlines(), 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Try to convert to appropriate type
                        if value.lower() in ['true', 'false']:
                            value = value.lower() == 'true'
                        elif value.isdigit():
                            value = int(value)
                        elif '.' in value and value.replace('.', '', 1).isdigit() and value.count('.') == 1:
                            # Only convert to float if it's a single decimal number (not IP address)
                            value = float(value)
                        # Leave IP addresses and other strings as-is
                        
                        config[key] = value
                    else:
                        print(f"Invalid properties format at line {line_num}: {line}")
                
                return config
            else:
                print(f"Unsupported config format: {file_ext}")
                return None
                
        except Exception as e:
            print(f"Error loading config {file_path}: {e}")
            return None
    
    @staticmethod
    def save_config(file_path: Path, data: Dict[str, Any]) -> bool:
        """
        Save configuration file in appropriate format
        
        Args:
            file_path: Path to save to
            data: Configuration data
            
        Returns:
            True if successful
        """
        from .file_handler import FileHandler
        
        try:
            # Auto-detect format by extension
            suffix = file_path.suffix.lower()
            
            if suffix in ['.yml', '.yaml']:
                content = yaml.dump(data, default_flow_style=False, indent=2)
            elif suffix == '.json':
                content = json.dumps(data, indent=2, separators=(',', ': '))
            elif suffix == '.properties':
                # Flatten dict for properties format
                flattened = ConfigParser.flatten_dict(data)
                content = '\n'.join(f"{k}={v}" for k, v in flattened.items())
            else:
                # Default to YAML for unknown extensions
                content = yaml.dump(data, default_flow_style=False, indent=2)
            
            # Use FileHandler for safe writing
            backup_root = file_path.parent / '.backups'
            file_handler = FileHandler(backup_root)
            return file_handler.atomic_write(file_path, content)
            
        except Exception as e:
            print(f"Error saving config {file_path}: {e}")
            return False
    
    @staticmethod
    def get_nested_value(data: Dict[str, Any], key_path: str) -> Optional[Any]:
        """
        Get value from nested dict using dot notation
        
        Args:
            data: Configuration dict
            key_path: Dot-separated path (e.g., "database.mysql.host")
            
        Returns:
            Value at path or None if not found
        """
        try:
            keys = key_path.split('.')
            current = data
            
            for key in keys:
                if not isinstance(current, dict) or key not in current:
                    return None
                current = current[key]
            
            return current
            
        except Exception as e:
            print(f"Error getting nested value '{key_path}': {e}")
            return None
    
    @staticmethod
    def set_nested_value(data: Dict[str, Any], key_path: str, value: Any) -> Dict[str, Any]:
        """
        Set value in nested dict using dot notation
        
        Args:
            data: Configuration dict
            key_path: Dot-separated path
            value: Value to set
            
        Returns:
            Modified dict
        """
        try:
            keys = key_path.split('.')
            current = data
            
            # Navigate to parent of target key
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                elif not isinstance(current[key], dict):
                    # Convert non-dict to dict if needed
                    current[key] = {}
                current = current[key]
            
            # Set the final value
            current[keys[-1]] = value
            
            return data
            
        except Exception as e:
            print(f"Error setting nested value '{key_path}': {e}")
            return data
    
    @staticmethod
    def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten nested dict to dot notation
        
        Args:
            data: Nested dict
            parent_key: Parent key prefix
            sep: Separator character
            
        Returns:
            Flattened dict
        """
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dicts
                items.extend(ConfigParser.flatten_dict(value, new_key, sep).items())
            else:
                # Convert value to string for properties format
                items.append((new_key, str(value)))
        
        return dict(items)
    
    @staticmethod
    def unflatten_dict(data: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
        """
        Unflatten dot notation dict to nested structure
        
        Args:
            data: Flattened dict
            sep: Separator character
            
        Returns:
            Nested dict
        """
        result = {}
        
        for key, value in data.items():
            parts = key.split(sep)
            current = result
            
            # Navigate to parent of target key, creating dicts as needed
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the final value
            current[parts[-1]] = value
        
        return result
    
    @staticmethod
    def validate_yaml(file_path: Path) -> bool:
        """
        Validate YAML file syntax
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            True if valid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            print(f"YAML validation error in {file_path}: {e}")
            return False
        except Exception as e:
            print(f"Error validating YAML {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_json(file_path: Path) -> bool:
        """
        Validate JSON file syntax
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            True if valid
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except json.JSONDecodeError as e:
            print(f"JSON validation error in {file_path}: {e}")
            return False
        except Exception as e:
            print(f"Error validating JSON {file_path}: {e}")
            return False
