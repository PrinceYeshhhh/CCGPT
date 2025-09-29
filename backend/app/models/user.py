"""
User and authentication models
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from app.core.uuid_type import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Business information
    business_name = Column(String(255), nullable=True)
    business_domain = Column(String(255), nullable=True)
    subscription_plan = Column(String(50), default="free")
    mobile_phone = Column(String(20), unique=True, nullable=True)
    phone_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(128), nullable=True)
    email_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Profile information
    username = Column(String(50), unique=True, nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    browser_notifications = Column(Boolean, default=False)
    usage_alerts = Column(Boolean, default=True)
    billing_updates = Column(Boolean, default=True)
    security_alerts = Column(Boolean, default=True)
    product_updates = Column(Boolean, default=False)
    
    # Appearance preferences
    theme = Column(String(20), default="system")  # light, dark, system
    layout = Column(String(20), default="comfortable")  # compact, comfortable, spacious
    language = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    
    # Security
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(32), nullable=True)
    two_factor_backup_codes = Column(String(1000), nullable=True)  # JSON array of backup codes
    
    # Relationships
    workspace = relationship("Workspace", back_populates="users")
    documents = relationship("Document", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    embed_codes = relationship("EmbedCode", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
