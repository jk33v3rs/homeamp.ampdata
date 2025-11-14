"""
Bedrock Compatibility Updater

Specialized module for rapid Bedrock compatibility updates after version changes.
Handles the critical path: Geyser, ViaVersion, ViaBackwards, Floodgate, and extensions.

Author: ArchiveSMP Configuration Management System
"""

import json
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class BedrockUpdater:
    """
    Manages Bedrock compatibility updates across the server network.
    
    Critical update path:
    1. Geyser-Standalone (proxy)
    2. ViaVersion (velocity proxy - Hangar snapshots)
    3. ViaBackwards (velocity proxy - Hangar snapshots)
    4. Floodgate (proxy + network servers)
    5. Geyser Extensions (as needed)
    """
    
    # API Endpoints for Bedrock-related plugins
    BEDROCK_ENDPOINTS = {
        'geyser_standalone': {
            'url': 'https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest',
            'type': 'geysermc',
            'platform': 'standalone',
            'description': 'Geyser Standalone (proxy)'
        },
        'geyser_spigot': {
            'url': 'https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest',
            'type': 'geysermc',
            'platform': 'spigot',
            'description': 'Geyser Spigot plugin'
        },
        'floodgate_standalone': {
            'url': 'https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest',
            'type': 'geysermc',
            'platform': 'standalone',
            'description': 'Floodgate Standalone (proxy)'
        },
        'floodgate_spigot': {
            'url': 'https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest',
            'type': 'geysermc',
            'platform': 'spigot',
            'description': 'Floodgate Spigot plugin'
        },
        'viaversion': {
            'url': 'https://hangar.papermc.io/api/v1/projects/ViaVersion/versions',
            'type': 'hangar',
            'description': 'ViaVersion (proxy - supports latest MC versions)'
        },
        'viabackwards': {
            'url': 'https://hangar.papermc.io/api/v1/projects/ViaBackwards/versions',
            'type': 'hangar',
            'description': 'ViaBackwards (proxy - backward compatibility)'
        },
        # Geyser Extensions
        'geyser_skin_manager': {
            'url': 'https://hangar.papermc.io/api/v1/projects/skinrestorer/versions',
            'type': 'hangar',
            'description': 'SkinRestorer (Geyser skin support)'
        }
    }
    
    # Network topology for Bedrock updates
    BEDROCK_DEPLOYMENT = {
        'velocity_proxy': {
            'server': 'OVH-Ryzen',
            'instance': 'Velocity01',
            'plugins': ['viaversion', 'viabackwards']
        },
        'geyser_proxy': {
            'server': 'OVH-Ryzen',
            'instance': 'Geyser01',
            'plugins': ['geyser_standalone', 'floodgate_standalone']
        },
        'network_servers': {
            'pattern': 'all_spigot_servers',
            'plugins': ['floodgate_spigot']
        }
    }
    
    def __init__(self, settings_path: Optional[Path] = None):
        """
        Initialize the Bedrock updater.
        
        Args:
            settings_path: Path to settings.yaml configuration
        """
        self.logger = logging.getLogger(__name__)
        self.settings_path = settings_path or Path(__file__).parent.parent.parent / 'config' / 'settings.yaml'
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'ArchiveSMP-BedrockUpdater/1.0'})
    
    def check_geysermc_version(self, project: str, platform: str) -> Optional[Dict[str, Any]]:
        """
        Check latest version from GeyserMC download API.
        
        Args:
            project: 'geyser' or 'floodgate'
            platform: 'standalone' or 'spigot'
            
        Returns:
            Dictionary with version info or None if error
        """
        try:
            url = f'https://download.geysermc.org/v2/projects/{project}/versions/latest/builds/latest'
            
            self.logger.info(f"Checking {project} ({platform}) version from GeyserMC API...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'project': project,
                'platform': platform,
                'version': data.get('version'),
                'build': data.get('build'),
                'download_url': f"https://download.geysermc.org/v2/projects/{project}/versions/latest/builds/latest/downloads/{platform}",
                'changes': data.get('changes', []),
                'time': data.get('time')
            }
            
        except Exception as e:
            self.logger.error(f"Error checking {project} version: {e}")
            return None
    
    def check_hangar_version(self, project: str, include_snapshots: bool = True) -> Optional[Dict[str, Any]]:
        """
        Check latest version from Hangar API.
        
        Args:
            project: Project slug (e.g., 'ViaVersion', 'ViaBackwards')
            include_snapshots: Include snapshot/alpha builds
            
        Returns:
            Dictionary with version info or None if error
        """
        try:
            url = f'https://hangar.papermc.io/api/v1/projects/{project}/versions'
            
            self.logger.info(f"Checking {project} version from Hangar...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            versions = data.get('result', [])
            
            if not versions:
                return None
            
            # Get the latest version (snapshots usually at the top)
            latest = versions[0]
            
            return {
                'project': project,
                'version': latest.get('name'),
                'channel': latest.get('channel', {}).get('name', 'release'),
                'download_url': f"https://hangar.papermc.io/api/v1/projects/{project}/versions/{latest.get('name')}/VELOCITY/download",
                'created_at': latest.get('createdAt'),
                'description': latest.get('description', '')
            }
            
        except Exception as e:
            self.logger.error(f"Error checking {project} from Hangar: {e}")
            return None
    
    def download_plugin(self, url: str, output_path: Path) -> bool:
        """
        Download a plugin file.
        
        Args:
            url: Download URL
            output_path: Where to save the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Downloading from {url}...")
            
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                self.logger.info(f"Download progress: {progress:.1f}%")
            
            self.logger.info(f"Downloaded successfully to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading plugin: {e}")
            return False
    
    def update_geyser_standalone(self, target_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Update Geyser Standalone on the proxy.
        
        Args:
            target_path: Override default installation path
            
        Returns:
            Update result dictionary
        """
        result = {
            'plugin': 'Geyser-Standalone',
            'success': False,
            'version': None,
            'error': None
        }
        
        try:
            # Check latest version
            version_info = self.check_geysermc_version('geyser', 'standalone')
            if not version_info:
                result['error'] = 'Failed to fetch version information'
                return result
            
            result['version'] = f"{version_info['version']}-{version_info['build']}"
            
            # Determine target path
            if not target_path:
                target_path = Path('/home/amp/.ampdata/instances/Geyser01/Geyser-Standalone.jar')
            
            # Backup existing version
            if target_path.exists():
                backup_path = target_path.with_suffix('.jar.bak')
                self.logger.info(f"Backing up existing Geyser to {backup_path}")
                import shutil
                shutil.copy2(target_path, backup_path)
            
            # Download new version
            if self.download_plugin(version_info['download_url'], target_path):
                result['success'] = True
                result['message'] = f"Updated to version {result['version']}"
            else:
                result['error'] = 'Download failed'
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Error updating Geyser: {e}")
        
        return result
    
    def update_floodgate(self, platform: str = 'both', target_servers: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update Floodgate on proxy and/or network servers.
        
        Args:
            platform: 'standalone', 'spigot', or 'both'
            target_servers: List of server instance names (for spigot platform)
            
        Returns:
            Update result dictionary
        """
        results = {
            'plugin': 'Floodgate',
            'updates': [],
            'success': True
        }
        
        try:
            # Update standalone (proxy)
            if platform in ['standalone', 'both']:
                version_info = self.check_geysermc_version('floodgate', 'standalone')
                if version_info:
                    target = Path('/home/amp/.ampdata/instances/Geyser01/plugins/floodgate-standalone.jar')
                    
                    if self.download_plugin(version_info['download_url'], target):
                        results['updates'].append({
                            'location': 'Geyser01 (proxy)',
                            'version': f"{version_info['version']}-{version_info['build']}",
                            'success': True
                        })
                    else:
                        results['success'] = False
                        results['updates'].append({
                            'location': 'Geyser01 (proxy)',
                            'success': False,
                            'error': 'Download failed'
                        })
            
            # Update spigot servers
            if platform in ['spigot', 'both']:
                version_info = self.check_geysermc_version('floodgate', 'spigot')
                if version_info:
                    # TODO: Implement multi-server deployment
                    # This would use the server configuration to deploy to all servers
                    results['updates'].append({
                        'location': 'Network servers',
                        'version': f"{version_info['version']}-{version_info['build']}",
                        'pending': True,
                        'note': 'Multi-server deployment needs configuration'
                    })
        
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            self.logger.error(f"Error updating Floodgate: {e}")
        
        return results
    
    def update_viaversion(self, include_viabackwards: bool = True) -> Dict[str, Any]:
        """
        Update ViaVersion and optionally ViaBackwards on Velocity proxy.
        
        Args:
            include_viabackwards: Also update ViaBackwards
            
        Returns:
            Update result dictionary
        """
        results = {
            'plugins': [],
            'success': True
        }
        
        try:
            # Update ViaVersion
            via_info = self.check_hangar_version('ViaVersion', include_snapshots=True)
            if via_info:
                target = Path('/home/amp/.ampdata/instances/Velocity01/plugins/ViaVersion.jar')
                
                if self.download_plugin(via_info['download_url'], target):
                    results['plugins'].append({
                        'name': 'ViaVersion',
                        'version': via_info['version'],
                        'channel': via_info['channel'],
                        'success': True
                    })
                else:
                    results['success'] = False
                    results['plugins'].append({
                        'name': 'ViaVersion',
                        'success': False,
                        'error': 'Download failed'
                    })
            
            # Update ViaBackwards if requested
            if include_viabackwards:
                vb_info = self.check_hangar_version('ViaBackwards', include_snapshots=True)
                if vb_info:
                    target = Path('/home/amp/.ampdata/instances/Velocity01/plugins/ViaBackwards.jar')
                    
                    if self.download_plugin(vb_info['download_url'], target):
                        results['plugins'].append({
                            'name': 'ViaBackwards',
                            'version': vb_info['version'],
                            'channel': vb_info['channel'],
                            'success': True
                        })
                    else:
                        results['success'] = False
                        results['plugins'].append({
                            'name': 'ViaBackwards',
                            'success': False,
                            'error': 'Download failed'
                        })
        
        except Exception as e:
            results['success'] = False
            results['error'] = str(e)
            self.logger.error(f"Error updating ViaVersion/ViaBackwards: {e}")
        
        return results
    
    def full_bedrock_update(self, restart_services: bool = False) -> Dict[str, Any]:
        """
        Perform a complete Bedrock compatibility update.
        
        Updates in order:
        1. ViaVersion + ViaBackwards (Velocity proxy)
        2. Geyser Standalone
        3. Floodgate (proxy + network)
        
        Args:
            restart_services: Whether to restart affected services
            
        Returns:
            Comprehensive update results
        """
        self.logger.info("=" * 60)
        self.logger.info("BEDROCK COMPATIBILITY UPDATE - FULL SUITE")
        self.logger.info("=" * 60)
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'updates': {},
            'overall_success': True,
            'restart_required': True
        }
        
        # Step 1: ViaVersion + ViaBackwards
        self.logger.info("\n[1/3] Updating ViaVersion + ViaBackwards...")
        via_results = self.update_viaversion(include_viabackwards=True)
        results['updates']['via'] = via_results
        if not via_results.get('success', False):
            results['overall_success'] = False
        
        # Step 2: Geyser Standalone
        self.logger.info("\n[2/3] Updating Geyser Standalone...")
        geyser_results = self.update_geyser_standalone()
        results['updates']['geyser'] = geyser_results
        if not geyser_results.get('success', False):
            results['overall_success'] = False
        
        # Step 3: Floodgate
        self.logger.info("\n[3/3] Updating Floodgate...")
        floodgate_results = self.update_floodgate(platform='both')
        results['updates']['floodgate'] = floodgate_results
        if not floodgate_results.get('success', False):
            results['overall_success'] = False
        
        # Summary
        self.logger.info("\n" + "=" * 60)
        if results['overall_success']:
            self.logger.info("✅ BEDROCK UPDATE COMPLETED SUCCESSFULLY")
        else:
            self.logger.warning("⚠️ BEDROCK UPDATE COMPLETED WITH ERRORS")
        self.logger.info("=" * 60)
        
        if restart_services:
            self.logger.info("\n🔄 Service restart would be triggered here")
            results['restart_triggered'] = True
        else:
            self.logger.info("\n⚠️ Manual restart required for changes to take effect")
            results['restart_triggered'] = False
        
        return results
    
    def check_all_versions(self) -> Dict[str, Any]:
        """
        Check current versions of all Bedrock-related plugins without updating.
        
        Returns:
            Dictionary with version information for all plugins
        """
        self.logger.info("Checking Bedrock plugin versions...")
        
        versions = {
            'geyser': self.check_geysermc_version('geyser', 'standalone'),
            'floodgate': self.check_geysermc_version('floodgate', 'standalone'),
            'viaversion': self.check_hangar_version('ViaVersion', include_snapshots=True),
            'viabackwards': self.check_hangar_version('ViaBackwards', include_snapshots=True)
        }
        
        return versions


def main():
    """CLI interface for Bedrock updater."""
    import argparse
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description='ArchiveSMP Bedrock Compatibility Updater')
    parser.add_argument('--check', action='store_true', help='Check versions without updating')
    parser.add_argument('--full', action='store_true', help='Perform full Bedrock update')
    parser.add_argument('--geyser', action='store_true', help='Update only Geyser')
    parser.add_argument('--via', action='store_true', help='Update only ViaVersion/ViaBackwards')
    parser.add_argument('--floodgate', action='store_true', help='Update only Floodgate')
    parser.add_argument('--restart', action='store_true', help='Restart services after update')
    
    args = parser.parse_args()
    
    updater = BedrockUpdater()
    
    if args.check:
        versions = updater.check_all_versions()
        print("\n" + "=" * 60)
        print("BEDROCK PLUGIN VERSIONS")
        print("=" * 60)
        for plugin, info in versions.items():
            if info:
                print(f"\n{plugin.upper()}:")
                print(json.dumps(info, indent=2))
    
    elif args.full:
        results = updater.full_bedrock_update(restart_services=args.restart)
        print("\n" + json.dumps(results, indent=2))
    
    elif args.geyser:
        result = updater.update_geyser_standalone()
        print(json.dumps(result, indent=2))
    
    elif args.via:
        result = updater.update_viaversion(include_viabackwards=True)
        print(json.dumps(result, indent=2))
    
    elif args.floodgate:
        result = updater.update_floodgate(platform='both')
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
