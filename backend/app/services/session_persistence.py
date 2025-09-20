"""
Session persistence service using Redis for ephemeral session state
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class SessionPersistenceService:
    """Redis-based session persistence for ephemeral chat state"""
    
    def __init__(self):
        self.redis_client = None
        self.default_ttl = 86400  # 24 hours
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client for session persistence"""
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
            logger.info("Session persistence service initialized with Redis")
        except Exception as e:
            logger.error("Failed to initialize Redis for session persistence", error=str(e))
            self.redis_client = None
    
    async def store_session_state(
        self,
        session_id: str,
        state: Dict[str, Any],
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Store ephemeral session state in Redis
        
        Args:
            session_id: Session identifier
            state: Session state data
            ttl_seconds: Time to live in seconds (default: 24 hours)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl_seconds or self.default_ttl
            key = f"session_state:{session_id}"
            
            # Add metadata
            state_with_metadata = {
                **state,
                "updated_at": datetime.now().isoformat(),
                "ttl": ttl
            }
            
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(state_with_metadata, default=str)
            )
            
            logger.info(
                "Session state stored",
                session_id=session_id,
                ttl_seconds=ttl
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to store session state",
                error=str(e),
                session_id=session_id
            )
            return False
    
    async def get_session_state(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve session state from Redis
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session state data or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            key = f"session_state:{session_id}"
            data = await self.redis_client.get(key)
            
            if data:
                state = json.loads(data)
                logger.info(
                    "Session state retrieved",
                    session_id=session_id
                )
                return state
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get session state",
                error=str(e),
                session_id=session_id
            )
            return None
    
    async def update_session_activity(
        self,
        session_id: str,
        activity_type: str = "message",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update session activity timestamp and metadata
        
        Args:
            session_id: Session identifier
            activity_type: Type of activity (message, typing, etc.)
            metadata: Additional activity metadata
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Get current state
            current_state = await self.get_session_state(session_id)
            if not current_state:
                current_state = {}
            
            # Update activity
            current_state["last_activity"] = {
                "type": activity_type,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store updated state
            return await self.store_session_state(session_id, current_state)
            
        except Exception as e:
            logger.error(
                "Failed to update session activity",
                error=str(e),
                session_id=session_id
            )
            return False
    
    async def store_streaming_message(
        self,
        session_id: str,
        message_id: str,
        content: str,
        is_complete: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store streaming message content in Redis
        
        Args:
            session_id: Session identifier
            message_id: Message identifier
            content: Message content
            is_complete: Whether the message is complete
            metadata: Additional message metadata
        
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"streaming_message:{session_id}:{message_id}"
            
            message_data = {
                "content": content,
                "is_complete": is_complete,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store with shorter TTL for streaming messages
            ttl = 3600  # 1 hour
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(message_data, default=str)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to store streaming message",
                error=str(e),
                session_id=session_id,
                message_id=message_id
            )
            return False
    
    async def get_streaming_message(
        self,
        session_id: str,
        message_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve streaming message from Redis
        
        Args:
            session_id: Session identifier
            message_id: Message identifier
        
        Returns:
            Message data or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            key = f"streaming_message:{session_id}:{message_id}"
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to get streaming message",
                error=str(e),
                session_id=session_id,
                message_id=message_id
            )
            return None
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (called by background task)
        
        Returns:
            Number of sessions cleaned up
        """
        if not self.redis_client:
            return 0
        
        try:
            # Get all session state keys
            pattern = "session_state:*"
            keys = await self.redis_client.keys(pattern)
            
            cleaned_count = 0
            for key in keys:
                # Check TTL
                ttl = await self.redis_client.ttl(key)
                if ttl <= 0:
                    await self.redis_client.delete(key)
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(
                    "Cleaned up expired sessions",
                    count=cleaned_count
                )
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired sessions", error=str(e))
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session persistence statistics"""
        if not self.redis_client:
            return {"enabled": False}
        
        try:
            # Count session states
            session_keys = await self.redis_client.keys("session_state:*")
            streaming_keys = await self.redis_client.keys("streaming_message:*")
            
            return {
                "enabled": True,
                "active_sessions": len(session_keys),
                "streaming_messages": len(streaming_keys),
                "default_ttl_seconds": self.default_ttl
            }
            
        except Exception as e:
            logger.error("Failed to get session stats", error=str(e))
            return {"enabled": False, "error": str(e)}
    
    async def delete_session_state(self, session_id: str) -> bool:
        """Delete session state from Redis"""
        if not self.redis_client:
            return False
        
        try:
            # Delete session state
            session_key = f"session_state:{session_id}"
            await self.redis_client.delete(session_key)
            
            # Delete any streaming messages for this session
            pattern = f"streaming_message:{session_id}:*"
            streaming_keys = await self.redis_client.keys(pattern)
            if streaming_keys:
                await self.redis_client.delete(*streaming_keys)
            
            logger.info("Session state deleted", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete session state",
                error=str(e),
                session_id=session_id
            )
            return False


# Global instance
session_persistence_service = SessionPersistenceService()
