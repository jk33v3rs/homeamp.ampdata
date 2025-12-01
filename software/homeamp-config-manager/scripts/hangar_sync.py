#!/usr/bin/env python3
"""
Hangar API Integration

Checks Hangar (PaperMC) for plugin updates and metadata.
Populates hangar_slug, docs_url, and version info.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import requests
from typing import Optional, Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_access import ConfigDatabase
from core.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HangarAPI:
    """Hangar (PaperMC) API integration for plugin updates"""
    
    BASE_URL = "https://hangar.papermc.io/api/v1"
    
    def __init__(self, db: ConfigDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArchiveSMP-ConfigManager/1.0'
        })
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """
        Search Hangar for projects
        
        Args:
            query: Search query (plugin name)
            
        Returns:
            List of project data
        """
        try:
            params = {
                'q': query,
                'limit': 10,
                'offset': 0
            }
            
            response = self.session.get(
                f"{self.BASE_URL}/projects",
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Hangar search failed for {query}: {response.status_code}")
                return []
            
            data = response.json()
            return data.get('result', [])
        
        except Exception as e:
            logger.error(f"Error searching Hangar for {query}: {e}")
            return []
    
    def get_project(self, owner: str, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get project details
        
        Args:
            owner: Project owner username
            slug: Project slug
            
        Returns:
            Project data or None
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/projects/{owner}/{slug}",
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error getting Hangar project {owner}/{slug}: {e}")
            return None
    
    def get_versions(self, owner: str, slug: str, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available versions for a project
        
        Args:
            owner: Project owner username
            slug: Project slug
            platform: Platform filter ('PAPER', 'WATERFALL', 'VELOCITY')
            
        Returns:
            List of version data
        """
        try:
            params = {}
            if platform:
                params['platform'] = platform.upper()
            
            response = self.session.get(
                f"{self.BASE_URL}/projects/{owner}/{slug}/versions",
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            return data.get('result', [])
        
        except Exception as e:
            logger.error(f"Error getting versions for {owner}/{slug}: {e}")
            return []
    
    def get_latest_version(self, owner: str, slug: str, platform: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get latest version for a project"""
        versions = self.get_versions(owner, slug, platform)
        
        if not versions:
            return None
        
        # Return most recent version
        return versions[0]
    
    def get_download_url(self, owner: str, slug: str, version_name: str, platform: str = 'PAPER') -> Optional[str]:
        """Get download URL for a specific version"""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/projects/{owner}/{slug}/versions/{version_name}/{platform}/download",
                timeout=10,
                allow_redirects=False
            )
            
            if response.status_code in (302, 303, 307, 308):
                return response.headers.get('Location')
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting download URL: {e}")
            return None
    
    def update_plugin_from_hangar(self, plugin_id: str, hangar_slug: str):
        """Update plugin metadata from Hangar"""
        logger.info(f"Updating {plugin_id} from Hangar...")
        
        # Parse slug (format: "owner/slug")
        if '/' in hangar_slug:
            owner, slug = hangar_slug.split('/', 1)
        else:
            # Try to guess owner or search
            results = self.search_projects(hangar_slug)
            if not results:
                logger.warning(f"Could not find Hangar project: {hangar_slug}")
                return
            
            # Use first result
            owner = results[0]['namespace']['owner']
            slug = results[0]['namespace']['slug']
        
        # Get project details
        project = self.get_project(owner, slug)
        
        if not project:
            logger.warning(f"Could not fetch Hangar data for {owner}/{slug}")
            return
        
        # Get latest version
        latest_version = self.get_latest_version(owner, slug)
        
        # Extract metadata
        latest_ver = latest_version.get('name') if latest_version else None
        description = project.get('description', '')
        license_name = project.get('settings', {}).get('license', {}).get('name', '')
        
        # URLs
        project_url = f"https://hangar.papermc.io/{owner}/{slug}"
        docs_url = project.get('settings', {}).get('homepage')
        wiki_url = project.get('settings', {}).get('issues')  # Often wiki is linked in issues
        
        # Download URL
        download_url = None
        if latest_version:
            download_url = self.get_download_url(owner, slug, latest_version['name'])
        
        # Check if has CI/CD (GitHub repo linked)
        has_cicd = False
        cicd_url = None
        github_repo = project.get('settings', {}).get('sources')
        
        if github_repo and 'github.com' in github_repo:
            has_cicd = True
            # Extract repo path
            import re
            match = re.search(r'github\.com/([^/]+/[^/]+)', github_repo)
            if match:
                repo_path = match.group(1).rstrip('/')
                cicd_url = f"https://github.com/{repo_path}/actions"
                github_repo = repo_path
        
        # Update database
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE plugins
            SET latest_version = %s,
                hangar_slug = %s,
                github_repo = COALESCE(github_repo, %s),
                docs_url = COALESCE(docs_url, %s),
                wiki_url = COALESCE(wiki_url, %s),
                plugin_page_url = COALESCE(plugin_page_url, %s),
                description = COALESCE(NULLIF(description, ''), %s),
                license = COALESCE(NULLIF(license, ''), %s),
                has_cicd = %s,
                cicd_provider = CASE WHEN %s THEN 'github' ELSE cicd_provider END,
                cicd_url = COALESCE(cicd_url, %s),
                last_checked_at = %s
            WHERE plugin_id = %s
        """, (
            latest_ver, f"{owner}/{slug}", github_repo,
            docs_url, wiki_url, project_url, description, license_name,
            has_cicd, has_cicd, cicd_url, datetime.now(), plugin_id
        ))
        
        self.db.conn.commit()
        logger.info(f"Updated {plugin_id}: v{latest_ver}")
    
    def scan_all_plugins(self):
        """Scan all Paper plugins and try to find them on Hangar"""
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT plugin_id, plugin_name, hangar_slug
            FROM plugins
            WHERE platform = 'paper'
        """)
        
        plugins = cursor.fetchall()
        logger.info(f"Scanning {len(plugins)} Paper plugins on Hangar...")
        
        for plugin in plugins:
            plugin_id = plugin['plugin_id']
            plugin_name = plugin['plugin_name']
            hangar_slug = plugin['hangar_slug']
            
            # If we already have hangar_slug, update from it
            if hangar_slug:
                self.update_plugin_from_hangar(plugin_id, hangar_slug)
                continue
            
            # Otherwise, try to search for it
            results = self.search_projects(plugin_name)
            
            if results:
                # Look for exact match
                exact_match = None
                for result in results:
                    if result['name'].lower() == plugin_name.lower():
                        exact_match = result
                        break
                
                if not exact_match:
                    exact_match = results[0]  # Use first result
                
                owner = exact_match['namespace']['owner']
                slug = exact_match['namespace']['slug']
                
                logger.info(f"Found {plugin_name} on Hangar: {owner}/{slug}")
                self.update_plugin_from_hangar(plugin_id, f"{owner}/{slug}")
            else:
                logger.info(f"No Hangar project found for {plugin_name}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hangar API integration')
    parser.add_argument('--scan-plugins', action='store_true',
                       help='Scan all Paper plugins')
    parser.add_argument('--update-plugin', metavar='PLUGIN_ID',
                       help='Update specific plugin')
    parser.add_argument('--hangar-slug', metavar='OWNER/SLUG',
                       help='Hangar slug (used with --update-plugin)')
    
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
        api = HangarAPI(db)
        
        if args.scan_plugins:
            api.scan_all_plugins()
        elif args.update_plugin and args.hangar_slug:
            api.update_plugin_from_hangar(args.update_plugin, args.hangar_slug)
        else:
            # Default: scan all
            api.scan_all_plugins()
    
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
