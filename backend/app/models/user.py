"""
User and authentication models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from app.core.uuid_type import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from typing import Optional
from datetime import datetime


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password: str = Column(String(255), nullable=False)
    full_name: Optional[str] = Column(String(255), nullable=True)
    workspace_id: str = Column(UUID(), ForeignKey("workspaces.id"), nullable=False)
    is_active: bool = Column(Boolean, default=True)
    is_superuser: bool = Column(Boolean, default=False)
    created_at: Optional[datetime] = Column(DateTime(timezone=True), server_default=func.now())
    updated_at: Optional[datetime] = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Business information
    business_name: Optional[str] = Column(String(255), nullable=True)
    business_domain: Optional[str] = Column(String(255), nullable=True)
    subscription_plan: str = Column(String(50), default="free")
    mobile_phone: Optional[str] = Column(String(20), unique=True, nullable=True)
    phone_verified: bool = Column(Boolean, default=False)
    email_verified: bool = Column(Boolean, default=False)
    email_verification_token: Optional[str] = Column(String(128), nullable=True)
    email_verification_sent_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    username: Optional[str] = Column(String(50), unique=True, nullable=True)
    profile_picture_url: Optional[str] = Column(String(500), nullable=True)
    
    # Notification preferences
    email_notifications: bool = Column(Boolean, default=True)
    browser_notifications: bool = Column(Boolean, default=False)
    usage_alerts: bool = Column(Boolean, default=True)
    billing_updates: bool = Column(Boolean, default=True)
    security_alerts: bool = Column(Boolean, default=True)
    product_updates: bool = Column(Boolean, default=False)
    
    # Appearance preferences
    theme: str = Column(String(20), default="system")  # light, dark, system
    layout: str = Column(String(20), default="comfortable")  # compact, comfortable, spacious
    language: str = Column(String(10), default="en")
    timezone: str = Column(String(50), default="UTC")
    
    # Security
    two_factor_enabled: bool = Column(Boolean, default=False)
    two_factor_secret: Optional[str] = Column(String(32), nullable=True)
    two_factor_backup_codes: Optional[str] = Column(String(1000), nullable=True)  # JSON array of backup codes
    
    # Relationships
    workspace = relationship("Workspace", back_populates="users")
    documents = relationship("Document", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    embed_codes = relationship("EmbedCode", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
