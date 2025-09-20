"""
Application configuration settings
"""

from pydantic import BaseSettings
from typing import List, Optional
import os
from .secrets import secrets_manager

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = secrets_manager.get_database_url() or "postgresql://user:password@localhost:5432/customercaregpt"
    
    # Redis
    REDIS_URL: str = secrets_manager.get_redis_url() or "redis://localhost:6379"
    
    # JWT
    SECRET_KEY: str = secrets_manager.get_jwt_secret() or "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google Gemini
    GEMINI_API_KEY: str = secrets_manager.get_api_key("gemini") or ""
    
    # Stripe Configuration
    STRIPE_API_KEY: str = secrets_manager.get_stripe_config().get("api_key", "")
    STRIPE_WEBHOOK_SECRET: str = secrets_manager.get_stripe_config().get("webhook_secret", "")
    STRIPE_SUCCESS_URL: str = "https://your-frontend.com/billing/success"
    STRIPE_CANCEL_URL: str = "https://your-frontend.com/billing/cancel"
    BILLING_DEFAULT_TIER: str = "starter"
    
    # Stripe Price IDs
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""
    STRIPE_WHITE_LABEL_PRICE_ID: str = ""
    
    # Application
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Monitoring
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = True
    
    # File Upload
    MAX_FILE_SIZE: int = 10485760  # 10MB
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf", "text/plain", "text/markdown"]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Token Budget
    DAILY_TOKEN_LIMIT: int = 10000
    MONTHLY_TOKEN_LIMIT: int = 100000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()