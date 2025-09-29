# 🚀 CustomerCareGPT Google Cloud Run Deployment Plan

## Overview
This document outlines the complete Google Cloud Platform deployment strategy for your CustomerCareGPT application using Cloud Run, which is perfect for your FastAPI backend with its serverless, cost-effective architecture.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloud CDN     │    │   Cloud Run     │    │   Cloud Run     │
│   (Static Files)│◄──►│   (Frontend)    │◄──►│   (Backend)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloud Storage │    │   Cloud SQL     │    │   Memorystore   │
│   (File Storage)│    │   (PostgreSQL)  │    │   (Redis)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Cloud Run     │
                       │   (ChromaDB)    │
                       └─────────────────┘
```

## 📋 Prerequisites

### Google Cloud Setup
1. **Google Cloud Account** with billing enabled
2. **Google Cloud CLI** installed and configured
3. **Docker** installed locally
4. **gcloud** CLI authenticated

### Required Google Cloud Services
- **Cloud Run** (Serverless containers)
- **Cloud SQL** (PostgreSQL)
- **Memorystore** (Redis)
- **Cloud Storage** (File storage)
- **Cloud CDN** (Content delivery)
- **Secret Manager** (Secrets)
- **Cloud Build** (CI/CD)
- **Cloud Logging** (Monitoring)

## 🛠️ Step-by-Step Deployment

### Phase 1: Project Setup

#### 1.1 Create Google Cloud Project
```bash
# Create new project
gcloud projects create customercaregpt-$(date +%s) --name="CustomerCareGPT"

# Set project
gcloud config set project customercaregpt-XXXXX

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable container.googleapis.com
```

#### 1.2 Create Cloud SQL PostgreSQL Database
```bash
# Create Cloud SQL instance
gcloud sql instances create customercaregpt-db \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --storage-type=SSD \
    --storage-size=10GB \
    --storage-auto-increase \
    --backup \
    --enable-ip-alias

# Create database
gcloud sql databases create customercaregpt --instance=customercaregpt-db

# Create user
gcloud sql users create postgres \
    --instance=customercaregpt-db \
    --password=YourSecurePassword123!
```

#### 1.3 Create Memorystore Redis
```bash
# Create Redis instance
gcloud redis instances create customercaregpt-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x \
    --tier=basic
```

### Phase 2: Container Setup

#### 2.1 Build and Push Docker Images
```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build and push backend
cd backend
docker build -t gcr.io/customercaregpt-XXXXX/backend:latest .
docker push gcr.io/customercaregpt-XXXXX/backend:latest

# Build and push frontend
cd ../frontend
docker build -t gcr.io/customercaregpt-XXXXX/frontend:latest .
docker push gcr.io/customercaregpt-XXXXX/frontend:latest

# Build and push worker
cd ../backend
docker build -t gcr.io/customercaregpt-XXXXX/worker:latest .
docker push gcr.io/customercaregpt-XXXXX/worker:latest

# Build and push chromadb
docker build -t gcr.io/customercaregpt-XXXXX/chromadb:latest -f Dockerfile.chromadb .
docker push gcr.io/customercaregpt-XXXXX/chromadb:latest
```

### Phase 3: Deploy Cloud Run Services

#### 3.1 Deploy Backend Service
```bash
# Deploy backend to Cloud Run
gcloud run deploy customercaregpt-backend \
    --image gcr.io/customercaregpt-XXXXX/backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8000 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --min-instances 0 \
    --set-env-vars "DEBUG=false,LOG_LEVEL=INFO,ENVIRONMENT=production" \
    --add-cloudsql-instances customercaregpt-XXXXX:us-central1:customercaregpt-db \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=secret-key:latest,STRIPE_API_KEY=stripe-api-key:latest"
```

#### 3.2 Deploy Frontend Service
```bash
# Deploy frontend to Cloud Run
gcloud run deploy customercaregpt-frontend \
    --image gcr.io/customercaregpt-XXXXX/frontend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 80 \
    --memory 512Mi \
    --cpu 0.5 \
    --max-instances 5 \
    --min-instances 0
