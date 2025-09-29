#!/usr/bin/env python3
"""
Environment Variables Setup Script for CustomerCareGPT
This script helps you set up all required environment variables for deployment
"""

import os
import secrets
import string
import json
from typing import Dict, List, Any

class EnvironmentSetup:
    """Setup environment variables for CustomerCareGPT"""
    
    def __init__(self):
        self.backend_vars = {}
        self.frontend_vars = {}
        self.required_vars = {}
        self.optional_vars = {}
        
    def generate_secret_key(self, length: int = 64) -> str:
        """Generate a secure secret key"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_jwt_secret(self, length: int = 64) -> str:
        """Generate a secure JWT secret"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def generate_password(self, length: int = 32) -> str:
        """Generate a secure password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def setup_backend_variables(self):
        """Setup backend environment variables"""
        print("🔧 Setting up Backend Environment Variables...")
        
        # Required variables
        self.required_vars = {
            # Database
            "DATABASE_URL": "postgresql+psycopg2://user:password@host:5432/customercaregpt",
            "POSTGRES_DB": "customercaregpt",
            "POSTGRES_USER": "customercaregpt",
            "POSTGRES_PASSWORD": self.generate_password(32),
            
            # Redis
            "REDIS_URL": "redis://customercaregpt-redis.xxxxx.cache.amazonaws.com:6379",
            "REDIS_PASSWORD": self.generate_password(32),
            
            # ChromaDB
            "CHROMA_URL": "https://customercaregpt-chromadb-xxxxx-uc.a.run.app",
            "CHROMA_AUTH_CREDENTIALS": self.generate_password(32),
            
            # Security
            "SECRET_KEY": self.generate_secret_key(64),
            "JWT_SECRET": self.generate_jwt_secret(64),
            "ALGORITHM": "HS256",
            
            # AI
            "GEMINI_API_KEY": "your-gemini-api-key-here",
            
            # Stripe
            "STRIPE_API_KEY": "sk_test_your_stripe_api_key_here",
            "STRIPE_WEBHOOK_SECRET": "whsec_your_webhook_secret_here",
            "STRIPE_STARTER_PRICE_ID": "price_starter",
            "STRIPE_PRO_PRICE_ID": "price_pro",
            "STRIPE_ENTERPRISE_PRICE_ID": "price_enterprise",
            "STRIPE_WHITE_LABEL_PRICE_ID": "price_white_label",
            
            # Application
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
            "PUBLIC_BASE_URL": "https://customercaregpt-backend-xxxxx-uc.a.run.app",
            "API_BASE_URL": "https://customercaregpt-backend-xxxxx-uc.a.run.app",
            
            # CORS
            "CORS_ORIGINS": "https://customercaregpt-frontend.vercel.app,https://customercaregpt-frontend-git-main.vercel.app",
            "ALLOWED_HOSTS": "customercaregpt-backend-xxxxx-uc.a.run.app,customercaregpt-frontend.vercel.app",
            
            # Email
            "EMAIL_PROVIDER": "ses",
            "SES_FROM_EMAIL": "noreply@customercaregpt.com",
            
            # Secrets
            "SECRETS_PROVIDER": "env",
        }
        
        # Optional variables with defaults
        self.optional_vars = {
            # Database Pool
            "DB_POOL_SIZE": "50",
            "DB_MAX_OVERFLOW": "30",
            "DB_POOL_TIMEOUT": "60",
            "DB_POOL_RECYCLE": "1800",
            
            # Redis Pool
            "REDIS_MAX_CONNECTIONS": "100",
            "REDIS_RETRY_ON_TIMEOUT": "true",
            "REDIS_SOCKET_KEEPALIVE": "true",
            "RQ_QUEUE_NAME": "default",
            
            # Security
            "PASSWORD_MIN_LENGTH": "12",
            "PASSWORD_REQUIRE_UPPERCASE": "true",
            "PASSWORD_REQUIRE_LOWERCASE": "true",
            "PASSWORD_REQUIRE_NUMBERS": "true",
            "PASSWORD_REQUIRE_SPECIAL_CHARS": "true",
            "PASSWORD_HISTORY_COUNT": "5",
            "MAX_LOGIN_ATTEMPTS": "5",
            "LOCKOUT_DURATION_MINUTES": "15",
            "SESSION_TIMEOUT_MINUTES": "30",
            "REQUIRE_EMAIL_VERIFICATION": "true",
            "REQUIRE_PHONE_VERIFICATION": "true",
            
            # JWT
            "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
            "REFRESH_TOKEN_EXPIRE_DAYS": "7",
            "JWT_ISSUER": "customercaregpt",
            "JWT_AUDIENCE": "customercaregpt-users",
            
            # ChromaDB
            "CHROMA_PERSIST_DIRECTORY": "/chroma/chroma",
            "CHROMA_SETTINGS": '{"anonymized_telemetry": false}',
            
            # Stripe
            "STRIPE_SUCCESS_URL": "https://customercaregpt-frontend.vercel.app/billing/success",
            "STRIPE_CANCEL_URL": "https://customercaregpt-frontend.vercel.app/billing/cancel",
            "BILLING_DEFAULT_TIER": "starter",
            
            # File Upload
            "MAX_FILE_SIZE": "10485760",
            "ALLOWED_FILE_TYPES": "application/pdf,text/plain,text/markdown",
            "UPLOAD_DIR": "uploads",
            
            # Rate Limiting
            "RATE_LIMIT_REQUESTS": "60",
            "RATE_LIMIT_WINDOW": "60",
            "RATE_LIMIT_WORKSPACE_PER_MIN": "100",
            "RATE_LIMIT_EMBED_PER_MIN": "60",
            
            # Security Headers
            "ENABLE_SECURITY_HEADERS": "true",
            "ENABLE_CSP": "true",
            "ENABLE_HSTS": "true",
            "ENABLE_RATE_LIMITING": "true",
            "ENABLE_INPUT_VALIDATION": "true",
            "ENABLE_REQUEST_LOGGING": "true",
            "ENABLE_CORS": "true",
            
            # Monitoring
            "PROMETHEUS_ENABLED": "true",
            "METRICS_ENABLED": "true",
            "HEALTH_CHECK_ENABLED": "true",
            
            # Vector Search
            "VECTOR_SEARCH_DEFAULT_TOP_K": "5",
            "VECTOR_SEARCH_SIMILARITY_THRESHOLD": "0.7",
            "VECTOR_SEARCH_CACHE_TTL": "3600",
            
            # RAG
            "RAG_DEFAULT_TOP_K": "6",
            "RAG_MAX_CONTEXT_LENGTH": "4000",
            "RAG_CONFIDENCE_THRESHOLD": "0.5",
            
            # Chat
            "CHAT_MAX_MESSAGES": "50",
            "CHAT_SESSION_TIMEOUT": "3600",
            "CHAT_TYPING_INDICATOR_DELAY": "1000",
            
            # Widget
            "WIDGET_DEFAULT_TITLE": "Customer Support",
            "WIDGET_DEFAULT_PLACEHOLDER": "Ask me anything...",
            "WIDGET_DEFAULT_WELCOME_MESSAGE": "Hello! How can I help you today?",
            "WIDGET_DEFAULT_PRIMARY_COLOR": "#4f46e5",
            "WIDGET_DEFAULT_SECONDARY_COLOR": "#f8f9fa",
            "WIDGET_DEFAULT_TEXT_COLOR": "#111111",
            "WIDGET_DEFAULT_POSITION": "bottom-right",
            "WIDGET_DEFAULT_MAX_MESSAGES": "50",
            "WIDGET_DEFAULT_Z_INDEX": "10000",
            
            # WebSocket
            "WEBSOCKET_MAX_CONNECTIONS": "1000",
            "WEBSOCKET_PING_INTERVAL": "30",
            "WEBSOCKET_PING_TIMEOUT": "10",
            "WEBSOCKET_MAX_RECONNECT_ATTEMPTS": "5",
            
            # Language
            "DEFAULT_LANGUAGE": "en",
            "SUPPORTED_LANGUAGES": "en,es,fr,de,it,pt,ru,zh,ja,ko",
            "AUTO_DETECT_LANGUAGE": "true",
            
            # Analytics
            "ANALYTICS_ENABLED": "true",
            "ANALYTICS_RETENTION_DAYS": "90",
            "ANALYTICS_BATCH_SIZE": "100",
            
            # A/B Testing
            "AB_TESTING_ENABLED": "true",
            "AB_TESTING_DEFAULT_TRAFFIC_SPLIT": "0.5",
        }
        
        # Combine all variables
        self.backend_vars = {**self.required_vars, **self.optional_vars}
        
        print(f"✅ Generated {len(self.required_vars)} required variables")
        print(f"✅ Generated {len(self.optional_vars)} optional variables")
    
    def setup_frontend_variables(self):
        """Setup frontend environment variables"""
        print("🌐 Setting up Frontend Environment Variables...")
        
        self.frontend_vars = {
            # Required
            "VITE_API_URL": "https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1",
            "VITE_WS_URL": "wss://customercaregpt-backend-xxxxx-uc.a.run.app/ws",
            
            # Optional
            "VITE_ANALYTICS_ID": "your-analytics-id",
            "VITE_SENTRY_DSN": "your-sentry-dsn",
            "VITE_DEMO_MODE": "false",
        }
        
        print(f"✅ Generated {len(self.frontend_vars)} frontend variables")
    
    def create_env_files(self):
        """Create environment files"""
        print("📁 Creating Environment Files...")
        
        # Create backend .env file
        with open(".env", "w") as f:
            f.write("# CustomerCareGPT Backend Environment Variables\n")
            f.write("# Generated by setup_env.py\n\n")
            
            f.write("# ============================================\n")
            f.write("# REQUIRED VARIABLES - MUST BE SET\n")
            f.write("# ============================================\n\n")
            
            for key, value in self.required_vars.items():
                f.write(f"{key}={value}\n")
            
            f.write("\n# ============================================\n")
            f.write("# OPTIONAL VARIABLES - DEFAULTS PROVIDED\n")
            f.write("# ============================================\n\n")
            
            for key, value in self.optional_vars.items():
                f.write(f"{key}={value}\n")
        
        # Create frontend .env.local file
        os.makedirs("frontend", exist_ok=True)
        with open("frontend/.env.local", "w") as f:
            f.write("# CustomerCareGPT Frontend Environment Variables\n")
            f.write("# Generated by setup_env.py\n\n")
            
            for key, value in self.frontend_vars.items():
                f.write(f"{key}={value}\n")
        
        print("✅ Created .env file for backend")
        print("✅ Created frontend/.env.local file for frontend")
    
    def create_vercel_env_file(self):
        """Create Vercel environment file"""
        print("🚀 Creating Vercel Environment File...")
        
        with open("frontend/vercel-env.json", "w") as f:
            vercel_env = {
                "env": {
                    "VITE_API_URL": self.frontend_vars["VITE_API_URL"],
                    "VITE_WS_URL": self.frontend_vars["VITE_WS_URL"]
                },
                "build": {
                    "env": {
                        "VITE_API_URL": self.frontend_vars["VITE_API_URL"],
                        "VITE_WS_URL": self.frontend_vars["VITE_WS_URL"]
                    }
                }
            }
            json.dump(vercel_env, f, indent=2)
        
        print("✅ Created frontend/vercel-env.json")
    
    def create_gcp_env_file(self):
        """Create Google Cloud Run environment file"""
        print("☁️ Creating Google Cloud Run Environment File...")
        
        with open("gcp-env.yaml", "w") as f:
            f.write("# Google Cloud Run Environment Variables\n")
            f.write("# Generated by setup_env.py\n\n")
            f.write("env:\n")
            
            for key, value in self.required_vars.items():
                f.write(f"  - name: {key}\n")
                f.write(f"    value: \"{value}\"\n")
        
        print("✅ Created gcp-env.yaml")
    
    def print_setup_instructions(self):
        """Print setup instructions"""
        print("\n" + "="*60)
        print("🎉 Environment Variables Setup Complete!")
        print("="*60)
        
        print("\n📋 Next Steps:")
        print("1. Update the placeholder values in .env file:")
        print("   - Replace 'your-gemini-api-key-here' with your actual Gemini API key")
        print("   - Replace 'sk_test_your_stripe_api_key_here' with your actual Stripe API key")
        print("   - Replace 'whsec_your_webhook_secret_here' with your actual Stripe webhook secret")
        print("   - Update database URLs with your actual database connection strings")
        print("   - Update Redis URLs with your actual Redis connection strings")
        print("   - Update ChromaDB URLs with your actual ChromaDB connection strings")
        
        print("\n2. For Vercel deployment:")
        print("   - Set environment variables in Vercel dashboard")
        print("   - Or use: vercel env add VITE_API_URL production")
        print("   - Or use: vercel env add VITE_WS_URL production")
        
        print("\n3. For Google Cloud Run deployment:")
        print("   - Set environment variables in Cloud Run service")
        print("   - Or use: gcloud run services update customercaregpt-backend --set-env-vars-from-file=gcp-env.yaml")
        
        print("\n4. Test your setup:")
        print("   - Run: python debug_deployment.py")
        print("   - Check: https://your-backend-url.run.app/debug/health")
        
        print("\n🔒 Security Notes:")
        print("- All secret keys and passwords have been generated securely")
        print("- Update placeholder values with your actual API keys")
        print("- Never commit .env files to version control")
        print("- Use different values for development and production")
        
        print("\n📚 Documentation:")
        print("- See COMPREHENSIVE_ENV_ANALYSIS.md for detailed explanations")
        print("- See vercel-debugging-guide.md for debugging help")
    
    def run(self):
        """Run the complete setup"""
        print("🚀 CustomerCareGPT Environment Variables Setup")
        print("="*50)
        
        self.setup_backend_variables()
        self.setup_frontend_variables()
        self.create_env_files()
        self.create_vercel_env_file()
        self.create_gcp_env_file()
        self.print_setup_instructions()

if __name__ == "__main__":
    setup = EnvironmentSetup()
    setup.run()
