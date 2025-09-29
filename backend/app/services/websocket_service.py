"""
WebSocket service for realtime chat functionality
"""

import json
import asyncio
import uuid
import time
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import structlog
from datetime import datetime, timedelta

from app.services.rag_service import RAGService
from app.services.rate_limiting import rate_limiting_service
from app.services.token_budget import TokenBudgetService
from app.core.database import WriteSessionLocal as SessionLocal

logger = structlog.get_logger()


class WebSocketManager:
    """Manages WebSocket connections and realtime chat"""
    
    def __init__(self):
        # Active connections: {session_id: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # Session metadata: {session_id: {workspace_id, user_id, created_at}}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str, workspace_id: str, user_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
        
        self.active_connections[session_id][user_id] = websocket
        self.session_metadata[session_id] = {
            "workspace_id": workspace_id,
            "user_id": user_id,
            "created_at": datetime.now()
        }
        
        logger.info(
            "WebSocket connected",
            session_id=session_id,
            workspace_id=workspace_id,
            user_id=user_id
        )
        
        # Send welcome message
        await self.send_message(session_id, user_id, {
            "type": "connection_established",
            "message": "Connected to chat",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, session_id: str, user_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            if user_id in self.active_connections[session_id]:
                del self.active_connections[session_id][user_id]
                
                # If no more connections for this session, clean up
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
                    if session_id in self.session_metadata:
                        del self.session_metadata[session_id]
        
        logger.info(
            "WebSocket disconnected",
            session_id=session_id,
            user_id=user_id
        )
    
    async def send_message(self, session_id: str, user_id: str, message: Dict[str, Any]):
        """Send a message to a specific user in a session"""
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            try:
                websocket = self.active_connections[session_id][user_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(
                    "Failed to send WebSocket message",
                    error=str(e),
                    session_id=session_id,
                    user_id=user_id
                )
                # Remove broken connection
                self.disconnect(session_id, user_id)
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast a message to all users in a session"""
        if session_id in self.active_connections:
            for user_id, websocket in self.active_connections[session_id].items():
                await self.send_message(session_id, user_id, message)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata"""
        return self.session_metadata.get(session_id)
    
    def get_active_sessions(self) -> Dict[str, int]:
        """Get count of active connections per session"""
        return {
            session_id: len(connections) 
            for session_id, connections in self.active_connections.items()
        }


class RealtimeChatService:
    """Service for handling realtime chat with WebSocket streaming"""
    
    def __init__(self):
        self.websocket_manager = WebSocketManager()
        self.rag_service = None  # Will be initialized per request
    
    async def handle_websocket_connection(
        self, 
        websocket: WebSocket, 
        session_id: str, 
        workspace_id: str, 
        user_id: str
    ):
        """Handle a WebSocket connection for realtime chat"""
        await self.websocket_manager.connect(websocket, session_id, workspace_id, user_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process the message
                await self._process_realtime_message(
                    session_id=session_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    message_data=message_data
                )
                
        except WebSocketDisconnect:
            self.websocket_manager.disconnect(session_id, user_id)
        except Exception as e:
            logger.error(
                "WebSocket error",
                error=str(e),
                session_id=session_id,
                user_id=user_id
            )
            self.websocket_manager.disconnect(session_id, user_id)
    
    async def _process_realtime_message(
        self,
        session_id: str,
        workspace_id: str,
        user_id: str,
        message_data: Dict[str, Any]
    ):
        """Process a realtime chat message"""
        try:
            message_type = message_data.get("type", "user_message")
            
            if message_type == "user_message":
                await self._handle_user_message(
                    session_id=session_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    message=message_data.get("message", ""),
                    context=message_data.get("context")
                )
            elif message_type == "typing_start":
                await self._handle_typing_start(session_id, user_id)
            elif message_type == "typing_stop":
                await self._handle_typing_stop(session_id, user_id)
            elif message_type == "ping":
                await self._handle_ping(session_id, user_id)
            else:
                logger.warning(
                    "Unknown message type",
                    message_type=message_type,
                    session_id=session_id
                )
                
        except Exception as e:
            logger.error(
                "Failed to process realtime message",
                error=str(e),
                session_id=session_id,
                user_id=user_id
            )
            
            # Send error message to user
            await self.websocket_manager.send_message(session_id, user_id, {
                "type": "error",
                "message": "Failed to process your message. Please try again.",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_user_message(
        self,
        session_id: str,
        workspace_id: str,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Handle a user message with streaming response"""
        try:
            # Send typing indicator
            await self.websocket_manager.send_message(session_id, user_id, {
                "type": "assistant_typing",
                "message": "AI is thinking...",
                "timestamp": datetime.now().isoformat()
            })
            
            # Rate limiting check
            is_allowed, rate_limit_info = await rate_limiting_service.check_workspace_rate_limit(
                workspace_id=workspace_id,
                limit=60,
                window_seconds=60
            )
            
            if not is_allowed:
                await self.websocket_manager.send_message(session_id, user_id, {
                    "type": "error",
                    "message": "Rate limit exceeded. Please try again later.",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            # Initialize RAG service
            db = SessionLocal()
            try:
                rag_service = RAGService(db)
                
                # Process with streaming
                await self._stream_rag_response(
                    rag_service=rag_service,
                    session_id=session_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    message=message,
                    context=context
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(
                "Failed to handle user message",
                error=str(e),
                session_id=session_id,
                user_id=user_id
            )
            
            await self.websocket_manager.send_message(session_id, user_id, {
                "type": "error",
                "message": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _stream_rag_response(
        self,
        rag_service: RAGService,
        session_id: str,
        workspace_id: str,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Stream RAG response in realtime"""
        try:
            # Send search indicator
            await self.websocket_manager.send_message(session_id, user_id, {
                "type": "searching",
                "message": "Searching knowledge base...",
                "timestamp": datetime.now().isoformat()
            })
            
            # Stream the RAG response
            full_response = ""
            sources = []
            
            async for chunk in rag_service.process_query_stream(
                workspace_id=workspace_id,
                query=message,
                session_id=session_id,
                top_k=6
            ):
                if chunk.type == "answer" and chunk.content:
                    # Stream the answer content
                    full_response += chunk.content
                    
                    # Send partial response
                    await self.websocket_manager.send_message(session_id, user_id, {
                        "type": "assistant_message_chunk",
                        "content": chunk.content,
                        "is_partial": True,
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif chunk.type == "sources" and chunk.sources:
                    sources = [source.dict() for source in chunk.sources]
                
                elif chunk.type == "end":
                    # Send final complete response
                    await self.websocket_manager.send_message(session_id, user_id, {
                        "type": "assistant_message_complete",
                        "content": full_response,
                        "sources": sources,
                        "is_partial": False,
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif chunk.type == "error":
                    await self.websocket_manager.send_message(session_id, user_id, {
                        "type": "error",
                        "message": chunk.content or "An error occurred while processing your request.",
                        "timestamp": datetime.now().isoformat()
                    })
                    return
            
        except Exception as e:
            logger.error(
                "Failed to stream RAG response",
                error=str(e),
                session_id=session_id,
                user_id=user_id
            )
            
            await self.websocket_manager.send_message(session_id, user_id, {
                "type": "error",
                "message": "Failed to generate response. Please try again.",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_typing_start(self, session_id: str, user_id: str):
        """Handle typing start indicator"""
        await self.websocket_manager.broadcast_to_session(session_id, {
            "type": "user_typing",
            "user_id": user_id,
            "is_typing": True,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_typing_stop(self, session_id: str, user_id: str):
        """Handle typing stop indicator"""
        await self.websocket_manager.broadcast_to_session(session_id, {
            "type": "user_typing",
            "user_id": user_id,
            "is_typing": False,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_ping(self, session_id: str, user_id: str):
        """Handle ping/pong for connection health"""
        await self.websocket_manager.send_message(session_id, user_id, {
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        })
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        active_sessions = self.websocket_manager.get_active_sessions()
        total_connections = sum(active_sessions.values())
        
        return {
            "total_connections": total_connections,
            "active_sessions": len(active_sessions),
            "sessions": active_sessions
        }
    
    async def process_chat_message(
        self,
        session_id: str,
        workspace_id: str,
        user_id: str,
        message: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Process a chat message and return response"""
        try:
            # Initialize RAG service if needed
            if not self.rag_service:
                from app.services.rag_service import RAGService
                from app.core.database import get_db
                db = next(get_db())
                self.rag_service = RAGService(db)
            
            # Process message with RAG
            response = await self.rag_service.process_query(
                query=message,
                workspace_id=workspace_id,
                session_id=session_id,
                user_id=user_id
            )
            
            return {
                "type": "chat_response",
                "content": response.get("answer", "I'm sorry, I couldn't process that message."),
                "sources": response.get("sources", []),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error("Failed to process chat message", error=str(e))
            return {
                "type": "error",
                "content": "Sorry, I encountered an error processing your message.",
                "timestamp": time.time()
            }
    
    async def broadcast_typing(
        self,
        session_id: str,
        user_id: str,
        is_typing: bool
    ):
        """Broadcast typing indicator to session"""
        try:
            if session_id in self.websocket_manager.active_connections:
                message = {
                    "type": "typing",
                    "user_id": user_id,
                    "is_typing": is_typing,
                    "timestamp": time.time()
                }
                
                # Send to all connections in the session
                for conn_user_id, websocket in self.websocket_manager.active_connections[session_id].items():
                    if conn_user_id != user_id:  # Don't send to the user who is typing
                        try:
                            await websocket.send_json(message)
                        except Exception as e:
                            logger.error("Failed to send typing indicator", error=str(e))
                            
        except Exception as e:
            logger.error("Failed to broadcast typing", error=str(e))


# Global instance
realtime_chat_service = RealtimeChatService()

# Backwards-compatibility alias expected by some tests
WebSocketService = RealtimeChatService