# 🔧 Comprehensive Environment Variables Analysis

## Overview
This document provides a complete analysis of ALL environment variables needed for CustomerCareGPT deployment across Frontend, Backend, Database, LLM, and all services.

## 📊 Environment Variables by Category

### **1. 🗄️ Database Configuration**

#### **PostgreSQL (Primary Database)**
```bash
# Required
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/customercaregpt
POSTGRES_DB=customercaregpt
POSTGRES_USER=customercaregpt
POSTGRES_PASSWORD=secure-password

# Optional (for scaling)
READ_REPLICA_URLS=postgresql://user:pass@postgres-read:5432/customercaregpt

# Database Pool Configuration
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=60
DB_POOL_RECYCLE=1800
```

#### **Redis (Cache & Queue)**
```bash
# Required
REDIS_URL=redis://customercaregpt-redis.xxxxx.cache.amazonaws.com:6379
REDIS_PASSWORD=secure-redis-password

# Optional
REDIS_MAX_CONNECTIONS=100
REDIS_RETRY_ON_TIMEOUT=true
REDIS_SOCKET_KEEPALIVE=true
RQ_QUEUE_NAME=default
```

#### **ChromaDB (Vector Database)**
```bash
# Required
CHROMA_URL=https://customercaregpt-chromadb-xxxxx-uc.a.run.app
CHROMA_PERSIST_DIRECTORY=/chroma/chroma
CHROMA_AUTH_CREDENTIALS=your-chroma-auth-credentials

# Optional
CHROMA_SETTINGS={"anonymized_telemetry": false}
```

### **2. 🔐 Security & Authentication**

#### **JWT & Encryption**
```bash
# Required
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET=your-jwt-secret-key-here-change-in-production
ALGORITHM=HS256

# Optional
ENCRYPTION_KEY=your-encryption-key
JWT_ISSUER=customercaregpt
JWT_AUDIENCE=customercaregpt-users
```

#### **Password Security**
```bash
# Optional (with defaults)
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true
PASSWORD_HISTORY_COUNT=5
```

#### **Account Security**
```bash
# Optional (with defaults)
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
SESSION_TIMEOUT_MINUTES=30
REQUIRE_EMAIL_VERIFICATION=true
REQUIRE_PHONE_VERIFICATION=true
```

### **3. 🤖 AI & LLM Configuration**

#### **Google Gemini**
```bash
# Required
GEMINI_API_KEY=your-gemini-api-key
```

#### **Embedding Configuration**
```bash
# Optional (with defaults)
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_BATCH_SIZE=32
EMBEDDING_CACHE_SIZE=1000
```

#### **Vector Search**
```bash
# Optional (with defaults)
VECTOR_SEARCH_DEFAULT_TOP_K=5
VECTOR_SEARCH_SIMILARITY_THRESHOLD=0.7
VECTOR_SEARCH_CACHE_TTL=3600
```

#### **RAG Configuration**
```bash
# Optional (with defaults)
RAG_DEFAULT_TOP_K=6
RAG_MAX_CONTEXT_LENGTH=4000
RAG_CONFIDENCE_THRESHOLD=0.5
```

### **4. 💳 Payment & Billing (Stripe)**

#### **Stripe Core**
```bash
# Required
STRIPE_API_KEY=sk_test_your_stripe_api_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Optional
STRIPE_SUCCESS_URL=https://your-frontend.com/billing/success
STRIPE_CANCEL_URL=https://your-frontend.com/billing/cancel
BILLING_DEFAULT_TIER=starter
```

#### **Stripe Price IDs**
```bash
# Required for billing
STRIPE_STARTER_PRICE_ID=price_starter
STRIPE_PRO_PRICE_ID=price_pro
STRIPE_ENTERPRISE_PRICE_ID=price_enterprise
STRIPE_WHITE_LABEL_PRICE_ID=price_white_label
```

### **5. 📧 Email & Communication**

#### **Email Provider**
```bash
# Required (choose one)
EMAIL_PROVIDER=ses  # or "sendgrid"

# AWS SES
SES_FROM_EMAIL=noreply@customercaregpt.com

# SendGrid
SENDGRID_API_KEY=your-sendgrid-api-key
```

#### **SMTP Configuration**
```bash
# Optional (if using SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@customercaregpt.com
ADMIN_EMAIL=admin@customercaregpt.com
```

#### **SMS/OTP Provider**
```bash
# Required (choose one)
SMS_PROVIDER=twilio  # or "sns"

# Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890

# AWS SNS
AWS_SNS_REGION=us-east-1
```

### **6. 🌐 Frontend Configuration (Vercel)**

#### **API URLs**
```bash
# Required
VITE_API_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1
VITE_WS_URL=wss://customercaregpt-backend-xxxxx-uc.a.run.app/ws

# Optional
VITE_API_BASE_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app
VITE_DEMO_MODE=false
```

#### **Analytics & Monitoring**
```bash
# Optional
VITE_ANALYTICS_ID=your-analytics-id
VITE_SENTRY_DSN=your-sentry-dsn
```

### **7. 🏗️ Backend Configuration**

