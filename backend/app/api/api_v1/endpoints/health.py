"""
Health check and readiness probe endpoints
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional

from app.utils.health import get_health_status, get_readiness_status, get_startup_checks
from app.utils.metrics import get_metrics, get_metrics_content_type
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Basic health check endpoint (liveness probe)
    
    Returns simple status to indicate the service is alive.
    Used by Kubernetes liveness probes.
    """
    try:
        status = await get_health_status()
        return JSONResponse(content=status, status_code=200)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={"status": "unhealthy", "error": str(e)},
            status_code=503
        )

@router.get("/ready")
async def readiness_check(
    components: Optional[List[str]] = Query(None, description="Specific components to check")
):
    """
    Readiness check endpoint (readiness probe)
    
    Checks all critical dependencies and returns detailed status.
    Used by Kubernetes readiness probes.
    """
    try:
        status = await get_readiness_status(components)
        
        # Return 200 if healthy, 503 if unhealthy
        if status["status"] == "healthy":
            return JSONResponse(content=status, status_code=200)
        else:
            return JSONResponse(content=status, status_code=503)
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "unknown"
            },
            status_code=503
        )

@router.get("/startup")
async def startup_check():
    """
    Startup check endpoint
    
    Comprehensive check of all components during startup.
    Used for initial service validation.
    """
    try:
        status = await get_startup_checks()
        return JSONResponse(content=status, status_code=200)
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": "unknown"
            },
            status_code=503
        )

@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus format for monitoring.
    """
    try:
        metrics_data = get_metrics()
        return JSONResponse(
            content=metrics_data,
            media_type=get_metrics_content_type(),
            status_code=200
        )
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
        return JSONResponse(
            content={"error": "Metrics unavailable"},
            status_code=503
        )

@router.get("/status")
async def status_check():
    """
    Detailed status endpoint
    
    Returns comprehensive service status including version info.
    """
    try:
        # Get basic health
        health = await get_health_status()
        
        # Get readiness status
        readiness = await get_readiness_status()
        
        # Combine status information
        status = {
            "service": "CustomerCareGPT API",
            "version": "1.0.0",
            "health": health,
            "readiness": readiness,
            "timestamp": health["timestamp"]
        }
        
        # Determine overall status
        if health["status"] == "healthy" and readiness["status"] == "healthy":
            status["overall_status"] = "healthy"
            return JSONResponse(content=status, status_code=200)
        else:
            status["overall_status"] = "unhealthy"
            return JSONResponse(content=status, status_code=503)
            
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return JSONResponse(
            content={
                "service": "CustomerCareGPT API",
                "version": "1.0.0",
                "overall_status": "error",
                "error": str(e)
            },
            status_code=503
        )
