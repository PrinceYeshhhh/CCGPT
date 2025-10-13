# Backup and Disaster Recovery Service for CustomerCareGPT
# Comprehensive backup strategy for production environments

import os
import json
import shutil
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import redis
import tarfile
import gzip
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.core.database import get_db
from app.utils.logging_config import business_logger, security_logger

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Types of backups supported"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    WAL = "wal"  # Write-Ahead Log backup

class BackupStatus(Enum):
    """Backup status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class BackupMetadata:
    """Metadata for backup operations"""
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    size_bytes: int = 0
    checksum: Optional[str] = None
    retention_days: int = 30
    components: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.components is None:
            self.components = []

class BackupService:
    """Comprehensive backup and disaster recovery service"""
    
    def __init__(self):
        self.backup_dir = Path(settings.BACKUP_DIR or "/app/backups")
        # Don't create directory during import - create it lazily when needed
        self._backup_dir_created = False
        
        # S3 configuration for remote backups
        self.s3_client = None
        self.s3_bucket = settings.S3_BACKUP_BUCKET
        if settings.USE_S3_BACKUP and settings.AWS_ACCESS_KEY_ID:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        
        # Backup retention policies
        self.retention_days = settings.BACKUP_RETENTION_DAYS or 30
        self.max_backups = 10  # Default value
        
    def _ensure_backup_dir(self):
        """Ensure backup directory exists, create it if needed."""
        if not self._backup_dir_created:
            try:
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                self._backup_dir_created = True
            except PermissionError:
                # In CI/testing environments, use a temp directory instead
                import tempfile
                self.backup_dir = Path(tempfile.gettempdir()) / "backups"
                self.backup_dir.mkdir(parents=True, exist_ok=True)
                self._backup_dir_created = True
        
        # Backup retention policies
        self.retention_policies = {
            BackupType.FULL: 30,  # days
            BackupType.INCREMENTAL: 7,
            BackupType.DIFFERENTIAL: 14,
            BackupType.WAL: 3
        }
        
        # Component configurations
        self.components = {
            'database': self._backup_database,
            'redis': self._backup_redis,
            'chromadb': self._backup_chromadb,
            'uploads': self._backup_uploads,
            'config': self._backup_config
        }
    
    async def create_backup(
        self, 
        backup_type: BackupType = BackupType.FULL,
        components: List[str] = None,
        retention_days: int = None
    ) -> BackupMetadata:
        """Create a comprehensive backup"""
        
        if components is None:
            components = list(self.components.keys())
        
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{backup_type.value}"
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=backup_type,
            status=BackupStatus.IN_PROGRESS,
            created_at=datetime.now(),
            retention_days=retention_days or self.retention_policies.get(backup_type, 30),
            components=components
        )
        
        logger.info(
            "Starting backup operation",
            backup_id=backup_id,
            backup_type=backup_type.value,
            components=components
        )
        
        try:
            # Ensure backup directory exists
            self._ensure_backup_dir()
            
            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup each component
            for component in components:
                if component in self.components:
                    await self.components[component](backup_path, metadata)
            
            # Create backup manifest
            await self._create_manifest(backup_path, metadata)
            
            # Compress backup
            await self._compress_backup(backup_path, metadata)
            
            # Upload to remote storage if configured
            if self.s3_client and self.s3_bucket:
                await self._upload_to_s3(backup_path, metadata)
            
            # Update metadata
            metadata.status = BackupStatus.COMPLETED
            metadata.completed_at = datetime.now()
            
            logger.info(
                "Backup completed successfully",
                backup_id=backup_id,
                size_bytes=metadata.size_bytes,
                duration_seconds=(metadata.completed_at - metadata.created_at).total_seconds()
            )
            
        except Exception as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            
            logger.error(
                "Backup failed",
                backup_id=backup_id,
                error=str(e),
                exc_info=True
            )
            
            # Cleanup failed backup
            if backup_path.exists():
                shutil.rmtree(backup_path)
        
        # Save metadata
        await self._save_metadata(metadata)
        
        return metadata
    
    async def _backup_database(self, backup_path: Path, metadata: BackupMetadata):
        """Backup PostgreSQL database"""
        db_path = backup_path / "database"
        db_path.mkdir(exist_ok=True)
        
        # Parse database URL
        db_url = settings.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL not configured")
        
        # Extract connection parameters
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        # Create database dump
        dump_file = db_path / "database.sql"
        
        # Use pg_dump for comprehensive backup
        cmd = [
            "pg_dump",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-d", parsed.path[1:] or "customercaregpt",
            "-f", str(dump_file),
            "--verbose",
            "--no-password",
            "--format=plain",
            "--encoding=UTF8",
            "--no-owner",
            "--no-privileges"
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password
        
        # Execute pg_dump
        import subprocess
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Database backup failed: {result.stderr}")
        
        # Create schema-only backup
        schema_file = db_path / "schema.sql"
        schema_cmd = cmd + ["--schema-only"]
        schema_cmd[-2] = str(schema_file)
        
        result = subprocess.run(schema_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Schema backup failed: {result.stderr}")
        
        # Create data-only backup
        data_file = db_path / "data.sql"
        data_cmd = cmd + ["--data-only"]
        data_cmd[-2] = str(data_file)
        
        result = subprocess.run(data_cmd, env=env, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Data backup failed: {result.stderr}")
        
        metadata.size_bytes += sum(f.stat().st_size for f in db_path.glob("*.sql"))
        
        logger.info(
            "Database backup completed",
            backup_id=metadata.backup_id,
            dump_size=sum(f.stat().st_size for f in db_path.glob("*.sql"))
        )
    
    async def _backup_redis(self, backup_path: Path, metadata: BackupMetadata):
        """Backup Redis data"""
        redis_path = backup_path / "redis"
        redis_path.mkdir(exist_ok=True)
        
        # Connect to Redis
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Create RDB backup
        rdb_file = redis_path / "dump.rdb"
        
        # Trigger RDB save
        redis_client.bgsave()
        
        # Wait for save to complete
        while redis_client.lastsave() == redis_client.lastsave():
            await asyncio.sleep(1)
        
        # Copy RDB file (this would need to be done via Docker volume mount in production)
        # For now, we'll create a JSON export
        redis_data = {}
        
        # Export all keys
        for key in redis_client.scan_iter():
            key_type = redis_client.type(key)
            
            if key_type == 'string':
                redis_data[key] = redis_client.get(key)
            elif key_type == 'hash':
                redis_data[key] = redis_client.hgetall(key)
            elif key_type == 'list':
                redis_data[key] = redis_client.lrange(key, 0, -1)
            elif key_type == 'set':
                redis_data[key] = list(redis_client.smembers(key))
            elif key_type == 'zset':
                redis_data[key] = redis_client.zrange(key, 0, -1, withscores=True)
        
        # Save to JSON
        json_file = redis_path / "redis_data.json"
        with open(json_file, 'w') as f:
            json.dump(redis_data, f, default=str, indent=2)
        
        metadata.size_bytes += json_file.stat().st_size
        
        logger.info(
            "Redis backup completed",
            backup_id=metadata.backup_id,
            keys_backed_up=len(redis_data)
        )
    
    async def _backup_chromadb(self, backup_path: Path, metadata: BackupMetadata):
        """Backup ChromaDB vector database"""
        chroma_path = backup_path / "chromadb"
        chroma_path.mkdir(exist_ok=True)
        
        # ChromaDB data directory
        chroma_data_dir = Path(settings.CHROMA_PERSIST_DIRECTORY or "/chroma/chroma")
        
        if chroma_data_dir.exists():
            # Create tar archive of ChromaDB data
            tar_file = chroma_path / "chromadb_data.tar.gz"
            
            with tarfile.open(tar_file, "w:gz") as tar:
                tar.add(chroma_data_dir, arcname="chroma")
            
            metadata.size_bytes += tar_file.stat().st_size
            
            logger.info(
                "ChromaDB backup completed",
                backup_id=metadata.backup_id,
                archive_size=tar_file.stat().st_size
            )
        else:
            logger.warning(f"ChromaDB data directory not found: {chroma_data_dir}")
    
    async def _backup_uploads(self, backup_path: Path, metadata: BackupMetadata):
        """Backup uploaded files"""
        uploads_path = backup_path / "uploads"
        uploads_path.mkdir(exist_ok=True)
        
        # Uploads directory
        uploads_dir = Path(settings.UPLOAD_DIR or "/app/uploads")
        
        if uploads_dir.exists():
            # Create tar archive of uploads
            tar_file = uploads_path / "uploads.tar.gz"
            
            with tarfile.open(tar_file, "w:gz") as tar:
                tar.add(uploads_dir, arcname="uploads")
            
            metadata.size_bytes += tar_file.stat().st_size
            
            logger.info(
                "Uploads backup completed",
                backup_id=metadata.backup_id,
                archive_size=tar_file.stat().st_size
            )
        else:
            logger.warning(f"Uploads directory not found: {uploads_dir}")
    
    async def _backup_config(self, backup_path: Path, metadata: BackupMetadata):
        """Backup configuration files"""
        config_path = backup_path / "config"
        config_path.mkdir(exist_ok=True)
        
        # Backup environment configuration
        env_file = config_path / "environment.json"
        env_data = {
            "database_url": settings.DATABASE_URL,
            "redis_url": settings.REDIS_URL,
            "chroma_url": settings.CHROMA_URL,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
            "backup_created_at": datetime.now().isoformat()
        }
        
        with open(env_file, 'w') as f:
            json.dump(env_data, f, indent=2)
        
        # Backup application configuration
        app_config_file = config_path / "app_config.json"
        app_config = {
            "cors_origins": settings.CORS_ORIGINS,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "api_base_url": settings.API_BASE_URL,
            "public_base_url": settings.PUBLIC_BASE_URL,
            "jwt_secret_set": bool(settings.JWT_SECRET),
            "secret_key_set": bool(settings.SECRET_KEY),
            "gemini_api_key_set": bool(settings.GEMINI_API_KEY),
            "stripe_api_key_set": bool(settings.STRIPE_API_KEY)
        }
        
        with open(app_config_file, 'w') as f:
            json.dump(app_config, f, indent=2)
        
        metadata.size_bytes += env_file.stat().st_size + app_config_file.stat().st_size
        
        logger.info(
            "Configuration backup completed",
            backup_id=metadata.backup_id
        )
    
    async def _create_manifest(self, backup_path: Path, metadata: BackupMetadata):
        """Create backup manifest file"""
        manifest = {
            "backup_id": metadata.backup_id,
            "backup_type": metadata.backup_type.value,
            "status": metadata.status.value,
            "created_at": metadata.created_at.isoformat(),
            "completed_at": metadata.completed_at.isoformat() if metadata.completed_at else None,
            "size_bytes": metadata.size_bytes,
            "retention_days": metadata.retention_days,
            "components": metadata.components,
            "error_message": metadata.error_message,
            "version": "1.0",
            "application": "CustomerCareGPT",
            "environment": settings.ENVIRONMENT
        }
        
        manifest_file = backup_path / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    async def _compress_backup(self, backup_path: Path, metadata: BackupMetadata):
        """Compress backup directory"""
        self._ensure_backup_dir()
        compressed_file = self.backup_dir / f"{metadata.backup_id}.tar.gz"
        
        with tarfile.open(compressed_file, "w:gz") as tar:
            tar.add(backup_path, arcname=metadata.backup_id)
        
        # Update size
        metadata.size_bytes = compressed_file.stat().st_size
        
        # Remove uncompressed directory
        shutil.rmtree(backup_path)
        
        logger.info(
            "Backup compressed",
            backup_id=metadata.backup_id,
            compressed_size=metadata.size_bytes
        )
    
    async def _upload_to_s3(self, backup_path: Path, metadata: BackupMetadata):
        """Upload backup to S3"""
        if not self.s3_client or not self.s3_bucket:
            return
        
        self._ensure_backup_dir()
        compressed_file = self.backup_dir / f"{metadata.backup_id}.tar.gz"
        
        try:
            s3_key = f"backups/{metadata.backup_id}.tar.gz"
            
            self.s3_client.upload_file(
                str(compressed_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'Metadata': {
                        'backup_id': metadata.backup_id,
                        'backup_type': metadata.backup_type.value,
                        'created_at': metadata.created_at.isoformat(),
                        'environment': settings.ENVIRONMENT
                    }
                }
            )
            
            logger.info(
                "Backup uploaded to S3",
                backup_id=metadata.backup_id,
                s3_bucket=self.s3_bucket,
                s3_key=s3_key
            )
            
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            raise
    
    async def _save_metadata(self, metadata: BackupMetadata):
        """Save backup metadata"""
        self._ensure_backup_dir()
        metadata_file = self.backup_dir / f"{metadata.backup_id}_metadata.json"
        
        metadata_dict = {
            "backup_id": metadata.backup_id,
            "backup_type": metadata.backup_type.value,
            "status": metadata.status.value,
            "created_at": metadata.created_at.isoformat(),
            "completed_at": metadata.completed_at.isoformat() if metadata.completed_at else None,
            "size_bytes": metadata.size_bytes,
            "checksum": metadata.checksum,
            "retention_days": metadata.retention_days,
            "components": metadata.components,
            "error_message": metadata.error_message
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
    
    async def list_backups(self) -> List[BackupMetadata]:
        """List all available backups"""
        self._ensure_backup_dir()
        backups = []
        
        for metadata_file in self.backup_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                
                metadata = BackupMetadata(
                    backup_id=data["backup_id"],
                    backup_type=BackupType(data["backup_type"]),
                    status=BackupStatus(data["status"]),
                    created_at=datetime.fromisoformat(data["created_at"]),
                    completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                    size_bytes=data["size_bytes"],
                    checksum=data.get("checksum"),
                    retention_days=data["retention_days"],
                    components=data["components"],
                    error_message=data.get("error_message")
                )
                
                backups.append(metadata)
                
            except Exception as e:
                logger.error(f"Failed to load backup metadata from {metadata_file}: {e}")
        
        return sorted(backups, key=lambda x: x.created_at, reverse=True)
    
    async def restore_backup(self, backup_id: str, components: List[str] = None) -> bool:
        """Restore from backup"""
        if components is None:
            components = list(self.components.keys())
        
        logger.info(
            "Starting backup restore",
            backup_id=backup_id,
            components=components
        )
        
        try:
            # Find backup file
            backup_file = self.backup_dir / f"{backup_id}.tar.gz"
            if not backup_file.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            # Extract backup
            extract_path = self.backup_dir / f"restore_{backup_id}"
            extract_path.mkdir(exist_ok=True)
            
            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(extract_path)
            
            # Restore components
            for component in components:
                if component == 'database':
                    await self._restore_database(extract_path / backup_id)
                elif component == 'redis':
                    await self._restore_redis(extract_path / backup_id)
                elif component == 'chromadb':
                    await self._restore_chromadb(extract_path / backup_id)
                elif component == 'uploads':
                    await self._restore_uploads(extract_path / backup_id)
            
            # Cleanup
            shutil.rmtree(extract_path)
            
            logger.info(
                "Backup restore completed",
                backup_id=backup_id,
                components=components
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Backup restore failed",
                backup_id=backup_id,
                error=str(e),
                exc_info=True
            )
            return False
    
    async def _restore_database(self, backup_path: Path):
        """Restore database from backup"""
        db_path = backup_path / "database"
        dump_file = db_path / "database.sql"
        
        if not dump_file.exists():
            raise FileNotFoundError(f"Database dump not found: {dump_file}")
        
        # Parse database URL
        db_url = settings.DATABASE_URL
        import urllib.parse
        parsed = urllib.parse.urlparse(db_url)
        
        # Restore database
        cmd = [
            "psql",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-d", parsed.path[1:] or "customercaregpt",
            "-f", str(dump_file)
        ]
        
        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password
        
        import subprocess
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Database restore failed: {result.stderr}")
    
    async def _restore_redis(self, backup_path: Path):
        """Restore Redis from backup"""
        redis_path = backup_path / "redis"
        json_file = redis_path / "redis_data.json"
        
        if not json_file.exists():
            raise FileNotFoundError(f"Redis backup not found: {json_file}")
        
        # Load Redis data
        with open(json_file, 'r') as f:
            redis_data = json.load(f)
        
        # Connect to Redis and restore
        redis_client = redis.from_url(settings.REDIS_URL)
        
        # Clear existing data
        redis_client.flushdb()
        
        # Restore data
        for key, value in redis_data.items():
            if isinstance(value, str):
                redis_client.set(key, value)
            elif isinstance(value, dict):
                redis_client.hmset(key, value)
            elif isinstance(value, list):
                redis_client.lpush(key, *value)
    
    async def _restore_chromadb(self, backup_path: Path):
        """Restore ChromaDB from backup"""
        chroma_path = backup_path / "chromadb"
        tar_file = chroma_path / "chromadb_data.tar.gz"
        
        if not tar_file.exists():
            raise FileNotFoundError(f"ChromaDB backup not found: {tar_file}")
        
        # ChromaDB data directory
        chroma_data_dir = Path(settings.CHROMA_PERSIST_DIRECTORY or "/chroma/chroma")
        chroma_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract backup
        with tarfile.open(tar_file, "r:gz") as tar:
            tar.extractall(chroma_data_dir.parent)
    
    async def _restore_uploads(self, backup_path: Path):
        """Restore uploads from backup"""
        uploads_path = backup_path / "uploads"
        tar_file = uploads_path / "uploads.tar.gz"
        
        if not tar_file.exists():
            raise FileNotFoundError(f"Uploads backup not found: {tar_file}")
        
        # Uploads directory
        uploads_dir = Path(settings.UPLOAD_DIR or "/app/uploads")
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract backup
        with tarfile.open(tar_file, "r:gz") as tar:
            tar.extractall(uploads_dir.parent)
    
    async def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        backups = await self.list_backups()
        cutoff_date = datetime.now() - timedelta(days=30)  # Default retention
        
        for backup in backups:
            if backup.created_at < cutoff_date:
                await self.delete_backup(backup.backup_id)
    
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        try:
            # Delete local files
            backup_file = self.backup_dir / f"{backup_id}.tar.gz"
            metadata_file = self.backup_dir / f"{backup_id}_metadata.json"
            
            if backup_file.exists():
                backup_file.unlink()
            
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Delete from S3 if configured
            if self.s3_client and self.s3_bucket:
                s3_key = f"backups/{backup_id}.tar.gz"
                try:
                    self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
                except ClientError as e:
                    logger.warning(f"Failed to delete backup from S3: {e}")
            
            logger.info("Backup deleted", backup_id=backup_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {e}")
            return False

# Global backup service instance
backup_service = BackupService()
