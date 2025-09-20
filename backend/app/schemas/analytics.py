"""
Analytics Pydantic schemas
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date


class AnalyticsOverview(BaseModel):
    """Analytics overview schema"""
    total_documents: int
    total_chunks: int
    total_sessions: int
    total_messages: int
    active_sessions: int
    avg_response_time: float
    avg_confidence: str
    top_questions: List[Dict[str, Any]]


class DocumentAnalytics(BaseModel):
    """Document analytics schema"""
    document_id: int
    filename: str
    status: str
    chunks_count: int
    views_count: int
    last_accessed: Optional[datetime] = None
    created_at: datetime


class SessionAnalytics(BaseModel):
    """Session analytics schema"""
    session_id: str
    created_at: datetime
    ended_at: Optional[datetime] = None
    duration_minutes: Optional[float] = None
    message_count: int
    user_satisfaction: Optional[str] = None
    is_flagged: bool = False


class MessageAnalytics(BaseModel):
    """Message analytics schema"""
    message_id: int
    role: str
    content: str
    response_time_ms: Optional[int] = None
    confidence_score: Optional[str] = None
    is_flagged: bool = False
    created_at: datetime


class UsageStats(BaseModel):
    """Usage statistics schema"""
    date: date
    sessions_count: int
    messages_count: int
    documents_uploaded: int
    avg_session_duration: float


class EmbedCodeAnalytics(BaseModel):
    """Embed code analytics schema"""
    code_id: int
    code_name: str
    usage_count: int
    last_used: Optional[datetime] = None
    is_active: bool
    created_at: datetime
