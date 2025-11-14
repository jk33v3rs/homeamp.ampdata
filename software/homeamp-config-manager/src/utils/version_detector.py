"""
Version Detection System

Detects plugin versions from filenames and JAR files, with nightly build tracking
for unversioned or SNAPSHOT builds.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PluginVersion:
    """Represents a plugin's version information"""
    plugin_name: str
    version: str
    is_snapshot: bool
    is_nightly: bool
    build_number: Optional[int]
    file_path: Path
    file_modified: datetime
    
    def __str__(self):
        return f"{self.plugin_name}: {self.version}"
    
    def to_dict(self):
        return {
            'plugin_name': self.plugin_name,
            'version': self.version,
            'is_snapshot': self.is_snapshot,
            'is_nightly': self.is_nightly,
            'build_number': self.build_number,
            'file_path': str(self.file_path),
            'file_modified': self.file_modified.isoformat()
        }


class VersionDetector:
    """Detects plugin versions from filenames and generates nightly identifiers"""
    
    # Common version patterns in plugin filenames
    VERSION_PATTERNS = [
        # LuckPerms-Bukkit-5.4.145.jar
        r'-([\d]+\.[\d]+\.[\d]+(?:\.[\d]+)?)',
        # Pl3xMap-1.21.4-525.jar
        r'-([\d]+\.[\d]+\.[\d]+-[\d]+)',
        # CMI-9.7.14.2.jar
        r'-([\d]+\.[\d]+\.[\d]+\.[\d]+)',
        # Plugin-v1.2.3.jar
        r'-v([\d]+\.[\d]+\.[\d]+)',
        # Plugin-1.0-SNAPSHOT.jar
        r'-([\d]+\.[\d]+(?:\.[\d]+)?-SNAPSHOT)',
        # Plugin-build-3847.jar
        r'-build-(\d+)',
        # Plugin-nightly-20251114.jar
        r'-nightly-([\d]+)',
    ]
    
    def __init__(self):
        self.nightly_counter = {}  # Track nightly builds per day
    
    def extract_version_from_filename(self, filename: str) -> Optional[str]:
        """
        Extract version from plugin filename
        
        Args:
            filename: Plugin JAR filename
            
        Returns:
            Version string if found, None otherwise
        """
        # Try each pattern
        for pattern in self.VERSION_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def extract_plugin_name(self, filename: str) -> str:
        """
        Extract plugin name from filename (before version/extension)
        
        Args:
            filename: Plugin JAR filename
            
        Returns:
            Plugin name
        """
        # Remove .jar extension
        name = filename.replace('.jar', '')
        
        # Try to find version and split on it
        for pattern in self.VERSION_PATTERNS:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                # Take everything before the version
                return name[:match.start()].rstrip('-_')
        
        # No version found, return whole name
        return name
    
    def generate_nightly_version(self, file_path: Path) -> Tuple[str, int]:
        """
        Generate nightly build identifier from file modification time
        
        Args:
            file_path: Path to plugin JAR file
            
        Returns:
            Tuple of (nightly_version_string, build_number)
        """
        # Get file modification time
        mtime = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mtime)
        
        # Create date key for tracking daily builds
        date_key = mod_date.strftime('%Y%m%d')
        
        # Increment counter for this date
        if date_key not in self.nightly_counter:
            self.nightly_counter[date_key] = 0
        self.nightly_counter[date_key] += 1
        
        build_num = self.nightly_counter[date_key]
        
        # Format: nightly-YYYYMMDD-NNN
        nightly_version = f"nightly-{date_key}-{build_num:03d}"
        
        return nightly_version, build_num
    
    def is_snapshot_version(self, version: str) -> bool:
        """Check if version is a SNAPSHOT build"""
        return 'SNAPSHOT' in version.upper()
    
    def detect_version(self, file_path: Path) -> PluginVersion:
        """
        Detect version information from a plugin JAR file
        
        Args:
            file_path: Path to plugin JAR file
            
        Returns:
            PluginVersion object with detected information
        """
        filename = file_path.name
        plugin_name = self.extract_plugin_name(filename)
        version = self.extract_version_from_filename(filename)
        
        # Get file modification time
        mtime = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mtime)
        
        is_snapshot = False
        is_nightly = False
        build_number = None
        
        if version:
            is_snapshot = self.is_snapshot_version(version)
            
            # If it's a SNAPSHOT, append nightly identifier
            if is_snapshot:
                nightly_version, build_number = self.generate_nightly_version(file_path)
                version = f"{version}-{nightly_version}"
                is_nightly = True
        else:
            # No version found, generate nightly identifier
            version, build_number = self.generate_nightly_version(file_path)
            is_nightly = True
        
        return PluginVersion(
            plugin_name=plugin_name,
            version=version,
            is_snapshot=is_snapshot,
            is_nightly=is_nightly,
            build_number=build_number,
            file_path=file_path,
            file_modified=mod_date
        )
    
    def scan_plugins_directory(self, plugins_dir: Path) -> List[PluginVersion]:
        """
        Scan a plugins directory and detect all plugin versions
        
        Args:
            plugins_dir: Path to plugins directory
            
        Returns:
            List of PluginVersion objects
        """
        if not plugins_dir.exists():
            logger.warning(f"Plugins directory does not exist: {plugins_dir}")
            return []
        
        versions = []
        
        for jar_file in sorted(plugins_dir.glob("*.jar")):
            try:
                plugin_version = self.detect_version(jar_file)
                versions.append(plugin_version)
                logger.debug(f"Detected: {plugin_version}")
            except Exception as e:
                logger.error(f"Error detecting version for {jar_file}: {e}")
        
        return versions
    
    def scan_all_instances(self, base_path: Path) -> Dict[str, List[PluginVersion]]:
        """
        Scan all AMP instances and detect plugin versions
        
        Args:
            base_path: Base path containing instance directories
            
        Returns:
            Dictionary mapping instance_id -> list of PluginVersion objects
        """
        instances = {}
        
        # Scan utildata directories for instance snapshots
        for platform in ['HETZNER', 'OVH']:
            platform_path = base_path / 'utildata' / platform
            
            if not platform_path.exists():
                continue
            
            for instance_dir in platform_path.iterdir():
                if not instance_dir.is_dir():
                    continue
                
                instance_id = instance_dir.name
                plugins_dir = instance_dir / 'plugins'
                
                if plugins_dir.exists():
                    versions = self.scan_plugins_directory(plugins_dir)
                    if versions:
                        instances[instance_id] = versions
                        logger.info(f"Scanned {instance_id}: {len(versions)} plugins")
        
        return instances
    
    def generate_version_report(self, instances: Dict[str, List[PluginVersion]]) -> Dict:
        """
        Generate comprehensive version report across all instances
        
        Args:
            instances: Dictionary of instance_id -> plugin versions
            
        Returns:
            Report dictionary with aggregated version information
        """
        report = {
            'total_instances': len(instances),
            'total_plugins': 0,
            'snapshot_builds': 0,
            'nightly_builds': 0,
            'plugins_by_name': {},
            'instances': {}
        }
        
        # Aggregate by plugin name
        for instance_id, versions in instances.items():
            instance_plugins = []
            
            for pv in versions:
                report['total_plugins'] += 1
                if pv.is_snapshot:
                    report['snapshot_builds'] += 1
                if pv.is_nightly:
                    report['nightly_builds'] += 1
                
                # Track versions by plugin name
                if pv.plugin_name not in report['plugins_by_name']:
                    report['plugins_by_name'][pv.plugin_name] = {
                        'versions': set(),
                        'instances': set()
                    }
                
                report['plugins_by_name'][pv.plugin_name]['versions'].add(pv.version)
                report['plugins_by_name'][pv.plugin_name]['instances'].add(instance_id)
                
                instance_plugins.append(pv.to_dict())
            
            report['instances'][instance_id] = {
                'plugin_count': len(versions),
                'plugins': instance_plugins
            }
        
        # Convert sets to lists for JSON serialization
        for plugin_name, data in report['plugins_by_name'].items():
            data['versions'] = sorted(list(data['versions']))
            data['instances'] = sorted(list(data['instances']))
            data['version_count'] = len(data['versions'])
        
        return report


