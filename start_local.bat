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
set REDIS_URL=
set CHROMA_PERSIST_DIRECTORY=./chroma-test
set GEMINI_API_KEY=dummy
set STRIPE_API_KEY=sk_test_dummy
set STRIPE_WEBHOOK_SECRET=
set STRIPE_SUCCESS_URL=http://localhost:5173/billing/success
set STRIPE_CANCEL_URL=http://localhost:5173/billing/cancel
set ENABLE_RATE_LIMITING=false

REM Start backend via robust dev_server (auto-picks free port; fixes PYTHONPATH)
start cmd /c "python -m app.dev_server"
cd ..

REM Frontend env
cd frontend
REM Auto-detect selected backend port written by dev_server
set DEFAULT_BACKEND_PORT=8000

REM Wait up to ~10 seconds for dev_server to write the port file
set SELECTED_BACKEND_PORT=
set /a __wait_count=0
:wait_port_file
if exist "..\backend\.backend_port" (
  for /f "usebackq delims=" %%p in ("..\backend\.backend_port") do set SELECTED_BACKEND_PORT=%%p
)
if "%SELECTED_BACKEND_PORT%"=="" (
  if %__wait_count% GEQ 20 goto use_default_port
  set /a __wait_count+=1
  ping -n 1 127.0.0.1 >nul
  goto wait_port_file
)
goto have_port

:use_default_port
set SELECTED_BACKEND_PORT=%DEFAULT_BACKEND_PORT%

:have_port

set VITE_API_URL=http://127.0.0.1:%SELECTED_BACKEND_PORT%
set VITE_API_BASE_URL=http://127.0.0.1:%SELECTED_BACKEND_PORT%/api/v1
set VITE_WS_URL=ws://127.0.0.1:%SELECTED_BACKEND_PORT%/ws
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
