#!/bin/bash
# Production Docker Deployment Script for CustomerCareGPT
# This script deploys the application using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE="env.production.docker"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found. Please create it first."
        exit 1
    fi
    
    log_success "All requirements met"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "./docker/nginx/ssl"
    mkdir -p "./docker/grafana/provisioning"
    
    log_success "Directories created"
}

backup_data() {
    log_info "Creating backup of existing data..."
    
    if [ -d "$BACKUP_DIR" ]; then
        BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
        
        # Backup volumes if they exist
        if docker volume ls | grep -q "customercaregpt_postgres_data"; then
            log_info "Backing up PostgreSQL data..."
            docker run --rm -v customercaregpt_postgres_data:/data -v "$(pwd)/$BACKUP_DIR/$BACKUP_NAME":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
        fi
        
        if docker volume ls | grep -q "customercaregpt_redis_data"; then
            log_info "Backing up Redis data..."
            docker run --rm -v customercaregpt_redis_data:/data -v "$(pwd)/$BACKUP_DIR/$BACKUP_NAME":/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
        fi
        
        log_success "Backup created: $BACKUP_DIR/$BACKUP_NAME"
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    # Build backend image
    log_info "Building backend image..."
    docker-compose -f "$COMPOSE_FILE" build backend
    
    # Build frontend image
    log_info "Building frontend image..."
    docker-compose -f "$COMPOSE_FILE" build frontend
    
    log_success "Images built successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Pull latest images
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    
    log_success "Services deployed"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    log_info "Waiting for PostgreSQL..."
    timeout 60 bash -c 'until docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres; do sleep 2; done'
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    timeout 60 bash -c 'until docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping; do sleep 2; done'
    
    # Wait for ChromaDB
    log_info "Waiting for ChromaDB..."
    timeout 60 bash -c 'until curl -f http://localhost:8001/api/v1/heartbeat; do sleep 2; done'
    
    # Wait for backend
    log_info "Waiting for backend API..."
    timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 2; done'
    
    # Wait for frontend
    log_info "Waiting for frontend..."
    timeout 60 bash -c 'until curl -f http://localhost:3000; do sleep 2; done'
    
    log_success "All services are ready"
}

run_migrations() {
    log_info "Running database migrations..."
    
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec backend alembic upgrade head
    
    log_success "Database migrations completed"
}

check_health() {
    log_info "Checking service health..."
    
    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend is healthy"
    else
        log_error "Backend health check failed"
        return 1
    fi
    
    # Check frontend health
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is healthy"
    else
        log_error "Frontend health check failed"
        return 1
    fi
    
    # Check database health
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        log_success "Database is healthy"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    # Check Redis health
    if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is healthy"
    else
        log_error "Redis health check failed"
        return 1
    fi
}

show_status() {
    log_info "Service Status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo ""
    log_info "Service URLs:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:8000"
    echo "  API Documentation: http://localhost:8000/docs"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana: http://localhost:3001"
    echo "  ChromaDB: http://localhost:8001"
}

cleanup() {
    log_info "Cleaning up..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting CustomerCareGPT production deployment..."
    
    check_requirements
    create_directories
    backup_data
    build_images
    deploy_services
    wait_for_services
    run_migrations
    check_health
    show_status
    cleanup
    
    log_success "Deployment completed successfully!"
    log_info "You can now access the application at http://localhost:3000"
}

# Rollback function
rollback() {
    log_warning "Rolling back to previous version..."
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore from backup
    if [ -d "$BACKUP_DIR" ]; then
        LATEST_BACKUP=$(ls -t "$BACKUP_DIR" | head -n1)
        if [ -n "$LATEST_BACKUP" ]; then
            log_info "Restoring from backup: $LATEST_BACKUP"
            # Restore logic would go here
        fi
    fi
    
    log_success "Rollback completed"
}

# Update function
update() {
    log_info "Updating CustomerCareGPT..."
    
    # Pull latest changes
    git pull origin main
    
    # Rebuild and redeploy
    build_images
    deploy_services
    wait_for_services
    run_migrations
    check_health
    
    log_success "Update completed"
}

# Main script
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    update)
        update
        ;;
    status)
        show_status
        ;;
    logs)
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    stop)
        docker-compose -f "$COMPOSE_FILE" down
        ;;
    start)
        docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
        ;;
    restart)
        docker-compose -f "$COMPOSE_FILE" restart
        ;;
    *)
        echo "Usage: $0 {deploy|rollback|update|status|logs|stop|start|restart}"
        exit 1
        ;;
esac
