"""
Centralized logging configuration with structlog
"""

import structlog
import logging
import sys
import os
from typing import Any, Dict, Optional
from datetime import datetime
import json

from app.core.config import settings

def configure_logging():
    """Configure structured logging for the application"""
    
    # Configure structlog
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
            add_request_context,
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

def add_request_context(logger, method_name, event_dict):
    """Add request context to log entries"""
    # This will be populated by middleware
    request_context = getattr(structlog.contextvars, "request_context", {})
    event_dict.update(request_context)
    return event_dict

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance"""
    return structlog.get_logger(name)

class RequestLogger:
    """Logger with request context"""
    
    def __init__(self, name: Optional[str] = None):
        # Optional name for tests; default to 'app'
        self.logger = get_logger(name or "app")
        self.context = {}
    
    def bind(self, **kwargs) -> "RequestLogger":
        """Bind context to logger"""
        new_logger = RequestLogger(self.logger.name)
        new_logger.context = {**self.context, **kwargs}
        return new_logger
    
    def info(self, message: str, **kwargs):
        """Log info message with context"""
        self.logger.info(message, **{**self.context, **kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context"""
        self.logger.warning(message, **{**self.context, **kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error message with context"""
        self.logger.error(message, **{**self.context, **kwargs})
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, **{**self.context, **kwargs})

def log_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
):
    """Log HTTP request with standard fields"""
    logger = get_logger("http")
    logger.info(
        "HTTP request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        workspace_id=workspace_id,
        user_id=user_id,
        request_id=request_id
    )

def log_error(
    error: Exception,
    message: str,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **context
):
    """Log error with context"""
    logger = get_logger("error")
    logger.error(
        message,
        error_type=type(error).__name__,
        error_message=str(error),
        workspace_id=workspace_id,
        user_id=user_id,
        request_id=request_id,
        **context,
        exc_info=True
    )

def log_business_event(
    event: str,
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **data
):
    """Log business events for analytics"""
    logger = get_logger("business")
    logger.info(
        f"Business event: {event}",
        event=event,
        workspace_id=workspace_id,
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        **data
    )

def log_performance(
    operation: str,
    duration_ms: float,
    workspace_id: Optional[str] = None,
    **metrics
):
    """Log performance metrics"""
    logger = get_logger("performance")
    logger.info(
        f"Performance: {operation}",
        operation=operation,
        duration_ms=duration_ms,
        workspace_id=workspace_id,
        timestamp=datetime.utcnow().isoformat(),
        **metrics
    )

def log_security_event(
    event: str,
    severity: str = "medium",
    workspace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    **context
):
    """Log security events"""
    logger = get_logger("security")
    logger.warning(
        f"Security event: {event}",
        event=event,
        severity=severity,
        workspace_id=workspace_id,
        user_id=user_id,
        ip_address=ip_address,
        timestamp=datetime.utcnow().isoformat(),
        **context
    )

# Initialize logging on import
configure_logging()