```

#### 3.3 Deploy Worker Service
```bash
# Deploy worker to Cloud Run
gcloud run deploy customercaregpt-worker \
    --image gcr.io/customercaregpt-XXXXX/worker:latest \
    --platform managed \
    --region us-central1 \
    --no-allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 0.5 \
    --max-instances 3 \
    --min-instances 0 \
    --add-cloudsql-instances customercaregpt-XXXXX:us-central1:customercaregpt-db \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=secret-key:latest"
```

#### 3.4 Deploy ChromaDB Service
```bash
# Deploy ChromaDB to Cloud Run
gcloud run deploy customercaregpt-chromadb \
    --image gcr.io/customercaregpt-XXXXX/chromadb:latest \
    --platform managed \
    --region us-central1 \
    --no-allow-unauthenticated \
    --port 8001 \
    --memory 512Mi \
    --cpu 0.5 \
    --max-instances 2 \
    --min-instances 0
```

### Phase 4: Secrets Management

#### 4.1 Store Secrets in Secret Manager
```bash
# Store Gemini API key
echo -n "your-gemini-api-key-here" | gcloud secrets create gemini-api-key --data-file=-

# Store secret key
echo -n "your-secret-key-here" | gcloud secrets create secret-key --data-file=-

# Store Stripe API key
echo -n "your-stripe-api-key-here" | gcloud secrets create stripe-api-key --data-file=-

# Store Stripe webhook secret
echo -n "your-stripe-webhook-secret-here" | gcloud secrets create stripe-webhook-secret --data-file=-
```

### Phase 5: Cloud Storage Setup

#### 5.1 Create Cloud Storage Bucket
```bash
# Create bucket for file uploads
gsutil mb gs://customercaregpt-uploads-XXXXX

# Set bucket permissions
gsutil iam ch allUsers:objectViewer gs://customercaregpt-uploads-XXXXX
```

### Phase 6: Load Balancer and CDN

#### 6.1 Set up Cloud CDN
```bash
# Create backend bucket for static files
gsutil mb gs://customercaregpt-static-XXXXX

