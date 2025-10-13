"""
Global error handling middleware for CustomerCareGPT
"""

import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.utils.error_handling import error_handler, CustomError, ErrorType, ErrorSeverity
from app.utils.logging_config import security_logger

logger = structlog.get_logger()


class GlobalErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware that catches all unhandled exceptions"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        
        except CustomError as e:
            # Handle custom errors
            return error_handler.handle_error(
                error=e,
                request=request,
                user_id=getattr(request.state, 'user_id', None)
            )
        
        except RequestValidationError as e:
            # Handle FastAPI validation errors
            return error_handler.handle_error(
                error=e,
                request=request,
                user_id=getattr(request.state, 'user_id', None)
            )
        
        except StarletteHTTPException as e:
            # Handle HTTP exceptions
            return error_handler.handle_error(
                error=e,
                request=request,
                user_id=getattr(request.state, 'user_id', None)
            )
        
        except Exception as e:
            # Handle all other exceptions
            logger.error(
                "Unhandled exception",
                error=str(e),
                error_type=type(e).__name__,
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else None,
                traceback=traceback.format_exc()
            )
            
            # Log security event for suspicious errors
            if self._is_suspicious_error(e):
                security_logger.log_suspicious_activity(
                    activity_type="unhandled_exception",
                    ip_address=request.client.host if request.client else "unknown",
                    details=f"Unhandled exception: {type(e).__name__}: {str(e)}",
                    path=request.url.path,
                    method=request.method
                )
            
            return error_handler.handle_error(
                error=e,
                request=request,
                user_id=getattr(request.state, 'user_id', None)
            )
    
    def _is_suspicious_error(self, error: Exception) -> bool:
        """Check if error might indicate suspicious activity"""
        error_str = str(error).lower()
        suspicious_patterns = [
            "sql injection",
            "xss",
            "script",
            "javascript",
            "eval",
            "exec",
            "import",
            "os.system",
            "subprocess",
            "command injection",
            "path traversal",
            "directory traversal",
            "file inclusion",
            "code injection"
        ]
        
        return any(pattern in error_str for pattern in suspicious_patterns)


class ErrorRecoveryMiddleware(BaseHTTPMiddleware):
    """Middleware for error recovery and circuit breaker patterns"""
    
    def __init__(self, app, max_failures: int = 5, recovery_timeout: int = 60):
        super().__init__(app)
        self.max_failures = max_failures
        self.recovery_timeout = recovery_timeout
        self.failure_counts = {}
        self.circuit_breakers = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check circuit breaker for this endpoint
        endpoint = f"{request.method}:{request.url.path}"
        
        if self._is_circuit_open(endpoint):
            logger.warning(
                "Circuit breaker open for endpoint",
                endpoint=endpoint,
                failures=self.failure_counts.get(endpoint, 0)
            )
            
            return error_handler.handle_error(
                error=CustomError(
                    message="Service temporarily unavailable",
                    error_type=ErrorType.SYSTEM_ERROR,
                    severity=ErrorSeverity.HIGH,
                    retry_after=self.recovery_timeout
                ),
                request=request
            )
        
        try:
            response = await call_next(request)
            
            # Reset failure count on success
            if endpoint in self.failure_counts:
                del self.failure_counts[endpoint]
            
            return response
        
        except Exception as e:
            # Increment failure count
            self.failure_counts[endpoint] = self.failure_counts.get(endpoint, 0) + 1
            
            # Check if circuit should be opened
            if self.failure_counts[endpoint] >= self.max_failures:
                self._open_circuit(endpoint)
                logger.error(
                    "Circuit breaker opened for endpoint",
                    endpoint=endpoint,
                    failures=self.failure_counts[endpoint]
                )
            
            # Re-raise the exception to be handled by other middleware
            raise
    
    def _is_circuit_open(self, endpoint: str) -> bool:
        """Check if circuit breaker is open for endpoint"""
        if endpoint not in self.circuit_breakers:
            return False
        
        import time
        return time.time() - self.circuit_breakers[endpoint] < self.recovery_timeout
    
    def _open_circuit(self, endpoint: str):
        """Open circuit breaker for endpoint"""
        import time
        self.circuit_breakers[endpoint] = time.time()


class ErrorMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect error metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record success metrics
            duration = (time.time() - start_time) * 1000
            from app.utils.metrics import metrics_collector
            metrics_collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=duration
            )
            
            return response
        
        except Exception as e:
            # Record error metrics
            duration = (time.time() - start_time) * 1000
            from app.utils.metrics import metrics_collector
            # metrics API expects (error_type, endpoint)
            metrics_collector.record_error(
                error_type=type(e).__name__,
                endpoint=request.url.path
            )
            
            # Re-raise to be handled by error handler
            raise


# Import time for metrics middleware
import time
