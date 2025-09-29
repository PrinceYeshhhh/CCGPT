"""
Comprehensive analytics endpoints for the Analytics dashboard page
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import structlog

from app.core.database import get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.embed import EmbedCode
from app.api.api_v1.dependencies import get_current_user
from app.services.analytics_service import AnalyticsService

logger = structlog.get_logger()
router = APIRouter()


@router.get("/detailed-overview")
async def get_detailed_analytics_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed analytics overview for the Analytics page"""
    try:
        workspace_id = str(current_user.workspace_id)
        analytics_service = AnalyticsService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get all metrics in parallel
        metrics = await analytics_service.get_dashboard_metrics(workspace_id, days)
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error("Failed to get analytics overview", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics overview"
        )


@router.get("/detailed-usage-stats")
async def get_detailed_usage_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get usage statistics over time for charts"""
    try:
        workspace_id = str(current_user.workspace_id)
        analytics_service = AnalyticsService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily usage stats
        usage_stats = await analytics_service._get_usage_metrics(workspace_id, start_date, end_date)
        
        return {
            "status": "success",
            "data": usage_stats
        }
        
    except Exception as e:
        logger.error("Failed to get usage stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.get("/detailed-hourly")
async def get_detailed_hourly_trends(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get hourly query distribution"""
    try:
        workspace_id = str(current_user.workspace_id)
        analytics_service = AnalyticsService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get hourly trends
        hourly_stats = await analytics_service._get_hourly_metrics(workspace_id, start_date, end_date)
        
        return {
            "status": "success",
            "data": hourly_stats
        }
        
    except Exception as e:
        logger.error("Failed to get hourly trends", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve hourly trends"
        )


@router.get("/detailed-satisfaction")
async def get_detailed_satisfaction_stats(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get satisfaction statistics"""
    try:
        workspace_id = str(current_user.workspace_id)
        analytics_service = AnalyticsService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get satisfaction metrics
        satisfaction_stats = await analytics_service._get_satisfaction_metrics(workspace_id, start_date, end_date)
        
        return {
            "status": "success",
            "data": satisfaction_stats
        }
        
    except Exception as e:
        logger.error("Failed to get satisfaction stats", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve satisfaction statistics"
        )


@router.get("/detailed-top-questions")
async def get_detailed_top_questions(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    limit: int = Query(10, ge=1, le=50, description="Number of top questions to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get most frequently asked questions"""
    try:
        workspace_id = str(current_user.workspace_id)
        analytics_service = AnalyticsService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get top questions
        top_questions = await analytics_service._get_top_questions(workspace_id, start_date, end_date, limit)
        
        return {
            "status": "success",
            "data": top_questions
        }
        
    except Exception as e:
        logger.error("Failed to get top questions", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve top questions"
        )


@router.get("/detailed-export")
async def export_detailed_analytics_data(
    format: str = Query("json", pattern="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export analytics data"""
    try:
        workspace_id = str(current_user.workspace_id)
        analytics_service = AnalyticsService(db)
        
        # Get all analytics data
        export_data = await analytics_service.export_analytics_data(workspace_id, days, format)
        
        return {
            "status": "success",
            "data": export_data,
            "format": format
        }
        
    except Exception as e:
        logger.error("Failed to export analytics data", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics data"
        )
