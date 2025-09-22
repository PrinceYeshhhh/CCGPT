"""
Chat and conversation models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from app.core.uuid_type import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Session metadata
    user_label = Column(String(255), nullable=True)  # Optional user label like "Customer A"
    visitor_ip = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="chat_sessions")
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ChatSession(id={self.id}, session_id='{self.session_id}')>"


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(), ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # AI response metadata
    model_used = Column(String(100), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # RAG metadata
    sources_used = Column(JSON, nullable=True)  # List of document chunks used
    confidence_score = Column(String(10), nullable=True)  # high, medium, low
    
    # Message metadata
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role='{self.role}', session_id={self.session_id})>"


# EmbedCode model moved to embed.py to avoid duplicate table definitions
