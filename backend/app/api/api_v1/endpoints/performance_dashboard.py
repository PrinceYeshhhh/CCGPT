"""
Performance dashboard endpoints for frontend
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import BaseResponse
from pydantic import BaseModel

logger = structlog.get_logger()
router = APIRouter()


class PerformanceSummary(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    response_time_avg: float
    requests_per_second: float
    error_rate: float
    active_connections: int


class PerformanceTrend(BaseModel):
    timestamp: str
    cpu_usage: float
    memory_usage: float
    response_time: float
    requests_count: int


class PerformanceAlert(BaseModel):
    id: str
    type: str
    severity: str
    message: str
    timestamp: str
    resolved: bool


@router.get("/summary")
async def get_performance_summary(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance summary for the last N days"""
    try:
        # Mock performance data - in real implementation, this would come from monitoring
        summary = PerformanceSummary(
            cpu_usage=45.2,
            memory_usage=67.8,
            disk_usage=23.1,
            response_time_avg=245.5,
            requests_per_second=12.3,
            error_rate=0.02,
            active_connections=156
        )
        
        return BaseResponse(
            success=True,
            message="Performance summary retrieved successfully",
            data=summary.dict()
        )
        
    except Exception as e:
        logger.error("Failed to get performance summary", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance summary"
        )


@router.get("/trends")
async def get_performance_trends(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance trends over time"""
    try:
        # Generate mock trend data
        trends = []
        end_time = datetime.utcnow()
        
        for i in range(days * 24):  # Hourly data
            timestamp = end_time - timedelta(hours=i)
            trends.append(PerformanceTrend(
                timestamp=timestamp.isoformat(),
                cpu_usage=45.0 + (i % 20) - 10,  # Mock variation
                memory_usage=65.0 + (i % 15) - 7,
                response_time=200.0 + (i % 100) - 50,
                requests_count=10 + (i % 20)
            ))
        
        trends.reverse()  # Oldest first
        
        return BaseResponse(
            success=True,
            message="Performance trends retrieved successfully",
            data=trends
        )
        
    except Exception as e:
        logger.error("Failed to get performance trends", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance trends"
        )


@router.get("/alerts")
async def get_performance_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current performance alerts"""
    try:
        # Mock alert data
        alerts = [
            PerformanceAlert(
                id="alert_1",
                type="high_memory",
                severity="warning",
                message="Memory usage is above 80%",
                timestamp=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
                resolved=False
            ),
            PerformanceAlert(
                id="alert_2",
                type="slow_response",
                severity="info",
                message="Average response time increased by 15%",
                timestamp=(datetime.utcnow() - timedelta(hours=5)).isoformat(),
                resolved=True
            )
        ]
        
        return BaseResponse(
            success=True,
            message="Performance alerts retrieved successfully",
            data=alerts
        )
        
    except Exception as e:
        logger.error("Failed to get performance alerts", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance alerts"
        )
