"""
Token budget tracking service for workspace-level usage control
"""

import asyncio
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import redis.asyncio as aioredis
import structlog

from app.core.config import settings
from app.models.chat import ChatMessage

logger = structlog.get_logger()


class TokenBudgetService:
    """Token budget tracking service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client for token budget caching"""
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
            logger.info("Token budget service initialized with Redis")
        except Exception as e:
            logger.error("Failed to initialize Redis for token budget", error=str(e))
            self.redis_client = None
    
    async def check_token_budget(
        self,
        workspace_id: str,
        requested_tokens: int,
        daily_limit: int = 10000,
        monthly_limit: int = 100000
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if workspace has sufficient token budget
        
        Args:
            workspace_id: Workspace identifier
            requested_tokens: Number of tokens requested
            daily_limit: Daily token limit
            monthly_limit: Monthly token limit
        
        Returns:
            Tuple of (is_within_budget, budget_info)
        """
        try:
            # Get current usage
            daily_used = await self._get_daily_usage(workspace_id)
            monthly_used = await self._get_monthly_usage(workspace_id)
            
            # Check limits
            daily_remaining = daily_limit - daily_used
            monthly_remaining = monthly_limit - monthly_used
            
            within_daily = daily_remaining >= requested_tokens
            within_monthly = monthly_remaining >= requested_tokens
            
            is_within_budget = within_daily and within_monthly
            
            # Calculate reset times
            now = datetime.now()
            daily_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            monthly_reset = (now + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            budget_info = {
                "daily_limit": daily_limit,
                "daily_used": daily_used,
                "daily_remaining": daily_remaining,
                "monthly_limit": monthly_limit,
                "monthly_used": monthly_used,
                "monthly_remaining": monthly_remaining,
                "requested_tokens": requested_tokens,
                "within_daily_limit": within_daily,
                "within_monthly_limit": within_monthly,
                "reset_daily_at": daily_reset,
                "reset_monthly_at": monthly_reset
            }
            
            return is_within_budget, budget_info
            
        except Exception as e:
            logger.error(
                "Token budget check failed",
                error=str(e),
                workspace_id=workspace_id
            )
            # On error, allow the request
            return True, {
                "daily_limit": daily_limit,
                "daily_used": 0,
                "daily_remaining": daily_limit,
                "monthly_limit": monthly_limit,
                "monthly_used": 0,
                "monthly_remaining": monthly_limit,
                "requested_tokens": requested_tokens,
                "within_daily_limit": True,
                "within_monthly_limit": True,
                "reset_daily_at": datetime.now() + timedelta(days=1),
                "reset_monthly_at": datetime.now() + timedelta(days=32)
            }
    
    async def consume_tokens(
        self,
        workspace_id: str,
        tokens_used: int,
        model_used: str = "gemini-pro"
    ) -> bool:
        """
        Consume tokens for workspace
        
        Args:
            workspace_id: Workspace identifier
            tokens_used: Number of tokens consumed
            model_used: Model used for generation
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update Redis cache
            if self.redis_client:
                today = datetime.now().strftime("%Y-%m-%d")
                this_month = datetime.now().strftime("%Y-%m")
                
                # Update daily usage
                daily_key = f"token_budget:{workspace_id}:daily:{today}"
                await self.redis_client.incrby(daily_key, tokens_used)
                await self.redis_client.expire(daily_key, 86400 * 2)  # Expire in 2 days
                
                # Update monthly usage
                monthly_key = f"token_budget:{workspace_id}:monthly:{this_month}"
                await self.redis_client.incrby(monthly_key, tokens_used)
                await self.redis_client.expire(monthly_key, 86400 * 35)  # Expire in 35 days
            
            logger.info(
                "Tokens consumed",
                workspace_id=workspace_id,
                tokens_used=tokens_used,
                model_used=model_used
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to consume tokens",
                error=str(e),
                workspace_id=workspace_id,
                tokens_used=tokens_used
            )
            return False
    
    async def _get_daily_usage(self, workspace_id: str) -> int:
        """Get daily token usage for workspace"""
        try:
            # Try Redis first
            if self.redis_client:
                today = datetime.now().strftime("%Y-%m-%d")
                daily_key = f"token_budget:{workspace_id}:daily:{today}"
                cached_usage = await self.redis_client.get(daily_key)
                
                if cached_usage:
                    return int(cached_usage)
            
            # Fallback to database
            today = datetime.now().date()
            usage = self.db.query(func.sum(ChatMessage.tokens_used)).join(
                ChatMessage.session_id == ChatMessage.session_id
            ).filter(
                and_(
                    ChatMessage.created_at >= today,
                    ChatMessage.created_at < today + timedelta(days=1),
                    ChatMessage.tokens_used.isnot(None)
                )
            ).scalar()
            
            return int(usage) if usage else 0
            
        except Exception as e:
            logger.error("Failed to get daily usage", error=str(e), workspace_id=workspace_id)
            return 0
    
    async def _get_monthly_usage(self, workspace_id: str) -> int:
        """Get monthly token usage for workspace"""
        try:
            # Try Redis first
            if self.redis_client:
                this_month = datetime.now().strftime("%Y-%m")
                monthly_key = f"token_budget:{workspace_id}:monthly:{this_month}"
                cached_usage = await self.redis_client.get(monthly_key)
                
                if cached_usage:
                    return int(cached_usage)
            
            # Fallback to database
            now = datetime.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = (month_start + timedelta(days=32)).replace(day=1)
            
            usage = self.db.query(func.sum(ChatMessage.tokens_used)).join(
                ChatMessage.session_id == ChatMessage.session_id
            ).filter(
                and_(
                    ChatMessage.created_at >= month_start,
                    ChatMessage.created_at < next_month,
                    ChatMessage.tokens_used.isnot(None)
                )
            ).scalar()
            
            return int(usage) if usage else 0
            
        except Exception as e:
            logger.error("Failed to get monthly usage", error=str(e), workspace_id=workspace_id)
            return 0
    
    async def get_budget_info(self, workspace_id: str) -> Dict[str, Any]:
        """Get complete budget information for workspace"""
        try:
            daily_used = await self._get_daily_usage(workspace_id)
            monthly_used = await self._get_monthly_usage(workspace_id)
            
            now = datetime.now()
            daily_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            monthly_reset = (now + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            return {
                "daily_used": daily_used,
                "monthly_used": monthly_used,
                "reset_daily_at": daily_reset,
                "reset_monthly_at": monthly_reset
            }
            
        except Exception as e:
            logger.error("Failed to get budget info", error=str(e), workspace_id=workspace_id)
            return {
                "daily_used": 0,
                "monthly_used": 0,
                "reset_daily_at": datetime.now() + timedelta(days=1),
                "reset_monthly_at": datetime.now() + timedelta(days=32)
            }
    
    async def reset_budget(self, workspace_id: str) -> bool:
        """Reset token budget for workspace"""
        try:
            if self.redis_client:
                # Clear all budget keys for this workspace
                pattern = f"token_budget:{workspace_id}:*"
                keys = await self.redis_client.keys(pattern)
                
                if keys:
                    await self.redis_client.delete(*keys)
                    logger.info("Token budget reset", workspace_id=workspace_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to reset budget", error=str(e), workspace_id=workspace_id)
            return False
