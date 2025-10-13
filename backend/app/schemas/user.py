"""
User Pydantic schemas
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    mobile_phone: str
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_domain: Optional[str] = None

    @field_validator('mobile_phone')
    @classmethod
    def validate_mobile_phone(cls, v):
        """Validate mobile phone number format"""
        if not v:
            raise ValueError('Mobile phone number is required')
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', v)
        
        # Check if it's a valid mobile number (10-15 digits)
        if not (10 <= len(digits_only) <= 15):
            raise ValueError('Mobile phone number must be between 10-15 digits')
        
        return digits_only


class UserCreate(UserBase):
    """User creation schema"""
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password strength with enhanced security requirements"""
        from app.core.config import settings
        
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long')
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        
        if settings.PASSWORD_REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        # Check for common weak patterns
        weak_patterns = [
            r'(.)\1{2,}',  # Repeated characters
            r'123456',  # Sequential numbers
            r'password',  # Common words
            r'qwerty',  # Keyboard patterns
        ]
        
        for pattern in weak_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Password contains weak patterns')
        
        return v


class UserLogin(BaseModel):
    """User login schema - accepts either identifier or email + password"""
    identifier: Optional[str] = None  # Can be email or mobile
    email: Optional[str] = None       # Backward compatibility for clients sending 'email'
    password: str

    @field_validator('identifier', mode='before')
    @classmethod
    def coerce_identifier(cls, v, info):
        """Allow 'email' field as an alias for identifier if identifier missing"""
        if v and isinstance(v, str) and v.strip():
            return v
        if hasattr(info, 'data') and 'email' in info.data:
            email = info.data['email']
            if email and isinstance(email, str) and email.strip():
                return email
        raise ValueError('Email or mobile phone number is required')

    @field_validator('identifier')
    @classmethod
    def validate_identifier(cls, v):
        """Validate that identifier is either email or mobile"""
        if not v:
            raise ValueError('Email or mobile phone number is required')
        
        # Check if it's an email
        if '@' in v:
            return v
        
        # Check if it's a mobile number
        digits_only = re.sub(r'\D', '', v)
        if 10 <= len(digits_only) <= 15:
            return digits_only
        
        raise ValueError('Please provide a valid email address or mobile phone number')


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
    phone_verified: bool
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserResponse(UserRead):
    """User response schema (alias for UserRead)"""
    pass


class UserInDB(UserRead):
    """User in database schema (includes hashed password)"""
    hashed_password: str
