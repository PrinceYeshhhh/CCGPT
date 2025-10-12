#!/bin/bash
# Docker Health Check Script for CustomerCareGPT Backend
# This script performs comprehensive health checks

set -e

# Configuration
BACKEND_URL="http://localhost:8000"
TIMEOUT=10
MAX_RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[HEALTH]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Health check functions
check_backend_health() {
    log_info "Checking backend health endpoint..."
    
    response=$(curl -s -w "%{http_code}" -o /dev/null --max-time $TIMEOUT "$BACKEND_URL/health" || echo "000")
    
    if [ "$response" = "200" ]; then
        log_info "Backend health check passed"
        return 0
    else
        log_error "Backend health check failed (HTTP $response)"
        return 1
    fi
}

check_backend_ready() {
    log_info "Checking backend readiness endpoint..."
    
    response=$(curl -s -w "%{http_code}" -o /dev/null --max-time $TIMEOUT "$BACKEND_URL/ready" || echo "000")
    
    if [ "$response" = "200" ]; then
        log_info "Backend readiness check passed"
        return 0
    else
        log_error "Backend readiness check failed (HTTP $response)"
        return 1
    fi
}

check_database_connection() {
    log_info "Checking database connection..."
    
    # Check if we can connect to the database
    python3 -c "
import os
import sys
import psycopg2
from urllib.parse import urlparse

try:
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print('DATABASE_URL not set')
        sys.exit(1)
    
    parsed = urlparse(db_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password
    )
    conn.close()
    print('Database connection successful')
    sys.exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "Database connection check passed"
        return 0
    else
        log_error "Database connection check failed"
        return 1
    fi
}

check_redis_connection() {
    log_info "Checking Redis connection..."
    
    python3 -c "
import os
import sys
import redis

try:
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print('REDIS_URL not set')
        sys.exit(1)
    
    r = redis.from_url(redis_url)
    r.ping()
    print('Redis connection successful')
    sys.exit(0)
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "Redis connection check passed"
        return 0
    else
        log_error "Redis connection check failed"
        return 1
    fi
}

check_chromadb_connection() {
    log_info "Checking ChromaDB connection..."
    
    python3 -c "
import os
import sys
import requests

try:
    chroma_url = os.getenv('CHROMA_URL', 'http://chromadb:8001')
    response = requests.get(f'{chroma_url}/api/v1/heartbeat', timeout=5)
    if response.status_code == 200:
        print('ChromaDB connection successful')
        sys.exit(0)
    else:
        print(f'ChromaDB health check failed: HTTP {response.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'ChromaDB connection failed: {e}')
    sys.exit(1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log_info "ChromaDB connection check passed"
        return 0
    else
        log_error "ChromaDB connection check failed"
        return 1
    fi
}

check_disk_space() {
    log_info "Checking disk space..."
    
    # Check if we have at least 1GB free space
    available_space=$(df /app | awk 'NR==2 {print $4}')
    required_space=1048576  # 1GB in KB
    
    if [ "$available_space" -gt "$required_space" ]; then
        log_info "Disk space check passed"
        return 0
    else
        log_error "Insufficient disk space (available: ${available_space}KB, required: ${required_space}KB)"
        return 1
    fi
}

check_memory_usage() {
    log_info "Checking memory usage..."
    
    # Check if memory usage is below 90%
    memory_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ "$memory_usage" -lt 90 ]; then
        log_info "Memory usage check passed (${memory_usage}%)"
        return 0
    else
        log_warning "High memory usage (${memory_usage}%)"
        return 1
    fi
}

# Main health check function
main() {
    log_info "Starting comprehensive health check..."
    
    local exit_code=0
    
    # Run all health checks
    check_backend_health || exit_code=1
    check_backend_ready || exit_code=1
    check_database_connection || exit_code=1
    check_redis_connection || exit_code=1
    check_chromadb_connection || exit_code=1
    check_disk_space || exit_code=1
    check_memory_usage || exit_code=1
    
    if [ $exit_code -eq 0 ]; then
        log_info "All health checks passed"
    else
        log_error "Some health checks failed"
    fi
    
    exit $exit_code
}

# Run main function
main "$@"
