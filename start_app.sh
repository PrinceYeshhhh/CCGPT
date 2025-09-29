#!/bin/bash

# CustomerCareGPT Application Startup Script
# This script starts all necessary services for the application

set -e

echo "🚀 Starting CustomerCareGPT Application..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] && [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "🔍 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

if ! command_exists node; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

if ! command_exists redis-server; then
    echo "❌ Redis is required but not installed"
    exit 1
fi

echo "✅ All dependencies found"

# Start Redis if not running
echo "🔧 Starting Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes
    echo "✅ Redis started"
else
    echo "✅ Redis already running"
fi

# Start backend
echo "🔧 Starting Backend..."
cd backend

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Start FastAPI server
echo "🚀 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Start document processing workers
echo "🔧 Starting document processing workers..."
python start_workers.py &
WORKERS_PID=$!

cd ..

# Start frontend
echo "🔧 Starting Frontend..."
cd frontend

# Install Node dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Start Vite dev server
echo "🚀 Starting Vite dev server..."
npm run dev &
FRONTEND_PID=$!

cd ..

echo ""
echo "🎉 CustomerCareGPT is starting up!"
echo "=================================="
echo "📊 Backend API: https://customercaregpt-backend-xxxxx-uc.a.run.app"
echo "📊 API Docs: https://customercaregpt-backend-xxxxx-uc.a.run.app/api/docs"
echo "🌐 Frontend: https://customercaregpt-frontend.vercel.app"
echo "🔧 Redis: customercaregpt-redis.xxxxx.cache.amazonaws.com:6379"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    # Kill all background processes
    kill $BACKEND_PID 2>/dev/null || true
    kill $WORKERS_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for all background processes
wait
