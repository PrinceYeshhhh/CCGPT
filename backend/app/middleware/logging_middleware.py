"""
Enhanced logging middleware for request context and performance tracking
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from app.utils.logging_config import api_logger, security_logger

logger = structlog.get_logger()


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context to all log entries"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        
        # Add request context to structlog
        with structlog.contextvars.bound_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            content_length=request.headers.get("content-length", "0")
        ):
            start_time = time.time()
            
            # Log request start
            logger.info(
                "Request started",
                event_type="request_start"
            )
            
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log request completion
                api_logger.log_request(
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                    ip_address=request.client.host if request.client else "unknown"
                )
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as e:
                # Calculate duration for failed requests
                duration_ms = (time.time() - start_time) * 1000
                
                # Log request error
                api_logger.log_error(
                    method=request.method,
                    path=request.url.path,
                    status_code=500,
                    error=str(e),
                    ip_address=request.client.host if request.client else "unknown"
                )
                
                # Re-raise the exception
                raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log performance metrics for slow requests"""
    
    def __init__(self, app, slow_request_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_request_threshold_ms = slow_request_threshold_ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log slow requests
        if duration_ms > self.slow_request_threshold_ms:
            logger.warning(
                "Slow request detected",
                method=request.method,
                path=request.url.path,
                duration_ms=duration_ms,
                threshold_ms=self.slow_request_threshold_ms,
                event_type="slow_request"
            )
        
        # Log performance metrics
        from app.utils.logging_config import log_performance
        log_performance(
            operation=f"{request.method} {request.url.path}",
            duration_ms=duration_ms,
            status_code=response.status_code
        )
        
        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log security-related events"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for suspicious patterns in request
        suspicious_indicators = []
        
        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "").lower()
        if any(pattern in user_agent for pattern in ["bot", "crawler", "scanner", "test"]):
            suspicious_indicators.append("suspicious_user_agent")
        
        # Check for suspicious paths
        path = request.url.path.lower()
        if any(pattern in path for pattern in ["admin", "wp-admin", "phpmyadmin", "config"]):
            suspicious_indicators.append("suspicious_path")
        
        # Check for suspicious query parameters
        for param_name, param_value in request.query_params.items():
            if any(pattern in param_value.lower() for pattern in ["<script", "javascript:", "union select"]):
                suspicious_indicators.append("suspicious_query_param")
        
        # Log suspicious activity
        if suspicious_indicators:
            security_logger.log_suspicious_activity(
                activity_type="request_analysis",
                ip_address=request.client.host if request.client else "unknown",
                details=f"Indicators: {', '.join(suspicious_indicators)}",
                indicators=suspicious_indicators,
                path=request.url.path,
                method=request.method
            )
        
        # Process request
        response = await call_next(request)
        
        # Log security events based on response
        if response.status_code == 401:
            security_logger.log_security_violation(
                violation_type="unauthorized_access",
                ip_address=request.client.host if request.client else "unknown",
                path=request.url.path,
                method=request.method
            )
        elif response.status_code == 403:
            security_logger.log_security_violation(
                violation_type="forbidden_access",
                ip_address=request.client.host if request.client else "unknown",
                path=request.url.path,
                method=request.method
            )
        elif response.status_code == 429:
            security_logger.log_rate_limit_exceeded(
                ip_address=request.client.host if request.client else "unknown",
                endpoint=request.url.path,
                limit=0,  # Will be filled by rate limiting middleware
                method=request.method
            )
        
        return response
