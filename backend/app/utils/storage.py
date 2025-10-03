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
    
    async def save_file(self, file_content: bytes, workspace_id: str, document_id: str, filename: str) -> Tuple[str, int]:
        """Save file and return (path, size)"""
        raise NotImplementedError
    
    async def get_file(self, path: str) -> bytes:
        """Get file content by path"""
        raise NotImplementedError
    
    async def delete_file(self, path: str) -> bool:
        """Delete file by path"""
        raise NotImplementedError


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage adapter"""
    
    def __init__(self, base_dir: str = None):
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
    
    async def delete_file(self, path: str) -> bool:
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
    
    def __init__(self):
        if not settings.USE_S3:
            raise ValueError("S3 storage is not enabled")
        
        import boto3
        from botocore.exceptions import ClientError
        
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        self.bucket_name = settings.S3_BUCKET_NAME
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
    
    async def delete_file(self, path: str) -> bool:
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
        from google.cloud import storage  # type: ignore
        self.client = storage.Client()
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
    
    async def delete_file(self, path: str) -> bool:
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
        return S3StorageAdapter()
    if getattr(settings, "USE_GCS", False):
        return GCSStorageAdapter()
    else:
        return LocalStorageAdapter()
