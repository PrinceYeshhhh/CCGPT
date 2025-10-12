"""
Common response schemas for consistent API responses
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """Base response wrapper for all API endpoints"""
    success: bool = True
    message: str = ""
    data: Optional[T] = None
    errors: Optional[List[str]] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int

class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: str(datetime.utcnow()))

from datetime import datetime
