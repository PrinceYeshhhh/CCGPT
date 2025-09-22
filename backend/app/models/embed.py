"""
Embed code models for widget integration
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from app.core.uuid_type import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class EmbedCode(Base):
    """Embed code model for widget integration"""
    __tablename__ = "embed_codes"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Embed code details
    code_name = Column(String(255), nullable=False)
    client_api_key = Column(String(255), unique=True, nullable=False, index=True)
    snippet_template = Column(Text, nullable=True)  # Base JS template
    
    # Widget configuration
    default_config = Column(JSON, nullable=False)  # Default widget config
    custom_config = Column(JSON, nullable=True)    # Custom overrides
    
    # Generated code
    embed_script = Column(Text, nullable=False)
    embed_html = Column(Text, nullable=True)
    
    # Usage tracking
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="embed_codes")
    user = relationship("User", back_populates="embed_codes")
    
    def __repr__(self):
        return f"<EmbedCode(id={self.id}, code_name='{self.code_name}')>"


class WidgetAsset(Base):
    """Widget asset model for storing custom assets"""
    __tablename__ = "widget_assets"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    embed_code_id = Column(UUID(), ForeignKey("embed_codes.id"), nullable=True)
    
    # Asset details
    asset_type = Column(String(50), nullable=False)  # avatar, logo, background
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Asset metadata
    alt_text = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    embed_code = relationship("EmbedCode")
    
    def __repr__(self):
        return f"<WidgetAsset(id={self.id}, asset_type='{self.asset_type}')>"
