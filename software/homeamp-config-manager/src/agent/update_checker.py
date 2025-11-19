"""
Update Checker - CI/CD Integration
Background task to check for plugin updates from various sources
"""

import logging
import time
from typing import Dict, List, Optional
from datetime import datetime
import requests
import mysql.connector
from packaging import version

from ..core.settings import get_settings

logger = logging.getLogger(__name__)


class UpdateChecker:
    """
    Checks for plugin updates from various sources
    Supports: Spigot, Modrinth, Hangar, GitHub, Jenkins
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArchiveSMP-ConfigManager/2.0'
        })
    
    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(
            host=self.settings.db_host,
            port=self.settings.db_port,
            user=self.settings.db_user,
            password=self.settings.db_password,
            database=self.settings.db_name
        )
    
    def run_update_check_cycle(self):
        """
        Run complete update check cycle for all plugins
        Called by scheduled task (hourly)
        """
        logger.info("Starting update check cycle...")
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get all plugins with update sources
            cursor.execute("""
                SELECT 
                    p.plugin_id,
                    p.name,
                    p.version as current_version,
                    p.source,
                    pus.source_type,
                    pus.source_url,
                    pus.source_identifier
                FROM plugins p
                LEFT JOIN plugin_update_sources pus ON p.plugin_id = pus.plugin_id
                WHERE pus.source_type IS NOT NULL
            """)
            
            plugins = cursor.fetchall()
            logger.info(f"Found {len(plugins)} plugins with update sources")
            
            updates_found = 0
            
            for plugin in plugins:
                try:
                    latest_version = self.check_plugin_update(
                        plugin['source_type'],
                        plugin['source_url'],
                        plugin['source_identifier']
                    )
                    
                    if latest_version:
                        # Compare versions
                        if self.is_newer_version(plugin['current_version'], latest_version):
                            self.record_update_available(
                                plugin['plugin_id'],
                                plugin['current_version'],
                                latest_version
                            )
                            updates_found += 1
                            logger.info(f"Update found for {plugin['name']}: {plugin['current_version']} → {latest_version}")
                        else:
                            logger.debug(f"No update for {plugin['name']} (current: {plugin['current_version']}, latest: {latest_version})")
                
                except Exception as e:
                    logger.error(f"Error checking updates for {plugin['name']}: {e}")
                    continue
            
            logger.info(f"Update check cycle complete. Found {updates_found} updates.")
            
        finally:
            cursor.close()
            conn.close()
    
    def check_plugin_update(self, source_type: str, source_url: str, source_identifier: str) -> Optional[str]:
        """
        Check for updates based on source type
        Returns latest version string or None
        """
        if source_type == 'spigot':
            return self.check_spigot_update(source_identifier)
        elif source_type == 'modrinth':
            return self.check_modrinth_update(source_identifier)
        elif source_type == 'hangar':
            return self.check_hangar_update(source_identifier)
        elif source_type == 'github':
            return self.check_github_update(source_identifier)
        elif source_type == 'jenkins':
            return self.check_jenkins_update(source_url)
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return None
    
    def check_spigot_update(self, resource_id: str) -> Optional[str]:
        """Check Spigot API for latest version"""
        try:
            url = f"https://api.spigotmc.org/simple/0.2/index.php?action=getResource&id={resource_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get('current_version')
        
        except Exception as e:
            logger.error(f"Spigot API error for resource {resource_id}: {e}")
            return None
    
    def check_modrinth_update(self, project_id: str) -> Optional[str]:
        """Check Modrinth API for latest version"""
        try:
            url = f"https://api.modrinth.com/v2/project/{project_id}/version"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            versions = response.json()
            if versions:
                # Get latest non-beta version
                latest = versions[0]
                return latest.get('version_number')
        
        except Exception as e:
            logger.error(f"Modrinth API error for project {project_id}: {e}")
            return None
    
    def check_hangar_update(self, project_slug: str) -> Optional[str]:
        """Check Hangar API for latest version"""
        try:
            url = f"https://hangar.papermc.io/api/v1/projects/{project_slug}/versions"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            versions = data.get('result', [])
            if versions:
                latest = versions[0]
                return latest.get('name')
        
        except Exception as e:
            logger.error(f"Hangar API error for project {project_slug}: {e}")
            return None
    
    def check_github_update(self, repo: str) -> Optional[str]:
        """Check GitHub Releases for latest version"""
        try:
            # repo format: "owner/repo"
            url = f"https://api.github.com/repos/{repo}/releases/latest"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            tag_name = data.get('tag_name', '')
            # Remove 'v' prefix if present
            return tag_name.lstrip('v')
        
        except Exception as e:
            logger.error(f"GitHub API error for repo {repo}: {e}")
            return None
    
    def check_jenkins_update(self, jenkins_url: str) -> Optional[str]:
        """Check Jenkins for latest build"""
        try:
            # jenkins_url format: "https://ci.example.com/job/plugin-name"
            url = f"{jenkins_url}/lastSuccessfulBuild/api/json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            build_number = data.get('number')
            return str(build_number) if build_number else None
        
        except Exception as e:
            logger.error(f"Jenkins API error for {jenkins_url}: {e}")
            return None
    
    def is_newer_version(self, current: str, latest: str) -> bool:
        """
        Compare version strings
        Returns True if latest is newer than current
        """
        try:
            # Clean version strings
            current_clean = current.strip().lstrip('v')
            latest_clean = latest.strip().lstrip('v')
            
            # Use packaging.version for semantic versioning
            return version.parse(latest_clean) > version.parse(current_clean)
        
        except Exception as e:
            logger.warning(f"Version comparison failed: {current} vs {latest}: {e}")
            # Fallback to string comparison
            return latest != current
    
    def record_update_available(self, plugin_id: int, current_version: str, latest_version: str):
        """
        Record available update in database
        """
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Update or insert into plugin_versions table
            cursor.execute("""
                INSERT INTO plugin_versions 
                (plugin_id, current_version, latest_version, update_available, checked_at)
                VALUES (%s, %s, %s, TRUE, NOW())
                ON DUPLICATE KEY UPDATE
                    latest_version = %s,
                    update_available = TRUE,
                    checked_at = NOW()
            """, (plugin_id, current_version, latest_version, latest_version))
            
            conn.commit()
        
        finally:
            cursor.close()
            conn.close()


# ====================
# Checker Subclasses
# ====================

class SpigotAPIChecker:
    """Dedicated Spigot checker"""
    
    @staticmethod
    def fetch_latest_build(resource_id: str) -> Optional[str]:
        try:
            url = f"https://api.spigotmc.org/simple/0.2/index.php?action=getResource&id={resource_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('current_version')
        except Exception as e:
            logger.error(f"Spigot checker error: {e}")
            return None


class ModrinthAPIChecker:
    """Dedicated Modrinth checker"""
    
    @staticmethod
    def fetch_latest_version(project_id: str) -> Optional[str]:
        try:
            url = f"https://api.modrinth.com/v2/project/{project_id}/version"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            versions = response.json()
            if versions:
                return versions[0].get('version_number')
        except Exception as e:
            logger.error(f"Modrinth checker error: {e}")
            return None


class HangarAPIChecker:
    """Dedicated Hangar checker"""
    
    @staticmethod
    def fetch_latest_version(project_slug: str) -> Optional[str]:
        try:
            url = f"https://hangar.papermc.io/api/v1/projects/{project_slug}/versions"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            versions = data.get('result', [])
            if versions:
                return versions[0].get('name')
        except Exception as e:
            logger.error(f"Hangar checker error: {e}")
            return None


class GitHubReleasesChecker:
    """Dedicated GitHub checker"""
    
    @staticmethod
    def fetch_latest_release(repo_owner: str, repo_name: str) -> Optional[str]:
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            tag_name = data.get('tag_name', '')
            return tag_name.lstrip('v')
        except Exception as e:
            logger.error(f"GitHub checker error: {e}")
            return None


class JenkinsChecker:
    """Dedicated Jenkins checker"""
    
    @staticmethod
    def fetch_latest_build(jenkins_url: str, job_name: str) -> Optional[str]:
        try:
            url = f"{jenkins_url}/job/{job_name}/lastSuccessfulBuild/api/json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            build_number = data.get('number')
            return str(build_number) if build_number else None
        except Exception as e:
            logger.error(f"Jenkins checker error: {e}")
            return None


# ====================
# Utility Functions
# ====================

def compare_versions(current: str, latest: str) -> bool:
    """
    Determine if update available
    Returns True if latest > current
    """
    try:
        current_clean = current.strip().lstrip('v')
        latest_clean = latest.strip().lstrip('v')
        return version.parse(latest_clean) > version.parse(current_clean)
    except Exception:
        return latest != current
