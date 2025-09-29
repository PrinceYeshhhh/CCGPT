#!/bin/bash
# CustomerCareGPT Local Development Startup Script
# This script starts the local development environment

set -e

echo "🏠 CustomerCareGPT Local Development"
echo "===================================="

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker and try again"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi

echo "📦 Starting local services with Docker Compose..."

# Start services
docker-compose -f docker-compose.local.yml up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services"
    exit 1
fi

echo ""
echo "✅ Local services started successfully!"
echo ""
echo "🌐 Services available at:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo "  - Redis: localhost:6379"
echo "  - ChromaDB: http://localhost:8001"
echo ""
echo "📊 To view logs:"
echo "  docker-compose -f docker-compose.local.yml logs -f"
echo ""
echo "🛑 To stop services:"
echo "  docker-compose -f docker-compose.local.yml down"
echo ""

# Wait a moment for services to start
echo "⏳ Waiting for services to be ready..."
sleep 10

# Test backend health
echo "🔍 Testing backend health..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy and ready!"
else
    echo "⚠️  Backend is starting up, please wait a moment..."
    echo "   You can check logs with: docker-compose -f docker-compose.local.yml logs backend"
fi

echo ""
echo "🎉 Local development environment is ready!"
echo "   Frontend (Vercel): https://customercaregpt-frontend.vercel.app"
echo "   Backend (Local): http://localhost:8000"
echo ""
