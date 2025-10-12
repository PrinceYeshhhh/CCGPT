# CustomerCareGPT Docker Production Deployment

This guide covers deploying CustomerCareGPT using Docker in a production environment.

## 🏗️ Architecture Overview

The production Docker setup includes:

- **Backend API**: FastAPI application with Gunicorn
- **Frontend**: React application served by Nginx
- **PostgreSQL**: Primary database with optimized configuration
- **Redis**: Caching and session storage
- **ChromaDB**: Vector database for embeddings
- **Nginx**: Reverse proxy with SSL termination
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboard
- **Background Workers**: Document processing

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM
- 50GB+ disk space
- SSL certificates (for HTTPS)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd CustomerCareGPT
```

### 2. Configure Environment

```bash
# Copy the production environment template
cp env.production.docker .env

# Edit the environment file with your values
nano .env
```

**Required Environment Variables:**

```bash
# Security (REQUIRED)
SECRET_KEY=your_super_secret_key_here
JWT_SECRET=your_jwt_secret_key_here
POSTGRES_PASSWORD=your_secure_postgres_password

# External Services (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key
STRIPE_API_KEY=sk_live_your_stripe_key

# Domain Configuration (REQUIRED)
PUBLIC_BASE_URL=https://api.yourdomain.com
CORS_ORIGINS=["https://yourdomain.com"]
ALLOWED_HOSTS=["yourdomain.com"]
```

### 3. Deploy

```bash
# Make deployment script executable
chmod +x deploy-docker-prod.sh

# Deploy the application
./deploy-docker-prod.sh deploy
```

### 4. Verify Deployment

```bash
# Check service status
./deploy-docker-prod.sh status

# View logs
./deploy-docker-prod.sh logs

# Check health
curl http://localhost:8000/health
```

## 🔧 Configuration

### Database Configuration

PostgreSQL is configured with production-optimized settings:

- **Memory**: 2GB limit, 1GB reserved
- **Connections**: 200 max connections
- **WAL**: Optimized for write performance
- **Logging**: Query performance monitoring

### Redis Configuration

Redis is configured for caching and session storage:

- **Memory**: 512MB limit with LRU eviction
- **Persistence**: AOF + RDB snapshots
- **Performance**: 4 I/O threads

### Backend Configuration

The backend runs with:

- **Gunicorn**: 4 workers with Uvicorn
- **Memory**: 4GB limit, 2GB reserved
- **CPU**: 2 cores limit, 1 core reserved
- **Health Checks**: Comprehensive monitoring

## 📊 Monitoring

### Prometheus Metrics

Access Prometheus at `http://localhost:9090` to view:

- HTTP request metrics
- Database connection pool usage
- Redis memory usage
- Application performance metrics

### Grafana Dashboard

Access Grafana at `http://localhost:3001` (admin/password):

- System resource usage
- Application performance
- Database performance
- Custom business metrics

### Health Endpoints

- **Liveness**: `GET /health`
- **Readiness**: `GET /ready`
- **Detailed**: `GET /health/detailed`
- **External**: `GET /health/external`

## 🔒 Security Features

### Network Security

- **Isolated Network**: All services run in isolated Docker network
- **No External Ports**: Only necessary ports exposed
- **Internal Communication**: Services communicate via internal network

### Application Security

- **Security Headers**: Comprehensive security headers via Nginx
- **Rate Limiting**: Per-endpoint rate limiting
- **Input Validation**: Comprehensive input sanitization
- **CSRF Protection**: Token-based CSRF protection
- **Authentication**: JWT-based authentication

### Data Security

- **Encrypted Storage**: All data encrypted at rest
- **Secure Communication**: HTTPS/TLS for all external communication
- **Password Hashing**: bcrypt with 12 rounds
- **Secret Management**: Environment-based secret management

## 📈 Performance Optimization

### Resource Limits

Each service has defined resource limits:

```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 2G
      cpus: '1.0'
```

### Caching Strategy

- **Redis**: API response caching
- **Nginx**: Static asset caching
- **Database**: Connection pooling
- **Vector Search**: ChromaDB caching

### Scaling

To scale the application:

```bash
# Scale backend workers
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Scale background workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=2
```

## 🛠️ Management Commands

### Deployment Script

```bash
# Deploy application
./deploy-docker-prod.sh deploy

# Update application
./deploy-docker-prod.sh update

# Rollback deployment
./deploy-docker-prod.sh rollback

# Check status
./deploy-docker-prod.sh status

# View logs
./deploy-docker-prod.sh logs

# Stop services
./deploy-docker-prod.sh stop

# Start services
./deploy-docker-prod.sh start

# Restart services
./deploy-docker-prod.sh restart
```

### Docker Compose Commands

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Stop all services
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Execute commands in containers
docker-compose -f docker-compose.prod.yml exec backend bash
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres
```

## 🔄 Backup and Recovery

### Automated Backups

The deployment script automatically creates backups before deployment:

```bash
# Manual backup
./deploy-docker-prod.sh backup

# Restore from backup
./deploy-docker-prod.sh restore backup_20240101_120000
```

### Database Backups

```bash
# Create database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres customercaregpt > backup.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres customercaregpt < backup.sql
```

### Volume Backups

```bash
# Backup all volumes
docker run --rm -v customercaregpt_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .
docker run --rm -v customercaregpt_redis_data:/data -v $(pwd):/backup alpine tar czf /backup/redis_backup.tar.gz -C /data .
```

## 🚨 Troubleshooting

### Common Issues

**1. Services won't start**

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check resource usage
docker stats

# Check disk space
df -h
```

**2. Database connection issues**

```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.core.database import get_db; print('DB OK')"
```

**3. High memory usage**

```bash
# Check memory usage
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Scale down if needed
docker-compose -f docker-compose.prod.yml up -d --scale backend=2
```

**4. SSL certificate issues**

```bash
# Check certificate files
ls -la docker/nginx/ssl/

# Test SSL configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

### Log Locations

- **Application Logs**: `./logs/`
- **Nginx Logs**: `docker/nginx/logs/`
- **Database Logs**: `docker-compose logs postgres`
- **Redis Logs**: `docker-compose logs redis`

### Health Check Script

```bash
# Run comprehensive health check
docker-compose -f docker-compose.prod.yml exec backend /app/docker/healthcheck.sh
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Configuration](https://www.postgresql.org/docs/current/runtime-config.html)
- [Redis Configuration](https://redis.io/docs/management/config/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)

## 🤝 Support

For production support and issues:

1. Check the logs first
2. Run health checks
3. Review this documentation
4. Contact the development team

---

**Note**: This is a production-ready configuration. Ensure all environment variables are properly set and SSL certificates are configured before deploying to production.
