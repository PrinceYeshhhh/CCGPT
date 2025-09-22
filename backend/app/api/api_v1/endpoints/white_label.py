"""
White-label purchase and license management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import logging

from app.core.database import get_db
from app.api.api_v1.dependencies import get_current_user
from app.models.user import User
from app.models.workspace import Workspace
from app.models.subscriptions import Subscription
from app.services.stripe_service import stripe_service
from app.services.license_service import license_service
from app.schemas.billing import CheckoutRequest, CheckoutResponse

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/purchase", response_model=CheckoutResponse)
async def purchase_white_label(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase white-label license (one-time payment)"""
    
    # Get workspace
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    try:
        # Create checkout session for white-label
        result = await stripe_service.create_checkout_session(
            workspace_id=str(workspace.id),
            plan_tier="white_label",
            customer_email=current_user.email,
            customer_name=current_user.full_name or workspace.name,
            success_url=request.success_url or f"{request.success_url}/billing/white-label/success",
            cancel_url=request.cancel_url or f"{request.cancel_url}/billing/white-label/cancel"
        )
        
        logger.info(f"Created white-label checkout session for workspace {workspace.id}")
        
        return CheckoutResponse(
            checkout_url=result['url'],
            plan="white_label",
            message="White-label checkout session created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating white-label checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create white-label checkout session"
        )

@router.get("/license")
async def get_license(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get white-label license for current workspace"""
    
    # Check if workspace has white-label subscription
    subscription = db.query(Subscription).filter(
        Subscription.workspace_id == current_user.workspace_id,
        Subscription.tier == "white_label",
        Subscription.status == "active"
    ).first()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active white-label license found"
        )
    
    # Get license from metadata
    license_b64 = subscription.metadata.get("license_key") if subscription.metadata else None
    if not license_b64:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License key not found in subscription"
        )
    
    # Validate license
    license_data = license_service.validate_license(license_b64)
    if not license_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired license"
        )
    
    return {
        "license_key": license_b64,
        "license_data": license_data,
        "features": license_data.get("features", {}),
        "expires_at": license_data.get("expires_at"),
        "customer_name": license_data.get("customer_name"),
        "customer_email": license_data.get("customer_email")
    }

@router.get("/license/download")
async def download_license(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download license file"""
    
    # Get license
    license_response = await get_license(current_user, db)
    license_b64 = license_response["license_key"]
    
    # Generate license file content
    content = license_service.generate_license_file_content(license_b64)
    
    # Return as downloadable file
    return StreamingResponse(
        iter([content]),
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=CustomerCareGPT_License_{current_user.workspace_id}.txt"
        }
    )

@router.post("/activate")
async def activate_license(
    license_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Activate a white-label license"""
    
    # Validate license
    license_data = license_service.validate_license(license_key)
    if not license_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired license"
        )
    
    # Check if license matches workspace
    if license_data.get("workspace_id") != str(current_user.workspace_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License does not match current workspace"
        )
    
    # Create or update subscription
    subscription = db.query(Subscription).filter(
        Subscription.workspace_id == current_user.workspace_id
    ).first()
    
    if not subscription:
        subscription = Subscription(
            workspace_id=current_user.workspace_id,
            tier="white_label",
            status="active",
            seats=-1,  # Unlimited
            monthly_query_quota=None,  # Unlimited
            queries_this_period=0,
            metadata={"license_key": license_key, "activated_at": datetime.utcnow().isoformat()}
        )
        db.add(subscription)
    else:
        subscription.tier = "white_label"
        subscription.status = "active"
        subscription.seats = -1
        subscription.monthly_query_quota = None
        existing_metadata = subscription.metadata or {}
        subscription.metadata = {
            **existing_metadata,
            "license_key": license_key,
            "activated_at": datetime.utcnow().isoformat()
        }
    
    # Update workspace plan
    workspace = db.query(Workspace).filter(Workspace.id == current_user.workspace_id).first()
    if workspace:
        workspace.plan = "white_label"
    
    db.commit()
    
    logger.info(f"Activated white-label license for workspace {current_user.workspace_id}")
    
    return {
        "message": "License activated successfully",
        "license_data": license_data,
        "features": license_data.get("features", {})
    }

@router.get("/features")
async def get_license_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available features for current license"""
    
    # Get license
    try:
        license_response = await get_license(current_user, db)
        return {
            "features": license_response["features"],
            "license_data": license_response["license_data"]
        }
    except HTTPException:
        # No license - return free tier features
        return {
            "features": {
                "unlimited_queries": False,
                "unlimited_documents": False,
                "custom_branding": False,
                "api_access": False,
                "priority_support": False,
                "white_label": False
            },
            "license_data": None
        }

@router.post("/webhook")
async def handle_white_label_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle white-label specific webhook events"""
    
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
    
    logger.info(f"Processing white-label webhook event: {event['type']}")
    
    try:
        if event['type'] == 'checkout.session.completed':
            await handle_white_label_checkout_completed(event, db)
        else:
            logger.info(f"Unhandled white-label webhook event type: {event['type']}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing white-label webhook event {event['type']}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )

async def handle_white_label_checkout_completed(event: Dict[str, Any], db: Session):
    """Handle white-label checkout completion"""
    session = event['data']['object']
    workspace_id = session['metadata'].get('workspace_id')
    
    if not workspace_id:
        logger.error(f"Missing workspace_id in white-label checkout session: {session['id']}")
        return
    
    # Get workspace
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        logger.error(f"Workspace not found: {workspace_id}")
        return
    
    # Generate license
    features = {
        "unlimited_queries": True,
        "unlimited_documents": True,
        "custom_branding": True,
        "api_access": True,
        "priority_support": True,
        "white_label": True,
        "custom_domain": True,
        "advanced_analytics": True
    }
    
    license_b64 = license_service.generate_license(
        workspace_id=workspace_id,
        customer_name=workspace.name,
        customer_email=session.get('customer_email', ''),
        features=features
    )
    
    # Create subscription
    subscription = Subscription(
        workspace_id=workspace_id,
        stripe_customer_id=session['customer'],
        tier="white_label",
        status="active",
        seats=-1,  # Unlimited
        monthly_query_quota=None,  # Unlimited
        queries_this_period=0,
        metadata={
            "license_key": license_b64,
            "purchase_date": datetime.utcnow().isoformat(),
            "features": features
        }
    )
    
    db.add(subscription)
    
    # Update workspace plan
    workspace.plan = "white_label"
    
    db.commit()
    
    logger.info(f"White-label license generated for workspace {workspace_id}")
