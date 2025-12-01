"""
Cloud Storage Module

Handles interaction with MinIO/S3-compatible storage for:
- Uploading change requests
- Downloading baseline configs
- Storing/retrieving reports
- Distributing plugin updates
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from minio import Minio
from minio.error import S3Error
import json
import io


class CloudStorage:
    """MinIO/S3 storage interface"""
    
    def __init__(self, endpoint: str, access_key: str, secret_key: str, 
                 secure: bool = True):
        """
        Initialize cloud storage client
        
        Args:
            endpoint: MinIO endpoint (e.g., "minio.example.com:9000")
            access_key: Access key ID
            secret_key: Secret access key
            secure: Use HTTPS
            region: S3 region
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
            
        )
        self.endpoint = endpoint
    
    def ensure_bucket_exists(self, bucket_name: str) -> bool:
        """
        Ensure a bucket exists, create if it doesn't.
        
        Args:
            bucket_name: Name of the bucket
            
        Returns:
            True if bucket exists or was created successfully
        """
        try:
            # Check if bucket exists
            if self.client.bucket_exists(bucket_name):
                return True
            else:
                # Bucket doesn't exist, create it
                self.client.make_bucket(bucket_name)
                return True
        except Exception as e:
            print(f"Error with bucket {bucket_name}: {e}")
            return True  # Assume bucket exists if check fails
    
    def upload_file(self, bucket_name: str, object_name: str, file_path: str, 
                   content_type: str = "application/octet-stream") -> bool:
        """
        Upload a file to storage.
        
        Args:
            bucket_name: Bucket to upload to
            object_name: Name of the object in the bucket
            file_path: Local path to the file
            content_type: MIME type of the file
            
        Returns:
            True if upload successful
        """
        try:
            self.ensure_bucket_exists(bucket_name)
            self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type
            )
            return True
        except Exception as e:
            # Catch all exceptions including MinIO region query errors (404)
            print(f"Failed to upload {file_path} to {bucket_name}/{object_name}: {e}")
            return False
    
    def upload_json(self, bucket_name: str, object_name: str, data: Dict[str, Any]) -> bool:
        """
        Upload JSON data to storage.
        
        Args:
            bucket_name: Bucket to upload to
            object_name: Name of the object in the bucket
            data: JSON-serializable data
            
        Returns:
            True if upload successful
        """
        try:
            self.ensure_bucket_exists(bucket_name)
            json_data = json.dumps(data, indent=2)
            json_bytes = io.BytesIO(json_data.encode('utf-8'))
            
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=json_bytes,
                length=len(json_data.encode('utf-8')),
                content_type="application/json"
            )
            return True
        except (S3Error, ValueError) as e:
            print(f"Failed to upload JSON to {bucket_name}/{object_name}: {e}")
            return False
    
    def download_file(self, bucket_name: str, object_name: str, file_path: str) -> bool:
        """
        Download a file from storage.
        
        Args:
            bucket_name: Bucket to download from
            object_name: Name of the object in the bucket
            file_path: Local path to save the file
            
        Returns:
            True if download successful
        """
        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            return True
        except Exception as e:
            # Catch all exceptions including MinIO region query errors (404)
            print(f"Failed to download {bucket_name}/{object_name} to {file_path}: {e}")
            return False
    
    def download_json(self, bucket_name: str, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Download and parse JSON from storage
        
        Args:
            bucket_name: Source bucket
            object_name: Object name in bucket
            
        Returns:
            Parsed JSON data or None
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read().decode('utf-8')
            return json.loads(data)
        except (S3Error, ValueError) as e:
            print(f"Failed to download JSON from {bucket_name}/{object_name}: {e}")
            return None
        finally:
            if 'response' in locals():
                response.close()
    
    def list_objects(self, bucket_name: str, prefix: str = "") -> List[str]:
        """
        List objects in bucket with optional prefix
        
        Args:
            bucket_name: Bucket to list
            prefix: Object prefix to filter by
            
        Returns:
            List of object names
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except Exception as e:
            # Catch all exceptions including MinIO region query errors (404)
            print(f"Failed to list objects in {bucket_name}: {e}")
            return []
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete an object from storage
        
        Args:
            bucket_name: Bucket containing the object
            object_name: Name of object to delete
            
        Returns:
            True if deletion successful
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            return True
        except Exception as e:
            # Catch all exceptions including MinIO region query errors (404)
            print(f"Failed to delete {bucket_name}/{object_name}: {e}")
            return False
    
    def object_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Check if object exists
        
        Args:
            bucket_name: Bucket to check
            object_name: Object name
            
        Returns:
            True if exists
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_object_metadata(self, bucket_name: str, object_name: str) -> Optional[Dict[str, Any]]:
        """
        Get object metadata
        
        Args:
            bucket_name: Bucket name
            object_name: Object name
            
        Returns:
            Metadata dict or None
        """
        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                'size': stat.size,
                'etag': stat.etag,
                'last_modified': stat.last_modified,
                'content_type': stat.content_type,
                'metadata': stat.metadata
            }
        except Exception as e:
            # Catch all exceptions including MinIO region query errors (404)
            print(f"Failed to get metadata for {bucket_name}/{object_name}: {e}")
            return None


class ChangeRequestManager:
    """Manages change requests via cloud storage"""
    
    def __init__(self, storage: CloudStorage, bucket_name: str = "archivesmp-changes"):
        """
        Initialize change request manager
        
        Args:
            storage: CloudStorage instance
            bucket_name: Bucket for change requests
        """
        self.storage = storage
        self.bucket_name = bucket_name
        self.storage.ensure_bucket_exists(bucket_name)
    
    def upload_change_request(self, change_request: Dict[str, Any]) -> str:
        """
        Upload change request to storage
        
        Args:
            change_request: The change request data
            
        Returns:
            Request ID for tracking
        """
        import uuid
        from datetime import datetime
        
        request_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Add metadata to the change request
        change_request.update({
            'request_id': request_id,
            'timestamp': timestamp,
            'status': 'pending'
        })
        
        # Upload to changes bucket
        bucket_name = "archivesmp-changes"
        object_name = f"pending/{request_id}.json"
        
        if self.storage.upload_json(bucket_name, object_name, change_request):
            return request_id
        else:
            raise Exception("Failed to upload change request")
    
    def list_pending_changes(self) -> List[Dict[str, Any]]:
        """
        List all pending change requests
        
        Returns:
            List of pending change requests
        """
        bucket_name = "archivesmp-changes"
        prefix = "pending/"
        
        object_names = self.storage.list_objects(bucket_name, prefix)
        changes = []
        
        for object_name in object_names:
            if object_name.endswith('.json'):
                change_data = self.storage.download_json(bucket_name, object_name)
                if change_data:
                    changes.append(change_data)
        
        return changes
    
    def download_change_request(self, change_id: str) -> Optional[Dict[str, Any]]:
        """
        Download change request data
        
        Args:
            change_id: Change request ID
            
        Returns:
            Change request data or None
        """
        bucket_name = "archivesmp-changes"
        
        # Try pending first
        object_name = f"pending/{change_id}.json"
        change_data = self.storage.download_json(bucket_name, object_name)
        
        if not change_data:
            # Try completed
            object_name = f"completed/{change_id}.json"
            change_data = self.storage.download_json(bucket_name, object_name)
        
        return change_data
    
    def mark_change_completed(self, change_id: str) -> bool:
        """
        Mark change as completed (move to completed/)
        
        Args:
            change_id: Change request ID
            
        Returns:
            True if successful
        """
        bucket_name = "archivesmp-changes"
        pending_object = f"pending/{change_id}.json"
        completed_object = f"completed/{change_id}.json"
        
        # Download the pending change
        change_data = self.storage.download_json(bucket_name, pending_object)
        if not change_data:
            return False
        
        # Update status
        change_data['status'] = 'completed'
        
        # Upload to completed folder
        if self.storage.upload_json(bucket_name, completed_object, change_data):
            # Delete from pending
            self.storage.delete_object(bucket_name, pending_object)
            return True
        
        return False
    
    def upload_change_result(self, change_id: str, result: Dict[str, Any]) -> bool:
        """
        Upload change execution result
        
        Args:
            change_id: Change request ID
            result: Execution result data
            
        Returns:
            True if successful
        """
        bucket_name = "archivesmp-changes"
        object_name = f"results/{change_id}_result.json"
        
        # Add timestamp to result
        from datetime import datetime
        result['execution_timestamp'] = datetime.now().isoformat()
        result['change_id'] = change_id
        
        return self.storage.upload_json(bucket_name, object_name, result)
