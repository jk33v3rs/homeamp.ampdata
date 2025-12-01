"""
Deviation Analyzer Module

Analyzes configuration deviations across the server network to identify:
- Per-server intentional settings (world names, server IDs)
- Dev server expected differences
- Probable misconfigurations requiring review
- Even splits that may indicate intentional grouping
- Multiple variations suggesting high inconsistency
"""

from typing import Dict, List, Tuple, Any
from pathlib import Path


class DeviationAnalyzer:
    """Analyzes configuration deviations to categorize and prioritize issues"""
    
    def __init__(self, deviations_file: Path):
        """
        Initialize analyzer with deviations data
        
        Args:
            deviations_file: Path to plugin_configs_deviations.md
        """
        self.deviations_file = deviations_file
        self.data = None
    
    def parse_deviations(self) -> Dict[str, Dict[str, Dict[str, Dict[str, str]]]]:
        """
        Parse deviations markdown into structured data
        
        Returns:
            Nested dict: {plugin: {file: {key: {server: value}}}}
        """
        try:
            if self.data is not None:
                return self.data
            
            if not self.deviations_file.exists():
                print(f"Deviations file not found: {self.deviations_file}")
                self.data = {}
                return self.data
            
            deviations = {}
            current_plugin = None
            current_file = None
            current_key = None
            
            with open(self.deviations_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                
                if not line or line.startswith('<!--'):
                    continue
                
                # Plugin headers (# PluginName)
                if line.startswith('# ') and not line.startswith('## '):
                    current_plugin = line[2:].strip()
                    if current_plugin not in deviations:
                        deviations[current_plugin] = {}
                    continue
                
                # Config file headers (## config.yml)
                if line.startswith('## '):
                    if current_plugin:
                        current_file = line[3:].strip()
                        if current_file not in deviations[current_plugin]:
                            deviations[current_plugin][current_file] = {}
                    continue
                
                # Key headers (### some.config.key)
                if line.startswith('### '):
                    if current_plugin and current_file:
                        current_key = line[4:].strip()
                        if current_key not in deviations[current_plugin][current_file]:
                            deviations[current_plugin][current_file][current_key] = {}
                    continue
                
                # Server value lines (- **SERVER01**: `value`)
                if line.startswith('- **') and current_plugin and current_file and current_key:
                    try:
                        # Parse format: - **SERVER01**: `value`
                        parts = line.split('**: ')
                        if len(parts) == 2:
                            server = parts[0].replace('- **', '').strip()
                            value = parts[1].strip()
                            
                            # Remove backticks and quotes
                            if value.startswith('`') and value.endswith('`'):
                                value = value[1:-1]
                            elif value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            deviations[current_plugin][current_file][current_key][server] = value
                    except Exception as e:
                        print(f"Warning: Could not parse line: {line} - {e}")
                        continue
            
            self.data = deviations
            return self.data
            
        except Exception as e:
            print(f"Error parsing deviations file: {e}")
            self.data = {}
            return self.data
    
    def is_per_server_setting(self, key: str, values: Dict[str, str]) -> Tuple[bool, str]:
        """
        Identify settings that are intentionally per-server
        
        Args:
            key: Configuration key name
            values: Server->value mapping
            
        Returns:
            (is_per_server, reason)
        """
        try:
            key_lower = key.lower()
            
            # Common per-server setting patterns
            per_server_keywords = [
                'server-name', 'server_name', 'servername',
                'world-name', 'world_name', 'worldname',
                'server-id', 'server_id', 'serverid',
                'port', 'ip', 'address', 'host',
                'database.host', 'database.port',
                'rcon.port', 'rcon-port',
                'server.ip', 'server.port'
            ]
            
            # Check if key matches per-server patterns
            for keyword in per_server_keywords:
                if keyword in key_lower:
                    return True, f"Key '{key}' contains per-server identifier '{keyword}'"
            
            # Check if values look like server-specific data
            value_list = list(values.values())
            
            # Check for server names in values
            if any(server in str(value).upper() for value in value_list for server in values.keys()):
                return True, "Values contain server names"
            
            # Check for world names (common pattern: world_servername)
            if any('world_' in str(value).lower() for value in value_list):
                return True, "Values appear to be world names"
            
            # Check for port numbers
            if all(str(value).isdigit() and 1000 <= int(value) <= 65535 for value in value_list):
                return True, "Values appear to be port numbers"
            
            # Check for IP addresses
            if any('.' in str(value) and len(str(value).split('.')) == 4 for value in value_list):
                return True, "Values appear to be IP addresses"
            
            # Check for database connection strings
            if any('jdbc:' in str(value) or 'mysql://' in str(value) for value in value_list):
                return True, "Values appear to be database connection strings"
            
            return False, "No per-server patterns detected"
            
        except Exception as e:
            print(f"Error analyzing per-server setting: {e}")
            return False, f"Error: {e}"
    
    def is_dev_server_deviation(self, servers: List[str]) -> Tuple[bool, str]:
        """
        Check if deviation is only DEV01 being different
        
        Args:
            servers: List of servers with deviations
            
        Returns:
            (is_dev_deviation, reason)
        """
        try:
            dev_servers = ['DEV01', 'dev01', 'DEVELOPMENT', 'development', 'TEST01', 'test01']
            
            # Check if only dev servers have deviations
            has_dev_server = any(dev in servers for dev in dev_servers)
            has_non_dev_server = any(server not in dev_servers for server in servers)
            
            if has_dev_server and not has_non_dev_server:
                return True, "Only development/test servers have deviations"
            elif has_dev_server and len(servers) <= 2:
                return True, "Minimal deviation with development server involved"
            else:
                return False, "Production servers involved in deviation"
                
        except Exception as e:
            print(f"Error checking dev server deviation: {e}")
            return False, f"Error: {e}"
    
    def analyze_deviation_pattern(self, key: str, server_values: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze a specific deviation to categorize it
        
        Args:
            key: Configuration key
            server_values: Server->value mapping
            
        Returns:
            Analysis dict with category, severity, recommendations
        """
        try:
            analysis = {
                'key': key,
                'server_count': len(server_values),
                'unique_values': len(set(server_values.values())),
                'category': 'unknown',
                'severity': 'medium',
                'confidence': 0.5,
                'recommendations': []
            }
            
            servers = list(server_values.keys())
            values = list(server_values.values())
            
            # Check if it's a per-server setting
            is_per_server, per_server_reason = self.is_per_server_setting(key, server_values)
            if is_per_server:
                analysis['category'] = 'per_server_intentional'
                analysis['severity'] = 'low'
                analysis['confidence'] = 0.9
                analysis['recommendations'].append(f"Intentional per-server setting: {per_server_reason}")
                return analysis
            
            # Check if it's a dev server deviation
            is_dev, dev_reason = self.is_dev_server_deviation(servers)
            if is_dev:
                analysis['category'] = 'dev_server_expected'
                analysis['severity'] = 'low'
                analysis['confidence'] = 0.8
                analysis['recommendations'].append(f"Development server deviation: {dev_reason}")
                return analysis
            
            # Analyze value patterns
            unique_count = analysis['unique_values']
            server_count = analysis['server_count']
            
            if unique_count == 2 and server_count > 2:
                # Even split between two values
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1
                
                counts = list(value_counts.values())
                if abs(counts[0] - counts[1]) <= 1:
                    analysis['category'] = 'even_split_grouping'
                    analysis['severity'] = 'medium'
                    analysis['confidence'] = 0.7
                    analysis['recommendations'].append("Even split suggests intentional server grouping")
                else:
                    analysis['category'] = 'probable_misconfiguration'
                    analysis['severity'] = 'high'
                    analysis['confidence'] = 0.8
                    analysis['recommendations'].append("Uneven split suggests misconfiguration")
            
            elif unique_count > server_count * 0.7:
                # High variation - many different values
                analysis['category'] = 'high_inconsistency'
                analysis['severity'] = 'high'
                analysis['confidence'] = 0.9
                analysis['recommendations'].append("High variation indicates serious inconsistency")
            
            elif unique_count == 1:
                # All same value (shouldn't appear in deviations, but just in case)
                analysis['category'] = 'consistent'
                analysis['severity'] = 'low'
                analysis['confidence'] = 1.0
                analysis['recommendations'].append("All servers have same value")
            
            else:
                # Some variation, needs review
                analysis['category'] = 'needs_review'
                analysis['severity'] = 'medium'
                analysis['confidence'] = 0.6
                analysis['recommendations'].append("Moderate variation requires manual review")
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing deviation pattern: {e}")
            return {
                'key': key,
                'category': 'error',
                'severity': 'high',
                'error': str(e),
                'recommendations': ['Error during analysis - needs manual review']
            }
    
    def generate_report(self, output_path: Path) -> None:
        """
        Generate categorized deviation analysis report
        
        Args:
            output_path: Where to write the report
        """
        import json
        from datetime import datetime
        
        try:
            # Parse deviations data
            deviations = self.parse_deviations()
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'deviation_analysis',
                'source_file': str(self.deviations_file),
                'summary': {
                    'total_plugins': len(deviations),
                    'total_deviations': 0,
                    'by_category': {},
                    'by_severity': {'high': 0, 'medium': 0, 'low': 0}
                },
                'detailed_analysis': {},
                'high_priority_issues': []
            }
            
            # Analyze each deviation
            for plugin_name, files in deviations.items():
                report['detailed_analysis'][plugin_name] = {}
                
                for file_name, keys in files.items():
                    report['detailed_analysis'][plugin_name][file_name] = {}
                    
                    for key_name, server_values in keys.items():
                        analysis = self.analyze_deviation_pattern(key_name, server_values)
                        report['detailed_analysis'][plugin_name][file_name][key_name] = analysis
                        
                        # Update counters
                        report['summary']['total_deviations'] += 1
                        
                        category = analysis.get('category', 'unknown')
                        severity = analysis.get('severity', 'medium')
                        
                        report['summary']['by_category'][category] = report['summary']['by_category'].get(category, 0) + 1
                        report['summary']['by_severity'][severity] += 1
                        
                        # Add to high priority if needed
                        if severity == 'high':
                            report['high_priority_issues'].append({
                                'plugin': plugin_name,
                                'file': file_name,
                                'key': key_name,
                                'category': category,
                                'analysis': analysis,
                                'servers_affected': list(server_values.keys())
                            })
            
            # Write report
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, separators=(',', ': '), default=str)
            
            print(f"Deviation analysis report generated: {output_path}")
            print(f"Total deviations analyzed: {report['summary']['total_deviations']}")
            print(f"High priority issues: {report['summary']['by_severity']['high']}")
            
        except Exception as e:
            print(f"Error generating deviation report: {e}")
    
    def get_high_priority_issues(self) -> List[Dict[str, Any]]:
        """
        Get list of high-priority configuration issues
        
        Returns:
            List of issue dicts with plugin, file, key, affected servers
        """
        try:
            deviations = self.parse_deviations()
            high_priority_issues = []
            
            for plugin_name, files in deviations.items():
                for file_name, keys in files.items():
                    for key_name, server_values in keys.items():
                        analysis = self.analyze_deviation_pattern(key_name, server_values)
                        
                        # Only include high severity issues
                        if analysis.get('severity') == 'high':
                            issue = {
                                'plugin': plugin_name,
                                'file': file_name,
                                'key': key_name,
                                'category': analysis.get('category', 'unknown'),
                                'confidence': analysis.get('confidence', 0.0),
                                'affected_servers': list(server_values.keys()),
                                'server_values': server_values,
                                'recommendations': analysis.get('recommendations', []),
                                'priority_score': self._calculate_issue_priority(analysis, server_values)
                            }
                            high_priority_issues.append(issue)
            
            # Sort by priority score (highest first)
            high_priority_issues.sort(key=lambda x: x.get('priority_score', 0), reverse=True)
            
            return high_priority_issues
            
        except Exception as e:
            print(f"Error getting high priority issues: {e}")
            return []
    
    def _calculate_issue_priority(self, analysis: Dict[str, Any], server_values: Dict[str, str]) -> float:
        """Calculate priority score for an issue"""
        try:
            score = 0.0
            
            # Base score from confidence
            confidence = analysis.get('confidence', 0.5)
            score += confidence * 50
            
            # Server count impact
            server_count = len(server_values)
            score += min(server_count * 5, 50)  # Cap at 50
            
            # Category impact
            category = analysis.get('category', 'unknown')
            if category == 'high_inconsistency':
                score += 30
            elif category == 'probable_misconfiguration':
                score += 25
            elif category == 'needs_review':
                score += 15
            
            # Critical plugin boost
            plugin_keywords = ['security', 'auth', 'permission', 'database', 'economy']
            key_lower = analysis.get('key', '').lower()
            if any(keyword in key_lower for keyword in plugin_keywords):
                score += 20
            
            return score
            
        except Exception:
            return 0.0