def main():
    """CLI for testing version detection"""
    import sys
    import json
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python version_detector.py <path_to_plugins_or_base_dir>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    detector = VersionDetector()
    
    if path.is_dir() and (path / 'utildata').exists():
        # Scan all instances
        print(f"Scanning all instances in: {path}")
        instances = detector.scan_all_instances(path)
        report = detector.generate_version_report(instances)
        
        print(f"\n=== Version Detection Report ===")
        print(f"Total Instances: {report['total_instances']}")
        print(f"Total Plugins: {report['total_plugins']}")
        print(f"Snapshot Builds: {report['snapshot_builds']}")
        print(f"Nightly Builds: {report['nightly_builds']}")
        
        print(f"\n=== Plugins ({len(report['plugins_by_name'])} unique) ===")
        for plugin_name, data in sorted(report['plugins_by_name'].items()):
            print(f"\n{plugin_name}:")
            print(f"  Versions: {data['version_count']}")
            for version in data['versions']:
                print(f"    - {version}")
            print(f"  Instances: {', '.join(data['instances'])}")
        
        # Save full report
        report_file = path / 'version_detection_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nFull report saved to: {report_file}")
        
    elif path.is_dir():
        # Scan single plugins directory
        print(f"Scanning plugins directory: {path}")
        versions = detector.scan_plugins_directory(path)
        
        print(f"\n=== Detected Versions ({len(versions)} plugins) ===")
        for pv in versions:
            flags = []
            if pv.is_snapshot:
                flags.append("SNAPSHOT")
            if pv.is_nightly:
                flags.append("NIGHTLY")
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            print(f"{pv.plugin_name}: {pv.version}{flag_str}")
    else:
        print(f"Error: {path} is not a valid directory")
        sys.exit(1)


if __name__ == '__main__':
    main()
