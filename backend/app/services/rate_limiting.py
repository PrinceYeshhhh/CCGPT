"""
Rate limiting service for API endpoints
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
import redis.asyncio as aioredis
from datetime import datetime, timedelta
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RateLimitingService:
    """Rate limiting service using Redis"""
    
    def __init__(self):
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client for rate limiting"""
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
            logger.info("Rate limiting service initialized with Redis")
        except Exception as e:
            logger.error("Failed to initialize Redis for rate limiting", error=str(e))
            # Continue without rate limiting
            self.redis_client = None
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int = 60,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (workspace_id, user_id, etc.)
            limit: Maximum requests per window
            window_seconds: Time window in seconds
        
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        if not self.redis_client:
            # If Redis is not available, allow all requests
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset_time": datetime.now() + timedelta(seconds=window_seconds),
                "window_seconds": window_seconds
            }
        
        try:
            current_time = int(time.time())
            window_start = current_time - (current_time % window_seconds)
            key = f"rate_limit:{identifier}:{window_start}"
            
            # Get current count
            current_count = await self.redis_client.get(key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= limit:
                # Rate limit exceeded
                reset_time = datetime.fromtimestamp(window_start + window_seconds)
                return False, {
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": reset_time,
                    "window_seconds": window_seconds
                }
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            await pipe.execute()
            
            remaining = limit - current_count - 1
            reset_time = datetime.fromtimestamp(window_start + window_seconds)
            
            return True, {
                "limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "window_seconds": window_seconds
            }
            
        except Exception as e:
            logger.error(
                "Rate limit check failed",
                error=str(e),
                identifier=identifier
            )
            # On error, allow the request
            return True, {
                "limit": limit,
                "remaining": limit,
                "reset_time": datetime.now() + timedelta(seconds=window_seconds),
                "window_seconds": window_seconds
            }
    
    async def check_workspace_rate_limit(
        self,
        workspace_id: str,
        limit: int = 60,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, any]]:
        """Check rate limit for workspace"""
        return await self.check_rate_limit(
            identifier=f"workspace:{workspace_id}",
            limit=limit,
            window_seconds=window_seconds
        )
    
    async def check_user_rate_limit(
        self,
        user_id: int,
        limit: int = 100,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, any]]:
        """Check rate limit for user"""
        return await self.check_rate_limit(
            identifier=f"user:{user_id}",
            limit=limit,
            window_seconds=window_seconds
        )
    
    async def check_ip_rate_limit(
        self,
        ip_address: str,
        limit: int = 30,
        window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, any]]:
        """Check rate limit for IP address"""
        return await self.check_rate_limit(
            identifier=f"ip:{ip_address}",
            limit=limit,
            window_seconds=window_seconds
        )
    
    async def reset_rate_limit(self, identifier: str) -> bool:
        """Reset rate limit for identifier"""
        if not self.redis_client:
            return True
        
        try:
            # Get all keys for this identifier
            pattern = f"rate_limit:{identifier}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.info("Rate limit reset", identifier=identifier)
            
            return True
            
        except Exception as e:
            logger.error("Failed to reset rate limit", error=str(e), identifier=identifier)
            return False
    
    async def get_rate_limit_stats(self, identifier: str) -> Dict[str, any]:
        """Get rate limit statistics for identifier"""
        if not self.redis_client:
            return {"enabled": False}
        
        try:
            pattern = f"rate_limit:{identifier}:*"
            keys = await self.redis_client.keys(pattern)
            
            total_requests = 0
            for key in keys:
                count = await self.redis_client.get(key)
                total_requests += int(count) if count else 0
            
            return {
                "enabled": True,
                "total_requests": total_requests,
                "active_windows": len(keys)
            }
            
        except Exception as e:
            logger.error("Failed to get rate limit stats", error=str(e), identifier=identifier)
            return {"enabled": False, "error": str(e)}


# Global instance
rate_limiting_service = RateLimitingService()
