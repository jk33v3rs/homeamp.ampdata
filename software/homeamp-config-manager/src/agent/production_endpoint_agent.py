"""
Production-Ready Configuration Management Endpoint Agent

FEATURES:
- Full auto-discovery of instances, plugins, datapacks
- No hardcoded assumptions about plugin/datapack names
- Dynamic meta-tagging with user-extensible categories
- CI/CD integration for plugin updates
- Datapack deployment management
- Plugin info page registry tracking
- Comprehensive drift detection and logging
- Plugin update queue processing
- Webhook event handling
"""

import time
import logging
import sys
import hashlib
import re
import json
import zipfile
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import yaml

from ..database.db_access import ConfigDatabase
from ..amp_integration.instance_scanner import AMPInstanceScanner
from ..analyzers.config_reader import PluginConfigReader


class ProductionEndpointAgent:
    """
    Fully self-discovering, production-ready agent.
    Runs on physical servers to maintain central database state.
    """
    
    def __init__(self, server_name: str, db_config: Dict[str, Any], config: Dict[str, Any] = None):
        """
        Args:
            server_name: Physical server name ('hetzner-xeon' or 'ovh-ryzen')
            db_config: Database connection config
            config: Agent configuration (scan intervals, feature flags, etc.)
        """
        self.server_name = server_name
        self.db = ConfigDatabase(**db_config)
        self.config = config or {}
        
        # Logging
        self.setup_logging()
        
        # AMP instance discovery
        self.amp_base_dir = Path(self.config.get('amp_base_dir', '/home/amp/.ampdata/instances'))
        self.scanner = AMPInstanceScanner(self.amp_base_dir)
        
        # State tracking
        self.current_run_id: Optional[int] = None
        self.discovered_instances: Dict[str, Dict] = {}
        self.plugin_registry: Dict[str, Dict] = {}  # {plugin_id: metadata}
        self.datapack_registry: Dict[str, Dict] = {}
        
        # Feature flags
        self.enable_auto_discovery = self.config.get('enable_auto_discovery', True)
        self.enable_plugin_updates = self.config.get('enable_plugin_updates', True)
        self.enable_datapack_deployment = self.config.get('enable_datapack_deployment', True)
        self.enable_drift_detection = self.config.get('enable_drift_detection', True)
        self.enable_meta_tagging = self.config.get('enable_meta_tagging', True)
        
        # Intervals (seconds)
        self.full_scan_interval = self.config.get('full_scan_interval', 300)  # 5 min
        self.update_check_interval = self.config.get('update_check_interval', 600)  # 10 min
        self.queue_process_interval = self.config.get('queue_process_interval', 60)  # 1 min
        
        self.running = False
        self.last_full_scan = None
        self.last_update_check = None
        self.last_queue_process = None
    
    def setup_logging(self):
        """Configure logging with emojis for visual clarity"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f'/var/log/archivesmp/agent-{self.server_name}.log')
            ]
        )
        self.logger = logging.getLogger(f'agent-{self.server_name}')
    
    def start(self):
        """Start agent main loop"""
        self.logger.info(f"🚀 Starting production endpoint agent for {self.server_name}")
        self.logger.info(f"📁 AMP Base Dir: {self.amp_base_dir}")
        self.logger.info(f"⚙️  Features: discovery={self.enable_auto_discovery}, "
                        f"updates={self.enable_plugin_updates}, "
                        f"datapacks={self.enable_datapack_deployment}, "
                        f"drift={self.enable_drift_detection}")
        
        self.db.connect()
        self.running = True
        
        # Initial load of registries
        self._load_plugin_registry()
        self._load_datapack_registry()
        
        try:
            while self.running:
                self._run_cycle()
                time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            self.logger.info("🛑 Received shutdown signal")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("👋 Shutting down agent")
        self.running = False
        if self.current_run_id:
            self._end_discovery_run('partial')
        self.db.disconnect()
    
    def _run_cycle(self):
        """Execute one agent cycle - check what needs doing"""
        now = datetime.now()
        
        try:
            # 1. Full discovery scan
            if self.enable_auto_discovery and self._should_run_full_scan(now):
                self._run_full_discovery()
                self.last_full_scan = now
            
            # 2. Update checks
            if self.enable_plugin_updates and self._should_check_updates(now):
                self._check_plugin_updates()
                self.last_update_check = now
            
            # 3. Process deployment queues
            if self._should_process_queues(now):
                if self.enable_plugin_updates:
                    self._process_plugin_update_queue()
                if self.enable_datapack_deployment:
                    self._process_datapack_deployment_queue()
                self.last_queue_process = now
            
            # 4. Process webhook events
            if self.enable_plugin_updates:
                self._process_webhook_events()
        
        except Exception as e:
            self.logger.error(f"❌ Error in agent cycle: {e}", exc_info=True)
    
    def _should_run_full_scan(self, now: datetime) -> bool:
        if not self.last_full_scan:
            return True
        elapsed = (now - self.last_full_scan).total_seconds()
        return elapsed >= self.full_scan_interval
    
    def _should_check_updates(self, now: datetime) -> bool:
        if not self.last_update_check:
            return True
        elapsed = (now - self.last_update_check).total_seconds()
        return elapsed >= self.update_check_interval
    
    def _should_process_queues(self, now: datetime) -> bool:
        if not self.last_queue_process:
            return True
        elapsed = (now - self.last_queue_process).total_seconds()
        return elapsed >= self.queue_process_interval
    
    # ========================================================================
    # AUTO-DISCOVERY SYSTEM
    # ========================================================================
    
    def _run_full_discovery(self):
        """Run complete discovery: instances, plugins, datapacks, configs"""
        self.logger.info("🔍 Starting full discovery scan")
        self.current_run_id = self._start_discovery_run('full_scan')
        
        stats = {
            'instances': 0,
            'plugins': 0,
            'datapacks': 0,
            'configs': 0,
            'new_items': 0,
            'changed_items': 0
        }
        
        try:
            # 1. Discover instances
            instances = self._discover_instances()
            stats['instances'] = len(instances)
            
            # 2. For each instance, discover plugins, datapacks, configs
            for instance in instances:
                instance_id = instance['name']
                instance_path = Path(instance['path'])
                
                self.logger.info(f"📦 Scanning instance: {instance_id}")
                
                # Ensure instance exists in DB
                self._register_instance(instance)
                
                # Discover plugins
                plugins = self._discover_instance_plugins(instance_id, instance_path)
                stats['plugins'] += len(plugins)
                
                # Discover datapacks
                datapacks = self._discover_instance_datapacks(instance_id, instance_path)
                stats['datapacks'] += len(datapacks)
                
                # Scan configs
                if self.enable_drift_detection:
                    self._scan_instance_configs(instance_id, instance_path)
                    stats['configs'] += 1
                
                # Scan server properties
                self._scan_server_properties(instance_id, instance_path)
                
                # Auto-tag instance (ML-based tag suggestions)
                if self.enable_meta_tagging:
                    self._auto_tag_instance(instance_id)
            
            self._end_discovery_run('completed', stats)
            self.logger.info(f"✅ Discovery complete: {stats}")
        
        except Exception as e:
            self.logger.error(f"❌ Discovery failed: {e}", exc_info=True)
            self._end_discovery_run('failed')
    
    def _discover_instances(self) -> List[Dict]:
        """
        Discover all AMP instances in /home/amp/.ampdata/instances
        NO HARDCODING - dynamically scans folder
        """
        if not self.amp_base_dir.exists():
            self.logger.warning(f"⚠️  AMP base dir not found: {self.amp_base_dir}")
            return []
        
        discovered = []
        
        for instance_dir in self.amp_base_dir.iterdir():
            if not instance_dir.is_dir():
                continue
            
            # Check if it's a valid Minecraft instance
            minecraft_dir = instance_dir / 'Minecraft'
            if not minecraft_dir.exists():
                continue
            
            instance_info = {
                'name': instance_dir.name,
                'path': str(instance_dir),
                'platform': self._detect_platform(instance_dir),
                'minecraft_version': self._detect_minecraft_version(instance_dir),
                'server_name': self.server_name
            }
            
            discovered.append(instance_info)
            self._log_discovery_item('instance', instance_info['name'], str(instance_dir), 'discovered')
        
        return discovered
    
    def _discover_instance_plugins(self, instance_id: str, instance_path: Path) -> List[Dict]:
        """
        Discover all plugins in instance - NO HARDCODING
        Scans plugins/ folder and registers any JAR files
        """
        plugins_dir = instance_path / 'Minecraft' / 'plugins'
        if not plugins_dir.exists():
            return []
        
        discovered = []
        
        for jar_file in plugins_dir.glob('*.jar'):
            plugin_info = self._analyze_plugin_jar(jar_file)
            if not plugin_info:
                continue
            
            plugin_id = plugin_info['plugin_id']
            
            # Ensure plugin exists in registry
            self._register_plugin(plugin_info)
            
            # Register installation
            self._register_plugin_installation(instance_id, plugin_id, plugin_info, jar_file)
            
            discovered.append(plugin_info)
            self._log_discovery_item('plugin', plugin_id, str(jar_file), 'discovered')
        
        return discovered
    
    def _discover_instance_datapacks(self, instance_id: str, instance_path: Path) -> List[Dict]:
        """
        Discover all datapacks - NO HARDCODING
        Scans world/datapacks folders for all worlds
        """
        minecraft_dir = instance_path / 'Minecraft'
        discovered = []
        
        # Find all world folders
        for world_dir in minecraft_dir.iterdir():
            if not world_dir.is_dir():
                continue
            
            datapacks_dir = world_dir / 'datapacks'
            if not datapacks_dir.exists():
                continue
            
            world_name = world_dir.name
            
            # Scan datapacks in this world
            for datapack_item in datapacks_dir.iterdir():
                if datapack_item.name == 'bukkit':
                    continue  # Skip bukkit internal folder
                
                datapack_info = self._analyze_datapack(datapack_item, world_name)
                if not datapack_info:
                    continue
                
                datapack_id = datapack_info['datapack_id']
                
                # Ensure datapack exists in registry
                self._register_datapack(datapack_info)
                
                # Register installation
                self._register_datapack_installation(instance_id, datapack_id, world_name, datapack_info, datapack_item)
                
                discovered.append(datapack_info)
                self._log_discovery_item('datapack', datapack_id, str(datapack_item), 'discovered')
        
        return discovered
    
    def _analyze_plugin_jar(self, jar_path: Path) -> Optional[Dict]:
        """
        Extract metadata from plugin JAR file
        Reads plugin.yml or fabric.mod.json
        """
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                # Try Paper/Spigot plugin.yml
                if 'plugin.yml' in jar.namelist():
                    with jar.open('plugin.yml') as f:
                        plugin_yml = yaml.safe_load(f)
                    
                    return {
                        'plugin_id': self._normalize_plugin_id(plugin_yml.get('name', jar_path.stem)),
                        'plugin_name': plugin_yml.get('name', jar_path.stem),
                        'display_name': plugin_yml.get('name'),
                        'version': plugin_yml.get('version', 'unknown'),
                        'platform': 'paper',
                        'author': plugin_yml.get('author', plugin_yml.get('authors', ['Unknown'])[0] if isinstance(plugin_yml.get('authors'), list) else 'Unknown'),
                        'description': plugin_yml.get('description', ''),
                        'main_class': plugin_yml.get('main'),
                        'dependencies': plugin_yml.get('depend', []),
                        'soft_dependencies': plugin_yml.get('softdepend', [])
                    }
                
                # Try Fabric mod
                elif 'fabric.mod.json' in jar.namelist():
                    with jar.open('fabric.mod.json') as f:
                        fabric_json = json.load(f)
                    
                    return {
                        'plugin_id': self._normalize_plugin_id(fabric_json.get('id', jar_path.stem)),
                        'plugin_name': fabric_json.get('id'),
                        'display_name': fabric_json.get('name'),
                        'version': fabric_json.get('version', 'unknown'),
                        'platform': 'fabric',
                        'author': fabric_json.get('authors', [{'name': 'Unknown'}])[0].get('name') if isinstance(fabric_json.get('authors'), list) else fabric_json.get('authors', 'Unknown'),
                        'description': fabric_json.get('description', ''),
                        'dependencies': list(fabric_json.get('depends', {}).keys())
                    }
                
                # Unknown format - use filename
                else:
                    return {
                        'plugin_id': self._normalize_plugin_id(jar_path.stem),
                        'plugin_name': jar_path.stem,
                        'display_name': jar_path.stem,
                        'version': self._extract_version_from_filename(jar_path.stem),
                        'platform': 'unknown',
                        'author': 'Unknown',
                        'description': ''
                    }
        
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to analyze {jar_path.name}: {e}")
            return None
    
    def _analyze_datapack(self, datapack_path: Path, world_name: str) -> Optional[Dict]:
        """
        Extract metadata from datapack (ZIP or folder)
        Reads pack.mcmeta
        """
        try:
            # If it's a folder
            if datapack_path.is_dir():
                mcmeta_path = datapack_path / 'pack.mcmeta'
                if mcmeta_path.exists():
                    with open(mcmeta_path) as f:
                        mcmeta = json.load(f)
                    
                    return {
                        'datapack_id': self._normalize_plugin_id(datapack_path.name),
                        'datapack_name': datapack_path.name,
                        'display_name': datapack_path.name,
                        'version': 'unknown',
                        'description': mcmeta.get('pack', {}).get('description', '')
                    }
            
            # If it's a ZIP
            elif datapack_path.suffix == '.zip':
                with zipfile.ZipFile(datapack_path) as zf:
                    if 'pack.mcmeta' in zf.namelist():
                        with zf.open('pack.mcmeta') as f:
                            mcmeta = json.load(f)
                        
                        return {
                            'datapack_id': self._normalize_plugin_id(datapack_path.stem),
                            'datapack_name': datapack_path.stem,
                            'display_name': datapack_path.stem,
                            'version': self._extract_version_from_filename(datapack_path.stem),
                            'description': mcmeta.get('pack', {}).get('description', '')
                        }
            
            return None
        
        except Exception as e:
            self.logger.warning(f"⚠️  Failed to analyze datapack {datapack_path.name}: {e}")
            return None
    
    def _normalize_plugin_id(self, name: str) -> str:
        """Convert plugin name to normalized ID (lowercase, no spaces)"""
        return re.sub(r'[^a-z0-9_-]', '', name.lower().replace(' ', '_'))
    
    def _extract_version_from_filename(self, filename: str) -> str:
        """Extract version from filename like PluginName-1.2.3.jar"""
        match = re.search(r'[-_]v?(\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?)', filename)
        return match.group(1) if match else 'unknown'
    
    def _detect_platform(self, instance_path: Path) -> str:
        """Detect platform (Paper, Fabric, Forge) from instance files"""
        minecraft_dir = instance_path / 'Minecraft'
        
        # Check for platform-specific files
        if (minecraft_dir / 'paper.yml').exists():
            return 'paper'
        elif (minecraft_dir / 'fabric-server-launcher.properties').exists():
            return 'fabric'
        elif (minecraft_dir / 'forge-installer.jar').exists():
            return 'forge'
        else:
            return 'vanilla'
    
    def _detect_minecraft_version(self, instance_path: Path) -> str:
        """Detect Minecraft version from server files"""
        # Try to read from server jar name or version.json
        minecraft_dir = instance_path / 'Minecraft'
        
        # Check server jar pattern
        for jar in minecraft_dir.glob('*.jar'):
            if 'server' in jar.name.lower():
                version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', jar.name)
                if version_match:
                    return version_match.group(1)
        
        return 'unknown'
    
    # Continued in next message due to length...
