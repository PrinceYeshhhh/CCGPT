"""
WebSocket security service for authentication and rate limiting
"""

import asyncio
import time
from typing import Dict, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from app.core.database import redis_manager
from app.services.auth import AuthService
from app.services.embed_service import EmbedService
from app.core.database import WriteSessionLocal as SessionLocal
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class WebSocketSecurityService:
    """Security service for WebSocket connections"""
    
    def __init__(self):
        self.redis_client = redis_manager.get_client()
        self.connection_limits = {
            "per_user": 5,  # Max 5 connections per user
            "per_ip": 10,   # Max 10 connections per IP
            "global": 1000  # Max 1000 total connections
        }
        self.rate_limits = {
            "messages_per_minute": 60,
            "messages_per_hour": 1000
        }
        self.active_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.connection_metadata: Dict[str, Dict] = {}  # connection_id -> metadata
    
    async def authenticate_connection(
        self, 
        websocket: WebSocket, 
        token: Optional[str] = None,
        client_api_key: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """Authenticate WebSocket connection"""
        try:
            # Optional origin check for embed usage when CORS is restricted
            try:
                origin = websocket.headers.get('origin') or websocket.headers.get('Origin')
                allowed = getattr(settings, 'CORS_ORIGINS', ["*"])
                if allowed and isinstance(allowed, list) and "*" not in allowed and origin:
                    if origin not in allowed:
                        logger.warning("WebSocket origin rejected", origin=origin)
                        return None
            except Exception:
                # Fail open to avoid breaking behavior in permissive environments
                pass
            if token:
                # JWT token authentication (dashboard users)
                auth_service = AuthService(db=None)
                payload = auth_service.verify_token(token, "access")
                if not payload or payload.get("sub") is None:
                    return None
                
                # Get user info from token
                db = SessionLocal()
                try:
                    from app.models.user import User
                    user = db.query(User).filter(User.email == payload.get("sub")).first()
                    if not user:
                        return None
                    
                    return {
                        "user_id": str(user.id),
                        "workspace_id": str(user.workspace_id),
                        "auth_type": "jwt"
                    }
                finally:
                    db.close()
            
            elif client_api_key:
                # API key authentication (embed widget)
                db = SessionLocal()
                try:
                    embed_service = EmbedService(db)
                    embed_code = embed_service.get_embed_code_by_api_key(client_api_key)
                    if not embed_code or not embed_code.is_active:
                        return None
                    
                    return {
                        "user_id": str(embed_code.user_id),
                        "workspace_id": str(embed_code.workspace_id),
                        "embed_code_id": str(embed_code.id),
                        "auth_type": "api_key"
                    }
                finally:
                    db.close()
            
            return None
            
        except Exception as e:
            logger.error("WebSocket authentication failed", error=str(e))
            return None
    
    async def check_connection_limits(self, user_id: str, client_ip: str) -> bool:
        """Check if connection limits are exceeded"""
        try:
            # Check per-user limit
            user_connections = self.active_connections.get(user_id, set())
            if len(user_connections) >= self.connection_limits["per_user"]:
                logger.warning("User connection limit exceeded", user_id=user_id)
                return False
            
            # Check per-IP limit
            ip_key = f"ws_connections:ip:{client_ip}"
            ip_count = self.redis_client.get(ip_key)
            if ip_count and int(ip_count) >= self.connection_limits["per_ip"]:
                logger.warning("IP connection limit exceeded", ip=client_ip)
                return False
            
            # Check global limit
            global_key = "ws_connections:global"
            global_count = self.redis_client.get(global_key)
            if global_count and int(global_count) >= self.connection_limits["global"]:
                logger.warning("Global connection limit exceeded")
                return False
            
            return True
            
        except Exception as e:
            logger.error("Connection limit check failed", error=str(e))
            return False
    
    async def register_connection(
        self, 
        connection_id: str, 
        user_id: str, 
        client_ip: str,
        metadata: Dict
    ) -> bool:
        """Register a new WebSocket connection"""
        try:
            # Add to user connections
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(connection_id)
            
            # Store connection metadata
            self.connection_metadata[connection_id] = {
                "user_id": user_id,
                "client_ip": client_ip,
                "connected_at": time.time(),
                **metadata
            }
            
            # Update Redis counters
            ip_key = f"ws_connections:ip:{client_ip}"
            global_key = "ws_connections:global"
            
            self.redis_client.incr(ip_key)
            self.redis_client.expire(ip_key, 3600)  # 1 hour
            
            self.redis_client.incr(global_key)
            self.redis_client.expire(global_key, 3600)  # 1 hour
            
            logger.info("WebSocket connection registered", 
                       connection_id=connection_id, user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to register connection", error=str(e))
            return False
    
    async def unregister_connection(self, connection_id: str) -> bool:
        """Unregister a WebSocket connection"""
        try:
            metadata = self.connection_metadata.get(connection_id)
            if not metadata:
                return False
            
            user_id = metadata["user_id"]
            client_ip = metadata["client_ip"]
            
            # Remove from user connections
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(connection_id)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # Remove metadata
            del self.connection_metadata[connection_id]
            
            # Update Redis counters
            ip_key = f"ws_connections:ip:{client_ip}"
            global_key = "ws_connections:global"
            
            self.redis_client.decr(ip_key)
            self.redis_client.decr(global_key)
            
            logger.info("WebSocket connection unregistered", 
                       connection_id=connection_id, user_id=user_id)
            return True
            
        except Exception as e:
            logger.error("Failed to unregister connection", error=str(e))
            return False
    
    async def check_message_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded message rate limits"""
        try:
            # Per-minute rate limit
            minute_key = f"ws_messages:minute:{user_id}:{int(time.time() // 60)}"
            minute_count = self.redis_client.get(minute_key)
            if minute_count and int(minute_count) >= self.rate_limits["messages_per_minute"]:
                return False
            
            # Per-hour rate limit
            hour_key = f"ws_messages:hour:{user_id}:{int(time.time() // 3600)}"
            hour_count = self.redis_client.get(hour_key)
            if hour_count and int(hour_count) >= self.rate_limits["messages_per_hour"]:
                return False
            
            return True
            
        except Exception as e:
            logger.error("Message rate limit check failed", error=str(e))
            return True  # Fail open
    
    async def record_message(self, user_id: str) -> None:
        """Record a message for rate limiting"""
        try:
            current_time = time.time()
            
            # Record per-minute
            minute_key = f"ws_messages:minute:{user_id}:{int(current_time // 60)}"
            self.redis_client.incr(minute_key)
            self.redis_client.expire(minute_key, 120)  # 2 minutes
            
            # Record per-hour
            hour_key = f"ws_messages:hour:{user_id}:{int(current_time // 3600)}"
            self.redis_client.incr(hour_key)
            self.redis_client.expire(hour_key, 7200)  # 2 hours
            
        except Exception as e:
            logger.error("Failed to record message", error=str(e))
    
    def validate_message(self, message: dict) -> bool:
        """Validate WebSocket message content"""
        try:
            if not isinstance(message, dict):
                return False
            
            # Check required fields
            if "type" not in message:
                return False
            
            # Validate message type
            allowed_types = ["chat", "ping", "pong", "typing", "stop_typing"]
            if message["type"] not in allowed_types:
                return False
            
            # Validate message content
            if message["type"] == "chat" and "content" in message:
                content = message["content"]
                if not isinstance(content, str) or len(content) > 1000:
                    return False
                
                # Check for dangerous content
                dangerous_patterns = ["<script", "javascript:", "eval("]
                content_lower = content.lower()
                for pattern in dangerous_patterns:
                    if pattern in content_lower:
                        return False
            
            return True
            
        except Exception as e:
            logger.error("Message validation failed", error=str(e))
            return False
    
    def get_connection_stats(self) -> Dict:
        """Get WebSocket connection statistics"""
        try:
            total_connections = sum(len(connections) for connections in self.active_connections.values())
            
            return {
                "total_connections": total_connections,
                "unique_users": len(self.active_connections),
                "connection_metadata": len(self.connection_metadata)
            }
        except Exception as e:
            logger.error("Failed to get connection stats", error=str(e))
            return {"error": "Failed to get stats"}


# Global instance
websocket_security_service = WebSocketSecurityService()
