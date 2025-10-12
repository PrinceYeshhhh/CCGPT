# Performance Optimization Guide
# Comprehensive performance monitoring, analysis, and optimization for CustomerCareGPT

## Overview

This guide covers the comprehensive performance optimization system implemented in CustomerCareGPT, including real-time monitoring, automated analysis, and optimization recommendations.

## Table of Contents

1. [Performance Monitoring System](#performance-monitoring-system)
2. [Caching Strategy](#caching-strategy)
3. [Database Optimization](#database-optimization)
4. [Query Optimization](#query-optimization)
5. [Memory Management](#memory-management)
6. [API Performance](#api-performance)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Optimization Tools](#optimization-tools)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Performance Monitoring System

### Real-time Metrics Collection

The performance monitoring system tracks:

- **System Metrics**: CPU, memory, disk usage, network I/O
- **Application Metrics**: Response times, error rates, request throughput
- **Database Metrics**: Connection pool usage, query performance, slow queries
- **Cache Metrics**: Hit rates, miss rates, cache size
- **Business Metrics**: User sessions, document processing, chat messages

### Performance Dashboard

Access the performance dashboard at `/api/v1/performance/dashboard` (admin only):

```json
{
  "current_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "response_time_p95": 0.8,
    "error_rate": 0.02,
    "requests_per_second": 15.3
  },
  "recommendations": [...],
  "optimization_summary": {
    "performance_score": 85,
    "total_recommendations": 3,
    "high_priority_issues": 1
  }
}
```

### Alerting System

Automatic alerts are generated for:

- CPU usage > 80%
- Memory usage > 85%
- Response time P95 > 2 seconds
- Error rate > 5%
- Database connections > 80% of pool

## Caching Strategy

### Multi-tier Caching

1. **L1 Cache (Local)**: In-memory cache for frequently accessed data
2. **L2 Cache (Redis)**: Distributed cache for shared data
3. **Query Cache**: Database query result caching
4. **API Cache**: HTTP response caching
5. **Vector Cache**: Embedding and search result caching

### Cache Configuration

```python
# Cache TTL settings
VECTOR_CACHE_TTL = 600  # 10 minutes
API_CACHE_TTL = 300     # 5 minutes
QUERY_CACHE_TTL = 300   # 5 minutes
```

### Cache Invalidation

- **Time-based**: Automatic expiration
- **Event-based**: Invalidation on data changes
- **Manual**: Administrative cache clearing
- **Namespace-based**: Clear by data category

### Cache Optimization

```python
# Enable caching for expensive operations
@cached(ttl=300, namespace="analytics")
async def get_analytics_data(workspace_id: str):
    # Expensive analytics calculation
    pass

# Cache invalidation on data changes
@cache_invalidate("analytics")
async def update_analytics_data(workspace_id: str):
    # Update analytics data
    pass
```

## Database Optimization

### Connection Pooling

Optimized connection pool settings:

```python
# Write database
pool_size = 50
max_overflow = 30
pool_timeout = 60
pool_recycle = 1800  # 30 minutes

# Read replicas
pool_size = 30
max_overflow = 20
statement_timeout = 30000  # 30 seconds
```

### Database Indexes

Critical indexes for performance:

```sql
-- Document queries
CREATE INDEX idx_documents_workspace_status ON documents(workspace_id, status);
CREATE INDEX idx_documents_workspace_uploaded ON documents(workspace_id, uploaded_at);

-- Chat queries
CREATE INDEX idx_chat_sessions_workspace_created ON chat_sessions(workspace_id, created_at);
CREATE INDEX idx_chat_messages_session_created ON chat_messages(session_id, created_at);

-- User queries
CREATE INDEX idx_users_workspace_id ON users(workspace_id);
CREATE INDEX idx_users_email ON users(email);

-- Embed queries
CREATE INDEX idx_embed_codes_api_key ON embed_codes(client_api_key);
CREATE INDEX idx_embed_codes_workspace ON embed_codes(workspace_id);
```

### Query Optimization

Use the optimized query builder:

```python
# Optimized query with caching
query = OptimizedQueryBuilder(session)\
    .select(Document)\
    .where(Document.workspace_id == workspace_id)\
    .where(Document.status == 'done')\
    .order_by(Document.uploaded_at.desc())\
    .limit(20)\
    .cache(ttl=300)

results = await query.execute(f"documents:{workspace_id}:recent")
```

### Database Monitoring

Monitor database performance:

```python
# Get connection pool stats
stats = db_manager.get_connection_stats()

# Monitor slow queries
slow_queries = query_monitor.get_slow_queries(limit=10)

# Analyze query performance
analysis = await db_optimizer.analyze_query_performance()
```

## Query Optimization

### Query Performance Monitoring

Track query performance automatically:

```python
@query_performance_monitor
def expensive_database_operation():
    # Database operation
    pass
```

### Query Caching

Cache expensive queries:

```python
@cached_query(ttl=300)
async def get_user_analytics(user_id: str):
    # Expensive analytics query
    pass
```

### Query Optimization Recommendations

The system provides automatic recommendations:

- Missing indexes
- N+1 query patterns
- Full table scans
- Inefficient joins
- Suboptimal WHERE clauses

## Memory Management

### Memory Optimization

Automatic memory management:

- Garbage collection when memory usage > 80%
- Connection pool cleanup
- Cache size limits
- Memory leak detection

### Memory Monitoring

```python
# Get memory usage
memory = psutil.virtual_memory()
print(f"Memory usage: {memory.percent}%")

# Monitor memory trends
history = performance_service.monitor.get_metrics_history(hours=1)
```

## API Performance

### Request Optimization

Middleware for request optimization:

1. **Performance Monitoring**: Track request duration and status
2. **Cache Optimization**: Automatic response caching
3. **Database Query Optimization**: Monitor and optimize queries
4. **Memory Optimization**: Automatic garbage collection

### Response Caching

Automatic caching for GET requests:

```python
# Cacheable endpoints
cacheable_paths = {
    "/api/v1/analytics/overview": 300,  # 5 minutes
    "/api/v1/analytics/usage-stats": 600,  # 10 minutes
    "/api/v1/documents": 60,  # 1 minute
}
```

### Performance Headers

Response headers for performance monitoring:

```
X-Response-Time: 0.234s
X-Request-ID: req_1234567890_1
X-Cache: HIT
X-DB-Queries: 3
X-DB-Time: 0.045s
X-Memory-Usage: 67.8%
```

## Monitoring and Alerting

### Performance Alerts

Automatic alerts for:

- High CPU usage (> 80%)
- High memory usage (> 85%)
- Slow response times (> 2s P95)
- High error rates (> 5%)
- Database connection issues
- Cache performance issues

### Alert Management

```python
# Get recent alerts
alerts = performance_service.get_performance_alerts(hours=24)

# Clear alerts
await performance_service.clear_alerts()
```

### Performance Baselines

Automatic baseline calculation:

- CPU usage baseline
- Memory usage baseline
- Response time baseline
- Request throughput baseline

## Optimization Tools

### Performance Optimizer CLI

Command-line tool for performance optimization:

```bash
# Analyze current performance
python scripts/performance_optimizer.py --analyze --hours 24

# Get optimization recommendations
python scripts/performance_optimizer.py --recommendations

# Optimize database
python scripts/performance_optimizer.py --optimize-db --apply-changes

# Optimize cache
python scripts/performance_optimizer.py --optimize-cache --clear-cache

# Run complete optimization cycle
python scripts/performance_optimizer.py --optimize-all --apply-changes

# Generate comprehensive report
python scripts/performance_optimizer.py --output performance_report.json
```

### Performance API Endpoints

Administrative endpoints for performance management:

```bash
# Get performance dashboard
GET /api/v1/performance/dashboard

# Get current metrics
GET /api/v1/performance/metrics/current

# Get metrics history
GET /api/v1/performance/metrics/history?hours=24

# Get optimization recommendations
GET /api/v1/performance/recommendations

# Get performance alerts
GET /api/v1/performance/alerts?hours=24

# Clear performance alerts
POST /api/v1/performance/alerts/clear

# Apply optimization
POST /api/v1/performance/optimize/{recommendation_id}

# Get query performance
GET /api/v1/performance/query-performance

# Get database stats
GET /api/v1/performance/database-stats

# Get cache stats
GET /api/v1/performance/cache-stats

# Clear cache
POST /api/v1/performance/cache/clear?namespace=analytics

# Get connection pool stats
GET /api/v1/performance/connection-pool

# Get index suggestions
GET /api/v1/performance/suggest-indexes
```

## Best Practices

### Application Performance

1. **Use Caching**: Cache expensive operations and frequently accessed data
2. **Optimize Queries**: Use proper indexes and avoid N+1 queries
3. **Monitor Performance**: Track metrics and set up alerts
4. **Optimize Memory**: Monitor memory usage and implement cleanup
5. **Use Background Jobs**: Move heavy operations to background workers

### Database Performance

1. **Proper Indexing**: Create indexes for common query patterns
2. **Connection Pooling**: Use appropriate pool sizes
3. **Query Optimization**: Use EXPLAIN ANALYZE for slow queries
4. **Read Replicas**: Use read replicas for read-heavy workloads
5. **Connection Monitoring**: Monitor connection pool usage

### Cache Performance

1. **Appropriate TTL**: Set cache TTL based on data freshness requirements
2. **Cache Invalidation**: Implement proper cache invalidation strategies
3. **Cache Warming**: Pre-populate cache with frequently accessed data
4. **Cache Monitoring**: Monitor cache hit rates and performance
5. **Cache Sizing**: Set appropriate cache size limits

### API Performance

1. **Response Caching**: Cache GET responses where appropriate
2. **Request Optimization**: Minimize database queries per request
3. **Pagination**: Implement pagination for large datasets
4. **Compression**: Use response compression
5. **CDN**: Use CDN for static assets

## Troubleshooting

### Common Performance Issues

#### High CPU Usage

**Symptoms**: CPU usage > 80%, slow response times

**Solutions**:
1. Check for infinite loops or inefficient algorithms
2. Optimize database queries
3. Implement caching
4. Scale horizontally

#### High Memory Usage

**Symptoms**: Memory usage > 85%, potential OOM errors

**Solutions**:
1. Check for memory leaks
2. Implement garbage collection
3. Optimize data structures
4. Increase memory limits

#### Slow Database Queries

**Symptoms**: High database response times, slow queries

**Solutions**:
1. Add missing indexes
2. Optimize query structure
3. Use query caching
4. Consider read replicas

#### Low Cache Hit Rate

**Symptoms**: Cache hit rate < 70%, high database load

**Solutions**:
1. Review cache TTL settings
2. Implement cache warming
3. Optimize cache key patterns
4. Increase cache size

#### High Error Rate

**Symptoms**: Error rate > 5%, user complaints

**Solutions**:
1. Check application logs
2. Monitor external service health
3. Implement circuit breakers
4. Add retry logic

### Performance Debugging

#### Enable Debug Logging

```python
# Enable performance debug logging
import logging
logging.getLogger("app.services.performance_service").setLevel(logging.DEBUG)
```

#### Monitor Specific Operations

```python
# Monitor specific function performance
@monitor_performance
async def expensive_operation():
    # Operation to monitor
    pass
```

#### Database Query Analysis

```python
# Analyze slow queries
slow_queries = query_monitor.get_slow_queries(limit=10)
for query in slow_queries:
    print(f"Query: {query['query']}")
    print(f"Duration: {query['duration']}s")
    print(f"Parameters: {query['params']}")
```

### Performance Monitoring Setup

#### Enable Performance Monitoring

```python
# Start performance monitoring
from app.services.performance_service import performance_service
performance_service.start()
```

#### Set Up Alerts

```python
# Configure alert thresholds
performance_service.monitor.alert_thresholds = {
    "cpu_percent": 80.0,
    "memory_percent": 85.0,
    "response_time_p95": 2.0,
    "error_rate": 0.05
}
```

#### Monitor Performance Trends

```python
# Get performance trends
history = performance_service.monitor.get_metrics_history(hours=24)
trend = performance_service.optimizer._calculate_trend()
print(f"Performance trend: {trend}")
```

## Conclusion

The performance optimization system provides comprehensive monitoring, analysis, and optimization capabilities for CustomerCareGPT. By following the best practices and using the provided tools, you can ensure optimal performance and user experience.

For additional support or questions, refer to the API documentation or contact the development team.
