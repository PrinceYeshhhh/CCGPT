#!/bin/bash

# CustomerCareGPT Google Cloud Run Deployment Script
# This script automates the deployment of CustomerCareGPT to Google Cloud Run

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="customercaregpt-$(date +%s)"
REGION="us-central1"
SERVICE_ACCOUNT="customercaregpt-sa"

echo -e "${BLUE}🚀 CustomerCareGPT Google Cloud Run Deployment${NC}"
echo -e "${BLUE}=============================================${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

if ! command_exists gcloud; then
    echo -e "${RED}❌ Google Cloud CLI is not installed. Please install it first.${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with Google Cloud. Please run 'gcloud auth login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Function to create project and enable APIs
setup_project() {
    echo -e "${YELLOW}🏗️ Setting up Google Cloud project...${NC}"
    
    # Create project
    gcloud projects create "$PROJECT_ID" --name="CustomerCareGPT" || true
    gcloud config set project "$PROJECT_ID"
    
    # Enable billing (user needs to do this manually)
    echo -e "${YELLOW}⚠️  Please enable billing for project $PROJECT_ID in the Google Cloud Console${NC}"
    echo "Visit: https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
    read -p "Press Enter when billing is enabled..."
    
    # Enable required APIs
    echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
    gcloud services enable run.googleapis.com
    gcloud services enable sqladmin.googleapis.com
    gcloud services enable redis.googleapis.com
    gcloud services enable storage.googleapis.com
    gcloud services enable secretmanager.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable container.googleapis.com
    
    echo -e "${GREEN}✅ Project setup completed${NC}"
}

# Function to create Cloud SQL database
create_database() {
    echo -e "${YELLOW}🗄️ Creating Cloud SQL database...${NC}"
    
    # Create Cloud SQL instance
    gcloud sql instances create customercaregpt-db \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region="$REGION" \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup \
        --enable-ip-alias || true
    
    # Create database
    gcloud sql databases create customercaregpt --instance=customercaregpt-db || true
    
    # Create user
    gcloud sql users create postgres \
        --instance=customercaregpt-db \
        --password=YourSecurePassword123! || true
    
    echo -e "${GREEN}✅ Database created${NC}"
}

# Function to create Redis instance
create_redis() {
    echo -e "${YELLOW}🔴 Creating Redis instance...${NC}"
    
    gcloud redis instances create customercaregpt-redis \
        --size=1 \
        --region="$REGION" \
        --redis-version=redis_6_x \
        --tier=basic || true
    
    echo -e "${GREEN}✅ Redis instance created${NC}"
}

# Function to create secrets
create_secrets() {
    echo -e "${YELLOW}🔐 Creating secrets...${NC}"
    
    # Create secrets (user needs to provide values)
    echo -e "${YELLOW}Please provide the following secrets:${NC}"
    
    read -p "Gemini API Key: " -s GEMINI_API_KEY
    echo
    read -p "Secret Key: " -s SECRET_KEY
    echo
    read -p "Stripe API Key: " -s STRIPE_API_KEY
    echo
    read -p "Stripe Webhook Secret: " -s STRIPE_WEBHOOK_SECRET
    echo
    
    # Store secrets
    echo -n "$GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=- || true
    echo -n "$SECRET_KEY" | gcloud secrets create secret-key --data-file=- || true
    echo -n "$STRIPE_API_KEY" | gcloud secrets create stripe-api-key --data-file=- || true
    echo -n "$STRIPE_WEBHOOK_SECRET" | gcloud secrets create stripe-webhook-secret --data-file=- || true
    
    echo -e "${GREEN}✅ Secrets created${NC}"
}

