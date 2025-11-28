"""HomeAMP V2.0 - Discovery service for scanning instances."""

import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from homeamp_v2.core.exceptions import DiscoveryError
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class DiscoveryService:
    """Service for discovering instances, plugins, datapacks, and configurations."""

    def __init__(self, uow: UnitOfWork):
        """Initialize discovery service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow

    def scan_instance(self, instance_id: int) -> Dict:
        """Scan a single instance for plugins, datapacks, and configs.

        Args:
            instance_id: Instance ID to scan

        Returns:
            Discovery results dictionary

        Raises:
            DiscoveryError: If scan fails
        """
        try:
            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise DiscoveryError(f"Instance {instance_id} not found")

            logger.info(f"Starting discovery scan for instance: {instance.name}")

            results = {
                "instance_id": instance_id,
                "instance_name": instance.name,
                "scan_time": datetime.utcnow().isoformat(),
                "plugins": self._scan_plugins(instance),
                "datapacks": self._scan_datapacks(instance),
                "configs": self._scan_configs(instance),
                "worlds": self._scan_worlds(instance),
            }

            logger.info(
                f"Discovery complete: {len(results['plugins'])} plugins, "
                f"{len(results['datapacks'])} datapacks, "
                f"{len(results['configs'])} configs, "
                f"{len(results['worlds'])} worlds"
            )

            return results

        except Exception as e:
            logger.error(f"Discovery scan failed for instance {instance_id}: {e}")
            raise DiscoveryError(f"Discovery scan failed: {e}") from e

    def _scan_plugins(self, instance) -> List[Dict]:
        """Scan plugins directory.

        Args:
            instance: Instance model

        Returns:
            List of discovered plugins
        """
        plugins = []
        plugins_dir = Path(instance.base_path) / "plugins"

        if not plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {plugins_dir}")
            return plugins

        for jar_file in plugins_dir.glob("*.jar"):
            try:
                plugin_info = self._extract_plugin_info(jar_file)
                if plugin_info:
                    plugins.append(plugin_info)
            except Exception as e:
                logger.warning(f"Failed to extract info from {jar_file.name}: {e}")

        return plugins

    def _extract_plugin_info(self, jar_path: Path) -> Optional[Dict]:
        """Extract plugin information from JAR file.

        Args:
            jar_path: Path to JAR file

        Returns:
            Plugin info dictionary or None
        """
        import zipfile
        
        # Try to parse JAR file for plugin.yml or paper-plugin.yml
        try:
            with zipfile.ZipFile(jar_path, 'r') as jar:
                # Try paper-plugin.yml first (newer format)
                plugin_yml = None
                if 'paper-plugin.yml' in jar.namelist():
                    plugin_yml = yaml.safe_load(jar.read('paper-plugin.yml'))
                elif 'plugin.yml' in jar.namelist():
                    plugin_yml = yaml.safe_load(jar.read('plugin.yml'))
                
                if plugin_yml:
                    return {
                        "name": plugin_yml.get('name', jar_path.stem),
                        "version": plugin_yml.get('version', 'unknown'),
                        "file_name": jar_path.name,
                        "file_size": jar_path.stat().st_size,
                        "modified_time": datetime.fromtimestamp(jar_path.stat().st_mtime).isoformat(),
                        "description": plugin_yml.get('description'),
                        "author": plugin_yml.get('author') or plugin_yml.get('authors', [None])[0] if isinstance(plugin_yml.get('authors'), list) else None,
                        "website": plugin_yml.get('website'),
                        "main_class": plugin_yml.get('main'),
                    }
        except (zipfile.BadZipFile, KeyError, yaml.YAMLError) as e:
            logger.debug(f"Could not parse {jar_path.name} as plugin JAR: {e}")
        
        # Fallback: extract from filename
        name = jar_path.stem
        version = "unknown"

        # Try to extract version from common naming patterns
        if "-" in name:
            parts = name.split("-")
            if len(parts) >= 2:
                # Common patterns: PluginName-1.0.0.jar, plugin-name-v1.0.jar
                potential_version = parts[-1]
                if any(char.isdigit() for char in potential_version):
                    version = potential_version.lstrip("v")
                    name = "-".join(parts[:-1])

        return {
            "name": name,
            "version": version,
            "file_name": jar_path.name,
            "file_size": jar_path.stat().st_size,
            "modified_time": datetime.fromtimestamp(jar_path.stat().st_mtime).isoformat(),
        }

    def _scan_datapacks(self, instance) -> List[Dict]:
        """Scan datapacks in world directories.

        Args:
            instance: Instance model

        Returns:
            List of discovered datapacks
        """
        datapacks = []
        base_path = Path(instance.base_path)

        # Scan common world directories
        world_dirs = ["world", "world_nether", "world_the_end"]

        for world_name in world_dirs:
            datapacks_dir = base_path / world_name / "datapacks"
            if datapacks_dir.exists():
                for item in datapacks_dir.iterdir():
                    if item.is_dir() or item.suffix == ".zip":
                        try:
                            datapack_info = self._extract_datapack_info(item, world_name)
                            if datapack_info:
                                datapacks.append(datapack_info)
                        except Exception as e:
                            logger.warning(f"Failed to extract datapack info from {item.name}: {e}")

        return datapacks

    def _extract_datapack_info(self, datapack_path: Path, world_name: str) -> Optional[Dict]:
        """Extract datapack information.

        Args:
            datapack_path: Path to datapack
            world_name: World name

        Returns:
            Datapack info dictionary or None
        """
        pack_mcmeta = datapack_path / "pack.mcmeta" if datapack_path.is_dir() else None

        name = datapack_path.stem
        description = "Unknown"

        # Try to read pack.mcmeta for metadata
        if pack_mcmeta and pack_mcmeta.exists():
            try:
                with open(pack_mcmeta, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    description = metadata.get("pack", {}).get("description", "Unknown")
            except Exception as e:
                logger.debug(f"Failed to read pack.mcmeta: {e}")

        return {
            "name": name,
            "world": world_name,
            "description": description,
            "type": "directory" if datapack_path.is_dir() else "zip",
            "path": str(datapack_path),
        }

    def _scan_configs(self, instance) -> List[Dict]:
        """Scan plugin configuration files.

        Args:
            instance: Instance model

        Returns:
            List of discovered config files
        """
        configs = []
        plugins_dir = Path(instance.base_path) / "plugins"

        if not plugins_dir.exists():
            return configs

        # Scan for common config file patterns
        config_patterns = ["*.yml", "*.yaml", "*.json", "*.conf", "*.properties"]

        for pattern in config_patterns:
            for config_file in plugins_dir.rglob(pattern):
                # Skip JAR files and other non-config files
                if config_file.suffix == ".jar":
                    continue

                # Determine plugin name from directory structure
                try:
                    relative = config_file.relative_to(plugins_dir)
                    plugin_name = relative.parts[0] if len(relative.parts) > 1 else "server"

                    configs.append(
                        {
                            "plugin_name": plugin_name,
                            "file_name": config_file.name,
                            "file_path": str(relative),
                            "file_size": config_file.stat().st_size,
                            "modified_time": datetime.fromtimestamp(config_file.stat().st_mtime).isoformat(),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to process config file {config_file}: {e}")

        return configs

    def _scan_worlds(self, instance) -> List[Dict]:
        """Scan world directories.

        Args:
            instance: Instance model

        Returns:
            List of discovered worlds
        """
        worlds = []
        base_path = Path(instance.base_path)

        # Check for level.dat to identify world directories
        for item in base_path.iterdir():
            if item.is_dir():
                level_dat = item / "level.dat"
                if level_dat.exists():
                    try:
                        worlds.append(
                            {
                                "name": item.name,
                                "path": str(item.relative_to(base_path)),
                                "size": sum(f.stat().st_size for f in item.rglob("*") if f.is_file()),
                            }
                        )
                    except Exception as e:
                        logger.warning(f"Failed to process world {item.name}: {e}")

        return worlds

    def scan_all_instances(self) -> Dict:
        """Scan all active instances.

        Returns:
            Discovery results for all instances

        Raises:
            DiscoveryError: If scan fails
        """
        try:
            instances = self.uow.instances.get_active()
            logger.info(f"Starting discovery scan for {len(instances)} active instances")

            results = {"scan_time": datetime.utcnow().isoformat(), "instances": []}

            for instance in instances:
                try:
                    instance_result = self.scan_instance(instance.id)
                    results["instances"].append(instance_result)
                except Exception as e:
                    logger.error(f"Failed to scan instance {instance.name}: {e}")
                    results["instances"].append(
                        {
                            "instance_id": instance.id,
                            "instance_name": instance.name,
                            "error": str(e),
                        }
                    )

            logger.info(f"Discovery scan complete for {len(instances)} instances")
            return results

        except Exception as e:
            logger.error(f"Discovery scan failed: {e}")
            raise DiscoveryError(f"Discovery scan failed: {e}") from e
