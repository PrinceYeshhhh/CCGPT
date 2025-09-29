@echo off
REM CustomerCareGPT Google Cloud Run Deployment Script for Windows
REM This script automates the deployment of CustomerCareGPT to Google Cloud Run

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_ID=customercaregpt-%RANDOM%
set REGION=us-central1

echo 🚀 CustomerCareGPT Google Cloud Run Deployment
echo =============================================
echo Project ID: %PROJECT_ID%
echo Region: %REGION%
echo.

REM Check prerequisites
echo 🔍 Checking prerequisites...

where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Google Cloud CLI is not installed. Please install it first.
    echo Install from: https://cloud.google.com/sdk/docs/install
    exit /b 1
)

where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install it first.
    exit /b 1
)

REM Check if user is authenticated
gcloud auth list --filter=status:ACTIVE --format="value(account)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Not authenticated with Google Cloud. Please run 'gcloud auth login' first.
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Main deployment function
:deploy
echo 🏗️ Setting up Google Cloud project...

REM Create project
gcloud projects create %PROJECT_ID% --name="CustomerCareGPT" 2>nul || echo Project may already exist
gcloud config set project %PROJECT_ID%

echo ⚠️  Please enable billing for project %PROJECT_ID% in the Google Cloud Console
echo Visit: https://console.cloud.google.com/billing/linkedaccount?project=%PROJECT_ID%
pause

REM Enable required APIs
echo 🔧 Enabling required APIs...
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable container.googleapis.com

echo ✅ Project setup completed

REM Create Cloud SQL database
echo 🗄️ Creating Cloud SQL database...
gcloud sql instances create customercaregpt-db --database-version=POSTGRES_15 --tier=db-f1-micro --region=%REGION% --storage-type=SSD --storage-size=10GB --storage-auto-increase --backup --enable-ip-alias 2>nul || echo Database instance may already exist

gcloud sql databases create customercaregpt --instance=customercaregpt-db 2>nul || echo Database may already exist

gcloud sql users create postgres --instance=customercaregpt-db --password=YourSecurePassword123! 2>nul || echo User may already exist

echo ✅ Database created

REM Create Redis instance
echo 🔴 Creating Redis instance...
gcloud redis instances create customercaregpt-redis --size=1 --region=%REGION% --redis-version=redis_6_x --tier=basic 2>nul || echo Redis instance may already exist

echo ✅ Redis instance created

REM Create secrets
echo 🔐 Creating secrets...
echo Please provide the following secrets:

set /p GEMINI_API_KEY="Gemini API Key: "
set /p SECRET_KEY="Secret Key: "
set /p STRIPE_API_KEY="Stripe API Key: "
set /p STRIPE_WEBHOOK_SECRET="Stripe Webhook Secret: "

echo %GEMINI_API_KEY% | gcloud secrets create gemini-api-key --data-file=- 2>nul || echo Secret may already exist
echo %SECRET_KEY% | gcloud secrets create secret-key --data-file=- 2>nul || echo Secret may already exist
echo %STRIPE_API_KEY% | gcloud secrets create stripe-api-key --data-file=- 2>nul || echo Secret may already exist
echo %STRIPE_WEBHOOK_SECRET% | gcloud secrets create stripe-webhook-secret --data-file=- 2>nul || echo Secret may already exist

echo ✅ Secrets created

REM Build and push Docker images
echo 📦 Building and pushing Docker images...

REM Configure Docker for GCR
gcloud auth configure-docker

REM Build and push backend
echo 🔨 Building backend...
cd backend
docker build -t gcr.io/%PROJECT_ID%/backend:latest .
docker push gcr.io/%PROJECT_ID%/backend:latest
cd ..

REM Build and push frontend
echo 🔨 Building frontend...
cd frontend
docker build -t gcr.io/%PROJECT_ID%/frontend:latest .
docker push gcr.io/%PROJECT_ID%/frontend:latest
cd ..

REM Build and push worker
echo 🔨 Building worker...
cd backend
docker build -t gcr.io/%PROJECT_ID%/worker:latest .
docker push gcr.io/%PROJECT_ID%/worker:latest
cd ..

