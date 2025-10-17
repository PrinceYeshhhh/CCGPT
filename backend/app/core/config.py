"""
Application configuration settings
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Union
import os
from pathlib import Path
from dotenv import load_dotenv

# Preload environment files for local/dev setups before Settings() is instantiated.
# Order of precedence: .env.local, .env, local.env (all optional)
if os.getenv("ENVIRONMENT", "development").lower() not in ["production", "staging", "testing", "test"]:
    try:
        backend_root = Path(__file__).resolve().parents[2]
        for candidate in [backend_root / ".env.local", backend_root / ".env", backend_root / "local.env"]:
            if candidate.exists():
                load_dotenv(dotenv_path=str(candidate), override=False)
    except Exception:
        # Do not fail settings import if dotenv loading has issues
        pass

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = ""  # Must be set via environment variable
    POSTGRES_DB: str = "customercaregpt"
    POSTGRES_USER: str = "customercaregpt"
    POSTGRES_PASSWORD: str = ""  # Must be set via environment variable
    
    # Database Pool Configuration
    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 60
    DB_POOL_RECYCLE: int = 1800
    
    # Read Replica URLs (for scaling)
    READ_REPLICA_URLS: List[str] = []
    
    # Redis Configuration
    REDIS_URL: str = ""  # Must be set via environment variable
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
    SECRET_KEY: str = ""  # Must be set via environment variable
    JWT_SECRET: str = ""  # Must be set via environment variable
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
    CHROMA_URL: str = ""  # Must be set via environment variable
    CHROMA_PERSIST_DIRECTORY: str = "/tmp/chroma_test" if os.getenv("TESTING") == "true" else "/chroma/chroma"
    CHROMA_AUTH_CREDENTIALS: str = ""
    
    # Stripe Configuration
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_SUCCESS_URL: str = ""  # Must be set via environment variable
    STRIPE_CANCEL_URL: str = ""  # Must be set via environment variable
    BILLING_DEFAULT_TIER: str = "starter"
    
    # Stripe Price IDs
    STRIPE_STARTER_PRICE_ID: str = ""
    STRIPE_PRO_PRICE_ID: str = ""
    STRIPE_ENTERPRISE_PRICE_ID: str = ""
    
    # Email Provider
    EMAIL_PROVIDER: str = "ses"  # or "sendgrid"
    FROM_EMAIL: str = "noreply@customercaregpt.com"
    SES_FROM_EMAIL: str = ""  # Legacy; fallback to FROM_EMAIL
    SENDGRID_API_KEY: str = ""
    PUBLIC_BASE_URL: str = ""  # Must be set via environment variable
    
    # Storage Configuration
    USE_S3: bool = False
    USE_GCS: bool = False
    UPLOAD_DIR: str = "uploads"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = ""
    GCS_BUCKET_NAME: str = ""
    STRIPE_WHITE_LABEL_PRICE_ID: str = ""
    
    # Application
    DEBUG: bool = False  # Default to False for security
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"  # Default to INFO for production
    CORS_ORIGINS: Union[List[str], str] = []  # Must be set via environment variable
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = [
        "Authorization",
        "Content-Type",
        "X-Client-API-Key",
        "X-Embed-Code-ID",
        "X-Workspace-ID",
        "X-Requested-With",
        "X-Client-Version",
        "X-CSRF-Token",
        "Origin",
        "Referer"
    ]
    ALLOWED_HOSTS: Union[List[str], str] = []  # Must be set via environment variable
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True
    ENABLE_CSP: bool = True
    ENABLE_HSTS: bool = True
    
    # Monitoring
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = True
    METRICS_ENABLED: bool = True
    
    # Backup Configuration
    BACKUP_DIR: str = "/app/backups"
    USE_S3_BACKUP: bool = False
    S3_BACKUP_BUCKET: str = ""
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_SCHEDULER_ENABLED: bool = True
    HEALTH_CHECK_ENABLED: bool = True
    
    # Vector Cache Configuration
    VECTOR_CACHE_TTL: int = 600
    VECTOR_CACHE_MAX_SIZE: int = 1000
    
    # Chunking Configuration
    MAX_CHUNK_TOKENS: int = 512
    CHUNK_OVERLAP_TOKENS: int = 50
    
    # Production Security Flags
    ENABLE_RATE_LIMITING: bool = True
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
    API_BASE_URL: str = ""  # Must be set via environment variable
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
    ADMIN_EMAIL: str = "admin@customercaregpt.com"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Apply environment-aware defaults
        self.apply_environment_defaults()
        # Validate production secrets
        self.validate_production_secrets()

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

    def get_environment_aware_defaults(self) -> dict:
        """Get environment-aware default values"""
        is_production = self.ENVIRONMENT.lower() in ["production", "staging"]
        
        defaults = {}
        
        if not is_production:
            # Development defaults
            defaults.update({
                "DATABASE_URL": "sqlite:///./dev.db",
                "REDIS_URL": "redis://localhost:6379",
                "CHROMA_URL": "http://localhost:8001",
                "PUBLIC_BASE_URL": "http://localhost:8000",
                "API_BASE_URL": "http://localhost:8000",
                "STRIPE_SUCCESS_URL": "http://localhost:3000/billing/success",
                "STRIPE_CANCEL_URL": "http://localhost:3000/billing/cancel",
                "CORS_ORIGINS": ["http://localhost:3000", "http://localhost:3001"],
                "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
                "DEBUG": True,
                "LOG_LEVEL": "DEBUG"
            })
        else:
            # Production defaults
            defaults.update({
                "DEBUG": False,
                "LOG_LEVEL": "INFO",
                "ENABLE_SECURITY_HEADERS": True,
                "ENABLE_RATE_LIMITING": True,
                "ENABLE_INPUT_VALIDATION": True,
                "ENABLE_REQUEST_LOGGING": True,
                "PROMETHEUS_ENABLED": True,
                "METRICS_ENABLED": True,
                "HEALTH_CHECK_ENABLED": True
            })
        
        return defaults
    
    # Normalize boolean environment variables that may arrive as strings
    @field_validator(
        "USE_S3",
        "USE_GCS",
        "USE_S3_BACKUP",
        "PROMETHEUS_ENABLED",
        "METRICS_ENABLED",
        "HEALTH_CHECK_ENABLED",
        "DEBUG",
        "ENABLE_SECURITY_HEADERS",
        "ENABLE_RATE_LIMITING",
        "ENABLE_INPUT_VALIDATION",
        "ENABLE_REQUEST_LOGGING",
        "ENABLE_CORS",
        mode="before",
    )
    @classmethod
    def _coerce_bool_env(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return value
        if isinstance(value, str):
            normalized = value.strip().strip('"').strip("'").lower()
            if normalized in {"true", "1", "yes", "y", "on"}:
                return True
            if normalized in {"false", "0", "no", "n", "off", ""}:
                return False
        return value

    def apply_environment_defaults(self) -> None:
        """Apply environment-aware defaults to unset values"""
        defaults = self.get_environment_aware_defaults()
        
        for key, value in defaults.items():
            if hasattr(self, key) and not getattr(self, key):
                setattr(self, key, value)
    
    def validate_production_secrets(self) -> None:
        """Validate that critical secrets are set for production deployment"""
        if self.ENVIRONMENT.lower() in ["production", "staging"]:
            critical_secrets = [
                ("SECRET_KEY", self.SECRET_KEY),
                ("JWT_SECRET", self.JWT_SECRET),
                ("DATABASE_URL", self.DATABASE_URL),
                ("REDIS_URL", self.REDIS_URL),
                ("GEMINI_API_KEY", self.GEMINI_API_KEY),
                ("PUBLIC_BASE_URL", self.PUBLIC_BASE_URL),
                ("API_BASE_URL", self.API_BASE_URL),
            ]
            
            missing_secrets = []
            for name, value in critical_secrets:
                if not value or value in ["", "your-secret-key-here-change-in-production", "your-jwt-secret-key-here-change-in-production"]:
                    missing_secrets.append(name)
            
            if missing_secrets:
                raise ValueError(
                    f"Critical secrets not set for {self.ENVIRONMENT} environment: {', '.join(missing_secrets)}. "
                    "Please set these environment variables before starting the application."
                )
            
            # Validate CORS origins are set for production
            if not self.CORS_ORIGINS:
                raise ValueError(
                    f"CORS_ORIGINS must be set for {self.ENVIRONMENT} environment. "
                    "This is required for security."
                )
            
            # Validate allowed hosts are set for production
            if not self.ALLOWED_HOSTS:
                raise ValueError(
                    f"ALLOWED_HOSTS must be set for {self.ENVIRONMENT} environment. "
                    "This is required for security."
                )

    def __post_init__(self):
        """Run validation after initialization"""
        self.validate_production_secrets()

# Global settings instance
settings = Settings()