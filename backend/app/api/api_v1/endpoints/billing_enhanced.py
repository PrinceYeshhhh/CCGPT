"""
Enhanced billing endpoints with Stripe integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.models.subscriptions import Subscription
from app.schemas.billing import BillingInfo, UsageStats, CheckoutRequest, CheckoutResponse
from app.services.stripe_service import stripe_service
from app.middleware.quota_middleware import get_quota_info, QuotaExceededException

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status", response_model=BillingInfo)
async def get_billing_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current billing status and subscription information"""
    
    # Get workspace
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.workspace_id == current_user.workspace_id
    ).first()
    
    if not subscription:
        # No subscription - return free tier info
        return BillingInfo(
            plan="free",
            status="active",
            current_period_end=(datetime.utcnow() + timedelta(days=30)).isoformat(),
            cancel_at_period_end=False,
            usage=UsageStats(
                queries_used=0,
                queries_limit=100,  # Free tier limit
                documents_used=0,
                documents_limit=5,
                storage_used=0,
                storage_limit=100 * 1024 * 1024  # 100MB
            ),
            billing_portal_url=None
        )
    
    # Calculate usage for current period
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Count documents
    documents_used = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).count()
    
    # Calculate storage usage (simplified)
    storage_used = 0  # Would need to calculate from documents
    
    # Set limits based on plan
    plan_config = stripe_service.get_plan_config(subscription.tier)
    
    return BillingInfo(
        plan=subscription.tier,
        status=subscription.status,
        current_period_end=subscription.period_end.isoformat() if subscription.period_end else None,
        cancel_at_period_end=subscription.status == 'canceled',
        usage=UsageStats(
            queries_used=subscription.queries_this_period,
            queries_limit=subscription.monthly_query_quota or -1,
            documents_used=documents_used,
            documents_limit=5 if subscription.tier == 'free' else -1,
            storage_used=storage_used,
            storage_limit=100 * 1024 * 1024 if subscription.tier == 'free' else 1024 * 1024 * 1024
        ),
        billing_portal_url=f"https://billing.stripe.com/p/login/{subscription.stripe_customer_id}" if subscription.stripe_customer_id else None
    )

