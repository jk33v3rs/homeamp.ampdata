"""HomeAMP V2.0 - GitHub API client."""

import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for interacting with GitHub API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None, timeout: int = 30):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token (optional, but recommended)
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        headers = {"Accept": "application/vnd.github.v3+json"}

        if token:
            headers["Authorization"] = f"token {token}"

        self.client = httpx.Client(timeout=timeout, headers=headers)

    def get_repository(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository details or None
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"GitHub get repository error: {e}")
            return None

    def get_releases(self, owner: str, repo: str, per_page: int = 10) -> List[Dict]:
        """Get releases for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Number of results per page

        Returns:
            List of release objects
        """
        try:
            params = {"per_page": per_page}
            response = self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/releases", params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"GitHub get releases error: {e}")
            return []

    def get_latest_release(self, owner: str, repo: str) -> Optional[Dict]:
        """Get latest release for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Latest release object or None
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/releases/latest")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"GitHub get latest release error: {e}")
            return None

    def get_release_by_tag(self, owner: str, repo: str, tag: str) -> Optional[Dict]:
        """Get a specific release by tag name.

        Args:
            owner: Repository owner
            repo: Repository name
            tag: Tag name

        Returns:
            Release object or None
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/releases/tags/{tag}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"GitHub get release by tag error: {e}")
            return None

    def get_release_assets(self, owner: str, repo: str, release_id: int) -> List[Dict]:
        """Get assets for a release.

        Args:
            owner: Repository owner
            repo: Repository name
            release_id: Release ID

        Returns:
            List of asset objects
        """
        try:
            response = self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/releases/{release_id}/assets")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"GitHub get release assets error: {e}")
            return []

    def download_asset(self, asset_url: str, output_path: str) -> bool:
        """Download a release asset.

        Args:
            asset_url: Asset download URL
            output_path: Local output path

        Returns:
            True if successful, False otherwise
        """
        try:
            # GitHub requires specific Accept header for asset downloads
            headers = {"Accept": "application/octet-stream"}

            with self.client.stream("GET", asset_url, headers=headers, follow_redirects=True) as response:
                response.raise_for_status()

                with open(output_path, "wb") as f:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)

            logger.info(f"Downloaded asset to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Download error: {e}")
            return False

    def get_commits(
        self,
        owner: str,
        repo: str,
        sha: Optional[str] = None,
        per_page: int = 10,
    ) -> List[Dict]:
        """Get commits for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            sha: SHA or branch to start listing commits from
            per_page: Number of results per page

        Returns:
            List of commit objects
        """
        try:
            params = {"per_page": per_page}
            if sha:
                params["sha"] = sha

            response = self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/commits", params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"GitHub get commits error: {e}")
            return []

    def get_tags(self, owner: str, repo: str, per_page: int = 10) -> List[Dict]:
        """Get tags for a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            per_page: Number of results per page

        Returns:
            List of tag objects
        """
        try:
            params = {"per_page": per_page}
            response = self.client.get(f"{self.BASE_URL}/repos/{owner}/{repo}/tags", params=params)
            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"GitHub get tags error: {e}")
            return []

    def close(self):
        """Close HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
