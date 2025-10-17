"""
Standardized plan limits and validation utilities
"""

from typing import Dict, Any, Optional
from enum import Enum

class PlanTier(str, Enum):
    FREE = "free"
    FREE_TRIAL = "free_trial"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    WHITE_LABEL = "white_label"

class PlanLimits:
    """Standardized plan limits across the application"""
    
    # Query limits per month
    QUERY_LIMITS = {
        PlanTier.FREE: 0,  # Free tier has no queries
        PlanTier.FREE_TRIAL: 100,
        PlanTier.STARTER: 7000,
        PlanTier.PRO: 50000,
        PlanTier.ENTERPRISE: -1,  # Unlimited
        PlanTier.WHITE_LABEL: -1,  # Unlimited
    }
    
    # Document limits
    DOCUMENT_LIMITS = {
        PlanTier.FREE: 0,  # Free tier has no documents
        PlanTier.FREE_TRIAL: 1,
        PlanTier.STARTER: 5,
        PlanTier.PRO: 25,
        PlanTier.ENTERPRISE: -1,  # Unlimited
        PlanTier.WHITE_LABEL: -1,  # Unlimited
    }
    
    # Storage limits in bytes
    STORAGE_LIMITS = {
        PlanTier.FREE: 0,  # Free tier has no storage
        PlanTier.FREE_TRIAL: 10 * 1024 * 1024,  # 10MB
        PlanTier.STARTER: 100 * 1024 * 1024,  # 100MB
        PlanTier.PRO: 500 * 1024 * 1024,  # 500MB
        PlanTier.ENTERPRISE: 10 * 1024 * 1024 * 1024,  # 10GB
        PlanTier.WHITE_LABEL: -1,  # Unlimited
    }
    
    # API rate limits (requests per minute)
    RATE_LIMITS = {
        PlanTier.FREE: 0,  # Free tier has no API access
        PlanTier.FREE_TRIAL: 10,
        PlanTier.STARTER: 60,
        PlanTier.PRO: 300,
        PlanTier.ENTERPRISE: 1000,
        PlanTier.WHITE_LABEL: 1000,
    }
    
    @classmethod
    def get_limits(cls, plan_tier: str) -> Dict[str, Any]:
        """Get all limits for a plan tier"""
        tier = PlanTier(plan_tier) if plan_tier in [t.value for t in PlanTier] else PlanTier.FREE
        
        # Tests expect canonical keys like max_documents, max_storage_bytes, max_requests_per_minute
        return {
            "max_queries_per_month": cls.QUERY_LIMITS[tier],
            "max_documents": cls.DOCUMENT_LIMITS[tier],
            "max_storage_bytes": cls.STORAGE_LIMITS[tier],
            "max_requests_per_minute": cls.RATE_LIMITS[tier],
            "is_unlimited": cls.QUERY_LIMITS[tier] == -1
        }
    
    @classmethod
    def check_query_limit(cls, plan_tier: str, current_usage: int) -> bool:
        """Check if query limit is exceeded"""
        limit = cls.QUERY_LIMITS.get(PlanTier(plan_tier), cls.QUERY_LIMITS[PlanTier.FREE])
        return limit == -1 or current_usage < limit
    
    @classmethod
    def check_document_limit(cls, plan_tier: str, current_count: int) -> bool:
        """Check if document limit is exceeded"""
        limit = cls.DOCUMENT_LIMITS.get(PlanTier(plan_tier), cls.DOCUMENT_LIMITS[PlanTier.FREE])
        return limit == -1 or current_count < limit
    
    @classmethod
    def check_storage_limit(cls, plan_tier: str, current_usage: int) -> bool:
        """Check if storage limit is exceeded"""
        limit = cls.STORAGE_LIMITS.get(PlanTier(plan_tier), cls.STORAGE_LIMITS[PlanTier.FREE])
        return limit == -1 or current_usage < limit
    
    @classmethod
    def get_remaining_queries(cls, plan_tier: str, current_usage: int) -> int:
        """Get remaining queries for a plan"""
        limit = cls.QUERY_LIMITS.get(PlanTier(plan_tier), cls.QUERY_LIMITS[PlanTier.FREE])
        if limit == -1:
            return -1  # Unlimited
        return max(0, limit - current_usage)
    
    @classmethod
    def get_remaining_documents(cls, plan_tier: str, current_count: int) -> int:
        """Get remaining documents for a plan"""
        limit = cls.DOCUMENT_LIMITS.get(PlanTier(plan_tier), cls.DOCUMENT_LIMITS[PlanTier.FREE])
        if limit == -1:
            return -1  # Unlimited
        return max(0, limit - current_count)
    
    @classmethod
    def get_remaining_storage(cls, plan_tier: str, current_usage: int) -> int:
        """Get remaining storage for a plan"""
        limit = cls.STORAGE_LIMITS.get(PlanTier(plan_tier), cls.STORAGE_LIMITS[PlanTier.FREE])
        if limit == -1:
            return -1  # Unlimited
        return max(0, limit - current_usage)
