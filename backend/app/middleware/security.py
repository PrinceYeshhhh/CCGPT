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
    """Enhanced input validation and sanitization middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.suspicious_patterns = [
            # XSS patterns
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"data:text/html",
            r"on\w+\s*=",  # Event handlers
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<form[^>]*>",
            r"<input[^>]*>",
            
            # SQL injection patterns
            r"union\s+select",
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"update\s+set",
            r"alter\s+table",
            r"create\s+table",
            r"exec\s*\(",
            r"execute\s*\(",
            r"sp_",
            r"xp_",
            
            # Command injection patterns
            r"system\s*\(",
            r"eval\s*\(",
            r"shell_exec",
            r"passthru",
            r"proc_open",
            r"popen",
            r"`.*`",  # Backticks
            r"\$\(.*\)",  # Command substitution
            
            # Path traversal
            r"\.\./",
            r"\.\.\\",
            r"%2e%2e%2f",
            r"%2e%2e%5c",
            
            # LDAP injection
            r"\)\s*\(|\)\s*&|\)\s*\|",
            r"\*\s*\)",
            
            # NoSQL injection
            r"\$where",
            r"\$ne",
            r"\$gt",
            r"\$lt",
            r"\$regex",
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
        
        # File upload validation
        self.allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.xls'}
        self.max_file_size = 50 * 1024 * 1024  # 50MB
    
    def _validate_string(self, value: str, field_name: str = "input") -> tuple[bool, str]:
        """Validate a string value for suspicious patterns"""
        if not isinstance(value, str):
            return True, ""
        
        # Check length limits
        if len(value) > 10000:  # 10KB limit per field
            return False, f"{field_name} too long"
        
        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(value):
                return False, f"Suspicious pattern detected in {field_name}"
        
        # Check for null bytes
        if '\x00' in value:
            return False, f"Null bytes not allowed in {field_name}"
        
        return True, ""
    
    def _validate_json_data(self, data: dict, path: str = "") -> tuple[bool, str]:
        """Recursively validate JSON data"""
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Validate key
            is_valid, error = self._validate_string(str(key), f"key {current_path}")
            if not is_valid:
                return False, error
            
            # Validate value based on type
            if isinstance(value, str):
                is_valid, error = self._validate_string(value, f"field {current_path}")
                if not is_valid:
                    return False, error
            elif isinstance(value, dict):
                is_valid, error = self._validate_json_data(value, current_path)
                if not is_valid:
                    return False, error
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str):
                        is_valid, error = self._validate_string(item, f"field {current_path}[{i}]")
                        if not is_valid:
                            return False, error
                    elif isinstance(item, dict):
                        is_valid, error = self._validate_json_data(item, f"{current_path}[{i}]")
                        if not is_valid:
                            return False, error
        
        return True, ""
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain endpoints
        if request.url.path in ["/health", "/ready", "/metrics", "/health/detailed", "/health/external"]:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            # Validate query parameters
            for param_name, param_value in request.query_params.items():
                is_valid, error = self._validate_string(str(param_value), f"query parameter {param_name}")
                if not is_valid:
                    logger.warning(
                        "Invalid query parameter",
                        param=param_name,
                        error=error,
                        client_ip=client_ip,
                        path=request.url.path
                    )
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"detail": f"Invalid query parameter: {error}"}
                    )
            
            # Validate request body for JSON requests
            if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
                body = await request.body()
                if body:
                    try:
                        import json
                        data = json.loads(body.decode('utf-8'))
                        is_valid, error = self._validate_json_data(data)
                        if not is_valid:
                            logger.warning(
                                "Invalid JSON data",
                                error=error,
                                client_ip=client_ip,
                                path=request.url.path
                            )
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": f"Invalid input data: {error}"}
                            )
                    except json.JSONDecodeError:
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": "Invalid JSON format"}
                        )
            
            # Validate form data
            elif request.method in ["POST", "PUT", "PATCH"] and "multipart/form-data" in request.headers.get("content-type", ""):
                # This is handled by FastAPI's file upload handling
                # Additional validation can be added here if needed
                pass
            
            # Validate headers
            for header_name, header_value in request.headers.items():
                if header_name.lower() not in ["authorization", "content-type", "content-length", "user-agent"]:
                    is_valid, error = self._validate_string(header_value, f"header {header_name}")
                    if not is_valid:
                        logger.warning(
                            "Invalid header",
                            header=header_name,
                            error=error,
                            client_ip=client_ip,
                            path=request.url.path
                        )
                        return JSONResponse(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            content={"detail": f"Invalid header: {error}"}
                        )
        
        except Exception as e:
            logger.error("Input validation error", error=str(e), client_ip=client_ip)
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Input validation failed"}
            )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting middleware with Redis-backed sliding window and multiple rate limit tiers."""
    
    def __init__(self, app):
        super().__init__(app)
        self.requests = {}  # Fallback in-memory storage
        self.cleanup_interval = 60
        self.last_cleanup = time.time()
        self.redis = redis_manager.get_client()
        
        # Rate limit configurations
        self.rate_limits = {
            "global": {
                "requests": settings.RATE_LIMIT_REQUESTS,
                "window": 60,  # 1 minute
                "burst": settings.RATE_LIMIT_REQUESTS * 2  # Allow burst
            },
            "auth": {
                "requests": 10,  # 10 auth attempts per minute
                "window": 60,
                "burst": 20
            },
            "api": {
                "requests": 100,  # 100 API calls per minute
                "window": 60,
                "burst": 200
            },
            "embed": {
                "requests": 600,  # 600 embed requests per minute
                "window": 60,
                "burst": 1200
            }
        }
    
    def _get_rate_limit_config(self, request: Request) -> dict:
        """Determine rate limit configuration based on request path and type"""
        path = request.url.path
        
        # Authentication endpoints
        if path.startswith("/api/v1/auth/"):
            return self.rate_limits["auth"]
        
        # Embed widget endpoints
        if path.startswith("/api/v1/embed/") or path.startswith("/embed/"):
            return self.rate_limits["embed"]
        
        # API endpoints
        if path.startswith("/api/"):
            return self.rate_limits["api"]
        
        # Default to global rate limit
        return self.rate_limits["global"]
    
    def _get_identifier(self, request: Request) -> str:
        """Generate unique identifier for rate limiting"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # For authenticated requests, use user ID if available
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Extract user info from JWT (simplified)
                # In production, you'd decode the JWT properly
                user_id = "authenticated_user"  # Placeholder
                return f"user:{user_id}"
            except:
                pass
        
        # For embed requests, use API key if available
        api_key = request.headers.get("X-Client-API-Key")
        if api_key:
            return f"embed:{api_key}"
        
        # Default to IP + user agent hash
        return f"ip:{client_ip}:{hashlib.md5(user_agent.encode()).hexdigest()[:8]}"
    
    async def _check_redis_rate_limit(self, key: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Check rate limit using Redis with sliding window"""
        try:
            now = time.time()
            pipe = self.redis.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, now - window)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window)
            
            results = pipe.execute()
            current_count = results[1]
            
            # Check if limit exceeded
            if current_count >= limit:
                return False, current_count, int(now + window)
            
            return True, current_count + 1, int(now + window)
            
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}")
            raise e
    
    async def _check_memory_rate_limit(self, identifier: str, limit: int, window: int) -> tuple[bool, int, int]:
        """Fallback in-memory rate limiting"""
        current_time = time.time()
        
        # Cleanup old entries
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(int(current_time))
            self.last_cleanup = current_time
        
        # Get or create request list for this identifier
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside the window
        window_start = current_time - window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        current_count = len(self.requests[identifier])
        if current_count >= limit:
            return False, current_count, int(current_time + window)
        
        # Add current request
        self.requests[identifier].append(current_time)
        
        return True, current_count + 1, int(current_time + window)
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/ready", "/metrics", "/health/detailed", "/health/external"]:
            return await call_next(request)
        
        # Get rate limit configuration
        config = self._get_rate_limit_config(request)
        limit = config["requests"]
        window = config["window"]
        
        # Get identifier
        identifier = self._get_identifier(request)
        key = f"rate_limit:{identifier}"
        
        # Check rate limit
        allowed = False
        count = 0
        reset_time = 0
        
        try:
            # Try Redis first
            allowed, count, reset_time = await self._check_redis_rate_limit(key, limit, window)
        except Exception as e:
            logger.warning(f"Redis rate limiting failed, falling back to memory: {e}")
            try:
                # Fallback to in-memory
                allowed, count, reset_time = await self._check_memory_rate_limit(identifier, limit, window)
            except Exception as e2:
                logger.error(f"Rate limiting completely failed: {e2}")
                # Allow request if rate limiting fails
                allowed = True
                count = 0
                reset_time = int(time.time() + window)
        
        # Check if rate limit exceeded
        if not allowed:
            # Record security event
            from app.utils.metrics import metrics_collector
            metrics_collector.record_security_event("rate_limit_exceeded", request.client.host if request.client else "unknown")
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": window,
                    "limit": limit,
                    "current": count
                },
                headers={
                    "Retry-After": str(window),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "X-RateLimit-Window": str(window)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, limit - count)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        response.headers["X-RateLimit-Window"] = str(window)
        
        return response
    
    def _cleanup_old_entries(self, current_time: int):
        """Clean up old in-memory rate limit entries"""
        window_start = current_time - 60
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] 
                if req_time > window_start
            ]
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
    """Enhanced CSRF protection middleware with proper token validation"""
    
    def __init__(self, app):
        super().__init__(app)
        self.exempt_paths = [
            "/health", "/ready", "/metrics", 
            "/api/v1/auth/login", "/api/v1/auth/register",
            "/api/v1/embed/", "/ws/"
        ]
        self.safe_methods = ["GET", "HEAD", "OPTIONS"]
        self.redis = redis_manager.get_client()
        self.token_ttl = 3600  # 1 hour
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            return await call_next(request)
        
        # If Authorization Bearer token present, treat as API call and skip CSRF
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)
        
        # Check for CSRF token in header or form data
        csrf_token = self._extract_csrf_token(request)
        if not csrf_token:
            logger.warning(
                "Missing CSRF token",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "")
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "CSRF token required",
                    "error_code": "CSRF_TOKEN_MISSING"
                }
            )
        
        # Validate CSRF token
        if not await self._validate_csrf_token(csrf_token, request):
            logger.warning(
                "Invalid CSRF token",
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown",
                token_length=len(csrf_token) if csrf_token else 0
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Invalid CSRF token",
                    "error_code": "CSRF_TOKEN_INVALID"
                }
            )
        
        return await call_next(request)
    
    def _extract_csrf_token(self, request: Request) -> Optional[str]:
        """Extract CSRF token from headers or form data"""
        # Try header first
        token = request.headers.get("X-CSRF-Token") or request.headers.get("X-Csrf-Token")
        if token:
            return token
        
        # Try form data (for form submissions)
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type:
            try:
                # This is a simplified approach - in production, you'd need to handle
                # form data parsing more carefully
                pass
            except Exception:
                pass
        
        return None
    
    async def _validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token with proper session-based validation"""
        if not token or len(token) < 32:
            return False
        
        try:
            # Check if token exists in Redis with proper format
            token_key = f"csrf_token:{token}"
            token_data = self.redis.get(token_key)
            
            if not token_data:
                return False
            
            # Parse token data (in production, this would be more sophisticated)
            import json
            try:
                data = json.loads(token_data)
            except json.JSONDecodeError:
                return False
            
            # Validate token hasn't expired
            if data.get("expires_at", 0) < time.time():
                self.redis.delete(token_key)
                return False
            
            # Validate token is associated with correct session/IP
            client_ip = request.client.host if request.client else "unknown"
            if data.get("client_ip") != client_ip:
                logger.warning(
                    "CSRF token IP mismatch",
                    token_ip=data.get("client_ip"),
                    request_ip=client_ip
                )
                return False
            
            # Token is valid - optionally refresh expiry
            self.redis.expire(token_key, self.token_ttl)
            return True
            
        except Exception as e:
            logger.error("CSRF token validation error", error=str(e))
            return False
    
    def generate_csrf_token(self, client_ip: str) -> str:
        """Generate a new CSRF token"""
        token = secrets.token_urlsafe(32)
        token_data = {
            "created_at": time.time(),
            "expires_at": time.time() + self.token_ttl,
            "client_ip": client_ip,
            "token": token
        }
        
        try:
            import json
            self.redis.setex(
                f"csrf_token:{token}",
                self.token_ttl,
                json.dumps(token_data)
            )
        except Exception as e:
            logger.error("Failed to store CSRF token", error=str(e))
        
        return token


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