# Function to build and push Docker images
build_and_push() {
    echo -e "${YELLOW}📦 Building and pushing Docker images...${NC}"
    
    # Configure Docker for GCR
    gcloud auth configure-docker
    
    # Build and push backend
    echo -e "${YELLOW}🔨 Building backend...${NC}"
    cd backend
    docker build -t "gcr.io/$PROJECT_ID/backend:latest" .
    docker push "gcr.io/$PROJECT_ID/backend:latest"
    cd ..
    
    # Build and push frontend
    echo -e "${YELLOW}🔨 Building frontend...${NC}"
    cd frontend
    docker build -t "gcr.io/$PROJECT_ID/frontend:latest" .
    docker push "gcr.io/$PROJECT_ID/frontend:latest"
    cd ..
    
    # Build and push worker
    echo -e "${YELLOW}🔨 Building worker...${NC}"
    cd backend
    docker build -t "gcr.io/$PROJECT_ID/worker:latest" .
    docker push "gcr.io/$PROJECT_ID/worker:latest"
    cd ..
    
    echo -e "${GREEN}✅ All images built and pushed${NC}"
}

# Function to deploy Cloud Run services
deploy_services() {
    echo -e "${YELLOW}🚀 Deploying Cloud Run services...${NC}"
    
    # Get Cloud SQL connection name
    SQL_CONNECTION_NAME=$(gcloud sql instances describe customercaregpt-db --format="value(connectionName)")
    
    # Deploy backend
    echo -e "${YELLOW}🚀 Deploying backend service...${NC}"
    gcloud run deploy customercaregpt-backend \
        --image "gcr.io/$PROJECT_ID/backend:latest" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --port 8000 \
        --memory 1Gi \
        --cpu 1 \
        --max-instances 10 \
        --min-instances 0 \
        --set-env-vars "DEBUG=false,LOG_LEVEL=INFO,ENVIRONMENT=production" \
        --add-cloudsql-instances "$SQL_CONNECTION_NAME" \
        --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=secret-key:latest,STRIPE_API_KEY=stripe-api-key:latest,STRIPE_WEBHOOK_SECRET=stripe-webhook-secret:latest"
    
    # Deploy frontend
    echo -e "${YELLOW}🚀 Deploying frontend service...${NC}"
    gcloud run deploy customercaregpt-frontend \
        --image "gcr.io/$PROJECT_ID/frontend:latest" \
        --platform managed \
        --region "$REGION" \
        --allow-unauthenticated \
        --port 80 \
        --memory 512Mi \
        --cpu 0.5 \
        --max-instances 5 \
        --min-instances 0
    
    # Deploy worker
    echo -e "${YELLOW}🚀 Deploying worker service...${NC}"
    gcloud run deploy customercaregpt-worker \
        --image "gcr.io/$PROJECT_ID/worker:latest" \
        --platform managed \
        --region "$REGION" \
        --no-allow-unauthenticated \
        --port 8080 \
        --memory 512Mi \
        --cpu 0.5 \
        --max-instances 3 \
        --min-instances 0 \
        --add-cloudsql-instances "$SQL_CONNECTION_NAME" \
        --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=secret-key:latest"
    
    echo -e "${GREEN}✅ All services deployed${NC}"
}

# Function to show deployment URLs
show_urls() {
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 Service URLs:${NC}"
    
    # Get service URLs
    BACKEND_URL=$(gcloud run services describe customercaregpt-backend --platform managed --region "$REGION" --format 'value(status.url)')
    FRONTEND_URL=$(gcloud run services describe customercaregpt-frontend --platform managed --region "$REGION" --format 'value(status.url)')
    
    echo "Backend API: $BACKEND_URL"
    echo "Frontend: $FRONTEND_URL"
    echo ""
    echo -e "${BLUE}🔍 Health Check URLs:${NC}"
    echo "Backend Health: $BACKEND_URL/health"
    echo "Backend Ready: $BACKEND_URL/ready"
    echo "Backend Metrics: $BACKEND_URL/metrics"
    echo ""
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "1. Update your frontend environment variables with the backend URL"
    echo "2. Test the health endpoints"
    echo "3. Set up monitoring and alerting"
    echo "4. Configure custom domain (optional)"

    # Auto-configure backend environment variables with discovered URLs
    if [ -n "$BACKEND_URL" ]; then
      echo -e "${YELLOW}🔧 Setting backend env vars PUBLIC_BASE_URL and API_BASE_URL...${NC}"
      gcloud run services update customercaregpt-backend \
        --platform managed \
        --region "$REGION" \
        --set-env-vars "PUBLIC_BASE_URL=$BACKEND_URL,API_BASE_URL=$BACKEND_URL" >/dev/null 2>&1 || true
    fi

    # Display confirmation
    echo -e "${GREEN}✅ Backend env updated with:${NC}"
    echo "   PUBLIC_BASE_URL=$BACKEND_URL"
    echo "   API_BASE_URL=$BACKEND_URL"
}

