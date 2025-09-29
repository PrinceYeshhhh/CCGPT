"""
CustomerCareGPT - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import structlog
import os

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.api.websocket.chat_ws import router as websocket_router
from app.db.session import engine
from app.db.base import Base
from app.middleware.security import (
    InputValidationMiddleware,
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityExceptionHandler,
    CSRFProtectionMiddleware
)
from app.middleware.security_headers import SecurityHeadersMiddleware as NewSecurityHeadersMiddleware, create_cors_middleware
from app.utils.error_monitoring import error_monitor, create_error_response, log_api_call

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Rely on Alembic migrations for schema management in all environments

# Initialize FastAPI app
app = FastAPI(
    title="CustomerCareGPT API",
    description="Intelligent customer support automation platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add security middleware (order matters!) - only if enabled
if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(NewSecurityHeadersMiddleware)

if settings.ENABLE_INPUT_VALIDATION:
    app.add_middleware(InputValidationMiddleware)

if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(RateLimitMiddleware)

# Add CSRF protection for production
if settings.ENVIRONMENT == "production":
    app.add_middleware(CSRFProtectionMiddleware)

# CORS is handled by create_cors_middleware below

if settings.ENABLE_REQUEST_LOGGING:
    app.add_middleware(RequestLoggingMiddleware)

# Add security middleware
app.add_middleware(NewSecurityHeadersMiddleware)

# Add trusted host middleware (skip in testing)
if not os.getenv("TESTING"):
    allowed_hosts = getattr(settings, "ALLOWED_HOSTS", ["*"])
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

# Add CORS middleware with security restrictions (must be last)
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)],
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

# Mount static files (skip in testing)
if not os.getenv("TESTING"):
    app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket router
app.include_router(websocket_router, prefix="/ws")

# Include debug router for error monitoring
from app.utils.error_monitoring import router as debug_router
app.include_router(debug_router, prefix="/debug")

# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with security considerations"""
    return SecurityExceptionHandler.handle_security_exception(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with enhanced error monitoring"""
    logger.error(f"Unhandled exception: {exc}", path=request.url.path)
    
    # Log error with full context
    error_context = error_monitor.log_error(
        error=exc,
        context={"path": request.url.path, "method": request.method},
        request=request
    )
    
    # Return standardized error response
    return create_error_response(
        error=exc,
        context={"debug": settings.DEBUG, "error_id": error_context["error_count"]},
        request=request
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CustomerCareGPT API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Basic health check (liveness probe)"""
    from app.utils.health import get_health_status
    return await get_health_status()

@app.get("/ready")
async def readiness_check():
    """Readiness check (readiness probe)"""
    from app.utils.health import get_readiness_status
    return await get_readiness_status()

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with performance metrics"""
    from app.utils.health import get_detailed_health_status
    return await get_detailed_health_status()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from app.utils.metrics import get_metrics, get_metrics_content_type
    from fastapi.responses import Response
    
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting CustomerCareGPT Scaled System")
    
    try:
        # Initialize database with performance optimizations
        from app.core.database import initialize_database
        await initialize_database()
        logger.info("Database initialization completed")
        
        # Initialize other services
        from app.core.queue import queue_manager
        from app.utils.circuit_breaker import circuit_breaker_manager
        
        logger.info("System startup completed successfully")
        
    except Exception as e:
        logger.error(f"System startup failed: {e}")
        raise

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down CustomerCareGPT Scaled System")
    
    try:
        # Stop background workers
        from app.worker.enhanced_worker import enhanced_worker
        enhanced_worker.stop()
        
        logger.info("System shutdown completed")
        
    except Exception as e:
        logger.error(f"System shutdown error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
