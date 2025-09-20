from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.core.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id"), nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    tier = Column(String, nullable=False)  # 'starter', 'pro', 'white_label'
    status = Column(String, nullable=False)  # 'active', 'past_due', 'canceled', 'trialing', 'unpaid'
    seats = Column(Integer, default=1)
    monthly_query_quota = Column(BigInteger, nullable=True)  # NULL for unlimited
    queries_this_period = Column(BigInteger, default=0)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    next_billing_at = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(id={self.id}, workspace_id={self.workspace_id}, tier={self.tier}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status in ['active', 'trialing']

    @property
    def is_quota_exceeded(self) -> bool:
        """Check if monthly query quota has been exceeded"""
        if self.monthly_query_quota is None:
            return False  # Unlimited
        return self.queries_this_period >= self.monthly_query_quota

    @property
    def quota_usage_percentage(self) -> float:
        """Get quota usage as percentage"""
        if self.monthly_query_quota is None or self.monthly_query_quota == 0:
            return 0.0
        return (self.queries_this_period / self.monthly_query_quota) * 100

    @property
    def remaining_queries(self) -> int:
        """Get remaining queries in current period"""
        if self.monthly_query_quota is None:
            return -1  # Unlimited
        return max(0, self.monthly_query_quota - self.queries_this_period)

    def increment_usage(self, amount: int = 1) -> bool:
        """Increment query usage. Returns True if successful, False if quota exceeded"""
        if self.is_quota_exceeded:
            return False
        
        if self.monthly_query_quota is not None:
            if self.queries_this_period + amount > self.monthly_query_quota:
                return False
        
        self.queries_this_period += amount
        return True

    def reset_period_usage(self):
        """Reset usage for new billing period"""
        self.queries_this_period = 0
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "stripe_customer_id": self.stripe_customer_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "tier": self.tier,
            "status": self.status,
            "seats": self.seats,
            "monthly_query_quota": self.monthly_query_quota,
            "queries_this_period": self.queries_this_period,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "next_billing_at": self.next_billing_at.isoformat() if self.next_billing_at else None,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
            "is_quota_exceeded": self.is_quota_exceeded,
            "quota_usage_percentage": self.quota_usage_percentage,
            "remaining_queries": self.remaining_queries
        }
