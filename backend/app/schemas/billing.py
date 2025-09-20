from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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

class CheckoutRequest(BaseModel):
    plan: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CheckoutResponse(BaseModel):
    checkout_url: str
    plan: str
    message: str

class Invoice(BaseModel):
    id: str
    amount: int  # in cents
    currency: str
    status: str
    created: datetime
    invoice_pdf: Optional[str] = None

class InvoicesResponse(BaseModel):
    invoices: list[Invoice]
    message: str
