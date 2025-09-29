"""
Rate limiting middleware for dashboard endpoints
"""

import time
import redis
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    async def check_rate_limit(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int,
        identifier: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limit
        
        Args:
            key: Rate limit key (e.g., 'dashboard_api', 'analytics_export')
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            identifier: Additional identifier (e.g., user_id, ip_address)
        
        Returns:
            Dict with rate limit status and remaining requests
        """
        try:
            # Create full key with identifier
            full_key = f"rate_limit:{key}:{identifier}" if identifier else f"rate_limit:{key}"
            
            # Get current time
            current_time = int(time.time())
            window_start = current_time - window_seconds
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(full_key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(full_key)
            
            # Add current request
            pipe.zadd(full_key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(full_key, window_seconds)
            
            # Execute pipeline
            results = pipe.execute()
            
            current_count = results[1]
            
            # Check if limit exceeded
            if current_count >= limit:
                # Get oldest request time
                oldest_requests = self.redis_client.zrange(full_key, 0, 0, withscores=True)
                reset_time = int(oldest_requests[0][1]) + window_seconds if oldest_requests else current_time + window_seconds
                
                return {
                    "allowed": False,
                    "limit": limit,
                    "remaining": 0,
                    "reset_time": reset_time,
                    "retry_after": reset_time - current_time
                }
            
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit - current_count - 1,
                "reset_time": current_time + window_seconds,
                "retry_after": 0
            }
            
        except Exception as e:
            logger.error("Rate limiting error", error=str(e), key=key)
            # Fail open - allow request if Redis is down
            return {
                "allowed": True,
                "limit": limit,
                "remaining": limit,
                "reset_time": int(time.time()) + window_seconds,
                "retry_after": 0
            }


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit decorators for different endpoint types
def dashboard_rate_limit(limit: int = 60, window_seconds: int = 60):
    """Rate limit for dashboard API calls"""
    async def decorator(request: Request, call_next):
        # Get user identifier (user_id or IP)
        user_id = getattr(request.state, 'user_id', None)
        client_ip = request.client.host if request.client else 'unknown'
        identifier = str(user_id) if user_id else client_ip
        
        # Check rate limit
        rate_limit_result = await rate_limiter.check_rate_limit(
            key="dashboard_api",
            limit=limit,
            window_seconds=window_seconds,
            identifier=identifier
        )
        
        if not rate_limit_result["allowed"]:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": rate_limit_result["retry_after"],
                    "limit": rate_limit_result["limit"],
                    "remaining": rate_limit_result["remaining"]
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                    "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                    "X-RateLimit-Reset": str(rate_limit_result["reset_time"]),
                    "Retry-After": str(rate_limit_result["retry_after"])
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
        
        return response
    
    return decorator


def analytics_export_rate_limit(limit: int = 10, window_seconds: int = 3600):
    """Rate limit for analytics export (more restrictive)"""
    async def decorator(request: Request, call_next):
        user_id = getattr(request.state, 'user_id', None)
        client_ip = request.client.host if request.client else 'unknown'
        identifier = str(user_id) if user_id else client_ip
        
        rate_limit_result = await rate_limiter.check_rate_limit(
            key="analytics_export",
            limit=limit,
            window_seconds=window_seconds,
            identifier=identifier
        )
        
        if not rate_limit_result["allowed"]:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Export rate limit exceeded. Please try again later.",
                    "retry_after": rate_limit_result["retry_after"],
                    "limit": rate_limit_result["limit"],
                    "remaining": rate_limit_result["remaining"]
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                    "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                    "X-RateLimit-Reset": str(rate_limit_result["reset_time"]),
                    "Retry-After": str(rate_limit_result["retry_after"])
                }
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
        
        return response
    
    return decorator


def performance_metrics_rate_limit(limit: int = 100, window_seconds: int = 60):
    """Rate limit for performance metrics collection"""
    async def decorator(request: Request, call_next):
        user_id = getattr(request.state, 'user_id', None)
        client_ip = request.client.host if request.client else 'unknown'
        identifier = str(user_id) if user_id else client_ip
        
        rate_limit_result = await rate_limiter.check_rate_limit(
            key="performance_metrics",
            limit=limit,
            window_seconds=window_seconds,
            identifier=identifier
        )
        
        if not rate_limit_result["allowed"]:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Performance metrics rate limit exceeded.",
                    "retry_after": rate_limit_result["retry_after"]
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                    "X-RateLimit-Remaining": str(rate_limit_result["remaining"]),
                    "X-RateLimit-Reset": str(rate_limit_result["reset_time"]),
                    "Retry-After": str(rate_limit_result["retry_after"])
                }
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_result["reset_time"])
        
        return response
    
    return decorator
