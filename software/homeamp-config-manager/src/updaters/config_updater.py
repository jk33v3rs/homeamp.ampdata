"""
Config Updater Module

Applies bulk configuration updates to server configs with safety checks,
validation, backups, and rollback capabilities.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import logging


class ConfigUpdater:
    """Safely applies configuration changes to servers"""
    
    def __init__(self, utildata_path: Path, dry_run: bool = True):
        """
        Initialize config updater
        
        Args:
            utildata_path: Root path to utildata
            dry_run: If True, simulate changes without applying
        """
        self.utildata_path = utildata_path
        self.dry_run = dry_run
        self.backup_dir = None
        self.logger = logging.getLogger(__name__)
        
        # Initialize change manager - will be injected later if needed
        self.change_manager = None
    
    def load_change_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a change request from storage
        
        Args:
            request_id: Change request ID
            
        Returns:
            Change request data or None
        """
        if not self.change_manager:
            self.logger.error("Change manager not initialized")
            return None
            
        try:
            change_data = self.change_manager.download_change_request(request_id)
            if change_data:
                self.logger.info(f"Loaded change request {request_id}")
                return change_data
            else:
                self.logger.warning(f"Change request {request_id} not found")
                return None
        except Exception as e:
            self.logger.error(f"Failed to load change request {request_id}: {e}")
            return None
    
    def validate_change_request(self, change_request: Dict[str, Any]) -> bool:
        """
        Validate a change request before applying
        
        Args:
            change_request: Change request to validate
            
        Returns:
            True if valid
        """
        required_fields = ['changes', 'request_id', 'target_servers']
        
        # Check required fields
        for field in required_fields:
            if field not in change_request:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Validate changes structure
        changes = change_request.get('changes', [])
        if not isinstance(changes, list):
            self.logger.error("Changes must be a list")
            return False
        
        for i, change in enumerate(changes):
            if not isinstance(change, dict):
                self.logger.error(f"Change {i} must be a dictionary")
                return False
            
            required_change_fields = ['action', 'file_path']
            for field in required_change_fields:
                if field not in change:
                    self.logger.error(f"Change {i} missing required field: {field}")
                    return False
        
        self.logger.info(f"Change request {change_request.get('request_id')} validated successfully")
        return True
    
    def create_backup(self, target_files: List[str]) -> Optional[str]:
        """
        Create backup of files before changing
        
        Args:
            target_files: List of files to backup
            
        Returns:
            Backup directory path or None
        """
        try:
            # Create backup directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.utildata_path / "backups" / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            self.backup_dir = str(backup_dir)
            
            for file_path in target_files:
                source_path = Path(file_path)
                if source_path.exists():
                    # Preserve directory structure in backup
                    relative_path = source_path.relative_to(self.utildata_path)
                    backup_file_path = backup_dir / relative_path
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    import shutil
                    shutil.copy2(source_path, backup_file_path)
                    self.logger.debug(f"Backed up {source_path} to {backup_file_path}")
            
            self.logger.info(f"Created backup in {backup_dir}")
            return str(backup_dir)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def verify_expected_value(self, server_name: str, plugin_name: str, 
                             config_file: str, key_path: str, expected_value: Any) -> bool:
        """
        Verify current value matches expected before changing
        
        Args:
            server_name: Name of server
            plugin_name: Name of plugin
            config_file: Config file name
            key_path: Dot-notation path to key
            expected_value: Expected current value
            
        Returns:
            True if matches, False otherwise
        """
        try:
            from ..core.config_parser import ConfigParser
            from ..core.safety_validator import SafetyValidator
            
            # Build file path
            file_path = self.utildata_path / server_name / "plugins" / plugin_name / config_file
            
            # Validate file exists
            if not SafetyValidator.validate_config_file_exists(server_name, plugin_name, config_file, self.utildata_path):
                return False
            
            # Load current config
            current_config = ConfigParser.load_config(file_path)
            if current_config is None:
                print(f"Could not load config file: {file_path}")
                return False
            
            # Get current value
            current_value = ConfigParser.get_nested_value(current_config, key_path)
            
            # Validate expected value matches
            return SafetyValidator.validate_expected_value(current_value, expected_value, strict=False)
            
        except Exception as e:
            print(f"Error verifying expected value: {e}")
            return False
    
    def apply_single_change(self, change: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a single configuration change
        
        Args:
            change: Single change specification
            
        Returns:
            Change result with success status
        """
        action = change.get('action')
        file_path = change.get('file_path')
        
        if not action or not file_path:
            return {
                'success': False,
                'error': 'Missing action or file_path',
                'change': change
            }
        
        full_path = self.utildata_path / file_path
        
        try:
            if action == 'update_yaml_key':
                return self._update_yaml_key(full_path, change)
            elif action == 'replace_line':
                return self._replace_line(full_path, change)
            elif action == 'add_line':
                return self._add_line(full_path, change)
            elif action == 'delete_line':
                return self._delete_line(full_path, change)
            else:
                return {
                    'success': False,
                    'error': f'Unknown action: {action}',
                    'change': change
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'change': change
            }
    
    def _update_yaml_key(self, file_path: Path, change: Dict[str, Any]) -> Dict[str, Any]:
        """Update a YAML key with new value"""
        if self.dry_run:
            return {
                'success': True,
                'action': 'update_yaml_key',
                'file_path': str(file_path),
                'dry_run': True,
                'message': f"Would update YAML key in {file_path}"
            }
        
        import yaml
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            key_path = change.get('key_path', '').split('.')
            new_value = change.get('new_value')
            
            # Navigate to the key
            current = data
            for key in key_path[:-1]:
                current = current[key]
            
            # Update the value
            current[key_path[-1]] = new_value
            
            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, default_flow_style=False)
            
            return {
                'success': True,
                'action': 'update_yaml_key',
                'file_path': str(file_path),
                'key_path': change.get('key_path'),
                'new_value': new_value
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'update_yaml_key',
                'file_path': str(file_path),
                'error': str(e)
            }
    
    def _replace_line(self, file_path: Path, change: Dict[str, Any]) -> Dict[str, Any]:
        """Replace a line in a text file"""
        if self.dry_run:
            return {
                'success': True,
                'action': 'replace_line',
                'file_path': str(file_path),
                'dry_run': True,
                'message': f"Would replace line in {file_path}"
            }
        
        # Implementation for line replacement
        old_line = change.get('old_line')
        new_line = change.get('new_line')
        
        if not old_line or not new_line:
            return {
                'success': False,
                'error': 'Missing old_line or new_line',
                'action': 'replace_line'
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            replaced = False
            for i, line in enumerate(lines):
                if old_line.strip() in line.strip():
                    lines[i] = new_line + '\n'
                    replaced = True
                    break
            
            if replaced:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            
            return {
                'success': replaced,
                'action': 'replace_line',
                'file_path': str(file_path),
                'replaced': replaced
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'replace_line',
                'file_path': str(file_path),
                'error': str(e)
            }
    
    def _add_line(self, file_path: Path, change: Dict[str, Any]) -> Dict[str, Any]:
        """Add a line to a file"""
        if self.dry_run:
            return {
                'success': True,
                'action': 'add_line',
                'file_path': str(file_path),
                'dry_run': True
            }
        
        new_line = change.get('new_line')
        position = change.get('position', 'end')  # 'start', 'end', or line number
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            if position == 'start':
                lines.insert(0, new_line + '\n')
            elif position == 'end':
                lines.append(new_line + '\n')
            elif isinstance(position, int):
                lines.insert(position, new_line + '\n')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return {
                'success': True,
                'action': 'add_line',
                'file_path': str(file_path)
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'add_line',
                'file_path': str(file_path),
                'error': str(e)
            }
    
    def _delete_line(self, file_path: Path, change: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a line from a file"""
        if self.dry_run:
            return {
                'success': True,
                'action': 'delete_line',
                'file_path': str(file_path),
                'dry_run': True
            }
        
        target_line = change.get('target_line')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            new_lines = []
            deleted = False
            for line in lines:
                if target_line.strip() not in line.strip():
                    new_lines.append(line)
                else:
                    deleted = True
            
            if deleted:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
            
            return {
                'success': deleted,
                'action': 'delete_line',
                'file_path': str(file_path),
                'deleted': deleted
            }
        except Exception as e:
            return {
                'success': False,
                'action': 'delete_line',
                'file_path': str(file_path),
                'error': str(e)
            }
    
    def apply_change_request(self, change_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a complete change request
        
        Args:
            change_request: Change request to apply
            
        Returns:
            Application result with success status and details
        """
        request_id = change_request.get('request_id', 'unknown')
        
        if not self.validate_change_request(change_request):
            return {
                'success': False,
                'request_id': request_id,
                'error': 'Change request validation failed'
            }
        
        # Get target files for backup
        target_files = []
        for change in change_request.get('changes', []):
            file_path = change.get('file_path')
            if file_path:
                full_path = self.utildata_path / file_path
                target_files.append(str(full_path))
        
        # Create backup if not in dry run mode
        backup_path = None
        if not self.dry_run:
            backup_path = self.create_backup(target_files)
            if not backup_path:
                return {
                    'success': False,
                    'request_id': request_id,
                    'error': 'Failed to create backup'
                }
        
        # Apply changes
        results = []
        success_count = 0
        
        for change in change_request.get('changes', []):
            result = self.apply_single_change(change)
            results.append(result)
            if result.get('success'):
                success_count += 1
        
        overall_success = success_count == len(change_request.get('changes', []))
        
        return {
            'success': overall_success,
            'request_id': request_id,
            'backup_path': backup_path,
            'applied_changes': success_count,
            'total_changes': len(change_request.get('changes', [])),
            'results': results,
            'dry_run': self.dry_run
        }
    
    def rollback_change(self, change_id: str) -> Dict[str, Any]:
        """
        Rollback a previously applied change
        
        Args:
            change_id: ID of change to rollback
            
        Returns:
            Rollback result
        """
        if not self.backup_dir:
            return {
                'success': False,
                'error': 'No backup directory available for rollback'
            }
        
        backup_path = Path(self.backup_dir)
        if not backup_path.exists():
            return {
                'success': False,
                'error': f'Backup directory not found: {backup_path}'
            }
        
        try:
            import shutil
            restored_files = []
            
            # Restore all files from backup
            for backup_file in backup_path.rglob('*'):
                if backup_file.is_file():
                    # Calculate original path
                    relative_path = backup_file.relative_to(backup_path)
                    original_path = self.utildata_path / relative_path
                    
                    # Ensure directory exists
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Restore file
                    shutil.copy2(backup_file, original_path)
                    restored_files.append(str(original_path))
            
            return {
                'success': True,
                'change_id': change_id,
                'restored_files': restored_files,
                'backup_path': str(backup_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'change_id': change_id
            }
    
    def generate_preview(self, change_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate preview of changes without applying
        
        Args:
            change_request: Change request to preview
            
        Returns:
            Preview with affected files and changes
        """
        preview = {
            'request_id': change_request.get('request_id'),
            'total_changes': len(change_request.get('changes', [])),
            'affected_files': [],
            'change_details': []
        }
        
        for i, change in enumerate(change_request.get('changes', [])):
            file_path = change.get('file_path')
            action = change.get('action')
            
            if file_path:
                full_path = self.utildata_path / file_path
                
                change_detail = {
                    'index': i,
                    'action': action,
                    'file_path': str(full_path),
                    'file_exists': full_path.exists(),
                    'change': change
                }
                
                preview['change_details'].append(change_detail)
                
                if str(full_path) not in preview['affected_files']:
                    preview['affected_files'].append(str(full_path))
        
        return preview
    
    def log_change(self, change: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Log change to immutable audit trail
        
        Args:
            change: Change that was attempted
            result: Result of the change
        """
        import json
        from datetime import datetime
        import os
        
        try:
            # Create audit log directory
            audit_dir = self.utildata_path / ".audit_logs"
            audit_dir.mkdir(exist_ok=True)
            
            # Create log entry
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user': os.getenv('USER', os.getenv('USERNAME', 'unknown')),
                'change_request': change,
                'result': result,
                'success': result.get('success', False),
                'error': result.get('error', None),
                'affected_files': result.get('affected_files', []),
                'backup_path': result.get('backup_path', None)
            }
            
            # Generate log filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = audit_dir / f"config_change_{timestamp}_{os.getpid()}.log"
            
            # Write log entry
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, separators=(',', ': '))
            
            # Also append to daily summary log
            daily_log = audit_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.log"
            with open(daily_log, 'a', encoding='utf-8') as f:
                summary = {
                    'timestamp': log_entry['timestamp'],
                    'user': log_entry['user'],
                    'success': log_entry['success'],
                    'server': change.get('server_name', 'unknown'),
                    'plugin': change.get('plugin_name', 'unknown'),
                    'changes_count': len(change.get('changes', [])),
                    'error': log_entry['error']
                }
                f.write(json.dumps(summary) + '\n')
                
        except Exception as e:
            print(f"Error logging change: {e}")
            # Don't fail the operation if logging fails
