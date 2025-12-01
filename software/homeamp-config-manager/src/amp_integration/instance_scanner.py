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
        Discover all AMP instances (Paper, Fabric, NeoForge, Geyser, Velocity)
        
        Returns:
            List of instance dicts with comprehensive metadata
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
            
            # Check for Minecraft directory (Bukkit/Spigot/Paper/Purpur/Pufferfish)
            minecraft_dir = instance_dir / "Minecraft"
            if minecraft_dir.exists():
                instance = self._scan_minecraft_instance(instance_dir, minecraft_dir)
                if instance:
                    instances.append(instance)
                continue
            
            # Check for Geyser standalone (GenericApplication)
            geyser_dir = instance_dir / "GenericApplication"
            if geyser_dir.exists():
                instance = self._scan_geyser_instance(instance_dir, geyser_dir)
                if instance:
                    instances.append(instance)
                continue
        
        logger.info(f"Discovered {len(instances)} instances in {self.base_dir}")
        return instances
    
    def _scan_minecraft_instance(self, instance_dir: Path, minecraft_dir: Path) -> Dict[str, Any]:
        """Scan a Minecraft-based server instance"""
        # Detect platform type
        platform = 'paper'  # default
        mods_dir = minecraft_dir / "mods"
        plugins_dir = minecraft_dir / "plugins"
        
        if mods_dir.exists():
            # Fabric or NeoForge
            fabric_loader = minecraft_dir / "libraries" / "net" / "fabricmc"
            if fabric_loader.exists():
                platform = 'fabric'
            else:
                platform = 'neoforge'
        
        # Read server.properties for main world
        server_props = minecraft_dir / "server.properties"
        level_name = "world"  # default
        if server_props.exists():
            try:
                content = server_props.read_text()
                for line in content.splitlines():
                    if line.startswith("level-name="):
                        level_name = line.split("=", 1)[1].strip()
                        break
            except Exception as e:
                logger.warning(f"Failed to read server.properties: {e}")
        
        # Locate world folder and datapacks
        world_dir = minecraft_dir / level_name
        datapacks_dir = world_dir / "datapacks" if world_dir.exists() else None
        
        return {
            'name': instance_dir.name,
            'path': str(instance_dir),
            'minecraft_path': str(minecraft_dir),
            'plugins_path': str(plugins_dir) if plugins_dir.exists() else None,
            'mods_path': str(mods_dir) if mods_dir.exists() else None,
            'has_plugins': plugins_dir.exists(),
            'has_mods': mods_dir.exists(),
            'platform': platform,
            'server_properties': str(server_props) if server_props.exists() else None,
            'level_name': level_name,
            'world_path': str(world_dir) if world_dir.exists() else None,
            'datapacks_path': str(datapacks_dir) if datapacks_dir and datapacks_dir.exists() else None,
            'amp_config': str(instance_dir / "AMPConfig.conf") if (instance_dir / "AMPConfig.conf").exists() else None,
            'bukkit_yml': str(minecraft_dir / "bukkit.yml") if (minecraft_dir / "bukkit.yml").exists() else None,
            'spigot_yml': str(minecraft_dir / "spigot.yml") if (minecraft_dir / "spigot.yml").exists() else None,
            'paper_yml': str(minecraft_dir / "config" / "paper-global.yml") if (minecraft_dir / "config" / "paper-global.yml").exists() else None,
            'pufferfish_yml': str(minecraft_dir / "pufferfish.yml") if (minecraft_dir / "pufferfish.yml").exists() else None,
            'purpur_yml': str(minecraft_dir / "purpur.yml") if (minecraft_dir / "purpur.yml").exists() else None
        }
    
    def _scan_geyser_instance(self, instance_dir: Path, geyser_dir: Path) -> Dict[str, Any]:
        """Scan a Geyser standalone instance"""
        config_dir = geyser_dir / "config"
        return {
            'name': instance_dir.name,
            'path': str(instance_dir),
            'minecraft_path': str(geyser_dir),
            'plugins_path': str(config_dir) if config_dir.exists() else None,
            'has_plugins': config_dir.exists(),
            'platform': 'geyser',
            'amp_config': str(instance_dir / "AMPConfig.conf") if (instance_dir / "AMPConfig.conf").exists() else None
        }
