from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta
import os

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.schemas.billing import BillingInfo, UsageStats

router = APIRouter()

@router.get("/info", response_model=BillingInfo)
async def get_billing_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing information and usage statistics for the current workspace."""
    
    # Get user's workspace
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Calculate usage for the current month
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Count queries (user messages) this month
    queries_used = db.query(ChatMessage).join(ChatSession).filter(
        ChatSession.workspace_id == workspace.id,
        ChatMessage.role == "user",
        ChatMessage.created_at >= month_start
    ).count()
    
    # Count active sessions this month
    active_sessions = db.query(ChatSession).filter(
        ChatSession.workspace_id == workspace.id,
        ChatSession.last_activity_at >= month_start
    ).count()
    
    # Count documents
    documents_used = db.query(Document).filter(
        Document.workspace_id == workspace.id
    ).count()
    
    # Calculate storage usage (sum of all document sizes)
    storage_used = db.query(Document).filter(
        Document.workspace_id == workspace.id
    ).with_entities(Document.file_size).all()
    
    total_storage = sum([doc.file_size or 0 for doc in storage_used])
    
    # Determine plan based on workspace settings or default to free
    plan = getattr(workspace, 'plan', 'free')
    
    # Set limits based on plan
    if plan == 'free':
        queries_limit = 100
        documents_limit = 5
        storage_limit = 100 * 1024 * 1024  # 100MB
    elif plan == 'pro':
        queries_limit = 10000
        documents_limit = -1  # unlimited
        storage_limit = 1000 * 1024 * 1024  # 1GB
    elif plan == 'enterprise':
        queries_limit = -1  # unlimited
        documents_limit = -1  # unlimited
        storage_limit = 10 * 1024 * 1024 * 1024  # 10GB
    else:
        queries_limit = 100
        documents_limit = 5
        storage_limit = 100 * 1024 * 1024
    
    # Check if billing is active (simplified - in real implementation, check Stripe)
    billing_status = "active"  # This would come from Stripe webhook data
    current_period_end = now + timedelta(days=30)  # This would come from Stripe
    cancel_at_period_end = False  # This would come from Stripe
    
    # Generate billing portal URL (this would be from Stripe)
    billing_portal_url = None
    if plan != 'free':
        # In real implementation: get from Stripe
        billing_portal_url = f"https://billing.stripe.com/p/login/{workspace.id}"
    
    return BillingInfo(
        plan=plan,
        status=billing_status,
        current_period_end=current_period_end.isoformat(),
        cancel_at_period_end=cancel_at_period_end,
        usage=UsageStats(
            queries_used=queries_used,
            queries_limit=queries_limit,
            documents_used=documents_used,
            documents_limit=documents_limit,
            storage_used=total_storage,
            storage_limit=storage_limit
        ),
        billing_portal_url=billing_portal_url
    )

@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed usage statistics for the current workspace."""
    
    # Get user's workspace
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # Calculate usage for the current month
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Count queries (user messages) this month
    queries_used = db.query(ChatMessage).join(ChatSession).filter(
        ChatSession.workspace_id == workspace.id,
        ChatMessage.role == "user",
        ChatMessage.created_at >= month_start
    ).count()
    
    # Count documents
    documents_used = db.query(Document).filter(
        Document.workspace_id == workspace.id
    ).count()
    
    # Calculate storage usage
    storage_used = db.query(Document).filter(
        Document.workspace_id == workspace.id
    ).with_entities(Document.file_size).all()
    
    total_storage = sum([doc.file_size or 0 for doc in storage_used])
    
    # Determine plan and limits
    plan = getattr(workspace, 'plan', 'free')
    
    if plan == 'free':
        queries_limit = 100
        documents_limit = 5
        storage_limit = 100 * 1024 * 1024
    elif plan == 'pro':
        queries_limit = 10000
        documents_limit = -1
        storage_limit = 1000 * 1024 * 1024
    elif plan == 'enterprise':
        queries_limit = -1
        documents_limit = -1
        storage_limit = 10 * 1024 * 1024 * 1024
    else:
        queries_limit = 100
        documents_limit = 5
        storage_limit = 100 * 1024 * 1024
    
    return UsageStats(
        queries_used=queries_used,
        queries_limit=queries_limit,
        documents_used=documents_used,
        documents_limit=documents_limit,
        storage_used=total_storage,
        storage_limit=storage_limit
    )

@router.post("/checkout")
async def create_checkout_session(
    plan: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for plan upgrade."""
    
    if plan not in ['pro', 'enterprise']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid plan. Must be 'pro' or 'enterprise'"
        )
    
    # Get user's workspace
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    # In a real implementation, this would:
    # 1. Create a Stripe checkout session
    # 2. Return the checkout URL
    # 3. Handle webhooks to update workspace plan
    
    # For now, return a mock response
    checkout_url = f"https://checkout.stripe.com/pay/{workspace.id}_{plan}"
    
    return {
        "checkout_url": checkout_url,
        "plan": plan,
        "message": "Redirect to Stripe checkout"
    }

@router.post("/webhook")
async def handle_billing_webhook(
    payload: Dict[str, Any]
):
    """Handle Stripe webhook events for billing updates."""
    
    # In a real implementation, this would:
    # 1. Verify the webhook signature
    # 2. Parse the event type
    # 3. Update workspace plan based on event
    # 4. Handle subscription changes, cancellations, etc.
    
    event_type = payload.get("type")
    
    if event_type == "checkout.session.completed":
        # Handle successful checkout
        pass
    elif event_type == "customer.subscription.updated":
        # Handle subscription changes
        pass
    elif event_type == "customer.subscription.deleted":
        # Handle subscription cancellation
        pass
    
    return {"status": "success"}

@router.get("/invoices")
async def get_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing invoices for the current workspace."""
    
    # In a real implementation, this would fetch invoices from Stripe
    # For now, return empty list
    return {
        "invoices": [],
        "message": "No invoices available"
    }
