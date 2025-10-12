"""
Comprehensive error handling utilities for CustomerCareGPT
"""

import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union, Type
from enum import Enum
import structlog
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from redis.exceptions import RedisError
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.utils.logging_config import security_logger, api_logger, database_logger

logger = structlog.get_logger()


class ErrorType(Enum):
    """Error type classification for better handling"""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    AUTHORIZATION_ERROR = "authorization_error"
    NOT_FOUND_ERROR = "not_found_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_API_ERROR = "external_api_error"
    FILE_PROCESSING_ERROR = "file_processing_error"
    VECTOR_SEARCH_ERROR = "vector_search_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    SYSTEM_ERROR = "system_error"
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CustomError(Exception):
    """Base custom error class"""
    
    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        retry_after: Optional[int] = None
    ):
        self.message = message
        self.error_type = error_type
        self.severity = severity
        self.details = details or {}
        self.user_message = user_message or message
        self.retry_after = retry_after
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow()
        super().__init__(message)


class ValidationError(CustomError):
    """Validation error with specific handling"""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_type=ErrorType.VALIDATION_ERROR,
            severity=ErrorSeverity.LOW,
            details={"field": field} if field else {},
            **kwargs
        )


class AuthenticationError(CustomError):
    """Authentication error"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHENTICATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class AuthorizationError(CustomError):
    """Authorization error"""
    
    def __init__(self, message: str = "Access denied", **kwargs):
        super().__init__(
            message=message,
            error_type=ErrorType.AUTHORIZATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )


class NotFoundError(CustomError):
    """Resource not found error"""
    
    def __init__(self, resource: str, identifier: str, **kwargs):
        super().__init__(
            message=f"{resource} not found",
            error_type=ErrorType.NOT_FOUND_ERROR,
            severity=ErrorSeverity.LOW,
            details={"resource": resource, "identifier": identifier},
            **kwargs
        )


class DatabaseError(CustomError):
    """Database operation error"""
    
    def __init__(self, message: str, operation: str, **kwargs):
        super().__init__(
            message=message,
            error_type=ErrorType.DATABASE_ERROR,
            severity=ErrorSeverity.HIGH,
            details={"operation": operation},
            **kwargs
        )


class ExternalAPIError(CustomError):
    """External API error"""
    
    def __init__(self, service: str, message: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(
            message=message,
            error_type=ErrorType.EXTERNAL_API_ERROR,
            severity=ErrorSeverity.MEDIUM,
            details={"service": service, "status_code": status_code},
            **kwargs
        )


class RateLimitError(CustomError):
    """Rate limit exceeded error"""
    
    def __init__(self, limit: int, retry_after: int, **kwargs):
        super().__init__(
            message="Rate limit exceeded",
            error_type=ErrorType.RATE_LIMIT_ERROR,
            severity=ErrorSeverity.LOW,
            retry_after=retry_after,
            details={"limit": limit},
            **kwargs
        )


class ErrorHandler:
    """Centralized error handling and response generation"""
    
    def __init__(self):
        self.error_mappings = {
            # FastAPI/Starlette errors
            RequestValidationError: self._handle_validation_error,
            StarletteHTTPException: self._handle_http_exception,
            
            # SQLAlchemy errors
            IntegrityError: self._handle_integrity_error,
            OperationalError: self._handle_operational_error,
            SQLAlchemyError: self._handle_database_error,
            
            # Redis errors
            RedisError: self._handle_redis_error,
            
            # HTTP client errors
            httpx.HTTPError: self._handle_http_error,
            httpx.TimeoutException: self._handle_timeout_error,
            
            # Pydantic errors
            ValidationError: self._handle_pydantic_validation_error,
            
            # Custom errors
            CustomError: self._handle_custom_error,
        }
    
    def handle_error(
        self,
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """Handle any error and return appropriate JSON response"""
        
        # Get error handler
        error_handler = self._get_error_handler(type(error))
        
        # Create error context
        error_context = self._create_error_context(error, request, user_id, context)
        
        # Log the error
        self._log_error(error, error_context)
        
        # Generate response
        return error_handler(error, error_context)
    
    def _get_error_handler(self, error_type: Type[Exception]):
        """Get appropriate error handler for error type"""
        for error_class, handler in self.error_mappings.items():
            if issubclass(error_type, error_class):
                return handler
        
        return self._handle_unknown_error
    
    def _create_error_context(
        self,
        error: Exception,
        request: Optional[Request] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create comprehensive error context"""
        error_context = {
            "error_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "user_id": user_id,
            "context": context or {}
        }
        
        if request:
            error_context.update({
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "referer": request.headers.get("referer"),
            })
        
        return error_context
    
    def _log_error(self, error: Exception, context: Dict[str, Any]):
        """Log error with appropriate level and context"""
        log_level = self._get_log_level(error)
        
        if log_level == "error":
            logger.error(
                "Error occurred",
                error_id=context["error_id"],
                error_type=context["error_type"],
                error_message=context["error_message"],
                user_id=context.get("user_id"),
                path=context.get("path"),
                method=context.get("method"),
                client_ip=context.get("client_ip"),
                **context.get("context", {})
            )
        elif log_level == "warning":
            logger.warning(
                "Warning occurred",
                error_id=context["error_id"],
                error_type=context["error_type"],
                error_message=context["error_message"],
                user_id=context.get("user_id"),
                path=context.get("path"),
                method=context.get("method"),
                **context.get("context", {})
            )
        else:
            logger.info(
                "Info event",
                error_id=context["error_id"],
                error_type=context["error_type"],
                error_message=context["error_message"],
                **context.get("context", {})
            )
    
    def _get_log_level(self, error: Exception) -> str:
        """Determine appropriate log level for error"""
        if isinstance(error, (CustomError,)):
            if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
                return "error"
            elif error.severity == ErrorSeverity.MEDIUM:
                return "warning"
            else:
                return "info"
        elif isinstance(error, (SQLAlchemyError, RedisError, httpx.HTTPError)):
            return "error"
        elif isinstance(error, (RequestValidationError,)):
            return "info"
        else:
            return "error"
    
    def _handle_validation_error(self, error: RequestValidationError, context: Dict[str, Any]) -> JSONResponse:
        """Handle FastAPI validation errors"""
        details = []
        for err in error.errors():
            details.append({
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid input data",
                "details": details,
                "error_id": context["error_id"]
            }
        )
    
    def _handle_http_exception(self, error: StarletteHTTPException, context: Dict[str, Any]) -> JSONResponse:
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": "HTTP Error",
                "message": error.detail,
                "error_id": context["error_id"]
            }
        )
    
    def _handle_integrity_error(self, error: IntegrityError, context: Dict[str, Any]) -> JSONResponse:
        """Handle database integrity errors"""
        database_logger.log_query(
            operation="integrity_error",
            table="unknown",
            duration_ms=0,
            success=False,
            error=str(error)
        )
        
        # Check for common integrity violations
        error_msg = str(error.orig) if hasattr(error, 'orig') else str(error)
        
        if "duplicate key" in error_msg.lower():
            message = "A record with this information already exists"
        elif "foreign key" in error_msg.lower():
            message = "Referenced record does not exist"
        elif "not null" in error_msg.lower():
            message = "Required field is missing"
        else:
            message = "Data integrity violation"
        
        return JSONResponse(
            status_code=400,
            content={
                "error": "Data Integrity Error",
                "message": message,
                "error_id": context["error_id"]
            }
        )
    
    def _handle_operational_error(self, error: OperationalError, context: Dict[str, Any]) -> JSONResponse:
        """Handle database operational errors"""
        database_logger.log_query(
            operation="operational_error",
            table="unknown",
            duration_ms=0,
            success=False,
            error=str(error)
        )
        
        return JSONResponse(
            status_code=503,
            content={
                "error": "Database Error",
                "message": "Database temporarily unavailable",
                "error_id": context["error_id"]
            }
        )
    
    def _handle_database_error(self, error: SQLAlchemyError, context: Dict[str, Any]) -> JSONResponse:
        """Handle general database errors"""
        database_logger.log_query(
            operation="database_error",
            table="unknown",
            duration_ms=0,
            success=False,
            error=str(error)
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Database Error",
                "message": "Database operation failed",
                "error_id": context["error_id"]
            }
        )
    
    def _handle_redis_error(self, error: RedisError, context: Dict[str, Any]) -> JSONResponse:
        """Handle Redis errors"""
        return JSONResponse(
            status_code=503,
            content={
                "error": "Cache Error",
                "message": "Cache service temporarily unavailable",
                "error_id": context["error_id"]
            }
        )
    
    def _handle_http_error(self, error: httpx.HTTPError, context: Dict[str, Any]) -> JSONResponse:
        """Handle HTTP client errors"""
        return JSONResponse(
            status_code=502,
            content={
                "error": "External Service Error",
                "message": "External service temporarily unavailable",
                "error_id": context["error_id"]
            }
        )
    
    def _handle_timeout_error(self, error: httpx.TimeoutException, context: Dict[str, Any]) -> JSONResponse:
        """Handle timeout errors"""
        return JSONResponse(
            status_code=504,
            content={
                "error": "Timeout Error",
                "message": "Request timed out",
                "error_id": context["error_id"]
            }
        )
    
    def _handle_pydantic_validation_error(self, error: ValidationError, context: Dict[str, Any]) -> JSONResponse:
        """Handle Pydantic validation errors"""
        details = []
        for err in error.errors():
            details.append({
                "field": ".".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
                "type": err["type"]
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "message": "Invalid data format",
                "details": details,
                "error_id": context["error_id"]
            }
        )
    
    def _handle_custom_error(self, error: CustomError, context: Dict[str, Any]) -> JSONResponse:
        """Handle custom errors"""
        status_code = self._get_status_code_for_error_type(error.error_type)
        
        response_content = {
            "error": error.error_type.value.replace("_", " ").title(),
            "message": error.user_message,
            "error_id": error.error_id
        }
        
        if error.details:
            response_content["details"] = error.details
        
        if error.retry_after:
            response_content["retry_after"] = error.retry_after
        
        return JSONResponse(
            status_code=status_code,
            content=response_content
        )
    
    def _handle_unknown_error(self, error: Exception, context: Dict[str, Any]) -> JSONResponse:
        """Handle unknown errors"""
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "error_id": context["error_id"]
            }
        )
    
    def _get_status_code_for_error_type(self, error_type: ErrorType) -> int:
        """Get appropriate HTTP status code for error type"""
        status_mapping = {
            ErrorType.VALIDATION_ERROR: 422,
            ErrorType.AUTHENTICATION_ERROR: 401,
            ErrorType.AUTHORIZATION_ERROR: 403,
            ErrorType.NOT_FOUND_ERROR: 404,
            ErrorType.RATE_LIMIT_ERROR: 429,
            ErrorType.DATABASE_ERROR: 500,
            ErrorType.EXTERNAL_API_ERROR: 502,
            ErrorType.FILE_PROCESSING_ERROR: 400,
            ErrorType.VECTOR_SEARCH_ERROR: 500,
            ErrorType.BUSINESS_LOGIC_ERROR: 400,
            ErrorType.SYSTEM_ERROR: 500,
            ErrorType.NETWORK_ERROR: 503,
            ErrorType.TIMEOUT_ERROR: 504,
            ErrorType.UNKNOWN_ERROR: 500,
        }
        return status_mapping.get(error_type, 500)


# Global error handler instance
error_handler = ErrorHandler()


def handle_exception(
    error: Exception,
    request: Optional[Request] = None,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Convenience function to handle any exception"""
    return error_handler.handle_error(error, request, user_id, context)


def create_error_response(
    message: str,
    error_type: ErrorType = ErrorType.UNKNOWN_ERROR,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type.value.replace("_", " ").title(),
            "message": message,
            "details": details or {},
            "error_id": str(uuid.uuid4())
        }
    )
