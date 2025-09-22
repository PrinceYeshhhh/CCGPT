from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
from datetime import datetime

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceSettings, WorkspaceUpdate, WorkspaceResponse

router = APIRouter()

@router.get("/settings", response_model=WorkspaceSettings)
async def get_workspace_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get workspace settings for the current user."""
    
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    return WorkspaceSettings(
        id=str(workspace.id),
        name=workspace.name,
        description=workspace.description,
        logo_url=workspace.logo_url,
        website_url=workspace.website_url,
        support_email=workspace.support_email,
        timezone=workspace.timezone or "UTC",
        created_at=workspace.created_at.isoformat(),
        updated_at=workspace.updated_at.isoformat()
    )

@router.patch("/settings", response_model=WorkspaceSettings)
async def update_workspace_settings(
    settings: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update workspace settings."""
    
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Update workspace fields
    if settings.name is not None:
        workspace.name = settings.name
    if settings.description is not None:
        workspace.description = settings.description
    if settings.website_url is not None:
        workspace.website_url = settings.website_url
    if settings.support_email is not None:
        workspace.support_email = settings.support_email
    if settings.timezone is not None:
        workspace.timezone = settings.timezone
    
    workspace.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(workspace)
    
    return WorkspaceSettings(
        id=str(workspace.id),
        name=workspace.name,
        description=workspace.description,
        logo_url=workspace.logo_url,
        website_url=workspace.website_url,
        support_email=workspace.support_email,
        timezone=workspace.timezone or "UTC",
        created_at=workspace.created_at.isoformat(),
        updated_at=workspace.updated_at.isoformat()
    )

@router.post("/upload-logo")
async def upload_workspace_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload workspace logo."""
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (5MB limit)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
    filename = f"{uuid.uuid4()}{file_extension}"
    
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads/logos"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Update workspace logo URL
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Generate URL (in production, this would be a CDN URL)
    logo_url = f"/uploads/logos/{filename}"
    workspace.logo_url = logo_url
    workspace.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "logo_url": logo_url,
        "message": "Logo uploaded successfully"
    }

@router.delete("/logo")
async def delete_workspace_logo(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete workspace logo."""
    
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Delete file if it exists
    if workspace.logo_url:
        file_path = workspace.logo_url.lstrip('/')
        if os.path.exists(file_path):
            os.remove(file_path)
    
    # Clear logo URL
    workspace.logo_url = None
    workspace.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Logo deleted successfully"
    }

@router.get("/info", response_model=WorkspaceResponse)
async def get_workspace_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get basic workspace information."""
    
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    return WorkspaceResponse(
        id=str(workspace.id),
        name=workspace.name,
        description=workspace.description,
        logo_url=workspace.logo_url,
        created_at=workspace.created_at.isoformat()
    )
