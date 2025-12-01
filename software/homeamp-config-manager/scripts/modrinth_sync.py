#!/usr/bin/env python3
"""
Modrinth API Integration

Checks Modrinth for plugin/mod/datapack updates and metadata.
Populates modrinth_id, docs_url, and version info.
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


class ModrinthAPI:
    """Modrinth API integration for plugin/mod updates"""
    
    BASE_URL = "https://api.modrinth.com/v2"
    
    def __init__(self, db: ConfigDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArchiveSMP-ConfigManager/1.0'
        })
    
    def search_project(self, query: str, project_type: str = 'plugin') -> Optional[Dict[str, Any]]:
        """
        Search Modrinth for a project
        
        Args:
            query: Search query (plugin name)
            project_type: 'plugin', 'mod', or 'datapack'
            
        Returns:
            Project data or None
        """
        try:
            params = {
                'query': query,
                'facets': f'[["project_type:{project_type}"]]',
                'limit': 5
            }
            
            response = self.session.get(
                f"{self.BASE_URL}/search",
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"Modrinth search failed for {query}: {response.status_code}")
                return None
            
            data = response.json()
            hits = data.get('hits', [])
            
            if not hits:
                return None
            
            # Return first exact match or first result
            for hit in hits:
                if hit['title'].lower() == query.lower() or hit['slug'].lower() == query.lower():
                    return hit
            
            return hits[0]
        
        except Exception as e:
            logger.error(f"Error searching Modrinth for {query}: {e}")
            return None
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project details by ID or slug
        
        Args:
            project_id: Project ID or slug
            
        Returns:
            Project data or None
        """
        try:
            response = self.session.get(
                f"{self.BASE_URL}/project/{project_id}",
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error getting Modrinth project {project_id}: {e}")
            return None
    
    def get_versions(self, project_id: str, game_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available versions for a project
        
        Args:
            project_id: Project ID or slug
            game_version: Minecraft version filter (e.g., '1.21.3')
            
        Returns:
            List of version data
        """
        try:
            params = {}
            if game_version:
                params['game_versions'] = f'["{game_version}"]'
            
            response = self.session.get(
                f"{self.BASE_URL}/project/{project_id}/version",
                params=params,
                timeout=10
            )
            
            if response.status_code != 200:
                return []
            
            return response.json()
        
        except Exception as e:
            logger.error(f"Error getting versions for {project_id}: {e}")
            return []
    
    def get_latest_version(self, project_id: str, game_version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get latest version for a project"""
        versions = self.get_versions(project_id, game_version)
        
        if not versions:
            return None
        
        # Filter for release versions (not beta/alpha)
        release_versions = [v for v in versions if v.get('version_type') == 'release']
        
        if release_versions:
            return release_versions[0]
        
        return versions[0]
    
    def update_plugin_from_modrinth(self, plugin_id: str, modrinth_project_id: str):
        """Update plugin metadata from Modrinth"""
        logger.info(f"Updating {plugin_id} from Modrinth...")
        
        # Get project details
        project = self.get_project(modrinth_project_id)
        
        if not project:
            logger.warning(f"Could not fetch Modrinth data for {modrinth_project_id}")
            return
        
        # Get latest version
        latest_version = self.get_latest_version(modrinth_project_id)
        
        # Extract metadata
        latest_ver = latest_version.get('version_number') if latest_version else None
        description = project.get('description', '')
        license_name = project.get('license', {}).get('name', '') if isinstance(project.get('license'), dict) else project.get('license', '')
        
        # URLs
        docs_url = project.get('wiki_url') or project.get('source_url')
        project_url = f"https://modrinth.com/plugin/{project['slug']}"
        
        # Download URL
        download_url = None
        if latest_version and latest_version.get('files'):
            download_url = latest_version['files'][0]['url']
        
        # Update database
        cursor = self.db.conn.cursor()
        cursor.execute("""
            UPDATE plugins
            SET latest_version = %s,
                modrinth_id = %s,
                docs_url = COALESCE(docs_url, %s),
                plugin_page_url = COALESCE(plugin_page_url, %s),
                description = COALESCE(NULLIF(description, ''), %s),
                license = COALESCE(NULLIF(license, ''), %s),
                last_checked_at = %s
            WHERE plugin_id = %s
        """, (
            latest_ver, modrinth_project_id, docs_url, project_url,
            description, license_name, datetime.now(), plugin_id
        ))
        
        self.db.conn.commit()
        logger.info(f"Updated {plugin_id}: v{latest_ver}")
    
    def scan_all_plugins(self):
        """Scan all registered plugins and try to find them on Modrinth"""
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT plugin_id, plugin_name, modrinth_id, platform
            FROM plugins
            WHERE platform IN ('paper', 'fabric', 'neoforge')
        """)
        
        plugins = cursor.fetchall()
        logger.info(f"Scanning {len(plugins)} plugins on Modrinth...")
        
        for plugin in plugins:
            plugin_id = plugin['plugin_id']
            plugin_name = plugin['plugin_name']
            modrinth_id = plugin['modrinth_id']
            
            # If we already have modrinth_id, update from it
            if modrinth_id:
                self.update_plugin_from_modrinth(plugin_id, modrinth_id)
                continue
            
            # Otherwise, try to search for it
            project_type = 'mod' if plugin['platform'] in ('fabric', 'neoforge') else 'plugin'
            result = self.search_project(plugin_name, project_type)
            
            if result:
                modrinth_slug = result['slug']
                logger.info(f"Found {plugin_name} on Modrinth: {modrinth_slug}")
                self.update_plugin_from_modrinth(plugin_id, modrinth_slug)
            else:
                logger.info(f"No Modrinth project found for {plugin_name}")
    
    def scan_datapacks(self):
        """Scan datapacks and find them on Modrinth"""
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT datapack_name, modrinth_id
            FROM instance_datapacks
            WHERE datapack_name != 'vanilla'
        """)
        
        datapacks = cursor.fetchall()
        logger.info(f"Scanning {len(datapacks)} datapacks on Modrinth...")
        
        for datapack in datapacks:
            datapack_name = datapack['datapack_name']
            modrinth_id = datapack['modrinth_id']
            
            if modrinth_id:
                # Update from existing ID
                project = self.get_project(modrinth_id)
                if project:
                    latest = self.get_latest_version(modrinth_id)
                    version = latest.get('version_number') if latest else None
                    
                    cursor.execute("""
                        UPDATE instance_datapacks
                        SET version = %s,
                            last_checked_at = %s
                        WHERE datapack_name = %s
                    """, (version, datetime.now(), datapack_name))
                    
                    self.db.conn.commit()
            else:
                # Search for it
                result = self.search_project(datapack_name, 'datapack')
                if result:
                    modrinth_slug = result['slug']
                    logger.info(f"Found datapack {datapack_name}: {modrinth_slug}")
                    
                    # Get version
                    latest = self.get_latest_version(modrinth_slug)
                    version = latest.get('version_number') if latest else None
                    
                    cursor.execute("""
                        UPDATE instance_datapacks
                        SET modrinth_id = %s,
                            version = %s,
                            last_checked_at = %s
                        WHERE datapack_name = %s
                    """, (modrinth_slug, version, datetime.now(), datapack_name))
                    
                    self.db.conn.commit()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Modrinth API integration')
    parser.add_argument('--scan-plugins', action='store_true',
                       help='Scan all plugins')
    parser.add_argument('--scan-datapacks', action='store_true',
                       help='Scan all datapacks')
    parser.add_argument('--update-plugin', metavar='PLUGIN_ID',
                       help='Update specific plugin')
    parser.add_argument('--modrinth-id', metavar='ID',
                       help='Modrinth project ID (used with --update-plugin)')
    
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
        api = ModrinthAPI(db)
        
        if args.scan_plugins:
            api.scan_all_plugins()
        elif args.scan_datapacks:
            api.scan_datapacks()
        elif args.update_plugin and args.modrinth_id:
            api.update_plugin_from_modrinth(args.update_plugin, args.modrinth_id)
        else:
            # Default: scan everything
            api.scan_all_plugins()
            api.scan_datapacks()
    
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
