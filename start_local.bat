@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Backend env
cd backend
set JWT_SECRET=dev-secret
set JWT_ISSUER=customercaregpt
set JWT_AUDIENCE=customercaregpt-users
set ALGORITHM=HS256
set ENVIRONMENT=development
set DEBUG=True
set LOG_LEVEL=DEBUG
set DATABASE_URL=sqlite:///./dev.db
set REDIS_URL=redis://localhost:6379/0
set CHROMA_PERSIST_DIRECTORY=./chroma-test
set GEMINI_API_KEY=dummy
set STRIPE_API_KEY=sk_test_dummy
set STRIPE_WEBHOOK_SECRET=
set STRIPE_SUCCESS_URL=http://localhost:5173/billing/success
set STRIPE_CANCEL_URL=http://localhost:5173/billing/cancel

start cmd /c "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..

REM Frontend env
cd frontend
set VITE_API_URL=http://localhost:8000/api/v1
set VITE_WS_URL=ws://localhost:8000/ws
set VITE_API_BASE_URL=http://localhost:8000
set NODE_ENV=development

start cmd /c "npm run dev"
cd ..

echo Services starting... Backend on http://localhost:8000, Frontend on http://localhost:5173
endlocal
@echo off
REM CustomerCareGPT Local Development Startup Script
REM This script starts the local development environment

echo 🏠 CustomerCareGPT Local Development
echo ====================================

REM Check if Docker is running
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)

echo 📦 Starting local services with Docker Compose...

REM Start services
docker-compose -f docker-compose.local.yml up -d

if errorlevel 1 (
    echo ❌ Failed to start services
    pause
    exit /b 1
)

echo.
echo ✅ Local services started successfully!
echo.
echo 🌐 Services available at:
echo   - Backend API: http://localhost:8000
echo   - API Docs: http://localhost:8000/docs
echo   - Health Check: http://localhost:8000/health
echo   - Redis: localhost:6379
echo   - ChromaDB: http://localhost:8001
echo.
echo 📊 To view logs:
echo   docker-compose -f docker-compose.local.yml logs -f
echo.
echo 🛑 To stop services:
echo   docker-compose -f docker-compose.local.yml down
echo.

REM Wait a moment for services to start
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Test backend health
echo 🔍 Testing backend health...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend is starting up, please wait a moment...
    echo    You can check logs with: docker-compose -f docker-compose.local.yml logs backend
) else (
    echo ✅ Backend is healthy and ready!
)

echo.
echo 🎉 Local development environment is ready!
echo    Frontend (Vercel): https://customercaregpt-frontend.vercel.app
echo    Backend (Local): http://localhost:8000
echo.
pause
