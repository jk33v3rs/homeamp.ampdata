"""
Simple plugin config reader - reads YAML config files
"""

from pathlib import Path
from typing import Dict, Any
import yaml
import logging

logger = logging.getLogger(__name__)


class PluginConfigReader:
    """Reads plugin configuration files"""
    
    def __init__(self, plugins_dir: Path):
        """
        Args:
            plugins_dir: Path to plugins directory
        """
        self.plugins_dir = Path(plugins_dir)
    
    def read_all_configs(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Read all plugin configs
        
        Returns:
            {plugin_name: {config_file: {key: value}}}
        """
        configs = {}
        
        if not self.plugins_dir.exists():
            return configs
        
        # Scan for plugin folders
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            plugin_name = plugin_dir.name
            plugin_configs = {}
            
            # Read all YAML/YML files in plugin directory
            for config_file in plugin_dir.glob("*.yml"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        if data:
                            plugin_configs[config_file.name] = data
                except Exception as e:
                    logger.warning(f"Failed to read {config_file}: {e}")
            
            for config_file in plugin_dir.glob("*.yaml"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                        if data:
                            plugin_configs[config_file.name] = data
                except Exception as e:
                    logger.warning(f"Failed to read {config_file}: {e}")
            
            if plugin_configs:
                configs[plugin_name] = plugin_configs
        
        return configs
