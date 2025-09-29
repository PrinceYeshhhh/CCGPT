"""
Performance monitoring endpoints for frontend metrics collection
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.models.user import User
from app.api.api_v1.dependencies import get_current_user
from app.services.performance_service import PerformanceService
from app.schemas.performance import (
    PerformanceMetricsRequest,
    PerformanceMetricsResponse,
    PerformanceSummary,
    PerformanceTrends,
    PerformanceAlerts
)

logger = structlog.get_logger()
router = APIRouter()


@router.post("/metrics", response_model=PerformanceMetricsResponse)
async def collect_performance_metrics(
    request: PerformanceMetricsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Collect performance metrics from frontend"""
    try:
        performance_service = PerformanceService(db)
        
        # Store metrics for the current user's workspace
        workspace_id = str(current_user.workspace_id)
        
        result = await performance_service.store_metrics(
            workspace_id=workspace_id,
            user_id=str(current_user.id),
            metrics=request.metrics,
            metadata=request.metadata
        )
        
        logger.info(
            "Performance metrics collected",
            user_id=current_user.id,
            workspace_id=workspace_id,
            metrics_count=len(request.metrics)
        )
        
        return PerformanceMetricsResponse(
            status="success",
            message="Metrics collected successfully",
            stored_count=result.get("stored_count", 0)
        )
        
    except Exception as e:
        logger.error(
            "Failed to collect performance metrics",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect performance metrics"
        )


@router.get("/summary", response_model=PerformanceSummary)
async def get_performance_summary(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance summary for the workspace"""
    try:
        performance_service = PerformanceService(db)
        workspace_id = str(current_user.workspace_id)
        
        summary = await performance_service.get_performance_summary(
            workspace_id=workspace_id,
            days=days
        )
        
        return summary
        
    except Exception as e:
        logger.error(
            "Failed to get performance summary",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance summary"
        )


@router.get("/trends", response_model=PerformanceTrends)
async def get_performance_trends(
    days: int = 30,
    metric_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance trends over time"""
    try:
        performance_service = PerformanceService(db)
        workspace_id = str(current_user.workspace_id)
        
        trends = await performance_service.get_performance_trends(
            workspace_id=workspace_id,
            days=days,
            metric_type=metric_type
        )
        
        return trends
        
    except Exception as e:
        logger.error(
            "Failed to get performance trends",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance trends"
        )


@router.get("/alerts", response_model=List[PerformanceAlerts])
async def get_performance_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get performance alerts for the workspace"""
    try:
        performance_service = PerformanceService(db)
        workspace_id = str(current_user.workspace_id)
        
        alerts = await performance_service.get_performance_alerts(
            workspace_id=workspace_id
        )
        
        return alerts
        
    except Exception as e:
        logger.error(
            "Failed to get performance alerts",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance alerts"
        )


@router.get("/real-time")
async def get_real_time_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get real-time performance metrics"""
    try:
        performance_service = PerformanceService(db)
        workspace_id = str(current_user.workspace_id)
        
        real_time_metrics = await performance_service.get_real_time_metrics(
            workspace_id=workspace_id
        )
        
        return {
            "status": "success",
            "data": real_time_metrics
        }
        
    except Exception as e:
        logger.error(
            "Failed to get real-time metrics",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve real-time metrics"
        )


@router.post("/benchmark")
async def run_performance_benchmark(
    benchmark_type: str = "full",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run performance benchmark for the workspace"""
    try:
        performance_service = PerformanceService(db)
        workspace_id = str(current_user.workspace_id)
        
        benchmark_results = await performance_service.run_benchmark(
            workspace_id=workspace_id,
            benchmark_type=benchmark_type
        )
        
        return {
            "status": "success",
            "data": benchmark_results
        }
        
    except Exception as e:
        logger.error(
            "Failed to run performance benchmark",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run performance benchmark"
        )


@router.get("/health")
async def get_performance_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall performance health status"""
    try:
        performance_service = PerformanceService(db)
        workspace_id = str(current_user.workspace_id)
        
        health_status = await performance_service.get_health_status(
            workspace_id=workspace_id
        )
        
        return {
            "status": "success",
            "data": health_status
        }
        
    except Exception as e:
        logger.error(
            "Failed to get performance health",
            error=str(e),
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance health"
        )
