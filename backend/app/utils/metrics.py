"""
Prometheus metrics and monitoring system
"""

import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import structlog
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
import threading

logger = structlog.get_logger()

# Create a custom registry for our metrics
registry = CollectorRegistry()


# Define Prometheus metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

http_errors_total = Counter(
    'http_errors_total',
    'Total HTTP errors',
    ['error_type', 'endpoint'],
    registry=registry
)

security_events_total = Counter(
    'security_events_total',
    'Total security events',
    ['event_type'],
    registry=registry
)

security_failed_logins_total = Counter(
    'security_failed_logins_total',
    'Total failed login attempts',
    ['ip_address'],
    registry=registry
)

security_blocked_ips_total = Gauge(
    'security_blocked_ips_total',
    'Total number of blocked IP addresses',
    registry=registry
)

api_calls_total = Counter(
    'api_calls_total',
    'Total API calls',
    ['endpoint'],
    registry=registry
)

user_sessions_total = Counter(
    'user_sessions_total',
    'Total user sessions',
    ['user_id'],
    registry=registry
)

document_uploads_total = Counter(
    'document_uploads_total',
    'Total document uploads',
    ['user_id'],
    registry=registry
)

document_upload_size_bytes = Histogram(
    'document_upload_size_bytes',
    'Document upload size in bytes',
    ['user_id'],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600],  # 1KB to 100MB
    registry=registry
)

chat_messages_total = Counter(
    'chat_messages_total',
    'Total chat messages',
    ['user_id', 'role'],
    registry=registry
)

chat_response_time_seconds = Histogram(
    'chat_response_time_seconds',
    'Chat response time in seconds',
    ['user_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

active_connections = Gauge(
    'active_connections',
    'Number of active connections',
    registry=registry
)

application_uptime_seconds = Gauge(
    'application_uptime_seconds',
    'Application uptime in seconds',
    registry=registry
)

database_connections_active = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=registry
)

database_connections_idle = Gauge(
    'database_connections_idle',
    'Number of idle database connections',
    registry=registry
)

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'status'],
    registry=registry
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Redis operation duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
    registry=registry
)

vector_search_operations_total = Counter(
    'vector_search_operations_total',
    'Total vector search operations',
    ['workspace_id'],
    registry=registry
)

