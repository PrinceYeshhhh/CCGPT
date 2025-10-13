"""
Embed code Pydantic schemas
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class EmbedCodeBase(BaseModel):
    """Base embed code schema"""
    code_name: str
    widget_config: Dict[str, Any]


class EmbedCodeCreate(EmbedCodeBase):
    """Embed code creation schema"""
    pass


class EmbedCodeUpdate(BaseModel):
    """Embed code update schema"""
    code_name: Optional[str] = None
    widget_config: Optional[Dict[str, Any]] = None


class EmbedCodeResponse(EmbedCodeBase):
    """Embed code response schema"""
    id: uuid.UUID
    workspace_id: uuid.UUID
    client_api_key: str
    snippet_template: Optional[str] = None
    default_config: Dict[str, Any]
    custom_config: Optional[Dict[str, Any]] = None
    embed_script: str
    embed_html: Optional[str] = None
    is_active: bool
    usage_count: int
    last_used: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class WidgetConfig(BaseModel):
    """Widget configuration schema"""
    title: str = "Customer Support"
    placeholder: str = "Ask me anything..."
    primary_color: str = "#4f46e5"
    secondary_color: str = "#f8f9fa"
    text_color: str = "#111111"
    position: str = "bottom-right"  # bottom-right, bottom-left, top-right, top-left
    show_avatar: bool = True
    avatar_url: Optional[str] = None
    welcome_message: str = "Hello! How can I help you today?"
    max_messages: int = 50
    enable_sound: bool = True
    enable_typing_indicator: bool = True
    enable_websocket: bool = True
    theme: str = "light"  # light, dark, custom
    custom_css: Optional[str] = None


class EmbedCodeGenerateRequest(BaseModel):
    """Request schema for generating embed code"""
    workspace_id: str = Field(..., description="Workspace identifier")
    code_name: str = Field(..., description="Name for the embed code")
    config: Optional[WidgetConfig] = Field(None, description="Widget configuration")
    snippet_template: Optional[str] = Field(None, description="Custom snippet template")


class EmbedCodeGenerateResponse(BaseModel):
    """Response schema for generated embed code"""
    embed_code_id: uuid.UUID = Field(..., description="Generated embed code ID")
    client_api_key: str = Field(..., description="Client API key for widget authentication")
    embed_snippet: str = Field(..., description="HTML snippet to embed")
    widget_url: str = Field(..., description="URL to widget JavaScript file")
    config: WidgetConfig = Field(..., description="Widget configuration")


class WidgetAssetCreate(BaseModel):
    """Widget asset creation schema"""
    asset_type: str = Field(..., description="Type of asset (avatar, logo, background)")
    file_name: str = Field(..., description="Original file name")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    alt_text: Optional[str] = Field(None, description="Alt text for accessibility")


class WidgetAssetResponse(BaseModel):
    """Widget asset response schema"""
    id: uuid.UUID
    asset_type: str
    file_name: str
    file_url: str
    file_size: int
    mime_type: str
    alt_text: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WidgetPreviewRequest(BaseModel):
    """Request schema for widget preview"""
    config: WidgetConfig = Field(..., description="Widget configuration to preview")
    workspace_id: str = Field(..., description="Workspace identifier")


class WidgetPreviewResponse(BaseModel):
    """Response schema for widget preview"""
    preview_html: str = Field(..., description="HTML for widget preview")
    preview_css: str = Field(..., description="CSS for widget preview")
    preview_js: str = Field(..., description="JavaScript for widget preview")
