"""
Config Backup and Rollback System

Manages configuration file backups with:
- Timestamped .bak files
- Organized by server/plugin/date
- Restoration interface
- Integration with AMP backup API
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json


class ConfigBackupManager:
    """Manage configuration backups and rollbacks"""
    
    def __init__(self, backup_root: Path):
        """
        Initialize backup manager
        
        Args:
            backup_root: Root directory for backups
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def backup_config(self, config_file: Path, server_name: str, 
                     plugin_name: str) -> Optional[Path]:
        """
        Create timestamped backup of a configuration file
        
        Args:
            config_file: Path to config file to backup
            server_name: Server name (e.g., 'DEV01', 'PROD01')
            plugin_name: Plugin name
            
        Returns:
            Path to backup file, or None if failed
        """
        try:
            if not config_file.exists():
                self.logger.error(f"Config file does not exist: {config_file}")
                return None
            
            # Create backup directory structure: backups/server/plugin/date/
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.backup_root / server_name / plugin_name / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup filename: original_name.bak
            backup_file = backup_dir / f"{config_file.name}.bak"
            
            # Copy file
            shutil.copy2(config_file, backup_file)
            
            # Create metadata file
            metadata = {
                'original_path': str(config_file),
                'backup_time': datetime.now().isoformat(),
                'server': server_name,
                'plugin': plugin_name,
                'file_size': config_file.stat().st_size
            }
            
            metadata_file = backup_dir / 'backup_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Backed up {config_file.name} to {backup_file}")
            return backup_file
            
        except Exception as e:
            self.logger.error(f"Error backing up config: {e}")
            return None
    
    def backup_plugin_configs(self, plugin_dir: Path, server_name: str, 
                             plugin_name: str) -> Optional[Path]:
        """
        Backup all config files for a plugin
        
        Args:
            plugin_dir: Plugin directory containing configs
            server_name: Server name
            plugin_name: Plugin name
            
        Returns:
            Path to backup directory, or None if failed
        """
        try:
            if not plugin_dir.exists() or not plugin_dir.is_dir():
                self.logger.error(f"Plugin directory does not exist: {plugin_dir}")
                return None
            
            # Create backup directory
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.backup_root / server_name / plugin_name / timestamp
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup all config files
            config_extensions = ['.yml', '.yaml', '.json', '.properties', '.conf', '.cfg']
            backed_up_files = []
            
            for config_file in plugin_dir.rglob('*'):
                if config_file.is_file() and config_file.suffix in config_extensions:
                    # Preserve directory structure
                    rel_path = config_file.relative_to(plugin_dir)
                    backup_file = backup_dir / f"{rel_path}.bak"
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(config_file, backup_file)
                    backed_up_files.append(str(rel_path))
            
            # Create metadata
            metadata = {
                'original_path': str(plugin_dir),
                'backup_time': datetime.now().isoformat(),
                'server': server_name,
                'plugin': plugin_name,
                'files_backed_up': backed_up_files,
                'total_files': len(backed_up_files)
            }
            
            metadata_file = backup_dir / 'backup_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Backed up {len(backed_up_files)} config files for {plugin_name}")
            return backup_dir
            
        except Exception as e:
            self.logger.error(f"Error backing up plugin configs: {e}")
            return None
    
    def restore_config(self, backup_path: Path, restore_to: Optional[Path] = None) -> bool:
        """
        Restore a configuration file from backup
        
        Args:
            backup_path: Path to backup file (.bak)
            restore_to: Optional path to restore to (default: original location)
            
        Returns:
            True if successful
        """
        try:
            if not backup_path.exists():
                self.logger.error(f"Backup file does not exist: {backup_path}")
                return False
            
            # Read metadata to get original path
            metadata_file = backup_path.parent / 'backup_metadata.json'
            
            if restore_to is None:
                if not metadata_file.exists():
                    self.logger.error("Metadata file missing, cannot determine restore location")
                    return False
                
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                restore_to = Path(metadata['original_path'])
            
            # Create backup of current file before restoring
            if restore_to.exists():
                current_backup = restore_to.parent / f"{restore_to.name}.pre-restore.bak"
                shutil.copy2(restore_to, current_backup)
                self.logger.info(f"Created pre-restore backup: {current_backup}")
            
            # Restore the file
            restore_to.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, restore_to)
            
            self.logger.info(f"Restored {restore_to} from backup")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring config: {e}")
            return False
    
    def list_backups(self, server_name: Optional[str] = None, 
                    plugin_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available backups
        
        Args:
            server_name: Optional filter by server
            plugin_name: Optional filter by plugin
            
        Returns:
            List of backup info dicts
        """
        backups = []
        
        try:
            search_path = self.backup_root
            
            if server_name:
                search_path = search_path / server_name
                if not search_path.exists():
                    return backups
            
            if plugin_name and server_name:
                search_path = search_path / plugin_name
                if not search_path.exists():
                    return backups
            
            # Find all metadata files
            for metadata_file in search_path.rglob('backup_metadata.json'):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    metadata['backup_path'] = str(metadata_file.parent)
                    backups.append(metadata)
                except Exception as e:
                    self.logger.warning(f"Error reading metadata {metadata_file}: {e}")
            
            # Sort by backup time (newest first)
            backups.sort(key=lambda x: x.get('backup_time', ''), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """
        Remove backups older than specified days
        
        Args:
            days_to_keep: Number of days to keep backups
            
        Returns:
            Number of backups removed
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            removed_count = 0
            
            for metadata_file in self.backup_root.rglob('backup_metadata.json'):
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    backup_time = datetime.fromisoformat(metadata['backup_time'])
                    
                    if backup_time < cutoff_date:
                        # Remove entire backup directory
                        backup_dir = metadata_file.parent
                        shutil.rmtree(backup_dir)
                        removed_count += 1
                        self.logger.info(f"Removed old backup: {backup_dir}")
                
                except Exception as e:
                    self.logger.warning(f"Error processing backup {metadata_file}: {e}")
            
            self.logger.info(f"Cleanup complete: removed {removed_count} old backups")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up backups: {e}")
            return 0
