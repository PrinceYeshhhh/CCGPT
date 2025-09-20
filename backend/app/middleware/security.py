"""
Security middleware for production hardening
Implements security headers, input validation, and security policies
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import re
import structlog
from typing import List, Optional
import time
from urllib.parse import urlparse

logger = structlog.get_logger()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.gemini.google.com https://api.stripe.com; "
                "frame-src 'none'; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        }
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input data"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.max_request_size = 10 * 1024 * 1024  # 10MB
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'vbscript:',  # VBScript URLs
            r'on\w+\s*=',  # Event handlers
            r'<iframe[^>]*>',  # Iframe tags
            r'<object[^>]*>',  # Object tags
            r'<embed[^>]*>',  # Embed tags
            r'<link[^>]*>',  # Link tags
            r'<meta[^>]*>',  # Meta tags
            r'<style[^>]*>',  # Style tags
            r'expression\s*\(',  # CSS expressions
            r'url\s*\(',  # CSS URLs
            r'@import',  # CSS imports
            r'<[^>]*>',  # HTML tags (general)
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.suspicious_patterns]
    
    async def dispatch(self, request: Request, call_next):
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(f"Request too large: {content_length} bytes", client_ip=request.client.host)
            raise HTTPException(status_code=413, detail="Request too large")
        
        # Validate request body for suspicious content
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    body_str = body.decode('utf-8', errors='ignore')
                    
                    # Check for suspicious patterns
                    for pattern in self.compiled_patterns:
                        if pattern.search(body_str):
                            logger.warning(
                                "Suspicious input detected",
                                pattern=pattern.pattern,
                                client_ip=request.client.host,
                                path=request.url.path
                            )
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid input detected"
                            )
                
                # Recreate request with validated body
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
                
            except UnicodeDecodeError:
                logger.warning("Invalid encoding in request body", client_ip=request.client.host)
                raise HTTPException(status_code=400, detail="Invalid encoding")
        
        response = await call_next(request)
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enhanced rate limiting with IP-based tracking"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "/api/v1/auth/login": {"requests": 5, "window": 60},  # 5 login attempts per minute
            "/api/v1/auth/register": {"requests": 3, "window": 60},  # 3 registrations per minute
            "/api/v1/rag/query": {"requests": 60, "window": 60},  # 60 queries per minute
            "/api/v1/documents/upload": {"requests": 10, "window": 60},  # 10 uploads per minute
        }
        self.client_requests = {}  # In production, use Redis
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def is_rate_limited(self, client_ip: str, path: str) -> bool:
        """Check if client is rate limited"""
        current_time = time.time()
        
        # Get rate limit for path or use default
        rate_limit = self.rate_limits.get(path, self.rate_limits["default"])
        max_requests = rate_limit["requests"]
        window = rate_limit["window"]
        
        # Clean old entries
        if client_ip in self.client_requests:
            self.client_requests[client_ip] = [
                req_time for req_time in self.client_requests[client_ip]
                if current_time - req_time < window
            ]
        else:
            self.client_requests[client_ip] = []
        
        # Check if limit exceeded
        if len(self.client_requests[client_ip]) >= max_requests:
            return True
        
        # Add current request
        self.client_requests[client_ip].append(current_time)
        return False
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        path = str(request.url.path)
        
        # Skip rate limiting for health checks
        if path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        if self.is_rate_limited(client_ip, path):
            logger.warning(
                "Rate limit exceeded",
                client_ip=client_ip,
                path=path
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        response = await call_next(request)
        return response

class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security controls"""
    
    def __init__(self, app: ASGIApp, allowed_origins: List[str] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []
        self.allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allowed_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-API-Key"
        ]
        self.max_age = 86400  # 24 hours
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if not origin:
            return False
        
        # Allow localhost for development
        if origin.startswith("http://localhost") or origin.startswith("https://localhost"):
            return True
        
        # Check against allowed origins
        for allowed_origin in self.allowed_origins:
            if allowed_origin == "*":
                return True
            if origin == allowed_origin:
                return True
            if allowed_origin.startswith("*."):
                domain = allowed_origin[2:]
                if origin.endswith(domain):
                    return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            if origin and not self.is_origin_allowed(origin):
                return JSONResponse(
                    status_code=403,
                    content={"error": "CORS policy violation"}
                )
            
            response = JSONResponse(content={})
        else:
            response = await call_next(request)
        
        # Add CORS headers
        if origin and self.is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        elif not origin:
            # Same-origin request
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        response.headers["Access-Control-Max-Age"] = str(self.max_age)
        response.headers["Vary"] = "Origin"
        
        return response

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for security monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.sensitive_paths = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/billing/",
            "/api/v1/rag/query"
        ]
    
    def get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        
        # Log request
        logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown")
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time,
                client_ip=client_ip
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=process_time,
                client_ip=client_ip
            )
            
            raise

class SecurityExceptionHandler:
    """Handle security-related exceptions"""
    
    @staticmethod
    def handle_security_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle security exceptions with appropriate responses"""
        
        if isinstance(exc, HTTPException):
            if exc.status_code == 413:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large", "message": "Request size exceeds limit"}
                )
            elif exc.status_code == 400:
                return JSONResponse(
                    status_code=400,
                    content={"error": "Bad request", "message": "Invalid input detected"}
                )
            elif exc.status_code == 429:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "message": "Too many requests"}
                )
        
        # Generic security error
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "message": "An error occurred"}
        )
