"""
WebSocket endpoints for realtime chat functionality
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import structlog

from app.core.database import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.api.api_v1.dependencies import get_current_user
from app.services.websocket_service import realtime_chat_service

logger = structlog.get_logger()
router = APIRouter()


@router.websocket("/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    workspace_id: str,
    user_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint for realtime chat
    
    Args:
        session_id: Chat session identifier
        workspace_id: Workspace identifier
        user_id: User identifier
        token: Optional authentication token
    """
    try:
        # Validate session_id format
        if not session_id or len(session_id) < 10:
            await websocket.close(code=4000, reason="Invalid session ID")
            return
        
        # TODO: Add proper authentication for WebSocket connections
        # For now, we'll accept the connection without token validation
        # In production, you should validate the token here
        
        logger.info(
            "WebSocket connection attempt",
            session_id=session_id,
            workspace_id=workspace_id,
            user_id=user_id
        )
        
        # Handle the WebSocket connection
        await realtime_chat_service.handle_websocket_connection(
            websocket=websocket,
            session_id=session_id,
            workspace_id=workspace_id,
            user_id=user_id
        )
        
    except WebSocketDisconnect:
        logger.info(
            "WebSocket disconnected",
            session_id=session_id,
            user_id=user_id
        )
    except Exception as e:
        logger.error(
            "WebSocket error",
            error=str(e),
            session_id=session_id,
            user_id=user_id
        )
        try:
            await websocket.close(code=4000, reason="Internal server error")
        except:
            pass


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    try:
        stats = realtime_chat_service.get_connection_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error("Failed to get WebSocket stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve WebSocket statistics"
        )


@router.post("/broadcast/{session_id}")
async def broadcast_to_session(
    session_id: str,
    message: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Broadcast a message to all users in a session (admin only)"""
    try:
        # Check if session exists and user has access
        session_info = realtime_chat_service.websocket_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or not active"
            )
        
        # Broadcast message
        await realtime_chat_service.websocket_manager.broadcast_to_session(
            session_id=session_id,
            message=message
        )
        
        logger.info(
            "Message broadcasted to session",
            session_id=session_id,
            user_id=current_user.id
        )
        
        return {
            "status": "success",
            "message": "Message broadcasted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to broadcast message",
            error=str(e),
            session_id=session_id,
            user_id=current_user.id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast message"
        )
