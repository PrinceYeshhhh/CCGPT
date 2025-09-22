"""
Enhanced chat session endpoints for session management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import structlog
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionResponse, 
    ChatSessionWithMessages,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionUpdate
)
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.services.session_persistence import session_persistence_service
from app.api.api_v1.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    request: ChatSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session"""
    try:
        chat_service = ChatService(db)
        
        # Generate session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        session = ChatSession(
            workspace_id=uuid.UUID(request.workspace_id),
            user_id=current_user.id,
            session_id=session_id,
            user_label=request.user_label,
            visitor_ip=request.visitor_ip,
            user_agent=request.user_agent,
            referrer=request.referrer,
            is_active=True
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        # Store initial session state in Redis
        await session_persistence_service.store_session_state(
            session_id=session_id,
            state={
                "workspace_id": request.workspace_id,
                "user_id": current_user.id,
                "created_at": session.created_at.isoformat(),
                "message_count": 0
            }
        )
        
        logger.info(
            "Chat session created",
            session_id=session_id,
            workspace_id=request.workspace_id,
            user_id=current_user.id
        )
        
        return ChatSessionResponse.from_orm(session)
        
    except Exception as e:
        logger.error(
            "Failed to create chat session",
            error=str(e),
            user_id=current_user.id,
            workspace_id=request.workspace_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session"
        )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False, description="Show only active sessions"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's chat sessions with optional filtering"""
    try:
        chat_service = ChatService(db)
        
        # Build query
        query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
        
        if workspace_id:
            query = query.filter(ChatSession.workspace_id == uuid.UUID(workspace_id))
        
        if active_only:
            query = query.filter(ChatSession.is_active == True)
        
        # Apply pagination and ordering
        sessions = query.order_by(
            ChatSession.last_activity_at.desc()
        ).offset(skip).limit(limit).all()
        
        # Get message counts for each session
        session_responses = []
        for session in sessions:
            message_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).count()
            
            session_response = ChatSessionResponse.from_orm(session)
            session_response.message_count = message_count
            session_responses.append(session_response)
        
        return session_responses
        
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
        
        # Get messages for the session
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        # Update last activity
        session.last_activity_at = db.query(func.now()).scalar()
        db.commit()
        
        # Update session activity in Redis
        await session_persistence_service.update_session_activity(
            session_id=session_id,
            activity_type="session_viewed"
        )
        
        # Build response
        session_response = ChatSessionWithMessages.from_orm(session)
        session_response.messages = [ChatMessageResponse.from_orm(msg) for msg in messages]
        session_response.message_count = len(messages)
        
        return session_response
        
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


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get messages for a specific session"""
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
        
        # Get messages with pagination
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.desc()).offset(skip).limit(limit).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        return [ChatMessageResponse.from_orm(msg) for msg in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get session messages",
            error=str(e),
            user_id=current_user.id,
            session_id=session_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session messages"
        )


@router.put("/sessions/{session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    session_id: str,
    request: ChatSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a chat session"""
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
        
        # Update fields
        if request.user_label is not None:
            session.user_label = request.user_label
        
        if request.is_active is not None:
            session.is_active = request.is_active
            if not request.is_active:
                session.ended_at = db.query(func.now()).scalar()
        
        db.commit()
        db.refresh(session)
        
        # Update session state in Redis
        await session_persistence_service.update_session_activity(
            session_id=session_id,
            activity_type="session_updated",
            metadata={"updated_fields": list(request.dict(exclude_unset=True).keys())}
        )
        
        logger.info(
            "Chat session updated",
            session_id=session_id,
            user_id=current_user.id
        )
        
        return ChatSessionResponse.from_orm(session)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update chat session",
            error=str(e),
            user_id=current_user.id,
            session_id=session_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat session"
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
        
        # Clean up session state in Redis
        await session_persistence_service.delete_session_state(session_id)
        
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
        
        # Clean up session state in Redis
        await session_persistence_service.delete_session_state(session_id)
        
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


@router.get("/sessions/{session_id}/state")
async def get_session_state(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ephemeral session state from Redis"""
    try:
        # Verify session exists and user has access
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
        
        # Get session state from Redis
        state = await session_persistence_service.get_session_state(session_id)
        
        if not state:
            return {"message": "No session state found"}
        
        return {
            "session_id": session_id,
            "state": state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get session state",
            error=str(e),
            user_id=current_user.id,
            session_id=session_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session state"
        )
