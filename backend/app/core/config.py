"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./dev.db"
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
    
    # JWT Security Configuration
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    JWT_SECRET: str = "your-jwt-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Reduced for security
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "customercaregpt"
    JWT_AUDIENCE: str = "customercaregpt-users"
    ENCRYPTION_KEY: Optional[str] = None
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
    PASSWORD_HISTORY_COUNT: int = 5  # Prevent password reuse
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    SESSION_TIMEOUT_MINUTES: int = 30
    REQUIRE_EMAIL_VERIFICATION: bool = True
    REQUIRE_PHONE_VERIFICATION: bool = True
    
    # Google Gemini
    GEMINI_API_KEY: str = ""
    
    # ChromaDB Configuration
    CHROMA_URL: str = "http://localhost:8001"
    CHROMA_PERSIST_DIRECTORY: str = "/chroma/chroma"
    CHROMA_AUTH_CREDENTIALS: str = ""
    
    # Stripe Configuration
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = "http://localhost:3000/billing/success"
    STRIPE_CANCEL_URL: str = "http://localhost:3000/billing/cancel"
    BILLING_DEFAULT_TIER: str = "starter"
    
    # Stripe Price IDs
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""
    
    # Email Provider
    EMAIL_PROVIDER: str = "ses"  # or "sendgrid"
    SES_FROM_EMAIL: str = ""
    SENDGRID_API_KEY: str = ""
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    
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
    LOG_LEVEL: str = "DEBUG"
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = [
        "Authorization", "Content-Type", "X-Client-API-Key", 
        "X-Embed-Code-ID", "X-Workspace-ID", "Origin", "Referer"
    ]
    ALLOWED_HOSTS: Union[List[str], str] = ["localhost", "127.0.0.1", "0.0.0.0", "testserver"]
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_CSP: bool = True
    ENABLE_HSTS: bool = True
    
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
    RATE_LIMIT_WORKSPACE_PER_MIN: int = 100
    RATE_LIMIT_EMBED_PER_MIN: int = 60
    
    # Token Budget
    DAILY_TOKEN_LIMIT: int = 10000
    MONTHLY_TOKEN_LIMIT: int = 100000
    
    # Embedding Configuration
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 32
    EMBEDDING_CACHE_SIZE: int = 1000
    
    # Vector Search Configuration
    VECTOR_SEARCH_DEFAULT_TOP_K: int = 5
    VECTOR_SEARCH_SIMILARITY_THRESHOLD: float = 0.7
    VECTOR_SEARCH_CACHE_TTL: int = 3600
    
    # RAG Configuration
    RAG_DEFAULT_TOP_K: int = 6
    RAG_MAX_CONTEXT_LENGTH: int = 4000
    RAG_CONFIDENCE_THRESHOLD: float = 0.5
    
    # Chat Configuration
    CHAT_MAX_MESSAGES: int = 50
    CHAT_SESSION_TIMEOUT: int = 3600  # 1 hour
    CHAT_TYPING_INDICATOR_DELAY: int = 1000  # 1 second
    
    # Widget Configuration
    WIDGET_DEFAULT_TITLE: str = "Customer Support"
    WIDGET_DEFAULT_PLACEHOLDER: str = "Ask me anything..."
    WIDGET_DEFAULT_WELCOME_MESSAGE: str = "Hello! How can I help you today?"
    WIDGET_DEFAULT_PRIMARY_COLOR: str = "#4f46e5"
    WIDGET_DEFAULT_SECONDARY_COLOR: str = "#f8f9fa"
    WIDGET_DEFAULT_TEXT_COLOR: str = "#111111"
    WIDGET_DEFAULT_POSITION: str = "bottom-right"
    WIDGET_DEFAULT_MAX_MESSAGES: int = 50
    WIDGET_DEFAULT_Z_INDEX: int = 10000
    
    # WebSocket Configuration
    WEBSOCKET_MAX_CONNECTIONS: int = 1000
    WEBSOCKET_PING_INTERVAL: int = 30
    WEBSOCKET_PING_TIMEOUT: int = 10
    WEBSOCKET_MAX_RECONNECT_ATTEMPTS: int = 5
    
    # API Configuration
    API_BASE_URL: str = "http://localhost:8000"
    API_V1_PREFIX: str = "/api/v1"
    
    # Multi-language Support
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGES: List[str] = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]
    AUTO_DETECT_LANGUAGE: bool = True
    
    # Analytics Configuration
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_RETENTION_DAYS: int = 90
    ANALYTICS_BATCH_SIZE: int = 100
    
    # A/B Testing Configuration
    AB_TESTING_ENABLED: bool = True
    AB_TESTING_DEFAULT_TRAFFIC_SPLIT: float = 0.5
    
    # SMS/OTP Provider
    SMS_PROVIDER: str = "twilio"  # or "sns"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""
    AWS_SNS_REGION: str = "us-east-1"
    
    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@customercaregpt.com"
    ADMIN_EMAIL: str = "admin@customercaregpt.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    # Accept comma-separated strings or JSON arrays for list settings
    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def _parse_csv_or_json_list(cls, value):
        if isinstance(value, str):
            v = value.strip()
            if v.startswith("["):
                try:
                    import json
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
            # Fallback to comma-separated parsing
            return [item.strip() for item in v.split(",") if item.strip()]
        return value

# Global settings instance
settings = Settings()