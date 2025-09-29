# 🔧 Environment Setup Guide for Frontend and Backend

## Overview
Yes, you need **different environment files** for Frontend and Backend because they serve different purposes and have different variable naming conventions.

## 📁 Environment File Structure

```
CustomerCareGPT/
├── .env                    # Main backend environment (root)
├── env.example            # Backend environment template (root)
├── frontend/
│   ├── .env.local         # Frontend environment (local dev)
│   ├── env.example        # Frontend environment template
│   └── vercel-env.example # Vercel environment template
└── backend/
    └── .env               # Backend environment (alternative location)
```

## 🔧 Backend Environment Files

### **1. Root `.env` File (Primary)**
**Location**: `CustomerCareGPT/.env`
**Purpose**: Main backend environment variables
**Used by**: FastAPI backend, Google Cloud Run

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

# Application
ENVIRONMENT=production
DEBUG=false
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

### **2. Backend `.env` File (Alternative)**
**Location**: `CustomerCareGPT/backend/.env`
**Purpose**: Alternative backend environment variables
**Used by**: Backend-specific configurations

## 🌐 Frontend Environment Files

### **1. Frontend `.env.local` File (Local Development)**
**Location**: `CustomerCareGPT/frontend/.env.local`
**Purpose**: Frontend environment variables for local development
**Used by**: Vite development server

```bash
# Backend API URL
VITE_API_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1

# WebSocket URL
VITE_WS_URL=wss://customercaregpt-backend-xxxxx-uc.a.run.app/ws

# Optional
VITE_ANALYTICS_ID=your-analytics-id
VITE_SENTRY_DSN=your-sentry-dsn
VITE_DEMO_MODE=false
```

### **2. Frontend `env.example` File (Template)**
**Location**: `CustomerCareGPT/frontend/env.example`
**Purpose**: Template for frontend environment variables
**Used by**: Documentation and setup

### **3. Vercel Environment Variables (Production)**
**Location**: Vercel Dashboard or `vercel-env.json`
**Purpose**: Frontend environment variables for production
**Used by**: Vercel deployment

## 🚀 Setup Instructions

### **Step 1: Backend Environment Setup**

#### **For Local Development:**
```bash
# Copy the example file
cp env.example .env

# Edit with your values
nano .env
```

#### **For Google Cloud Run:**
```bash
# Set environment variables in Cloud Run service
gcloud run services update customercaregpt-backend \
  --set-env-vars="DATABASE_URL=postgresql+psycopg2://user:password@host:5432/customercaregpt" \
  --set-env-vars="REDIS_URL=redis://customercaregpt-redis.xxxxx.cache.amazonaws.com:6379" \
  --set-env-vars="GEMINI_API_KEY=your-gemini-api-key" \
  --set-env-vars="SECRET_KEY=your-secret-key"
```

### **Step 2: Frontend Environment Setup**

#### **For Local Development:**
```bash
# Navigate to frontend directory
cd frontend

# Copy the example file
cp env.example .env.local

# Edit with your values
nano .env.local
```

#### **For Vercel Production:**
```bash
# Set environment variables in Vercel
vercel env add VITE_API_URL production
vercel env add VITE_WS_URL production

# Or set in Vercel dashboard
# Go to Project Settings > Environment Variables
```

## 🔍 Key Differences

### **Backend Environment Variables**
- **No prefix** (e.g., `DATABASE_URL`, `SECRET_KEY`)
- **Contains sensitive data** (API keys, database credentials)
- **Server-side only** (never exposed to client)
- **Used by**: FastAPI, Python services
- **Deployed to**: Google Cloud Run

### **Frontend Environment Variables**
- **VITE_ prefix required** (e.g., `VITE_API_URL`, `VITE_WS_URL`)
- **Client-side safe** (no sensitive data)
- **Bundled into client code** (visible in browser)
- **Used by**: React, Vite build process
- **Deployed to**: Vercel

## 📋 Variable Mapping

### **Backend → Frontend Mapping**
```bash
# Backend (Server-side)
API_BASE_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app
PUBLIC_BASE_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app

# Frontend (Client-side)
VITE_API_URL=https://customercaregpt-backend-xxxxx-uc.a.run.app/api/v1
VITE_WS_URL=wss://customercaregpt-backend-xxxxx-uc.a.run.app/ws
```

## 🔒 Security Considerations

### **Backend Environment (.env)**
- ✅ **Contains sensitive data** (API keys, passwords)
- ✅ **Never commit to version control**
- ✅ **Server-side only**
- ✅ **Use secrets management in production**

### **Frontend Environment (.env.local)**
- ✅ **Only client-safe variables**
- ✅ **VITE_ prefix required**
- ✅ **Can be committed to version control** (if no secrets)
- ✅ **Set in Vercel dashboard for production**

## 🛠️ Development Workflow

### **1. Local Development**
```bash
# Backend
cp env.example .env
# Edit .env with your values
python -m uvicorn app.main:app --reload

# Frontend
cd frontend
cp env.example .env.local
# Edit .env.local with your values
npm run dev
```

### **2. Production Deployment**
```bash
# Backend (Google Cloud Run)
# Set environment variables in Cloud Run service

# Frontend (Vercel)
# Set environment variables in Vercel dashboard
vercel deploy
```

## 📊 Environment Variables Summary

### **Backend Variables (100+)**
- Database configuration
- Security & authentication
- AI & LLM settings
- Payment processing
- Email & communication
- Monitoring & analytics
- Performance tuning

### **Frontend Variables (5+)**
- API URLs
- WebSocket URLs
- Analytics (optional)
- Error tracking (optional)
- Demo mode (optional)

## 🎯 Best Practices

### **1. Environment File Management**
- Use `.env.example` as templates
- Never commit `.env` files with secrets
- Use different values for dev/staging/production
- Document all required variables

### **2. Security**
- Rotate secrets regularly
- Use strong, unique passwords
- Enable secrets management in production
- Monitor for exposed credentials

### **3. Deployment**
- Set environment variables in deployment platforms
- Use CI/CD for environment management
- Test with production-like environments
- Monitor environment variable usage

## 🚀 Quick Start Commands

### **Setup All Environment Files**
```bash
# Backend
cp env.example .env
nano .env

# Frontend
cd frontend
cp env.example .env.local
nano .env.local
```

### **Deploy with Environment Variables**
```bash
# Backend to Google Cloud Run
./deploy-gcp.sh

# Frontend to Vercel
./deploy-vercel.sh
```

This setup ensures proper separation of concerns and security for both frontend and backend! 🎉
