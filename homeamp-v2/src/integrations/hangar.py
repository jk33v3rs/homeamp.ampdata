"""HomeAMP V2.0 - Hangar API client."""

import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class HangarClient:
    """Client for interacting with Hangar API (PaperMC plugin repository)."""

    BASE_URL = "https://hangar.papermc.io/api/v1"

    def __init__(self, timeout: int = 30):
        """Initialize Hangar client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

    def search_projects(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict]:
        """Search for projects on Hangar.

        Args:
            query: Search query
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of project search results
        """
        try:
            params = {
                "q": query,
                "limit": limit,
                "offset": offset,
            }

            response = self.client.get(f"{self.BASE_URL}/projects", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("result", [])

        except httpx.HTTPError as e:
            logger.error(f"Hangar search error: {e}")
            return []

    def get_project(self, author: str, slug: str) -> Optional[Dict]:
        """Get project details.

        Args:
            author: Project author username
            slug: Project slug

        Returns:
            Project details or None
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/projects/{author}/{slug}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Hangar get project error: {e}")
            return None

    def get_project_versions(
        self,
        author: str,
        slug: str,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict]:
        """Get versions for a project.

        Args:
            author: Project author username
            slug: Project slug
            limit: Maximum number of results
            offset: Result offset for pagination

        Returns:
            List of version objects
        """
        try:
            params = {
                "limit": limit,
                "offset": offset,
            }

            response = self.client.get(f"{self.BASE_URL}/projects/{author}/{slug}/versions", params=params)
            response.raise_for_status()

            data = response.json()
            return data.get("result", [])

        except httpx.HTTPError as e:
            logger.error(f"Hangar get versions error: {e}")
            return []

    def get_latest_version(
        self,
        author: str,
        slug: str,
        platform: str = "PAPER",
    ) -> Optional[Dict]:
        """Get latest version for a project.

        Args:
            author: Project author username
            slug: Project slug
            platform: Platform filter (PAPER, WATERFALL, VELOCITY)

        Returns:
            Latest version object or None
        """
        versions = self.get_project_versions(author, slug, limit=1)

        if not versions:
            return None

        # Filter by platform if needed
        for version in versions:
            if platform in version.get("platformDependencies", {}):
                return version

        return versions[0] if versions else None

    def get_version_details(
        self,
        author: str,
        slug: str,
        version_name: str,
    ) -> Optional[Dict]:
        """Get detailed information about a specific version.

        Args:
            author: Project author username
            slug: Project slug
            version_name: Version name

        Returns:
            Version details or None
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/projects/{author}/{slug}/versions/{version_name}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Hangar get version details error: {e}")
            return None

    def download_version(
        self,
        author: str,
        slug: str,
        version_name: str,
        platform: str,
        output_path: str,
    ) -> bool:
        """Download a version file.

        Args:
            author: Project author username
            slug: Project slug
            version_name: Version name
            platform: Platform (PAPER, WATERFALL, VELOCITY)
            output_path: Local output path

        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.BASE_URL}/projects/{author}/{slug}/versions/{version_name}/{platform}/download"

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
