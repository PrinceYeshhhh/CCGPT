# Backup and Disaster Recovery API Endpoints
# Administrative endpoints for backup management

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from enum import Enum

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.services.backup_service import backup_service, BackupType, BackupStatus, BackupMetadata
from app.utils.logging_config import business_logger, security_logger
from app.utils.error_handling import CustomError, AuthorizationError

router = APIRouter()

class BackupRequest(BaseModel):
    """Request model for creating backups"""
    backup_type: BackupType = BackupType.FULL
    components: Optional[List[str]] = Field(
        default=None,
        description="Components to backup (database, redis, chromadb, uploads, config)"
    )
    retention_days: Optional[int] = Field(
        default=None,
        description="Number of days to retain backup"
    )

class BackupResponse(BaseModel):
    """Response model for backup operations"""
    backup_id: str
    backup_type: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    size_bytes: int = 0
    components: List[str] = []
    error_message: Optional[str] = None

class RestoreRequest(BaseModel):
    """Request model for restoring backups"""
    backup_id: str
    components: Optional[List[str]] = Field(
        default=None,
        description="Components to restore"
    )

class BackupListResponse(BaseModel):
    """Response model for listing backups"""
    backups: List[BackupResponse]
    total_count: int
    total_size_bytes: int

@router.post("/create", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new backup.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for backup operations")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="create_backup",
        backup_type=request.backup_type.value,
        components=request.components or []
    )
    
    try:
        # Create backup in background
        metadata = await backup_service.create_backup(
            backup_type=request.backup_type,
            components=request.components,
            retention_days=request.retention_days
        )
        
        business_logger.info(
            "Backup creation initiated",
            backup_id=metadata.backup_id,
            backup_type=metadata.backup_type.value,
            user_id=str(current_user.id)
        )
        
        return BackupResponse(
            backup_id=metadata.backup_id,
            backup_type=metadata.backup_type.value,
            status=metadata.status.value,
            created_at=metadata.created_at,
            completed_at=metadata.completed_at,
            size_bytes=metadata.size_bytes,
            components=metadata.components,
            error_message=metadata.error_message
        )
        
    except Exception as e:
        business_logger.error(
            "Backup creation failed",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create backup: {str(e)}"
        )

@router.get("/list", response_model=BackupListResponse)
async def list_backups(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[BackupStatus] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List available backups.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for backup operations")
    
    try:
        backups = await backup_service.list_backups()
        
        # Apply filters
        if status_filter:
            backups = [b for b in backups if b.status == status_filter]
        
        # Apply pagination
        total_count = len(backups)
        backups = backups[offset:offset + limit]
        
        # Calculate total size
        total_size_bytes = sum(b.size_bytes for b in backups)
        
        backup_responses = [
            BackupResponse(
                backup_id=backup.backup_id,
                backup_type=backup.backup_type.value,
                status=backup.status.value,
                created_at=backup.created_at,
                completed_at=backup.completed_at,
                size_bytes=backup.size_bytes,
                components=backup.components,
                error_message=backup.error_message
            )
            for backup in backups
        ]
        
        return BackupListResponse(
            backups=backup_responses,
            total_count=total_count,
            total_size_bytes=total_size_bytes
        )
        
    except Exception as e:
        business_logger.error(
            "Failed to list backups",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )

@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get details of a specific backup.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for backup operations")
    
    try:
        backups = await backup_service.list_backups()
        backup = next((b for b in backups if b.backup_id == backup_id), None)
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
        
        return BackupResponse(
            backup_id=backup.backup_id,
            backup_type=backup.backup_type.value,
            status=backup.status.value,
            created_at=backup.created_at,
            completed_at=backup.completed_at,
            size_bytes=backup.size_bytes,
            components=backup.components,
            error_message=backup.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        business_logger.error(
            "Failed to get backup details",
            backup_id=backup_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup details: {str(e)}"
        )

@router.post("/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Restore from a backup.
    
    WARNING: This will overwrite existing data!
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for backup operations")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="restore_backup",
        backup_id=backup_id,
        components=request.components or []
    )
    
    try:
        # Verify backup exists
        backups = await backup_service.list_backups()
        backup = next((b for b in backups if b.backup_id == backup_id), None)
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
        
        if backup.status != BackupStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot restore from incomplete or failed backup"
            )
        
        # Restore backup
        success = await backup_service.restore_backup(
            backup_id=backup_id,
            components=request.components
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Backup restore failed"
            )
        
        business_logger.info(
            "Backup restore completed",
            backup_id=backup_id,
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Backup restored successfully",
                "backup_id": backup_id,
                "restored_components": request.components or backup.components
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        business_logger.error(
            "Backup restore failed",
            backup_id=backup_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup restore failed: {str(e)}"
        )

@router.delete("/{backup_id}")
async def delete_backup(
    backup_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Delete a backup.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for backup operations")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="delete_backup",
        backup_id=backup_id
    )
    
    try:
        success = await backup_service.delete_backup(backup_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete backup"
            )
        
        business_logger.info(
            "Backup deleted",
            backup_id=backup_id,
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Backup deleted successfully",
                "backup_id": backup_id
            }
        )
        
    except Exception as e:
        business_logger.error(
            "Failed to delete backup",
            backup_id=backup_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_old_backups(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Clean up old backups based on retention policy.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for backup operations")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="cleanup_backups"
    )
    
    try:
        await backup_service.cleanup_old_backups()
        
        business_logger.info(
            "Backup cleanup completed",
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Old backups cleaned up successfully"
            }
        )
        
    except Exception as e:
        business_logger.error(
            "Backup cleanup failed",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup cleanup failed: {str(e)}"
        )

@router.get("/status/health")
async def backup_health_check(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Check backup system health.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for backup operations")
    
    try:
        # Check backup directory
        backup_dir = backup_service.backup_dir
        backup_dir_exists = backup_dir.exists()
        backup_dir_writable = backup_dir.is_dir() and os.access(backup_dir, os.W_OK)
        
        # Check S3 connectivity if configured
        s3_available = False
        if backup_service.s3_client and backup_service.s3_bucket:
            try:
                backup_service.s3_client.head_bucket(Bucket=backup_service.s3_bucket)
                s3_available = True
            except Exception:
                pass
        
        # Get recent backup status
        recent_backups = await backup_service.list_backups()
        recent_backups = recent_backups[:5]  # Last 5 backups
        
        health_status = {
            "backup_directory": {
                "exists": backup_dir_exists,
                "writable": backup_dir_writable,
                "path": str(backup_dir)
            },
            "s3_storage": {
                "configured": backup_service.s3_client is not None,
                "available": s3_available,
                "bucket": backup_service.s3_bucket
            },
            "recent_backups": [
                {
                    "backup_id": b.backup_id,
                    "status": b.status.value,
                    "created_at": b.created_at.isoformat(),
                    "size_bytes": b.size_bytes
                }
                for b in recent_backups
            ],
            "overall_status": "healthy" if backup_dir_exists and backup_dir_writable else "unhealthy"
        }
        
        return health_status
        
    except Exception as e:
        business_logger.error(
            "Backup health check failed",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup health check failed: {str(e)}"
        )
