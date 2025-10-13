"""
Settings Pydantic schemas
"""

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class ProfileUpdate(BaseModel):
    """Profile update schema"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_domain: Optional[str] = None
    profile_picture_url: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v, info=None):
        """Validate username format"""
        if not v:
            raise ValueError('Username is required')
        
        # Username should be 3-30 characters, alphanumeric and underscores only
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', v):
            raise ValueError('Username must be 3-30 characters, alphanumeric and underscores only')
        
        return v.lower()


class PasswordChange(BaseModel):
    """Password change schema"""
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v, info=None):
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v, info=None):
        """Validate password confirmation"""
        if hasattr(info, 'data') and 'new_password' in info.data and v != info.data['new_password'] if hasattr(info, "data") and info.data else None:
            raise ValueError('Passwords do not match')
        return v


class OrganizationUpdate(BaseModel):
    """Organization update schema"""
    name: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    support_email: Optional[str] = None
    logo_url: Optional[str] = None
    custom_domain: Optional[str] = None
    widget_domain: Optional[str] = None
    timezone: str = "UTC"

    @field_validator('custom_domain', 'widget_domain')
    @classmethod
    def validate_domain(cls, v, info=None):
        """Validate domain format"""
        if v and not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$', v):
            raise ValueError('Please enter a valid domain')
        return v


class TeamMemberInvite(BaseModel):
    """Team member invitation schema"""
    email: EmailStr
    role: str = "member"  # member, admin, owner
    message: Optional[str] = None


class TeamMember(BaseModel):
    """Team member schema"""
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    status: str  # active, pending, inactive
    joined_at: datetime
    last_active: Optional[datetime] = None


class NotificationSettings(BaseModel):
    """Notification settings schema"""
    email_notifications: bool = True
    browser_notifications: bool = False
    usage_alerts: bool = True
    billing_updates: bool = True
    security_alerts: bool = True
    product_updates: bool = False


class AppearanceSettings(BaseModel):
    """Appearance settings schema"""
    theme: str = "system"  # light, dark, system
    layout: str = "comfortable"  # compact, comfortable, spacious
    language: str = "en"
    timezone: str = "UTC"


class TwoFactorSetup(BaseModel):
    """Two-factor authentication setup schema"""
    secret: str
    qr_code: str
    backup_codes: List[str]


class SettingsResponse(BaseModel):
    """Complete settings response schema"""
    profile: ProfileUpdate
    organization: OrganizationUpdate
    notifications: NotificationSettings
    appearance: AppearanceSettings
    two_factor_enabled: bool
    team_members: List[TeamMember]


class FileUploadResponse(BaseModel):
    """File upload response schema"""
    url: str
    filename: str
    size: int
    content_type: str
