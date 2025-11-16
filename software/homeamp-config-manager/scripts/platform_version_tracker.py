#!/usr/bin/env python3
"""
Platform Version Tracker

Tracks server platform versions (Paper build, Fabric loader, NeoForge, etc.)
and Minecraft versions for each instance.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import json
import re
import requests
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_access import ConfigDatabase
from core.settings import settings
from amp_integration.instance_scanner import AMPInstanceScanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlatformVersionTracker:
    """Tracks platform and game versions for instances"""
    
    def __init__(self, db: ConfigDatabase, amp_base_dir: Path):
        self.db = db
        self.amp_base_dir = amp_base_dir
        self.scanner = AMPInstanceScanner(amp_base_dir)
    
    def scan_all_instances(self):
        """Scan all instances for platform versions"""
        instances = self.scanner.discover_instances()
        logger.info(f"Scanning {len(instances)} instances for platform versions...")
        
        for instance in instances:
            try:
                self.scan_instance(instance)
            except Exception as e:
                logger.error(f"Failed to scan {instance['name']}: {e}", exc_info=True)
    
    def scan_instance(self, instance: dict):
        """Scan a single instance for platform versions"""
        instance_id = instance['name']
        instance_path = Path(instance['path'])
        minecraft_dir = instance_path / 'Minecraft'
        
        if not minecraft_dir.exists():
            logger.warning(f"Minecraft directory not found for {instance_id}")
            return
        
        # Detect platform and versions
        platform_info = self._detect_platform(minecraft_dir)
        
        if not platform_info:
            logger.warning(f"Could not detect platform for {instance_id}")
            return
        
        # Get Minecraft version from server.properties
        mc_version = self._get_minecraft_version(minecraft_dir)
        
        logger.info(
            f"{instance_id}: {platform_info['platform']} {platform_info.get('platform_version', '?')} "
            f"(MC {mc_version or '?'})"
        )
        
        # Update database
        cursor = self.db.conn.cursor()
        
        # Update instances table
        cursor.execute("""
            UPDATE instances
            SET instance_type = %s,
                platform_version = %s,
                minecraft_version = %s,
                last_scanned = %s
            WHERE instance_id = %s
        """, (
            platform_info['platform'],
            platform_info.get('platform_version'),
            mc_version,
            datetime.now(),
            instance_id
        ))
        
        self.db.conn.commit()
    
    def _detect_platform(self, minecraft_dir: Path) -> Optional[Dict[str, Any]]:
        """Detect server platform and version"""
        
        # Check for Paper
        paper_jar = self._find_jar(minecraft_dir, 'paper')
        if paper_jar:
            version = self._extract_paper_version(paper_jar)
            return {
                'platform': 'paper',
                'platform_version': version,
                'jar_file': paper_jar.name
            }
        
        # Check for Fabric
        fabric_loader = minecraft_dir / 'fabric-server-launcher.properties'
        if fabric_loader.exists():
            version = self._extract_fabric_version(fabric_loader)
            return {
                'platform': 'fabric',
                'platform_version': version
            }
        
        # Check for NeoForge
        neoforge_jar = self._find_jar(minecraft_dir, 'neoforge')
        if neoforge_jar:
            version = self._extract_neoforge_version(neoforge_jar)
            return {
                'platform': 'neoforge',
                'platform_version': version,
                'jar_file': neoforge_jar.name
            }
        
        # Check for Forge (legacy)
        forge_jar = self._find_jar(minecraft_dir, 'forge')
        if forge_jar:
            version = self._extract_forge_version(forge_jar)
            return {
                'platform': 'forge',
                'platform_version': version,
                'jar_file': forge_jar.name
            }
        
        # Check for Geyser Standalone
        geyser_jar = self._find_jar(minecraft_dir, 'geyser')
        if geyser_jar:
            return {
                'platform': 'geyser',
                'jar_file': geyser_jar.name
            }
        
        # Check for Velocity
        velocity_jar = self._find_jar(minecraft_dir, 'velocity')
        if velocity_jar:
            version = self._extract_velocity_version(velocity_jar)
            return {
                'platform': 'velocity',
                'platform_version': version,
                'jar_file': velocity_jar.name
            }
        
        # Fallback: check for generic server.jar
        server_jar = minecraft_dir / 'server.jar'
        if server_jar.exists():
            return {
                'platform': 'vanilla',
                'jar_file': 'server.jar'
            }
        
        return None
    
    def _find_jar(self, directory: Path, keyword: str) -> Optional[Path]:
        """Find JAR file containing keyword"""
        for jar_file in directory.glob('*.jar'):
            if keyword.lower() in jar_file.name.lower():
                return jar_file
        return None
    
    def _extract_paper_version(self, jar_file: Path) -> Optional[str]:
        """Extract Paper build version from JAR filename"""
        # Format: paper-1.21.3-123.jar
        match = re.search(r'paper-[\d.]+-(\d+)\.jar', jar_file.name)
        if match:
            build_number = match.group(1)
            # Also extract MC version
            mc_match = re.search(r'paper-([\d.]+)-\d+\.jar', jar_file.name)
            if mc_match:
                mc_version = mc_match.group(1)
                return f"{mc_version}-{build_number}"
            return f"build-{build_number}"
        
        return None
    
    def _extract_fabric_version(self, properties_file: Path) -> Optional[str]:
        """Extract Fabric loader version from properties"""
        try:
            with open(properties_file, 'r') as f:
                for line in f:
                    if line.startswith('serverVersion='):
                        return line.split('=', 1)[1].strip()
        except:
            pass
        return None
    
    def _extract_neoforge_version(self, jar_file: Path) -> Optional[str]:
        """Extract NeoForge version from JAR filename"""
        # Format: neoforge-21.3.5-beta.jar or similar
        match = re.search(r'neoforge-([\d.]+(?:-[a-z]+)?)', jar_file.name, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _extract_forge_version(self, jar_file: Path) -> Optional[str]:
        """Extract Forge version from JAR filename"""
        # Format: forge-1.20.1-47.3.0.jar
        match = re.search(r'forge-([\d.]+-[\d.]+)', jar_file.name, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _extract_velocity_version(self, jar_file: Path) -> Optional[str]:
        """Extract Velocity version from JAR filename"""
        # Format: velocity-3.3.0-SNAPSHOT-392.jar
        match = re.search(r'velocity-([\d.]+-[\w-]+)', jar_file.name, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def _get_minecraft_version(self, minecraft_dir: Path) -> Optional[str]:
        """Get Minecraft version from server.properties"""
        props_file = minecraft_dir / 'server.properties'
        
        if not props_file.exists():
            return None
        
        try:
            # Try to get from version.json (for newer servers)
            version_json = minecraft_dir / 'version.json'
            if version_json.exists():
                with open(version_json, 'r') as f:
                    data = json.load(f)
                    return data.get('id', data.get('name'))
            
            # Fallback: parse from JAR filename or properties
            with open(props_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('version='):
                        return line.split('=', 1)[1].strip()
            
            # Last resort: try to extract from Paper JAR name
            paper_jar = self._find_jar(minecraft_dir, 'paper')
            if paper_jar:
                match = re.search(r'paper-([\d.]+)-\d+\.jar', paper_jar.name)
                if match:
                    return match.group(1)
        
        except Exception as e:
            logger.warning(f"Failed to get MC version: {e}")
        
        return None
    
    def check_platform_updates(self):
        """Check for platform updates from official sources"""
        logger.info("Checking for platform updates...")
        
        # Check Paper builds
        self._check_paper_updates()
        
        # Check Fabric loader
        self._check_fabric_updates()
    
    def _check_paper_updates(self):
        """Check for latest Paper builds"""
        try:
            # Get list of Minecraft versions
            response = requests.get('https://api.papermc.io/v2/projects/paper', timeout=10)
            if response.status_code != 200:
                return
            
            data = response.json()
            versions = data.get('versions', [])
            
            if not versions:
                return
            
            latest_mc_version = versions[-1]
            
            # Get latest build for this version
            builds_response = requests.get(
                f'https://api.papermc.io/v2/projects/paper/versions/{latest_mc_version}',
                timeout=10
            )
            
            if builds_response.status_code != 200:
                return
            
            builds_data = builds_response.json()
            builds = builds_data.get('builds', [])
            
            if builds:
                latest_build = builds[-1]
                logger.info(f"Latest Paper: {latest_mc_version}-{latest_build}")
        
        except Exception as e:
            logger.error(f"Failed to check Paper updates: {e}")
    
    def _check_fabric_updates(self):
        """Check for latest Fabric loader"""
        try:
            response = requests.get(
                'https://meta.fabricmc.net/v2/versions/loader',
                timeout=10
            )
            
            if response.status_code != 200:
                return
            
            loaders = response.json()
            
            if loaders:
                stable_loaders = [l for l in loaders if l.get('stable', False)]
                if stable_loaders:
                    latest_loader = stable_loaders[0]['version']
                    logger.info(f"Latest Fabric Loader: {latest_loader}")
        
        except Exception as e:
            logger.error(f"Failed to check Fabric updates: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Platform version tracker')
    parser.add_argument('--amp-dir', default='/home/amp/.ampdata/instances',
                       help='AMP instances directory')
    parser.add_argument('--check-updates', action='store_true',
                       help='Check for platform updates')
    
    args = parser.parse_args()
    
    # Connect to database
    db = ConfigDatabase(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    db.connect()
    
    try:
        tracker = PlatformVersionTracker(db, Path(args.amp_dir))
        
        if args.check_updates:
            tracker.check_platform_updates()
        else:
            tracker.scan_all_instances()
    
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
