"""
Analytics dashboard endpoints for real-time metrics and insights
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.core.database import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.api.api_v1.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive dashboard metrics"""
    try:
        workspace_id = str(current_user.id)
        analytics_service = AnalyticsService(db)
        
        metrics = await analytics_service.get_dashboard_metrics(workspace_id, days)
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error("Failed to get dashboard metrics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard metrics"
        )


@router.get("/realtime")
async def get_real_time_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real-time metrics for live dashboard"""
    try:
        workspace_id = str(current_user.id)
        analytics_service = AnalyticsService(db)
        
        metrics = await analytics_service.get_real_time_metrics(workspace_id)
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error("Failed to get real-time metrics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve real-time metrics"
        )


@router.get("/chat-stats")
async def get_chat_statistics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed chat statistics"""
    try:
        workspace_id = str(current_user.id)
        analytics_service = AnalyticsService(db)
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        chat_metrics = await analytics_service._get_chat_metrics(workspace_id, start_date, end_date)
        
        return {
            "status": "success",
            "data": chat_metrics
        }
        
    except Exception as e:
        logger.error("Failed to get chat statistics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat statistics"
        )


@router.get("/performance")
async def get_performance_metrics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance metrics and response times"""
    try:
        workspace_id = str(current_user.id)
        analytics_service = AnalyticsService(db)
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        performance_metrics = await analytics_service._get_performance_metrics(workspace_id, start_date, end_date)
        
        return {
            "status": "success",
            "data": performance_metrics
        }
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )


@router.get("/embed-stats")
async def get_embed_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get embed widget statistics"""
    try:
        workspace_id = str(current_user.id)
        analytics_service = AnalyticsService(db)
        
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        embed_metrics = await analytics_service._get_embed_metrics(workspace_id, start_date, end_date)
        
        return {
            "status": "success",
            "data": embed_metrics
        }
        
    except Exception as e:
        logger.error("Failed to get embed statistics", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve embed statistics"
        )


@router.post("/track-event")
async def track_custom_event(
    event_type: str,
    event_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Track a custom analytics event"""
    try:
        workspace_id = str(current_user.id)
        analytics_service = AnalyticsService(db)
        
        success = await analytics_service.track_event(workspace_id, event_type, event_data)
        
        if success:
            return {
                "status": "success",
                "message": "Event tracked successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track event"
            )
        
    except Exception as e:
        logger.error("Failed to track event", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track event"
        )
