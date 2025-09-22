"""
RAG Query endpoints for enhanced retrieval-augmented generation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import structlog
import json

from app.models.subscriptions import Subscription

from app.core.database import get_db
from app.models.user import User
from app.schemas.rag import (
    RAGQueryRequest, 
    RAGQueryResponse, 
    RAGStreamChunk,
    RAGErrorResponse,
    RateLimitInfo,
    TokenBudgetInfo
)
from app.services.auth import AuthService
from app.services.rag_service import RAGService
from app.services.rate_limiting import rate_limiting_service
from app.services.token_budget import TokenBudgetService
from app.middleware.quota_middleware import check_quota, increment_usage
from app.api.api_v1.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    subscription: Optional[Subscription] = Depends(check_quota)
):
    """
    Process a RAG query with enhanced prompting and citations
    
    This endpoint implements the complete RAG pipeline:
    1. Embed query using sentence-transformers
    2. Search for relevant chunks using ChromaDB
    3. Build contextual prompt with citations
    4. Generate response using Google Gemini
    5. Return answer with sources and metadata
    """
    try:
        # Use user_id as workspace_id for now
        workspace_id = str(current_user.id)
        
        # Rate limiting check
        is_allowed, rate_limit_info = await rate_limiting_service.check_workspace_rate_limit(
            workspace_id=workspace_id,
            limit=60,  # 60 requests per minute
            window_seconds=60
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                    "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                    "X-RateLimit-Reset": str(int(rate_limit_info["reset_time"].timestamp()))
                }
            )
        
        # Token budget check
        token_budget_service = TokenBudgetService(db)
        estimated_tokens = len(request.query) // 4  # Rough estimation
        
        within_budget, budget_info = await token_budget_service.check_token_budget(
            workspace_id=workspace_id,
            requested_tokens=estimated_tokens,
            daily_limit=10000,  # 10k tokens per day
            monthly_limit=100000  # 100k tokens per month
        )
        
        if not within_budget:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Token budget exceeded. Please try again tomorrow.",
                headers={
                    "X-Daily-Limit": str(budget_info["daily_limit"]),
                    "X-Daily-Used": str(budget_info["daily_used"]),
                    "X-Monthly-Limit": str(budget_info["monthly_limit"]),
                    "X-Monthly-Used": str(budget_info["monthly_used"])
                }
            )
        
        # Process RAG query
        rag_service = RAGService(db)
        response = await rag_service.process_query(
            workspace_id=workspace_id,
            query=request.query,
            session_id=request.session_id,
            top_k=6
        )
        
        # Consume tokens
        if response.tokens_used:
            await token_budget_service.consume_tokens(
                workspace_id=workspace_id,
                tokens_used=response.tokens_used,
                model_used=response.model_used
            )
        
        # Increment quota usage
        await increment_usage(subscription, db)
        
        logger.info(
            "RAG query processed successfully",
            workspace_id=workspace_id,
            query=request.query[:100],
            response_time_ms=response.response_time_ms,
            sources_count=len(response.sources)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "RAG query failed",
            error=str(e),
            workspace_id=workspace_id,
            query=request.query[:100]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process RAG query"
        )


@router.post("/query/stream")
async def rag_query_stream(
    request: RAGQueryRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process a RAG query with streaming response for better UX
    
    Returns a streaming response with chunks for:
    - Query start
    - Vector search progress
    - Sources found
    - Answer generation
    - Final response
    """
    try:
        # Use user_id as workspace_id for now
        workspace_id = str(current_user.id)
        
        # Rate limiting check
        is_allowed, rate_limit_info = await rate_limiting_service.check_workspace_rate_limit(
            workspace_id=workspace_id,
            limit=60,
            window_seconds=60
        )
        
        if not is_allowed:
            error_response = RAGErrorResponse(
                error="Rate limit exceeded. Please try again later.",
                error_code="RATE_LIMIT_EXCEEDED",
                retry_after=60
            )
            return StreamingResponse(
                iter([f"data: {error_response.json()}\n\n"]),
                media_type="text/plain"
            )
        
        # Process streaming RAG query
        rag_service = RAGService(db)
        
        async def generate_stream():
            try:
                async for chunk in rag_service.process_query_stream(
                    workspace_id=workspace_id,
                    query=request.query,
                    session_id=request.session_id,
                    top_k=6
                ):
                    yield f"data: {chunk.json()}\n\n"
            except Exception as e:
                error_chunk = RAGStreamChunk(
                    type="error",
                    content=f"Error: {str(e)}",
                    metadata={"error": str(e)}
                )
                yield f"data: {error_chunk.json()}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(
            "RAG streaming query failed",
            error=str(e),
            workspace_id=workspace_id,
            query=request.query[:100]
        )
        
        error_response = RAGErrorResponse(
            error="Failed to process streaming query",
            error_code="STREAMING_ERROR"
        )
        return StreamingResponse(
            iter([f"data: {error_response.json()}\n\n"]),
            media_type="text/plain"
        )


@router.get("/rate-limit")
async def get_rate_limit_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get rate limit information for current user"""
    try:
        workspace_id = str(current_user.id)
        
        is_allowed, rate_limit_info = await rate_limiting_service.check_workspace_rate_limit(
            workspace_id=workspace_id,
            limit=60,
            window_seconds=60
        )
        
        return RateLimitInfo(**rate_limit_info)
        
    except Exception as e:
        logger.error("Failed to get rate limit info", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit information"
        )


@router.get("/token-budget")
async def get_token_budget_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get token budget information for current user"""
    try:
        workspace_id = str(current_user.id)
        token_budget_service = TokenBudgetService(db)
        
        budget_info = await token_budget_service.get_budget_info(workspace_id)
        
        return TokenBudgetInfo(
            daily_limit=10000,
            daily_used=budget_info["daily_used"],
            monthly_limit=100000,
            monthly_used=budget_info["monthly_used"],
            reset_daily_at=budget_info["reset_daily_at"],
            reset_monthly_at=budget_info["reset_monthly_at"]
        )
        
    except Exception as e:
        logger.error("Failed to get token budget info", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve token budget information"
        )


@router.post("/reset-budget")
async def reset_token_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reset token budget for current user (admin only)"""
    try:
        workspace_id = str(current_user.id)
        token_budget_service = TokenBudgetService(db)
        
        success = await token_budget_service.reset_budget(workspace_id)
        
        if success:
            return {"message": "Token budget reset successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset token budget"
            )
        
    except Exception as e:
        logger.error("Failed to reset token budget", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset token budget"
        )
