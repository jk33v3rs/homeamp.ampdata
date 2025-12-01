"""
Baseline Configuration Parser

Parses universal config baseline files (markdown format) into structured data.
Extracts expected key-value pairs from plugin baseline configs.
"""

import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging
import zipfile
import tempfile
import shutil

logger = logging.getLogger(__name__)


class BaselineParser:
    """Parse baseline configuration markdown files"""
    
    def __init__(self, baselines_dir: str = "data/baselines/universal_configs"):
        self.baselines_dir = Path(baselines_dir)
        self.temp_dir = None
        self.using_zip = False
        
        # Check if it's a zip file path
        zip_path = Path(str(baselines_dir) + ".zip")
        if zip_path.exists():
            # Extract zip to temp directory
            self.temp_dir = tempfile.mkdtemp(prefix="baselines_")
            logger.info(f"Extracting baselines from {zip_path} to {self.temp_dir}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            self.baselines_dir = Path(self.temp_dir)
            self.using_zip = True
        elif not self.baselines_dir.exists():
            # Try absolute path from project root
            project_root = Path(__file__).parent.parent.parent
            self.baselines_dir = project_root / baselines_dir
            
            # Check for zip at absolute path
            zip_path = Path(str(self.baselines_dir) + ".zip")
            if zip_path.exists():
                self.temp_dir = tempfile.mkdtemp(prefix="baselines_")
                logger.info(f"Extracting baselines from {zip_path} to {self.temp_dir}")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(self.temp_dir)
                self.baselines_dir = Path(self.temp_dir)
                self.using_zip = True
            elif not self.baselines_dir.exists():
                raise FileNotFoundError(f"Baselines directory or zip not found: {baselines_dir}")
    
    def __del__(self):
        """Clean up temp directory if using zip"""
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir {self.temp_dir}: {e}")
    
    def list_plugins(self) -> List[str]:
        """Get list of plugins with baseline configs"""
        plugins = []
        # Search in current dir and subdirs
        for file in self.baselines_dir.rglob("*_universal_config.md"):
            plugin_name = file.stem.replace("_universal_config", "")
            plugins.append(plugin_name)
        return sorted(plugins)
    
    def parse_plugin_baseline(self, plugin_name: str) -> Dict[str, Any]:
        """
        Parse baseline config for a plugin
        
        Returns dict of config keys to expected values
        """
        # Search recursively for the baseline file
        baseline_files = list(self.baselines_dir.rglob(f"{plugin_name}_universal_config.md"))
        
        if not baseline_files:
            logger.warning(f"No baseline found for {plugin_name}")
            return {}
        
        baseline_file = baseline_files[0]
        with open(baseline_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self._extract_config_values(content)
    
    def _extract_config_values(self, markdown: str) -> Dict[str, Any]:
        """
        Extract config key-value pairs from markdown
        
        Format: `key` = value
        or: `nested.key.path` = value
        """
        configs = {}
        
        # Pattern: `configKey` = value
        # Handles: strings ("value"), numbers, booleans, null
        pattern = r'`([^`]+)`\s*=\s*(.+?)(?:\n|$)'
        
        for match in re.finditer(pattern, markdown):
            key = match.group(1)
            value_str = match.group(2).strip()
            
            # Parse value type
            value = self._parse_value(value_str)
            configs[key] = value
        
        return configs
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse string value into appropriate Python type"""
        value_str = value_str.strip()
        
        # Remove trailing comments
        if '#' in value_str:
            value_str = value_str.split('#')[0].strip()
        
        # String (quoted)
        if value_str.startswith('"') and value_str.endswith('"'):
            return value_str[1:-1]
        if value_str.startswith("'") and value_str.endswith("'"):
            return value_str[1:-1]
        
        # Boolean
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # Null/None
        if value_str.lower() in ('null', 'none', '~'):
            return None
        
        # Number (int or float)
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass
        
        # List (simple comma-separated)
        if value_str.startswith('[') and value_str.endswith(']'):
            items_str = value_str[1:-1]
            if not items_str.strip():
                return []
            items = [self._parse_value(item.strip()) for item in items_str.split(',')]
            return items
        
        # Default: treat as unquoted string
        return value_str
    
    def get_all_baselines(self) -> Dict[str, Dict[str, Any]]:
        """Get all plugin baselines in one dict"""
        all_baselines = {}
        
        for plugin in self.list_plugins():
            all_baselines[plugin] = self.parse_plugin_baseline(plugin)
        
        return all_baselines
    
    def find_config_file_for_key(self, plugin_name: str, config_key: str) -> Optional[str]:
        """
        Try to infer which config file a key belongs to
        
        For now, assumes config.yml for most keys unless we detect special patterns
        """
        # Special config files we know about
        if 'message' in config_key.lower() or 'msg' in config_key.lower():
            return 'messages.yml'
        elif 'lang' in config_key.lower():
            return 'language.yml'
        elif 'command' in config_key.lower():
            return 'commands.yml'
        else:
            return 'config.yml'
    
    def get_nested_key_path(self, key: str) -> List[str]:
        """
        Convert flat key to nested path
        
        Example: "database.mysql.host" -> ["database", "mysql", "host"]
        """
        return key.split('.')


class DriftDetector:
    """Detect configuration drift between live configs and baselines"""
    
    def __init__(self, parser: BaselineParser):
        self.parser = parser
    
    def detect_drift(self, plugin_name: str, instance_id: str, 
                     live_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Compare live config against baseline and detect drift
        
        Returns list of drift entries with:
        - key: config key path
        - baseline_value: expected value
        - actual_value: current value
        - drift_type: 'missing', 'extra', 'different'
        """
        baseline = self.parser.parse_plugin_baseline(plugin_name)
        drifts = []
        
        # Check for missing or different values
        for key, expected_value in baseline.items():
            actual_value = self._get_nested_value(live_config, key)
            
            if actual_value is None and key not in self._flatten_config(live_config):
                drifts.append({
                    'plugin': plugin_name,
                    'instance_id': instance_id,
                    'key': key,
                    'config_file': self.parser.find_config_file_for_key(plugin_name, key),
                    'baseline_value': expected_value,
                    'actual_value': None,
                    'drift_type': 'missing',
                    'severity': 'warning'
                })
            elif actual_value != expected_value:
                # Check if it's a variable substitution (expected drift)
                if isinstance(expected_value, str) and '{{' in expected_value:
                    drift_type = 'variable'
                    severity = 'info'
                else:
                    drift_type = 'different'
                    severity = 'error'
                
                drifts.append({
                    'plugin': plugin_name,
                    'instance_id': instance_id,
                    'key': key,
                    'config_file': self.parser.find_config_file_for_key(plugin_name, key),
                    'baseline_value': expected_value,
                    'actual_value': actual_value,
                    'drift_type': drift_type,
                    'severity': severity
                })
        
        # Check for extra keys not in baseline
        flat_live = self._flatten_config(live_config)
        for key in flat_live:
            if key not in baseline:
                drifts.append({
                    'plugin': plugin_name,
                    'instance_id': instance_id,
                    'key': key,
                    'config_file': self.parser.find_config_file_for_key(plugin_name, key),
                    'baseline_value': None,
                    'actual_value': flat_live[key],
                    'drift_type': 'extra',
                    'severity': 'info'
                })
        
        return drifts
    
    def _get_nested_value(self, config: Dict, key_path: str) -> Any:
        """Get value from nested dict using dot notation"""
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if not isinstance(value, dict):
                return None
            value = value.get(key)
            if value is None:
                return None
        
        return value
    
    def _flatten_config(self, config: Dict, prefix: str = '') -> Dict[str, Any]:
        """Flatten nested config dict into dot notation keys"""
        flat = {}
        
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flat.update(self._flatten_config(value, full_key))
            else:
                flat[full_key] = value
        
        return flat
    
    def get_drift_summary(self, drifts: List[Dict]) -> Dict[str, int]:
        """Get summary counts of drift types"""
        summary = {
            'total': len(drifts),
            'missing': sum(1 for d in drifts if d['drift_type'] == 'missing'),
            'different': sum(1 for d in drifts if d['drift_type'] == 'different'),
            'extra': sum(1 for d in drifts if d['drift_type'] == 'extra'),
            'variable': sum(1 for d in drifts if d['drift_type'] == 'variable'),
            'errors': sum(1 for d in drifts if d['severity'] == 'error'),
            'warnings': sum(1 for d in drifts if d['severity'] == 'warning'),
        }
        return summary


if __name__ == "__main__":
    # Test the parser
    parser = BaselineParser()
    
    print("Available plugins with baselines:")
    plugins = parser.list_plugins()
    print(f"  Found {len(plugins)} plugins")
    
    # Test parsing EliteMobs
    print("\nParsing EliteMobs baseline:")
    elitemobs_config = parser.parse_plugin_baseline("EliteMobs")
    print(f"  Found {len(elitemobs_config)} config keys")
    
    # Show first few entries
    for i, (key, value) in enumerate(list(elitemobs_config.items())[:5]):
        print(f"    {key} = {value} ({type(value).__name__})")
    
    # Test drift detection (simulated)
    print("\nTesting drift detection:")
    detector = DriftDetector(parser)
    
    # Simulate a live config with some drift
    live_config = {
        'alwaysShowEliteMobNameTags': True,  # Different from baseline (false)
        'language': 'english',  # Same as baseline
        'setupDoneV4': True,  # Same
        'custom_new_key': 'value'  # Not in baseline
    }
    
    drifts = detector.detect_drift("EliteMobs", "TEST01", live_config)
    print(f"  Detected {len(drifts)} drift entries")
    
    summary = detector.get_drift_summary(drifts)
    print(f"  Summary: {summary}")
