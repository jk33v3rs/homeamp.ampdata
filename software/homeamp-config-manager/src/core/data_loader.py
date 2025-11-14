"""
Data Loader Module

Loads actual production configuration data from utildata directories
"""
from .settings import get_settings

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from dataclasses import dataclass


@dataclass
class ServerInfo:
    """Server configuration information"""
    server_id: str
    friendly_name: str
    platform: str  # OVH or Hetzner
    role: str
    port: int
    utildata_path: Path
    amp_config_path: Optional[Path] = None


class ProductionDataLoader:
    """Loads actual production data from utildata and configuration snapshots"""
    
    def __init__(self, base_path: Path):
        """
        Initialize data loader with base repository path
        
        Args:
            base_path: Path to homeamp.ampdata repository root
        """
        self.base_path = base_path
        self.utildata_path = base_path / "utildata"
        self.scripts_path = base_path / "scripts"
        self.universal_configs_path = self.utildata_path / "plugin_universal_configs"
        
        # Load server configuration data
        self.server_configs = self._load_server_configurations()
        self.servers = self._discover_servers()
    
    def _load_server_configurations(self) -> Dict[str, Any]:
        """Load complete server configurations from scripts directory"""
        config_file = self.scripts_path / get_settings().get_file_path("server_config")
        
        if not config_file.exists():
            print(f"Warning: {config_file} not found")
            return {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading server configurations: {e}")
            return {}
    
    def _discover_servers(self) -> Dict[str, ServerInfo]:
        """Discover all servers from utildata directory structure"""
        servers = {}
        
        # Check both OVH and Hetzner directories
        for platform in ["OVH", "Hetzner"]:
            platform_path = self.utildata_path / platform
            if not platform_path.exists():
                continue
                
            for server_dir in platform_path.iterdir():
                if not server_dir.is_dir():
                    continue
                
                server_id = server_dir.name
                
                # Get server info from loaded configurations
                server_config = self.server_configs.get("archivesmp_server_configurations", {}).get("servers", {}).get(server_id, {})
                profile = server_config.get("server_profile", {})
                
                servers[server_id] = ServerInfo(
                    server_id=server_id,
                    friendly_name=profile.get("friendly_name", server_id),
                    platform=platform,
                    role=profile.get("role", "Unknown"),
                    port=profile.get("port", 0),
                    utildata_path=server_dir,
                    amp_config_path=self._find_amp_config_path(server_id, platform)
                )
        
        return servers
    
    def _find_amp_config_path(self, server_id: str, platform: str) -> Optional[Path]:
        """Find AMP configuration snapshot path for a server"""
        if platform == "OVH":
            amp_path = self.base_path / "OVH.37.187.143.41" / "amp_config_snapshot" / server_id
        else:  # Hetzner
            amp_path = self.base_path / "HETZNER.135.181.212.169" / "amp_config_snapshot" / server_id
        
        return amp_path if amp_path.exists() else None
    
    def get_all_servers(self) -> Dict[str, ServerInfo]:
        """Get all discovered servers"""
        return self.servers
    
    def get_server_by_id(self, server_id: str) -> Optional[ServerInfo]:
        """Get server information by ID"""
        return self.servers.get(server_id)
    
    def get_servers_by_platform(self, platform: str) -> List[ServerInfo]:
        """Get all servers on a specific platform"""
        return [server for server in self.servers.values() if server.platform == platform]
    
    def load_universal_plugin_configs(self) -> Dict[str, Dict[str, Any]]:
        """Load universal plugin configurations from platform-specific expectations (primary) or fallback sources"""
        universal_configs = {}
        
        # Primary: Load from platform-specific expectations (paper, velocity, geyser)
        expectations_dir = self.base_path / "software" / "homeamp-config-manager" / "data" / "expectations"
        
        if expectations_dir.exists():
            print(f"Loading universal configs from platform-specific expectations: {expectations_dir}")
            
            for platform in ["paper", "velocity", "geyser"]:
                platform_config = expectations_dir / platform / "universal_configs.json"
                if platform_config.exists():
                    try:
                        with open(platform_config, 'r', encoding='utf-8') as f:
                            platform_configs = json.load(f)
                            universal_configs.update(platform_configs)
                            print(f"  Loaded {len(platform_configs)} configs from {platform}")
                    except Exception as e:
                        print(f"  Error loading {platform} configs: {e}")
            
            if universal_configs:
                print(f"Total universal configs loaded: {len(universal_configs)}")
                return universal_configs
        
        # Fallback 1: Check for broken-down configs in baselines
        universal_configs_dir = self.base_path / "software" / "homeamp-config-manager" / "data" / "baselines" / "universal_configs"
        
        if universal_configs_dir.exists():
            print(f"Loading universal configs from baselines: {universal_configs_dir}")
            
            for config_file in universal_configs_dir.glob("*.md"):
                plugin_name = config_file.stem
                
                try:
                    configs = self._parse_individual_plugin_config(config_file)
                    if configs:
                        universal_configs[plugin_name] = configs
                except Exception as e:
                    print(f"Error parsing {config_file}: {e}")
            
            return universal_configs
        
        # Fallback 2: utildata directory structure if it exists
        utildata_universal_path = self.utildata_path / "plugin_universal_configs"
        if utildata_universal_path.exists():
            print(f"Loading universal configs from utildata: {utildata_universal_path}")
            
            for config_file in utildata_universal_path.glob("*_universal_config.md"):
                plugin_name = config_file.stem.replace("_universal_config", "")
                
                try:
                    configs = self._parse_universal_config_file(config_file)
                    if configs:
                        universal_configs[plugin_name] = configs
                except Exception as e:
                    print(f"Error parsing {config_file}: {e}")
        
        return universal_configs
    
    def _parse_universal_config_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a universal config markdown file"""
        configs = {}
        current_section = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and markdown headers
                    if not line or line.startswith('#') or line.startswith('These settings'):
                        continue
                    
                    # Check for section headers
                    if line.startswith('## '):
                        current_section = line[3:].strip()
                        continue
                    
                    # Parse config lines (format: `key` = value)
                    if line.startswith('`') and '=' in line:
                        try:
                            # Extract key and value
                            parts = line.split(' = ', 1)
                            if len(parts) != 2:
                                continue
                            
                            key = parts[0].strip('`')
                            value_str = parts[1].strip()
                            
                            # Parse value (handle different types)
                            value = self._parse_config_value(value_str)
                            
                            # Store with section prefix if available
                            if current_section:
                                full_key = f"{current_section}.{key}"
                            else:
                                full_key = key
                            
                            configs[full_key] = value
                            
                        except Exception as e:
                            print(f"Error parsing line '{line}': {e}")
                            continue
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return configs
    
    def _parse_config_value(self, value_str: str) -> Any:
        """Parse configuration value from string"""
        value_str = value_str.strip()
        
        # Handle different value types
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False
        elif value_str.lower() == 'null' or value_str == 'None':
            return None
        elif value_str.startswith('[') and value_str.endswith(']'):
            # Parse list
            try:
                return json.loads(value_str.replace("'", '"'))
            except:
                # Fallback to simple parsing
                content = value_str[1:-1].strip()
                if not content:
                    return []
                return [item.strip().strip("'\"") for item in content.split(',')]
        elif value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        elif value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]
        else:
            # Try to parse as number
            try:
                if '.' in value_str:
                    return float(value_str)
                else:
                    return int(value_str)
            except:
                return value_str
    
    def _parse_individual_plugin_config(self, file_path: Path) -> Dict[str, Any]:
        """Parse an individual plugin config markdown file (from broken-down structure)"""
        configs = {}
        current_section = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip headers and empty lines
                    if not line or line.startswith('#') or line.startswith('Universal baseline'):
                        continue
                    
                    # Check for section headers
                    if line.startswith('## '):
                        current_section = line[3:].strip()
                        continue
                    
                    # Check for file headers (### filename.yml)
                    if line.startswith('### '):
                        current_section = line[4:].strip()
                        continue
                    
                    # Parse config lines (format: - `key`: `value`)
                    if line.startswith('- `') and '`: `' in line:
                        try:
                            # Extract key and value
                            parts = line.split('`: `', 1)
                            if len(parts) != 2:
                                continue
                            
                            key = parts[0][3:]  # Remove '- `'
                            value_str = parts[1].rstrip('`')
                            
                            # Parse value (handle different types)
                            value = self._parse_config_value(value_str)
                            
                            # Store with section prefix if available
                            if current_section and current_section != "Configuration Settings":
                                full_key = f"{current_section}.{key}"
                            else:
                                full_key = key
                            
                            configs[full_key] = value
                            
                        except Exception as e:
                            print(f"Error parsing line '{line}': {e}")
                            continue
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return configs
    
    def load_plugin_deviations(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Load plugin deviations from individual plugin deviation files"""
        deviations = {}
        
        # Check for broken-down deviations first
        deviations_dir = self.base_path / "software" / "homeamp-config-manager" / "data" / "deviations"
        
        if deviations_dir.exists():
            print(f"Loading plugin deviations from: {deviations_dir}")
            
            for deviation_file in deviations_dir.glob("*.md"):
                # Skip summary files
                if deviation_file.name.startswith("_"):
                    continue
                    
                plugin_name = deviation_file.stem
                
                try:
                    plugin_deviations = self._parse_plugin_deviations(deviation_file)
                    if plugin_deviations:
                        deviations[plugin_name] = plugin_deviations
                except Exception as e:
                    print(f"Error parsing {deviation_file}: {e}")
        
        return deviations
    
    def _parse_plugin_deviations(self, file_path: Path) -> Dict[str, Dict[str, Any]]:
        """Parse an individual plugin deviation file"""
        deviations = {}
        current_file = None
        current_setting = None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip headers and empty lines
                    if not line or line.startswith('#') or line.startswith('Server-specific') or line.startswith('**'):
                        continue
                    
                    # Check for file headers (### filename.yml)
                    if line.startswith('### '):
                        current_file = line[4:].strip()
                        continue
                    
                    # Check for setting headers (**SettingName**)
                    if line.startswith('**') and line.endswith('**'):
                        current_setting = line[2:-2]
                        continue
                    
                    # Parse server deviation lines (- SERVER01: `value`)
                    if line.startswith('- ') and ':' in line and current_file and current_setting:
                        try:
                            parts = line[2:].split(':', 1)  # Remove '- ' and split on first ':'
                            if len(parts) != 2:
                                continue
                            
                            server_name = parts[0].strip()
                            value_str = parts[1].strip().strip('`')
                            
                            # Parse value
                            value = self._parse_config_value(value_str)
                            
                            # Store deviation
                            if current_file not in deviations:
                                deviations[current_file] = {}
                            if current_setting not in deviations[current_file]:
                                deviations[current_file][current_setting] = {}
                            
                            deviations[current_file][current_setting][server_name] = value
                            
                        except Exception as e:
                            print(f"Error parsing deviation line '{line}': {e}")
                            continue
        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return deviations
    
    def get_server_deviations(self, server_id: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get all deviations for a specific server across all plugins"""
        all_deviations = self.load_plugin_deviations()
        server_deviations = {}
        
        for plugin_name, plugin_deviations in all_deviations.items():
            plugin_server_deviations = {}
            
            for config_file, file_deviations in plugin_deviations.items():
                file_server_deviations = {}
                
                for setting_name, setting_deviations in file_deviations.items():
                    if server_id in setting_deviations:
                        file_server_deviations[setting_name] = setting_deviations[server_id]
                
                if file_server_deviations:
                    plugin_server_deviations[config_file] = file_server_deviations
            
            if plugin_server_deviations:
                server_deviations[plugin_name] = plugin_server_deviations
        
        return server_deviations
    
    def get_server_plugin_configs(self, server_id: str) -> Dict[str, Any]:
        """Get actual plugin configurations for a specific server"""
        server = self.get_server_by_id(server_id)
        if not server or not server.amp_config_path:
            return {}
        
        configs = {}
        plugins_path = server.amp_config_path / "Minecraft" / "plugins"
        
        if not plugins_path.exists():
            return {}
        
        # Look for common plugin config files
        for plugin_dir in plugins_path.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            plugin_name = plugin_dir.name
            plugin_configs = {}
            
            # Look for config files in plugin directory
            for config_file in plugin_dir.glob("*.yml"):
                try:
                    # For now, just record that the config exists
                    # Could extend to parse YAML content
                    plugin_configs[config_file.name] = str(config_file)
                except Exception as e:
                    print(f"Error processing {config_file}: {e}")
            
            if plugin_configs:
                configs[plugin_name] = plugin_configs
        
        return configs
    
    def get_server_status_summary(self) -> Dict[str, Any]:
        """Get summary status of all servers"""
        summary = {
            "total_servers": len(self.servers),
            "platforms": {
                "OVH": len(self.get_servers_by_platform("OVH")),
                "Hetzner": len(self.get_servers_by_platform("Hetzner"))
            },
            "servers": {}
        }
        
        for server_id, server in self.servers.items():
            summary["servers"][server_id] = {
                "friendly_name": server.friendly_name,
                "platform": server.platform,
                "role": server.role,
                "port": server.port,
                "utildata_exists": server.utildata_path.exists(),
                "amp_config_exists": server.amp_config_path.exists() if server.amp_config_path else False
            }
        
        return summary