"""
Comprehensive security middleware for CustomerCareGPT
"""

import time
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
import structlog
import re
import json

from app.core.config import settings
from app.core.database import redis_manager

logger = structlog.get_logger()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add comprehensive security headers"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy
        # In development, allow http/ws to enable local FE/BE communication
        if settings.ENVIRONMENT != "production":
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https: http:; "
                "connect-src 'self' http: https: ws: wss: data:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https: wss:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        response.headers["Content-Security-Policy"] = csp
        
        # HSTS (only in production)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Cache control for sensitive endpoints
        if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/billing"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize all input data"""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS
            r"javascript:",  # XSS
            r"on\w+\s*=",  # Event handlers
            r"union\s+select",  # SQL injection
            r"drop\s+table",  # SQL injection
            r"delete\s+from",  # SQL injection
            r"insert\s+into",  # SQL injection
            r"update\s+set",  # SQL injection
            r"exec\s*\(",  # Command injection
            r"system\s*\(",  # Command injection
            r"eval\s*\(",  # Code injection
            r"<iframe[^>]*>",  # Clickjacking
            r"<object[^>]*>",  # Object injection
            r"<embed[^>]*>",  # Embed injection
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain endpoints
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        # Validate request body
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Check for suspicious patterns in body
                    body_str = body.decode('utf-8', errors='ignore')
                    for pattern in self.compiled_patterns:
                        if pattern.search(body_str):
                            logger.warning(
                                "Suspicious input detected",
                                path=request.url.path,
                                pattern=pattern.pattern,
                                client_ip=request.client.host if request.client else "unknown"
                            )
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Invalid input detected"}
                            )
            except Exception as e:
                logger.error("Input validation error", error=str(e))
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request format"}
                )
        
        # Validate query parameters
        for param_name, param_value in request.query_params.items():
            if isinstance(param_value, str):
                for pattern in self.compiled_patterns:
                    if pattern.search(param_value):
                        logger.warning(
                            "Suspicious query parameter",
                            param=param_name,
                            value=param_value,
                            client_ip=request.client.host if request.client else "unknown"
                        )
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid query parameter"}
                        )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting middleware (Redis-backed with fallback)."""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = {}
        self.cleanup_interval = 60
        self.last_cleanup = time.time()
        self.redis = redis_manager.get_client()
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        identifier = f"{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
        window = 60
        limit = settings.RATE_LIMIT_REQUESTS
        now = int(time.time())
        bucket = now // window
        key = f"rate:{identifier}:{bucket}"
        
        allowed = True
        count = 0
        try:
            count = self.redis.incr(key)
            if count == 1:
                try:
                    self.redis.expire(key, window)
                except Exception:
                    pass
            if count > limit:
                allowed = False
        except Exception:
            # Fallback in-memory
            current_time = time.time()
            if current_time - self.last_cleanup > self.cleanup_interval:
                self._cleanup_old_entries(int(current_time))
                self.last_cleanup = current_time
            window_start = int(current_time) - window
            self.requests.setdefault(identifier, [])
            self.requests[identifier] = [t for t in self.requests[identifier] if t > window_start]
            if len(self.requests[identifier]) >= limit:
                allowed = False
            else:
                self.requests[identifier].append(int(current_time))
                count = len(self.requests[identifier])
        
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later.", "retry_after": window},
                headers={"Retry-After": str(window), "X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(now + window)}
            )
        
        response = await call_next(request)
        remaining = max(0, limit - int(count))
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(now + window)
        return response
    
    def _cleanup_old_entries(self, current_time: int):
        window_start = current_time - 60
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [t for t in self.requests[identifier] if t > window_start]
            if not self.requests[identifier]:
                del self.requests[identifier]


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            content_length=request.headers.get("content-length", "0")
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            process_time=process_time,
            client_ip=request.client.host if request.client else "unknown"
        )
        
        return response


class SecurityExceptionHandler:
    """Handle security-related exceptions"""
    
    @staticmethod
    def handle_security_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle security exceptions with appropriate responses"""
        
        # Log security exception
        logger.warning(
            "Security exception",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else "unknown",
            error_type=type(exc).__name__,
            error_message=str(exc)
        )
        
        # Don't expose internal errors in production
        if settings.ENVIRONMENT == "production":
            if isinstance(exc, HTTPException):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail}
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Internal server error"}
                )
        else:
            # Development mode - show more details
            if isinstance(exc, HTTPException):
                return JSONResponse(
                    status_code=exc.status_code,
                    content={"detail": exc.detail}
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "detail": "Internal server error",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc)
                    }
                )


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = ["/health", "/ready", "/metrics", "/api/v1/auth/login"]
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Skip CSRF check for GET, HEAD, OPTIONS
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)
        
        # If Authorization Bearer token present, treat as API call and skip CSRF (CORS + Auth protects)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)
        
        # Check for CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            logger.warning(
                "Missing CSRF token",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token required"}
            )
        
        # Validate CSRF token (simplified - use proper session-based validation in production)
        if not self._validate_csrf_token(csrf_token):
            logger.warning(
                "Invalid CSRF token",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown"
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"}
            )
        
        return await call_next(request)
    
    def _validate_csrf_token(self, token: str) -> bool:
        """Validate CSRF token (simplified implementation)"""
        # In production, implement proper session-based CSRF validation
        return len(token) >= 32 and token.isalnum()


# Enhanced CORS middleware with security considerations
class SecurityCORSMiddleware(CORSMiddleware):
    """Enhanced CORS middleware with security features"""
    
    def __init__(self, app, allowed_origins: List[str]):
        super().__init__(
            app=app,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            allow_headers=[
                "Accept",
                "Accept-Language",
                "Content-Language",
                "Content-Type",
                "Authorization",
                "X-CSRF-Token",
                "X-Requested-With",
                "X-Client-Version"
            ],
            expose_headers=[
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset"
            ],
            max_age=3600  # 1 hour
        )