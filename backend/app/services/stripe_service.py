"""
Stripe integration service for billing and subscriptions
"""

import stripe
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_API_KEY

class StripeService:
    """Service for handling Stripe operations"""
    
    def __init__(self):
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self.success_url = settings.STRIPE_SUCCESS_URL
        self.cancel_url = settings.STRIPE_CANCEL_URL
        self.default_tier = settings.BILLING_DEFAULT_TIER
        
        # Plan definitions
        self.plans = {
            'free_trial': {
                'name': 'Free Trial',
                'price_id': None,  # No Stripe price for trial
                'monthly_query_quota': 100,
                'seats': 1,
                'documents_limit': 1,
                'storage_limit': 10 * 1024 * 1024,  # 10MB
                'trial_days': 7,
                'features': [
                    '7-day free trial',
                    '100 queries total',
                    '1 document upload',
                    'Basic analytics',
                    'Email support'
                ]
            },
            'starter': {
                'name': 'Starter',
                'price_id': os.getenv('STRIPE_STARTER_PRICE_ID', 'price_starter'),
                'monthly_query_quota': 7000,
                'seats': 1,
                'documents_limit': 5,
                'storage_limit': 100 * 1024 * 1024,  # 100MB
                'trial_days': 0,  # No trial for paid plans
                'features': [
                    '7,000 queries/month',
                    'Up to 5 documents',
                    'Basic analytics',
                    'Email support'
                ]
            },
            'pro': {
                'name': 'Pro',
                'price_id': os.getenv('STRIPE_PRO_PRICE_ID', 'price_pro'),
                'monthly_query_quota': 50000,
                'seats': 5,
                'documents_limit': 25,
                'storage_limit': 500 * 1024 * 1024,  # 500MB
                'trial_days': 0,  # No trial for paid plans
                'features': [
                    '50,000 queries/month',
                    'Up to 25 documents',
                    'Advanced analytics',
                    'Priority support',
                    'API access',
                    'Custom branding'
                ]
            },
            'enterprise': {
                'name': 'Enterprise',
                'price_id': os.getenv('STRIPE_ENTERPRISE_PRICE_ID', 'price_enterprise'),
                'monthly_query_quota': None,  # Unlimited
                'seats': -1,  # Unlimited
                'documents_limit': -1,  # Unlimited
                'storage_limit': 10 * 1024 * 1024 * 1024,  # 10GB
                'trial_days': 0,  # No trial for paid plans
                'features': [
                    'Unlimited queries',
                    'Unlimited documents',
                    'Full analytics suite',
                    '24/7 phone support',
                    'Custom integrations',
                    'Dedicated account manager',
                    'SLA guarantee',
                    'White-label options'
                ]
            },
            'white_label': {
                'name': 'White Label',
                'price_id': os.getenv('STRIPE_WHITE_LABEL_PRICE_ID', 'price_white_label'),
                'monthly_query_quota': None,  # One-time purchase
                'seats': -1,  # Unlimited
                'documents_limit': -1,  # Unlimited
                'storage_limit': -1,  # Unlimited
                'trial_days': 0,  # No trial for one-time purchase
                'features': [
                    'One-time purchase',
                    'Unlimited queries',
                    'Unlimited documents',
                    'Full white-label solution',
                    'Custom domain support',
                    'Priority support',
                    'Source code access',
                    'Custom integrations'
                ]
            }
        }
    
    def get_plan_config(self, tier: str) -> Dict[str, Any]:
        """Get plan configuration by tier"""
        return self.plans.get(tier, self.plans['starter'])
    
    async def create_customer(self, workspace_id: str, email: str, name: str) -> str:
        """Create or retrieve Stripe customer"""
        try:
            # Check if customer already exists
            customers = stripe.Customer.list(email=email, limit=1)
            if customers.data:
                return customers.data[0].id
            
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'workspace_id': workspace_id,
                    'source': 'customercaregpt'
                }
            )
            
            logger.info(f"Created Stripe customer {customer.id} for workspace {workspace_id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {e}")
            raise
    
    async def create_checkout_session(
        self, 
        workspace_id: str, 
        plan_tier: str, 
        customer_email: str,
        customer_name: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Stripe checkout session"""
        try:
            plan_config = self.get_plan_config(plan_tier)
            
            # Create or retrieve customer
            customer_id = await self.create_customer(workspace_id, customer_email, customer_name)
            
            # Prepare checkout session parameters
            session_params = {
                'customer': customer_id,
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': plan_config['price_id'],
                    'quantity': 1,
                }],
                'mode': 'subscription' if plan_tier != 'white_label' else 'payment',
                'success_url': success_url or self.success_url,
                'cancel_url': cancel_url or self.cancel_url,
                'metadata': {
                    'workspace_id': workspace_id,
                    'plan_tier': plan_tier
                }
            }
            
            # Add subscription-specific parameters
            if plan_tier != 'white_label':
                session_params['subscription_data'] = {
                    'metadata': {
                        'workspace_id': workspace_id,
                        'plan_tier': plan_tier
                    }
                }
            
            # Create checkout session
            session = stripe.checkout.Session.create(**session_params)
            
            logger.info(f"Created checkout session {session.id} for workspace {workspace_id}, plan {plan_tier}")
            
            return {
                'session_id': session.id,
                'url': session.url,
                'plan_tier': plan_tier,
                'customer_id': customer_id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {e}")
            raise
    
    async def create_billing_portal_session(self, customer_id: str, return_url: str) -> str:
        """Create Stripe billing portal session"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            
            logger.info(f"Created billing portal session for customer {customer_id}")
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating billing portal session: {e}")
            raise
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Get Stripe subscription details"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription {subscription_id}: {e}")
            raise
    
    async def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> Dict[str, Any]:
        """Cancel Stripe subscription"""
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription {subscription_id}: {e}")
            raise
    
    async def update_subscription_quota(self, subscription_id: str, new_quota: int) -> Dict[str, Any]:
        """Update subscription quota (for admin overrides)"""
        try:
            # This would typically involve updating subscription items
            # For now, we'll just log the request
            logger.info(f"Request to update quota for subscription {subscription_id} to {new_quota}")
            
            # In a real implementation, you might:
            # 1. Update the subscription item quantity
            # 2. Or create a proration
            # 3. Or handle it through metadata
            
            return {"status": "success", "message": "Quota update requested"}
            
        except stripe.error.StripeError as e:
            logger.error(f"Error updating subscription quota: {e}")
            raise
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid webhook signature")
            return False
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def parse_webhook_event(self, payload: bytes, signature: str) -> Optional[Dict[str, Any]]:
        """Parse and verify webhook event"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid webhook signature")
            return None
        except Exception as e:
            logger.error(f"Error parsing webhook event: {e}")
            return None

# Global instance
stripe_service = StripeService()
