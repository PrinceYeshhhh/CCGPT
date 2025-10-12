"""
Organization management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import BaseResponse
from pydantic import BaseModel

logger = structlog.get_logger()
router = APIRouter()


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None


@router.put("/settings", response_model=BaseResponse)
async def update_organization_settings(
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update organization settings"""
    try:
        # For now, we'll store organization data in user model
        # In a real implementation, you'd have a separate Organization model
        
        updated_fields = []
        for field, value in org_data.dict(exclude_unset=True).items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
                updated_fields.append(field)
        
        db.commit()
        
        logger.info(
            "Organization settings updated successfully",
            user_id=current_user.id,
            updated_fields=updated_fields
        )
        
        return BaseResponse(
            success=True,
            message="Organization settings updated successfully",
            data=org_data.dict()
        )
        
    except Exception as e:
        logger.error("Failed to update organization settings", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization settings"
        )


@router.post("/logo", response_model=BaseResponse)
async def upload_organization_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload organization logo"""
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
        
        upload_dir = "uploads/organization_logos"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'png'
        filename = f"{current_user.id}_{uuid.uuid4().hex}.{file_extension}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update organization logo URL (stored in user model for now)
        logo_url = f"/uploads/organization_logos/{filename}"
        # You would update an organization model here
        
        logger.info(
            "Organization logo uploaded successfully",
            user_id=current_user.id,
            filename=filename
        )
        
        return BaseResponse(
            success=True,
            message="Organization logo uploaded successfully",
            data={"logo_url": logo_url}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload organization logo", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload organization logo"
        )
