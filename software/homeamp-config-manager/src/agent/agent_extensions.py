"""
Agent Extensions for Instance Path Tracking and Config File Discovery

These methods extend production_endpoint_agent.py with:
- Instance folder name and path tracking
- Instance.conf parsing for AMP UUID mapping
- Plugin config file discovery and tracking
- Config file hashing for change detection

INTEGRATION: Add these methods to ProductionEndpointAgent class
"""

from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import sys
sys.path.append(str(Path(__file__).parent.parent))
from parsers.instance_conf_parser import InstanceConfParser, parse_instance_conf


# ========================================================================
# INSTANCE FOLDER AND PATH TRACKING
# ========================================================================

def _discover_instance_folders(self) -> List[Dict]:
    """
    Discover all instance folders with full path tracking
    
    Returns:
        List of dicts with instance folder metadata:
        [
            {
                'folder_name': 'BENT01',
                'base_path': '/home/amp/.ampdata/instances/BENT01',
                'amp_uuid': '550e8400-e29b-41d4-a716-446655440000',
                'friendly_name': 'BENT01-ArchiveSMP',
                'port': 25565
            },
            ...
        ]
    """
    if not self.amp_base_dir.exists():
        self.logger.warning(f"[WARN]  AMP base dir not found: {self.amp_base_dir}")
        return []
    
    discovered = []
    
    for instance_dir in self.amp_base_dir.iterdir():
        if not instance_dir.is_dir():
            continue
        
        # Check if valid Minecraft instance
        minecraft_dir = instance_dir / 'Minecraft'
        if not minecraft_dir.exists():
            continue
        
        # Parse Instance.conf for AMP metadata
        conf_data = self._parse_instance_conf_for_folder(instance_dir.name)
        
        folder_info = {
            'folder_name': instance_dir.name,
            'base_path': str(instance_dir.absolute()),
            'amp_uuid': conf_data.get('instance_id') if conf_data else None,
            'friendly_name': conf_data.get('friendly_name') if conf_data else instance_dir.name,
            'port': conf_data.get('port') if conf_data else None,
            'platform': self._detect_platform(instance_dir),
            'minecraft_version': self._detect_minecraft_version(instance_dir)
        }
        
        discovered.append(folder_info)
        self.logger.info(f"[DIR] Discovered folder: {folder_info['folder_name']} (UUID: {folder_info['amp_uuid']})")
    
    return discovered


def _parse_instance_conf_for_folder(self, folder_name: str) -> Optional[Dict]:
    """
    Parse Instance.conf file for a specific instance folder
    
    Args:
        folder_name: Name of instance folder (e.g., 'BENT01')
        
    Returns:
        Dictionary with parsed Instance.conf data or None if not found
    """
    conf_path = self.amp_base_dir / folder_name / 'Instance.conf'
    
    if not conf_path.exists():
        self.logger.warning(f"[WARN]  Instance.conf not found for {folder_name}")
        return None
    
    try:
        conf_data = parse_instance_conf(str(conf_path))
        return conf_data
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to parse Instance.conf for {folder_name}: {e}")
        return None


def _map_folder_to_instance_id(self, folder_name: str, amp_uuid: Optional[str]) -> Optional[int]:
    """
    Map instance folder to database instance_id
    
    Args:
        folder_name: Folder name (e.g., 'BENT01')
        amp_uuid: AMP UUID from Instance.conf
        
    Returns:
        Database instance_id or None if not found
    """
    # Try to find by amp_instance_id first (if we have UUID)
    if amp_uuid:
        result = self.db.execute_query(
            "SELECT instance_id FROM instances WHERE amp_instance_id = %s",
            (amp_uuid,)
        )
        if result:
            return result[0]['instance_id']
    
    # Fall back to matching by instance_name
    result = self.db.execute_query(
        "SELECT instance_id FROM instances WHERE instance_name = %s",
        (folder_name,)
    )
    if result:
        return result[0]['instance_id']
    
    self.logger.warning(f"[WARN]  No database match for folder {folder_name} (UUID: {amp_uuid})")
    return None


def _update_instance_paths(self, instance_id: int, folder_name: str, base_path: str, amp_uuid: Optional[str] = None):
    """
    Update instance table with folder name and base path
    
    Args:
        instance_id: Database instance ID
        folder_name: Instance folder name
        base_path: Full path to instance folder
        amp_uuid: AMP UUID (optional, for updating amp_instance_id)
    """
    update_fields = {
        'instance_folder_name': folder_name,
        'instance_base_path': base_path
    }
    
    if amp_uuid:
        update_fields['amp_instance_id'] = amp_uuid
    
    # Build UPDATE query
    set_clause = ', '.join([f"{k} = %s" for k in update_fields.keys()])
    values = list(update_fields.values()) + [instance_id]
    
    query = f"UPDATE instances SET {set_clause} WHERE instance_id = %s"
    
    try:
        self.db.execute(query, values)
        self.logger.info(f"[OK] Updated paths for instance {instance_id}: {folder_name} -> {base_path}")
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to update instance paths: {e}")


# ========================================================================
# CONFIG FILE DISCOVERY AND TRACKING
# ========================================================================

