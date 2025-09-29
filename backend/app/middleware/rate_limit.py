"""
Redis-backed rate limiting middleware
"""

import redis
import time
import json
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
import asyncio
from datetime import datetime, timedelta

from app.core.config import settings
from app.utils.logger import get_logger, log_security_event
from app.services.rate_limiting import rate_limiting_service

logger = get_logger(__name__)

class RateLimiter:
    """Redis-backed rate limiter with sliding window algorithm"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.workspace_limit = int(settings.RATE_LIMIT_WORKSPACE_PER_MIN)
        self.embed_limit = int(settings.RATE_LIMIT_EMBED_PER_MIN)
        self.window_size = 60  # 60 seconds
    
    def _get_key(self, identifier: str, limit_type: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"ratelimit:{limit_type}:{identifier}"
    
    def _get_sliding_window_key(self, identifier: str, limit_type: str) -> str:
        """Generate sliding window key"""
        return f"ratelimit:window:{limit_type}:{identifier}"
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        limit_type: str, 
        limit: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is within rate limit using sliding window algorithm
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        if limit is None:
            limit = self.workspace_limit if limit_type == "workspace" else self.embed_limit
        
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Use sliding window with sorted sets
        key = self._get_sliding_window_key(identifier, limit_type)
        
        try:
            # Remove expired entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = self.redis_client.zcard(key)
            
            if current_count >= limit:
                # Rate limit exceeded
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    oldest_time = oldest_request[0][1]
                    retry_after = int(oldest_time + self.window_size - current_time)
                else:
                    retry_after = self.window_size
                
                rate_limit_info = {
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": current_time + retry_after,
                    "retry_after": retry_after
                }
                
                # Log rate limit hit
                log_security_event(
                    "rate_limit_exceeded",
                    severity="low",
                    workspace_id=identifier if limit_type == "workspace" else None,
                    limit_type=limit_type,
                    current_count=current_count,
                    limit=limit
                )
                
                return False, rate_limit_info
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, self.window_size)
            
            # Calculate remaining requests
            remaining = max(0, limit - current_count - 1)
            
            rate_limit_info = {
                "limit": limit,
                "remaining": remaining,
                "reset_time": current_time + self.window_size,
                "retry_after": 0
            }
            
            return True, rate_limit_info
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True, {"limit": limit, "remaining": limit, "reset_time": 0, "retry_after": 0}
    
    async def get_rate_limit_info(self, identifier: str, limit_type: str) -> Dict[str, Any]:
        """Get current rate limit information without consuming a request"""
        limit = self.workspace_limit if limit_type == "workspace" else self.embed_limit
        current_time = time.time()
        window_start = current_time - self.window_size
        
        key = self._get_sliding_window_key(identifier, limit_type)
        
        try:
            # Remove expired entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = self.redis_client.zcard(key)
            remaining = max(0, limit - current_count)
            
            return {
                "limit": limit,
                "remaining": remaining,
                "reset_time": current_time + self.window_size,
                "retry_after": 0
            }
        except Exception as e:
            logger.error(f"Rate limit info check failed: {e}")
            return {"limit": limit, "remaining": limit, "reset_time": 0, "retry_after": 0}

# Global rate limiter instance
rate_limiter = RateLimiter()

class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip rate limiting for health checks and metrics
        if request.url.path in ["/health", "/ready", "/metrics"]:
            await self.app(scope, receive, send)
            return
        
        # Determine rate limit type and identifier
        limit_type, identifier = self._get_rate_limit_info(request)
        
        if limit_type and identifier:
            # Use shared Redis-backed service for consistency across services
            is_allowed, info = await rate_limiting_service.check_rate_limit(
                identifier=f"{limit_type}:{identifier}",
                limit=settings.RATE_LIMIT_REQUESTS,
                window_seconds=settings.RATE_LIMIT_WINDOW
            )
            rate_limit_info = {
                "limit": info.get("limit", settings.RATE_LIMIT_REQUESTS),
                "remaining": info.get("remaining", 0),
                "reset_time": info.get("reset_time", 0).timestamp() if hasattr(info.get("reset_time"), "timestamp") else info.get("reset_time", 0),
                "retry_after": max(0, int(info.get("window_seconds", settings.RATE_LIMIT_WINDOW))) if not is_allowed else 0,
            }
            
            if not is_allowed:
                response = JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "code": "rate_limited",
                        "message": "Rate limit exceeded. Please try again later.",
                        "retry_after": rate_limit_info["retry_after"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                        "X-RateLimit-Reset": str(int(rate_limit_info["reset_time"])),
                        "Retry-After": str(rate_limit_info["retry_after"])
                    }
                )
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
    
    def _get_rate_limit_info(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        """Determine rate limit type and identifier from request"""
        
        # Check for workspace-based rate limiting
        if request.url.path.startswith("/api/v1/"):
            # Try to get workspace_id from headers or JWT
            workspace_id = request.headers.get("X-Workspace-ID")
            if workspace_id:
                return "workspace", workspace_id
            
            # For auth endpoints, use IP address
            if request.url.path.startswith("/api/v1/auth/"):
                client_ip = self._get_client_ip(request)
                return "workspace", client_ip
        
        # Check for embed-based rate limiting
        if request.url.path.startswith("/api/v1/embed/") and "widget" in request.url.path:
            embed_id = request.headers.get("X-Embed-ID")
            if embed_id:
                return "embed", embed_id
        
        return None, None
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

def create_rate_limit_dependency(limit_type: str):
    """Create a rate limit dependency for specific endpoints"""
    async def rate_limit_dependency(
        request: Request,
        workspace_id: Optional[str] = None,
        embed_id: Optional[str] = None
    ):
        identifier = None
        
        if limit_type == "workspace" and workspace_id:
            identifier = workspace_id
        elif limit_type == "embed" and embed_id:
            identifier = embed_id
        else:
            # Fallback to IP-based limiting
            client_ip = request.client.host if request.client else "unknown"
            identifier = client_ip
        
        if identifier:
            is_allowed, info = await rate_limiting_service.check_rate_limit(
                identifier=f"{limit_type}:{identifier}",
                limit=settings.RATE_LIMIT_REQUESTS,
                window_seconds=settings.RATE_LIMIT_WINDOW
            )
            rate_limit_info = {
                "limit": info.get("limit", settings.RATE_LIMIT_REQUESTS),
                "remaining": info.get("remaining", 0),
                "reset_time": info.get("reset_time", 0).timestamp() if hasattr(info.get("reset_time"), "timestamp") else info.get("reset_time", 0),
                "retry_after": max(0, int(info.get("window_seconds", settings.RATE_LIMIT_WINDOW))) if not is_allowed else 0,
            }
            
            if not is_allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "code": "rate_limited",
                        "message": "Rate limit exceeded. Please try again later.",
                        "retry_after": rate_limit_info["retry_after"]
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                        "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                        "X-RateLimit-Reset": str(int(rate_limit_info["reset_time"])),
                        "Retry-After": str(rate_limit_info["retry_after"])
                    }
                )
        
        return rate_limit_info
    
    return rate_limit_dependency

# Pre-configured dependencies
workspace_rate_limit = create_rate_limit_dependency("workspace")
embed_rate_limit = create_rate_limit_dependency("embed")

async def get_rate_limit_status(identifier: str, limit_type: str) -> Dict[str, Any]:
    """Get current rate limit status without consuming a request"""
    return await rate_limiter.get_rate_limit_info(identifier, limit_type)
