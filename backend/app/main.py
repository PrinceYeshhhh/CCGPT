"""
CustomerCareGPT - Main FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import structlog

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

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="CustomerCareGPT API",
    description="Intelligent customer support automation platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add security middleware (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityCORSMiddleware, allowed_origins=settings.CORS_ORIGINS)
app.add_middleware(RequestLoggingMiddleware)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Mount static files
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
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
