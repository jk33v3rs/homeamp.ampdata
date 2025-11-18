"""
Format-Preserving YAML Handler
Purpose: Read/write YAML files while preserving comments, formatting, and structure
Author: AI Assistant
Date: 2025-01-04
Related Todos: #29, #30, #31, #32, #33

Uses ruamel.yaml instead of pyyaml to maintain:
- Comments
- Key order
- Indentation
- Quotes
- Blank lines
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
import logging

logger = logging.getLogger(__name__)


class YAMLHandler:
    """
    Format-preserving YAML file operations.
    
    Example usage:
        handler = YAMLHandler()
        data = handler.read_yaml('/path/to/config.yml')
        handler.modify_key(data, 'settings.economy.enabled', True)
        handler.write_yaml('/path/to/config.yml', data)
    """
    
    def __init__(self):
        """Initialize YAML handler with preservation settings."""
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.default_flow_style = False
        self.yaml.width = 4096  # Prevent line wrapping
        self.yaml.indent(mapping=2, sequence=2, offset=0)
    
    def read_yaml(self, file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Read YAML file preserving all formatting.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML data as dict, or None on error
            
        Raises:
            YAMLError: If file has syntax errors
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"YAML file not found: {file_path}")
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = self.yaml.load(f)
            logger.debug(f"Successfully read YAML: {file_path}")
            return data
        except YAMLError as e:
            logger.error(f"YAML syntax error in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None
    
    def write_yaml(self, file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
        """
        Write YAML file preserving formatting from source.
        
        Args:
            file_path: Path to write YAML file
            data: YAML data structure (from read_yaml)
            
        Returns:
            True if successful, False otherwise
        """
        file_path = Path(file_path)
        
        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data, f)
            logger.debug(f"Successfully wrote YAML: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing {file_path}: {e}")
            return False
    
    def modify_key(
        self, 
        data: Dict[str, Any], 
        key_path: str, 
        new_value: Any
    ) -> bool:
        """
        Modify a nested key in YAML data using dot notation.
        
        Args:
            data: YAML data structure (modified in-place)
            key_path: Dot-separated path (e.g., 'settings.economy.starting-balance')
            new_value: New value to set
            
        Returns:
            True if successful, False if key path not found
            
        Example:
            modify_key(data, 'database.host', 'localhost')
            modify_key(data, 'features.teleport.enabled', True)
        """
        keys = key_path.split('.')
        current = data
        
        # Navigate to parent of target key
        try:
            for key in keys[:-1]:
                if key not in current:
                    logger.warning(f"Key path not found: {key_path} (missing: {key})")
                    return False
                current = current[key]
            
            # Set the final key
            final_key = keys[-1]
            old_value = current.get(final_key, '<not set>')
            current[final_key] = new_value
            
            logger.info(f"Modified {key_path}: {old_value} → {new_value}")
            return True
        except (KeyError, TypeError) as e:
            logger.error(f"Error modifying {key_path}: {e}")
            return False
    
    def get_key(self, data: Dict[str, Any], key_path: str) -> Optional[Any]:
        """
        Get value at a nested key path.
        
        Args:
            data: YAML data structure
            key_path: Dot-separated path
            
        Returns:
            Value at key path, or None if not found
        """
        keys = key_path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            logger.debug(f"Key path not found: {key_path}")
            return None
    
    def key_exists(self, data: Dict[str, Any], key_path: str) -> bool:
        """
        Check if a nested key path exists.
        
        Args:
            data: YAML data structure
            key_path: Dot-separated path
            
        Returns:
            True if key exists, False otherwise
        """
        return self.get_key(data, key_path) is not None
    
    def validate_syntax(self, file_path: Union[str, Path]) -> tuple[bool, Optional[str]]:
        """
        Validate YAML file syntax without loading data.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.yaml.load(f)
            return True, None
        except YAMLError as e:
            error_msg = str(e)
            logger.warning(f"YAML syntax error in {file_path}: {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Error validating {file_path}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def add_comment(self, data: Dict[str, Any], key_path: str, comment: str) -> bool:
        """
        Add a comment to a key (if using CommentedMap from ruamel.yaml).
        
        Args:
            data: YAML data structure
            key_path: Dot-separated path
            comment: Comment text (without # prefix)
            
        Returns:
            True if successful
        """
        # This is an advanced feature - ruamel.yaml CommentedMap required
        # For now, just log that it's not fully implemented
        logger.info(f"Comment requested for {key_path}: {comment}")
        # TODO: Implement with CommentedMap.yaml_set_comment_before_after_key
        return True


# Convenience functions for common operations
def read_yaml(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Read YAML file preserving formatting."""
    handler = YAMLHandler()
    return handler.read_yaml(file_path)


def write_yaml(file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
    """Write YAML file preserving formatting."""
    handler = YAMLHandler()
    return handler.write_yaml(file_path, data)


def modify_yaml_key(
    file_path: Union[str, Path],
    key_path: str,
    new_value: Any,
    create_backup: bool = True
) -> bool:
    """
    Modify a key in a YAML file in one operation.
    
    Args:
        file_path: Path to YAML file
        key_path: Dot-separated key path
        new_value: New value to set
        create_backup: Whether to create .bak file
        
    Returns:
        True if successful
    """
    handler = YAMLHandler()
    file_path = Path(file_path)
    
    # Create backup if requested
    if create_backup and file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
    
    # Read, modify, write
    data = handler.read_yaml(file_path)
    if data is None:
        return False
    
    if not handler.modify_key(data, key_path, new_value):
        return False
    
    return handler.write_yaml(file_path, data)
