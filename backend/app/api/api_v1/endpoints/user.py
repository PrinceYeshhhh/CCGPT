"""
User profile management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import BaseResponse
from app.schemas.user import UserResponse, UserUpdate

logger = structlog.get_logger()
router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile information"""
    try:
        return UserResponse.from_orm(current_user)
    except Exception as e:
        logger.error("Failed to get user profile", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile information"""
    try:
        # Update user fields
        for field, value in profile_data.dict(exclude_unset=True).items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(
            "User profile updated successfully",
            user_id=current_user.id,
            updated_fields=list(profile_data.dict(exclude_unset=True).keys())
        )
        
        return UserResponse.from_orm(current_user)
        
    except Exception as e:
        logger.error("Failed to update user profile", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.post("/profile-picture", response_model=BaseResponse)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload user profile picture"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed"
            )
        
        # Save file (simplified implementation)
        import os
        import uuid
        
        upload_dir = "uploads/profile_pictures"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        filename = f"{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update user profile picture URL
        profile_picture_url = f"/uploads/profile_pictures/{filename}"
        current_user.profile_picture_url = profile_picture_url
        db.commit()
        
        logger.info(
            "Profile picture uploaded successfully",
            user_id=current_user.id,
            filename=filename
        )
        
        return BaseResponse(
            success=True,
            message="Profile picture uploaded successfully",
            data={"profile_picture_url": profile_picture_url}
        )
    
    except Exception as e:
        logger.error("Failed to upload profile picture", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile picture"
        )


@router.put("/change-password", response_model=BaseResponse)
async def change_password(
    password_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    try:
        from app.utils.password import hash_password
        
        current_password = password_data.get('current_password')
        new_password = password_data.get('new_password')
        
        if not current_password or not new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password and new password are required"
            )
        
        # Verify current password
        from app.utils.password import verify_password
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        hashed_new_password = hash_password(new_password)
        current_user.hashed_password = hashed_new_password
        
        db.commit()
        
        logger.info(
            "Password changed successfully",
            user_id=current_user.id
        )
        
        return BaseResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to change password", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
