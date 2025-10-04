"""
Enhanced billing endpoints with Stripe integration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.core.config import settings
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.models.subscriptions import Subscription
from app.schemas.billing import BillingInfo, UsageStats, CheckoutRequest, CheckoutResponse, PaymentMethod, PaymentMethodsResponse, PaymentMethodInfo, InvoicesResponse, Invoice
from app.services.stripe_service import stripe_service
from app.middleware.quota_middleware import get_quota_info, QuotaExceededException
from app.utils.plan_limits import PlanLimits

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
    
    # Set limits based on new pricing structure
    plan_config = stripe_service.get_plan_config(subscription.tier)

    # Get standardized limits for the plan tier
    plan_limits = PlanLimits.get_limits(subscription.tier)

    # Derive a base URL for billing links
    base_url = ""
    try:
        from urllib.parse import urlparse
        success_or_public = getattr(settings, 'STRIPE_SUCCESS_URL', '') or getattr(settings, 'PUBLIC_BASE_URL', '')
        if success_or_public:
            parsed = urlparse(success_or_public)
            if parsed.scheme and parsed.netloc:
                base_url = f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        base_url = ""

    billing_portal_url = f"{base_url}/billing/portal" if (subscription.stripe_customer_id and base_url) else None

    return BillingInfo(
        plan=subscription.tier,
        status=subscription.status,
        current_period_end=subscription.period_end.isoformat() if subscription.period_end else None,
        cancel_at_period_end=subscription.status == 'canceled',
        usage=UsageStats(
            queries_used=subscription.queries_this_period,
            queries_limit=plan_limits['queries_limit'],
            documents_used=documents_used,
            documents_limit=plan_limits['documents_limit'],
            storage_used=storage_used,
            storage_limit=plan_limits['storage_limit']
        ),
        billing_portal_url=billing_portal_url,
        trial_end=subscription.period_end.isoformat() if subscription.tier == 'free_trial' and subscription.period_end else None,
        is_trial=subscription.tier == 'free_trial'
    )

@router.post("/create-checkout-session", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create checkout session for plan upgrade with multiple payment methods"""
    
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
        # Handle different payment methods
        if request.payment_method == PaymentMethod.STRIPE:
            # Create Stripe checkout session
            result = await stripe_service.create_checkout_session(
                workspace_id=str(workspace.id),
                plan_tier=request.plan_tier,
                customer_email=current_user.email,
                customer_name=current_user.full_name or workspace.name,
                success_url=request.success_url,
                cancel_url=request.cancel_url
            )
            
            logger.info(f"Created Stripe checkout session for workspace {workspace.id}, plan {request.plan_tier}")
            
            return CheckoutResponse(
                checkout_url=result['url'],
                plan=request.plan_tier,
                payment_method=request.payment_method.value,
                message="Stripe checkout session created successfully"
            )
            
        elif request.payment_method == PaymentMethod.CARD:
            # For direct card payments, we'll use Stripe Payment Intents
            # This is a simplified implementation - in production, you'd want more robust card handling
            result = await stripe_service.create_checkout_session(
                workspace_id=str(workspace.id),
                plan_tier=request.plan_tier,
                customer_email=current_user.email,
                customer_name=current_user.full_name or workspace.name,
                success_url=request.success_url,
                cancel_url=request.cancel_url
            )
            
            return CheckoutResponse(
                checkout_url=result['url'],
                plan=request.plan_tier,
                payment_method=request.payment_method.value,
                message="Card payment session created successfully"
            )
            
        elif request.payment_method == PaymentMethod.UPI:
            # For UPI payments, generate a payment URL
            # This is a mock implementation - in production, integrate with UPI providers like Razorpay, PayU, etc.
            upi_url = f"upi://pay?pa=merchant@upi&pn=CustomerCareGPT&tr={workspace.id}_{request.plan_tier}&am={stripe_service.get_plan_config(request.plan_tier).get('price', 0)}&cu=INR"
            
            return CheckoutResponse(
                upi_payment_url=upi_url,
                plan=request.plan_tier,
                payment_method=request.payment_method.value,
                message="UPI payment URL generated successfully"
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment method {request.payment_method} not supported yet"
            )
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.get("/payment-methods", response_model=PaymentMethodsResponse)
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment methods for the current user"""
    try:
        # Get subscription to check if user has Stripe customer
        subscription = db.query(Subscription).filter(
            Subscription.workspace_id == current_user.workspace_id
        ).first()
        
        if not subscription or not subscription.stripe_customer_id:
            return PaymentMethodsResponse(
                payment_methods=[],
                default_method=None,
                message="No payment methods found"
            )
        
        # In a real implementation, this would fetch from Stripe
        # For now, return mock data based on subscription
        payment_methods = []
        
        if subscription.tier in ['starter', 'pro', 'enterprise', 'white_label']:
            payment_methods = [
                PaymentMethodInfo(
                    id="pm_card_visa",
                    type="card",
                    last4="4242",
                    brand="visa",
                    exp_month=12,
                    exp_year=2027,
                    is_default=True
                )
            ]
        
        return PaymentMethodsResponse(
            payment_methods=payment_methods,
            default_method="pm_card_visa" if payment_methods else None,
            message="Payment methods retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error fetching payment methods: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment methods"
        )

@router.get("/invoices", response_model=InvoicesResponse)
async def get_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing invoices for the current user"""
    try:
        # Get subscription
        subscription = db.query(Subscription).filter(
            Subscription.workspace_id == current_user.workspace_id
        ).first()
        
        if not subscription or not subscription.stripe_customer_id:
            return InvoicesResponse(
                invoices=[],
                message="No invoices found"
            )
        
        # In a real implementation, this would fetch from Stripe
        # For now, return mock data based on subscription
        invoices = []
        
        if subscription.tier in ['starter', 'pro', 'enterprise', 'white_label']:
            # Generate mock invoices based on plan
            plan_prices = {
                'starter': 2000,  # $20
                'pro': 5000,      # $50
                'enterprise': 20000,  # $200
                'white_label': 99900  # $999
            }
            
            price = plan_prices.get(subscription.tier, 0)
            if price > 0:
                base = (lambda s: f"{s.scheme}://{s.netloc}")(__import__('urllib.parse').urlparse(getattr(settings, 'STRIPE_SUCCESS_URL', '') or getattr(settings, 'PUBLIC_BASE_URL', ''))) if (getattr(settings, 'STRIPE_SUCCESS_URL', '') or getattr(settings, 'PUBLIC_BASE_URL', '')) else ''
                invoices = [
                    Invoice(
                        id=f"inv_{subscription.id}_001",
                        amount=price,
                        currency="usd",
                        status="paid",
                        created=datetime.utcnow() - timedelta(days=30),
                        invoice_pdf=(f"{base}/billing/invoice/{subscription.id}_001.pdf" if base else None),
                        description=f"{subscription.tier.title()} Plan - Monthly"
                    )
                ]
                
                # Add more historical invoices
                if subscription.tier != 'white_label':  # White label is one-time
                    for i in range(2, 4):
                        invoices.append(
                            Invoice(
                                id=f"inv_{subscription.id}_{i:03d}",
                                amount=price,
                                currency="usd",
                                status="paid",
                                created=datetime.utcnow() - timedelta(days=30*i),
                                invoice_pdf=(f"{base}/billing/invoice/{subscription.id}_{i:03d}.pdf" if base else None),
                                description=f"{subscription.tier.title()} Plan - Monthly"
                            )
                        )
        
        return InvoicesResponse(
            invoices=invoices,
            message=f"Found {len(invoices)} invoices"
        )
        
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch invoices"
        )


