"""
Input validation utilities for dashboard endpoints
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from pydantic import BaseModel, validator
import structlog

logger = structlog.get_logger()


class DashboardQueryValidator(BaseModel):
    """Validator for dashboard query parameters"""
    
    days: int = 30
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    limit: int = 100
    offset: int = 0
    
    @validator('days')
    def validate_days(cls, v):
        if not 1 <= v <= 365:
            raise ValueError('Days must be between 1 and 365')
        return v
    
    @validator('limit')
    def validate_limit(cls, v):
        if not 1 <= v <= 1000:
            raise ValueError('Limit must be between 1 and 1000')
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v < 0:
            raise ValueError('Offset must be non-negative')
        return v
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v < values['start_date']:
                raise ValueError('End date must be after start date')
        return v


class AnalyticsFilterValidator(BaseModel):
    """Validator for analytics filter parameters"""
    
    date_range: str = '7d'
    query_type: str = 'all'
    user_type: str = 'all'
    satisfaction: str = 'all'
    
    @validator('date_range')
    def validate_date_range(cls, v):
        allowed_ranges = ['7d', '30d', '90d', '1y']
        if v not in allowed_ranges:
            raise ValueError(f'Date range must be one of: {", ".join(allowed_ranges)}')
        return v
    
    @validator('query_type')
    def validate_query_type(cls, v):
        allowed_types = ['all', 'general', 'support', 'sales']
        if v not in allowed_types:
            raise ValueError(f'Query type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('user_type')
    def validate_user_type(cls, v):
        allowed_types = ['all', 'new', 'returning']
        if v not in allowed_types:
            raise ValueError(f'User type must be one of: {", ".join(allowed_types)}')
        return v
    
    @validator('satisfaction')
    def validate_satisfaction(cls, v):
        allowed_values = ['all', 'satisfied', 'neutral', 'unsatisfied']
        if v not in allowed_values:
            raise ValueError(f'Satisfaction must be one of: {", ".join(allowed_values)}')
        return v


class PerformanceMetricsValidator(BaseModel):
    """Validator for performance metrics data"""
    
    lcp: Optional[float] = None
    fid: Optional[float] = None
    cls: Optional[float] = None
    fcp: Optional[float] = None
    ttfb: Optional[float] = None
    page_load_time: Optional[float] = None
    api_response_time: Optional[float] = None
    memory_usage: Optional[float] = None
    
    @validator('lcp', 'fid', 'cls', 'fcp', 'ttfb', 'page_load_time', 'api_response_time', 'memory_usage')
    def validate_positive_numbers(cls, v):
        if v is not None and v < 0:
            raise ValueError('Performance metrics must be non-negative')
        return v


def validate_workspace_access(workspace_id: str, user_workspace_id: str) -> bool:
    """Validate that user has access to the workspace"""
    if workspace_id != user_workspace_id:
        logger.warning(
            "User attempted to access different workspace",
            requested_workspace=workspace_id,
            user_workspace=user_workspace_id
        )
        return False
    return True


def sanitize_string_input(input_str: str, max_length: int = 255) -> str:
    """Sanitize string input for security"""
    if not input_str:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', str(input_str))
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning("Input string truncated", original_length=len(input_str), max_length=max_length)
    
    return sanitized


def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> bool:
    """Validate date range parameters"""
    if start_date and end_date:
        if start_date > end_date:
            return False
        # Check if range is not too large (max 1 year)
        if (end_date - start_date).days > 365:
            return False
    return True


def validate_pagination_params(limit: int, offset: int) -> bool:
    """Validate pagination parameters"""
    return 1 <= limit <= 1000 and offset >= 0


def validate_export_format(format_str: str) -> bool:
    """Validate export format parameter"""
    allowed_formats = ['json', 'csv', 'xlsx']
    return format_str.lower() in allowed_formats
