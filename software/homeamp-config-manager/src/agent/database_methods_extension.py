"""
Database Methods Extension for Config File Tracking

Additional database interaction methods for endpoint config file management.
These extend agent_database_methods.py with config tracking, backup, and change history.

INTEGRATION: Add these methods to AgentDatabaseMethods class
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import hashlib


# ========================================================================
# CONFIG FILE REGISTRATION AND TRACKING
# ========================================================================

def _register_endpoint_config_file(self, config_file_id: int = None, instance_id: int = None, 
                                   plugin_id: str = None, file_path: str = None,
                                   file_type: str = None, current_hash: str = None,
                                   file_size: int = None) -> Optional[int]:
    """
    Register or update config file in endpoint_config_files table
    
    Args:
        config_file_id: Existing file ID (for updates) or None (for inserts)
        instance_id: Database instance ID
        plugin_id: Plugin identifier
        file_path: Relative path from instance root (e.g., 'Minecraft/plugins/PluginName/config.yml')
        file_type: File type ('yaml', 'json', 'toml', 'properties', 'conf')
        current_hash: SHA-256 hash of current file content
        file_size: File size in bytes
        
    Returns:
        config_file_id (int) or None if failed
    """
    try:
        if config_file_id:
            # Update existing record
            self.db.execute_query("""
                UPDATE endpoint_config_files
                SET current_hash = %(current_hash)s,
                    file_size = %(file_size)s,
                    last_discovered = NOW()
                WHERE config_file_id = %(config_file_id)s
            """, {
                'config_file_id': config_file_id,
                'current_hash': current_hash,
                'file_size': file_size
            })
            return config_file_id
        else:
            # Insert new record
            result = self.db.execute_query("""
                INSERT INTO endpoint_config_files (
                    instance_id, plugin_id, file_path, file_type, 
                    current_hash, file_size, first_discovered, last_discovered
                ) VALUES (
                    %(instance_id)s, %(plugin_id)s, %(file_path)s, %(file_type)s,
                    %(current_hash)s, %(file_size)s, NOW(), NOW()
                )
                ON DUPLICATE KEY UPDATE
                    current_hash = VALUES(current_hash),
                    file_size = VALUES(file_size),
                    last_discovered = NOW()
            """, {
                'instance_id': instance_id,
                'plugin_id': plugin_id,
                'file_path': file_path,
                'file_type': file_type,
                'current_hash': current_hash,
                'file_size': file_size
            })
            
            # Get the inserted ID
            if result:
                last_id = self.db.execute_query("SELECT LAST_INSERT_ID() as id", fetch=True)
                if last_id:
                    return last_id[0]['id']
            
            return None
            
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to register config file {file_path}: {e}")
        return None


# ========================================================================
# CONFIG BACKUP OPERATIONS
# ========================================================================

def _create_config_backup(self, config_file_id: int, instance_id: int, 
                         file_path: str, reason: str = 'manual') -> Optional[int]:
    """
    Create backup of config file in database
    
    Args:
        config_file_id: Config file ID from endpoint_config_files
        instance_id: Instance ID
        file_path: Absolute path to config file
        reason: Backup reason ('before_modification', 'manual', 'scheduled', 'pre_deployment')
        
    Returns:
        backup_id (int) or None if failed
    """
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Calculate hash
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Insert backup
        result = self.db.execute_query("""
            INSERT INTO endpoint_config_backups (
                config_file_id, instance_id, backup_content, 
                content_hash, backup_reason, created_at
            ) VALUES (
                %(config_file_id)s, %(instance_id)s, %(content)s,
                %(content_hash)s, %(reason)s, NOW()
            )
        """, {
            'config_file_id': config_file_id,
            'instance_id': instance_id,
            'content': content,
            'content_hash': content_hash,
            'reason': reason
        })
        
        # Get backup ID
        if result:
            last_id = self.db.execute_query("SELECT LAST_INSERT_ID() as id", fetch=True)
            if last_id:
                backup_id = last_id[0]['id']
                self.logger.info(f"[OK] Created backup {backup_id} for config {config_file_id}")
                return backup_id
        
        return None
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to create backup for {file_path}: {e}")
        return None


def _restore_config_from_backup(self, backup_id: int, restore_to_path: str) -> bool:
    """
    Restore config file from backup
    
    Args:
        backup_id: Backup ID from endpoint_config_backups
        restore_to_path: Absolute path where to restore the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Retrieve backup content
        result = self.db.execute_query("""
            SELECT backup_content, content_hash
            FROM endpoint_config_backups
            WHERE backup_id = %(backup_id)s
        """, {'backup_id': backup_id}, fetch=True)
        
        if not result:
            self.logger.error(f"[ERROR] Backup {backup_id} not found")
            return False
        
        content = result[0]['backup_content']
        expected_hash = result[0]['content_hash']
        
        # Write to file
        with open(restore_to_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Verify hash
        with open(restore_to_path, 'r', encoding='utf-8') as f:
            restored_content = f.read()
        
        actual_hash = hashlib.sha256(restored_content.encode('utf-8')).hexdigest()
        
        if actual_hash != expected_hash:
            self.logger.error(f"[ERROR] Hash mismatch after restore! Expected: {expected_hash}, Got: {actual_hash}")
            return False
        
        self.logger.info(f"[OK] Restored backup {backup_id} to {restore_to_path}")
        return True
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to restore backup {backup_id}: {e}")
        return False


# ========================================================================
# CONFIG CHANGE TRACKING
# ========================================================================

def _log_config_change(self, config_file_id: int, instance_id: int, 
                      change_type: str, changed_by: str = 'system',
                      change_details: Dict = None, backup_id: int = None) -> bool:
    """
    Log config file change in history
    
    Args:
        config_file_id: Config file ID
        instance_id: Instance ID
        change_type: Type of change ('created', 'modified', 'deleted', 'restored')
        changed_by: Who made the change ('system', 'agent', 'api', 'user:username')
        change_details: JSON dict with change details (keys modified, etc.)
        backup_id: Associated backup ID (if backup was created)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        self.db.execute_query("""
            INSERT INTO endpoint_config_change_history (
                config_file_id, instance_id, change_type, changed_by,
                change_details, backup_id, changed_at
            ) VALUES (
                %(config_file_id)s, %(instance_id)s, %(change_type)s, %(changed_by)s,
                %(change_details)s, %(backup_id)s, NOW()
            )
        """, {
            'config_file_id': config_file_id,
            'instance_id': instance_id,
            'change_type': change_type,
            'changed_by': changed_by,
            'change_details': json.dumps(change_details) if change_details else None,
            'backup_id': backup_id
        })
        
        self.logger.debug(f" Logged {change_type} for config {config_file_id}")
        return True
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to log config change: {e}")
        return False


# ========================================================================
# CONFIG FILE QUERIES
# ========================================================================

def _get_config_file_info(self, config_file_id: int) -> Optional[Dict]:
    """
    Get config file metadata
    
    Args:
        config_file_id: Config file ID
        
    Returns:
        Dict with config file info or None
    """
    try:
        result = self.db.execute_query("""
            SELECT 
                cf.config_file_id,
                cf.instance_id,
                cf.plugin_id,
                cf.file_path,
                cf.file_type,
                cf.current_hash,
                cf.file_size,
                cf.first_discovered,
                cf.last_discovered,
                i.instance_name,
                i.instance_folder_name,
                i.instance_base_path,
                p.plugin_name,
                p.display_name as plugin_display_name
            FROM endpoint_config_files cf
            JOIN instances i ON cf.instance_id = i.instance_id
            JOIN plugins p ON cf.plugin_id = p.plugin_id
            WHERE cf.config_file_id = %(config_file_id)s
        """, {'config_file_id': config_file_id}, fetch=True)
        
        if result:
            return dict(result[0])
        return None
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to get config file info: {e}")
        return None


def _get_config_files_by_instance(self, instance_id: int) -> List[Dict]:
    """
    Get all config files for an instance
    
    Args:
        instance_id: Instance ID
        
    Returns:
        List of config file dicts
    """
    try:
        result = self.db.execute_query("""
            SELECT 
                cf.*,
                p.plugin_name,
                p.display_name as plugin_display_name
            FROM endpoint_config_files cf
            JOIN plugins p ON cf.plugin_id = p.plugin_id
            WHERE cf.instance_id = %(instance_id)s
            ORDER BY p.plugin_name, cf.file_path
        """, {'instance_id': instance_id}, fetch=True)
        
        return [dict(row) for row in result] if result else []
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to get config files for instance {instance_id}: {e}")
        return []


def _get_config_files_by_plugin(self, instance_id: int, plugin_id: str) -> List[Dict]:
    """
    Get all config files for a specific plugin on an instance
    
    Args:
        instance_id: Instance ID
        plugin_id: Plugin ID
        
    Returns:
        List of config file dicts
    """
    try:
        result = self.db.execute_query("""
            SELECT * FROM endpoint_config_files
            WHERE instance_id = %(instance_id)s
              AND plugin_id = %(plugin_id)s
            ORDER BY file_path
        """, {
            'instance_id': instance_id,
            'plugin_id': plugin_id
        }, fetch=True)
        
        return [dict(row) for row in result] if result else []
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to get config files for {plugin_id}: {e}")
        return []


def _mark_config_outdated(self, config_file_id: int, old_hash: str, new_hash: str) -> bool:
    """
    Mark config file as changed (hash mismatch)
    
    Args:
        config_file_id: Config file ID
        old_hash: Previous hash
        new_hash: New hash
        
    Returns:
        True if successful
    """
    try:
        # Update hash
        self.db.execute_query("""
            UPDATE endpoint_config_files
            SET current_hash = %(new_hash)s,
                last_discovered = NOW()
            WHERE config_file_id = %(config_file_id)s
        """, {
            'config_file_id': config_file_id,
            'new_hash': new_hash
        })
        
        # Log change
        self._log_config_change(
            config_file_id=config_file_id,
            instance_id=None,  # Will need to look this up if needed
            change_type='modified',
            changed_by='external',
            change_details={'old_hash': old_hash, 'new_hash': new_hash}
        )
        
        self.logger.info(f"[WARN]  Config {config_file_id} changed (hash mismatch)")
        return True
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to mark config as outdated: {e}")
        return False


# ========================================================================
# BACKUP MANAGEMENT
# ========================================================================

def _get_latest_backup(self, config_file_id: int) -> Optional[Dict]:
    """
    Get most recent backup for a config file
    
    Args:
        config_file_id: Config file ID
        
    Returns:
        Dict with backup info or None
    """
    try:
        result = self.db.execute_query("""
            SELECT * FROM endpoint_config_backups
            WHERE config_file_id = %(config_file_id)s
            ORDER BY created_at DESC
            LIMIT 1
        """, {'config_file_id': config_file_id}, fetch=True)
        
        if result:
            return dict(result[0])
        return None
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to get latest backup: {e}")
        return None


def _list_backups(self, config_file_id: int, limit: int = 10) -> List[Dict]:
    """
    List backups for a config file
    
    Args:
        config_file_id: Config file ID
        limit: Maximum number of backups to return
        
    Returns:
        List of backup dicts
    """
    try:
        result = self.db.execute_query("""
            SELECT 
                backup_id,
                config_file_id,
                instance_id,
                content_hash,
                backup_reason,
                created_at
            FROM endpoint_config_backups
            WHERE config_file_id = %(config_file_id)s
            ORDER BY created_at DESC
            LIMIT %(limit)s
        """, {
            'config_file_id': config_file_id,
            'limit': limit
        }, fetch=True)
        
        return [dict(row) for row in result] if result else []
        
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to list backups: {e}")
        return []


# ========================================================================
# INTEGRATION NOTES
# ========================================================================
"""
TO INTEGRATE THESE METHODS INTO agent_database_methods.py:

1. Import json at top of file (if not already imported)

2. Add these methods to the AgentDatabaseMethods class

3. Call from agent as needed:
   - _register_endpoint_config_file() during config discovery
   - _create_config_backup() before any config modification
   - _log_config_change() after any config change
   - _restore_config_from_backup() when rollback needed
   - _mark_config_outdated() when hash mismatch detected

4. Usage example in agent:
   # Discover config files
   config_files = self._discover_plugin_config_files(instance_id, instance_path, plugin_id)
   for config in config_files:
       config_file_id = self._register_endpoint_config_file(
           instance_id=config['instance_id'],
           plugin_id=config['plugin_id'],
           file_path=config['file_path'],
           file_type=config['file_type'],
           current_hash=config['file_hash'],
           file_size=config['file_size']
       )
"""