# Upload frontend build to bucket
gsutil -m cp -r frontend/dist/* gs://customercaregpt-static-XXXXX/

# Create Cloud CDN
gcloud compute url-maps create customercaregpt-cdn \
    --default-backend-bucket=customercaregpt-static-XXXXX
```

## 🔧 Environment Configuration

### Production Environment Variables
```bash
# Database
DATABASE_URL=postgresql://postgres:password@/customercaregpt?host=/cloudsql/customercaregpt-XXXXX:us-central1:customercaregpt-db

# Redis
REDIS_URL=redis://10.x.x.x:6379

# ChromaDB
CHROMA_URL=https://customercaregpt-chromadb-xxxxx-uc.a.run.app

# Security
SECRET_KEY=your-secret-key
ENABLE_SECURITY_HEADERS=true
ENABLE_RATE_LIMITING=true

# Monitoring
LOG_LEVEL=INFO
PROMETHEUS_ENABLED=true
```

## 💰 Cost Estimation

### Google Cloud Run Pricing (Monthly)
- **Backend Service**: ~$5-15 (1 vCPU, 1GB RAM, 100K requests)
- **Frontend Service**: ~$2-8 (0.5 vCPU, 512MB RAM, 50K requests)
- **Worker Service**: ~$2-8 (0.5 vCPU, 512MB RAM, 10K requests)
- **ChromaDB Service**: ~$2-8 (0.5 vCPU, 512MB RAM, 5K requests)

### Other Services
- **Cloud SQL**: ~$10-20 (db-f1-micro)
- **Memorystore**: ~$15-25 (1GB Redis)
- **Cloud Storage**: ~$2-5 (10GB + requests)
- **Cloud CDN**: ~$5-15 (1TB transfer)

**Total Estimated Monthly Cost: $43-103**

### Free Tier Benefits
- **$300 credit** for new accounts
- **180,000 vCPU-seconds** free per month
- **360,000 GiB-seconds** free per month
- **2 million requests** free per month

**With free tier: $0-20/month for first year!** 🎉

## 🚀 Deployment Scripts

### Quick Deploy Script (`deploy-gcp.sh`)
```bash
#!/bin/bash

# CustomerCareGPT Google Cloud Run Deployment Script
set -e

# Configuration
PROJECT_ID="customercaregpt-$(date +%s)"
REGION="us-central1"

echo "🚀 Deploying CustomerCareGPT to Google Cloud Run..."

# Set project
gcloud config set project $PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com sqladmin.googleapis.com redis.googleapis.com storage.googleapis.com secretmanager.googleapis.com

# Build and push images
echo "📦 Building and pushing Docker images..."
gcloud auth configure-docker

# Backend
cd backend
docker build -t gcr.io/$PROJECT_ID/backend:latest .
docker push gcr.io/$PROJECT_ID/backend:latest

# Frontend
cd ../frontend
docker build -t gcr.io/$PROJECT_ID/frontend:latest .
docker push gcr.io/$PROJECT_ID/frontend:latest

# Deploy services
echo "🚀 Deploying Cloud Run services..."
gcloud run deploy customercaregpt-backend --image gcr.io/$PROJECT_ID/backend:latest --platform managed --region $REGION --allow-unauthenticated --port 8000 --memory 1Gi --cpu 1
gcloud run deploy customercaregpt-frontend --image gcr.io/$PROJECT_ID/frontend:latest --platform managed --region $REGION --allow-unauthenticated --port 80 --memory 512Mi --cpu 0.5

echo "✅ Deployment complete!"
echo "Backend URL: $(gcloud run services describe customercaregpt-backend --platform managed --region $REGION --format 'value(status.url)')"
echo "Frontend URL: $(gcloud run services describe customercaregpt-frontend --platform managed --region $REGION --format 'value(status.url)')"
```

## 🔍 Health Checks and Monitoring

### Health Check Endpoints
- **Backend Health**: `https://customercaregpt-backend-xxxxx-uc.a.run.app/health`
- **Backend Ready**: `https://customercaregpt-backend-xxxxx-uc.a.run.app/ready`
- **Backend Metrics**: `https://customercaregpt-backend-xxxxx-uc.a.run.app/metrics`

### Cloud Logging
- **Automatic logging** to Cloud Logging
- **Structured logs** with JSON format
- **Log-based metrics** and alerting
- **Integration** with Cloud Monitoring

## 🛡️ Security Features

### Built-in Security
- **HTTPS by default** for all services
- **Identity and Access Management** (IAM)
- **Secret Manager** for sensitive data
- **VPC connector** for private networking
- **Cloud Armor** for DDoS protection

### Network Security
- **Private Google Access** for Cloud SQL
- **VPC peering** for Memorystore
- **Firewall rules** for service communication
- **SSL/TLS encryption** in transit

## 📈 Auto-Scaling

### Cloud Run Scaling
- **Automatic scaling** from 0 to 1000 instances
- **CPU and memory-based** scaling
- **Request-based** scaling
- **Cold start optimization**

### Scaling Configuration
```bash
# Configure scaling
gcloud run services update customercaregpt-backend \
    --min-instances 1 \
    --max-instances 10 \
    --concurrency 80 \
    --cpu-throttling
```

## 🔄 CI/CD Pipeline

### Cloud Build Configuration (`cloudbuild.yaml`)
```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/backend:$COMMIT_SHA', './backend']
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/frontend:$COMMIT_SHA', './frontend']
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/backend:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/frontend:$COMMIT_SHA']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: 'gcloud'
    args: ['run', 'deploy', 'customercaregpt-backend', '--image', 'gcr.io/$PROJECT_ID/backend:$COMMIT_SHA', '--region', 'us-central1']
```

## 🎯 Advantages of Cloud Run

### ✅ Pros
- **Serverless** - no infrastructure management
- **Cost-effective** - pay only for usage
- **Auto-scaling** - handles traffic spikes
- **Fast deployment** - minutes not hours
- **Built-in monitoring** - Cloud Logging & Monitoring
- **Security** - Google's security infrastructure
- **Global** - deploy to multiple regions

### ⚠️ Considerations
- **Cold starts** - first request may be slower
- **Vendor lock-in** - Google-specific features
- **Memory limits** - max 8GB per instance
- **Request timeout** - max 60 minutes

## 🚀 Next Steps

1. **Set up Google Cloud account** and enable billing
2. **Install Google Cloud CLI** and authenticate
3. **Run the deployment script** to get started
4. **Configure secrets** in Secret Manager
5. **Set up monitoring** and alerting
6. **Configure custom domain** (optional)
7. **Set up CI/CD** with Cloud Build

This Cloud Run deployment will give you a production-ready, scalable, and cost-effective solution for your CustomerCareGPT application!