# Function to check deployment status
status() {
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    
    # Check if project exists
    if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Project '$PROJECT_ID' exists${NC}"
        
        # List Cloud Run services
        echo -e "${YELLOW}📋 Cloud Run Services:${NC}"
        gcloud run services list --platform managed --region "$REGION" --format "table(metadata.name,status.url,status.conditions[0].status)"
        
        # List Cloud SQL instances
        echo -e "${YELLOW}🗄️ Cloud SQL Instances:${NC}"
        gcloud sql instances list --format "table(name,databaseVersion,settings.tier,status)"
        
        # List Redis instances
        echo -e "${YELLOW}🔴 Redis Instances:${NC}"
        gcloud redis instances list --region "$REGION" --format "table(name,memorySizeGb,redisVersion,state"
    else
        echo -e "${RED}❌ Project '$PROJECT_ID' not found${NC}"
    fi
}

# Function to clean up resources
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up resources...${NC}"
    
    read -p "Are you sure you want to delete all CustomerCareGPT resources? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}⚠️  This will delete all resources. Proceeding...${NC}"
        
        # Delete Cloud Run services
        echo "Deleting Cloud Run services..."
        gcloud run services delete customercaregpt-backend --platform managed --region "$REGION" --quiet || true
        gcloud run services delete customercaregpt-frontend --platform managed --region "$REGION" --quiet || true
        gcloud run services delete customercaregpt-worker --platform managed --region "$REGION" --quiet || true
        
        # Delete Cloud SQL instance
        echo "Deleting Cloud SQL instance..."
        gcloud sql instances delete customercaregpt-db --quiet || true
        
        # Delete Redis instance
        echo "Deleting Redis instance..."
        gcloud redis instances delete customercaregpt-redis --region "$REGION" --quiet || true
        
        # Delete secrets
        echo "Deleting secrets..."
        gcloud secrets delete gemini-api-key --quiet || true
        gcloud secrets delete secret-key --quiet || true
        gcloud secrets delete stripe-api-key --quiet || true
        gcloud secrets delete stripe-webhook-secret --quiet || true
        
        # Delete project
        echo "Deleting project..."
        gcloud projects delete "$PROJECT_ID" --quiet || true
        
        echo -e "${GREEN}✅ Cleanup completed${NC}"
    else
        echo -e "${YELLOW}❌ Cleanup cancelled${NC}"
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}CustomerCareGPT Google Cloud Run Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy    Full deployment (setup + deploy)"
    echo "  setup     Setup project and infrastructure only"
    echo "  build     Build and push Docker images only"
    echo "  deploy-services  Deploy Cloud Run services only"
    echo "  status    Check deployment status"
    echo "  cleanup   Delete all resources (DANGEROUS)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy     # Full deployment"
    echo "  $0 status     # Check status"
    echo "  $0 cleanup    # Clean up resources"
}

# Main deployment function
deploy() {
    setup_project
    create_database
    create_redis
    create_secrets
    build_and_push
    deploy_services
    show_urls
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    setup)
        setup_project
        create_database
        create_redis
        create_secrets
        ;;
    build)
        build_and_push
        ;;
    deploy-services)
        deploy_services
        show_urls
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac
