"""
Chat service for handling conversations and AI responses
"""

import uuid
import time
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import structlog

from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.services.vector_service import VectorService
from app.services.gemini_service import GeminiService
from app.services.support_context_service import support_context_service
from app.utils.cache import analytics_cache

logger = structlog.get_logger()


class ChatService:
    """Chat service for managing conversations and AI responses"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_service = VectorService()
        self.gemini_service = GeminiService()
    
    async def process_message(
        self,
        user_id: int,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a user message and generate AI response"""
        
        # Get or create session
        session = await self._get_or_create_session(user_id, session_id)
        
        # Save user message
        user_message = self._save_message(
            session_id=session.id,
            role="user",
            content=message
        )
        
        # Generate AI response
        start_time = time.time()
        ai_response = await self._generate_ai_response(
            user_id=user_id,
            message=message,
            context=context
        )
        response_time = int((time.time() - start_time) * 1000)
        
        # Save AI response
        ai_message = self._save_message(
            session_id=session.id,
            role="assistant",
            content=ai_response["content"],
            model_used=ai_response.get("model_used"),
            response_time_ms=response_time,
            tokens_used=ai_response.get("tokens_used"),
            sources_used=ai_response.get("sources_used"),
            confidence_score=ai_response.get("confidence_score")
        )
        # Invalidate analytics cache for workspace if provided; fallback to user scope
        try:
            workspace_id = None
            if context and isinstance(context, dict):
                workspace_id = context.get("workspace_id")
            if workspace_id:
                analytics_cache.invalidate_workspace_sync(str(workspace_id))
            else:
                analytics_cache.invalidate_workspace_sync(str(user_id))
        except Exception:
            pass
        
        # Update session
        session.updated_at = func.now()
        self.db.commit()
        
        return {
            "message": ai_message,
            "session_id": session.session_id,
            "sources": ai_response.get("sources_used"),
            "confidence": ai_response.get("confidence_score"),
            "tone": ai_response.get("tone", "friendly"),
            "source_type": ai_response.get("source_type", "generic")
        }
    
    async def _get_or_create_session(
        self, 
        user_id: int, 
        session_id: Optional[str] = None
    ) -> ChatSession:
        """Get existing session or create new one"""
        if session_id:
            session = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).first()
            
            if session:
                return session
        
        # Create new session
        new_session_id = str(uuid.uuid4())
        session = ChatSession(
            user_id=user_id,
            session_id=new_session_id,
            is_active=True
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(
            "New chat session created",
            user_id=user_id,
            session_id=new_session_id
        )
        
        return session
    
    def _save_message(
        self,
        session_id: int,
        role: str,
        content: str,
        model_used: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        sources_used: Optional[List[Dict[str, Any]]] = None,
        confidence_score: Optional[str] = None
    ) -> ChatMessage:
        """Save a chat message"""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            model_used=model_used,
            response_time_ms=response_time_ms,
            tokens_used=tokens_used,
            sources_used=sources_used,
            confidence_score=confidence_score
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    async def _generate_ai_response(
        self,
        user_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate AI response using RAG"""
        try:
            # Search for relevant chunks using workspace_id when available, else fallback to user_id
            workspace_id = str(user_id)
            if context and isinstance(context, dict) and context.get("workspace_id"):
                workspace_id = str(context.get("workspace_id"))
            similar_chunks = await self.vector_service.search_similar_chunks(
                query=message,
                workspace_id=workspace_id,
                limit=5
            )
            
            # Prepare context for AI
            has_docs = bool(similar_chunks)
            if has_docs:
                context_text = self._prepare_context(similar_chunks)
                source_type = "document"
            else:
                # Fallback to generic customer service context
                context_text = support_context_service.get_generic_customer_service_context(workspace_id)
                source_type = "generic"
            
            # Generate response using Gemini
            # Determine tone preset from workspace settings if available
            tone = None
            try:
                if context and isinstance(context, dict):
                    tone = context.get("tone")  # allow upstream to provide tone
            except Exception:
                tone = None

            response = await self.gemini_service.generate_response(
                user_message=message,
                context=context_text,
                sources=similar_chunks if has_docs else [],
                tone=tone,
                source_type=source_type
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "AI response generation failed",
                error=str(e),
                user_id=user_id,
                message=message[:100]
            )
            
            # Return fallback response
            return {
                "content": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
                "model_used": "fallback",
                "confidence_score": "low",
                "sources_used": []
            }
    
    def _prepare_context(self, similar_chunks: List[Dict[str, Any]]) -> str:
        """Prepare context text from similar chunks"""
        if not similar_chunks:
            return ""
        
        context_parts = []
        for chunk in similar_chunks:
            content = chunk["content"]
            metadata = chunk["metadata"]
            
            # Add source information
            source_info = ""
            if metadata.get("section_title"):
                source_info = f"From: {metadata['section_title']}"
            elif metadata.get("document_id"):
                source_info = f"From document {metadata['document_id']}"
            
            if source_info:
                context_parts.append(f"{source_info}\n{content}")
            else:
                context_parts.append(content)
        
        return "\n\n".join(context_parts)
    
    def get_user_sessions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        active_only: bool = False
    ) -> List[ChatSession]:
        """Get user's chat sessions"""
        query = self.db.query(ChatSession).filter(ChatSession.user_id == user_id)
        
        if active_only:
            query = query.filter(ChatSession.is_active == True)
        
        return query.order_by(ChatSession.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_session_by_id(self, session_id: str, user_id: int) -> Optional[ChatSession]:
        """Get chat session by ID"""
        return self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id
        ).first()
    
    def end_session(self, session_id: str, user_id: int) -> bool:
        """End a chat session"""
        session = self.get_session_by_id(session_id, user_id)
        if not session:
            return False
        
        session.is_active = False
        session.ended_at = func.now()
        self.db.commit()
        
        return True
    
    def delete_session(self, session_id: str, user_id: int) -> bool:
        """Delete a chat session and all messages"""
        session = self.get_session_by_id(session_id, user_id)
        if not session:
            return False
        
        try:
            # Delete all messages first (cascade should handle this)
            self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).delete()
            
            # Delete session
            self.db.delete(session)
            self.db.commit()
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete chat session",
                error=str(e),
                session_id=session_id,
                user_id=user_id
            )
            self.db.rollback()
            return False
    
    def flag_message(
        self,
        session_id: str,
        message_id: int,
        user_id: int,
        reason: str
    ) -> bool:
        """Flag a message for review"""
        session = self.get_session_by_id(session_id, user_id)
        if not session:
            return False
        
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.session_id == session.id
        ).first()
        
        if not message:
            return False
        
        message.is_flagged = True
        message.flag_reason = reason
        self.db.commit()
        
        return True