echo ✅ All images built and pushed

REM Deploy Cloud Run services
echo 🚀 Deploying Cloud Run services...

REM Get Cloud SQL connection name
for /f "tokens=*" %%i in ('gcloud sql instances describe customercaregpt-db --format="value(connectionName)"') do set SQL_CONNECTION_NAME=%%i

REM Deploy backend
echo 🚀 Deploying backend service...
gcloud run deploy customercaregpt-backend --image gcr.io/%PROJECT_ID%/backend:latest --platform managed --region %REGION% --allow-unauthenticated --port 8000 --memory 1Gi --cpu 1 --max-instances 10 --min-instances 0 --set-env-vars "DEBUG=false,LOG_LEVEL=INFO,ENVIRONMENT=production" --add-cloudsql-instances %SQL_CONNECTION_NAME% --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=secret-key:latest,STRIPE_API_KEY=stripe-api-key:latest,STRIPE_WEBHOOK_SECRET=stripe-webhook-secret:latest"

REM Deploy frontend
echo 🚀 Deploying frontend service...
gcloud run deploy customercaregpt-frontend --image gcr.io/%PROJECT_ID%/frontend:latest --platform managed --region %REGION% --allow-unauthenticated --port 80 --memory 512Mi --cpu 0.5 --max-instances 5 --min-instances 0

REM Deploy worker
echo 🚀 Deploying worker service...
gcloud run deploy customercaregpt-worker --image gcr.io/%PROJECT_ID%/worker:latest --platform managed --region %REGION% --no-allow-unauthenticated --port 8080 --memory 512Mi --cpu 0.5 --max-instances 3 --min-instances 0 --add-cloudsql-instances %SQL_CONNECTION_NAME% --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=secret-key:latest"

echo ✅ All services deployed

REM Show deployment URLs
echo 🎉 Deployment completed successfully!
echo.
echo 📋 Service URLs:

for /f "tokens=*" %%i in ('gcloud run services describe customercaregpt-backend --platform managed --region %REGION% --format "value(status.url)"') do set BACKEND_URL=%%i
for /f "tokens=*" %%i in ('gcloud run services describe customercaregpt-frontend --platform managed --region %REGION% --format "value(status.url)"') do set FRONTEND_URL=%%i

echo Backend API: %BACKEND_URL%
echo Frontend: %FRONTEND_URL%
echo.
echo 🔍 Health Check URLs:
echo Backend Health: %BACKEND_URL%/health
echo Backend Ready: %BACKEND_URL%/ready
echo Backend Metrics: %BACKEND_URL%/metrics
echo.
echo 💡 Next steps:
echo 1. Update your frontend environment variables with the backend URL
echo 2. Test the health endpoints
echo 3. Set up monitoring and alerting
echo 4. Configure custom domain (optional)

goto :eof

REM Function to check deployment status
:status
echo 📊 Checking deployment status...

gcloud projects describe %PROJECT_ID% >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Project '%PROJECT_ID%' exists
    
    echo 📋 Cloud Run Services:
    gcloud run services list --platform managed --region %REGION% --format "table(metadata.name,status.url,status.conditions[0].status)"
    
    echo 🗄️ Cloud SQL Instances:
    gcloud sql instances list --format "table(name,databaseVersion,settings.tier,status)"
    
    echo 🔴 Redis Instances:
    gcloud redis instances list --region %REGION% --format "table(name,memorySizeGb,redisVersion,state"
) else (
    echo ❌ Project '%PROJECT_ID%' not found
)
goto :eof

REM Function to show help
:help
echo CustomerCareGPT Google Cloud Run Deployment Script
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   deploy    Full deployment (setup + deploy)
echo   status    Check deployment status
echo   help      Show this help message
echo.
echo Examples:
echo   %0 deploy     # Full deployment
echo   %0 status     # Check status
goto :eof

REM Main script logic
if "%1"=="deploy" goto deploy
if "%1"=="status" goto status
if "%1"=="help" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help
if "%1"=="" goto deploy

echo ❌ Unknown command: %1
goto help
