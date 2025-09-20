"""
Prometheus metrics collection and instrumentation
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from typing import Optional, Dict, Any
import time
import functools
from contextlib import contextmanager

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
QUERY_COUNT = Counter(
    'rag_queries_total',
    'Total RAG queries processed',
    ['workspace_id', 'status']
)

QUERY_DURATION = Histogram(
    'rag_query_duration_seconds',
    'RAG query processing duration in seconds',
    ['workspace_id']
)

VECTOR_SEARCH_DURATION = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration in seconds',
    ['workspace_id']
)

GEMINI_API_CALLS = Counter(
    'gemini_api_calls_total',
    'Total Gemini API calls',
    ['workspace_id', 'status']
)

GEMINI_API_DURATION = Histogram(
    'gemini_api_duration_seconds',
    'Gemini API call duration in seconds',
    ['workspace_id']
)

# System metrics
ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active database connections'
)

QUEUE_LENGTH = Gauge(
    'job_queue_length',
    'Number of jobs in queue',
    ['queue_name']
)

CACHE_HITS = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

# Subscription metrics
SUBSCRIPTION_QUOTA_USAGE = Gauge(
    'subscription_quota_usage_ratio',
    'Subscription quota usage ratio (0-1)',
    ['workspace_id', 'tier']
)

RATE_LIMIT_HITS = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['workspace_id', 'limit_type']
)

class MetricsCollector:
    """Centralized metrics collection"""
    
    @staticmethod
    def record_request(method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    @staticmethod
    def record_query(workspace_id: str, status: str, duration: float):
        """Record RAG query metrics"""
        QUERY_COUNT.labels(
            workspace_id=workspace_id,
            status=status
        ).inc()
        
        QUERY_DURATION.labels(
            workspace_id=workspace_id
        ).observe(duration)
    
    @staticmethod
    def record_vector_search(workspace_id: str, duration: float):
        """Record vector search metrics"""
        VECTOR_SEARCH_DURATION.labels(
            workspace_id=workspace_id
        ).observe(duration)
    
    @staticmethod
    def record_gemini_call(workspace_id: str, status: str, duration: float):
        """Record Gemini API call metrics"""
        GEMINI_API_CALLS.labels(
            workspace_id=workspace_id,
            status=status
        ).inc()
        
        GEMINI_API_DURATION.labels(
            workspace_id=workspace_id
        ).observe(duration)
    
    @staticmethod
    def record_cache_hit(cache_type: str):
        """Record cache hit"""
        CACHE_HITS.labels(cache_type=cache_type).inc()
    
    @staticmethod
    def record_cache_miss(cache_type: str):
        """Record cache miss"""
        CACHE_MISSES.labels(cache_type=cache_type).inc()
    
    @staticmethod
    def record_quota_usage(workspace_id: str, tier: str, usage_ratio: float):
        """Record subscription quota usage"""
        SUBSCRIPTION_QUOTA_USAGE.labels(
            workspace_id=workspace_id,
            tier=tier
        ).set(usage_ratio)
    
    @staticmethod
    def record_rate_limit_hit(workspace_id: str, limit_type: str):
        """Record rate limit hit"""
        RATE_LIMIT_HITS.labels(
            workspace_id=workspace_id,
            limit_type=limit_type
        ).inc()
    
    @staticmethod
    def set_queue_length(queue_name: str, length: int):
        """Set queue length metric"""
        QUEUE_LENGTH.labels(queue_name=queue_name).set(length)
    
    @staticmethod
    def set_active_connections(count: int):
        """Set active connections metric"""
        ACTIVE_CONNECTIONS.set(count)

def metrics_middleware(func):
    """Decorator to automatically record metrics for functions"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Extract workspace_id if available
            workspace_id = kwargs.get('workspace_id', 'unknown')
            
            # Record metrics based on function name
            if 'query' in func.__name__:
                MetricsCollector.record_query(workspace_id, 'success', duration)
            elif 'vector_search' in func.__name__:
                MetricsCollector.record_vector_search(workspace_id, duration)
            elif 'gemini' in func.__name__:
                MetricsCollector.record_gemini_call(workspace_id, 'success', duration)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            workspace_id = kwargs.get('workspace_id', 'unknown')
            
            # Record error metrics
            if 'query' in func.__name__:
                MetricsCollector.record_query(workspace_id, 'error', duration)
            elif 'gemini' in func.__name__:
                MetricsCollector.record_gemini_call(workspace_id, 'error', duration)
            
            raise
    return wrapper

@contextmanager
def time_operation(operation_name: str, workspace_id: Optional[str] = None):
    """Context manager to time operations"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        if workspace_id:
            if 'vector_search' in operation_name:
                MetricsCollector.record_vector_search(workspace_id, duration)
            elif 'gemini' in operation_name:
                MetricsCollector.record_gemini_call(workspace_id, 'success', duration)

def get_metrics() -> str:
    """Get Prometheus metrics in text format"""
    return generate_latest()

def get_metrics_content_type() -> str:
    """Get content type for metrics endpoint"""
    return CONTENT_TYPE_LATEST

# Custom metrics for specific business logic
class BusinessMetrics:
    """Business-specific metrics"""
    
    @staticmethod
    def record_document_upload(workspace_id: str, file_size: int, processing_time: float):
        """Record document upload metrics"""
        # This would be implemented with custom metrics
        pass
    
    @staticmethod
    def record_embed_code_generation(workspace_id: str):
        """Record embed code generation"""
        # This would be implemented with custom metrics
        pass
    
    @staticmethod
    def record_subscription_change(workspace_id: str, old_tier: str, new_tier: str):
        """Record subscription tier changes"""
        # This would be implemented with custom metrics
        pass

# Health check metrics
class HealthMetrics:
    """Health check related metrics"""
    
    @staticmethod
    def record_health_check(component: str, status: str, duration: float):
        """Record health check results"""
        # This would be implemented with custom metrics
        pass
    
    @staticmethod
    def record_dependency_check(dependency: str, status: str, duration: float):
        """Record dependency health checks"""
        # This would be implemented with custom metrics
        pass
