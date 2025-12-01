#!/usr/bin/env python3
"""
Plugin Metadata Populator

Scans live instances and populates plugin metadata tables:
- plugins (with versions, sources, CI/CD info)
- instance_plugins (what's installed where)
- instance_datapacks (datapack tracking)
- instance_server_properties (server.properties values)
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import yaml
import json
import hashlib
import re

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


class PluginMetadataPopulator:
    """Populates plugin metadata from live instances"""
    
    def __init__(self, db: ConfigDatabase, amp_base_dir: Path):
        self.db = db
        self.amp_base_dir = amp_base_dir
        self.scanner = AMPInstanceScanner(amp_base_dir)
    
    def populate_all(self):
        """Populate all metadata tables"""
        logger.info("Starting plugin metadata population...")
        
        instances = self.scanner.discover_instances()
        logger.info(f"Found {len(instances)} instances")
        
        for instance in instances:
            try:
                self.populate_instance(instance)
            except Exception as e:
                logger.error(f"Failed to process {instance['name']}: {e}", exc_info=True)
        
        logger.info("Plugin metadata population complete")
    
    def populate_instance(self, instance: dict):
        """Populate metadata for a single instance"""
        instance_id = instance['name']
        logger.info(f"Processing {instance_id}...")
        
        instance_path = Path(instance['path'])
        minecraft_dir = instance_path / 'Minecraft'
        
        if not minecraft_dir.exists():
            logger.warning(f"Minecraft directory not found for {instance_id}")
            return
        
        # 1. Scan plugins
        plugins_dir = minecraft_dir / 'plugins'
        if plugins_dir.exists():
            self._scan_plugins(instance_id, plugins_dir)
        
        # 2. Scan datapacks
        datapacks_dir = minecraft_dir / 'world' / 'datapacks'
        if datapacks_dir.exists():
            self._scan_datapacks(instance_id, datapacks_dir)
        
        # 3. Scan server properties
        server_props = minecraft_dir / 'server.properties'
        if server_props.exists():
            self._scan_server_properties(instance_id, server_props)
    
    def _scan_plugins(self, instance_id: str, plugins_dir: Path):
        """Scan and register plugins"""
        for item in plugins_dir.iterdir():
            # Check for JAR files
            if item.is_file() and item.suffix == '.jar':
                self._process_plugin_jar(instance_id, item)
            
            # Check for plugin folders with plugin.yml
            elif item.is_dir():
                plugin_yml = item / 'plugin.yml'
                if plugin_yml.exists():
                    self._process_plugin_folder(instance_id, item, plugin_yml)
    
    def _process_plugin_jar(self, instance_id: str, jar_file: Path):
        """Process a plugin JAR file"""
        import zipfile
        
        try:
            with zipfile.ZipFile(jar_file, 'r') as zf:
                # Try to read plugin.yml
                try:
                    plugin_yml_data = zf.read('plugin.yml').decode('utf-8')
                    plugin_info = yaml.safe_load(plugin_yml_data)
                except:
                    # Try fabric.mod.json
                    try:
                        fabric_json_data = zf.read('fabric.mod.json').decode('utf-8')
                        plugin_info = json.loads(fabric_json_data)
                        plugin_info = self._normalize_fabric_metadata(plugin_info)
                    except:
                        # Unknown plugin format
                        logger.warning(f"Could not read metadata from {jar_file.name}")
                        return
                
                self._register_plugin(instance_id, plugin_info, jar_file)
        
        except Exception as e:
            logger.warning(f"Failed to process JAR {jar_file.name}: {e}")
    
    def _process_plugin_folder(self, instance_id: str, folder: Path, plugin_yml: Path):
        """Process an unpacked plugin folder"""
        try:
            with open(plugin_yml, 'r', encoding='utf-8') as f:
                plugin_info = yaml.safe_load(f)
            
            self._register_plugin(instance_id, plugin_info, folder)
        
        except Exception as e:
            logger.warning(f"Failed to process plugin folder {folder.name}: {e}")
    
    def _normalize_fabric_metadata(self, fabric_data: dict) -> dict:
        """Convert Fabric mod metadata to plugin.yml format"""
        return {
            'name': fabric_data.get('name', fabric_data.get('id', 'Unknown')),
            'version': fabric_data.get('version', '1.0.0'),
            'main': fabric_data.get('entrypoints', {}).get('main', [''])[0],
            'authors': fabric_data.get('authors', []),
            'description': fabric_data.get('description', ''),
            'website': fabric_data.get('contact', {}).get('homepage', '')
        }
    
    def _register_plugin(self, instance_id: str, plugin_info: dict, file_path: Path):
        """Register plugin in database"""
        plugin_name = plugin_info.get('name', 'Unknown')
        version = plugin_info.get('version', '1.0.0')
        
        # Normalize plugin ID
        plugin_id = self._normalize_plugin_id(plugin_name)
        
        # Calculate file hash
        file_hash = self._calculate_hash(file_path) if file_path.is_file() else None
        
        # Detect platform
        platform = self._detect_platform(plugin_info)
        
        # Try to find source repositories
        sources = self._discover_sources(plugin_name, plugin_info)
        
        # Insert/update plugin registry
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO plugins 
            (plugin_id, plugin_name, platform, current_version, 
             github_repo, modrinth_id, hangar_slug, spigot_id, bukkit_id, curseforge_id,
             docs_url, wiki_url, plugin_page_url,
             has_cicd, cicd_provider, cicd_url,
             description, author, license,
             last_checked_at, last_updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                current_version = VALUES(current_version),
                github_repo = COALESCE(VALUES(github_repo), github_repo),
                modrinth_id = COALESCE(VALUES(modrinth_id), modrinth_id),
                hangar_slug = COALESCE(VALUES(hangar_slug), hangar_slug),
                docs_url = COALESCE(VALUES(docs_url), docs_url),
                wiki_url = COALESCE(VALUES(wiki_url), wiki_url),
                last_checked_at = VALUES(last_checked_at)
        """, (
            plugin_id, plugin_name, platform, version,
            sources.get('github_repo'), sources.get('modrinth_id'), sources.get('hangar_slug'),
            sources.get('spigot_id'), sources.get('bukkit_id'), sources.get('curseforge_id'),
            sources.get('docs_url'), sources.get('wiki_url'), sources.get('plugin_page_url'),
            sources.get('has_cicd', False), sources.get('cicd_provider', 'none'), sources.get('cicd_url'),
            plugin_info.get('description', ''), self._get_author(plugin_info), plugin_info.get('license', ''),
            datetime.now(), datetime.now()
        ))
        
        # Insert/update instance_plugins
        cursor.execute("""
            INSERT INTO instance_plugins
            (instance_id, plugin_id, installed_version, file_name, file_hash, is_enabled, installed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                installed_version = VALUES(installed_version),
                file_name = VALUES(file_name),
                file_hash = VALUES(file_hash),
                last_checked_at = NOW()
        """, (
            instance_id, plugin_id, version, file_path.name, file_hash, True, datetime.now()
        ))
        
        self.db.conn.commit()
        logger.info(f"Registered: {plugin_name} v{version} on {instance_id}")
    
    def _normalize_plugin_id(self, plugin_name: str) -> str:
        """Create normalized plugin ID"""
        return re.sub(r'[^a-z0-9_-]', '', plugin_name.lower().replace(' ', '-'))
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _detect_platform(self, plugin_info: dict) -> str:
        """Detect plugin platform"""
        if 'main' in plugin_info:
            main_class = plugin_info.get('main', '')
            if 'fabric' in main_class.lower():
                return 'fabric'
            elif 'neoforge' in main_class.lower() or 'forge' in main_class.lower():
                return 'neoforge'
            else:
                return 'paper'  # Default to Paper/Spigot
        return 'paper'
    
    def _get_author(self, plugin_info: dict) -> str:
        """Extract author from plugin info"""
        author = plugin_info.get('author', plugin_info.get('authors', ''))
        if isinstance(author, list):
            return ', '.join(author)
        return str(author)
    
    def _discover_sources(self, plugin_name: str, plugin_info: dict) -> dict:
        """Discover source repositories and documentation"""
        sources = {}
        
        # Check website field for common patterns
        website = plugin_info.get('website', '')
        
        if 'github.com' in website:
            # Extract GitHub repo
            match = re.search(r'github\.com/([^/]+/[^/]+)', website)
            if match:
                sources['github_repo'] = match.group(1)
                sources['has_cicd'] = True
                sources['cicd_provider'] = 'github'
                sources['cicd_url'] = f"https://github.com/{match.group(1)}/actions"
        
        if 'modrinth.com' in website:
            # Extract Modrinth slug
            match = re.search(r'modrinth\.com/(?:mod|plugin)/([^/]+)', website)
            if match:
                sources['modrinth_id'] = match.group(1)
        
        if 'hangar.papermc.io' in website:
            # Extract Hangar slug
            match = re.search(r'hangar\.papermc\.io/([^/]+)', website)
            if match:
                sources['hangar_slug'] = match.group(1)
        
        if 'spigotmc.org' in website:
            # Extract Spigot ID
            match = re.search(r'spigotmc\.org/resources/[^.]+\.(\d+)', website)
            if match:
                sources['spigot_id'] = match.group(1)
        
        if 'dev.bukkit.org' in website or 'curseforge.com' in website:
            # Extract Bukkit/CurseForge ID
            match = re.search(r'/projects/([^/]+)', website)
            if match:
                if 'bukkit' in website:
                    sources['bukkit_id'] = match.group(1)
                else:
                    sources['curseforge_id'] = match.group(1)
        
        # Documentation URLs
        if website:
            sources['plugin_page_url'] = website
            
            # Common doc URL patterns
            if 'github.com' in website:
                repo = sources.get('github_repo')
                if repo:
                    sources['docs_url'] = f"https://github.com/{repo}/wiki"
                    sources['wiki_url'] = f"https://github.com/{repo}/wiki"
        
        return sources
    
    def _scan_datapacks(self, instance_id: str, datapacks_dir: Path):
        """Scan and register datapacks"""
        for item in datapacks_dir.iterdir():
            if item.name == 'vanilla':
                continue
            
            datapack_name = item.stem if item.is_file() else item.name
            file_hash = self._calculate_hash(item) if item.is_file() else None
            
            # Try to detect source
            sources = self._discover_datapack_sources(datapack_name, item)
            
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO instance_datapacks
                (instance_id, datapack_name, world_name, file_name, file_hash,
                 modrinth_id, github_repo, custom_source, is_enabled, installed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    file_name = VALUES(file_name),
                    file_hash = VALUES(file_hash),
                    last_checked_at = NOW()
            """, (
                instance_id, datapack_name, 'world', item.name, file_hash,
                sources.get('modrinth_id'), sources.get('github_repo'), sources.get('custom_source'),
                True, datetime.now()
            ))
            
            self.db.conn.commit()
            logger.info(f"Registered datapack: {datapack_name} on {instance_id}")
    
    def _discover_datapack_sources(self, datapack_name: str, datapack_path: Path) -> dict:
        """Try to discover datapack sources"""
        sources = {}
        
        # Check for pack.mcmeta
        if datapack_path.is_dir():
            pack_meta = datapack_path / 'pack.mcmeta'
            if pack_meta.exists():
                try:
                    with open(pack_meta, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        description = meta.get('pack', {}).get('description', '')
                        
                        # Try to extract URLs from description
                        if 'github.com' in description:
                            match = re.search(r'github\.com/([^/\s]+/[^/\s]+)', description)
                            if match:
                                sources['github_repo'] = match.group(1)
                        
                        if 'modrinth.com' in description:
                            match = re.search(r'modrinth\.com/datapack/([^\s]+)', description)
                            if match:
                                sources['modrinth_id'] = match.group(1)
                except:
                    pass
        
        return sources
    
    def _scan_server_properties(self, instance_id: str, props_file: Path):
        """Scan server.properties file"""
        try:
            properties = {}
            with open(props_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        properties[key.strip()] = value.strip()
            
            # Extract common properties
            level_name = properties.get('level-name', 'world')
            gamemode = properties.get('gamemode', 'survival')
            difficulty = properties.get('difficulty', 'normal')
            max_players = int(properties.get('max-players', '20'))
            view_distance = int(properties.get('view-distance', '10'))
            simulation_distance = int(properties.get('simulation-distance', '10'))
            pvp = properties.get('pvp', 'true').lower() == 'true'
            spawn_protection = int(properties.get('spawn-protection', '16'))
            
            cursor = self.db.conn.cursor()
            cursor.execute("""
                INSERT INTO instance_server_properties
                (instance_id, level_name, gamemode, difficulty, max_players,
                 view_distance, simulation_distance, pvp, spawn_protection,
                 properties_json, last_updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    level_name = VALUES(level_name),
                    gamemode = VALUES(gamemode),
                    difficulty = VALUES(difficulty),
                    max_players = VALUES(max_players),
                    view_distance = VALUES(view_distance),
                    simulation_distance = VALUES(simulation_distance),
                    pvp = VALUES(pvp),
                    spawn_protection = VALUES(spawn_protection),
                    properties_json = VALUES(properties_json),
                    last_updated_at = VALUES(last_updated_at)
            """, (
                instance_id, level_name, gamemode, difficulty, max_players,
                view_distance, simulation_distance, pvp, spawn_protection,
                json.dumps(properties), datetime.now()
            ))
            
            self.db.conn.commit()
            logger.info(f"Registered server properties for {instance_id}")
        
        except Exception as e:
            logger.error(f"Failed to scan server.properties for {instance_id}: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Populate plugin metadata')
    parser.add_argument('--amp-dir', default='/home/amp/.ampdata/instances',
                       help='AMP instances directory')
    
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
        populator = PluginMetadataPopulator(db, Path(args.amp_dir))
        populator.populate_all()
    finally:
        db.disconnect()


if __name__ == '__main__':
    main()
