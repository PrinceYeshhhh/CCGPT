# Performance Monitoring and Optimization Service
# Real-time performance tracking, optimization recommendations, and automated tuning

import time
import asyncio
import psutil
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import structlog
from app.core.config import settings
from app.services.cache_service import cache_service
from app.services.query_optimizer import query_monitor, db_optimizer
from app.core.database import db_manager
from app.utils.metrics import metrics_collector

logger = structlog.get_logger()

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    db_connections_active: int
    db_connections_idle: int
    redis_connections: int
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    error_rate: float
    requests_per_second: float

@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    category: str
    priority: str  # high, medium, low
    title: str
    description: str
    impact: str
    effort: str
    current_value: Any
    recommended_value: Any
    estimated_improvement: str

class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.metrics_history = deque(maxlen=1000)  # Keep last 1000 measurements
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "response_time_p95": 2.0,  # 2 seconds
            "error_rate": 0.05,  # 5%
            "db_connections_active": 40  # 80% of pool size
        }
        self.alerts = []
        self.monitoring_active = False
        self.monitor_thread = None
        self.interval = 30  # seconds
        
        # Performance baselines
        self.baselines = {}
        self.baseline_calculated = False
        
        # Request tracking
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.request_counts = defaultdict(int)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for alerts
                self._check_alerts(metrics)
                
                # Calculate baselines if needed
                if not self.baseline_calculated and len(self.metrics_history) >= 10:
                    self._calculate_baselines()
                
                time.sleep(self.interval)
            
            except Exception as e:
                logger.error("Performance monitoring error", error=str(e))
                time.sleep(60)  # Wait 1 minute on error
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        # Database metrics
        db_stats = db_manager.get_connection_stats()
        db_active = db_stats.get('write_db', {}).get('checked_out', 0)
        db_idle = db_stats.get('write_db', {}).get('checked_in', 0)
        
        # Redis metrics
        redis_connections = 0
        try:
            from app.core.database import redis_manager
            redis_client = redis_manager.get_client()
            if hasattr(redis_client, 'connection_pool'):
                redis_connections = redis_client.connection_pool.connection_kwargs.get('max_connections', 0)
        except Exception:
            pass
        
        # Response time metrics
        response_times = list(self.request_times)
        if response_times:
            response_times.sort()
            p50 = response_times[int(len(response_times) * 0.5)]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0.0
        
        # Error rate
        total_requests = sum(self.request_counts.values())
        total_errors = sum(self.error_counts.values())
        error_rate = total_errors / total_requests if total_requests > 0 else 0.0
        
        # Requests per second (last minute)
        now = time.time()
        recent_requests = sum(
            count for timestamp, count in self.request_counts.items()
            if now - timestamp < 60
        )
        rps = recent_requests / 60.0
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            memory_available_mb=memory.available / (1024 * 1024),
            disk_usage_percent=disk.percent,
            disk_free_gb=disk.free / (1024 * 1024 * 1024),
            network_sent_mb=network.bytes_sent / (1024 * 1024),
            network_recv_mb=network.bytes_recv / (1024 * 1024),
            active_connections=len(psutil.net_connections()),
            db_connections_active=db_active,
            db_connections_idle=db_idle,
            redis_connections=redis_connections,
            response_time_p50=p50,
            response_time_p95=p95,
            response_time_p99=p99,
            error_rate=error_rate,
            requests_per_second=rps
        )
    
    def _check_alerts(self, metrics: PerformanceMetrics):
        """Check for performance alerts"""
        alerts = []
        
        for metric, threshold in self.alert_thresholds.items():
            value = getattr(metrics, metric, 0)
            if value > threshold:
                alert = {
                    "timestamp": metrics.timestamp,
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                    "severity": "high" if value > threshold * 1.5 else "medium"
                }
                alerts.append(alert)
                logger.warning(
                    "Performance alert",
                    metric=metric,
                    value=value,
                    threshold=threshold
                )
        
        self.alerts.extend(alerts)
        
        # Keep only recent alerts
        cutoff = datetime.now() - timedelta(hours=24)
        self.alerts = [a for a in self.alerts if a["timestamp"] > cutoff]
    
    def _calculate_baselines(self):
        """Calculate performance baselines"""
        if len(self.metrics_history) < 10:
            return
        
        recent_metrics = list(self.metrics_history)[-10:]
        
        self.baselines = {
            "cpu_percent": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
            "memory_percent": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics),
            "response_time_p95": sum(m.response_time_p95 for m in recent_metrics) / len(recent_metrics),
            "requests_per_second": sum(m.requests_per_second for m in recent_metrics) / len(recent_metrics)
        }
        
        self.baseline_calculated = True
        logger.info("Performance baselines calculated", baselines=self.baselines)
    
    def record_request(self, duration: float, status_code: int):
        """Record request performance"""
        self.request_times.append(duration)
        
        # Track by minute
        minute = int(time.time() / 60) * 60
        self.request_counts[minute] += 1
        
        if status_code >= 400:
            self.error_counts[minute] += 1
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        if not self.metrics_history:
            return None
        return self.metrics_history[-1]
    
    def get_metrics_history(self, hours: int = 1) -> List[PerformanceMetrics]:
        """Get metrics history for specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp > cutoff]
    
    def get_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alerts if a["timestamp"] > cutoff]
    
    def get_baselines(self) -> Dict[str, float]:
        """Get performance baselines"""
        return self.baselines.copy()

class PerformanceOptimizer:
    """Performance optimization engine"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.optimization_history = []
    
    async def analyze_performance(self) -> List[OptimizationRecommendation]:
        """Analyze current performance and generate recommendations"""
        recommendations = []
        
        # Get current metrics
        current = self.monitor.get_current_metrics()
        if not current:
            return recommendations
        
        # Get baselines
        baselines = self.monitor.get_baselines()
        
        # CPU optimization
        if current.cpu_percent > 70:
            recommendations.append(OptimizationRecommendation(
                category="cpu",
                priority="high" if current.cpu_percent > 85 else "medium",
                title="High CPU Usage",
                description=f"CPU usage is {current.cpu_percent:.1f}%, above optimal levels",
                impact="Reduced response times and potential service degradation",
                effort="medium",
                current_value=f"{current.cpu_percent:.1f}%",
                recommended_value="< 70%",
                estimated_improvement="20-30% better response times"
            ))
        
        # Memory optimization
        if current.memory_percent > 80:
            recommendations.append(OptimizationRecommendation(
                category="memory",
                priority="high" if current.memory_percent > 90 else "medium",
                title="High Memory Usage",
                description=f"Memory usage is {current.memory_percent:.1f}%, approaching limits",
                impact="Potential out-of-memory errors and service crashes",
                effort="high",
                current_value=f"{current.memory_percent:.1f}%",
                recommended_value="< 80%",
                estimated_improvement="Prevent service crashes and improve stability"
            ))
        
        # Database optimization
        if current.db_connections_active > 40:
            recommendations.append(OptimizationRecommendation(
                category="database",
                priority="high",
                title="High Database Connection Usage",
                description=f"Using {current.db_connections_active} of 50 database connections",
                impact="Potential connection pool exhaustion and request failures",
                effort="medium",
                current_value=f"{current.db_connections_active} connections",
                recommended_value="< 40 connections",
                estimated_improvement="Better connection availability and reduced timeouts"
            ))
        
        # Response time optimization
        if current.response_time_p95 > 1.0:
            recommendations.append(OptimizationRecommendation(
                category="response_time",
                priority="high" if current.response_time_p95 > 2.0 else "medium",
                title="Slow Response Times",
                description=f"95th percentile response time is {current.response_time_p95:.2f}s",
                impact="Poor user experience and potential timeout errors",
                effort="medium",
                current_value=f"{current.response_time_p95:.2f}s",
                recommended_value="< 1.0s",
                estimated_improvement="30-50% faster response times"
            ))
        
        # Error rate optimization
        if current.error_rate > 0.02:
            recommendations.append(OptimizationRecommendation(
                category="reliability",
                priority="high" if current.error_rate > 0.05 else "medium",
                title="High Error Rate",
                description=f"Error rate is {current.error_rate:.2%}, above acceptable levels",
                impact="Poor user experience and potential data loss",
                effort="high",
                current_value=f"{current.error_rate:.2%}",
                recommended_value="< 2%",
                estimated_improvement="Better reliability and user satisfaction"
            ))
        
        # Cache optimization
        cache_stats = await cache_service.get_stats()
        if cache_stats.get("hit_rate", 0) < 0.7:
            recommendations.append(OptimizationRecommendation(
                category="caching",
                priority="medium",
                title="Low Cache Hit Rate",
                description=f"Cache hit rate is {cache_stats.get('hit_rate', 0):.1%}",
                impact="Increased database load and slower response times",
                effort="low",
                current_value=f"{cache_stats.get('hit_rate', 0):.1%}",
                recommended_value="> 70%",
                estimated_improvement="20-40% faster response times"
            ))
        
        return recommendations
    
    async def get_optimization_summary(self) -> Dict[str, Any]:
        """Get comprehensive optimization summary"""
        recommendations = await self.analyze_performance()
        current = self.monitor.get_current_metrics()
        baselines = self.monitor.get_baselines()
        alerts = self.monitor.get_alerts(24)
        
        # Categorize recommendations
        by_category = defaultdict(list)
        for rec in recommendations:
            by_category[rec.category].append(rec)
        
        # Calculate optimization score
        total_issues = len(recommendations)
        high_priority = len([r for r in recommendations if r.priority == "high"])
        medium_priority = len([r for r in recommendations if r.priority == "medium"])
        
        optimization_score = max(0, 100 - (high_priority * 20 + medium_priority * 10))
        
        return {
            "optimization_score": optimization_score,
            "total_recommendations": total_issues,
            "high_priority_issues": high_priority,
            "medium_priority_issues": medium_priority,
            "recommendations_by_category": dict(by_category),
            "current_metrics": current.__dict__ if current else {},
            "baselines": baselines,
            "recent_alerts": len(alerts),
            "performance_trend": self._calculate_trend()
        }
    
    def _calculate_trend(self) -> str:
        """Calculate performance trend"""
        history = self.monitor.get_metrics_history(2)
        if len(history) < 10:
            return "insufficient_data"
        
        # Compare first half vs second half
        mid = len(history) // 2
        first_half = history[:mid]
        second_half = history[mid:]
        
        # Calculate average response time for each half
        first_avg = sum(m.response_time_p95 for m in first_half) / len(first_half)
        second_avg = sum(m.response_time_p95 for m in second_half) / len(second_half)
        
        if second_avg < first_avg * 0.9:
            return "improving"
        elif second_avg > first_avg * 1.1:
            return "degrading"
        else:
            return "stable"

