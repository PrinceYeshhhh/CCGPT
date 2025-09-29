@echo off
REM CustomerCareGPT Vercel Deployment Script for Windows
REM This script automates the deployment of the frontend to Vercel

setlocal enabledelayedexpansion

REM Configuration
set FRONTEND_DIR=frontend
set PROJECT_NAME=customercaregpt-frontend

echo 🚀 CustomerCareGPT Vercel Deployment
echo ===================================
echo Frontend Directory: %FRONTEND_DIR%
echo Project Name: %PROJECT_NAME%
echo.

REM Check prerequisites
echo 🔍 Checking prerequisites...

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install it first.
    echo Install from: https://nodejs.org/
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ npm is not installed. Please install it first.
    exit /b 1
)

where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Vercel CLI is not installed. Installing now...
    npm install -g vercel
)

REM Check if user is authenticated with Vercel
vercel whoami >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Not authenticated with Vercel. Please run 'vercel login' first.
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Main deployment function
:deploy
echo 📦 Installing dependencies...
cd %FRONTEND_DIR%
npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    exit /b 1
)

echo ✅ Dependencies installed

echo 🔨 Building project...
npm run build
if %errorlevel% neq 0 (
    echo ❌ Failed to build project
    exit /b 1
)

echo ✅ Project built successfully

echo 🚀 Deploying to Vercel...

REM Check if project is already linked
if exist ".vercel\project.json" (
    echo 📋 Project already linked to Vercel
) else (
    echo 🔗 Linking project to Vercel...
    vercel link --yes
    if %errorlevel% neq 0 (
        echo ❌ Failed to link project
        exit /b 1
    )
)

REM Deploy to preview
echo 🚀 Deploying to preview...
vercel --yes
if %errorlevel% neq 0 (
    echo ❌ Failed to deploy to preview
    exit /b 1
)

REM Deploy to production
echo 🚀 Deploying to production...
vercel --prod --yes
if %errorlevel% neq 0 (
    echo ❌ Failed to deploy to production
    exit /b 1
)

cd ..

echo ✅ Deployment completed
echo.
echo 📋 Next steps:
echo 1. Set up environment variables in Vercel dashboard
echo 2. Configure your custom domain (optional)
echo 3. Test your deployment

goto :eof

REM Function to install dependencies
:install
echo 📦 Installing dependencies...
cd %FRONTEND_DIR%
npm install
cd ..
echo ✅ Dependencies installed
goto :eof

REM Function to build project
:build
echo 🔨 Building project...
cd %FRONTEND_DIR%
npm run build
cd ..
echo ✅ Project built successfully
goto :eof

REM Function to set environment variables
:env
echo 🔧 Setting up environment variables...
cd %FRONTEND_DIR%

set /p BACKEND_URL="Enter your Google Cloud Run backend URL (e.g., https://customercaregpt-backend-xxxxx-uc.a.run.app): "

if "%BACKEND_URL%"=="" (
    echo ❌ Backend URL is required
    exit /b 1
)

echo 🔧 Setting VITE_API_URL...
vercel env add VITE_API_URL production
vercel env add VITE_API_URL preview

echo 🔧 Setting VITE_WS_URL...
vercel env add VITE_WS_URL production
vercel env add VITE_WS_URL preview

cd ..

echo ✅ Environment variables set
echo.
echo 💡 Don't forget to update the values in Vercel dashboard:
echo VITE_API_URL: %BACKEND_URL%/api/v1
echo VITE_WS_URL: wss://%BACKEND_URL:~8%/ws
goto :eof

REM Function to show deployment status
:status
echo 📊 Checking deployment status...
cd %FRONTEND_DIR%

if exist ".vercel\project.json" (
    echo ✅ Project is linked to Vercel
    
    echo 📋 Project Information:
    vercel inspect
    
    echo 📋 Recent Deployments:
    vercel ls --limit 5
    
    echo 🔧 Environment Variables:
    vercel env ls
) else (
    echo ❌ Project is not linked to Vercel
    echo Run: %0 deploy to link and deploy
)

cd ..
goto :eof

REM Function to open Vercel dashboard
:open
echo 🌐 Opening Vercel dashboard...
cd %FRONTEND_DIR%

if exist ".vercel\project.json" (
    vercel open
) else (
    echo ❌ Project is not linked to Vercel
    echo Run: %0 deploy to link and deploy
)

cd ..
goto :eof

REM Function to show help
:help
echo CustomerCareGPT Vercel Deployment Script
echo.
echo Usage: %0 [COMMAND]
echo.
echo Commands:
echo   deploy    Full deployment (install + build + deploy)
echo   install   Install dependencies only
echo   build     Build project only
echo   env       Set environment variables
echo   status    Check deployment status
echo   open      Open Vercel dashboard
echo   help      Show this help message
echo.
echo Examples:
echo   %0 deploy     # Full deployment
echo   %0 status     # Check status
echo   %0 env        # Set environment variables
goto :eof

REM Main script logic
if "%1"=="deploy" goto deploy
if "%1"=="install" goto install
if "%1"=="build" goto build
if "%1"=="env" goto env
if "%1"=="status" goto status
if "%1"=="open" goto open
if "%1"=="help" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help
if "%1"=="" goto deploy

echo ❌ Unknown command: %1
goto help