@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for plan upgrade"""
    
    # Validate plan tier
    if request.plan_tier not in ['starter', 'pro', 'enterprise', 'white_label']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan tier. Must be 'starter', 'pro', 'enterprise', or 'white_label'"
        )
    
    # Get workspace
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    try:
        # Create checkout session
        result = await stripe_service.create_checkout_session(
            workspace_id=str(workspace.id),
            plan_tier=request.plan_tier,
            customer_email=current_user.email,
            customer_name=current_user.full_name or workspace.name,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        logger.info(f"Created checkout session for workspace {workspace.id}, plan {request.plan_tier}")
        
        return CheckoutResponse(
            checkout_url=result['url'],
            plan=request.plan_tier,
            message="Checkout session created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.post("/portal")
async def create_billing_portal_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe billing portal session"""
    
    # Get subscription
    subscription = db.query(Subscription).filter(
        Subscription.workspace_id == current_user.workspace_id
    ).first()
    
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    try:
        # Create billing portal session
        portal_url = await stripe_service.create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url="https://your-frontend.com/billing"
        )
        
        return {
            "portal_url": portal_url,
            "message": "Billing portal session created"
        }
        
    except Exception as e:
        logger.error(f"Error creating billing portal session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )

@router.get("/usage")
async def get_usage_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get usage history for analytics"""
    
    # Get quota info
    quota_info = get_quota_info(current_user, db)
    
    # Get usage over time (last 30 days)
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    # This would typically query usage logs
    # For now, return mock data
    usage_history = []
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        usage_history.append({
            "date": date.isoformat(),
            "queries": max(0, quota_info["quota_used"] - (30 - i) * 10),  # Mock decreasing usage
            "documents": 0
        })
    
    return {
        "quota_info": quota_info,
        "usage_history": usage_history,
        "period_start": thirty_days_ago.isoformat(),
        "period_end": now.isoformat()
    }

@router.post("/webhook")
async def handle_stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    # Verify webhook signature
    event = stripe_service.parse_webhook_event(body, signature)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )
    
    logger.info(f"Processing Stripe webhook event: {event['type']}")
    
    try:
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            await handle_checkout_completed(event, db)
        elif event['type'] == 'invoice.payment_succeeded':
            await handle_payment_succeeded(event, db)
        elif event['type'] == 'customer.subscription.updated':
            await handle_subscription_updated(event, db)
        elif event['type'] == 'customer.subscription.deleted':
            await handle_subscription_deleted(event, db)
        elif event['type'] == 'invoice.payment_failed':
            await handle_payment_failed(event, db)
        else:
            logger.info(f"Unhandled webhook event type: {event['type']}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook event {event['type']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )

async def handle_checkout_completed(event: Dict[str, Any], db: Session):
    """Handle checkout.session.completed event"""
    session = event['data']['object']
    workspace_id = session['metadata'].get('workspace_id')
    plan_tier = session['metadata'].get('plan_tier')
    
    if not workspace_id or not plan_tier:
        logger.error(f"Missing metadata in checkout session: {session['id']}")
        return
    
    # Get or create subscription
    subscription = db.query(Subscription).filter(
        Subscription.workspace_id == workspace_id
    ).first()
    
    if not subscription:
        subscription = Subscription(
            workspace_id=workspace_id,
            stripe_customer_id=session['customer'],
            tier=plan_tier,
            status='active',
            seats=1,
            monthly_query_quota=stripe_service.get_plan_config(plan_tier)['monthly_query_quota'],
            queries_this_period=0,
            period_start=datetime.utcnow(),
            period_end=datetime.utcnow() + timedelta(days=30),
            next_billing_at=datetime.utcnow() + timedelta(days=30)
        )
        db.add(subscription)
    else:
        # Update existing subscription
        subscription.stripe_customer_id = session['customer']
        subscription.tier = plan_tier
        subscription.status = 'active'
        subscription.monthly_query_quota = stripe_service.get_plan_config(plan_tier)['monthly_query_quota']
        subscription.queries_this_period = 0
        subscription.period_start = datetime.utcnow()
        subscription.period_end = datetime.utcnow() + timedelta(days=30)
        subscription.next_billing_at = datetime.utcnow() + timedelta(days=30)
    
    # Update workspace plan
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace:
        workspace.plan = plan_tier
    
    db.commit()
    logger.info(f"Checkout completed for workspace {workspace_id}, plan {plan_tier}")

async def handle_payment_succeeded(event: Dict[str, Any], db: Session):
    """Handle invoice.payment_succeeded event"""
    invoice = event['data']['object']
    customer_id = invoice['customer']
    
    # Find subscription by customer ID
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    
    if subscription:
        subscription.status = 'active'
        subscription.queries_this_period = 0  # Reset for new period
        subscription.period_start = datetime.utcnow()
        subscription.period_end = datetime.utcnow() + timedelta(days=30)
        subscription.next_billing_at = datetime.utcnow() + timedelta(days=30)
        
        db.commit()
        logger.info(f"Payment succeeded for subscription {subscription.id}")

async def handle_subscription_updated(event: Dict[str, Any], db: Session):
    """Handle customer.subscription.updated event"""
    stripe_subscription = event['data']['object']
    subscription_id = stripe_subscription['id']
    
    # Find subscription by Stripe subscription ID
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if subscription:
        subscription.status = stripe_subscription['status']
        subscription.period_start = datetime.fromtimestamp(stripe_subscription['current_period_start'])
        subscription.period_end = datetime.fromtimestamp(stripe_subscription['current_period_end'])
        
        db.commit()
        logger.info(f"Updated subscription {subscription.id} status to {subscription.status}")

async def handle_subscription_deleted(event: Dict[str, Any], db: Session):
    """Handle customer.subscription.deleted event"""
    stripe_subscription = event['data']['object']
    subscription_id = stripe_subscription['id']
    
    # Find subscription by Stripe subscription ID
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == subscription_id
    ).first()
    
    if subscription:
        subscription.status = 'canceled'
        db.commit()
        logger.info(f"Canceled subscription {subscription.id}")

async def handle_payment_failed(event: Dict[str, Any], db: Session):
    """Handle invoice.payment_failed event"""
    invoice = event['data']['object']
    customer_id = invoice['customer']
    
    # Find subscription by customer ID
    subscription = db.query(Subscription).filter(
        Subscription.stripe_customer_id == customer_id
    ).first()
    
    if subscription:
        subscription.status = 'past_due'
        db.commit()
        logger.info(f"Payment failed for subscription {subscription.id}")

@router.get("/quota")
async def get_quota_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current quota status for the workspace"""
    return get_quota_info(current_user, db)