@router.get("/invoices/download-all")
async def download_all_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download all invoices as a ZIP file"""
    try:
        subscription = db.query(Subscription).filter(
            Subscription.workspace_id == current_user.workspace_id
        ).first()
        
        if not subscription or not subscription.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No subscription found"
            )
        
        # Get all invoices
        invoices = []
        if subscription.tier in ['starter', 'pro', 'enterprise', 'white_label']:
            plan_prices = {
                'starter': 2000,  # $20
                'pro': 5000,      # $50
                'enterprise': 20000,  # $200
                'white_label': 99900  # $999
            }
            
            price = plan_prices.get(subscription.tier, 0)
            if price > 0:
                # Generate mock invoices for demo
                for i in range(1, 4):
                    invoices.append({
                        'id': f"inv_{subscription.id}_{i:03d}",
                        'amount': price,
                        'currency': 'usd',
                        'status': 'paid',
                        'created': datetime.utcnow() - timedelta(days=30*i),
                        'description': f"{subscription.tier.title()} Plan - Monthly"
                    })
        
        if not invoices:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No invoices found"
            )
        
        # Create a simple ZIP file with invoice data
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for invoice in invoices:
                # Create invoice content
                invoice_content = f"""
Invoice ID: {invoice['id']}
Amount: ${invoice['amount'] / 100:.2f} {invoice['currency'].upper()}
Status: {invoice['status'].title()}
Date: {invoice['created'].strftime('%Y-%m-%d')}
Description: {invoice['description']}
                """.strip()
                
                zip_file.writestr(f"invoice_{invoice['id']}.txt", invoice_content)
        
        zip_buffer.seek(0)
        
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=all-invoices-{subscription.id}.zip"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating invoice ZIP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invoice ZIP file"
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
        # Derive frontend base from STRIPE_SUCCESS_URL or PUBLIC_BASE_URL
        from urllib.parse import urlparse
        _fb = getattr(settings, 'STRIPE_SUCCESS_URL', '') or getattr(settings, 'PUBLIC_BASE_URL', '')
        _ret = None
        if _fb:
            _p = urlparse(_fb)
            _ret = f"{_p.scheme}://{_p.netloc}/billing"
        portal_url = await stripe_service.create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=_ret or None
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
