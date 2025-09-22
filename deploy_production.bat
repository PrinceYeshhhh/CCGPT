@echo off
REM Production Deployment Script for CustomerCareGPT (Windows)
REM This script handles the complete production deployment process

setlocal enabledelayedexpansion

REM Configuration
set PROJECT_NAME=customercaregpt
set ENVIRONMENT=production
set BACKUP_DIR=.\backups
set LOG_DIR=.\logs

REM Create necessary directories
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Logging function
:log
echo [%date% %time%] %~1
goto :eof

:error
echo [ERROR] %~1 >&2
goto :eof

:success
echo [SUCCESS] %~1
goto :eof

:warning
echo [WARNING] %~1
goto :eof

REM Check prerequisites
:check_prerequisites
call :log "Checking prerequisites..."

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    call :error "Docker is not installed. Please install Docker Desktop first."
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    call :error "Docker Compose is not installed. Please install Docker Compose first."
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    call :error ".env file not found. Please create it from env.example"
    exit /b 1
)

call :success "Prerequisites check passed"
goto :eof

REM Backup existing data
:backup_data
call :log "Creating backup of existing data..."

set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
set backup_path=%BACKUP_DIR%\backup_%timestamp%

if not exist "%backup_path%" mkdir "%backup_path%"

REM Backup database if it exists
docker ps | findstr "%PROJECT_NAME%_postgres" >nul
if not errorlevel 1 (
    call :log "Backing up database..."
    docker exec %PROJECT_NAME%_postgres pg_dump -U customercaregpt customercaregpt > "%backup_path%\database.sql"
    call :success "Database backed up to %backup_path%\database.sql"
)

REM Backup Redis data if it exists
docker ps | findstr "%PROJECT_NAME%_redis" >nul
if not errorlevel 1 (
    call :log "Backing up Redis data..."
    docker exec %PROJECT_NAME%_redis redis-cli --rdb /data/backup.rdb
    docker cp %PROJECT_NAME%_redis:/data/backup.rdb "%backup_path%\redis.rdb"
    call :success "Redis data backed up to %backup_path%\redis.rdb"
)

REM Backup ChromaDB data if it exists
docker ps | findstr "%PROJECT_NAME%_chromadb" >nul
if not errorlevel 1 (
    call :log "Backing up ChromaDB data..."
    docker cp %PROJECT_NAME%_chromadb:/chroma/chroma "%backup_path%\chroma_data"
    call :success "ChromaDB data backed up to %backup_path%\chroma_data"
)

call :success "Backup completed: %backup_path%"
goto :eof

REM Run production readiness tests
:run_tests
call :log "Running production readiness tests..."

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    call :warning "Python not found, skipping comprehensive tests"
    goto :eof
)

REM Run the comprehensive test suite
if exist "test_production_readiness_comprehensive.py" (
    python test_production_readiness_comprehensive.py
    if errorlevel 1 (
        call :error "Production readiness tests failed"
        exit /b 1
    )
    call :success "Production readiness tests passed"
) else (
    call :warning "Comprehensive test script not found, skipping tests"
)
goto :eof

REM Deploy services
:deploy_services
call :log "Building and deploying services..."

REM Stop existing services
call :log "Stopping existing services..."
docker-compose -f docker-compose.prod.yml down --remove-orphans

REM Build and start services
call :log "Building and starting services..."
docker-compose -f docker-compose.prod.yml up --build -d

REM Wait for services to be ready
call :log "Waiting for services to be ready..."
timeout /t 30 /nobreak >nul

REM Check service health
call :check_service_health
goto :eof

REM Check service health
:check_service_health
call :log "Checking service health..."

REM Check if all services are running
set services=postgres redis chromadb backend frontend worker
for %%s in (%services%) do (
    docker ps | findstr "%PROJECT_NAME%_%%s" >nul
    if errorlevel 1 (
        call :error "Service %%s is not running"
        exit /b 1
    ) else (
        call :success "Service %%s is running"
    )
)

