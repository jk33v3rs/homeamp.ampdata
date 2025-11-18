"""
AMP Instance.conf Parser

Parses AMP Instance.conf files to extract instance metadata.
These INI-format files contain critical instance information like UUID, friendly name, and ports.
"""

import configparser
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class InstanceConfParser:
    """Parse AMP Instance.conf files"""
    
    def __init__(self, conf_path: str):
        """
        Initialize parser
        
        Args:
            conf_path: Path to Instance.conf file
        """
        self.conf_path = Path(conf_path)
        self.config = configparser.ConfigParser()
        self.data: Dict = {}
        
        if not self.conf_path.exists():
            raise FileNotFoundError(f"Instance.conf not found: {self.conf_path}")
    
    def parse(self) -> Dict:
        """
        Parse the Instance.conf file
        
        Returns:
            Dictionary with instance metadata
            
        Example output:
        {
            'instance_id': '550e8400-e29b-41d4-a716-446655440000',
            'friendly_name': 'BENT01-ArchiveSMP',
            'port': 25565,
            'application': 'Minecraft',
            'module': 'MinecraftModule',
            'raw_sections': {...}  # All sections and keys
        }
        """
        try:
            self.config.read(self.conf_path)
            
            # Extract common fields
            self.data = {
                'instance_id': self.get_amp_uuid(),
                'friendly_name': self.get_friendly_name(),
                'port': self.get_port(),
                'application': self.get_application(),
                'module': self.get_module(),
                'raw_sections': self._get_all_sections()
            }
            
            return self.data
            
        except Exception as e:
            logger.error(f"Error parsing {self.conf_path}: {e}")
            raise
    
    def get_amp_uuid(self) -> Optional[str]:
        """
        Get AMP internal instance UUID
        
        This is usually in the [Meta] section as 'InstanceID'
        
        Returns:
            UUID string or None if not found
        """
        try:
            # Try different possible locations
            if self.config.has_option('Meta', 'InstanceID'):
                return self.config.get('Meta', 'InstanceID')
            
            if self.config.has_option('Instance', 'InstanceID'):
                return self.config.get('Instance', 'InstanceID')
            
            # Some versions use 'ID'
            if self.config.has_option('Meta', 'ID'):
                return self.config.get('Meta', 'ID')
            
            logger.warning(f"InstanceID not found in {self.conf_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting InstanceID: {e}")
            return None
    
    def get_friendly_name(self) -> Optional[str]:
        """
        Get instance friendly name
        
        Returns:
            Friendly name or None if not found
        """
        try:
            # Try different possible locations
            if self.config.has_option('Meta', 'FriendlyName'):
                return self.config.get('Meta', 'FriendlyName')
            
            if self.config.has_option('Instance', 'FriendlyName'):
                return self.config.get('Instance', 'FriendlyName')
            
            if self.config.has_option('Meta', 'InstanceName'):
                return self.config.get('Meta', 'InstanceName')
            
            logger.warning(f"FriendlyName not found in {self.conf_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting FriendlyName: {e}")
            return None
    
    def get_port(self) -> Optional[int]:
        """
        Get application port (e.g., Minecraft server port)
        
        Returns:
            Port number or None if not found
        """
        try:
            # Try different possible locations
            port_keys = [
                ('Server', 'ApplicationPort'),
                ('Minecraft', 'Server.Port'),
                ('MinecraftModule.Minecraft.Server', 'Port'),
                ('Settings', 'Port'),
                ('Meta', 'ApplicationPort')
            ]
            
            for section, key in port_keys:
                if self.config.has_section(section) and self.config.has_option(section, key):
                    port_str = self.config.get(section, key)
                    try:
                        return int(port_str)
                    except ValueError:
                        logger.warning(f"Invalid port value: {port_str}")
                        continue
            
            logger.warning(f"Port not found in {self.conf_path}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting port: {e}")
            return None
    
    def get_application(self) -> Optional[str]:
        """
        Get application type (e.g., 'Minecraft', 'Terraria')
        
        Returns:
            Application name or None if not found
        """
        try:
            if self.config.has_option('Meta', 'App'):
                return self.config.get('Meta', 'App')
            
            if self.config.has_option('Meta', 'Application'):
                return self.config.get('Meta', 'Application')
            
            # Default to Minecraft if not found
            return 'Minecraft'
            
        except Exception as e:
            logger.error(f"Error extracting application: {e}")
            return None
    
    def get_module(self) -> Optional[str]:
        """
        Get AMP module name (e.g., 'MinecraftModule')
        
        Returns:
            Module name or None if not found
        """
        try:
            if self.config.has_option('Meta', 'Module'):
                return self.config.get('Meta', 'Module')
            
            if self.config.has_option('Meta', 'ModuleName'):
                return self.config.get('Meta', 'ModuleName')
            
            # Default based on application
            app = self.get_application()
            if app == 'Minecraft':
                return 'MinecraftModule'
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting module: {e}")
            return None
    
    def get_value(self, section: str, key: str, default=None) -> Optional[str]:
        """
        Get a specific configuration value
        
        Args:
            section: Section name
            key: Key name
            default: Default value if not found
            
        Returns:
            Value or default
        """
        try:
            if self.config.has_option(section, key):
                return self.config.get(section, key)
            return default
        except Exception as e:
            logger.error(f"Error getting {section}.{key}: {e}")
            return default
    
    def _get_all_sections(self) -> Dict:
        """
        Get all sections and their key-value pairs
        
        Returns:
            Dictionary of all sections and values
        """
        sections = {}
        
        for section in self.config.sections():
            sections[section] = {}
            for key in self.config.options(section):
                sections[section][key] = self.config.get(section, key)
        
        return sections
    
    def to_dict(self) -> Dict:
        """
        Convert parsed data to dictionary
        
        Returns:
            Dictionary with all parsed data
        """
        if not self.data:
            self.parse()
        return self.data


