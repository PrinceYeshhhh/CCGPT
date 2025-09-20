"""
Workspace model for multi-tenant support
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base

class Workspace(Base):
    """Workspace model for multi-tenant support"""
    __tablename__ = "workspaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    support_email = Column(String(255), nullable=True)
    timezone = Column(String(50), default="UTC")
    plan = Column(String(50), default="free")  # 'free', 'starter', 'pro', 'enterprise', 'white_label'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="workspace")
    subscription = relationship("Subscription", back_populates="workspace", uselist=False)
    documents = relationship("Document", back_populates="workspace")
    chat_sessions = relationship("ChatSession", back_populates="workspace")
    embed_codes = relationship("EmbedCode", back_populates="workspace")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}', plan='{self.plan}')>"
