"""
Error monitoring and debugging utilities for production deployment
"""

import structlog
import traceback
import json
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import aiohttp

logger = structlog.get_logger()

class ErrorMonitor:
    """Centralized error monitoring and logging"""
    
    def __init__(self):
        self.error_count = 0
        self.error_types = {}
        self.recent_errors = []
    
    def log_error(self, 
                  error: Exception, 
                  context: Optional[Dict[str, Any]] = None,
                  request: Optional[Request] = None,
                  user_id: Optional[str] = None):
        """Log an error with full context"""
        
        self.error_count += 1
        error_type = type(error).__name__
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
        
        # Build error context
        error_context = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "error_count": self.error_count,
            "user_id": user_id,
            "context": context or {}
        }
        
        # Add request context if available
        if request:
            error_context.update({
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "referer": request.headers.get("referer")
            })
        
        # Store recent errors (keep last 100)
        self.recent_errors.append(error_context)
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)
        
        # Log with structured logging
        logger.error(
            "Error occurred",
            error_type=error_type,
            error_message=str(error),
            traceback=traceback.format_exc(),
            context=context,
            user_id=user_id,
            request_method=request.method if request else None,
            request_url=str(request.url) if request else None
        )
        
        return error_context
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        return {
            "total_errors": self.error_count,
            "error_types": self.error_types,
            "recent_errors": self.recent_errors[-10:],  # Last 10 errors
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def clear_errors(self):
        """Clear error history"""
        self.error_count = 0
        self.error_types = {}
        self.recent_errors = []

# Global error monitor instance
error_monitor = ErrorMonitor()

def create_error_response(error: Exception, 
                         status_code: int = 500,
                         context: Optional[Dict[str, Any]] = None,
                         request: Optional[Request] = None,
                         user_id: Optional[str] = None) -> JSONResponse:
    """Create a standardized error response"""
    
    # Log the error
    error_context = error_monitor.log_error(error, context, request, user_id)
    
    # Create error response
    error_response = {
        "error": True,
        "message": "An internal server error occurred",
        "error_id": error_context["error_count"],
        "timestamp": error_context["timestamp"]
    }
    
    # Add debug info in development
    if context and context.get("debug", False):
        error_response.update({
            "error_type": error_context["error_type"],
            "error_message": error_context["error_message"],
            "traceback": error_context["traceback"]
        })
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )

async def test_api_connectivity(base_url: str) -> Dict[str, Any]:
    """Test API connectivity and return results"""
    results = {
        "base_url": base_url,
        "tests": {},
        "overall_status": "unknown"
    }
    
    test_endpoints = [
        ("/health", "Health Check"),
        ("/api/v1/", "API Root"),
        ("/api/v1/auth/", "Auth Endpoint"),
        ("/api/v1/documents/", "Documents Endpoint")
    ]
    
    async with aiohttp.ClientSession() as session:
        for endpoint, name in test_endpoints:
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(url, timeout=10) as response:
                    results["tests"][name] = {
                        "status": "success",
                        "status_code": response.status,
                        "url": url,
                        "response_time": "N/A"  # Could add timing
                    }
            except Exception as e:
                results["tests"][name] = {
                    "status": "error",
                    "error": str(e),
                    "url": url
                }
    
    # Determine overall status
    successful_tests = sum(1 for test in results["tests"].values() if test["status"] == "success")
    total_tests = len(results["tests"])
    
    if successful_tests == total_tests:
        results["overall_status"] = "healthy"
    elif successful_tests > 0:
        results["overall_status"] = "partial"
    else:
        results["overall_status"] = "unhealthy"
    
    return results

def log_api_call(request: Request, response, duration_ms: float):
    """Log API call details for debugging"""
    logger.info(
        "API call",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        duration_ms=duration_ms,
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

def log_database_operation(operation: str, table: str, duration_ms: float, success: bool):
    """Log database operations for debugging"""
    logger.info(
        "Database operation",
        operation=operation,
        table=table,
        duration_ms=duration_ms,
        success=success
    )

def log_redis_operation(operation: str, key: str, duration_ms: float, success: bool):
    """Log Redis operations for debugging"""
    logger.info(
        "Redis operation",
        operation=operation,
        key=key,
        duration_ms=duration_ms,
        success=success
    )

def log_chromadb_operation(operation: str, collection: str, duration_ms: float, success: bool):
    """Log ChromaDB operations for debugging"""
    logger.info(
        "ChromaDB operation",
        operation=operation,
        collection=collection,
        duration_ms=duration_ms,
        success=success
    )

# Error monitoring endpoints
from fastapi import APIRouter
router = APIRouter()

@router.get("/debug/errors")
async def get_error_summary():
    """Get error summary for debugging"""
    return error_monitor.get_error_summary()

@router.get("/debug/health")
async def get_debug_health():
    """Get detailed health information for debugging"""
    from app.core.config import settings
    
    health_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        "database_url": settings.DATABASE_URL[:20] + "..." if settings.DATABASE_URL else None,
        "redis_url": settings.REDIS_URL[:20] + "..." if settings.REDIS_URL else None,
        "chroma_url": settings.CHROMA_URL,
        "cors_origins": settings.CORS_ORIGINS,
        "error_summary": error_monitor.get_error_summary()
    }
    
    return health_info

@router.get("/debug/test-connectivity")
async def test_connectivity():
    """Test connectivity to all services"""
    from app.core.config import settings
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }
    
    # Test database
    try:
        from app.core.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        results["tests"]["database"] = {"status": "success", "message": "Database connected"}
    except Exception as e:
        results["tests"]["database"] = {"status": "error", "message": str(e)}
    
    # Test Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        results["tests"]["redis"] = {"status": "success", "message": "Redis connected"}
    except Exception as e:
        results["tests"]["redis"] = {"status": "error", "message": str(e)}
    
    # Test ChromaDB
    try:
        import requests
        response = requests.get(f"{settings.CHROMA_URL}/api/v1/heartbeat", timeout=5)
        if response.status_code == 200:
            results["tests"]["chromadb"] = {"status": "success", "message": "ChromaDB connected"}
        else:
            results["tests"]["chromadb"] = {"status": "error", "message": f"Status {response.status_code}"}
    except Exception as e:
        results["tests"]["chromadb"] = {"status": "error", "message": str(e)}
    
    return results
