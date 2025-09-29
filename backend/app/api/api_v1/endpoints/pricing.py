"""
Pricing endpoints for fetching real pricing data
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.schemas.billing import PricingResponse, PricingPlan, TrialRequest, TrialResponse
from app.services.stripe_service import stripe_service
from app.models.subscriptions import Subscription
from app.models.workspace import Workspace
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/plans", response_model=PricingResponse)
async def get_pricing_plans():
    """Get all available pricing plans with real Stripe data"""
    
    try:
        # Get plan configurations from Stripe service
        plans_data = []
        
        # Only include main plans (exclude free_trial and white_label from main pricing)
        main_plans = ['starter', 'pro', 'enterprise']
        
        for tier in main_plans:
            config = stripe_service.plans[tier]
            
            # Convert price from dollars to cents for consistency
            price_cents = 0
            if tier == 'starter':
                price_cents = 2000  # $20
            elif tier == 'pro':
                price_cents = 5000  # $50
            elif tier == 'enterprise':
                price_cents = 20000  # $200
            
            plan = PricingPlan(
                id=tier,
                name=config['name'],
                description=f"Perfect for {tier} businesses",
                price=price_cents,
                currency="usd",
                interval="month",
                features=config['features'],
                stripe_price_id=config['price_id'],
                popular=(tier == 'pro'),
                trial_days=0  # No trial for paid plans
            )
            plans_data.append(plan)
        
        return PricingResponse(
            plans=plans_data,
            currency="usd",
            trial_days=7
        )
        
    except Exception as e:
        logger.error(f"Error fetching pricing plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pricing plans"
        )

@router.post("/start-trial", response_model=TrialResponse)
async def start_free_trial(
    request: TrialRequest,
    db: Session = Depends(get_db)
):
    """Start a 7-day free trial (one-time only per user)"""
    
    try:
        from app.services.auth import AuthService
        from app.models.user import User
        
        auth_service = AuthService(db)
        
        # Strict validation - check both email and mobile uniqueness
        validation_result = auth_service.validate_user_registration(
            request.email, 
            request.mobile_phone
        )
        
        if not validation_result["valid"]:
            return TrialResponse(
                success=False,
                message=validation_result["message"]
            )
        
        # Check if user already has used their trial (one-time only)
        # Check by both email and mobile to ensure strict uniqueness
        existing_trial_by_email = db.query(Subscription).filter(
            Subscription.workspace_id == request.email,
            Subscription.tier == 'free_trial'
        ).first()
        
        existing_trial_by_mobile = db.query(Subscription).join(User).filter(
            User.mobile_phone == request.mobile_phone,
            Subscription.tier == 'free_trial'
        ).first()

        if existing_trial_by_email or existing_trial_by_mobile:
            return TrialResponse(
                success=False,
                message="You have already used your free trial. Please choose a paid plan."
            )
        
        # Check if user has any active subscription
        existing_subscription = db.query(Subscription).filter(
            Subscription.workspace_id == request.email,
            Subscription.status.in_(['active', 'trialing'])
        ).first()
        
        if existing_subscription:
            return TrialResponse(
                success=False,
                message="You already have an active subscription"
            )
        
        # Create free trial subscription (7 days, 100 queries, 1 document)
        trial_end = datetime.utcnow() + timedelta(days=7)
        trial_config = stripe_service.get_plan_config('free_trial')
        
        trial_subscription = Subscription(
            workspace_id=request.email,  # Using email as workspace_id for trial
            tier='free_trial',
            status='trialing',
            seats=1,
            monthly_query_quota=trial_config['monthly_query_quota'],
            queries_this_period=0,
            period_start=datetime.utcnow(),
            period_end=trial_end,
            next_billing_at=trial_end
        )
        
        db.add(trial_subscription)
        db.commit()
        
        logger.info(f"Started free trial for {request.email}")
        
        return TrialResponse(
            success=True,
            message="7-day free trial started! You get 100 queries and can upload 1 document.",
            trial_end=trial_end.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting trial: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start trial"
        )

@router.get("/trial-status")
async def get_trial_status(
    workspace_id: str,
    db: Session = Depends(get_db)
):
    """Get trial status for a workspace"""
    
    try:
        subscription = db.query(Subscription).filter(
            Subscription.workspace_id == workspace_id,
            Subscription.status == 'trialing'
        ).first()
        
        if not subscription:
            return {
                "has_trial": False,
                "message": "No active trial found"
            }
        
        now = datetime.utcnow()
        trial_remaining = (subscription.period_end - now).days if subscription.period_end else 0
        
        return {
            "has_trial": True,
            "plan": subscription.tier,
            "trial_end": subscription.period_end.isoformat() if subscription.period_end else None,
            "days_remaining": max(0, trial_remaining),
            "quota_used": subscription.queries_this_period,
            "quota_limit": subscription.monthly_query_quota
        }
        
    except Exception as e:
        logger.error(f"Error checking trial status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check trial status"
        )

@router.get("/white-label", response_model=PricingPlan)
async def get_white_label_pricing():
    """Get white label pricing information"""
    
    try:
        config = stripe_service.get_plan_config('white_label')
        
        plan = PricingPlan(
            id='white_label',
            name=config['name'],
            description="Complete white-label solution for resellers",
            price=99900,  # $999 in cents
            currency="usd",
            interval="one_time",
            features=config['features'],
            stripe_price_id=config['price_id'],
            popular=False,
            trial_days=0
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Error fetching white label pricing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch white label pricing"
        )
