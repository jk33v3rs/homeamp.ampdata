"""
File Handler Module

Handles file operations with safety checks, atomic writes,
and backup management.
"""

from typing import Optional
from pathlib import Path
import shutil
import os
from datetime import datetime


class FileHandler:
    """Safe file operations with backup and rollback"""
    
    def __init__(self, backup_root: Path):
        """
        Initialize file handler
        
        Args:
            backup_root: Root directory for backups
        """
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, file_path: Path) -> Path:
        """
        Create timestamped backup of a file
        
        Args:
            file_path: File to backup
            
        Returns:
            Path to backup file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")
        
        # Create timestamp-based backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        
        # Create backup directory structure matching original path
        relative_path = file_path.parent.relative_to(file_path.anchor) if file_path.is_absolute() else file_path.parent
        backup_dir = self.backup_root / relative_path
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backup_path = backup_dir / backup_name
        
        # Copy file with metadata preservation
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    def atomic_write(self, file_path: Path, content: str) -> bool:
        """
        Write file atomically (temp file + rename)
        
        Args:
            file_path: Target file path
            content: Content to write
            
        Returns:
            True if successful
        """
        import tempfile
        import os
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temporary file in same directory as target
            temp_fd, temp_path = tempfile.mkstemp(
                dir=file_path.parent,
                prefix=f".{file_path.name}.tmp.",
                text=True
            )
            
            try:
                # Write content to temp file
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    os.fsync(temp_file.fileno())  # Force write to disk
                
                # Atomic rename (replaces target file)
                temp_path_obj = Path(temp_path)
                temp_path_obj.replace(file_path)
                
                return True
                
            except Exception:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                raise
                
        except Exception as e:
            print(f"Atomic write failed for {file_path}: {e}")
            return False
    
    def safe_read(self, file_path: Path) -> Optional[str]:
        """
        Safely read file with error handling
        
        Args:
            file_path: File to read
            
        Returns:
            File contents or None if error
        """
        try:
            # Check if file exists and is readable
            if not file_path.exists():
                print(f"File does not exist: {file_path}")
                return None
                
            if not file_path.is_file():
                print(f"Path is not a file: {file_path}")
                return None
                
            # Check file permissions
            if not os.access(file_path, os.R_OK):
                print(f"File is not readable: {file_path}")
                return None
            
            # Read file with explicit encoding
            with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
                content = file.read()
                
            return content
            
        except PermissionError:
            print(f"Permission denied reading file: {file_path}")
            return None
        except UnicodeDecodeError as e:
            print(f"Unicode decode error reading {file_path}: {e}")
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception:
                return None
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def rollback_from_backup(self, backup_path: Path, target_path: Path) -> bool:
        """
        Restore file from backup
        
        Args:
            backup_path: Backup file
            target_path: Where to restore to
            
        Returns:
            True if successful
        """
        try:
            # Verify backup file exists
            if not backup_path.exists():
                print(f"Backup file does not exist: {backup_path}")
                return False
                
            if not backup_path.is_file():
                print(f"Backup path is not a file: {backup_path}")
                return False
            
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup of current file before rollback (if it exists)
            if target_path.exists():
                rollback_backup = self.create_backup(target_path)
                print(f"Created rollback backup: {rollback_backup}")
            
            # Copy backup to target location with metadata preservation
            shutil.copy2(backup_path, target_path)
            
            print(f"Successfully rolled back {target_path} from {backup_path}")
            return True
            
        except Exception as e:
            print(f"Rollback failed from {backup_path} to {target_path}: {e}")
            return False
    
    def cleanup_old_backups(self, max_age_days: int = 30, keep_minimum: int = 5) -> int:
        """
        Clean up old backup files
        
        Args:
            max_age_days: Delete backups older than this
            keep_minimum: Always keep at least this many backups
            
        Returns:
            Number of backups deleted
        """
        import time
        
        deleted_count = 0
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        try:
            # Find all backup files recursively
            backup_files = []
            for root, dirs, files in os.walk(self.backup_root):
                for file in files:
                    if file.endswith('.backup'):
                        file_path = Path(root) / file
                        try:
                            # Get file modification time
                            file_mtime = file_path.stat().st_mtime
                            backup_files.append((file_path, file_mtime))
                        except OSError:
                            continue
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Keep minimum number of backups regardless of age
            files_to_check = backup_files[keep_minimum:]
            
            # Delete old backups
            for file_path, file_mtime in files_to_check:
                file_age = current_time - file_mtime
                
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        print(f"Deleted old backup: {file_path}")
                    except OSError as e:
                        print(f"Failed to delete backup {file_path}: {e}")
            
            print(f"Cleanup completed: deleted {deleted_count} old backups")
            return deleted_count
            
        except Exception as e:
            print(f"Backup cleanup failed: {e}")
            return 0
    
    def verify_file_integrity(self, file_path: Path) -> bool:
        """
        Verify file can be read and parsed
        
        Args:
            file_path: File to verify
            
        Returns:
            True if file is valid
        """
        import hashlib
        import yaml
        import json
        
        try:
            # First check if file can be read
            content = self.safe_read(file_path)
            if content is None:
                return False
            
            # Calculate checksum for basic integrity
            content_bytes = content.encode('utf-8')
            checksum = hashlib.sha256(content_bytes).hexdigest()
            
            # Try to parse based on file extension
            file_ext = file_path.suffix.lower()
            
            if file_ext in ['.yml', '.yaml']:
                try:
                    yaml.safe_load(content)
                    print(f"YAML file {file_path} is valid (checksum: {checksum[:8]}...)")
                    return True
                except yaml.YAMLError as e:
                    print(f"YAML parsing failed for {file_path}: {e}")
                    return False
                    
            elif file_ext == '.json':
                try:
                    json.loads(content)
                    print(f"JSON file {file_path} is valid (checksum: {checksum[:8]}...)")
                    return True
                except json.JSONDecodeError as e:
                    print(f"JSON parsing failed for {file_path}: {e}")
                    return False
                    
            elif file_ext in ['.properties', '.cfg', '.conf']:
                # Basic validation for properties files
                try:
                    # Check for basic key=value format
                    lines = content.splitlines()
                    for line_num, line in enumerate(lines, 1):
                        line = line.strip()
                        if line and not line.startswith('#') and '=' not in line:
                            print(f"Invalid properties format at line {line_num}: {line}")
                            return False
                    print(f"Properties file {file_path} is valid (checksum: {checksum[:8]}...)")
                    return True
                except Exception as e:
                    print(f"Properties validation failed for {file_path}: {e}")
                    return False
            else:
                # For other file types, just check readability
                print(f"File {file_path} is readable (checksum: {checksum[:8]}...)")
                return True
                
        except Exception as e:
            print(f"File integrity check failed for {file_path}: {e}")
            return False
