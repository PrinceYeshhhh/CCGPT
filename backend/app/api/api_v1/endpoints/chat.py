"""
Chat endpoints for customer support interactions
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatRequest, 
    ChatResponse, 
    ChatSessionResponse, 
    ChatSessionWithMessages,
    ChatMessageResponse
)
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.api.api_v1.dependencies import get_current_user
from app.middleware.quota_middleware import check_quota, increment_usage

logger = structlog.get_logger()
router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    subscription = Depends(check_quota)
):
    """Send a message and get AI response"""
    try:
        chat_service = ChatService(db)
        
        # Process the message and get response
        response = await chat_service.process_message(
            user_id=current_user.id,
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        
        # Increment usage after successful message processing
        await increment_usage(subscription, db)
        
        logger.info(
            "Message processed successfully",
            user_id=current_user.id,
            session_id=response.session_id,
            message_id=response.message.id
        )
        
        return response
        
    except Exception as e:
        logger.error(
            "Message processing failed",
            error=str(e),
            user_id=current_user.id,
            message=request.message[:100]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    skip: int = 0,
    limit: int = 20,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's chat sessions"""
    try:
        chat_service = ChatService(db)
        sessions = chat_service.get_user_sessions(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            active_only=active_only
        )
        
        return [ChatSessionResponse.from_orm(session) for session in sessions]
        
    except Exception as e:
        logger.error("Failed to get chat sessions", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )


@router.get("/sessions/{session_id}", response_model=ChatSessionWithMessages)
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific chat session with messages"""
    try:
        chat_service = ChatService(db)
        session = chat_service.get_session_by_id(
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        return ChatSessionWithMessages.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get chat session",
            error=str(e),
            user_id=current_user.id,
            session_id=session_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat session"
        )


@router.post("/sessions/{session_id}/end")
async def end_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End a chat session"""
    try:
        chat_service = ChatService(db)
        success = chat_service.end_session(
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        logger.info(
            "Chat session ended",
            user_id=current_user.id,
            session_id=session_id
        )
        
        return {"message": "Chat session ended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to end chat session",
            error=str(e),
            user_id=current_user.id,
            session_id=session_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to end chat session"
        )


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session and all its messages"""
    try:
        chat_service = ChatService(db)
        success = chat_service.delete_session(
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        logger.info(
            "Chat session deleted",
            user_id=current_user.id,
            session_id=session_id
        )
        
        return {"message": "Chat session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete chat session",
            error=str(e),
            user_id=current_user.id,
            session_id=session_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete chat session"
        )


@router.post("/sessions/{session_id}/flag")
async def flag_message(
    session_id: str,
    message_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Flag a message for review"""
    try:
        chat_service = ChatService(db)
        success = chat_service.flag_message(
            session_id=session_id,
            message_id=message_id,
            user_id=current_user.id,
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        logger.info(
            "Message flagged",
            user_id=current_user.id,
            session_id=session_id,
            message_id=message_id,
            reason=reason
        )
        
        return {"message": "Message flagged successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to flag message",
            error=str(e),
            user_id=current_user.id,
            session_id=session_id,
            message_id=message_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to flag message"
        )