def _discover_plugin_config_files(self, instance_id: int, instance_path: Path, plugin_id: str) -> List[Dict]:
    """
    Discover all config files for a specific plugin
    
    Args:
        instance_id: Database instance ID
        instance_path: Path to instance folder
        plugin_id: Plugin identifier
        
    Returns:
        List of config file metadata dicts
    """
    # Plugin config folder: Minecraft/plugins/{PluginName}/
    plugins_dir = instance_path / 'Minecraft' / 'plugins'
    
    # Try to find plugin folder (case-insensitive search)
    plugin_folder = None
    for folder in plugins_dir.iterdir():
        if folder.is_dir() and folder.name.lower() == plugin_id.lower():
            plugin_folder = folder
            break
    
    if not plugin_folder:
        # No config folder (plugin might not create one)
        return []
    
    discovered = []
    
    # Scan for all config files (YAML, JSON, TOML, .properties)
    for config_file in plugin_folder.rglob('*'):
        if not config_file.is_file():
            continue
        
        file_type = self._detect_config_file_type(config_file)
        if not file_type:
            continue
        
        # Calculate hash
        file_hash = self._calculate_config_file_hash(config_file)
        
        config_info = {
            'instance_id': instance_id,
            'plugin_id': plugin_id,
            'file_path': str(config_file.relative_to(instance_path)),
            'absolute_path': str(config_file.absolute()),
            'file_type': file_type,
            'file_hash': file_hash,
            'file_size': config_file.stat().st_size
        }
        
        discovered.append(config_info)
    
    return discovered


def _register_config_file(self, config_info: Dict):
    """
    Register config file in endpoint_config_files table
    
    Args:
        config_info: Config file metadata dict
    """
    query = """
        INSERT INTO endpoint_config_files 
        (instance_id, plugin_id, file_path, file_type, current_hash, file_size, last_discovered)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
            file_type = VALUES(file_type),
            current_hash = VALUES(current_hash),
            file_size = VALUES(file_size),
            last_discovered = NOW()
    """
    
    try:
        self.db.execute(query, (
            config_info['instance_id'],
            config_info['plugin_id'],
            config_info['file_path'],
            config_info['file_type'],
            config_info['file_hash'],
            config_info['file_size']
        ))
        self.logger.debug(f" Registered config: {config_info['file_path']}")
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to register config file: {e}")


def _detect_config_file_type(self, file_path: Path) -> Optional[str]:
    """
    Detect config file type by extension
    
    Args:
        file_path: Path to config file
        
    Returns:
        File type string ('yaml', 'json', 'toml', 'properties', 'conf') or None
    """
    extension = file_path.suffix.lower()
    
    if extension in ['.yml', '.yaml']:
        return 'yaml'
    elif extension == '.json':
        return 'json'
    elif extension == '.toml':
        return 'toml'
    elif extension == '.properties':
        return 'properties'
    elif extension in ['.conf', '.cfg', '.config']:
        return 'conf'
    elif extension == '.txt' and 'config' in file_path.name.lower():
        return 'text'
    else:
        return None


def _calculate_config_file_hash(self, file_path: Path) -> str:
    """
    Calculate SHA-256 hash of config file
    
    Args:
        file_path: Path to config file
        
    Returns:
        SHA-256 hash string
    """
    sha256 = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks for large files
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    except Exception as e:
        self.logger.error(f"[ERROR] Failed to hash {file_path}: {e}")
        return ''


def _scan_all_plugin_configs(self):
    """
    Full scan of all plugin config files across all instances
    
    This should be called during full discovery to populate endpoint_config_files table
    """
    instances = self._discover_instance_folders()
    
    total_configs = 0
    
    for instance_info in instances:
        folder_name = instance_info['folder_name']
        base_path = Path(instance_info['base_path'])
        
        # Map to database instance_id
        instance_id = self._map_folder_to_instance_id(folder_name, instance_info['amp_uuid'])
        if not instance_id:
            continue
        
        # Update instance paths
        self._update_instance_paths(
            instance_id,
            folder_name,
            instance_info['base_path'],
            instance_info['amp_uuid']
        )
        
        # Get all plugins for this instance
        plugins = self.db.execute_query(
            """
            SELECT DISTINCT p.plugin_id 
            FROM plugins p
            JOIN instance_plugins ip ON p.plugin_id = ip.plugin_id
            WHERE ip.instance_id = %s
            """,
            (instance_id,)
        )
        
        if not plugins:
            continue
        
        # Discover configs for each plugin
        for plugin_row in plugins:
            plugin_id = plugin_row['plugin_id']
            config_files = self._discover_plugin_config_files(instance_id, base_path, plugin_id)
            
            for config_info in config_files:
                self._register_config_file(config_info)
                total_configs += 1
    
    self.logger.info(f"[OK] Discovered {total_configs} config files across all instances")


# ========================================================================
# INTEGRATION NOTES
# ========================================================================
"""
TO INTEGRATE THESE METHODS INTO production_endpoint_agent.py:

1. Add these methods to the ProductionEndpointAgent class

2. Call _discover_instance_folders() in _run_full_discovery():
   Replace _discover_instances() with _discover_instance_folders()

3. Call _scan_all_plugin_configs() in _run_full_discovery():
   Add after plugin discovery loop

4. Update _discover_instance_plugins() to register configs:
   After registering plugin installation, call:
   config_files = self._discover_plugin_config_files(instance_id, instance_path, plugin_id)
   for config in config_files:
       self._register_config_file(config)
"""
