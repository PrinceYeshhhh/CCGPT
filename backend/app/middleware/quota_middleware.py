"""
Quota enforcement middleware for API endpoints
"""

from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.subscriptions import Subscription
from app.models.workspace import Workspace

logger = logging.getLogger(__name__)

class QuotaExceededException(HTTPException):
    """Exception raised when quota is exceeded"""
    def __init__(self, message: str = "Quota exceeded", quota_info: Optional[dict] = None):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "quota_exceeded",
                "message": message,
                "quota_info": quota_info or {}
            }
        )

async def check_quota(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Subscription:
    """
    Check if user's workspace has remaining quota for API calls.
    Raises QuotaExceededException if quota is exceeded.
    """
    
    # Get workspace subscription
    subscription = db.query(Subscription).filter(
        Subscription.workspace_id == current_user.workspace_id,
        Subscription.status.in_(['active', 'trialing'])
    ).first()
    
    if not subscription:
        # No active subscription - check if workspace has free tier
        workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
        if not workspace or workspace.plan == 'free':
            # Free tier - check against free tier limits
            free_quota = 100  # Free tier gets 100 queries
            # This would need to be tracked separately or in subscription table
            # For now, we'll allow free tier users
            logger.info(f"Free tier user {current_user.id} - allowing request")
            return None
        else:
            raise QuotaExceededException(
                "No active subscription found. Please subscribe to continue.",
                {"tier": "none", "status": "inactive"}
            )
    
    # Check if quota is exceeded
    if subscription.is_quota_exceeded:
        quota_info = {
            "tier": subscription.tier,
            "status": subscription.status,
            "quota_used": subscription.queries_this_period,
            "quota_limit": subscription.monthly_query_quota,
            "remaining": subscription.remaining_queries,
            "usage_percentage": subscription.quota_usage_percentage
        }
        
        logger.warning(f"Quota exceeded for workspace {current_user.workspace_id}: {quota_info}")
        
        raise QuotaExceededException(
            f"Your {subscription.tier} plan quota has been exceeded. Upgrade to continue.",
            quota_info
        )
    
    # Check if approaching quota limit (80% warning)
    if subscription.monthly_query_quota and subscription.quota_usage_percentage >= 80:
        logger.info(f"Workspace {current_user.workspace_id} approaching quota limit: {subscription.quota_usage_percentage:.1f}%")
    
    return subscription

async def increment_usage(
    subscription: Optional[Subscription] = Depends(check_quota),
    db: Session = Depends(get_db)
) -> bool:
    """
    Increment usage counter for the workspace.
    This should be called after successful API operations.
    """
    
    if not subscription:
        # Free tier - we could track usage separately or just allow
        logger.info("Free tier usage - not tracking")
        return True
    
    # Increment usage atomically
    try:
        if not subscription.increment_usage(1):
            # This shouldn't happen if check_quota passed, but just in case
            raise QuotaExceededException("Quota exceeded during usage increment")
        
        db.commit()
        logger.debug(f"Incremented usage for workspace {subscription.workspace_id}: {subscription.queries_this_period}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error incrementing usage: {e}")
        raise

def get_quota_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get quota information for the current workspace.
    Used for displaying quota status in UI.
    """
    
    subscription = db.query(Subscription).filter(
        Subscription.workspace_id == current_user.workspace_id,
        Subscription.status.in_(['active', 'trialing'])
    ).first()
    
    if not subscription:
        # Free tier
        return {
            "tier": "free",
            "status": "active",
            "quota_used": 0,  # Would need to track this separately
            "quota_limit": 100,
            "remaining": 100,
            "usage_percentage": 0.0,
            "is_unlimited": False
        }
    
    return {
        "tier": subscription.tier,
        "status": subscription.status,
        "quota_used": subscription.queries_this_period,
        "quota_limit": subscription.monthly_query_quota,
        "remaining": subscription.remaining_queries,
        "usage_percentage": subscription.quota_usage_percentage,
        "is_unlimited": subscription.monthly_query_quota is None,
        "period_start": subscription.period_start.isoformat() if subscription.period_start else None,
        "period_end": subscription.period_end.isoformat() if subscription.period_end else None,
        "next_billing_at": subscription.next_billing_at.isoformat() if subscription.next_billing_at else None
    }

# Redis-based quota tracking for high-volume scenarios
class RedisQuotaTracker:
    """
    Redis-based quota tracking for high-volume API calls.
    This reduces database load by maintaining counters in Redis
    and periodically syncing to the database.
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.sync_interval = 300  # 5 minutes
    
    def get_quota_key(self, workspace_id: str) -> str:
        """Get Redis key for workspace quota"""
        return f"quota:{workspace_id}"
    
    def get_usage_key(self, workspace_id: str) -> str:
        """Get Redis key for workspace usage"""
        return f"usage:{workspace_id}"
    
    async def check_quota_redis(self, workspace_id: str, quota_limit: int) -> bool:
        """Check quota using Redis counter"""
        usage_key = self.get_usage_key(workspace_id)
        current_usage = await self.redis.get(usage_key)
        
        if current_usage is None:
            current_usage = 0
        else:
            current_usage = int(current_usage)
        
        return current_usage < quota_limit
    
    async def increment_usage_redis(self, workspace_id: str) -> int:
        """Increment usage counter in Redis"""
        usage_key = self.get_usage_key(workspace_id)
        new_usage = await self.redis.incr(usage_key)
        
        # Set expiration to end of month (if not already set)
        if new_usage == 1:
            # Set expiration to end of current month
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
            ttl = int((next_month - now).total_seconds())
            await self.redis.expire(usage_key, ttl)
        
        return new_usage
    
    async def sync_to_database(self, workspace_id: str, db: Session):
        """Sync Redis usage counter to database"""
        usage_key = self.get_usage_key(workspace_id)
        redis_usage = await self.redis.get(usage_key)
        
        if redis_usage is not None:
            subscription = db.query(Subscription).filter(
                Subscription.workspace_id == workspace_id
            ).first()
            
            if subscription:
                subscription.queries_this_period = int(redis_usage)
                db.commit()
                logger.info(f"Synced Redis usage to DB for workspace {workspace_id}: {redis_usage}")
