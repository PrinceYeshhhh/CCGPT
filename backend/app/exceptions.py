"""
Custom exceptions for CustomerCareGPT
"""

from typing import Optional, Dict, Any


class CustomerCareGPTException(Exception):
    """Base exception for CustomerCareGPT"""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(CustomerCareGPTException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTH_ERROR", details)


class AuthorizationError(CustomerCareGPTException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AUTHZ_ERROR", details)


class RateLimitError(CustomerCareGPTException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class TokenBudgetError(CustomerCareGPTException):
    """Token budget errors"""
    
    def __init__(self, message: str = "Token budget exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "TOKEN_BUDGET_ERROR", details)


class EmbeddingError(CustomerCareGPTException):
    """Embedding generation errors"""
    
    def __init__(self, message: str = "Embedding generation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMBEDDING_ERROR", details)


class VectorSearchError(CustomerCareGPTException):
    """Vector search errors"""
    
    def __init__(self, message: str = "Vector search failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VECTOR_SEARCH_ERROR", details)


class RAGError(CustomerCareGPTException):
    """RAG processing errors"""
    
    def __init__(self, message: str = "RAG processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RAG_ERROR", details)


class ChatError(CustomerCareGPTException):
    """Chat processing errors"""
    
    def __init__(self, message: str = "Chat processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CHAT_ERROR", details)


class EmbedCodeError(CustomerCareGPTException):
    """Embed code related errors"""
    
    def __init__(self, message: str = "Embed code error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMBED_CODE_ERROR", details)


class DocumentProcessingError(CustomerCareGPTException):
    """Document processing errors"""
    
    def __init__(self, message: str = "Document processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR", details)


class WebSocketError(CustomerCareGPTException):
    """WebSocket related errors"""
    
    def __init__(self, message: str = "WebSocket error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "WEBSOCKET_ERROR", details)


class ConfigurationError(CustomerCareGPTException):
    """Configuration related errors"""
    
    def __init__(self, message: str = "Configuration error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIG_ERROR", details)


class AnalyticsError(CustomerCareGPTException):
    """Analytics related errors"""
    
    def __init__(self, message: str = "Analytics error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ANALYTICS_ERROR", details)


class ValidationError(CustomerCareGPTException):
    """Data validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class ExternalServiceError(CustomerCareGPTException):
    """External service errors (Gemini, Redis, etc.)"""
    
    def __init__(self, service: str, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        self.service = service
        super().__init__(f"{service}: {message}", "EXTERNAL_SERVICE_ERROR", details)


class DatabaseError(CustomerCareGPTException):
    """Database related errors"""
    
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class CacheError(CustomerCareGPTException):
    """Cache related errors"""
    
    def __init__(self, message: str = "Cache error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CACHE_ERROR", details)


class ABTestingError(CustomerCareGPTException):
    """A/B Testing related errors"""
    
    def __init__(self, message: str = "A/B Testing error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "AB_TESTING_ERROR", details)


class LanguageError(CustomerCareGPTException):
    """Language detection and processing related errors"""
    
    def __init__(self, message: str = "Language processing error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "LANGUAGE_ERROR", details)