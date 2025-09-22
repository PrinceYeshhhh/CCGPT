"""
Analytics endpoints for usage statistics and insights
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
import structlog

from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverview,
    DocumentAnalytics,
    SessionAnalytics,
    MessageAnalytics,
    UsageStats,
    EmbedCodeAnalytics
)
from app.services.auth import AuthService
from app.services.analytics import AnalyticsService
from app.api.api_v1.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics overview for the user"""
    try:
        analytics_service = AnalyticsService(db)
        overview = analytics_service.get_user_overview(current_user.id)
        
        return AnalyticsOverview(**overview)
        
    except Exception as e:
        logger.error("Failed to get analytics overview", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics overview"
        )


@router.get("/documents", response_model=List[DocumentAnalytics])
async def get_document_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document analytics"""
    try:
        analytics_service = AnalyticsService(db)
        documents = analytics_service.get_document_analytics(current_user.id)
        
        return [DocumentAnalytics.from_orm(doc) for doc in documents]
        
    except Exception as e:
        logger.error("Failed to get document analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document analytics"
        )


@router.get("/sessions", response_model=List[SessionAnalytics])
async def get_session_analytics(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get session analytics"""
    try:
        analytics_service = AnalyticsService(db)
        sessions = analytics_service.get_session_analytics(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        return [SessionAnalytics.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error("Failed to get session analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session analytics"
        )


@router.get("/messages", response_model=List[MessageAnalytics])
async def get_message_analytics(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    flagged_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get message analytics"""
    try:
        analytics_service = AnalyticsService(db)
        messages = analytics_service.get_message_analytics(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            flagged_only=flagged_only
        )
        
        return [MessageAnalytics.from_orm(message) for message in messages]
        
    except Exception as e:
        logger.error("Failed to get message analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve message analytics"
        )


@router.get("/usage-stats", response_model=List[UsageStats])
async def get_usage_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics over time"""
    try:
        analytics_service = AnalyticsService(db)
        stats = analytics_service.get_usage_stats(
            user_id=current_user.id,
            days=days
        )
        
        return [UsageStats(**stat) for stat in stats]
        
    except Exception as e:
        logger.error("Failed to get usage stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.get("/embed-codes", response_model=List[EmbedCodeAnalytics])
async def get_embed_code_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get embed code analytics"""
    try:
        analytics_service = AnalyticsService(db)
        embed_codes = analytics_service.get_embed_code_analytics(current_user.id)
        
        return [EmbedCodeAnalytics.from_orm(code) for code in embed_codes]
        
    except Exception as e:
        logger.error("Failed to get embed code analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed code analytics"
        )


@router.get("/export")
async def export_analytics(
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export analytics data"""
    try:
        analytics_service = AnalyticsService(db)
        export_data = analytics_service.export_analytics(
            user_id=current_user.id,
            format=format,
            start_date=start_date,
            end_date=end_date
        )
        
        if format == "csv":
            return {"data": export_data, "content_type": "text/csv"}
        else:
            return {"data": export_data, "content_type": "application/json"}
        
    except Exception as e:
        logger.error("Failed to export analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics data"
        )
