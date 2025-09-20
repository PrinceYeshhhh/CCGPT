"""
User Pydantic schemas
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_domain: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update schema"""
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_domain: Optional[str] = None
    subscription_plan: Optional[str] = None


class UserRead(UserBase):
    """User read schema (public user info)"""
    id: int
    is_active: bool
    is_superuser: bool
    subscription_plan: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserResponse(UserRead):
    """User response schema (alias for UserRead)"""
    pass


class UserInDB(UserRead):
    """User in database schema (includes hashed password)"""
    hashed_password: str
