"""
Server-Aware Config Engine

Maps AMP instances to servers, reads server-specific variables from Excel,
applies universal configs, and populates template values.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
import re
import yaml

from .excel_reader import ExcelConfigReader


class ServerAwareConfigEngine:
    """Generate server-specific configurations from universal templates"""
    
    def __init__(self, excel_reader: ExcelConfigReader, universal_configs_dir: Path):
        """
        Initialize config engine
        
        Args:
            excel_reader: Excel reader for server variables
            universal_configs_dir: Directory containing universal config markdown files
        """
        self.excel_reader = excel_reader
        self.universal_configs_dir = Path(universal_configs_dir)
        self.logger = logging.getLogger(__name__)
        
        # Cache for parsed universal configs
        self._universal_configs = {}
    
    def detect_server_from_amp_instance(self, instance_id: str, 
                                       amp_client) -> Optional[str]:
        """
        Detect server name from AMP instance ID
        
        Args:
            instance_id: AMP instance ID (UUID)
            amp_client: AMPClient instance
            
        Returns:
            Server name (e.g., 'DEV01', 'PROD01') or None
        """
        try:
            # Get instance info from AMP
            instances = amp_client.get_instances()
            
            for instance in instances:
                if instance.get('InstanceID') == instance_id:
                    # Instance name should match server name (e.g., 'DEV01')
                    instance_name = instance.get('InstanceName', '').upper()
                    self.logger.info(f"Detected server {instance_name} from instance {instance_id}")
                    return instance_name
            
            self.logger.warning(f"Could not find instance {instance_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting server from instance: {e}")
            return None
    
    def load_universal_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Load universal config for a plugin from markdown file
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            Dict with universal config data, or None if not found
        """
        try:
            # Check cache first
            if plugin_name in self._universal_configs:
                return self._universal_configs[plugin_name]
            
            # Find markdown file
            config_file = self.universal_configs_dir / f"{plugin_name}_universal_config.md"
            
            if not config_file.exists():
                self.logger.warning(f"No universal config found for {plugin_name}")
                return None
            
            # Parse markdown file
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML code blocks
            yaml_blocks = re.findall(r'```(?:yaml|yml)\n(.*?)\n```', content, re.DOTALL)
            
            if not yaml_blocks:
                self.logger.warning(f"No YAML blocks found in {config_file}")
                return None
            
            # Parse first YAML block as universal config
            universal_config = yaml.safe_load(yaml_blocks[0])
            
            # Cache it
            self._universal_configs[plugin_name] = universal_config
            
            self.logger.info(f"Loaded universal config for {plugin_name}")
            return universal_config
            
        except Exception as e:
            self.logger.error(f"Error loading universal config for {plugin_name}: {e}")
            return None
    
    def apply_server_variables(self, config: Dict[str, Any], 
                               server_name: str) -> Dict[str, Any]:
        """
        Apply server-specific variables to config template
        
        Args:
            config: Config dict with template variables (e.g., {{max_players}})
            server_name: Server name
            
        Returns:
            Config with variables replaced
        """
        try:
            # Get server variables from Excel
            server_vars = self.excel_reader.get_server_variables(server_name)
            
            if not server_vars:
                self.logger.warning(f"No variables found for server {server_name}")
                return config
            
            # Convert config to JSON string, replace variables, parse back
            import json
            config_str = json.dumps(config)
            
            # Replace {{variable_name}} with actual values
            for var_name, var_value in server_vars.items():
                pattern = r'\{\{' + re.escape(var_name) + r'\}\}'
                config_str = re.sub(pattern, str(var_value), config_str)
            
            # Parse back to dict
            populated_config = json.loads(config_str)
            
            self.logger.info(f"Applied {len(server_vars)} variables for {server_name}")
            return populated_config
            
        except Exception as e:
            self.logger.error(f"Error applying server variables: {e}")
            return config
    
    def generate_server_config(self, plugin_name: str, server_name: str) -> Optional[Dict[str, Any]]:
        """
        Generate complete server-specific config for a plugin
        
        Args:
            plugin_name: Name of plugin
            server_name: Server name
            
        Returns:
            Server-specific config dict
        """
        try:
            # Load universal config
            universal_config = self.load_universal_config(plugin_name)
            
            if not universal_config:
                return None
            
            # Apply server variables
            server_config = self.apply_server_variables(universal_config, server_name)
            
            self.logger.info(f"Generated config for {plugin_name} on {server_name}")
            return server_config
            
        except Exception as e:
            self.logger.error(f"Error generating server config: {e}")
            return None
    
    def write_config_file(self, config: Dict[str, Any], output_path: Path, 
                         format: str = 'yaml') -> bool:
        """
        Write config dict to file
        
        Args:
            config: Config dict
            output_path: Path to write to
            format: File format ('yaml', 'json', 'properties')
            
        Returns:
            True if successful
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'yaml':
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
            
            elif format == 'json':
                import json
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
            
            elif format == 'properties':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for key, value in config.items():
                        f.write(f"{key}={value}\n")
            
            else:
                self.logger.error(f"Unsupported format: {format}")
                return False
            
            self.logger.info(f"Wrote config to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing config file: {e}")
            return False
    
    def deploy_config_to_server(self, plugin_name: str, server_name: str, 
                                amp_instance_id: str, amp_client,
                                config_filename: str = 'config.yml') -> bool:
        """
        Generate and deploy config to server via AMP
        
        Args:
            plugin_name: Plugin name
            server_name: Server name
            amp_instance_id: AMP instance ID
            amp_client: AMPClient instance
            config_filename: Name of config file
            
        Returns:
            True if successful
        """
        try:
            # Generate server-specific config
            config = self.generate_server_config(plugin_name, server_name)
            
            if not config:
                return False
            
            # Write to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                yaml.safe_dump(config, f, default_flow_style=False)
                temp_path = Path(f.name)
            
            # Upload to server via AMP file manager
            remote_path = f"/plugins/{plugin_name}/{config_filename}"
            
            # TODO: Implement AMP file upload when AMP client supports it
            # For now, return success if config was generated
            self.logger.info(f"Generated config for {plugin_name} (deployment pending AMP file upload)")
            
            # Clean up temp file
            temp_path.unlink()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deploying config: {e}")
            return False
