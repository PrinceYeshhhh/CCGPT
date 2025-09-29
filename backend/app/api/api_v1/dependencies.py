"""
Common dependencies for API v1 endpoints (thin wrappers around core deps)
"""

from app.core.dependencies import get_current_user  # re-export correct dependency

__all__ = [
    "get_current_user",
]