def parse_instance_conf(conf_path: str) -> Dict:
    """
    Convenience function to parse Instance.conf
    
    Args:
        conf_path: Path to Instance.conf file
        
    Returns:
        Dictionary with instance metadata
        
    Example:
        data = parse_instance_conf('/home/amp/.ampdata/instances/BENT01/Instance.conf')
        print(f"UUID: {data['instance_id']}")
        print(f"Name: {data['friendly_name']}")
        print(f"Port: {data['port']}")
    """
    parser = InstanceConfParser(conf_path)
    return parser.parse()


def discover_instance_conf_files(amp_data_path: str = "/home/amp/.ampdata") -> Dict[str, str]:
    """
    Discover all Instance.conf files in AMP instances
    
    Args:
        amp_data_path: Path to AMP data directory
        
    Returns:
        Dictionary mapping instance folder names to Instance.conf paths
        
    Example:
        {
            'BENT01': '/home/amp/.ampdata/instances/BENT01/Instance.conf',
            'SMP101': '/home/amp/.ampdata/instances/SMP101/Instance.conf'
        }
    """
    instances_dir = Path(amp_data_path) / 'instances'
    
    if not instances_dir.exists():
        logger.error(f"Instances directory not found: {instances_dir}")
        return {}
    
    conf_files = {}
    
    for instance_dir in instances_dir.iterdir():
        if not instance_dir.is_dir():
            continue
        
        conf_path = instance_dir / 'Instance.conf'
        if conf_path.exists():
            conf_files[instance_dir.name] = str(conf_path)
        else:
            logger.warning(f"No Instance.conf found for {instance_dir.name}")
    
    logger.info(f"Discovered {len(conf_files)} Instance.conf files")
    return conf_files


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Discover all Instance.conf files
    conf_files = discover_instance_conf_files()
    
    # Parse each one
    for folder_name, conf_path in conf_files.items():
        print(f"\n{'='*60}")
        print(f"Instance Folder: {folder_name}")
        print(f"{'='*60}")
        
        try:
            data = parse_instance_conf(conf_path)
            
            print(f"AMP UUID:       {data['instance_id']}")
            print(f"Friendly Name:  {data['friendly_name']}")
            print(f"Port:           {data['port']}")
            print(f"Application:    {data['application']}")
            print(f"Module:         {data['module']}")
            print(f"\nAll Sections: {list(data['raw_sections'].keys())}")
            
        except Exception as e:
            print(f"ERROR: {e}")
