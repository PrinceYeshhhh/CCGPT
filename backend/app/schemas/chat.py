"""
Chat Pydantic schemas
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class ChatMessageBase(BaseModel):
    """Base chat message schema"""
    content: str


class ChatMessageCreate(ChatMessageBase):
    """Chat message creation schema"""
    session_id: Optional[str] = None


class ChatMessageResponse(ChatMessageBase):
    """Chat message response schema"""
    model_config = {"protected_namespaces": (), "from_attributes": True}
    
    id: uuid.UUID
    role: str
    model_used: Optional[str] = None
    response_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    sources_used: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[str] = None
    is_flagged: bool = False
    created_at: datetime


class ChatSessionResponse(BaseModel):
    """Chat session response schema"""
    id: uuid.UUID
    workspace_id: uuid.UUID
    session_id: str
    user_label: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    last_activity_at: datetime
    message_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)


class ChatSessionWithMessages(ChatSessionResponse):
    """Chat session with messages"""
    messages: List[ChatMessageResponse] = []


class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Chat response schema"""
    message: ChatMessageResponse
    session_id: str
    sources: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[str] = None


class ChatSessionCreate(BaseModel):
    """Chat session creation schema"""
    workspace_id: str = Field(..., description="Workspace identifier")
    user_label: Optional[str] = Field(None, description="Optional user label like 'Customer A'")
    visitor_ip: Optional[str] = Field(None, description="Visitor IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    referrer: Optional[str] = Field(None, description="Referrer URL")


class ChatSessionUpdate(BaseModel):
    """Chat session update schema"""
    user_label: Optional[str] = Field(None, description="Optional user label like 'Customer A'")
    is_active: Optional[bool] = Field(None, description="Session active status")


class WebSocketMessage(BaseModel):
    """WebSocket message schema"""
    type: str = Field(..., description="Message type")
    content: Optional[str] = Field(None, description="Message content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: str = Field(..., description="Message timestamp")


class WebSocketConnectionInfo(BaseModel):
    """WebSocket connection information"""
    session_id: str = Field(..., description="Session identifier")
    workspace_id: str = Field(..., description="Workspace identifier")
    user_id: str = Field(..., description="User identifier")
    connected_at: datetime = Field(..., description="Connection timestamp")


class SessionStateInfo(BaseModel):
    """Session state information"""
    session_id: str = Field(..., description="Session identifier")
    workspace_id: str = Field(..., description="Workspace identifier")
    user_id: str = Field(..., description="User identifier")
    last_activity: Optional[Dict[str, Any]] = Field(None, description="Last activity information")
    created_at: str = Field(..., description="Session creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
