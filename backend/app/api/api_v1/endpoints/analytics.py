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
    EmbedCodeAnalytics,
    HourlyStat,
    SatisfactionStat,
    KPISummary
)
from app.services.auth import AuthService
from app.services.analytics import AnalyticsService
from app.api.api_v1.dependencies import get_current_user
from app.utils.validators import DashboardQueryValidator, AnalyticsFilterValidator

logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get analytics overview for the user"""
    try:
        # Validate input parameters
        query_params = DashboardQueryValidator(days=days)
        
        analytics_service = AnalyticsService(db)
        overview = analytics_service.get_user_overview(current_user.id)
        
        return AnalyticsOverview(**overview)
        
    except ValueError as e:
        logger.warning("Invalid input parameters", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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


@router.get("/hourly", response_model=List[HourlyStat])
async def get_hourly_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated hourly trends for sessions/messages for past N days"""
    try:
        analytics_service = AnalyticsService(db)
        data = analytics_service.get_hourly_trends(current_user.id, days=days)
        return [HourlyStat(**row) for row in data]
    except Exception as e:
        logger.error("Failed to get hourly trends", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hourly trends"
        )


@router.get("/satisfaction", response_model=List[SatisfactionStat])
async def get_satisfaction_stats(
    days: int = Query(30, ge=1, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get daily satisfaction stats for the past N days"""
    try:
        analytics_service = AnalyticsService(db)
        data = analytics_service.get_satisfaction_stats(current_user.id, days=days)
        return [SatisfactionStat(**row) for row in data]
    except Exception as e:
        logger.error("Failed to get satisfaction stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve satisfaction statistics"
        )


@router.get("/kpis", response_model=KPISummary)
async def get_kpis(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get KPI metrics with deltas for the dashboard overview."""
    try:
        analytics_service = AnalyticsService(db)
        data = analytics_service.get_kpis(current_user.id, days=days)
        return KPISummary(**data)
    except Exception as e:
        logger.error("Failed to get KPIs", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve KPIs"
        )


@router.get("/export")
async def export_analytics(
    format: str = Query("json", pattern="^(json|csv)$"),
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
