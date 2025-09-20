"""
RAG (Retrieval-Augmented Generation) schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class RAGQueryRequest(BaseModel):
    """RAG query request schema"""
    workspace_id: str = Field(..., description="Workspace identifier")
    session_id: Optional[str] = Field(None, description="Optional session ID for conversation continuity")
    query: str = Field(..., description="User query", min_length=1, max_length=1000)


class RAGSource(BaseModel):
    """RAG source citation schema"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Document ID")
    chunk_index: int = Field(..., description="Chunk index within document")
    text: str = Field(..., description="Source text excerpt")
    similarity_score: float = Field(..., description="Similarity score", ge=0.0, le=1.0)


class RAGQueryResponse(BaseModel):
    """RAG query response schema"""
    answer: str = Field(..., description="AI-generated answer")
    sources: List[RAGSource] = Field(..., description="Cited sources")
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    session_id: str = Field(..., description="Session ID")
    tokens_used: Optional[int] = Field(None, description="Tokens used for generation")
    confidence_score: str = Field(..., description="Confidence level: high/medium/low")
    model_used: str = Field(..., description="LLM model used")


class RAGStreamChunk(BaseModel):
    """RAG streaming response chunk"""
    type: str = Field(..., description="Chunk type: start/answer/sources/end")
    content: Optional[str] = Field(None, description="Chunk content")
    sources: Optional[List[RAGSource]] = Field(None, description="Sources (for sources chunk)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit: int = Field(..., description="Request limit per window")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset_time: datetime = Field(..., description="When the rate limit resets")
    window_seconds: int = Field(..., description="Rate limit window in seconds")


class TokenBudgetInfo(BaseModel):
    """Token budget information"""
    daily_limit: int = Field(..., description="Daily token limit")
    daily_used: int = Field(..., description="Tokens used today")
    monthly_limit: int = Field(..., description="Monthly token limit")
    monthly_used: int = Field(..., description="Tokens used this month")
    reset_daily_at: datetime = Field(..., description="When daily budget resets")
    reset_monthly_at: datetime = Field(..., description="When monthly budget resets")


class RAGErrorResponse(BaseModel):
    """RAG error response schema"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")