vector_search_duration_seconds = Histogram(
    'vector_search_duration_seconds',
    'Vector search duration in seconds',
    ['workspace_id'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

ai_generation_requests_total = Counter(
    'ai_generation_requests_total',
    'Total AI generation requests',
    ['model', 'workspace_id'],
    registry=registry
)

ai_generation_duration_seconds = Histogram(
    'ai_generation_duration_seconds',
    'AI generation duration in seconds',
    ['model', 'workspace_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

ai_generation_tokens_total = Counter(
    'ai_generation_tokens_total',
    'Total AI generation tokens',
    ['model', 'workspace_id', 'token_type'],
    registry=registry
)

# Thread-safe metrics collector
class MetricsCollector:
    """Thread-safe metrics collector using Prometheus client"""
    
    def __init__(self):
        self.start_time = time.time()
        self.blocked_ips = set()
        self._lock = threading.Lock()
        # Simple in-memory store expected by some unit tests
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record a request metric"""
        # Normalize path to avoid high cardinality
        normalized_path = self._normalize_path(path)
        http_requests_total.labels(method=method, endpoint=normalized_path, status_code=str(status_code)).inc()
        http_request_duration_seconds.labels(method=method, endpoint=normalized_path).observe(duration)
        # Store in-memory tallies
        with self._lock:
            key = f"requests:{method}:{normalized_path}:{status_code}"
            self._counters[key] = self._counters.get(key, 0) + 1
            self._histograms.setdefault(f"request_duration:{method}:{normalized_path}", []).append(duration)
    
    def record_error(self, error_type: str, endpoint: str):
        """Record an error metric"""
        normalized_endpoint = self._normalize_path(endpoint)
        http_errors_total.labels(error_type=error_type, endpoint=normalized_endpoint).inc()
    
    def record_security_event(self, event_type: str, ip_address: str):
        """Record a security event"""
        security_events_total.labels(event_type=event_type).inc()
        if event_type == "ip_blocked":
            with self._lock:
                self.blocked_ips.add(ip_address)
                security_blocked_ips_total.set(len(self.blocked_ips))
    
    def record_failed_login(self, ip_address: str):
        """Record a failed login attempt"""
        security_failed_logins_total.labels(ip_address=ip_address).inc()
    
    def record_api_call(self, endpoint: str):
        """Record an API call"""
        normalized_endpoint = self._normalize_path(endpoint)
        api_calls_total.labels(endpoint=normalized_endpoint).inc()
    
    def record_user_session(self, user_id: str):
        """Record a user session"""
        user_sessions_total.labels(user_id=user_id).inc()
    
    def record_document_upload(self, user_id: str, file_size: int):
        """Record a document upload"""
        document_uploads_total.labels(user_id=user_id).inc()
        document_upload_size_bytes.labels(user_id=user_id).observe(file_size)
    
    def record_chat_message(self, user_id: str, role: str = "user"):
        """Record a chat message"""
        chat_messages_total.labels(user_id=user_id, role=role).inc()
    
    def record_chat_response_time(self, user_id: str, duration: float):
        """Record chat response time"""
        chat_response_time_seconds.labels(user_id=user_id).observe(duration)
    
    def set_active_connections(self, count: int):
        """Set the number of active connections"""
        active_connections.set(count)
    
    def set_database_connections(self, active: int, idle: int):
        """Set database connection metrics"""
        database_connections_active.set(active)
        database_connections_idle.set(idle)
        with self._lock:
            self._gauges["db_active"] = float(active)
            self._gauges["db_idle"] = float(idle)
    
    def record_redis_operation(self, operation: str, duration: float, success: bool = True):
        """Record Redis operation"""
        status = "success" if success else "error"
        redis_operations_total.labels(operation=operation, status=status).inc()
        redis_operation_duration_seconds.labels(operation=operation).observe(duration)
    
    def record_vector_search(self, workspace_id: str, duration: float):
        """Record vector search operation"""
        vector_search_operations_total.labels(workspace_id=workspace_id).inc()
        vector_search_duration_seconds.labels(workspace_id=workspace_id).observe(duration)
    
    def record_ai_generation(self, model: str, workspace_id: str, duration: float, input_tokens: int = 0, output_tokens: int = 0):
        """Record AI generation metrics"""
        ai_generation_requests_total.labels(model=model, workspace_id=workspace_id).inc()
        ai_generation_duration_seconds.labels(model=model, workspace_id=workspace_id).observe(duration)
        
        if input_tokens > 0:
            ai_generation_tokens_total.labels(model=model, workspace_id=workspace_id, token_type="input").inc(input_tokens)
        if output_tokens > 0:
            ai_generation_tokens_total.labels(model=model, workspace_id=workspace_id, token_type="output").inc(output_tokens)
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path to avoid high cardinality"""
        # Replace UUIDs and IDs with placeholders
        import re
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{uuid}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        return path
    
    def update_uptime(self):
        """Update application uptime"""
        uptime = time.time() - self.start_time
        application_uptime_seconds.set(uptime)

    # ---- Test-friendly helpers ----
    def increment(self, name: str, by: int = 1):
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + by

    def record(self, name: str, value: float):
        with self._lock:
            self._histograms.setdefault(name, []).append(value)

    def set_gauge(self, name: str, value: float):
        with self._lock:
            self._gauges[name] = value

    def get(self, name: str):
        with self._lock:
            if name in self._counters:
                return self._counters[name]
            if name in self._gauges:
                return self._gauges[name]
            return self._histograms.get(name, [])


# Global metrics collector
metrics_collector = MetricsCollector()


def get_metrics() -> str:
    """Get metrics in Prometheus format"""
    # Update uptime before generating metrics
    metrics_collector.update_uptime()
    return generate_latest(registry)


def get_metrics_content_type() -> str:
    """Get the content type for metrics"""
    return CONTENT_TYPE_LATEST


def record_request(method: str, path: str, status_code: int, duration: float):
    """Record a request metric"""
    metrics_collector.record_request(method, path, status_code, duration)


def record_error(error_type: str, endpoint: str):
    """Record an error metric"""
    metrics_collector.record_error(error_type, endpoint)


def record_security_event(event_type: str, ip_address: str):
    """Record a security event"""
    metrics_collector.record_security_event(event_type, ip_address)


def record_failed_login(ip_address: str):
    """Record a failed login attempt"""
    metrics_collector.record_failed_login(ip_address)


def record_api_call(endpoint: str):
    """Record an API call"""
    metrics_collector.record_api_call(endpoint)


def record_user_session(user_id: str):
    """Record a user session"""
    metrics_collector.record_user_session(user_id)


def record_document_upload(user_id: str, file_size: int):
    """Record a document upload"""
    metrics_collector.record_document_upload(user_id, file_size)


def record_chat_message(user_id: str):
    """Record a chat message"""
    metrics_collector.record_chat_message(user_id)


def set_active_connections(count: int):
    """Set the number of active connections"""
    metrics_collector.set_active_connections(count)