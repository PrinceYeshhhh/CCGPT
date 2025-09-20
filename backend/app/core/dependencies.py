"""
FastAPI dependencies
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.services.auth import AuthService


def get_current_user(
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user dependency"""
    auth_service = AuthService(db)
    return auth_service.get_current_user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user dependency"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser dependency"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
