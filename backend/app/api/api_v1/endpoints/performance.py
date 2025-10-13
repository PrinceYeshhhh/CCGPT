# Performance Monitoring and Optimization API Endpoints
# Administrative endpoints for performance management

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.services.performance_service import performance_service
from app.services.query_optimizer import query_monitor, db_optimizer
from app.services.cache_service import cache_service
from app.utils.logging_config import business_logger, security_logger
from app.utils.error_handling import CustomError, AuthorizationError

router = APIRouter()

class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    db_connections_active: int
    db_connections_idle: int
    redis_connections: int
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    requests_per_second: float

class OptimizationRecommendationResponse(BaseModel):
    """Response model for optimization recommendations"""
    category: str
    priority: str
    title: str
    description: str
    impact: str
    effort: str
    current_value: str
    recommended_value: str
    estimated_improvement: str

class PerformanceDashboardResponse(BaseModel):
    """Response model for performance dashboard"""
    current_metrics: Optional[Dict[str, Any]]
    metrics_history: List[Dict[str, Any]]
    recommendations: List[OptimizationRecommendationResponse]
    optimization_summary: Dict[str, Any]
    recent_alerts: List[Dict[str, Any]]
    query_performance: Dict[str, Any]
    cache_statistics: Dict[str, Any]
    system_info: Dict[str, Any]

class PerformanceAlertResponse(BaseModel):
    """Response model for performance alerts"""
    timestamp: datetime
    metric: str
    value: float
    threshold: float
    severity: str

@router.get("/dashboard", response_model=PerformanceDashboardResponse)
async def get_performance_dashboard(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get comprehensive performance dashboard data.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        dashboard_data = await performance_service.get_performance_dashboard()
        
        logger.info(
            "Performance dashboard accessed",
            user_id=str(current_user.id)
        )
        
        return PerformanceDashboardResponse(**dashboard_data)
        
    except Exception as e:
        logger.error(
            "Failed to get performance dashboard",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance dashboard: {str(e)}"
        )

@router.get("/metrics/current", response_model=Optional[PerformanceMetricsResponse])
async def get_current_metrics(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get current performance metrics.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        current_metrics = performance_service.monitor.get_current_metrics()
        
        if not current_metrics:
            return None
        
        return PerformanceMetricsResponse(**current_metrics.__dict__)
        
    except Exception as e:
        logger.error(
            "Failed to get current metrics",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current metrics: {str(e)}"
        )

@router.get("/metrics/history", response_model=List[PerformanceMetricsResponse])
async def get_metrics_history(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get performance metrics history.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        history = performance_service.monitor.get_metrics_history(hours)
        
        return [PerformanceMetricsResponse(**metrics.__dict__) for metrics in history]
        
    except Exception as e:
        logger.error(
            "Failed to get metrics history",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics history: {str(e)}"
        )

@router.get("/recommendations", response_model=List[OptimizationRecommendationResponse])
async def get_optimization_recommendations(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get performance optimization recommendations.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        recommendations = await performance_service.optimizer.analyze_performance()
        
        return [
            OptimizationRecommendationResponse(
                category=rec.category,
                priority=rec.priority,
                title=rec.title,
                description=rec.description,
                impact=rec.impact,
                effort=rec.effort,
                current_value=rec.current_value,
                recommended_value=rec.recommended_value,
                estimated_improvement=rec.estimated_improvement
            )
            for rec in recommendations
        ]
        
    except Exception as e:
        logger.error(
            "Failed to get optimization recommendations",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get optimization recommendations: {str(e)}"
        )

@router.get("/alerts", response_model=List[PerformanceAlertResponse])
async def get_performance_alerts(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get recent performance alerts.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        alerts = performance_service.monitor.get_alerts(hours)
        
        return [
            PerformanceAlertResponse(
                timestamp=alert["timestamp"],
                metric=alert["metric"],
                value=alert["value"],
                threshold=alert["threshold"],
                severity=alert["severity"]
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(
            "Failed to get performance alerts",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance alerts: {str(e)}"
        )

@router.post("/alerts/clear")
async def clear_performance_alerts(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Clear all performance alerts.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="clear_performance_alerts"
    )
    
    try:
        await performance_service.clear_alerts()
        
        logger.info(
            "Performance alerts cleared",
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Performance alerts cleared successfully"}
        )
        
    except Exception as e:
        logger.error(
            "Failed to clear performance alerts",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear performance alerts: {str(e)}"
        )

@router.post("/optimize/{recommendation_id}")
async def apply_optimization(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Apply a specific optimization recommendation.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="apply_optimization",
        recommendation_id=recommendation_id
    )
    
    try:
        success = await performance_service.apply_optimization(recommendation_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to apply optimization"
            )
        
        logger.info(
            "Optimization applied",
            recommendation_id=recommendation_id,
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Optimization applied successfully",
                "recommendation_id": recommendation_id
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to apply optimization",
            recommendation_id=recommendation_id,
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply optimization: {str(e)}"
        )

@router.get("/query-performance")
async def get_query_performance(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get database query performance analysis.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        query_analysis = await db_optimizer.analyze_query_performance()
        
        return query_analysis
        
    except Exception as e:
        logger.error(
            "Failed to get query performance analysis",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get query performance analysis: {str(e)}"
        )

@router.get("/database-stats")
async def get_database_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get comprehensive database statistics.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        db_stats = await db_optimizer.get_database_stats()
        
        return db_stats
        
    except Exception as e:
        logger.error(
            "Failed to get database stats",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database stats: {str(e)}"
        )

@router.get("/cache-stats")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get cache performance statistics.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        cache_stats = await cache_service.get_stats()
        
        return cache_stats
        
    except Exception as e:
        logger.error(
            "Failed to get cache stats",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )

@router.post("/cache/clear")
async def clear_cache(
    namespace: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Clear cache data.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    security_logger.log_backup_operation(
        user_id=str(current_user.id),
        operation="clear_cache",
        namespace=namespace
    )
    
    try:
        if namespace:
            deleted_count = await cache_service.delete_pattern(f"{namespace}:*")
            message = f"Cleared {deleted_count} cache entries for namespace '{namespace}'"
        else:
            success = await cache_service.clear()
            message = "Cache cleared successfully" if success else "Failed to clear cache"
        
        logger.info(
            "Cache cleared",
            namespace=namespace,
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": message}
        )
        
    except Exception as e:
        logger.error(
            "Failed to clear cache",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )

@router.get("/connection-pool")
async def get_connection_pool_stats(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get database connection pool statistics.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        pool_analysis = await db_optimizer.optimize_connection_pool()
        
        return pool_analysis
        
    except Exception as e:
        logger.error(
            "Failed to get connection pool stats",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connection pool stats: {str(e)}"
        )

@router.get("/suggest-indexes")
async def suggest_database_indexes(
    workspace_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Get database index suggestions.
    
    Requires admin privileges.
    """
    # Check if user has admin privileges
    if not current_user.is_admin:
        raise AuthorizationError("Admin privileges required for performance monitoring")
    
    try:
        suggestions = await db_optimizer.suggest_indexes(workspace_id or "default")
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        logger.error(
            "Failed to get index suggestions",
            error=str(e),
            user_id=str(current_user.id),
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get index suggestions: {str(e)}"
        )