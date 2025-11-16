"""
Data Models for Web UI

Parses and serves universal configs and deviations data from actual production systems
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field
from enum import Enum
import json

from ..core.data_loader import ProductionDataLoader, ServerInfo
from ..core.settings import get_settings


class DeviationStatus(str, Enum):
    """Status of a deviation"""
    PENDING_REVIEW = "pending_review"
    APPROVED_GOOD = "approved_good"
    FLAGGED_BAD = "flagged_bad"
    FIXED = "fixed"


class DeviationItem(BaseModel):
    """Single configuration deviation"""
    plugin: str
    config_file: str
    key_path: str
    server: str
    value: Any
    universal_value: Optional[Any] = None
    status: DeviationStatus = DeviationStatus.PENDING_REVIEW
    replacement_value: Optional[Any] = None
    notes: str = ""
    flagged_by: Optional[str] = None
    flagged_at: Optional[str] = None


class PluginConfig(BaseModel):
    """Universal plugin configuration"""
    plugin: str
    config_file: str
    configs: Dict[str, Any]


class ServerView(BaseModel):
    """Per-server view data"""
    server_name: str
    total_deviations: int
    pending_review: int
    flagged_bad: int
    approved_good: int
    out_of_date_plugins: List[str]
    last_drift_check: Optional[str] = None
    agent_status: str = "unknown"


class GlobalView(BaseModel):
    """Global network view"""
    total_servers: int
    active_agents: int
    total_deviations: int
    critical_issues: int
    pending_changes: int
    servers: List[ServerView]


class DeviationParser:
    """Parses deviation and universal config files from production data"""
    
    def __init__(self, deviations_file: Path, universal_file: Path, base_repo_path: Optional[Path] = None):
        """
        Initialize parser
        
        Args:
            deviations_file: Path to plugin_configs_deviations.md
            universal_file: Path to plugin_configs_universal.md
            base_repo_path: Path to homeamp.ampdata repository root
        """
        self.deviations_file = deviations_file
        self.universal_file = universal_file
        self.deviations: List[DeviationItem] = []
        self.universal_configs: Dict[str, PluginConfig] = {}
        
        # Initialize production data loader if base path provided
        if base_repo_path:
            self.data_loader = ProductionDataLoader(base_repo_path)
        else:
            self.data_loader = None
    
    def load_universal_configs(self) -> Dict[str, PluginConfig]:
        """
        Parse universal configurations - from production data if available, fallback to file
        
        Returns:
            Dict mapping plugin name to PluginConfig
        """
        configs = {}
        
        # Try to load from production data loader first
        if self.data_loader:
            try:
                production_configs = self.data_loader.load_universal_plugin_configs()
                for plugin_name, plugin_configs in production_configs.items():
                    configs[plugin_name] = PluginConfig(
                        plugin=plugin_name,
                        config_file="production_configs",
                        configs=plugin_configs
                    )
                
                if configs:
                    print(f"Loaded {len(configs)} plugins from production universal configs")
                    self.universal_configs = configs
                    return configs
            except Exception as e:
                print(f"Error loading production configs, fallback to file parsing: {e}")
        
        # Fallback to original file parsing
        if not self.universal_file.exists():
            return {}
        
        current_plugin = None
        current_file = None
        current_content = []
        
        try:
            with open(self.universal_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.rstrip()
                    
                    # Plugin header: ## PluginName
                    if line.startswith('## '):
                        # Save previous plugin
                        if current_plugin and current_file:
                            self._save_universal_config(configs, current_plugin, current_file, current_content)
                        
                        current_plugin = line[3:].strip()
                        current_file = None
                        current_content = []
                    
                    # File header: ### filename.yml
                    elif line.startswith('### '):
                        # Save previous file
                        if current_plugin and current_file:
                            self._save_universal_config(configs, current_plugin, current_file, current_content)
                        
                        current_file = line[4:].strip()
                        current_content = []
                    
                    # Content line
                    elif current_plugin and current_file and line.strip():
                        # Skip markdown code blocks
                        if not line.startswith('```'):
                            current_content.append(line)
                
                # Save final plugin/file
                if current_plugin and current_file:
                    self._save_universal_config(configs, current_plugin, current_file, current_content)
        
        except Exception as e:
            print(f"Error parsing universal configs: {e}")
        
        self.universal_configs = configs
        return configs
    
    def _save_universal_config(self, configs: Dict[str, PluginConfig], plugin: str, config_file: str, content: List[str]):
        """Helper to save universal config data"""
        try:
            import yaml
            
            # Join content and parse as YAML
            yaml_content = '\n'.join(content)
            if yaml_content.strip():
                parsed_config = yaml.safe_load(yaml_content)
                
                if plugin not in configs:
                    configs[plugin] = PluginConfig(
                        plugin=plugin,
                        config_file=config_file,
                        configs={}
                    )
                
                configs[plugin].configs[config_file] = parsed_config
        except Exception as e:
            print(f"Error parsing config for {plugin}/{config_file}: {e}")
    
    def load_deviations(self) -> List[DeviationItem]:
        """
        Parse deviations file
        
        Returns:
            List of DeviationItem objects
        """
        if not self.deviations_file.exists():
            return []
        
        deviations = []
        current_plugin = None
        current_file = None
        
        try:
            with open(self.deviations_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Plugin header: ## PluginName
                    if line.startswith('## '):
                        current_plugin = line[3:].strip()
                        current_file = None
                    
                    # File header: ### filename.yml
                    elif line.startswith('### '):
                        current_file = line[4:].strip()
                    
                    # Deviation line: #### key.path
                    elif line.startswith('#### ') and current_plugin and current_file:
                        key_path = line[5:].strip()
                        # Next lines should contain server:value mappings
                        continue
                    
                    # Server deviation: - SERVER: value
                    elif line.startswith('- ') and current_plugin and current_file:
                        # Parse server:value mapping
                        deviation_text = line[2:].strip()
                        if ':' in deviation_text:
                            server, value_str = deviation_text.split(':', 1)
                            server = server.strip()
                            value_str = value_str.strip()
                            
                            # Try to parse value as YAML
                            try:
                                import yaml
                                value = yaml.safe_load(value_str)
                            except:
                                value = value_str
                            
                            # Get universal value if available
                            universal_value = self.get_universal_config(current_plugin, current_file, key_path)
                            
                            deviation = DeviationItem(
                                plugin=current_plugin,
                                config_file=current_file,
                                key_path=key_path,
                                server=server,
                                value=value,
                                universal_value=universal_value
                            )
                            deviations.append(deviation)
        
        except Exception as e:
            print(f"Error parsing deviations: {e}")
        
        self.deviations = deviations
        return deviations
        current_plugin = None
        current_file = None
        current_key = None
        
        with open(self.deviations_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip()
                
                # Plugin header: ## PluginName
                if line.startswith('## ') and not line.startswith('###'):
                    current_plugin = line[3:].strip()
                    continue
                
                # File header: ### filename.yml
                if line.startswith('### '):
                    current_file = line[4:].strip()
                    continue
                
                # Key header: **key_path**
                if line.startswith('**') and line.endswith('**'):
                    current_key = line[2:-2].strip()
                    continue
                
                # Server value: - SERVER: `value`
                if line.startswith('- ') and ': ' in line and current_plugin and current_file and current_key:
                    parts = line[2:].split(': ', 1)
                    if len(parts) == 2:
                        server = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        # Remove backticks
                        if value_str.startswith('`') and value_str.endswith('`'):
                            value_str = value_str[1:-1]
                        
                        # Parse value
                        value = self._parse_value(value_str)
                        
                        # Get universal value
                        universal_value = self.get_universal_config(current_plugin, current_file, current_key)
                        
                        deviation = DeviationItem(
                            plugin=current_plugin,
                            config_file=current_file,
                            key_path=current_key,
                            server=server,
                            value=value,
                            universal_value=universal_value
                        )
                        deviations.append(deviation)
        
        self.deviations = deviations
        return deviations
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse string value to appropriate Python type"""
        import json
        
        # Try JSON parsing first
        try:
            return json.loads(value_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Try boolean
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # Try int
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Return as string
        return value_str
    
    def get_deviations_by_server(self, server_name: str) -> List[DeviationItem]:
        """
        Get deviations for specific server
        
        Args:
            server_name: Server identifier
            
        Returns:
            List of deviations for that server
        """
        return [d for d in self.deviations if d.server == server_name]
    
    def get_deviations_by_plugin(self, plugin_name: str) -> List[DeviationItem]:
        """
        Get deviations for specific plugin
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            List of deviations for that plugin
        """
        return [d for d in self.deviations if d.plugin == plugin_name]
    
    def get_deviations_by_status(self, status: DeviationStatus) -> List[DeviationItem]:
        """
        Get deviations by status
        
        Args:
            status: DeviationStatus enum value
            
        Returns:
            List of deviations with that status
        """
        return [d for d in self.deviations if d.status == status]
    
    def get_universal_config(self, plugin: str, config_file: str, key_path: str) -> Optional[Any]:
        """
        Get universal value for a specific config key
        
        Args:
            plugin: Plugin name
            config_file: Config file name
            key_path: Dot-separated key path
            
        Returns:
            Universal value or None
        """
        if plugin not in self.universal_configs:
            return None
        
        plugin_config = self.universal_configs[plugin]
        if config_file not in plugin_config.configs:
            return None
        
        # Navigate through nested config using dot notation
        config_data = plugin_config.configs[config_file]
        try:
            keys = key_path.split('.')
            current = config_data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            
            return current
        except Exception:
            return None


class DeviationManager:
    """Manages deviation review and approval workflow"""
    
    def __init__(self, storage_path: Path):
        """
        Initialize manager
        
        Args:
            storage_path: Path to store review data
        """
        self.storage_path = storage_path
        self.reviews: Dict[str, DeviationItem] = {}
    
    def flag_deviation(self, server_name: str, plugin_name: str, config_path: str, reason: str) -> bool:
        """
        Flag a deviation as problematic
        
        Args:
            server_name: Server name
            plugin_name: Plugin name
            config_path: Path to config file
            reason: Reason for flagging
            
        Returns:
            True if flagged successfully
        """
        try:
            from datetime import datetime
            import json
            
            # Create flagged deviations directory if it doesn't exist
            flagged_dir = self.storage_path / "flagged_deviations"
            flagged_dir.mkdir(exist_ok=True)
            
            # Create flag record
            flag_record = {
                'server_name': server_name,
                'plugin_name': plugin_name,
                'config_path': config_path,
                'reason': reason,
                'flagged_at': datetime.now().isoformat(),
                'status': 'active',
                'flagged_by': 'system'  # Could be enhanced to track user
            }
            
            # Generate unique flag ID
            flag_id = f"{server_name}_{plugin_name}_{hash(config_path) % 10000:04d}"
            flag_file = flagged_dir / f"{flag_id}.json"
            
            # Save flag record
            with open(flag_file, 'w', encoding='utf-8') as f:
                json.dump(flag_record, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to flag deviation: {e}")
            return False
    
    def get_flagged_bad_deviations(self) -> List[DeviationItem]:
        """
        Get all deviations flagged as bad (needing fixes)
        
        Returns:
            List of bad deviations
        """
        try:
            import json
            flagged_deviations = []
            flagged_dir = self.storage_path / "flagged_deviations"
            
            if not flagged_dir.exists():
                return []
            
            for flag_file in flagged_dir.glob("*.json"):
                try:
                    with open(flag_file, 'r', encoding='utf-8') as f:
                        flag_data = json.load(f)
                    
                    if flag_data.get('status') == 'active':
                        deviation_item = DeviationItem(
                            plugin=flag_data['plugin_name'],
                            config_file=flag_data['config_path'],
                            key_path=flag_data.get('key_path', ''),
                            server=flag_data['server_name'],
                            value=flag_data.get('actual_value'),
                            universal_value=None,
                            status=DeviationStatus.FLAGGED_BAD,
                            notes=flag_data.get('reason', ''),
                            flagged_by=flag_data.get('flagged_by'),
                            flagged_at=flag_data.get('flagged_at')
                        )
                        flagged_deviations.append(deviation_item)
                
                except Exception as e:
                    print(f"Error loading flag file {flag_file}: {e}")
                    continue
            
            return flagged_deviations
            
        except Exception as e:
            print(f"Error getting flagged deviations: {e}")
            return []
    
    def generate_fix_changes(self) -> Dict[str, Any]:
        """
        Generate change request JSON for all flagged bad deviations
        
        Returns:
            Change request in expected_changes_template.json format
        """
        try:
            from datetime import datetime
            import uuid
            
            # Get all flagged deviations
            flagged_deviations = self.get_flagged_bad_deviations()
            
            if not flagged_deviations:
                return {
                    'success': False,
                    'message': 'No flagged deviations to fix',
                    'changes': []
                }
            
            # Group by server and create changes
            changes_by_server = {}
            for deviation in flagged_deviations:
                server = deviation.server
                if server not in changes_by_server:
                    changes_by_server[server] = []
                
                # Create change for this deviation
                change = {
                    'action': 'update_yaml_key',
                    'file_path': f"{deviation.plugin}/{deviation.config_file}",
                    'key_path': deviation.key_path,
                    'old_value': deviation.value,
                    'new_value': deviation.universal_value,
                    'reason': f"Fix flagged deviation: {deviation.notes}"
                }
                changes_by_server[server].append(change)
            
            # Create change request
            change_request = {
                'request_id': str(uuid.uuid4()),
                'title': 'Fix Flagged Configuration Deviations',
                'description': f'Automated fix for {len(flagged_deviations)} flagged configuration deviations',
                'created_at': datetime.now().isoformat(),
                'target_servers': list(changes_by_server.keys()),
                'changes': []
            }
            
            # Add all changes
            for server, server_changes in changes_by_server.items():
                change_request['changes'].extend(server_changes)
            
            return {
                'success': True,
                'change_request': change_request,
                'affected_servers': list(changes_by_server.keys()),
                'total_fixes': len(flagged_deviations)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate fix changes'
            }
    
    def save_reviews(self):
        """Save review data to disk"""
        try:
            import json
            from ..core.settings import get_settings
            settings = get_settings()
            reviews_file = self.storage_path / settings.get_file_path("deviation_reviews")
            
            # Convert reviews to serializable format
            reviews_data = {}
            for review_id, deviation_item in self.reviews.items():
                reviews_data[review_id] = {
                    'plugin': deviation_item.plugin,
                    'config_file': deviation_item.config_file,
                    'key_path': deviation_item.key_path,
                    'server': deviation_item.server,
                    'value': deviation_item.value,
                    'universal_value': deviation_item.universal_value,
                    'status': deviation_item.status.value,
                    'replacement_value': deviation_item.replacement_value,
                    'notes': deviation_item.notes,
                    'flagged_by': deviation_item.flagged_by,
                    'flagged_at': deviation_item.flagged_at
                }
            
            # Ensure directory exists
            reviews_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to file
            with open(reviews_file, 'w', encoding='utf-8') as f:
                json.dump(reviews_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to save reviews: {e}")
            return False
    
    def load_reviews(self):
        """Load review data from disk"""
        try:
            import json
            from ..core.settings import get_settings
            settings = get_settings()
            reviews_file = self.storage_path / settings.get_file_path("deviation_reviews")
            
            if not reviews_file.exists():
                self.reviews = {}
                return True
            
            # Load from file
            with open(reviews_file, 'r', encoding='utf-8') as f:
                reviews_data = json.load(f)
            
            # Convert back to DeviationItem objects
            self.reviews = {}
            for review_id, item_data in reviews_data.items():
                deviation_item = DeviationItem(
                    plugin=item_data['plugin'],
                    config_file=item_data['config_file'],
                    key_path=item_data['key_path'],
                    server=item_data['server'],
                    value=item_data['value'],
                    universal_value=item_data.get('universal_value'),
                    status=DeviationStatus(item_data['status']),
                    replacement_value=item_data.get('replacement_value'),
                    notes=item_data.get('notes', ''),
                    flagged_by=item_data.get('flagged_by'),
                    flagged_at=item_data.get('flagged_at')
                )
                self.reviews[review_id] = deviation_item
            
            return True
            
        except Exception as e:
            print(f"Failed to load reviews: {e}")
            return False
