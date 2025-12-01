"""
Drift Detector Module

Detects configuration drift by comparing live server configs
against expected baseline. Generates reports for manual review.

Now platform-aware: separates Paper, Velocity, and Geyser configs
to avoid predictable confusion that cataclysmically destroys servers.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json


# Plugin platform mappings
PLUGIN_PLATFORMS = {
    'paper': set(),  # Loaded from categorization
    'velocity': set(),
    'geyser': set(),
}

# Load platform categorization
def _load_platform_mapping():
    """Load plugin platform categorization"""
    try:
        repo_root = Path(__file__).parent.parent.parent.parent
        categorization_file = repo_root / 'plugin_platform_categorization.json'
        
        if categorization_file.exists():
            with open(categorization_file, 'r') as f:
                categorization = json.load(f)
            
            PLUGIN_PLATFORMS['paper'] = set(categorization['platforms']['paper']['plugins'])
            PLUGIN_PLATFORMS['velocity'] = set(categorization['platforms']['velocity']['plugins'])
            PLUGIN_PLATFORMS['geyser'] = set(categorization['platforms']['geyser']['plugins'])
    except Exception as e:
        print(f"Warning: Could not load plugin categorization: {e}")

_load_platform_mapping()


class DriftDetector:
    """Detects and reports configuration drift across servers"""
    
    def __init__(self, baseline_path: Path, platform: Optional[str] = None):
        """
        Initialize drift detector
        
        Args:
            baseline_path: Path to baseline configuration data (can be platform-specific)
            platform: Optional platform filter ('paper', 'velocity', 'geyser')
        """
        self.baseline_path = baseline_path
        self.platform = platform
        self.baseline = None
        
        # If platform specified, load platform-specific expectations
        if platform and platform in ['paper', 'velocity', 'geyser']:
            platform_path = baseline_path.parent / 'expectations' / platform
            if platform_path.exists():
                self.baseline_path = platform_path
    
    def load_baseline(self) -> Dict[str, Any]:
        """
        Load baseline configuration
        
        Returns:
            Baseline configuration dict
        """
        try:
            from ..core.config_parser import ConfigParser
            
            # Cache baseline if already loaded
            if self.baseline is not None:
                return self.baseline
            
            baseline_config = {}
            
            # Check if baseline_path is a single file or directory
            if self.baseline_path.is_file():
                # Single baseline file (e.g., universal configs)
                self.baseline = ConfigParser.load_config(self.baseline_path)
                return self.baseline or {}
            
            elif self.baseline_path.is_dir():
                # Directory of baseline configs
                for config_file in self.baseline_path.rglob("*.yml"):
                    try:
                        # Create hierarchical structure: plugin_name -> config_file -> data
                        rel_path = config_file.relative_to(self.baseline_path)
                        parts = rel_path.parts
                        
                        if len(parts) >= 2:  # plugin/config.yml
                            plugin_name = parts[0]
                            config_name = parts[-1].replace('.yml', '')
                            
                            if plugin_name not in baseline_config:
                                baseline_config[plugin_name] = {}
                            
                            config_data = ConfigParser.load_config(config_file)
                            if config_data:
                                baseline_config[plugin_name][config_name] = config_data
                                
                    except Exception as e:
                        print(f"Warning: Could not load baseline config {config_file}: {e}")
                        continue
                
                # Also check for JSON and properties files
                for ext in ['*.json', '*.properties']:
                    for config_file in self.baseline_path.rglob(ext):
                        try:
                            rel_path = config_file.relative_to(self.baseline_path)
                            parts = rel_path.parts
                            
                            if len(parts) >= 2:
                                plugin_name = parts[0]
                                config_name = parts[-1].split('.')[0]  # Remove extension
                                
                                if plugin_name not in baseline_config:
                                    baseline_config[plugin_name] = {}
                                
                                config_data = ConfigParser.load_config(config_file)
                                if config_data:
                                    baseline_config[plugin_name][config_name] = config_data
                                    
                        except Exception as e:
                            print(f"Warning: Could not load baseline config {config_file}: {e}")
                            continue
                
                self.baseline = baseline_config
                return self.baseline
            
            else:
                print(f"Baseline path does not exist: {self.baseline_path}")
                self.baseline = {}
                return self.baseline
                
        except Exception as e:
            print(f"Error loading baseline configuration: {e}")
            self.baseline = {}
            return self.baseline
    
    def scan_server_configs(self, server_path: Path) -> Dict[str, Any]:
        """
        Scan a server's actual configuration files
        
        Args:
            server_path: Path to server's plugin configs
            
        Returns:
            Current configuration dict
        """
        try:
            from ..core.config_parser import ConfigParser
            
            current_config = {}
            
            if not server_path.exists():
                print(f"Server path does not exist: {server_path}")
                return current_config
            
            # Look for plugins directory
            plugins_path = server_path / "plugins" if not server_path.name == "plugins" else server_path
            
            if not plugins_path.exists():
                print(f"Plugins directory not found: {plugins_path}")
                return current_config
            
            # Scan each plugin directory
            for plugin_dir in plugins_path.iterdir():
                if not plugin_dir.is_dir():
                    continue
                    
                plugin_name = plugin_dir.name
                current_config[plugin_name] = {}
                
                # Scan for config files in plugin directory
                for config_file in plugin_dir.rglob("*.yml"):
                    try:
                        config_name = config_file.stem  # Filename without extension
                        config_data = ConfigParser.load_config(config_file)
                        if config_data:
                            current_config[plugin_name][config_name] = config_data
                    except Exception as e:
                        print(f"Warning: Could not load config {config_file}: {e}")
                
                # Also scan JSON and properties files
                for ext in ['*.json', '*.properties']:
                    for config_file in plugin_dir.rglob(ext):
                        try:
                            config_name = config_file.stem
                            config_data = ConfigParser.load_config(config_file)
                            if config_data:
                                current_config[plugin_name][config_name] = config_data
                        except Exception as e:
                            print(f"Warning: Could not load config {config_file}: {e}")
                
                # Remove empty plugin entries
                if not current_config[plugin_name]:
                    del current_config[plugin_name]
            
            return current_config
            
        except Exception as e:
            print(f"Error scanning server configs: {e}")
            return {}
    
    @staticmethod
    def get_plugin_platform(plugin_name: str) -> str:
        """
        Determine which platform a plugin belongs to
        
        Args:
            plugin_name: Name of plugin
            
        Returns:
            'paper', 'velocity', 'geyser', or 'unknown'
        """
        if plugin_name in PLUGIN_PLATFORMS['velocity']:
            return 'velocity'
        elif plugin_name in PLUGIN_PLATFORMS['geyser']:
            return 'geyser'
        elif plugin_name in PLUGIN_PLATFORMS['paper']:
            return 'paper'
        else:
            return 'unknown'
    
    def detect_drift(self, server_name: str, server_path: Path) -> List[Dict[str, Any]]:
        """
        Detect drift for a specific server
        
        Args:
            server_name: Name of server
            server_path: Path to server configs
            
        Returns:
            List of drift items with plugin, file, key, expected, actual
        """
        try:
            from ..core.config_parser import ConfigParser
            
            drift_items = []
            
            # Load baseline and current configs
            baseline = self.load_baseline()
            current = self.scan_server_configs(server_path)
            
            if not baseline:
                print(f"No baseline configuration loaded for drift detection")
                return drift_items
            
            # Compare each plugin in baseline against current
            if not isinstance(baseline, dict):
                return drift_items
            if not isinstance(current, dict):
                return drift_items
                
            for plugin_name, baseline_plugin in baseline.items():
                if not isinstance(baseline_plugin, dict):
                    continue
                current_plugin = current.get(plugin_name, {})
                
                # Ensure current_plugin is a dict before iterating
                if not isinstance(current_plugin, dict):
                    continue
                
                for config_file, baseline_config in baseline_plugin.items():
                    current_config = current_plugin.get(config_file, {})
                    
                    # Ensure current_config is a dict before comparing
                    if not isinstance(current_config, dict):
                        current_config = {}
                    
                    # Compare configurations recursively
                    drift_items.extend(
                        self._compare_configs(
                            plugin_name, 
                            config_file, 
                            baseline_config, 
                            current_config,
                            server_name
                        )
                    )
            
            # Also check for extra configs not in baseline (potential drift)
            for plugin_name, current_plugin in current.items():
                if plugin_name not in baseline:
                    # Skip if current_plugin is not a dict
                    if not isinstance(current_plugin, dict):
                        continue
                    for config_file, current_config in current_plugin.items():
                        drift_items.append({
                            'server_name': server_name,
                            'plugin_name': plugin_name,
                            'config_file': config_file,
                            'key_path': '<entire_file>',
                            'expected_value': None,  # Not in baseline
                            'actual_value': '<exists>',
                            'drift_type': 'extra_config',
                            'severity': 'medium'
                        })
            
            return drift_items
            
        except Exception as e:
            print(f"Error detecting drift for server {server_name}: {e}")
            return []
    
    def _compare_configs(self, plugin_name: str, config_file: str, baseline: Dict[str, Any], 
                        current: Dict[str, Any], server_name: str, prefix: str = '') -> List[Dict[str, Any]]:
        """
        Recursively compare baseline and current configurations
        
        Args:
            plugin_name: Name of plugin
            config_file: Config file name
            baseline: Baseline configuration
            current: Current configuration
            server_name: Server name for reporting
            prefix: Key path prefix for nested keys
            
        Returns:
            List of drift items
        """
        drift_items = []
        
        # Handle cases where baseline or current are not dictionaries
        if not isinstance(baseline, dict):
            # Baseline is a primitive value (string, number, bool, list, etc.)
            if isinstance(baseline, list) and isinstance(current, list):
                # Both are lists - compare them (order-sensitive)
                if baseline != current:
                    drift_items.append({
                        "server_name": server_name,
                        "plugin_name": plugin_name,
                        "config_file": config_file,
                        "key_path": prefix if prefix else "<root>",
                        "expected_value": baseline,
                        "actual_value": current,
                        "drift_type": "list_mismatch",
                        "severity": "low"
                    })
            elif type(baseline) != type(current):
                # Type mismatch (e.g., list vs string, dict vs list)
                drift_items.append({
                    "server_name": server_name,
                    "plugin_name": plugin_name,
                    "config_file": config_file,
                    "key_path": prefix if prefix else "<root>",
                    "expected_value": baseline,
                    "actual_value": current,
                    "drift_type": "type_mismatch",
                    "severity": "medium"
                })
            elif baseline != current:
                # Same type, different value
                drift_items.append({
                    "server_name": server_name,
                    "plugin_name": plugin_name,
                    "config_file": config_file,
                    "key_path": prefix if prefix else "<root>",
                    "expected_value": baseline,
                    "actual_value": current,
                    "drift_type": "value_mismatch",
                    "severity": "low"
                })
            return drift_items
        
        if not isinstance(current, dict):
            # Current is not a dict but baseline is
            drift_items.append({
                "server_name": server_name,
                "plugin_name": plugin_name,
                "config_file": config_file,
                "key_path": prefix if prefix else "<root>",
                "expected_value": baseline,
                "actual_value": current,
                "drift_type": "type_mismatch",
                "severity": "medium"
            })
            return drift_items
        
        # Both are dicts - compare recursively
        try:
            # Check each key in baseline
            for key, baseline_value in baseline.items():
                key_path = f"{prefix}.{key}" if prefix else key
                
                if key not in current:
                    # Missing key in current config
                    drift_items.append({
                        'server_name': server_name,
                        'plugin_name': plugin_name,
                        'config_file': config_file,
                        'key_path': key_path,
                        'expected_value': baseline_value,
                        'actual_value': None,
                        'drift_type': 'missing_key',
                        'severity': 'high' if isinstance(baseline_value, dict) else 'medium'
                    })
                else:
                    current_value = current[key]
                    
                    # Nested dict - recurse
                    if isinstance(baseline_value, dict) and isinstance(current_value, dict):
                        drift_items.extend(
                            self._compare_configs(
                                plugin_name, config_file, baseline_value, 
                                current_value, server_name, key_path
                            )
                        )
                    # List comparison
                    elif isinstance(baseline_value, list) and isinstance(current_value, list):
                        if baseline_value != current_value:
                            drift_items.append({
                                'server_name': server_name,
                                'plugin_name': plugin_name,
                                'config_file': config_file,
                                'key_path': key_path,
                                'expected_value': baseline_value,
                                'actual_value': current_value,
                                'drift_type': 'list_mismatch',
                                'severity': 'low'
                            })
                    # Type mismatch (e.g., dict vs list, string vs int)
                    elif type(baseline_value) != type(current_value):
                        drift_items.append({
                            'server_name': server_name,
                            'plugin_name': plugin_name,
                            'config_file': config_file,
                            'key_path': key_path,
                            'expected_value': baseline_value,
                            'actual_value': current_value,
                            'drift_type': 'type_mismatch',
                            'severity': 'medium'
                        })
                    # Value mismatch (same type, different value)
                    elif baseline_value != current_value:
                        drift_items.append({
                            'server_name': server_name,
                            'plugin_name': plugin_name,
                            'config_file': config_file,
                            'key_path': key_path,
                            'expected_value': baseline_value,
                            'actual_value': current_value,
                            'drift_type': 'value_mismatch',
                            'severity': 'low'
                        })
            
            # Check for extra keys in current config
            for key, current_value in current.items():
                if key not in baseline:
                    key_path = f"{prefix}.{key}" if prefix else key
                    drift_items.append({
                        'server_name': server_name,
                        'plugin_name': plugin_name,
                        'config_file': config_file,
                        'key_path': key_path,
                        'expected_value': None,
                        'actual_value': current_value,
                        'drift_type': 'extra_key',
                        'severity': 'low'
                    })
            
            return drift_items
            
        except Exception as e:
            print(f"Error comparing configs: {e}")
            return drift_items
    
    def scan_all_servers(self, utildata_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan all servers for configuration drift
        
        Args:
            utildata_path: Root path to utildata directory
            
        Returns:
            Dict mapping server names to drift items
        """
        try:
            all_drift = {}
            
            if not utildata_path.exists():
                print(f"Utildata path does not exist: {utildata_path}")
                return all_drift
            
            # Scan each server directory
            for server_dir in utildata_path.iterdir():
                if not server_dir.is_dir():
                    continue
                
                server_name = server_dir.name
                
                # Skip system directories
                if server_name.startswith('.') or server_name in ['logs', 'backups', 'temp']:
                    continue
                
                print(f"Scanning server: {server_name}")
                
                try:
                    drift_items = self.detect_drift(server_name, server_dir)
                    if drift_items:
                        all_drift[server_name] = drift_items
                        print(f"Found {len(drift_items)} drift items for {server_name}")
                    else:
                        print(f"No drift detected for {server_name}")
                        
                except Exception as e:
                    print(f"Error scanning server {server_name}: {e}")
                    continue
            
            return all_drift
            
        except Exception as e:
            print(f"Error scanning all servers: {e}")
            return {}
    
    def generate_drift_report(self, output_path: Path, drift_data: Dict[str, List[Dict[str, Any]]]) -> None:
        """
        Generate drift report for manual review
        
        Args:
            output_path: Where to write report
            drift_data: Drift data from scan_all_servers
        """
        import json
        from datetime import datetime
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create comprehensive report
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_servers_scanned': len(drift_data),
                'servers_with_drift': len([s for s in drift_data.values() if s]),
                'total_drift_items': sum(len(items) for items in drift_data.values()),
                'summary_by_server': {},
                'summary_by_severity': {'high': 0, 'medium': 0, 'low': 0},
                'summary_by_type': {},
                'prioritized_items': self.prioritize_drift_items(drift_data),
                'detailed_findings': drift_data
            }
            
            # Generate server summaries
            for server_name, drift_items in drift_data.items():
                if not drift_items:
                    continue
                    
                server_summary = {
                    'total_drift_items': len(drift_items),
                    'by_severity': {'high': 0, 'medium': 0, 'low': 0},
                    'by_type': {},
                    'affected_plugins': set(),
                    'critical_issues': []
                }
                
                for item in drift_items:
                    # Count by severity
                    severity = item.get('severity', 'low')
                    server_summary['by_severity'][severity] += 1
                    report['summary_by_severity'][severity] += 1
                    
                    # Count by type
                    drift_type = item.get('drift_type', 'unknown')
                    server_summary['by_type'][drift_type] = server_summary['by_type'].get(drift_type, 0) + 1
                    report['summary_by_type'][drift_type] = report['summary_by_type'].get(drift_type, 0) + 1
                    
                    # Track affected plugins
                    server_summary['affected_plugins'].add(item.get('plugin_name', 'unknown'))
                    
                    # Flag critical issues
                    if severity == 'high' or drift_type == 'missing_key':
                        server_summary['critical_issues'].append({
                            'plugin': item.get('plugin_name'),
                            'config': item.get('config_file'),
                            'key': item.get('key_path'),
                            'issue': f"{drift_type}: {item.get('expected_value')} -> {item.get('actual_value')}"
                        })
                
                # Convert set to list for JSON serialization
                server_summary['affected_plugins'] = list(server_summary['affected_plugins'])
                report['summary_by_server'][server_name] = server_summary
            
            # Write report
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, separators=(',', ': '), default=str)
            
            print(f"Drift report generated: {output_path}")
            print(f"Total servers with drift: {report['servers_with_drift']}/{report['total_servers_scanned']}")
            print(f"Total drift items: {report['total_drift_items']}")
            
        except Exception as e:
            print(f"Error generating drift report: {e}")
    
    def prioritize_drift_items(self, drift_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Prioritize drift items by severity/impact
        
        Args:
            drift_data: Drift data from scan_all_servers
            
        Returns:
            Sorted list of drift items by priority
        """
        try:
            all_items = []
            
            # Flatten all drift items with priority scoring
            for server_name, drift_items in drift_data.items():
                for item in drift_items:
                    # Calculate priority score
                    priority_score = self._calculate_priority_score(item)
                    
                    # Add priority score to item
                    prioritized_item = item.copy()
                    prioritized_item['priority_score'] = priority_score
                    all_items.append(prioritized_item)
            
            # Sort by priority score (higher score = higher priority)
            all_items.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            
            return all_items[:50]  # Return top 50 items
            
        except Exception as e:
            print(f"Error prioritizing drift items: {e}")
            return []
    
    def _calculate_priority_score(self, item: Dict[str, Any]) -> int:
        """
        Calculate priority score for a drift item
        
        Args:
            item: Drift item
            
        Returns:
            Priority score (higher = more important)
        """
        score = 0
        
        # Base score by severity
        severity = item.get('severity', 'low')
        if severity == 'high':
            score += 100
        elif severity == 'medium':
            score += 50
        elif severity == 'low':
            score += 10
        
        # Additional score by drift type
        drift_type = item.get('drift_type', 'unknown')
        if drift_type == 'missing_key':
            score += 50  # Missing keys are serious
        elif drift_type == 'value_mismatch':
            score += 30  # Value mismatches need attention
        elif drift_type == 'extra_key':
            score += 10  # Extra keys are less critical
        elif drift_type == 'extra_config':
            score += 20  # Extra configs may indicate issues
        
        # Boost score for critical plugins
        plugin_name = item.get('plugin_name', '').lower()
        critical_plugins = [
            'coreprotect', 'luckperms', 'worldedit', 'worldguard', 
            'protocollib', 'vault', 'placeholderapi', 'essentials'
        ]
        if any(critical in plugin_name for critical in critical_plugins):
            score += 30
        
        # Boost score for security-related configs
        key_path = item.get('key_path', '').lower()
        security_keywords = ['password', 'token', 'key', 'secret', 'auth', 'permission']
        if any(keyword in key_path for keyword in security_keywords):
            score += 40
        
        return score