#### **Application Settings**
```bash
# Required
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Optional
API_BASE_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app
API_V1_PREFIX=/api/v1
PUBLIC_BASE_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app
```

#### **CORS Configuration**
```bash
# Required
CORS_ORIGINS=https://customercaregpt-frontend.vercel.app,https://customercaregpt-frontend-git-main.vercel.app
ALLOWED_HOSTS=customercaregpt-backend-xxxxx-uc.a.run.app,customercaregpt-frontend.vercel.app

# Optional
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Authorization,Content-Type,X-Client-API-Key,X-Embed-Code-ID,X-Workspace-ID,Origin,Referer
```

### **8. 🔒 Security Headers**

#### **Security Configuration**
```bash
# Optional (with defaults)
ENABLE_SECURITY_HEADERS=true
ENABLE_CSP=true
ENABLE_HSTS=true
ENABLE_RATE_LIMITING=true
ENABLE_INPUT_VALIDATION=true
ENABLE_REQUEST_LOGGING=true
ENABLE_CORS=true
```

#### **Rate Limiting**
```bash
# Optional (with defaults)
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=60
RATE_LIMIT_WORKSPACE_PER_MIN=100
RATE_LIMIT_EMBED_PER_MIN=60
```

### **9. 📁 File Upload & Storage**

#### **File Upload**
```bash
# Optional (with defaults)
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_FILE_TYPES=application/pdf,text/plain,text/markdown
UPLOAD_DIR=uploads
```

#### **S3 Storage (Optional)**
```bash
# Optional
USE_S3=false
S3_BUCKET_NAME=your-bucket-name
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

### **10. 📊 Monitoring & Analytics**

#### **Monitoring**
```bash
# Optional
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
```

#### **Analytics**
```bash
# Optional
ANALYTICS_ENABLED=true
ANALYTICS_RETENTION_DAYS=90
ANALYTICS_BATCH_SIZE=100
```

#### **A/B Testing**
```bash
# Optional
AB_TESTING_ENABLED=true
AB_TESTING_DEFAULT_TRAFFIC_SPLIT=0.5
```

### **11. 🌍 Internationalization**

#### **Language Support**
```bash
# Optional (with defaults)
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,es,fr,de,it,pt,ru,zh,ja,ko
AUTO_DETECT_LANGUAGE=true
```

### **12. 🔧 Queue Configuration**

#### **Queue Settings**
```bash
# Optional (with defaults)
HIGH_PRIORITY_QUEUE=high_priority
NORMAL_QUEUE=normal
LOW_PRIORITY_QUEUE=low_priority
```

### **13. 💬 Chat & Widget Configuration**

#### **Chat Settings**
```bash
# Optional (with defaults)
CHAT_MAX_MESSAGES=50
CHAT_SESSION_TIMEOUT=3600
CHAT_TYPING_INDICATOR_DELAY=1000
```

#### **Widget Settings**
```bash
# Optional (with defaults)
WIDGET_DEFAULT_TITLE=Customer Support
WIDGET_DEFAULT_PLACEHOLDER=Ask me anything...
WIDGET_DEFAULT_WELCOME_MESSAGE=Hello! How can I help you today?
WIDGET_DEFAULT_PRIMARY_COLOR=#4f46e5
WIDGET_DEFAULT_SECONDARY_COLOR=#f8f9fa
WIDGET_DEFAULT_TEXT_COLOR=#111111
WIDGET_DEFAULT_POSITION=bottom-right
WIDGET_DEFAULT_MAX_MESSAGES=50
WIDGET_DEFAULT_Z_INDEX=10000
```

#### **WebSocket Configuration**
```bash
# Optional (with defaults)
WEBSOCKET_MAX_CONNECTIONS=1000
WEBSOCKET_PING_INTERVAL=30
WEBSOCKET_PING_TIMEOUT=10
WEBSOCKET_MAX_RECONNECT_ATTEMPTS=5
```

### **14. 🔐 Secrets Management**

#### **Secrets Provider**
```bash
# Required
SECRETS_PROVIDER=env  # or "aws", "azure", "vault"

# AWS Secrets Manager
AWS_REGION=us-east-1

# Azure Key Vault
AZURE_KEY_VAULT_URL=https://your-vault.vault.azure.net/

# HashiCorp Vault
VAULT_URL=https://vault.customercaregpt.com
VAULT_TOKEN=your-vault-token
VAULT_SECRET_PATH=secret
```

### **15. 🧪 Testing Configuration**

#### **Test Environment**
```bash
# Required for testing
TESTING=true
```

## 📋 Environment Variables by Deployment

### **🔧 Google Cloud Run (Backend)**

#### **Required Environment Variables**
```bash
# Database
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/customercaregpt
POSTGRES_DB=customercaregpt
POSTGRES_USER=customercaregpt
POSTGRES_PASSWORD=secure-password

# Redis
REDIS_URL=redis://customercaregpt-redis.xxxxx.cache.amazonaws.com:6379
REDIS_PASSWORD=secure-redis-password

# ChromaDB
CHROMA_URL=https://customercaregpt-chromadb-xxxxx-uc.a.run.app
CHROMA_AUTH_CREDENTIALS=your-chroma-auth-credentials

