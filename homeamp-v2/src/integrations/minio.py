"""HomeAMP V2.0 - MinIO/S3 integration for map tile storage."""

import logging
from pathlib import Path
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)


class MinIOClient:
    """Client for MinIO S3-compatible object storage.
    
    Used for storing and retrieving Pl3xMap tiles, backups, and other assets.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = True,
        region: str = "us-east-1",
    ):
        """Initialize MinIO client.
        
        Args:
            endpoint: MinIO server endpoint (e.g., "minio.example.com:9000")
            access_key: MinIO access key
            secret_key: MinIO secret key
            secure: Use HTTPS (default: True)
            region: S3 region (default: "us-east-1")
        """
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.region = region
        self.base_url = f"{'https' if secure else 'http'}://{endpoint}"
        
        self._client: Optional[httpx.Client] = None
        
        logger.info(f"MinIO client initialized for {endpoint}")

    def __enter__(self):
        """Context manager entry."""
        self._client = httpx.Client(timeout=30.0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            self._client.close()

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if not self._client:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def bucket_exists(self, bucket_name: str) -> bool:
        """Check if bucket exists.
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            True if bucket exists
        """
        try:
            response = self.client.head(
                f"{self.base_url}/{bucket_name}",
                auth=(self.access_key, self.secret_key),
            )
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Bucket check failed: {e}")
            return False

    def create_bucket(self, bucket_name: str) -> bool:
        """Create a new bucket.
        
        Args:
            bucket_name: Bucket name
            
        Returns:
            True if bucket was created
        """
        try:
            response = self.client.put(
                f"{self.base_url}/{bucket_name}",
                auth=(self.access_key, self.secret_key),
            )
            
            if response.status_code in (200, 201):
                logger.info(f"Created bucket: {bucket_name}")
                return True
            else:
                logger.error(f"Failed to create bucket: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating bucket: {e}")
            return False

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: Path,
        content_type: Optional[str] = None,
    ) -> bool:
        """Upload a file to MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name in bucket (e.g., "maps/bent01/tiles/0/0/0.png")
            file_path: Local file path to upload
            content_type: MIME type (auto-detected if None)
            
        Returns:
            True if upload succeeded
        """
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False

        # Auto-detect content type
        if not content_type:
            content_type = self._detect_content_type(file_path)

        try:
            with open(file_path, "rb") as f:
                response = self.client.put(
                    f"{self.base_url}/{bucket_name}/{object_name}",
                    content=f.read(),
                    headers={"Content-Type": content_type},
                    auth=(self.access_key, self.secret_key),
                )

            if response.status_code in (200, 201):
                logger.debug(f"Uploaded {file_path.name} → {bucket_name}/{object_name}")
                return True
            else:
                logger.error(f"Upload failed: {response.status_code} {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: Path,
    ) -> bool:
        """Download a file from MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name in bucket
            file_path: Local file path to save to
            
        Returns:
            True if download succeeded
        """
        try:
            response = self.client.get(
                f"{self.base_url}/{bucket_name}/{object_name}",
                auth=(self.access_key, self.secret_key),
            )

            if response.status_code == 200:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                logger.debug(f"Downloaded {bucket_name}/{object_name} → {file_path}")
                return True
            else:
                logger.error(f"Download failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        recursive: bool = False,
    ) -> List[dict]:
        """List objects in a bucket.
        
        Args:
            bucket_name: Bucket name
            prefix: Filter by prefix (e.g., "public/bent01/")
            recursive: List recursively
            
        Returns:
            List of object metadata dictionaries
        """
        try:
            params = {}
            if prefix:
                params["prefix"] = prefix
            if not recursive:
                params["delimiter"] = "/"

            response = self.client.get(
                f"{self.base_url}/{bucket_name}",
                params=params,
                auth=(self.access_key, self.secret_key),
            )

            if response.status_code == 200:
                # Parse XML response
                import xml.etree.ElementTree as ET
                
                objects = []
                
                try:
                    root = ET.fromstring(response.content)
                    
                    # Handle XML namespaces
                    ns = {'s3': 'http://s3.amazonaws.com/doc/2006-03-01/'}
                    
                    # Parse Contents elements (files)
                    for content in root.findall('.//s3:Contents', ns) or root.findall('.//Contents'):
                        key_elem = content.find('s3:Key', ns) or content.find('Key')
                        size_elem = content.find('s3:Size', ns) or content.find('Size')
                        modified_elem = content.find('s3:LastModified', ns) or content.find('LastModified')
                        
                        if key_elem is not None:
                            obj = {
                                'name': key_elem.text,
                                'size': int(size_elem.text) if size_elem is not None and size_elem.text else 0,
                                'last_modified': modified_elem.text if modified_elem is not None else None,
                                'is_dir': False,
                            }
                            objects.append(obj)
                    
                    # Parse CommonPrefixes elements (directories) if delimiter was used
                    if not recursive:
                        for prefix_elem in root.findall('.//s3:CommonPrefixes', ns) or root.findall('.//CommonPrefixes'):
                            prefix_key = prefix_elem.find('s3:Prefix', ns) or prefix_elem.find('Prefix')
                            if prefix_key is not None:
                                obj = {
                                    'name': prefix_key.text,
                                    'size': 0,
                                    'last_modified': None,
                                    'is_dir': True,
                                }
                                objects.append(obj)
                
                except ET.ParseError as e:
                    logger.error(f"Failed to parse XML response: {e}")
                    # Fallback to empty list
                    objects = []
                
                logger.debug(f"Listed {len(objects)} objects in {bucket_name} with prefix={prefix}")
                return objects
            else:
                logger.error(f"List failed: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error listing objects: {e}")
            return []

    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """Delete an object from MinIO.
        
        Args:
            bucket_name: Bucket name
            object_name: Object name to delete
            
        Returns:
            True if deletion succeeded
        """
        try:
            response = self.client.delete(
                f"{self.base_url}/{bucket_name}/{object_name}",
                auth=(self.access_key, self.secret_key),
            )

            if response.status_code in (200, 204):
                logger.debug(f"Deleted {bucket_name}/{object_name}")
                return True
            else:
                logger.error(f"Delete failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error deleting object: {e}")
            return False

    def sync_directory(
        self,
        bucket_name: str,
        local_dir: Path,
        prefix: str = "",
        exclude_patterns: Optional[List[str]] = None,
    ) -> int:
        """Sync an entire directory to MinIO.
        
        Args:
            bucket_name: Bucket name
            local_dir: Local directory to sync
            prefix: S3 prefix for all objects
            exclude_patterns: File patterns to exclude (e.g., ["*.tmp", "*.log"])
            
        Returns:
            Number of files uploaded
        """
        if not local_dir.exists():
            logger.error(f"Directory not found: {local_dir}")
            return 0

        exclude_patterns = exclude_patterns or []
        uploaded_count = 0

        for file_path in local_dir.rglob("*"):
            if file_path.is_file():
                # Check exclusions
                if any(file_path.match(pattern) for pattern in exclude_patterns):
                    continue

                # Calculate object name
                relative_path = file_path.relative_to(local_dir)
                object_name = f"{prefix}{relative_path}".replace("\\", "/")

                # Upload
                if self.upload_file(bucket_name, object_name, file_path):
                    uploaded_count += 1

        logger.info(f"Synced {uploaded_count} files from {local_dir} to {bucket_name}/{prefix}")
        return uploaded_count

    def _detect_content_type(self, file_path: Path) -> str:
        """Detect MIME type from file extension.
        
        Args:
            file_path: File path
            
        Returns:
            MIME type string
        """
        extension_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".json": "application/json",
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
        }
        
        suffix = file_path.suffix.lower()
        return extension_map.get(suffix, "application/octet-stream")
