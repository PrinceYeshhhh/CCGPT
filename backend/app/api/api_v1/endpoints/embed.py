"""
Embed code management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import structlog

from app.core.database import get_db
from app.models.user import User
from app.schemas.embed import (
    EmbedCodeCreate, 
    EmbedCodeResponse, 
    EmbedCodeUpdate,
    WidgetConfig
)
from app.services.auth import AuthService
from app.api.api_v1.dependencies import get_current_user
from app.services.embed import EmbedService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/codes", response_model=EmbedCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_embed_code(
    embed_data: EmbedCodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new embed code"""
    try:
        embed_service = EmbedService(db)
        
        # Validate widget config
        widget_config = WidgetConfig(**embed_data.widget_config)
        
        # Create embed code
        embed_code = embed_service.create_embed_code(
            user_id=current_user.id,
            code_name=embed_data.code_name,
            widget_config=widget_config.dict()
        )
        
        logger.info(
            "Embed code created successfully",
            user_id=current_user.id,
            embed_code_id=embed_code.id,
            code_name=embed_code.code_name
        )
        
        return EmbedCodeResponse.from_orm(embed_code)
        
    except Exception as e:
        logger.error(
            "Embed code creation failed",
            error=str(e),
            user_id=current_user.id,
            code_name=embed_data.code_name
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create embed code"
        )


@router.get("/codes", response_model=List[EmbedCodeResponse])
async def get_embed_codes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's embed codes"""
    try:
        embed_service = EmbedService(db)
        embed_codes = embed_service.get_user_embed_codes(current_user.id)
        
        return [EmbedCodeResponse.from_orm(code) for code in embed_codes]
        
    except Exception as e:
        logger.error("Failed to get embed codes", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed codes"
        )


@router.get("/codes/{code_id}", response_model=EmbedCodeResponse)
async def get_embed_code(
    code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific embed code"""
    try:
        embed_service = EmbedService(db)
        embed_code = embed_service.get_embed_code_by_id(code_id, current_user.id)
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        return EmbedCodeResponse.from_orm(embed_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed code"
        )


@router.put("/codes/{code_id}", response_model=EmbedCodeResponse)
async def update_embed_code(
    code_id: int,
    embed_data: EmbedCodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an embed code"""
    try:
        embed_service = EmbedService(db)
        
        # Validate widget config if provided
        if embed_data.widget_config:
            widget_config = WidgetConfig(**embed_data.widget_config)
            embed_data.widget_config = widget_config.dict()
        
        embed_code = embed_service.update_embed_code(
            code_id=code_id,
            user_id=current_user.id,
            update_data=embed_data.dict(exclude_unset=True)
        )
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        logger.info(
            "Embed code updated successfully",
            user_id=current_user.id,
            embed_code_id=code_id
        )
        
        return EmbedCodeResponse.from_orm(embed_code)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update embed code"
        )


@router.delete("/codes/{code_id}")
async def delete_embed_code(
    code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an embed code"""
    try:
        embed_service = EmbedService(db)
        success = embed_service.delete_embed_code(code_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        logger.info(
            "Embed code deleted successfully",
            user_id=current_user.id,
            embed_code_id=code_id
        )
        
        return {"message": "Embed code deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete embed code"
        )


@router.post("/codes/{code_id}/regenerate")
async def regenerate_embed_code(
    code_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate embed code script"""
    try:
        embed_service = EmbedService(db)
        embed_code = embed_service.regenerate_embed_code(code_id, current_user.id)
        
        if not embed_code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found"
            )
        
        logger.info(
            "Embed code regenerated successfully",
            user_id=current_user.id,
            embed_code_id=code_id
        )
        
        return {"message": "Embed code regenerated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to regenerate embed code",
            error=str(e),
            user_id=current_user.id,
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate embed code"
        )


@router.get("/widget/{code_id}")
async def get_widget_script(
    code_id: int,
    db: Session = Depends(get_db)
):
    """Get widget script for embedding (public endpoint)"""
    try:
        embed_service = EmbedService(db)
        script_content = embed_service.get_widget_script(code_id)
        
        if not script_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embed code not found or inactive"
            )
        
        # Update usage count
        embed_service.increment_usage(code_id)
        
        return {"script": script_content}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get widget script",
            error=str(e),
            code_id=code_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget script"
        )
