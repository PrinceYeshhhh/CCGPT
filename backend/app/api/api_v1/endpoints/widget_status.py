"""
Widget status endpoints for checking subscription and widget behavior
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog

from app.core.database import get_db
from app.models.user import User
from app.models.subscriptions import Subscription
from app.api.api_v1.dependencies import get_current_user

logger = structlog.get_logger()
router = APIRouter()


@router.get("/subscription-status")
async def get_widget_subscription_status(
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """Get subscription status for widget behavior control"""
    try:
        # Get subscription for the workspace
        subscription = db.query(Subscription).filter(
            Subscription.workspace_id == workspace_id,
            Subscription.status.in_(['active', 'trialing'])
        ).first()
        
        if not subscription:
            return {
                "is_active": False,
                "plan": "free",
                "status": "inactive",
                "message": "No active subscription found"
            }
        
        # Check if subscription is active
        is_active = subscription.status in ['active', 'trialing']
        
        return {
            "is_active": is_active,
            "plan": subscription.tier,
            "status": subscription.status,
            "is_trial": subscription.tier == 'free_trial',
            "trial_end": subscription.period_end.isoformat() if subscription.period_end else None,
            "message": "Widget is active" if is_active else "Widget is inactive"
        }
        
    except Exception as e:
        logger.error(f"Error checking widget subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check widget subscription status"
        )


@router.get("/embed-status/{embed_id}")
async def get_embed_widget_status(
    embed_id: str,
    db: Session = Depends(get_db)
):
    """Get status for a specific embed widget"""
    try:
        from app.models.embed import EmbedCode
        
        # Get embed code
        embed_code = db.query(EmbedCode).filter(
            EmbedCode.id == embed_id,
            EmbedCode.is_active == True
        ).first()
        
        if not embed_code:
            return {
                "is_active": False,
                "message": "Embed code not found or inactive"
            }
        
        # Get subscription status for the workspace
        subscription = db.query(Subscription).filter(
            Subscription.workspace_id == embed_code.workspace_id,
            Subscription.status.in_(['active', 'trialing'])
        ).first()
        
        if not subscription:
            return {
                "is_active": False,
                "plan": "free",
                "status": "inactive",
                "message": "No active subscription for this workspace"
            }
        
        is_active = subscription.status in ['active', 'trialing']
        
        return {
            "is_active": is_active,
            "plan": subscription.tier,
            "status": subscription.status,
            "is_trial": subscription.tier == 'free_trial',
            "trial_end": subscription.period_end.isoformat() if subscription.period_end else None,
            "embed_id": embed_id,
            "message": "Widget is active" if is_active else "Widget is inactive"
        }
        
    except Exception as e:
        logger.error(f"Error checking embed widget status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check embed widget status"
        )
