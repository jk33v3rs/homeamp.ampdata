"""
Plugin Checker Module

Checks for available plugin updates by polling CI servers,
GitHub releases, and other plugin distribution sources.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from ..core.settings import get_settings
from datetime import datetime


class PluginChecker:
    """Checks for plugin updates across multiple sources"""
    
    def __init__(self, api_endpoints_config: Path):
        """
        Initialize plugin checker
        
        Args:
            api_endpoints_config: Path to plugin_api_endpoints.yaml
        """
        self.api_endpoints_config = api_endpoints_config
        self.endpoints = None
    
    def load_api_endpoints(self) -> Dict[str, Dict[str, str]]:
        """
        Load plugin API endpoint configurations
        
        Returns:
            Dict mapping plugin names to API endpoint info
        """
        import yaml
        
        try:
            if not self.api_endpoints_config.exists():
                # Create default config
                default_config = {
                    "WorldEdit": {"github": "EngineHub/WorldEdit"},
                    "WorldGuard": {"github": "EngineHub/WorldGuard"},
                    "Pl3xMap": {"github": "pl3xgaming/Pl3xMap"},
                    "LuckPerms": {"github": "LuckPerms/LuckPerms"},
                    "Vault": {"github": "MilkBowl/Vault"},
                    "PlaceholderAPI": {"spigot": "6245"},
                    "EssentialsX": {"github": "EssentialsX/Essentials"},
                    "CoreProtect": {"spigot": "8631"},
                    "GriefPrevention": {"spigot": "1884"},
                    "Plan": {"github": "plan-player-analytics/Plan"},
                    "Citizens": {"spigot": "13811"},
                    "Denizen": {"spigot": "21039"},
                    "Sentinel": {"spigot": "22017"},
                    "LibsDisguises": {"spigot": "81"},
                    "ProtocolLib": {"spigot": "1997"},
                    "Shopkeepers": {"github": "Shopkeepers/Shopkeepers"},
                    "ChestSort": {"spigot": "59773"},
                    "InvSort": {"spigot": "60746"},
                    "BetterSleeping": {"spigot": "60837"},
                    "UltimateTimber": {"spigot": "60306"}
                }
                
                with open(self.api_endpoints_config, 'w') as f:
                    yaml.dump(default_config, f, indent=2)
                
                self.endpoints = default_config
            else:
                with open(self.api_endpoints_config, 'r') as f:
                    self.endpoints = yaml.safe_load(f) or {}
            
            return self.endpoints
        except Exception as e:
            print(f"Error loading API endpoints: {e}")
            self.endpoints = {}
            return {}
    
    def check_github_release(self, repo: str) -> Optional[Dict[str, Any]]:
        """
        Check GitHub releases for latest version
        
        Args:
            repo: GitHub repo in format "owner/repo"
            
        Returns:
            Dict with version, download_url, release_date, changelog
        """
        import requests
        from datetime import datetime
        
        try:
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            headers = {"Accept": "application/vnd.github+json"}
            
            response = requests.get(url, headers=headers, timeout=settings.http_config.timeout_seconds)
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Find the .jar download URL
            download_url = None
            for asset in data.get("assets", []):
                if asset["name"].endswith(".jar"):
                    download_url = asset["browser_download_url"]
                    break
            
            return {
                "version": data["tag_name"].lstrip("v"),
                "download_url": download_url or data["html_url"],
                "release_date": data["published_at"],
                "changelog": data.get("body", ""),
                "prerelease": data.get("prerelease", False),
                "source": "github"
            }
        except Exception as e:
            print(f"Error checking GitHub release for {repo}: {e}")
            return None
    
    def check_spigot_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Check SpigotMC for latest resource version
        
        Args:
            resource_id: SpigotMC resource ID
            
        Returns:
            Dict with version, download_url, release_date
        """
        import requests
        
        try:
            # SpigotMC API endpoint
            url = f"https://api.spigotmc.org/legacy/update.php?resource={resource_id}"
            
            response = requests.get(url, timeout=settings.http_config.timeout_seconds)
            if response.status_code != 200:
                return None
            
            version = response.text.strip()
            if not version:
                return None
            
            return {
                "version": version,
                "download_url": f"https://www.spigotmc.org/resources/{resource_id}/",
                "release_date": None,  # SpigotMC API doesn't provide dates
                "changelog": None,
                "prerelease": False,
                "source": "spigot"
            }
        except Exception as e:
            print(f"Error checking SpigotMC resource {resource_id}: {e}")
            return None
    
    def check_hangar(self, plugin_slug: str) -> Optional[Dict[str, Any]]:
        """
        Check Hangar (Paper plugins) for latest version
        
        Args:
            plugin_slug: Hangar plugin slug
            
        Returns:
            Dict with version, download_url, release_date
        """
        import requests
        
        try:
            # Hangar API v1
            url = f"https://hangar.papermc.io/api/v1/projects/{plugin_slug}"
            headers = {"Accept": "application/json"}
            
            response = requests.get(url, headers=headers, timeout=settings.http_config.timeout_seconds)
            if response.status_code != 200:
                return None
            
            project_data = response.json()
            
            # Get latest version
            versions_url = f"https://hangar.papermc.io/api/v1/projects/{plugin_slug}/versions"
            versions_response = requests.get(versions_url, headers=headers, timeout=settings.http_config.timeout_seconds)
            
            if versions_response.status_code != 200:
                return None
            
            versions_data = versions_response.json()
            if not versions_data.get("result"):
                return None
            
            latest_version = versions_data["result"][0]
            
            return {
                "version": latest_version["name"],
                "download_url": f"https://hangar.papermc.io/{plugin_slug}/versions/{latest_version['name']}",
                "release_date": latest_version.get("createdAt"),
                "changelog": latest_version.get("description", ""),
                "prerelease": False,
                "source": "hangar"
            }
        except Exception as e:
            print(f"Error checking Hangar plugin {plugin_slug}: {e}")
            return None
    
    def get_installed_version(self, plugin_name: str, server_name: str, utildata_path: Path) -> Optional[str]:
        """
        Get currently installed version of a plugin on a server
        
        Args:
            plugin_name: Name of plugin
            server_name: Name of server
            utildata_path: Root utildata path
            
        Returns:
            Version string or None if not found
        """
        import yaml
        import zipfile
        import tempfile
        
        try:
            # Look for plugin.yml in the plugin JAR file
            plugins_dir = utildata_path / server_name / "plugins"
            if not plugins_dir.exists():
                return None
            
            # Find plugin JAR file (may have version in filename)
            jar_files = list(plugins_dir.glob(f"{plugin_name}*.jar"))
            if not jar_files:
                return None
            
            # Try to extract version from plugin.yml
            for jar_file in jar_files:
                try:
                    with zipfile.ZipFile(jar_file, 'r') as zip_ref:
                        if 'plugin.yml' in zip_ref.namelist():
                            with zip_ref.open('plugin.yml') as yml_file:
                                plugin_yml = yaml.safe_load(yml_file)
                                return plugin_yml.get('version')
                        elif 'paper-plugin.yml' in zip_ref.namelist():
                            with zip_ref.open('paper-plugin.yml') as yml_file:
                                plugin_yml = yaml.safe_load(yml_file)
                                return plugin_yml.get('version')
                except Exception:
                    continue
            
            # Fallback: try to extract version from filename
            for jar_file in jar_files:
                filename = jar_file.stem
                # Common patterns: PluginName-1.2.3.jar, PluginName_v1.2.3.jar
                import re
                version_match = re.search(r'[-_]v?(\d+(?:\.\d+)*(?:-[a-zA-Z0-9]+)?)', filename)
                if version_match:
                    return version_match.group(1)
            
            return "unknown"
        except Exception as e:
            print(f"Error getting version for {plugin_name} on {server_name}: {e}")
            return None
    
    def check_all_plugins(self, utildata_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Check all plugins for available updates
        
        Args:
            utildata_path: Root utildata path
            
        Returns:
            Dict mapping plugin names to update info
        """
        import yaml
        
        # Load API endpoint configuration
        if not self.endpoints:
            self.load_api_endpoints()
        
        from ..core.settings import get_settings
        
        settings = get_settings()
        update_info = {}
        servers = settings.all_servers
        
        # Get all unique plugins across all servers
        all_plugins = set()
        for server in servers:
            plugins_dir = utildata_path / server / "plugins"
            if plugins_dir.exists():
                for jar_file in plugins_dir.glob("*.jar"):
                    # Extract plugin name (remove version suffix)
                    import re
                    plugin_name = re.sub(r'[-_]v?\d+.*', '', jar_file.stem)
                    all_plugins.add(plugin_name)
        
        # Check each plugin for updates
        for plugin_name in all_plugins:
            plugin_info = {
                "current_versions": {},
                "latest_version": None,
                "update_available": False,
                "source": None,
                "download_url": None,
                "changelog": None,
                "risk_level": "unknown"
            }
            
            # Get current versions on each server
            for server in servers:
                version = self.get_installed_version(plugin_name, server, utildata_path)
                if version:
                    plugin_info["current_versions"][server] = version
            
            # Check for updates from configured sources
            if self.endpoints and plugin_name in self.endpoints:
                endpoint_config = self.endpoints[plugin_name]
                
                if endpoint_config.get("github"):
                    latest = self.check_github_release(endpoint_config["github"])
                elif endpoint_config.get("spigot"):
                    latest = self.check_spigot_resource(endpoint_config["spigot"])
                elif endpoint_config.get("hangar"):
                    latest = self.check_hangar(endpoint_config["hangar"])
                else:
                    latest = None
                
                if latest:
                    plugin_info["latest_version"] = latest["version"]
                    plugin_info["source"] = latest["source"]
                    plugin_info["download_url"] = latest["download_url"]
                    plugin_info["changelog"] = latest.get("changelog")
                    
                    # Check if update is available
                    for server, current_version in plugin_info["current_versions"].items():
                        if current_version != "unknown" and current_version != latest["version"]:
                            plugin_info["update_available"] = True
                            plugin_info["risk_level"] = self.assess_update_risk(
                                plugin_name, current_version, latest["version"]
                            )
                            break
            
            if plugin_info["current_versions"]:  # Only include if found on servers
                update_info[plugin_name] = plugin_info
        
        return update_info
    
    def assess_update_risk(self, plugin_name: str, current_version: str, new_version: str) -> str:
        """
        Assess risk level of updating a plugin
        
        Args:
            plugin_name: Name of plugin
            current_version: Current installed version
            new_version: Available new version
            
        Returns:
            Risk level: "low", "medium", "high", "critical"
        """
        try:
            import re
            
            # Parse version numbers
            def parse_version(version_str):
                # Extract semantic version (1.2.3) from string
                match = re.search(r'(\d+)\.(\d+)(?:\.(\d+))?', str(version_str))
                if match:
                    major = int(match.group(1))
                    minor = int(match.group(2))
                    patch = int(match.group(3) or 0)
                    return (major, minor, patch)
                return (0, 0, 0)
            
            current = parse_version(current_version)
            new = parse_version(new_version)
            
            # Risk assessment based on version changes
            if new[0] > current[0]:
                # Major version change - likely breaking changes
                return "high"
            elif new[1] > current[1]:
                # Minor version change - new features, possible issues
                if new[1] - current[1] > 2:
                    return "medium"
                else:
                    return "low"
            elif new[2] > current[2]:
                # Patch version - bug fixes, very low risk
                return "low"
            else:
                # Same or older version
                return "low"
                
        except Exception:
            return "medium"  # Default to medium risk if can't parse
    
    def generate_update_report(self, output_path: Path, update_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Generate plugin update availability report
        
        Args:
            output_path: Where to write report
            update_data: Update data from check_all_plugins
        """
        from datetime import datetime
        import json
        
        # Analyze the update data
        total_plugins = len(update_data)
        outdated_plugins = [name for name, data in update_data.items() if data.get('update_available')]
        
        # Categorize by risk level
        high_risk = [name for name, data in update_data.items() 
                    if data.get('update_available') and data.get('risk_level') == 'high']
        medium_risk = [name for name, data in update_data.items() 
                      if data.get('update_available') and data.get('risk_level') == 'medium']
        low_risk = [name for name, data in update_data.items() 
                   if data.get('update_available') and data.get('risk_level') == 'low']
        
        # Generate report
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_plugins': total_plugins,
                'outdated_plugins': len(outdated_plugins),
                'up_to_date_plugins': total_plugins - len(outdated_plugins),
                'high_risk_updates': len(high_risk),
                'medium_risk_updates': len(medium_risk),
                'low_risk_updates': len(low_risk)
            },
            'plugin_details': update_data,
            'recommendations': {
                'high_priority': high_risk,
                'medium_priority': medium_risk,
                'low_priority': low_risk
            }
        }
        
        # Write report to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Plugin update report generated: {output_path}")
        print(f"Total plugins: {total_plugins}")
        print(f"Outdated plugins: {len(outdated_plugins)}")
        print(f"High risk updates: {len(high_risk)}")
        print(f"Medium risk updates: {len(medium_risk)}")
        print(f"Low risk updates: {len(low_risk)}")
