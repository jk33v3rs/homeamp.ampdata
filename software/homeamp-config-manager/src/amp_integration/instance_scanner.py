"""
Simple AMP instance scanner - discovers instances in /home/amp/.ampdata/instances/
"""

from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AMPInstanceScanner:
    """Scans for AMP instances on the local server"""
    
    def __init__(self, base_dir: Path):
        """
        Args:
            base_dir: Base directory for AMP instances (e.g., /home/amp/.ampdata/instances/)
        """
        self.base_dir = Path(base_dir)
    
    def discover_instances(self) -> List[Dict[str, Any]]:
        """
        Discover all AMP instances (Paper, Geyser, Velocity)
        
        Returns:
            List of instance dicts with keys: name, path, config_path
        """
        instances = []
        
        if not self.base_dir.exists():
            logger.warning(f"Base directory does not exist: {self.base_dir}")
            return instances
        
        for instance_dir in self.base_dir.iterdir():
            if not instance_dir.is_dir():
                continue
            
            # Skip ADS controller instances
            if (instance_dir / "ADSModule.kvp").exists():
                continue
            
            # Check for Minecraft directory (Paper servers)
            minecraft_dir = instance_dir / "Minecraft"
            if minecraft_dir.exists():
                plugins_dir = minecraft_dir / "plugins"
                instances.append({
                    'name': instance_dir.name,
                    'path': str(instance_dir),
                    'minecraft_path': str(minecraft_dir),
                    'plugins_path': str(plugins_dir) if plugins_dir.exists() else None,
                    'has_plugins': plugins_dir.exists(),
                    'platform': 'paper'
                })
                continue
            
            # Check for Geyser standalone (GenericApplication)
            geyser_dir = instance_dir / "GenericApplication"
            if geyser_dir.exists():
                config_dir = geyser_dir / "config"
                instances.append({
                    'name': instance_dir.name,
                    'path': str(instance_dir),
                    'minecraft_path': str(geyser_dir),
                    'plugins_path': str(config_dir) if config_dir.exists() else None,
                    'has_plugins': config_dir.exists(),
                    'platform': 'geyser'
                })
                continue
        
        logger.info(f"Discovered {len(instances)} instances in {self.base_dir}")
        return instances
