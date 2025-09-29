"""
Security monitoring and threat detection utilities
"""

import time
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import structlog

logger = structlog.get_logger()


class SecurityMonitor:
    """Monitor security events and detect threats"""
    
    def __init__(self):
        self.failed_logins = defaultdict(list)  # IP -> list of timestamps
        self.suspicious_requests = defaultdict(list)  # IP -> list of requests
        self.blocked_ips = set()
        self.rate_limit_violations = defaultdict(list)
        self.security_events = deque(maxlen=10000)  # Keep last 10k events
        
        # Thresholds
        self.MAX_FAILED_LOGINS = 10
        self.LOGIN_WINDOW_MINUTES = 15
        self.SUSPICIOUS_REQUEST_THRESHOLD = 20
        self.REQUEST_WINDOW_MINUTES = 5
        self.BLOCK_DURATION_HOURS = 24
    
    def log_security_event(self, event_type: str, ip_address: str, details: Dict[str, Any]):
        """Log a security event"""
        event = {
            "timestamp": datetime.utcnow(),
            "event_type": event_type,
            "ip_address": ip_address,
            "details": details
        }
        
        self.security_events.append(event)
        
        # Log to structured logger
        logger.warning(
            "Security event detected",
            event_type=event_type,
            ip_address=ip_address,
            **details
        )
    
    def record_failed_login(self, ip_address: str, identifier: str):
        """Record a failed login attempt"""
        current_time = datetime.utcnow()
        
        # Clean old attempts
        cutoff_time = current_time - timedelta(minutes=self.LOGIN_WINDOW_MINUTES)
        self.failed_logins[ip_address] = [
            timestamp for timestamp in self.failed_logins[ip_address]
            if timestamp > cutoff_time
        ]
        
        # Add current attempt
        self.failed_logins[ip_address].append(current_time)
        
        # Check if IP should be blocked
        if len(self.failed_logins[ip_address]) >= self.MAX_FAILED_LOGINS:
            self.block_ip(ip_address, "Too many failed login attempts")
            self.log_security_event(
                "ip_blocked",
                ip_address,
                {
                    "reason": "failed_logins",
                    "attempts": len(self.failed_logins[ip_address]),
                    "identifier": identifier
                }
            )
    
    def record_suspicious_request(self, ip_address: str, request_path: str, user_agent: str):
        """Record a suspicious request"""
        current_time = datetime.utcnow()
        
        # Clean old requests
        cutoff_time = current_time - timedelta(minutes=self.REQUEST_WINDOW_MINUTES)
        self.suspicious_requests[ip_address] = [
            req for req in self.suspicious_requests[ip_address]
            if req["timestamp"] > cutoff_time
        ]
        
        # Add current request
        self.suspicious_requests[ip_address].append({
            "timestamp": current_time,
            "path": request_path,
            "user_agent": user_agent
        })
        
        # Check if IP should be blocked
        if len(self.suspicious_requests[ip_address]) >= self.SUSPICIOUS_REQUEST_THRESHOLD:
            self.block_ip(ip_address, "Suspicious request pattern")
            self.log_security_event(
                "ip_blocked",
                ip_address,
                {
                    "reason": "suspicious_requests",
                    "request_count": len(self.suspicious_requests[ip_address]),
                    "path": request_path
                }
            )
    
    def record_rate_limit_violation(self, ip_address: str, endpoint: str):
        """Record a rate limit violation"""
        current_time = datetime.utcnow()
        
        # Clean old violations
        cutoff_time = current_time - timedelta(minutes=60)
        self.rate_limit_violations[ip_address] = [
            violation for violation in self.rate_limit_violations[ip_address]
            if violation["timestamp"] > cutoff_time
        ]
        
        # Add current violation
        self.rate_limit_violations[ip_address].append({
            "timestamp": current_time,
            "endpoint": endpoint
        })
        
        # Check if IP should be blocked
        if len(self.rate_limit_violations[ip_address]) >= 5:
            self.block_ip(ip_address, "Repeated rate limit violations")
            self.log_security_event(
                "ip_blocked",
                ip_address,
                {
                    "reason": "rate_limit_violations",
                    "violations": len(self.rate_limit_violations[ip_address]),
                    "endpoint": endpoint
                }
            )
    
    def block_ip(self, ip_address: str, reason: str):
        """Block an IP address"""
        self.blocked_ips.add(ip_address)
        
        # Schedule unblocking
        unblock_time = datetime.utcnow() + timedelta(hours=self.BLOCK_DURATION_HOURS)
        
        logger.warning(
            "IP address blocked",
            ip_address=ip_address,
            reason=reason,
            unblock_time=unblock_time.isoformat()
        )
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked"""
        return ip_address in self.blocked_ips
    
    def unblock_ip(self, ip_address: str):
        """Manually unblock an IP address"""
        self.blocked_ips.discard(ip_address)
        
        # Clear related data
        self.failed_logins.pop(ip_address, None)
        self.suspicious_requests.pop(ip_address, None)
        self.rate_limit_violations.pop(ip_address, None)
        
        logger.info("IP address unblocked", ip_address=ip_address)
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get a summary of security events"""
        current_time = datetime.utcnow()
        
        # Count recent events
        recent_events = [
            event for event in self.security_events
            if event["timestamp"] > current_time - timedelta(hours=24)
        ]
        
        event_counts = defaultdict(int)
        for event in recent_events:
            event_counts[event["event_type"]] += 1
        
        return {
            "blocked_ips": len(self.blocked_ips),
            "recent_events": len(recent_events),
            "event_counts": dict(event_counts),
            "failed_login_ips": len(self.failed_logins),
            "suspicious_request_ips": len(self.suspicious_requests),
            "rate_limit_violation_ips": len(self.rate_limit_violations)
        }
    
    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect security anomalies"""
        anomalies = []
        current_time = datetime.utcnow()
        
        # Check for unusual patterns
        for ip_address, requests in self.suspicious_requests.items():
            if len(requests) > 10:  # High request volume
                anomalies.append({
                    "type": "high_request_volume",
                    "ip_address": ip_address,
                    "count": len(requests),
                    "severity": "medium"
                })
        
        # Check for failed login patterns
        for ip_address, attempts in self.failed_logins.items():
            if len(attempts) > 5:  # Multiple failed logins
                anomalies.append({
                    "type": "multiple_failed_logins",
                    "ip_address": ip_address,
                    "count": len(attempts),
                    "severity": "high"
                })
        
        return anomalies


# Global security monitor instance
security_monitor = SecurityMonitor()


def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor instance"""
    return security_monitor
