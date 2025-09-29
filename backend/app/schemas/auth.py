"""
Authentication Pydantic schemas
"""

from pydantic import BaseModel
from pydantic import EmailStr
from typing import Optional


class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


class TokenData(BaseModel):
    """Token data schema"""
    email: str = None


class RegisterRequest(BaseModel):
    """Registration request with mobile + OTP verification"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_domain: Optional[str] = None
    mobile_phone: str
    otp_code: str


class OTPRequest(BaseModel):
    """Request to send OTP to a mobile phone"""
    mobile_phone: str
