"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/customercaregpt"
    POSTGRES_DB: str = "customercaregpt"
    POSTGRES_USER: str = "customercaregpt"
    POSTGRES_PASSWORD: str = "secure-password"
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 60
    DB_POOL_RECYCLE: int = 1800
    
    # Read Replica URLs (for scaling)
    READ_REPLICA_URLS: List[str] = []
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: str = ""
    REDIS_MAX_CONNECTIONS: int = 100
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_SOCKET_KEEPALIVE: bool = True
    RQ_QUEUE_NAME: str = "default"
    
    # Queue Configuration
    HIGH_PRIORITY_QUEUE: str = "high_priority"
    NORMAL_QUEUE: str = "normal"
    LOW_PRIORITY_QUEUE: str = "low_priority"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here"
    JWT_SECRET: str = "your-jwt-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google Gemini
    GEMINI_API_KEY: str = ""
    
    # ChromaDB Configuration
    CHROMA_URL: str = "http://localhost:8001"
    CHROMA_PERSIST_DIRECTORY: str = "/chroma/chroma"
    CHROMA_AUTH_CREDENTIALS: str = ""
    
    # Stripe Configuration
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = "https://your-frontend.com/billing/success"
    STRIPE_CANCEL_URL: str = "https://your-frontend.com/billing/cancel"
    BILLING_DEFAULT_TIER: str = "starter"
    
    # Stripe Price IDs
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""
    
    # Storage Configuration
    USE_S3: bool = False
    UPLOAD_DIR: str = "uploads"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = ""
    STRIPE_WHITE_LABEL_PRICE_ID: str = ""
    
    # Application
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Monitoring
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = True
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_ENABLED: bool = True
    
    # Vector Cache Configuration
    VECTOR_CACHE_TTL: int = 600
    VECTOR_CACHE_MAX_SIZE: int = 1000
    
    # Production Security Flags
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_INPUT_VALIDATION: bool = True
    ENABLE_REQUEST_LOGGING: bool = True
    ENABLE_CORS: bool = True
    
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