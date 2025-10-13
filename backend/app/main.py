"""
CustomerCareGPT - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager
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
from app.middleware.logging_middleware import (
    RequestContextMiddleware,
    PerformanceLoggingMiddleware,
    SecurityLoggingMiddleware
)
from app.middleware.error_handler_middleware import (
    GlobalErrorHandlerMiddleware,
    ErrorRecoveryMiddleware,
    ErrorMetricsMiddleware
)
from app.middleware.performance_middleware import (
    PerformanceMonitoringMiddleware,
    CacheOptimizationMiddleware,
    DatabaseQueryOptimizationMiddleware,
    MemoryOptimizationMiddleware
)
from app.middleware.security_headers import SecurityHeadersMiddleware as NewSecurityHeadersMiddleware, create_cors_middleware
from app.utils.error_monitoring import error_monitor, create_error_response, log_api_call
from app.utils.observability import init_observability
from app.utils.backup_init import initialize_backup_system, shutdown_backup_system

# Configure structured logging
from app.utils.logging_config import configure_logging
configure_logging()

logger = structlog.get_logger()

# Rely on Alembic migrations for schema management in all environments

# Initialize observability (safe no-op if disabled)
init_observability("customercaregpt-backend")

# Background task for connection monitoring
import asyncio
from app.core.database import db_manager

async def connection_monitor():
    """Periodic connection monitoring and cleanup"""
    while True:
        try:
            db_manager.monitor_connections()
            await asyncio.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error("Connection monitoring task failed", error=str(e))
            await asyncio.sleep(60)  # Wait 1 minute before retrying

# Connection monitoring will be started in the startup event

# Initialize FastAPI app

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
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
        import os
        
        is_testing = os.getenv("TESTING") == "true" or os.getenv("ENVIRONMENT") == "testing"

        # Initialize backup system (skip in tests)
        if not is_testing:
            await initialize_backup_system()
            logger.info("Backup system initialization completed")
        else:
            logger.info("Skipping backup system initialization in testing mode")

        # Initialize performance service (skip in tests)
        if not is_testing:
            from app.services.performance_service import performance_service
            performance_service.start()
            logger.info("Performance service initialization completed")
        else:
            logger.info("Skipping performance service in testing mode")
        
        # Start connection monitoring task (skip in tests)
        if not is_testing:
            asyncio.create_task(connection_monitor())
            logger.info("Connection monitoring started")
        else:
            logger.info("Skipping connection monitor in testing mode")
        
        logger.info("System startup completed successfully")
        
    except Exception as e:
        logger.error(f"System startup failed: {e}")
        raise

# Shutdown event
    
    yield
    
    # Shutdown
    """Cleanup on shutdown"""
    logger.info("Shutting down CustomerCareGPT Scaled System")
    
    try:
        # Stop background workers
        from app.worker.enhanced_worker import enhanced_worker
        enhanced_worker.stop()
        
        # Shutdown backup system
        await shutdown_backup_system()
        logger.info("Backup system shutdown completed")

        # Shutdown performance service
        from app.services.performance_service import performance_service
        performance_service.stop()
        logger.info("Performance service shutdown completed")
        
        logger.info("System shutdown completed")
        
    except Exception as e:
        logger.error(f"System shutdown error: {e}")

app = FastAPI(
    title="CustomerCareGPT API",
    description="Intelligent customer support automation platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# IMPORTANT: Install CORS first so preflight requests are handled before other middleware
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [str(settings.CORS_ORIGINS)],
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

# Security and request middlewares (order after CORS)
if settings.ENABLE_SECURITY_HEADERS:
    app.add_middleware(NewSecurityHeadersMiddleware)

# Add error handling middlewares (order matters - error handlers should be first)
app.add_middleware(ErrorMetricsMiddleware)
app.add_middleware(ErrorRecoveryMiddleware, max_failures=5, recovery_timeout=60)
app.add_middleware(GlobalErrorHandlerMiddleware)

# Add performance optimization middlewares
app.add_middleware(MemoryOptimizationMiddleware)
app.add_middleware(DatabaseQueryOptimizationMiddleware)
app.add_middleware(CacheOptimizationMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware, slow_request_threshold=1.0)

# Add logging middlewares
app.add_middleware(RequestContextMiddleware)
app.add_middleware(PerformanceLoggingMiddleware, slow_request_threshold_ms=1000.0)
app.add_middleware(SecurityLoggingMiddleware)

if settings.ENABLE_REQUEST_LOGGING:
    app.add_middleware(RequestLoggingMiddleware)

if settings.ENABLE_INPUT_VALIDATION:
    app.add_middleware(InputValidationMiddleware)

if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(RateLimitMiddleware)

# Add CSRF protection for production
if settings.ENVIRONMENT == "production":
    app.add_middleware(CSRFProtectionMiddleware)

# Add trusted host middleware (skip in testing)
if not os.getenv("TESTING"):
    allowed_hosts = getattr(settings, "ALLOWED_HOSTS", ["*"])
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

# CORS already installed earlier

# Mount static files (skip in testing)
if not os.getenv("TESTING"):
    # Resolve uploads directory relative to project structure and ensure it exists
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    uploads_dir = os.path.abspath(os.path.join(base_dir, "uploads"))
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/static", StaticFiles(directory=uploads_dir), name="static")

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

# Add custom error handlers
from app.utils.error_handling import handle_exception, CustomError, ValidationError, AuthenticationError, AuthorizationError, NotFoundError, DatabaseError, ExternalAPIError, RateLimitError

@app.exception_handler(CustomError)
async def custom_error_handler(request: Request, exc: CustomError):
    """Handle custom errors"""
    return handle_exception(exc, request)

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    return handle_exception(exc, request)

@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    return handle_exception(exc, request)

@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors"""
    return handle_exception(exc, request)

@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle not found errors"""
    return handle_exception(exc, request)

@app.exception_handler(DatabaseError)
async def database_error_handler(request: Request, exc: DatabaseError):
    """Handle database errors"""
    return handle_exception(exc, request)

@app.exception_handler(ExternalAPIError)
async def external_api_error_handler(request: Request, exc: ExternalAPIError):
    """Handle external API errors"""
    return handle_exception(exc, request)

@app.exception_handler(RateLimitError)
async def rate_limit_error_handler(request: Request, exc: RateLimitError):
    """Handle rate limit errors"""
    return handle_exception(exc, request)

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

@app.get("/health/external")
async def external_services_health_check():
    """Check external services like Gemini API, Stripe, etc."""
    from app.utils.health import get_external_services_status
    return await get_external_services_status()

@app.get("/health/startup")
async def startup_health_check():
    """Startup health check for application initialization"""
    from app.utils.health import get_startup_checks
    return await get_startup_checks()

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
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
