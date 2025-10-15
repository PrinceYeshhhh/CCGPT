"""
Compatibility alias for AuthService import path expected by some tests.
"""
from .auth import AuthService  # re-export for test compatibility

__all__ = ["AuthService"]

