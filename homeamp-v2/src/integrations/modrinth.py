"""HomeAMP V2.0 - Modrinth API client."""

import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class ModrinthClient:
    """Client for interacting with Modrinth API."""

    BASE_URL = "https://api.modrinth.com/v2"

    def __init__(self, timeout: int = 30):
        """Initialize Modrinth client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def search_projects(
        self,
        query: str,
        facets: Optional[List[List[str]]] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """Search for projects on Modrinth.

        Args:
            query: Search query
            facets: Search facets for filtering
            limit: Maximum number of results

        Returns:
            List of project search results
        """
        try:
            params = {
                "query": query,
                "limit": limit,
            }

            if facets:
                params["facets"] = str(facets)

            response = self.client.get(f"{self.BASE_URL}/search", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("hits", [])

        except httpx.HTTPError as e:
            logger.error(f"Modrinth search error: {e}")
            return []

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project details by ID or slug.

        Args:
            project_id: Project ID or slug

        Returns:
            Project details or None
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/project/{project_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Modrinth get project error: {e}")
            return None

    def get_project_versions(
        self,
        project_id: str,
        game_versions: Optional[List[str]] = None,
        loaders: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Get versions for a project.

        Args:
            project_id: Project ID or slug
            game_versions: Filter by Minecraft versions
            loaders: Filter by mod loaders (paper, spigot, etc.)

        Returns:
            List of version objects
        """
        try:
            params = {}
            if game_versions:
                params["game_versions"] = str(game_versions)
            if loaders:
                params["loaders"] = str(loaders)

            response = self.client.get(f"{self.BASE_URL}/project/{project_id}/version", params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Modrinth get versions error: {e}")
            return []

    def get_latest_version(
        self,
        project_id: str,
        game_version: Optional[str] = None,
        loader: Optional[str] = None,
    ) -> Optional[Dict]:
        """Get latest version for a project.

        Args:
            project_id: Project ID or slug
            game_version: Minecraft version filter
            loader: Mod loader filter

        Returns:
            Latest version object or None
        """
        game_versions = [game_version] if game_version else None
        loaders = [loader] if loader else None

        versions = self.get_project_versions(project_id, game_versions, loaders)

        if not versions:
            return None

        # Versions are returned newest first
        return versions[0]

    def get_version_files(self, version_id: str) -> List[Dict]:
        """Get files for a specific version.

        Args:
            version_id: Version ID

        Returns:
            List of file objects
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/version/{version_id}")
            response.raise_for_status()

            version = response.json()
            return version.get("files", [])

        except httpx.HTTPError as e:
            logger.error(f"Modrinth get version files error: {e}")
            return []

    def download_file(self, url: str, output_path: str) -> bool:
        """Download a file from Modrinth.

        Args:
            url: File download URL
            output_path: Local output path

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.client.stream("GET", url) as response:
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)

            logger.info(f"Downloaded file to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Download error: {e}")
            return False

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
