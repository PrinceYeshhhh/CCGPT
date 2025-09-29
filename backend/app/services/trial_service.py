"""
Trial management service for handling trial expiration and enforcement
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import structlog

from app.models.subscriptions import Subscription
from app.models.workspace import Workspace
from app.core.database import get_db

logger = structlog.get_logger()


class TrialService:
    """Service for managing trial periods and expiration"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_trial_expiration(self, workspace_id: str) -> Dict[str, Any]:
        """Check if trial has expired for a workspace"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.workspace_id == workspace_id,
                Subscription.tier == 'free_trial'
            ).first()
            
            if not subscription:
                return {
                    "is_trial": False,
                    "is_expired": False,
                    "days_remaining": 0,
                    "message": "No trial found"
                }
            
            now = datetime.utcnow()
            is_expired = False
            days_remaining = 0
            
            if subscription.period_end:
                if now >= subscription.period_end:
                    is_expired = True
                    # Update subscription status to expired
                    subscription.status = 'expired'
                    self.db.commit()
                else:
                    days_remaining = (subscription.period_end - now).days
            
            return {
                "is_trial": True,
                "is_expired": is_expired,
                "days_remaining": days_remaining,
                "trial_end": subscription.period_end.isoformat() if subscription.period_end else None,
                "message": f"Trial expired" if is_expired else f"Trial active, {days_remaining} days remaining"
            }
            
        except Exception as e:
            logger.error(f"Error checking trial expiration: {e}")
            return {
                "is_trial": False,
                "is_expired": False,
                "days_remaining": 0,
                "message": "Error checking trial status"
            }
    
    def enforce_trial_limits(self, workspace_id: str) -> bool:
        """Enforce trial limits - return True if access should be allowed"""
        trial_status = self.check_trial_expiration(workspace_id)
        
        if trial_status["is_trial"] and trial_status["is_expired"]:
            logger.info(f"Trial expired for workspace {workspace_id}")
            return False
        
        return True
    
    def start_trial(self, workspace_id: str, user_id: str) -> Dict[str, Any]:
        """Start a 7-day free trial for a workspace"""
        try:
            # Check if trial already exists
            existing_trial = self.db.query(Subscription).filter(
                Subscription.workspace_id == workspace_id,
                Subscription.tier == 'free_trial'
            ).first()
            
            if existing_trial:
                return {
                    "success": False,
                    "message": "Trial already started for this workspace"
                }
            
            # Create new trial subscription
            trial_end = datetime.utcnow() + timedelta(days=7)
            trial_subscription = Subscription(
                workspace_id=workspace_id,
                user_id=user_id,
                tier='free_trial',
                status='trialing',
                monthly_query_quota=100,
                queries_this_period=0,
                period_start=datetime.utcnow(),
                period_end=trial_end,
                next_billing_at=trial_end
            )
            
            self.db.add(trial_subscription)
            self.db.commit()
            
            logger.info(f"Trial started for workspace {workspace_id}, expires {trial_end}")
            
            return {
                "success": True,
                "message": "Trial started successfully",
                "trial_end": trial_end.isoformat(),
                "days_remaining": 7
            }
            
        except Exception as e:
            logger.error(f"Error starting trial: {e}")
            self.db.rollback()
            return {
                "success": False,
                "message": "Failed to start trial"
            }
    
    def get_trial_info(self, workspace_id: str) -> Dict[str, Any]:
        """Get detailed trial information for a workspace"""
        trial_status = self.check_trial_expiration(workspace_id)
        
        if not trial_status["is_trial"]:
            return trial_status
        
        # Get usage information
        subscription = self.db.query(Subscription).filter(
            Subscription.workspace_id == workspace_id,
            Subscription.tier == 'free_trial'
        ).first()
        
        if not subscription:
            return trial_status
        
        return {
            **trial_status,
            "queries_used": subscription.queries_this_period,
            "queries_limit": subscription.monthly_query_quota,
            "queries_remaining": subscription.monthly_query_quota - subscription.queries_this_period,
            "usage_percentage": (subscription.queries_this_period / subscription.monthly_query_quota) * 100 if subscription.monthly_query_quota > 0 else 0
        }
