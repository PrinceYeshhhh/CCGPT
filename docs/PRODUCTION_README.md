# CustomerCareGPT Production Deployment Guide

This guide covers production deployment, monitoring, scaling, and maintenance for CustomerCareGPT.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Database Setup](#database-setup)
4. [Deployment](#deployment)
5. [Monitoring & Observability](#monitoring--observability)
6. [Scaling](#scaling)
7. [Backup & Recovery](#backup--recovery)
8. [Security](#security)
9. [Maintenance](#maintenance)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### Infrastructure Requirements

- **Kubernetes cluster** (1.21+) or Docker Swarm
- **PostgreSQL 15+** with 100GB+ storage
- **Redis 7+** with persistence enabled
- **ChromaDB** (standalone or managed)
- **Load balancer** (nginx, traefik, or cloud LB)
- **SSL/TLS certificates**
- **Monitoring stack** (Prometheus + Grafana)
- **Log aggregation** (ELK stack or cloud logging)

### Resource Requirements

| Component | CPU | Memory | Storage | Replicas |
|-----------|-----|--------|---------|----------|
| Backend API | 500m | 1Gi | 1Gi | 3-10 |
| Worker | 250m | 512Mi | 1Gi | 2-5 |
| Frontend | 100m | 128Mi | 100Mi | 2-3 |
| PostgreSQL | 1000m | 2Gi | 100GB+ | 1-3 |
| Redis | 200m | 512Mi | 10GB | 1-3 |
| ChromaDB | 500m | 1Gi | 50GB | 1-3 |

## Environment Setup

### 1. Create Kubernetes Namespace

```bash
kubectl create namespace customercaregpt
kubectl config set-context --current --namespace=customercaregpt
```

### 2. Create Secrets

```bash
# Create secrets file
cat > secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: customercaregpt-secrets
type: Opaque
data:
  database-url: $(echo -n "postgresql://user:pass@host:5432/db" | base64)
  redis-url: $(echo -n "redis://user:pass@host:6379" | base64)
  gemini-api-key: $(echo -n "your-gemini-key" | base64)
  secret-key: $(echo -n "your-secret-key" | base64)
  stripe-api-key: $(echo -n "sk_live_..." | base64)
  stripe-webhook-secret: $(echo -n "whsec_..." | base64)
EOF

kubectl apply -f secrets.yaml
```

### 3. Configure Environment Variables

```bash
# Create config map
cat > config.yaml << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: customercaregpt-config
data:
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  RATE_LIMIT_WORKSPACE_PER_MIN: "60"
  RATE_LIMIT_EMBED_PER_MIN: "600"
  DB_POOL_SIZE: "20"
  DB_MAX_OVERFLOW: "10"
  VECTOR_CACHE_TTL: "600"
EOF

kubectl apply -f config.yaml
```

## Database Setup

### 1. PostgreSQL Configuration

```sql
-- Create database and user
CREATE DATABASE customercaregpt;
CREATE USER customercaregpt WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE customercaregpt TO customercaregpt;

-- Configure connection limits
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Restart PostgreSQL
SELECT pg_reload_conf();
```

### 2. Run Database Migrations

```bash
# Run migrations
kubectl run migration-job --image=customercaregpt/backend:latest \
  --restart=Never --rm -it -- \
  alembic upgrade head
```

## Deployment

### 1. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 2. Deploy with Kubernetes

```bash
# Deploy all components
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
kubectl get ingress
```

### 3. Configure Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: customercaregpt-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - api.customercaregpt.com
    - app.customercaregpt.com
    secretName: customercaregpt-tls
  rules:
  - host: api.customercaregpt.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: customercaregpt-backend-service
            port:
              number: 8000
  - host: app.customercaregpt.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: customercaregpt-frontend-service
            port:
              number: 80
```

## Monitoring & Observability

### 1. Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'customercaregpt-backend'
    static_configs:
      - targets: ['customercaregpt-backend-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

### 2. Grafana Dashboards

Import the following dashboards:
- [Kubernetes Cluster Monitoring](https://grafana.com/grafana/dashboards/315)
- [PostgreSQL Database](https://grafana.com/grafana/dashboards/9628)
- [Redis Monitoring](https://grafana.com/grafana/dashboards/763)
- Custom CustomerCareGPT dashboard (see `monitoring/grafana/`)

### 3. Alert Rules

```yaml
# alerts.yml
groups:
- name: customercaregpt
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} errors per second"

  - alert: DatabaseDown
    expr: up{job="postgres"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "PostgreSQL is down"

  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
```

## Scaling

### 1. Horizontal Pod Autoscaling

```bash
# Check HPA status
kubectl get hpa

# Scale manually if needed
kubectl scale deployment customercaregpt-backend --replicas=5
```

### 2. Database Scaling

```bash
# Read replicas for PostgreSQL
kubectl apply -f k8s/postgres-read-replica.yaml

# Redis cluster mode
kubectl apply -f k8s/redis-cluster.yaml
```

### 3. Worker Scaling

```bash
# Scale workers based on queue length
kubectl apply -f k8s/worker-hpa-queue.yaml
```

## Backup & Recovery

### 1. Database Backup

```bash
#!/bin/bash
# backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="customercaregpt_backup_${DATE}.sql"

# Create backup
kubectl exec postgres-0 -- pg_dump -U customercaregpt customercaregpt > ${BACKUP_FILE}

# Upload to S3
aws s3 cp ${BACKUP_FILE} s3://customercaregpt-backups/database/

# Cleanup local file
rm ${BACKUP_FILE}

# Cleanup old backups (keep 30 days)
aws s3 ls s3://customercaregpt-backups/database/ | \
  awk '$1 < "'$(date -d '30 days ago' '+%Y-%m-%d')'" {print $4}' | \
  xargs -I {} aws s3 rm s3://customercaregpt-backups/database/{}
```

### 2. ChromaDB Backup

```bash
#!/bin/bash
# backup-chromadb.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="chromadb_backup_${DATE}"

# Create backup
kubectl exec chromadb-0 -- tar -czf /tmp/chromadb_backup.tar.gz /chroma/chroma
kubectl cp chromadb-0:/tmp/chromadb_backup.tar.gz ./chromadb_backup_${DATE}.tar.gz

# Upload to S3
aws s3 cp chromadb_backup_${DATE}.tar.gz s3://customercaregpt-backups/chromadb/

# Cleanup
rm chromadb_backup_${DATE}.tar.gz
```

### 3. Recovery Procedures

```bash
# Database recovery
kubectl exec -it postgres-0 -- psql -U customercaregpt -d customercaregpt -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
kubectl exec -i postgres-0 -- psql -U customercaregpt -d customercaregpt < backup_file.sql

# ChromaDB recovery
kubectl exec chromadb-0 -- rm -rf /chroma/chroma/*
kubectl cp chromadb_backup.tar.gz chromadb-0:/tmp/
kubectl exec chromadb-0 -- tar -xzf /tmp/chromadb_backup.tar.gz -C /
```

## Security

### 1. Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: customercaregpt-network-policy
spec:
  podSelector:
    matchLabels:
      app: customercaregpt-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector:
        matchLabels:
          name: redis
    ports:
    - protocol: TCP
      port: 6379
```

### 2. Pod Security Policies

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: customercaregpt-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### 3. RBAC Configuration

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: customercaregpt-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
```

## Maintenance

### 1. Rolling Updates

```bash
# Update backend
kubectl set image deployment/customercaregpt-backend backend=customercaregpt/backend:v1.1.0

# Monitor rollout
kubectl rollout status deployment/customercaregpt-backend

# Rollback if needed
kubectl rollout undo deployment/customercaregpt-backend
```

### 2. Database Maintenance

```bash
# Vacuum database
kubectl exec postgres-0 -- psql -U customercaregpt -d customercaregpt -c "VACUUM ANALYZE;"

# Check database size
kubectl exec postgres-0 -- psql -U customercaregpt -d customercaregpt -c "SELECT pg_size_pretty(pg_database_size('customercaregpt'));"
```

### 3. Log Rotation

```yaml
# logrotate configuration
/var/log/customercaregpt/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 app app
    postrotate
        kubectl exec deployment/customercaregpt-backend -- kill -USR1 1
    endscript
}
```

## Troubleshooting

### 1. Common Issues

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods

# Check for memory leaks
kubectl exec deployment/customercaregpt-backend -- python -c "
import psutil
print(psutil.virtual_memory())
print(psutil.Process().memory_info())
"
```

#### Database Connection Issues
```bash
# Check database connectivity
kubectl exec deployment/customercaregpt-backend -- python -c "
from app.core.database import get_db
db = next(get_db())
print('Database connected successfully')
"
```

#### Rate Limiting Issues
```bash
# Check Redis rate limiting
kubectl exec redis-0 -- redis-cli KEYS "ratelimit:*"
kubectl exec redis-0 -- redis-cli GET "ratelimit:workspace:workspace_id"
```

### 2. Debug Commands

```bash
# Get pod logs
kubectl logs deployment/customercaregpt-backend --tail=100 -f

# Check pod status
kubectl describe pod <pod-name>

# Check service endpoints
kubectl get endpoints

# Check ingress status
kubectl describe ingress customercaregpt-ingress
```

### 3. Performance Tuning

```bash
# Check resource usage
kubectl top nodes
kubectl top pods

# Check HPA status
kubectl get hpa

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

## Production Checklist

- [ ] All secrets stored in Kubernetes secrets or external secret manager
- [ ] Database backups scheduled and tested
- [ ] ChromaDB backup strategy implemented
- [ ] Monitoring and alerting configured
- [ ] Log aggregation set up
- [ ] SSL/TLS certificates configured
- [ ] Network policies applied
- [ ] Pod security policies configured
- [ ] RBAC properly configured
- [ ] Resource limits and requests set
- [ ] HPA configured for auto-scaling
- [ ] Health checks configured
- [ ] Rate limiting enabled
- [ ] Caching layer configured
- [ ] CDN configured for static assets
- [ ] Backup and recovery procedures tested
- [ ] Incident response plan documented
- [ ] Security scanning automated
- [ ] Dependency updates automated
- [ ] Performance benchmarks established

## Support

For production support and issues:
- **Email**: support@customercaregpt.com
- **Slack**: #production-support
- **On-call**: Check PagerDuty for current on-call engineer
- **Documentation**: https://docs.customercaregpt.com
