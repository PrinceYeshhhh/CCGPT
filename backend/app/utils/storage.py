"""
Storage adapters for local, S3 and GCS file storage
"""

import os
import uuid
import aiofiles
from typing import Optional, Tuple
from pathlib import Path
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class StorageAdapter:
    """Base storage adapter interface"""
    
    def __init__(self):
        # Prevent direct instantiation in tests
        if self.__class__ is StorageAdapter:
            raise TypeError("StorageAdapter is abstract and cannot be instantiated directly")

    async def save_file(self, file_content: bytes, workspace_id: str, document_id: str, filename: str) -> Tuple[str, int]:
        """Save file and return (path, size)"""
        raise NotImplementedError
    
    async def get_file(self, path: str) -> bytes:
        """Get file content by path"""
        raise NotImplementedError
    
    def delete_file(self, path: str) -> bool:
        """Delete file by path"""
        raise NotImplementedError


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage adapter"""
    
    def __init__(self, base_dir: Optional[str] = None):
        super().__init__()
        self.base_dir = base_dir or settings.UPLOAD_DIR
    
    def _secure_storage_path(self, workspace_id: str, document_id: str, filename: str) -> str:
        """Create secure storage path"""
        # Sanitize filename
        safe_name = filename.replace("/", "_").replace("\\", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        
        # Create directory structure: base_dir/workspace_id/document_id/filename
        dir_path = Path(self.base_dir) / workspace_id / document_id
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return str(dir_path / safe_name)
    
    async def save_file(self, file_content: bytes, workspace_id: str, document_id: str, filename: str) -> Tuple[str, int]:
        """Save file to local storage"""
        try:
            file_path = self._secure_storage_path(workspace_id, document_id, filename)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            file_size = len(file_content)
            
            logger.info(
                "File saved to local storage",
                workspace_id=workspace_id,
                document_id=document_id,
                filename=filename,
                file_size=file_size,
                file_path=file_path
            )
            
            return file_path, file_size
            
        except Exception as e:
            logger.error(
                "Failed to save file to local storage",
                error=str(e),
                workspace_id=workspace_id,
                document_id=document_id,
                filename=filename
            )
            raise
    
    async def get_file(self, path: str) -> bytes:
        """Get file content from local storage"""
        try:
            async with aiofiles.open(path, 'rb') as f:
                return await f.read()
        except Exception as e:
            logger.error("Failed to read file from local storage", error=str(e), path=path)
            raise
    
    def delete_file(self, path: str) -> bool:
        """Delete file from local storage"""
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info("File deleted from local storage", path=path)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete file from local storage", error=str(e), path=path)
            return False


class S3StorageAdapter(StorageAdapter):
    """S3 storage adapter"""
    
    # Expose boto3 at module scope for tests that monkeypatch it
    try:
        import boto3  # type: ignore
    except Exception:  # pragma: no cover
        boto3 = None  # type: ignore
    
    def __init__(self, bucket: Optional[str] = None, region: Optional[str] = None):
        super().__init__()
        # In tests, constructor signature (bucket, region) is expected
        if bucket is None:
            bucket = getattr(settings, 'S3_BUCKET_NAME', '')
        if region is None:
            region = getattr(settings, 'AWS_REGION', 'us-east-1')
        
        # Lazy import and test-friendly fallbacks
        try:
            if S3StorageAdapter.boto3 is None:
                import boto3 as _boto3  # type: ignore
            else:
                _boto3 = S3StorageAdapter.boto3  # type: ignore
            from botocore.exceptions import ClientError
        except Exception:  # pragma: no cover - tests will mock client
            class _Dummy:
                def __getattr__(self, name):
                    raise RuntimeError("boto3 unavailable in test")
            _boto3 = _Dummy()  # type: ignore
            class ClientError(Exception):
                pass
        
        self.s3_client = _boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = bucket
        self.ClientError = ClientError
    
    def _get_s3_key(self, workspace_id: str, document_id: str, filename: str) -> str:
        """Generate S3 key for file"""
        # Sanitize filename
        safe_name = filename.replace("/", "_").replace("\\", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        
        return f"workspaces/{workspace_id}/documents/{document_id}/{safe_name}"
    
    async def save_file(self, file_content: bytes, workspace_id: str, document_id: str, filename: str) -> Tuple[str, int]:
        """Save file to S3"""
        try:
            s3_key = self._get_s3_key(workspace_id, document_id, filename)
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=self._get_content_type(filename)
            )
            
            file_size = len(file_content)
            
            logger.info(
                "File saved to S3",
                workspace_id=workspace_id,
                document_id=document_id,
                filename=filename,
                file_size=file_size,
                s3_key=s3_key
            )
            
            return s3_key, file_size
            
        except self.ClientError as e:
            logger.error(
                "Failed to save file to S3",
                error=str(e),
                workspace_id=workspace_id,
                document_id=document_id,
                filename=filename
            )
            raise
    
    async def get_file(self, path: str) -> bytes:
        """Get file content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
            return response['Body'].read()
        except self.ClientError as e:
            logger.error("Failed to read file from S3", error=str(e), path=path)
            raise
    
    def delete_file(self, path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
            logger.info("File deleted from S3", path=path)
            return True
        except self.ClientError as e:
            logger.error("Failed to delete file from S3", error=str(e), path=path)
            return False
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on filename"""
        ext = filename.lower().split('.')[-1]
        content_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        return content_types.get(ext, 'application/octet-stream')


class GCSStorageAdapter(StorageAdapter):
    """Google Cloud Storage adapter"""
    
    def __init__(self):
        super().__init__()
        # Lazy import to allow tests to mock google clients
        from google.cloud import storage  # type: ignore
        try:
            self.client = storage.Client()
        except Exception:
            # In testing, allow a dummy client to be injected via mocks
            class _Dummy:
                def __getattr__(self, name):
                    raise RuntimeError("GCS client unavailable in test")
            self.client = _Dummy()
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "") or getattr(settings, "GCS_BUCKET_NAME", "")
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME is required for GCS storage")
        self.bucket = self.client.bucket(self.bucket_name)
    
    def _get_gcs_path(self, workspace_id: str, document_id: str, filename: str) -> str:
        safe_name = filename.replace("/", "_").replace("\\", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        return f"workspaces/{workspace_id}/documents/{document_id}/{safe_name}"
    
    async def save_file(self, file_content: bytes, workspace_id: str, document_id: str, filename: str) -> Tuple[str, int]:
        path = self._get_gcs_path(workspace_id, document_id, filename)
        blob = self.bucket.blob(path)
        blob.upload_from_string(file_content)
        logger.info("File saved to GCS", bucket=self.bucket_name, path=path)
        return path, len(file_content)
    
    async def get_file(self, path: str) -> bytes:
        blob = self.bucket.blob(path)
        return blob.download_as_bytes()
    
    def delete_file(self, path: str) -> bool:
        try:
            blob = self.bucket.blob(path)
            blob.delete()
            logger.info("File deleted from GCS", path=path)
            return True
        except Exception as e:
            logger.error("Failed to delete file from GCS", error=str(e), path=path)
            return False


def get_storage_adapter() -> StorageAdapter:
    """Get appropriate storage adapter based on configuration"""
    if getattr(settings, "USE_S3", False):
        return S3StorageAdapter(getattr(settings, 'S3_BUCKET_NAME', ''), getattr(settings, 'AWS_REGION', 'us-east-1'))
    if getattr(settings, "USE_GCS", False):
        return GCSStorageAdapter()
    else:
        return LocalStorageAdapter()
