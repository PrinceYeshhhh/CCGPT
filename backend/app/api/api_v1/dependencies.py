"""
Common dependencies for API endpoints
"""

from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth import AuthService
from app.models.user import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    return AuthService(db).get_current_user
