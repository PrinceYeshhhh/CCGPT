#!/bin/bash

# CustomerCareGPT Vercel Deployment Script
# This script automates the deployment of the frontend to Vercel

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DIR="frontend"
PROJECT_NAME="customercaregpt-frontend"

echo -e "${BLUE}🚀 CustomerCareGPT Vercel Deployment${NC}"
echo -e "${BLUE}===================================${NC}"
echo "Frontend Directory: $FRONTEND_DIR"
echo "Project Name: $PROJECT_NAME"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install it first.${NC}"
    echo "Install from: https://nodejs.org/"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed. Please install it first.${NC}"
    exit 1
fi

if ! command_exists vercel; then
    echo -e "${YELLOW}⚠️  Vercel CLI is not installed. Installing now...${NC}"
    npm install -g vercel
fi

# Check if user is authenticated with Vercel
if ! vercel whoami >/dev/null 2>&1; then
    echo -e "${RED}❌ Not authenticated with Vercel. Please run 'vercel login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Function to install dependencies
install_dependencies() {
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    
    cd "$FRONTEND_DIR"
    npm install
    cd ..
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Function to build the project
build_project() {
    echo -e "${YELLOW}🔨 Building project...${NC}"
    
    cd "$FRONTEND_DIR"
    npm run build
    cd ..
    
    echo -e "${GREEN}✅ Project built successfully${NC}"
}

# Function to deploy to Vercel
deploy_to_vercel() {
    echo -e "${YELLOW}🚀 Deploying to Vercel...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # Check if project is already linked
    if [ -f ".vercel/project.json" ]; then
        echo -e "${YELLOW}📋 Project already linked to Vercel${NC}"
    else
        echo -e "${YELLOW}🔗 Linking project to Vercel...${NC}"
        vercel link --yes
    fi
    
    # Deploy to preview
    echo -e "${YELLOW}🚀 Deploying to preview...${NC}"
    PREVIEW_URL=$(vercel --yes)
    
    # Deploy to production
    echo -e "${YELLOW}🚀 Deploying to production...${NC}"
    PRODUCTION_URL=$(vercel --prod --yes)
    
    cd ..
    
    echo -e "${GREEN}✅ Deployment completed${NC}"
    echo ""
    echo -e "${BLUE}📋 Deployment URLs:${NC}"
    echo "Preview: $PREVIEW_URL"
    echo "Production: $PRODUCTION_URL"
}

# Function to set environment variables
set_environment_variables() {
    echo -e "${YELLOW}🔧 Setting up environment variables...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # Get backend URL from user
    read -p "Enter your Google Cloud Run backend URL (e.g., https://customercaregpt-backend-xxxxx-uc.a.run.app): " BACKEND_URL
    
    if [ -z "$BACKEND_URL" ]; then
        echo -e "${RED}❌ Backend URL is required${NC}"
        exit 1
    fi
    
    # Set environment variables
    echo -e "${YELLOW}🔧 Setting VITE_API_URL...${NC}"
    vercel env add VITE_API_URL production
    vercel env add VITE_API_URL preview
    
    echo -e "${YELLOW}🔧 Setting VITE_WS_URL...${NC}"
    vercel env add VITE_WS_URL production
    vercel env add VITE_WS_URL preview
    
    cd ..
    
    echo -e "${GREEN}✅ Environment variables set${NC}"
    echo ""
    echo -e "${YELLOW}💡 Don't forget to update the values in Vercel dashboard:${NC}"
    echo "VITE_API_URL: $BACKEND_URL/api/v1"
    echo "VITE_WS_URL: wss://$(echo $BACKEND_URL | sed 's/https:\/\///')/ws"
}

# Function to show deployment status
show_status() {
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    
    cd "$FRONTEND_DIR"
    
    if [ -f ".vercel/project.json" ]; then
        echo -e "${GREEN}✅ Project is linked to Vercel${NC}"
        
        # Show project information
        echo -e "${YELLOW}📋 Project Information:${NC}"
        vercel inspect
        
        # Show deployments
        echo -e "${YELLOW}📋 Recent Deployments:${NC}"
        vercel ls --limit 5
        
        # Show environment variables
        echo -e "${YELLOW}🔧 Environment Variables:${NC}"
        vercel env ls
    else
        echo -e "${RED}❌ Project is not linked to Vercel${NC}"
        echo "Run: $0 deploy to link and deploy"
    fi
    
    cd ..
}

# Function to open Vercel dashboard
open_dashboard() {
    echo -e "${YELLOW}🌐 Opening Vercel dashboard...${NC}"
    
    cd "$FRONTEND_DIR"
    
    if [ -f ".vercel/project.json" ]; then
        vercel open
    else
        echo -e "${RED}❌ Project is not linked to Vercel${NC}"
        echo "Run: $0 deploy to link and deploy"
    fi
    
    cd ..
}

# Function to show help
show_help() {
    echo -e "${BLUE}CustomerCareGPT Vercel Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  deploy    Full deployment (install + build + deploy)"
    echo "  install   Install dependencies only"
    echo "  build     Build project only"
    echo "  deploy-only  Deploy to Vercel only"
    echo "  env       Set environment variables"
    echo "  status    Check deployment status"
    echo "  open      Open Vercel dashboard"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy     # Full deployment"
    echo "  $0 status     # Check status"
    echo "  $0 env        # Set environment variables"
}

# Main deployment function
deploy() {
    install_dependencies
    build_project
    deploy_to_vercel
    set_environment_variables
    show_status
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    install)
        install_dependencies
        ;;
    build)
        build_project
        ;;
    deploy-only)
        deploy_to_vercel
        ;;
    env)
        set_environment_variables
        ;;
    status)
        show_status
        ;;
    open)
        open_dashboard
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
