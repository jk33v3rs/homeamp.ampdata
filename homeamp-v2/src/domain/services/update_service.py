"""HomeAMP V2.0 - Update service for checking and managing updates."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from homeamp_v2.core.exceptions import UpdateCheckError
from homeamp_v2.data.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class UpdateService:
    """Service for checking and managing plugin/datapack updates."""

    def __init__(self, uow: UnitOfWork):
        """Initialize update service.

        Args:
            uow: Unit of Work for database access
        """
        self.uow = uow
        self.http_client = httpx.Client(timeout=30.0)

    def check_plugin_updates(self, plugin_id: Optional[int] = None) -> List[Dict]:
        """Check for plugin updates.

        Args:
            plugin_id: Optional specific plugin ID

        Returns:
            List of available updates

        Raises:
            UpdateCheckError: If update check fails
        """
        try:
            if plugin_id:
                plugins = [self.uow.plugins.get_by_id(plugin_id)]
                if not plugins[0]:
                    raise UpdateCheckError(f"Plugin {plugin_id} not found")
            else:
                plugins = self.uow.plugins.get_all()

            logger.info(f"Checking updates for {len(plugins)} plugins")

            updates = []
            for plugin in plugins:
                try:
                    update_info = self._check_plugin_update(plugin)
                    if update_info:
                        updates.append(update_info)
                except Exception as e:
                    logger.warning(f"Failed to check updates for plugin {plugin.name}: {e}")

            logger.info(f"Found {len(updates)} plugin updates available")
            return updates

        except Exception as e:
            logger.error(f"Plugin update check failed: {e}")
            raise UpdateCheckError(f"Plugin update check failed: {e}") from e

    def _check_plugin_update(self, plugin) -> Optional[Dict]:
        """Check for updates for a single plugin.

        Args:
            plugin: Plugin model

        Returns:
            Update info dictionary or None if no update
        """
        # Get update sources for this plugin from database
        from homeamp_v2.data.models.plugin import PluginUpdateSource
        from sqlalchemy import select
        
        stmt = select(PluginUpdateSource).where(PluginUpdateSource.plugin_id == plugin.id)
        result = self.uow.session.execute(stmt)
        update_sources = result.scalars().all()
        
        # Try each update source
        for source in update_sources:
            if source.source_type == "modrinth":
                update_info = self._check_modrinth_update_by_id(plugin, source.source_identifier)
                if update_info:
                    return update_info
            elif source.source_type == "hangar":
                update_info = self._check_hangar_update_by_id(plugin, source.source_identifier)
                if update_info:
                    return update_info
            elif source.source_type == "github":
                update_info = self._check_github_update_by_repo(plugin, source.source_identifier)
                if update_info:
                    return update_info
            elif source.source_type == "spigot":
                update_info = self._check_spigot_update_by_id(plugin, source.source_identifier)
                if update_info:
                    return update_info
        
        # Fallback: try to detect from plugin homepage URL
        if not plugin.homepage_url:
            return None

        # Detect source type from URL
        if "modrinth.com" in plugin.homepage_url:
            return self._check_modrinth_update(plugin)
        elif "hangar.papermc.io" in plugin.homepage_url:
            return self._check_hangar_update(plugin)
        elif "github.com" in plugin.homepage_url:
            return self._check_github_update(plugin)
        elif "spigotmc.org" in plugin.homepage_url:
            return self._check_spigot_update(plugin)

        return None

    def _check_modrinth_update(self, plugin) -> Optional[Dict]:
        """Check Modrinth for plugin update."""
        try:
            # Extract project ID from URL
            # Example: https://modrinth.com/plugin/project-id
            project_id = plugin.homepage_url.rstrip("/").split("/")[-1]
            return self._check_modrinth_update_by_id(plugin, project_id)
            
        except Exception as e:
            logger.debug(f"Modrinth update check failed for {plugin.name}: {e}")

        return None
    
    def _check_modrinth_update_by_id(self, plugin, project_id: str) -> Optional[Dict]:
        """Check Modrinth by project ID."""
        try:
            # Query Modrinth API
            url = f"https://api.modrinth.com/v2/project/{project_id}/version"
            response = self.http_client.get(url)
            response.raise_for_status()

            versions = response.json()
            if not versions:
                return None

            # Get latest version
            latest = versions[0]
            latest_version = latest["version_number"]

            # Compare with current version
            if latest_version != plugin.latest_version:
                return {
                    "plugin_id": plugin.id,
                    "plugin_name": plugin.name,
                    "current_version": plugin.latest_version,
                    "latest_version": latest_version,
                    "source": "modrinth",
                    "download_url": latest["files"][0]["url"] if latest.get("files") else None,
                    "changelog": latest.get("changelog", ""),
                }

        except Exception as e:
            logger.debug(f"Modrinth update check failed for {plugin.name}: {e}")

        return None

    def _check_hangar_update(self, plugin) -> Optional[Dict]:
        """Check Hangar for plugin update."""
        try:
            # Extract slug from URL
            # Example: https://hangar.papermc.io/author/project
            parts = plugin.homepage_url.rstrip("/").split("/")
            if len(parts) < 2:
                return None
            
            author = parts[-2]
            project = parts[-1]
            slug = f"{author}/{project}"
            
            return self._check_hangar_update_by_id(plugin, slug)
            
        except Exception as e:
            logger.debug(f"Hangar update check failed for {plugin.name}: {e}")
        
        return None
    
    def _check_hangar_update_by_id(self, plugin, slug: str) -> Optional[Dict]:
        """Check Hangar by project slug."""
        try:
            # Get latest version
            versions_url = f"https://hangar.papermc.io/api/v1/projects/{slug}/versions"
            versions_response = self.http_client.get(versions_url)
            versions_response.raise_for_status()
            
            versions = versions_response.json()
            if not versions or "result" not in versions:
                return None
            
            latest = versions["result"][0] if versions["result"] else None
            if not latest:
                return None
            
            latest_version = latest["name"]
            
            # Compare with current version
            if latest_version != plugin.latest_version:
                return {
                    "plugin_id": plugin.id,
                    "plugin_name": plugin.name,
                    "current_version": plugin.latest_version,
                    "latest_version": latest_version,
                    "source": "hangar",
                    "download_url": latest.get("downloads", {}).get("PAPER", {}).get("downloadUrl"),
                    "changelog": latest.get("description", ""),
                }
        
        except Exception as e:
            logger.debug(f"Hangar update check failed for {plugin.name} ({slug}): {e}")
        
        return None

    def _check_github_update(self, plugin) -> Optional[Dict]:
        """Check GitHub releases for plugin update."""
        try:
            # Extract owner/repo from URL
            # Example: https://github.com/owner/repo
            parts = plugin.homepage_url.rstrip("/").split("/")
            if len(parts) < 2:
                return None

            owner = parts[-2]
            repo = parts[-1]
            repo_slug = f"{owner}/{repo}"
            
            return self._check_github_update_by_repo(plugin, repo_slug)

        except Exception as e:
            logger.debug(f"GitHub update check failed for {plugin.name}: {e}")

        return None
    
    def _check_github_update_by_repo(self, plugin, repo_slug: str) -> Optional[Dict]:
        """Check GitHub by repository slug."""
        try:
            # Query GitHub API
            url = f"https://api.github.com/repos/{repo_slug}/releases/latest"
            response = self.http_client.get(
                url, headers={"Accept": "application/vnd.github.v3+json"}
            )
            response.raise_for_status()

            release = response.json()
            latest_version = release["tag_name"].lstrip("v")

            # Compare with current version
            if latest_version != plugin.latest_version:
                # Find JAR asset
                download_url = None
                for asset in release.get("assets", []):
                    if asset["name"].endswith(".jar"):
                        download_url = asset["browser_download_url"]
                        break

                return {
                    "plugin_id": plugin.id,
                    "plugin_name": plugin.name,
                    "current_version": plugin.latest_version,
                    "latest_version": latest_version,
                    "source": "github",
                    "download_url": download_url,
                    "changelog": release.get("body", ""),
                }

        except Exception as e:
            logger.debug(f"GitHub update check failed for {plugin.name}: {e}")

        return None

    def _check_spigot_update(self, plugin) -> Optional[Dict]:
        """Check SpigotMC for plugin update."""
        try:
            # Extract resource ID from URL
            # Example: https://www.spigotmc.org/resources/plugin-name.12345/
            parts = plugin.homepage_url.rstrip("/").split(".")
            if len(parts) < 2:
                return None
            
            resource_id = parts[-1].split("/")[0]
            return self._check_spigot_update_by_id(plugin, resource_id)
            
        except Exception as e:
            logger.debug(f"Spigot update check failed for {plugin.name}: {e}")
        
        return None
    
    def _check_spigot_update_by_id(self, plugin, resource_id: str) -> Optional[Dict]:
        """Check Spigot by resource ID."""
        try:
            # Query Spiget API (unofficial Spigot API)
            url = f"https://api.spiget.org/v2/resources/{resource_id}"
            response = self.http_client.get(url)
            response.raise_for_status()
            
            resource = response.json()
            
            # Get version info
            versions_url = f"https://api.spiget.org/v2/resources/{resource_id}/versions/latest"
            version_response = self.http_client.get(versions_url)
            version_response.raise_for_status()
            
            latest_version_data = version_response.json()
            latest_version = latest_version_data.get("name", resource.get("version", {}).get("name", "unknown"))
            
            # Compare with current version
            if latest_version != plugin.latest_version:
                return {
                    "plugin_id": plugin.id,
                    "plugin_name": plugin.name,
                    "current_version": plugin.latest_version,
                    "latest_version": latest_version,
                    "source": "spigot",
                    "download_url": f"https://www.spigotmc.org/resources/{resource_id}/download",
                    "changelog": resource.get("description", ""),
                }
        
        except Exception as e:
            logger.debug(f"Spigot update check failed for {plugin.name} (resource {resource_id}): {e}")
        
        return None

    def queue_plugin_update(
        self, plugin_id: int, instance_id: int, target_version: str, auto_update: bool = False
    ) -> int:
        """Queue a plugin update.

        Args:
            plugin_id: Plugin ID
            instance_id: Instance ID
            target_version: Target version
            auto_update: Whether to auto-update

        Returns:
            Update queue ID

        Raises:
            UpdateCheckError: If queueing fails
        """
        try:
            plugin = self.uow.plugins.get_by_id(plugin_id)
            if not plugin:
                raise UpdateCheckError(f"Plugin {plugin_id} not found")

            instance = self.uow.instances.get_by_id(instance_id)
            if not instance:
                raise UpdateCheckError(f"Instance {instance_id} not found")

            # Create PluginUpdateQueue entry
            from homeamp_v2.data.models.plugin import PluginUpdateQueue
            
            queue_entry = PluginUpdateQueue(
                plugin_id=plugin_id,
                instance_id=instance_id,
                current_version=plugin.latest_version,
                target_version=target_version,
                status="pending",
                auto_update=auto_update,
                queued_at=datetime.utcnow()
            )
            self.uow.session.add(queue_entry)
            
            logger.info(
                f"Queued plugin update: {plugin.name} to {target_version} "
                f"for instance {instance.name} (auto={auto_update})"
            )

            self.uow.commit()
            return queue_entry.id

        except Exception as e:
            self.uow.rollback()
            logger.error(f"Failed to queue plugin update: {e}")
            raise UpdateCheckError(f"Failed to queue plugin update: {e}") from e

    def check_datapack_updates(self, datapack_id: Optional[int] = None) -> List[Dict]:
        """Check for datapack updates.

        Args:
            datapack_id: Optional specific datapack ID

        Returns:
            List of available updates
        """
        updates = []
        
        try:
            from homeamp_v2.data.models.datapack import Datapack, DatapackVersion
            from sqlalchemy import select
            
            # Get datapacks to check
            if datapack_id:
                stmt = select(Datapack).where(Datapack.id == datapack_id)
            else:
                stmt = select(Datapack)
            
            result = self.uow.session.execute(stmt)
            datapacks = result.scalars().all()
            
            for datapack in datapacks:
                # Check if datapack has update source
                if not datapack.source_url:
                    continue
                
                # Query for newer versions
                version_stmt = select(DatapackVersion).where(
                    DatapackVersion.datapack_id == datapack.id
                ).order_by(DatapackVersion.released_at.desc()).limit(1)
                
                version_result = self.uow.session.execute(version_stmt)
                latest_version = version_result.scalar_one_or_none()
                
                if latest_version and latest_version.version_string != datapack.latest_version:
                    updates.append({
                        "datapack_id": datapack.id,
                        "datapack_name": datapack.name,
                        "current_version": datapack.latest_version,
                        "latest_version": latest_version.version_string,
                        "download_url": latest_version.download_url,
                    })
            
            logger.info(f"Datapack update check complete: {len(updates)} updates found")
            
        except Exception as e:
            logger.error(f"Datapack update check failed: {e}")
        
        return updates

    def get_update_history(self, instance_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Get update history.

        Args:
            instance_id: Optional instance ID filter
            limit: Maximum results

        Returns:
            List of update history entries
        """
        from homeamp_v2.data.models.deployment import DeploymentHistory
        from sqlalchemy import select
        
        try:
            # Query deployment history for update actions
            stmt = select(DeploymentHistory).where(
                DeploymentHistory.action == "update"
            )
            
            if instance_id:
                stmt = stmt.where(DeploymentHistory.instance_id == instance_id)
            
            stmt = stmt.order_by(DeploymentHistory.completed_at.desc()).limit(limit)
            
            result = self.uow.session.execute(stmt)
            histories = result.scalars().all()
            
            # Convert to dictionaries
            history_list = []
            for history in histories:
                history_list.append({
                    "id": history.id,
                    "instance_id": history.instance_id,
                    "deployment_type": history.deployment_type,
                    "action": history.action,
                    "status": history.status,
                    "executed_by": history.executed_by,
                    "completed_at": history.completed_at.isoformat(),
                    "duration_ms": history.duration_ms,
                })
            
            logger.info(f"Retrieved {len(history_list)} update history entries")
            return history_list
            
        except Exception as e:
            logger.error(f"Failed to get update history: {e}")
            return []
