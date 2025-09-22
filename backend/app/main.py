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
    SecurityHeadersMiddleware,
    InputValidationMiddleware,
    RateLimitMiddleware,
    CORSMiddleware as SecurityCORSMiddleware,
    RequestLoggingMiddleware,
    SecurityExceptionHandler
)

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

# Create database tables (skip in testing)
if not os.getenv("TESTING"):
    Base.metadata.create_all(bind=engine)

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
    app.add_middleware(SecurityHeadersMiddleware)

if settings.ENABLE_INPUT_VALIDATION:
    app.add_middleware(InputValidationMiddleware)

if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(RateLimitMiddleware)

if settings.ENABLE_CORS:
    app.add_middleware(SecurityCORSMiddleware, allowed_origins=settings.CORS_ORIGINS)

if settings.ENABLE_REQUEST_LOGGING:
    app.add_middleware(RequestLoggingMiddleware)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Mount static files (skip in testing)
if not os.getenv("TESTING"):
    app.mount("/static", StaticFiles(directory="uploads"), name="static")

# Include API router
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket router
app.include_router(websocket_router, prefix="/ws")

# Add exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with security considerations"""
    return SecurityExceptionHandler.handle_security_exception(request, exc)

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with security considerations"""
    logger.error(f"Unhandled exception: {exc}", path=request.url.path)
    return SecurityExceptionHandler.handle_security_exception(request, exc)

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