REM Check API health
call :log "Checking API health..."
set max_attempts=30
set attempt=1

:health_check_loop
curl -f http://localhost:8000/health >nul 2>&1
if not errorlevel 1 (
    call :success "API is healthy"
    goto :health_check_done
) else (
    call :log "API health check attempt !attempt!/!max_attempts! failed, retrying in 10 seconds..."
    timeout /t 10 /nobreak >nul
    set /a attempt+=1
    if !attempt! leq !max_attempts! goto :health_check_loop
)

call :error "API health check failed after !max_attempts! attempts"
exit /b 1

:health_check_done
REM Check frontend
call :log "Checking frontend..."
curl -f http://localhost/ >nul 2>&1
if not errorlevel 1 (
    call :success "Frontend is accessible"
) else (
    call :error "Frontend is not accessible"
    exit /b 1
)
goto :eof

REM Setup monitoring
:setup_monitoring
call :log "Setting up monitoring..."

REM Create monitoring directory
if not exist ".\monitoring" mkdir ".\monitoring"

REM Create Prometheus configuration
(
echo global:^
echo   scrape_interval: 15s^
echo.^
echo scrape_configs:^
echo   - job_name: 'customercaregpt-api'^
echo     static_configs:^
echo       - targets: ['backend:8000']^
echo     metrics_path: '/metrics'^
echo     scrape_interval: 5s
) > ".\monitoring\prometheus.yml"

call :success "Monitoring configuration created"
goto :eof

REM Setup SSL certificates
:setup_ssl
call :log "Setting up SSL certificates..."

REM Create SSL directory
if not exist ".\ssl" mkdir ".\ssl"

REM Check if SSL certificates exist
if not exist ".\ssl\cert.pem" (
    call :warning "SSL certificates not found. Please place your certificates in .\ssl\ directory"
    call :warning "Files needed: cert.pem and key.pem"
    call :warning "You can use Let's Encrypt or your own certificates"
) else (
    call :success "SSL certificates found"
)
goto :eof

REM Main deployment function
:main
call :log "Starting CustomerCareGPT Production Deployment"
call :log "=============================================="

REM Run all deployment steps
call :check_prerequisites
if errorlevel 1 exit /b 1

call :backup_data
if errorlevel 1 exit /b 1

call :run_tests
if errorlevel 1 exit /b 1

call :deploy_services
if errorlevel 1 exit /b 1

call :setup_monitoring
if errorlevel 1 exit /b 1

call :setup_ssl
if errorlevel 1 exit /b 1

call :success "Deployment completed successfully!"
call :log "=============================================="
call :log "Your CustomerCareGPT application is now running in production mode"
call :log "Frontend: http://localhost (or your domain)"
call :log "API: http://localhost:8000"
call :log "Health Check: http://localhost:8000/health"
call :log "Metrics: http://localhost:8000/metrics"
call :log "=============================================="
call :log "To manage the service:"
call :log "  Start: docker-compose -f docker-compose.prod.yml up -d"
call :log "  Stop: docker-compose -f docker-compose.prod.yml down"
call :log "  Logs: docker-compose -f docker-compose.prod.yml logs -f"
call :log "=============================================="
goto :eof

REM Handle script arguments
if "%1"=="backup" (
    call :backup_data
    goto :eof
)
if "%1"=="test" (
    call :run_tests
    goto :eof
)
if "%1"=="deploy" (
    call :deploy_services
    goto :eof
)
if "%1"=="health" (
    call :check_service_health
    goto :eof
)
if "%1"=="help" (
    echo Usage: %0 [command]
    echo.
    echo Commands:
    echo   backup    - Create backup of existing data
    echo   test      - Run production readiness tests
    echo   deploy    - Deploy services only
    echo   health    - Check service health
    echo   help      - Show this help message
    echo.
    echo If no command is specified, full deployment will be performed
    goto :eof
)

REM Default: run full deployment
call :main
