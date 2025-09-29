#!/bin/bash
# ============================================
# Google Cloud Run Deployment Configuration Loader
# ============================================
# This script loads the appropriate environment configuration
# Usage: source gcp/deploy-config.sh [production|staging|development]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-production}

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment configuration
load_config() {
    local env_file="gcp/${ENVIRONMENT}.env"
    
    if [[ ! -f "$env_file" ]]; then
        print_error "Environment file not found: $env_file"
        print_error "Available environments: production, staging, development"
        exit 1
    fi
    
    print_status "Loading configuration for environment: $ENVIRONMENT"
    source "$env_file"
    print_success "Configuration loaded from $env_file"
}

# Validate required variables
validate_config() {
    local required_vars=(
        "PROJECT_ID"
        "REGION"
        "SERVICE_ACCOUNT"
        "BACKEND_SERVICE_NAME"
        "FRONTEND_SERVICE_NAME"
        "WORKER_SERVICE_NAME"
        "CHROMADB_SERVICE_NAME"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            print_error "Required variable $var is not set"
            exit 1
        fi
    done
    
    print_success "All required variables are set"
}

# Display current configuration
show_config() {
    print_status "Current deployment configuration:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Project ID: $PROJECT_ID"
    echo "  Region: $REGION"
    echo "  Service Account: $SERVICE_ACCOUNT"
    echo "  Backend Service: $BACKEND_SERVICE_NAME"
    echo "  Frontend Service: $FRONTEND_SERVICE_NAME"
    echo "  Worker Service: $WORKER_SERVICE_NAME"
    echo "  ChromaDB Service: $CHROMADB_SERVICE_NAME"
    echo "  CPU Limit: $CPU_LIMIT"
    echo "  Memory Limit: $MEMORY_LIMIT"
    echo "  Max Instances: $MAX_INSTANCES"
    echo "  Min Instances: $MIN_INSTANCES"
}

# Main execution
main() {
    print_status "Google Cloud Run Deployment Configuration Loader"
    print_status "================================================="
    
    load_config
    validate_config
    show_config
    
    print_success "Configuration ready for deployment!"
    print_status "You can now run deployment commands with these variables"
}

# Run main function
main "$@"
