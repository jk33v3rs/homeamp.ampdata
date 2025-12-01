"""
Compliance Checker Module

Compares current network state against expected/baseline configurations
to determine which changes have been completed and which are still required.
"""

from typing import Dict, List, Any
from pathlib import Path


class ComplianceChecker:
    """Checks network compliance against expected configuration state"""
    
    def __init__(self, baseline_path: Path, current_state_path: Path):
        """
        Initialize compliance checker
        
        Args:
            baseline_path: Path to universal configs baseline
            current_state_path: Path to current network state data
        """
        self.baseline_path = baseline_path
        self.current_state_path = current_state_path
        self.baseline = None
        self.current_state = None
    
    def load_baseline(self) -> Dict[str, Any]:
        """
        Load baseline configuration data
        
        Returns:
            Baseline configuration dict
        """
        try:
            from ..core.config_parser import ConfigParser
            
            # Cache baseline if already loaded
            if self.baseline is not None:
                return self.baseline
            
            baseline_config = {}
            
            if not self.baseline_path.exists():
                print(f"Baseline path does not exist: {self.baseline_path}")
                self.baseline = {}
                return self.baseline
            
            # Load baseline configurations
            if self.baseline_path.is_file():
                # Single baseline file
                self.baseline = ConfigParser.load_config(self.baseline_path)
                return self.baseline or {}
            
            elif self.baseline_path.is_dir():
                # Directory of baseline configs
                for config_file in self.baseline_path.rglob("*.yml"):
                    try:
                        rel_path = config_file.relative_to(self.baseline_path)
                        parts = rel_path.parts
                        
                        if len(parts) >= 2:  # server/plugin/config.yml or plugin/config.yml
                            if len(parts) == 2:  # plugin/config.yml
                                plugin_name = parts[0]
                                config_name = parts[1].replace('.yml', '')
                                
                                if plugin_name not in baseline_config:
                                    baseline_config[plugin_name] = {}
                                
                                config_data = ConfigParser.load_config(config_file)
                                if config_data:
                                    baseline_config[plugin_name][config_name] = config_data
                            
                            elif len(parts) == 3:  # server/plugin/config.yml
                                server_name = parts[0]
                                plugin_name = parts[1]
                                config_name = parts[2].replace('.yml', '')
                                
                                if server_name not in baseline_config:
                                    baseline_config[server_name] = {}
                                if plugin_name not in baseline_config[server_name]:
                                    baseline_config[server_name][plugin_name] = {}
                                
                                config_data = ConfigParser.load_config(config_file)
                                if config_data:
                                    baseline_config[server_name][plugin_name][config_name] = config_data
                                    
                    except Exception as e:
                        print(f"Warning: Could not load baseline config {config_file}: {e}")
                        continue
                
                # Also load JSON and properties files
                for ext in ['*.json', '*.properties']:
                    for config_file in self.baseline_path.rglob(ext):
                        try:
                            rel_path = config_file.relative_to(self.baseline_path)
                            parts = rel_path.parts
                            config_name = parts[-1].split('.')[0]
                            
                            if len(parts) == 2:  # plugin/config
                                plugin_name = parts[0]
                                if plugin_name not in baseline_config:
                                    baseline_config[plugin_name] = {}
                                config_data = ConfigParser.load_config(config_file)
                                if config_data:
                                    baseline_config[plugin_name][config_name] = config_data
                            
                            elif len(parts) == 3:  # server/plugin/config
                                server_name = parts[0]
                                plugin_name = parts[1]
                                if server_name not in baseline_config:
                                    baseline_config[server_name] = {}
                                if plugin_name not in baseline_config[server_name]:
                                    baseline_config[server_name][plugin_name] = {}
                                config_data = ConfigParser.load_config(config_file)
                                if config_data:
                                    baseline_config[server_name][plugin_name][config_name] = config_data
                                    
                        except Exception as e:
                            print(f"Warning: Could not load baseline config {config_file}: {e}")
                            continue
                
                self.baseline = baseline_config
                return self.baseline
            
            else:
                print(f"Baseline path is neither file nor directory: {self.baseline_path}")
                self.baseline = {}
                return self.baseline
                
        except Exception as e:
            print(f"Error loading baseline configuration: {e}")
            self.baseline = {}
            return self.baseline
    
    def load_current_state(self) -> Dict[str, Any]:
        """
        Load current network state
        
        Returns:
            Current state dict
        """
        try:
            from ..core.config_parser import ConfigParser
            
            # Cache current state if already loaded
            if self.current_state is not None:
                return self.current_state
            
            current_config = {}
            
            if not self.current_state_path.exists():
                print(f"Current state path does not exist: {self.current_state_path}")
                self.current_state = {}
                return self.current_state
            
            # Load current state configurations
            if self.current_state_path.is_file():
                # Single current state file (e.g., from utildata analysis)
                self.current_state = ConfigParser.load_config(self.current_state_path)
                return self.current_state or {}
            
            elif self.current_state_path.is_dir():
                # Directory structure (likely utildata format)
                # Scan for server directories
                for server_dir in self.current_state_path.iterdir():
                    if not server_dir.is_dir():
                        continue
                    
                    server_name = server_dir.name
                    
                    # Skip system directories
                    if server_name.startswith('.') or server_name in ['logs', 'backups', 'temp']:
                        continue
                    
                    current_config[server_name] = {}
                    
                    # Look for plugins directory
                    plugins_dir = server_dir / "plugins"
                    if not plugins_dir.exists():
                        continue
                    
                    # Scan each plugin
                    for plugin_dir in plugins_dir.iterdir():
                        if not plugin_dir.is_dir():
                            continue
                        
                        plugin_name = plugin_dir.name
                        current_config[server_name][plugin_name] = {}
                        
                        # Load all config files for this plugin
                        for config_file in plugin_dir.rglob("*.yml"):
                            try:
                                config_name = config_file.stem
                                config_data = ConfigParser.load_config(config_file)
                                if config_data:
                                    current_config[server_name][plugin_name][config_name] = config_data
                            except Exception as e:
                                print(f"Warning: Could not load current config {config_file}: {e}")
                        
                        # Also load JSON and properties files
                        for ext in ['*.json', '*.properties']:
                            for config_file in plugin_dir.rglob(ext):
                                try:
                                    config_name = config_file.stem
                                    config_data = ConfigParser.load_config(config_file)
                                    if config_data:
                                        current_config[server_name][plugin_name][config_name] = config_data
                                except Exception as e:
                                    print(f"Warning: Could not load current config {config_file}: {e}")
                        
                        # Remove empty plugin entries
                        if not current_config[server_name][plugin_name]:
                            del current_config[server_name][plugin_name]
                    
                    # Remove empty server entries
                    if not current_config[server_name]:
                        del current_config[server_name]
                
                self.current_state = current_config
                return self.current_state
            
            else:
                print(f"Current state path is neither file nor directory: {self.current_state_path}")
                self.current_state = {}
                return self.current_state
                
        except Exception as e:
            print(f"Error loading current state: {e}")
            self.current_state = {}
            return self.current_state
    
    def compare_states(self) -> Dict[str, Any]:
        """
        Compare current state vs baseline to find differences
        
        Returns:
            Comparison results with compliant/non-compliant items
        """
        try:
            from ..core.safety_validator import SafetyValidator
            
            # Load both states
            baseline = self.load_baseline()
            current = self.load_current_state()
            
            comparison_results = {
                'compliant_items': [],
                'non_compliant_items': [],
                'missing_items': [],
                'extra_items': [],
                'summary': {
                    'total_baseline_configs': 0,
                    'compliant_count': 0,
                    'non_compliant_count': 0,
                    'missing_count': 0,
                    'extra_count': 0,
                    'compliance_percentage': 0
                }
            }
            
            # Compare baseline against current state
            comparison_results['total_baseline_configs'] = self._count_configs(baseline)
            
            # Check each item in baseline
            for server_or_plugin, server_data in baseline.items():
                if isinstance(server_data, dict):
                    for plugin_or_config, plugin_data in server_data.items():
                        if isinstance(plugin_data, dict):
                            # Three-level structure: server/plugin/config
                            server_name = server_or_plugin
                            plugin_name = plugin_or_config
                            
                            current_server = current.get(server_name, {})
                            current_plugin = current_server.get(plugin_name, {})
                            
                            for config_name, baseline_config in plugin_data.items():
                                current_config = current_plugin.get(config_name, {})
                                
                                # Compare this configuration
                                self._compare_single_config(
                                    server_name, plugin_name, config_name,
                                    baseline_config, current_config,
                                    comparison_results
                                )
                        else:
                            # Two-level structure: plugin/config
                            plugin_name = server_or_plugin
                            config_name = plugin_or_config
                            baseline_config = plugin_data
                            
                            # Look for this config across all servers
                            found_compliant = False
                            for server_name, server_configs in current.items():
                                current_plugin = server_configs.get(plugin_name, {})
                                current_config = current_plugin.get(config_name, {})
                                
                                if current_config:
                                    self._compare_single_config(
                                        server_name, plugin_name, config_name,
                                        baseline_config, current_config,
                                        comparison_results
                                    )
                                    found_compliant = True
                            
                            if not found_compliant:
                                comparison_results['missing_items'].append({
                                    'plugin_name': plugin_name,
                                    'config_name': config_name,
                                    'baseline_config': baseline_config,
                                    'servers_missing': list(current.keys())
                                })
            
            # Check for extra items in current state not in baseline
            for server_name, server_configs in current.items():
                for plugin_name, plugin_configs in server_configs.items():
                    for config_name, config_data in plugin_configs.items():
                        # Check if this exists in baseline
                        baseline_has_config = False
                        
                        # Check three-level baseline structure
                        if server_name in baseline:
                            if plugin_name in baseline[server_name]:
                                if config_name in baseline[server_name][plugin_name]:
                                    baseline_has_config = True
                        
                        # Check two-level baseline structure
                        if plugin_name in baseline:
                            if config_name in baseline[plugin_name]:
                                baseline_has_config = True
                        
                        if not baseline_has_config:
                            comparison_results['extra_items'].append({
                                'server_name': server_name,
                                'plugin_name': plugin_name,
                                'config_name': config_name,
                                'current_config': config_data
                            })
            
            # Calculate summary statistics
            summary = comparison_results['summary']
            summary['compliant_count'] = len(comparison_results['compliant_items'])
            summary['non_compliant_count'] = len(comparison_results['non_compliant_items'])
            summary['missing_count'] = len(comparison_results['missing_items'])
            summary['extra_count'] = len(comparison_results['extra_items'])
            
            total_items = summary['compliant_count'] + summary['non_compliant_count'] + summary['missing_count']
            if total_items > 0:
                summary['compliance_percentage'] = (summary['compliant_count'] / total_items) * 100
            
            return comparison_results
            
        except Exception as e:
            print(f"Error comparing states: {e}")
            return {
                'compliant_items': [],
                'non_compliant_items': [],
                'missing_items': [],
                'extra_items': [],
                'summary': {'error': str(e)}
            }
    
    def _count_configs(self, config_dict: Dict[str, Any]) -> int:
        """Count total number of configurations in nested dict"""
        count = 0
        for key, value in config_dict.items():
            if isinstance(value, dict):
                count += self._count_configs(value)
            else:
                count += 1
        return count
    
    def _compare_single_config(self, server_name: str, plugin_name: str, config_name: str,
                              baseline_config: Any, current_config: Any, 
                              results: Dict[str, Any]) -> None:
        """Compare a single configuration and update results"""
        try:
            from ..core.safety_validator import SafetyValidator
            
            if not current_config:
                # Missing configuration
                results['missing_items'].append({
                    'server_name': server_name,
                    'plugin_name': plugin_name,
                    'config_name': config_name,
                    'baseline_config': baseline_config,
                    'issue': 'Configuration not found'
                })
            elif SafetyValidator.validate_expected_value(current_config, baseline_config, strict=False):
                # Compliant configuration
                results['compliant_items'].append({
                    'server_name': server_name,
                    'plugin_name': plugin_name,
                    'config_name': config_name,
                    'status': 'compliant'
                })
            else:
                # Non-compliant configuration
                results['non_compliant_items'].append({
                    'server_name': server_name,
                    'plugin_name': plugin_name,
                    'config_name': config_name,
                    'expected': baseline_config,
                    'actual': current_config,
                    'issue': 'Configuration value mismatch'
                })
        except Exception as e:
            print(f"Error comparing config {server_name}/{plugin_name}/{config_name}: {e}")
            results['non_compliant_items'].append({
                'server_name': server_name,
                'plugin_name': plugin_name,
                'config_name': config_name,
                'expected': baseline_config,
                'actual': current_config,
                'issue': f'Comparison error: {e}'
            })
    
    def check_expected_changes(self, expected_changes_path: Path) -> Dict[str, Any]:
        """
        Check which expected changes have been completed
        
        Args:
            expected_changes_path: Path to expected changes JSON
            
        Returns:
            Dict with completed_changes and pending_changes lists
        """
        try:
            from ..core.config_parser import ConfigParser
            
            # Load expected changes
            if not expected_changes_path.exists():
                print(f"Expected changes file not found: {expected_changes_path}")
                return {
                    'completed_changes': [],
                    'pending_changes': [],
                    'summary': {'error': 'Expected changes file not found'}
                }
            
            expected_changes = ConfigParser.load_config(expected_changes_path)
            if not expected_changes:
                return {
                    'completed_changes': [],
                    'pending_changes': [],
                    'summary': {'error': 'Could not load expected changes'}
                }
            
            # Load current state for comparison
            current_state = self.load_current_state()
            
            completed_changes = []
            pending_changes = []
            
            # Process expected changes
            changes = expected_changes.get('changes', [])
            if not isinstance(changes, list):
                changes = [expected_changes]  # Single change object
            
            for change in changes:
                try:
                    server_name = change.get('server_name', 'all')
                    plugin_name = change.get('plugin_name')
                    config_file = change.get('config_file')
                    key_path = change.get('key_path')
                    expected_value = change.get('new_value')
                    
                    if not all([plugin_name, config_file, key_path, expected_value is not None]):
                        pending_changes.append({
                            'change': change,
                            'status': 'invalid',
                            'reason': 'Missing required fields'
                        })
                        continue
                    
                    change_completed = False
                    completion_details = []
                    
                    # Check if change has been applied
                    if server_name == 'all':
                        # Check across all servers
                        for srv_name, srv_configs in current_state.items():
                            plugin_configs = srv_configs.get(plugin_name, {})
                            config_data = plugin_configs.get(config_file.replace('.yml', ''), {})
                            
                            if config_data:
                                from ..core.config_parser import ConfigParser
                                current_value = ConfigParser.get_nested_value(config_data, key_path)
                                
                                if current_value == expected_value:
                                    completion_details.append({
                                        'server': srv_name,
                                        'status': 'completed',
                                        'current_value': current_value
                                    })
                                    change_completed = True
                                else:
                                    completion_details.append({
                                        'server': srv_name,
                                        'status': 'pending',
                                        'current_value': current_value,
                                        'expected_value': expected_value
                                    })
                    else:
                        # Check specific server
                        server_configs = current_state.get(server_name, {})
                        plugin_configs = server_configs.get(plugin_name, {})
                        config_data = plugin_configs.get(config_file.replace('.yml', ''), {})
                        
                        if config_data:
                            from ..core.config_parser import ConfigParser
                            current_value = ConfigParser.get_nested_value(config_data, key_path)
                            
                            if current_value == expected_value:
                                change_completed = True
                                completion_details.append({
                                    'server': server_name,
                                    'status': 'completed',
                                    'current_value': current_value
                                })
                            else:
                                completion_details.append({
                                    'server': server_name,
                                    'status': 'pending',
                                    'current_value': current_value,
                                    'expected_value': expected_value
                                })
                        else:
                            completion_details.append({
                                'server': server_name,
                                'status': 'pending',
                                'reason': 'Configuration not found'
                            })
                    
                    # Categorize the change
                    change_result = {
                        'change': change,
                        'completion_details': completion_details,
                        'overall_status': 'completed' if change_completed else 'pending'
                    }
                    
                    if change_completed:
                        completed_changes.append(change_result)
                    else:
                        pending_changes.append(change_result)
                        
                except Exception as e:
                    print(f"Error processing change: {e}")
                    pending_changes.append({
                        'change': change,
                        'status': 'error',
                        'reason': str(e)
                    })
            
            return {
                'completed_changes': completed_changes,
                'pending_changes': pending_changes,
                'summary': {
                    'total_changes': len(changes),
                    'completed_count': len(completed_changes),
                    'pending_count': len(pending_changes),
                    'completion_percentage': (len(completed_changes) / len(changes) * 100) if changes else 0
                }
            }
            
        except Exception as e:
            print(f"Error checking expected changes: {e}")
            return {
                'completed_changes': [],
                'pending_changes': [],
                'summary': {'error': str(e)}
            }
    
    def generate_compliance_report(self, output_path: Path) -> None:
        """
        Generate compliance report showing network status
        
        Args:
            output_path: Where to write the report
        """
        import json
        from datetime import datetime
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate comparison data
            comparison_results = self.compare_states()
            
            # Create comprehensive compliance report
            report = {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'compliance_report',
                'baseline_path': str(self.baseline_path),
                'current_state_path': str(self.current_state_path),
                'executive_summary': {
                    'overall_compliance_percentage': comparison_results['summary'].get('compliance_percentage', 0),
                    'total_configurations_checked': comparison_results['summary'].get('total_baseline_configs', 0),
                    'compliant_configurations': comparison_results['summary'].get('compliant_count', 0),
                    'non_compliant_configurations': comparison_results['summary'].get('non_compliant_count', 0),
                    'missing_configurations': comparison_results['summary'].get('missing_count', 0),
                    'extra_configurations': comparison_results['summary'].get('extra_count', 0)
                },
                'detailed_findings': comparison_results,
                'recommendations': self._generate_recommendations(comparison_results),
                'next_actions': self._generate_next_actions(comparison_results)
            }
            
            # Write report to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, separators=(',', ': '), default=str)
            
            print(f"Compliance report generated: {output_path}")
            print(f"Overall compliance: {report['executive_summary']['overall_compliance_percentage']:.1f}%")
            print(f"Compliant: {report['executive_summary']['compliant_configurations']}")
            print(f"Non-compliant: {report['executive_summary']['non_compliant_configurations']}")
            print(f"Missing: {report['executive_summary']['missing_configurations']}")
            
        except Exception as e:
            print(f"Error generating compliance report: {e}")
    
    def _generate_recommendations(self, comparison_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on compliance results"""
        recommendations = []
        
        try:
            summary = comparison_results.get('summary', {})
            
            # Compliance percentage recommendations
            compliance_pct = summary.get('compliance_percentage', 0)
            if compliance_pct < 50:
                recommendations.append("CRITICAL: Compliance is below 50%. Immediate action required.")
            elif compliance_pct < 80:
                recommendations.append("WARNING: Compliance is below 80%. Review and remediation needed.")
            elif compliance_pct < 95:
                recommendations.append("NOTICE: Good compliance but room for improvement.")
            else:
                recommendations.append("EXCELLENT: High compliance achieved.")
            
            # Missing configurations
            missing_count = summary.get('missing_count', 0)
            if missing_count > 0:
                recommendations.append(f"Deploy {missing_count} missing configurations to improve compliance.")
            
            # Non-compliant configurations
            non_compliant_count = summary.get('non_compliant_count', 0)
            if non_compliant_count > 0:
                recommendations.append(f"Review and fix {non_compliant_count} non-compliant configurations.")
            
            # Extra configurations
            extra_count = summary.get('extra_count', 0)
            if extra_count > 0:
                recommendations.append(f"Review {extra_count} extra configurations for necessity.")
            
        except Exception as e:
            recommendations.append(f"Error generating recommendations: {e}")
        
        return recommendations
    
    def _generate_next_actions(self, comparison_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate specific next actions based on compliance results"""
        actions = []
        
        try:
            # Actions for missing items
            missing_items = comparison_results.get('missing_items', [])
            for item in missing_items[:5]:  # Top 5 missing items
                actions.append({
                    'action': 'deploy_configuration',
                    'priority': 'high',
                    'description': f"Deploy {item.get('plugin_name')}/{item.get('config_name')} configuration",
                    'target': item.get('servers_missing', ['unknown'])[0] if item.get('servers_missing') else 'unknown'
                })
            
            # Actions for non-compliant items
            non_compliant_items = comparison_results.get('non_compliant_items', [])
            for item in non_compliant_items[:5]:  # Top 5 non-compliant items
                actions.append({
                    'action': 'fix_configuration',
                    'priority': 'medium',
                    'description': f"Fix {item.get('plugin_name')}/{item.get('config_name')} on {item.get('server_name')}",
                    'target': item.get('server_name', 'unknown'),
                    'expected': str(item.get('expected')),
                    'actual': str(item.get('actual'))
                })
            
            # Actions for extra items (lower priority)
            extra_items = comparison_results.get('extra_items', [])
            for item in extra_items[:3]:  # Top 3 extra items
                actions.append({
                    'action': 'review_extra_configuration',
                    'priority': 'low',
                    'description': f"Review extra {item.get('plugin_name')}/{item.get('config_name')} on {item.get('server_name')}",
                    'target': item.get('server_name', 'unknown')
                })
                
        except Exception as e:
            actions.append({
                'action': 'error',
                'priority': 'high',
                'description': f"Error generating actions: {e}"
            })
        
        return actions