# Security
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET=your-jwt-secret-key-here-change-in-production

# AI
GEMINI_API_KEY=your-gemini-api-key

# Stripe
STRIPE_API_KEY=sk_test_your_stripe_api_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_STARTER_PRICE_ID=price_starter
STRIPE_PRO_PRICE_ID=price_pro
STRIPE_ENTERPRISE_PRICE_ID=price_enterprise
STRIPE_WHITE_LABEL_PRICE_ID=price_white_label

# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
PUBLIC_BASE_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app
API_BASE_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app

# CORS
CORS_ORIGINS=https://customercaregpt-frontend.vercel.app,https://customercaregpt-frontend-git-main.vercel.app
ALLOWED_HOSTS=customercaregpt-backend-xxxxx-uc.a.run.app,customercaregpt-frontend.vercel.app

# Email
EMAIL_PROVIDER=ses
SES_FROM_EMAIL=noreply@customercaregpt.com

# Secrets
SECRETS_PROVIDER=env
```

### **🌐 Vercel (Frontend)**

#### **Required Environment Variables**
```bash
# API URLs
VITE_API_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1
VITE_WS_URL=wss://customercaregpt-backend-xxxxx-uc.a.run.app/ws

# Optional
VITE_ANALYTICS_ID=your-analytics-id
VITE_SENTRY_DSN=your-sentry-dsn
VITE_DEMO_MODE=false
```

### **🗄️ Google Cloud SQL (PostgreSQL)**

#### **Database Configuration**
```bash
# Connection
POSTGRES_DB=customercaregpt
POSTGRES_USER=customercaregpt
POSTGRES_PASSWORD=secure-password

# Pool Settings
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=60
DB_POOL_RECYCLE=1800
```

### **🔴 Google Memorystore (Redis)**

#### **Redis Configuration**
```bash
# Connection
REDIS_URL=redis://customercaregpt-redis.xxxxx.cache.amazonaws.com:6379
REDIS_PASSWORD=secure-redis-password

# Pool Settings
REDIS_MAX_CONNECTIONS=100
REDIS_RETRY_ON_TIMEOUT=true
REDIS_SOCKET_KEEPALIVE=true
```

## 🚀 Quick Setup Commands

### **1. Create Environment Files**

#### **Backend (.env)**
```bash
# Copy the example file
cp env.example .env

# Edit with your values
nano .env
```

#### **Frontend (.env.local)**
```bash
# Copy the example file
cp frontend/vercel-env.example frontend/.env.local

# Edit with your values
nano frontend/.env.local
```

### **2. Set Vercel Environment Variables**
```bash
# Set API URLs
vercel env add VITE_API_URL production
vercel env add VITE_WS_URL production

# Set optional variables
vercel env add VITE_ANALYTICS_ID production
vercel env add VITE_SENTRY_DSN production
```

### **3. Set Google Cloud Run Environment Variables**
```bash
# Set all required variables
gcloud run services update customercaregpt-backend \
  --set-env-vars="DATABASE_URL=postgresql+psycopg2://user:password@host:5432/customercaregpt" \
  --set-env-vars="REDIS_URL=redis://customercaregpt-redis.xxxxx.cache.amazonaws.com:6379" \
  --set-env-vars="CHROMA_URL=https://customercaregpt-chromadb-xxxxx-uc.a.run.app" \
  --set-env-vars="GEMINI_API_KEY=your-gemini-api-key" \
  --set-env-vars="SECRET_KEY=your-secret-key" \
  --set-env-vars="STRIPE_API_KEY=sk_test_your_stripe_api_key"
```

## ⚠️ Security Notes

### **🔒 Critical Security Variables**
- **SECRET_KEY**: Must be at least 32 characters, unique per environment
- **JWT_SECRET**: Must be different from SECRET_KEY, at least 32 characters
- **POSTGRES_PASSWORD**: Strong password for database
- **REDIS_PASSWORD**: Strong password for Redis
- **STRIPE_API_KEY**: Use test keys for development, live keys for production
- **GEMINI_API_KEY**: Keep secure, has usage limits

### **🛡️ Production Security Checklist**
- [ ] All default passwords changed
- [ ] Strong, unique secrets generated
- [ ] CORS origins properly configured
- [ ] Rate limiting enabled
- [ ] Security headers enabled
- [ ] Input validation enabled
- [ ] Request logging enabled
- [ ] Debug mode disabled
- [ ] HTTPS only in production

## 📊 Environment Variables Summary

### **Total Environment Variables: 100+**
- **Required**: 25+
- **Optional**: 75+
- **Security Critical**: 10+
- **Service Specific**: 50+

### **By Service:**
- **Backend**: 60+ variables
- **Frontend**: 5+ variables
- **Database**: 10+ variables
- **Redis**: 5+ variables
- **ChromaDB**: 3+ variables
- **Stripe**: 8+ variables
- **Email**: 5+ variables
- **Monitoring**: 5+ variables

This comprehensive analysis covers ALL environment variables needed for your CustomerCareGPT deployment! 🚀
