#!/usr/bin/env python3
"""
Wiki and Documentation URL Discovery

Automatically discovers wiki, documentation, and plugin page URLs
by checking common patterns and GitHub repositories.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import requests
import re
from typing import Optional, Dict, List
from urllib.parse import urljoin

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_access import ConfigDatabase
from core.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WikiDiscovery:
    """Discovers documentation and wiki URLs for plugins"""
    
    def __init__(self, db: ConfigDatabase):
        self.db = db
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArchiveSMP-ConfigManager/1.0'
        })
    
    def discover_all_plugins(self):
        """Discover docs for all plugins"""
        cursor = self.db.conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT plugin_id, plugin_name, github_repo, 
                   docs_url, wiki_url, plugin_page_url
            FROM plugins
            WHERE github_repo IS NOT NULL 
               OR docs_url IS NULL 
               OR wiki_url IS NULL
        """)
        
        plugins = cursor.fetchall()
        logger.info(f"Discovering docs for {len(plugins)} plugins...")
        
        for plugin in plugins:
            try:
                self.discover_plugin_docs(
                    plugin['plugin_id'],
                    plugin['plugin_name'],
                    plugin['github_repo']
                )
            except Exception as e:
                logger.error(f"Failed to discover docs for {plugin['plugin_name']}: {e}")
    
    def discover_plugin_docs(self, plugin_id: str, plugin_name: str, github_repo: Optional[str]):
        """Discover documentation URLs for a plugin"""
        logger.info(f"Discovering docs for {plugin_name}...")
        
        urls = {
            'docs_url': None,
            'wiki_url': None,
            'plugin_page_url': None
        }
        
        # 1. Check GitHub repository
        if github_repo:
            github_urls = self._discover_github_docs(github_repo)
            urls.update(github_urls)
        
        # 2. Search for common doc patterns
        search_urls = self._search_common_patterns(plugin_name)
        for key, value in search_urls.items():
            if value and not urls.get(key):
                urls[key] = value
        
        # 3. Check specific platforms
        platform_urls = self._check_platforms(plugin_name)
        for key, value in platform_urls.items():
            if value and not urls.get(key):
                urls[key] = value
        
        # Update database
        if any(urls.values()):
            cursor = self.db.conn.cursor()
            cursor.execute("""
                UPDATE plugins
                SET docs_url = COALESCE(docs_url, %s),
                    wiki_url = COALESCE(wiki_url, %s),
                    plugin_page_url = COALESCE(plugin_page_url, %s),
                    last_checked_at = %s
                WHERE plugin_id = %s
            """, (
                urls['docs_url'],
                urls['wiki_url'],
                urls['plugin_page_url'],
                datetime.now(),
                plugin_id
            ))
            
            self.db.conn.commit()
            
            found = [k for k, v in urls.items() if v]
            logger.info(f"Updated {plugin_name}: {', '.join(found)}")
    
    def _discover_github_docs(self, github_repo: str) -> Dict[str, Optional[str]]:
        """Discover docs from GitHub repository"""
        urls = {}
        
        # GitHub Wiki
        wiki_url = f"https://github.com/{github_repo}/wiki"
        if self._url_exists(wiki_url):
            urls['wiki_url'] = wiki_url
        
        # Check for GitHub Pages
        # Common patterns: username.github.io/repo or org.github.io/repo
        owner, repo = github_repo.split('/')
        pages_url = f"https://{owner}.github.io/{repo}"
        if self._url_exists(pages_url):
            urls['docs_url'] = pages_url
        
        # Check README for doc links
        readme_urls = self._parse_github_readme(github_repo)
        if readme_urls.get('docs') and not urls.get('docs_url'):
            urls['docs_url'] = readme_urls['docs']
        if readme_urls.get('wiki') and not urls.get('wiki_url'):
            urls['wiki_url'] = readme_urls['wiki']
        
        # GitHub repo as plugin page
        urls['plugin_page_url'] = f"https://github.com/{github_repo}"
        
        return urls
    
    def _parse_github_readme(self, github_repo: str) -> Dict[str, Optional[str]]:
        """Parse README for documentation links"""
        try:
            # Try to get README via API
            response = self.session.get(
                f"https://api.github.com/repos/{github_repo}/readme",
                headers={'Accept': 'application/vnd.github.raw+json'},
                timeout=10
            )
            
            if response.status_code != 200:
                return {}
            
            readme_content = response.text
            
            # Look for doc links
            doc_patterns = [
                r'Documentation:\s*\[.*?\]\((https?://[^\)]+)\)',
                r'Docs:\s*\[.*?\]\((https?://[^\)]+)\)',
                r'\[Documentation\]\((https?://[^\)]+)\)',
                r'\[Docs\]\((https?://[^\)]+)\)',
                r'https?://.*?docs?\..*?(?:\s|$)',
            ]
            
            wiki_patterns = [
                r'Wiki:\s*\[.*?\]\((https?://[^\)]+)\)',
                r'\[Wiki\]\((https?://[^\)]+)\)',
            ]
            
            urls = {}
            
            for pattern in doc_patterns:
                match = re.search(pattern, readme_content, re.IGNORECASE)
                if match:
                    urls['docs'] = match.group(1).strip()
                    break
            
            for pattern in wiki_patterns:
                match = re.search(pattern, readme_content, re.IGNORECASE)
                if match:
                    urls['wiki'] = match.group(1).strip()
                    break
            
            return urls
        
        except Exception as e:
            logger.debug(f"Failed to parse README for {github_repo}: {e}")
            return {}
    
    def _search_common_patterns(self, plugin_name: str) -> Dict[str, Optional[str]]:
        """Search for common documentation URL patterns"""
        urls = {}
        
        # Normalize plugin name for URL
        plugin_slug = plugin_name.lower().replace(' ', '-').replace('_', '-')
        
        # Common doc hosting patterns
        doc_patterns = [
            f"https://{plugin_slug}.readthedocs.io",
            f"https://docs.{plugin_slug}.com",
            f"https://wiki.{plugin_slug}.com",
            f"https://{plugin_slug}.github.io",
        ]
        
        for url in doc_patterns:
            if self._url_exists(url):
                urls['docs_url'] = url
                logger.info(f"Found docs: {url}")
                break
        
        return urls
    
    def _check_platforms(self, plugin_name: str) -> Dict[str, Optional[str]]:
        """Check specific plugin platforms"""
        urls = {}
        
        # Check SpigotMC
        spigot_url = self._search_spigot(plugin_name)
        if spigot_url:
            urls['plugin_page_url'] = spigot_url
        
        # Check Bukkit/CurseForge
        bukkit_url = self._search_bukkit(plugin_name)
        if bukkit_url:
            urls['plugin_page_url'] = bukkit_url
        
        return urls
    
    def _search_spigot(self, plugin_name: str) -> Optional[str]:
        """Search SpigotMC for plugin page"""
        try:
            # Try direct API search (if available)
            # Note: SpigotMC doesn't have a public search API, 
            # so this would require scraping or manual mapping
            
            # For now, return None - could be enhanced with scraping
            return None
        
        except Exception as e:
            logger.debug(f"Failed to search SpigotMC: {e}")
            return None
    
    def _search_bukkit(self, plugin_name: str) -> Optional[str]:
        """Search Bukkit/CurseForge for plugin page"""
        try:
            # CurseForge has an API but requires API key
            # For now, try common URL pattern
            plugin_slug = plugin_name.lower().replace(' ', '-')
            url = f"https://dev.bukkit.org/projects/{plugin_slug}"
            
            if self._url_exists(url):
                return url
            
            return None
        
        except Exception as e:
            logger.debug(f"Failed to search Bukkit: {e}")
            return None
    
    def _url_exists(self, url: str, timeout: int = 5) -> bool:
        """Check if a URL exists (returns 200)"""
        try:
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except:
            # Try GET if HEAD fails
            try:
                response = self.session.get(url, timeout=timeout, stream=True)
                return response.status_code == 200
            except:
                return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Wiki and docs discovery')
    parser.add_argument('--plugin', metavar='PLUGIN_ID',
                       help='Discover docs for specific plugin')
    parser.add_argument('--github-repo', metavar='OWNER/REPO',
                       help='GitHub repo (used with --plugin)')
    
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
        discovery = WikiDiscovery(db)
        
        if args.plugin:
            cursor = db.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT plugin_name, github_repo
                FROM plugins
                WHERE plugin_id = %s
            """, (args.plugin,))
            
            plugin = cursor.fetchone()
            if plugin:
                github_repo = args.github_repo or plugin['github_repo']
                discovery.discover_plugin_docs(
                    args.plugin,
                    plugin['plugin_name'],
                    github_repo
                )
            else:
                logger.error(f"Plugin not found: {args.plugin}")
        else:
            # Discover all
            discovery.discover_all_plugins()
    
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
