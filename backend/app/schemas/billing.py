from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PaymentMethod(str, Enum):
    CARD = "card"
    STRIPE = "stripe"
    UPI = "upi"
    BANK_TRANSFER = "bank_transfer"

class PlanTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    WHITE_LABEL = "white_label"

class UsageStats(BaseModel):
    queries_used: int
    queries_limit: int
    documents_used: int
    documents_limit: int
    storage_used: int  # in bytes
    storage_limit: int  # in bytes

class BillingInfo(BaseModel):
    plan: str  # 'free', 'pro', 'enterprise'
    status: str  # 'active', 'canceled', 'past_due'
    current_period_end: str  # ISO datetime
    cancel_at_period_end: bool
    usage: UsageStats
    billing_portal_url: Optional[str] = None
    trial_end: Optional[str] = None
    is_trial: bool = False

class PricingPlan(BaseModel):
    id: str
    name: str
    description: str
    price: int  # in cents
    currency: str
    interval: str  # 'month', 'year', 'one_time'
    features: List[str]
    stripe_price_id: Optional[str] = None
    popular: bool = False
    trial_days: int = 7

class PricingResponse(BaseModel):
    plans: List[PricingPlan]
    currency: str
    trial_days: int

class CheckoutRequest(BaseModel):
    plan_tier: str
    payment_method: PaymentMethod
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    trial_days: Optional[int] = 7

class CheckoutResponse(BaseModel):
    checkout_url: Optional[str] = None
    payment_intent_id: Optional[str] = None
    upi_payment_url: Optional[str] = None
    plan: str
    payment_method: str
    message: str

class PaymentMethodInfo(BaseModel):
    id: str
    type: str
    last4: Optional[str] = None
    brand: Optional[str] = None
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool = False

class PaymentMethodsResponse(BaseModel):
    payment_methods: List[PaymentMethodInfo]
    default_method: Optional[str] = None

class Invoice(BaseModel):
    id: str
    amount: int  # in cents
    currency: str
    status: str
    created: datetime
    invoice_pdf: Optional[str] = None
    description: Optional[str] = None

class InvoicesResponse(BaseModel):
    invoices: List[Invoice]
    message: str

class TrialRequest(BaseModel):
    plan_tier: str
    email: str
    mobile_phone: str
    full_name: str

class TrialResponse(BaseModel):
    success: bool
    message: str
    trial_end: Optional[str] = None
