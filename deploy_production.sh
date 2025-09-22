#!/bin/bash

# Production Deployment Script for CustomerCareGPT
# This script handles the complete production deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="customercaregpt"
ENVIRONMENT="production"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Create necessary directories
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        error ".env file not found. Please create it from env.example"
        exit 1
    fi
    
    # Check if required environment variables are set
    source .env
    required_vars=("POSTGRES_PASSWORD" "REDIS_PASSWORD" "GEMINI_API_KEY" "SECRET_KEY" "STRIPE_API_KEY")
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    success "Prerequisites check passed"
}

# Backup existing data
backup_data() {
    log "Creating backup of existing data..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_path="$BACKUP_DIR/backup_$timestamp"
    
    mkdir -p "$backup_path"
    
    # Backup database if it exists
    if docker ps | grep -q "${PROJECT_NAME}_postgres"; then
        log "Backing up database..."
        docker exec "${PROJECT_NAME}_postgres" pg_dump -U customercaregpt customercaregpt > "$backup_path/database.sql"
        success "Database backed up to $backup_path/database.sql"
    fi
    
    # Backup Redis data if it exists
    if docker ps | grep -q "${PROJECT_NAME}_redis"; then
        log "Backing up Redis data..."
        docker exec "${PROJECT_NAME}_redis" redis-cli --rdb /data/backup.rdb
        docker cp "${PROJECT_NAME}_redis:/data/backup.rdb" "$backup_path/redis.rdb"
        success "Redis data backed up to $backup_path/redis.rdb"
    fi
    
    # Backup ChromaDB data if it exists
    if docker ps | grep -q "${PROJECT_NAME}_chromadb"; then
        log "Backing up ChromaDB data..."
        docker cp "${PROJECT_NAME}_chromadb:/chroma/chroma" "$backup_path/chroma_data"
        success "ChromaDB data backed up to $backup_path/chroma_data"
    fi
    
    success "Backup completed: $backup_path"
}

# Run production readiness tests
run_tests() {
    log "Running production readiness tests..."
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        warning "Python3 not found, skipping comprehensive tests"
        return
    fi
    
    # Run the comprehensive test suite
    if [ -f "test_production_readiness_comprehensive.py" ]; then
        python3 test_production_readiness_comprehensive.py
        if [ $? -ne 0 ]; then
            error "Production readiness tests failed"
            exit 1
        fi
        success "Production readiness tests passed"
    else
        warning "Comprehensive test script not found, skipping tests"
    fi
}

# Build and deploy services
deploy_services() {
    log "Building and deploying services..."
    
    # Stop existing services
    log "Stopping existing services..."
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    
    # Build and start services
    log "Building and starting services..."
    docker-compose -f docker-compose.prod.yml up --build -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    # Check if all services are running
    services=("postgres" "redis" "chromadb" "backend" "frontend" "worker")
    
    for service in "${services[@]}"; do
        if docker ps | grep -q "${PROJECT_NAME}_${service}"; then
            success "Service $service is running"
        else
            error "Service $service is not running"
            exit 1
        fi
    done
    
    # Check API health
    log "Checking API health..."
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            success "API is healthy"
            break
        else
            log "API health check attempt $attempt/$max_attempts failed, retrying in 10 seconds..."
            sleep 10
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        error "API health check failed after $max_attempts attempts"
        exit 1
    fi
    
    # Check frontend
    log "Checking frontend..."
    if curl -f http://localhost/ > /dev/null 2>&1; then
        success "Frontend is accessible"
    else
        error "Frontend is not accessible"
        exit 1
    fi
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring directory
    mkdir -p ./monitoring
    
    # Create Prometheus configuration
    cat > ./monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'customercaregpt-api'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
EOF
    
    # Create Grafana dashboard configuration
    cat > ./monitoring/grafana-dashboard.json << EOF
{
  "dashboard": {
    "title": "CustomerCareGPT Production Dashboard",
    "panels": [
      {
        "title": "API Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"customercaregpt-api\"}",
            "legendFormat": "API Status"
          }
        ]
      }
    ]
  }
}
EOF
    
    success "Monitoring configuration created"
}

# Setup SSL certificates
setup_ssl() {
    log "Setting up SSL certificates..."
    
    # Create SSL directory
    mkdir -p ./ssl
    
    # Check if SSL certificates exist
    if [ ! -f "./ssl/cert.pem" ] || [ ! -f "./ssl/key.pem" ]; then
        warning "SSL certificates not found. Please place your certificates in ./ssl/ directory"
        warning "Files needed: cert.pem and key.pem"
        warning "You can use Let's Encrypt or your own certificates"
    else
        success "SSL certificates found"
    fi
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/customercaregpt > /dev/null << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $(whoami) $(whoami)
    postrotate
        docker-compose -f $(pwd)/docker-compose.prod.yml restart backend worker
    endscript
}
EOF
    
    success "Log rotation configured"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        # Allow SSH
        sudo ufw allow ssh
        
        # Allow HTTP and HTTPS
        sudo ufw allow 80
        sudo ufw allow 443
        
        # Allow API port (if needed for direct access)
        sudo ufw allow 8000
        
        # Enable firewall
        sudo ufw --force enable
        
        success "Firewall configured"
    else
        warning "UFW not available, please configure firewall manually"
    fi
}

# Setup systemd service
setup_systemd() {
    log "Setting up systemd service..."
    
    # Create systemd service file
    sudo tee /etc/systemd/system/customercaregpt.service > /dev/null << EOF
[Unit]
Description=CustomerCareGPT Production Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable customercaregpt.service
    
    success "Systemd service configured"
}

# Main deployment function
main() {
    log "Starting CustomerCareGPT Production Deployment"
    log "=============================================="
    
    # Run all deployment steps
    check_root
    check_prerequisites
    backup_data
    run_tests
    deploy_services
    setup_monitoring
    setup_ssl
    setup_log_rotation
    setup_firewall
    setup_systemd
    
    success "Deployment completed successfully!"
    log "=============================================="
    log "Your CustomerCareGPT application is now running in production mode"
    log "Frontend: http://localhost (or your domain)"
    log "API: http://localhost:8000"
    log "Health Check: http://localhost:8000/health"
    log "Metrics: http://localhost:8000/metrics"
    log "=============================================="
    log "To manage the service:"
    log "  Start: sudo systemctl start customercaregpt"
    log "  Stop: sudo systemctl stop customercaregpt"
    log "  Status: sudo systemctl status customercaregpt"
    log "  Logs: docker-compose -f docker-compose.prod.yml logs -f"
    log "=============================================="
}

# Handle script arguments
case "${1:-}" in
    "backup")
        backup_data
        ;;
    "test")
        run_tests
        ;;
    "deploy")
        deploy_services
        ;;
    "health")
        check_service_health
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  backup    - Create backup of existing data"
        echo "  test      - Run production readiness tests"
        echo "  deploy    - Deploy services only"
        echo "  health    - Check service health"
        echo "  help      - Show this help message"
        echo ""
        echo "If no command is specified, full deployment will be performed"
        ;;
    *)
        main
        ;;
esac