class PerformanceService:
    """Main performance service"""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.optimizer = PerformanceOptimizer(self.monitor)
        self.auto_optimization_enabled = False
    
    def start(self):
        """Start performance monitoring and optimization"""
        self.monitor.start_monitoring()
        logger.info("Performance service started")
    
    def stop(self):
        """Stop performance monitoring"""
        self.monitor.stop_monitoring()
        logger.info("Performance service stopped")
    
    def record_request(self, duration: float, status_code: int):
        """Record request performance"""
        self.monitor.record_request(duration, status_code)
    
    async def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""
        current = self.monitor.get_current_metrics()
        history = self.monitor.get_metrics_history(24)
        recommendations = await self.optimizer.analyze_performance()
        summary = await self.optimizer.get_optimization_summary()
        alerts = self.monitor.get_alerts(24)
        
        # Query performance analysis
        query_analysis = await db_optimizer.analyze_query_performance()
        
        # Cache statistics
        cache_stats = await cache_service.get_stats()
        
        return {
            "current_metrics": current.__dict__ if current else {},
            "metrics_history": [m.__dict__ for m in history[-100:]],  # Last 100 points
            "recommendations": [
                {
                    "category": r.category,
                    "priority": r.priority,
                    "title": r.title,
                    "description": r.description,
                    "impact": r.impact,
                    "effort": r.effort,
                    "current_value": r.current_value,
                    "recommended_value": r.recommended_value,
                    "estimated_improvement": r.estimated_improvement
                }
                for r in recommendations
            ],
            "optimization_summary": summary,
            "recent_alerts": alerts,
            "query_performance": query_analysis,
            "cache_statistics": cache_stats,
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": psutil.virtual_memory().total / (1024 * 1024 * 1024),
                "disk_total_gb": psutil.disk_usage('/').total / (1024 * 1024 * 1024)
            }
        }
    
    async def apply_optimization(self, recommendation_id: str) -> bool:
        """Apply a specific optimization recommendation"""
        # This would implement specific optimizations based on recommendation type
        # For now, we'll just log the action
        logger.info("Optimization applied", recommendation_id=recommendation_id)
        return True
    
    async def get_performance_alerts(self) -> List[Dict[str, Any]]:
        """Get recent performance alerts"""
        return self.monitor.get_alerts(24)
    
    async def clear_alerts(self):
        """Clear all performance alerts"""
        self.monitor.alerts.clear()
        logger.info("Performance alerts cleared")

# Global performance service instance
performance_service = PerformanceService()

# Performance monitoring decorator
def monitor_performance(func):
    """Decorator to monitor function performance"""
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        status_code = 200
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            performance_service.record_request(duration, status_code)
    
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        status_code = 200
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            performance_service.record_request(duration, status_code)
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper