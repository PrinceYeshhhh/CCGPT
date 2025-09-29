"""
Prometheus metrics and monitoring system
"""

import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import structlog

logger = structlog.get_logger()


class MetricsCollector:
    """Collect and format metrics for Prometheus"""
    
    def __init__(self):
        self.request_counts = Counter()
        self.request_durations = defaultdict(list)
        self.error_counts = Counter()
        self.active_connections = 0
        self.start_time = time.time()
        
        # Security metrics
        self.failed_logins = Counter()
        self.blocked_ips = set()
        self.security_events = Counter()
        
        # Business metrics
        self.api_calls = Counter()
        self.user_sessions = Counter()
        self.document_uploads = Counter()
        self.chat_messages = Counter()
    
    def record_request(self, method: str, path: str, status_code: int, duration: float):
        """Record a request metric"""
        self.request_counts[f"{method}_{path}_{status_code}"] += 1
        self.request_durations[f"{method}_{path}"].append(duration)
        
        # Keep only last 1000 durations per endpoint
        if len(self.request_durations[f"{method}_{path}"]) > 1000:
            self.request_durations[f"{method}_{path}"] = self.request_durations[f"{method}_{path}"][-1000:]
    
    def record_error(self, error_type: str, endpoint: str):
        """Record an error metric"""
        self.error_counts[f"{error_type}_{endpoint}"] += 1
    
    def record_security_event(self, event_type: str, ip_address: str):
        """Record a security event"""
        self.security_events[event_type] += 1
        if event_type == "ip_blocked":
            self.blocked_ips.add(ip_address)
    
    def record_failed_login(self, ip_address: str):
        """Record a failed login attempt"""
        self.failed_logins[ip_address] += 1
    
    def record_api_call(self, endpoint: str):
        """Record an API call"""
        self.api_calls[endpoint] += 1
    
    def record_user_session(self, user_id: str):
        """Record a user session"""
        self.user_sessions[user_id] += 1
    
    def record_document_upload(self, user_id: str, file_size: int):
        """Record a document upload"""
        self.document_uploads[user_id] += 1
    
    def record_chat_message(self, user_id: str):
        """Record a chat message"""
        self.chat_messages[user_id] += 1
    
    def set_active_connections(self, count: int):
        """Set the number of active connections"""
        self.active_connections = count
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        metrics = []
        current_time = int(time.time() * 1000)  # Milliseconds
        
        # HTTP request metrics
        for key, count in self.request_counts.items():
            parts = key.split('_', 2)
            if len(parts) >= 3:
                method, path, status = parts[0], parts[1], parts[2]
                metrics.append(f'http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count} {current_time}')
        
        # HTTP request duration metrics
        for key, durations in self.request_durations.items():
            if durations:
                parts = key.split('_', 1)
                if len(parts) >= 2:
                    method, path = parts[0], parts[1]
                    avg_duration = sum(durations) / len(durations)
                    metrics.append(f'http_request_duration_seconds{{method="{method}",path="{path}"}} {avg_duration:.3f} {current_time}')
        
        # Error metrics
        for key, count in self.error_counts.items():
            parts = key.split('_', 1)
            if len(parts) >= 2:
                error_type, endpoint = parts[0], parts[1]
                metrics.append(f'http_errors_total{{error_type="{error_type}",endpoint="{endpoint}"}} {count} {current_time}')
        
        # Security metrics
        for event_type, count in self.security_events.items():
            metrics.append(f'security_events_total{{event_type="{event_type}"}} {count} {current_time}')
        
        metrics.append(f'security_blocked_ips_total {len(self.blocked_ips)} {current_time}')
        
        # Business metrics
        for endpoint, count in self.api_calls.items():
            metrics.append(f'api_calls_total{{endpoint="{endpoint}"}} {count} {current_time}')
        
        metrics.append(f'user_sessions_total {len(self.user_sessions)} {current_time}')
        metrics.append(f'document_uploads_total {sum(self.document_uploads.values())} {current_time}')
        metrics.append(f'chat_messages_total {sum(self.chat_messages.values())} {current_time}')
        
        # System metrics
        uptime = time.time() - self.start_time
        metrics.append(f'application_uptime_seconds {uptime:.2f} {current_time}')
        metrics.append(f'active_connections {self.active_connections} {current_time}')
        
        return '\n'.join(metrics)


# Global metrics collector
metrics_collector = MetricsCollector()


def get_metrics() -> str:
    """Get metrics in Prometheus format"""
    return metrics_collector.get_metrics()


def get_metrics_content_type() -> str:
    """Get the content type for metrics"""
    return "text/plain; version=0.0.4; charset=utf-8"


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