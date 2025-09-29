"""
Performance monitoring service for collecting and analyzing frontend metrics
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
import structlog

from app.core.config import settings
from app.models.performance import PerformanceMetric as PerformanceMetricModel
from app.schemas.performance import (
    PerformanceSummary,
    PerformanceTrends,
    PerformanceTrendData,
    PerformanceAlerts,
    AlertSeverity,
    BenchmarkResult,
    HealthStatus,
    MetricType
)
from app.exceptions import AnalyticsError, DatabaseError

logger = structlog.get_logger()


class PerformanceService:
    """Service for managing performance metrics and analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def store_metrics(
        self, 
        workspace_id: str, 
        user_id: str, 
        metrics: List[Dict[str, Any]], 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store performance metrics in the database"""
        try:
            stored_count = 0
            
            for metric_data in metrics:
                # Create performance metric record
                metric = PerformanceMetricModel(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    metric_type=metric_data.get('type'),
                    value=metric_data.get('value', 0.0),
                    url=metadata.get('url'),
                    user_agent=metadata.get('userAgent'),
                    session_id=metadata.get('sessionId'),
                    timestamp=datetime.utcnow(),
                    metadata=json.dumps(metadata)
                )
                
                self.db.add(metric)
                stored_count += 1
            
            self.db.commit()
            
            # Trigger real-time analysis
            await self._analyze_metrics(workspace_id)
            
            return {"stored_count": stored_count}
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to store performance metrics",
                error=str(e),
                workspace_id=workspace_id
            )
            raise DatabaseError(f"Failed to store performance metrics: {str(e)}")
    
    async def get_performance_summary(
        self, 
        workspace_id: str, 
        days: int = 7
    ) -> PerformanceSummary:
        """Get performance summary for a workspace"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get metrics for the period
            metrics = self.db.query(PerformanceMetricModel).filter(
                and_(
                    PerformanceMetricModel.workspace_id == workspace_id,
                    PerformanceMetricModel.timestamp >= start_date,
                    PerformanceMetricModel.timestamp <= end_date
                )
            ).all()
            
            # Calculate summary statistics
            summary = await self._calculate_summary(workspace_id, metrics, days)
            
            return summary
            
        except Exception as e:
            logger.error(
                "Failed to get performance summary",
                error=str(e),
                workspace_id=workspace_id
            )
            raise AnalyticsError(f"Failed to get performance summary: {str(e)}")
    
    async def get_performance_trends(
        self, 
        workspace_id: str, 
        days: int = 30,
        metric_type: Optional[str] = None
    ) -> PerformanceTrends:
        """Get performance trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Build query
            query = self.db.query(PerformanceMetricModel).filter(
                and_(
                    PerformanceMetricModel.workspace_id == workspace_id,
                    PerformanceMetricModel.timestamp >= start_date,
                    PerformanceMetricModel.timestamp <= end_date
                )
            )
            
            if metric_type:
                query = query.filter(PerformanceMetricModel.metric_type == metric_type)
            
            metrics = query.all()
            
            # Group metrics by type and date
            trends = {}
            for metric in metrics:
                metric_type = metric.metric_type
                date = metric.timestamp.date()
                
                if metric_type not in trends:
                    trends[metric_type] = {}
                
                if date not in trends[metric_type]:
                    trends[metric_type][date] = []
                
                trends[metric_type][date].append(metric.value)
            
            # Calculate daily averages
            trend_data = {}
            for metric_type, daily_metrics in trends.items():
                trend_data[metric_type] = []
                for date, values in daily_metrics.items():
                    avg_value = sum(values) / len(values)
                    trend_data[metric_type].append(
                        PerformanceTrendData(
                            date=datetime.combine(date, datetime.min.time()),
                            value=avg_value,
                            metric_type=MetricType(metric_type)
                        )
                    )
                
                # Sort by date
                trend_data[metric_type].sort(key=lambda x: x.date)
            
            # Calculate summary statistics
            summary = await self._calculate_trends_summary(trend_data)
            
            return PerformanceTrends(
                workspace_id=workspace_id,
                period_days=days,
                trends=trend_data,
                summary=summary
            )
            
        except Exception as e:
            logger.error(
                "Failed to get performance trends",
                error=str(e),
                workspace_id=workspace_id
            )
            raise AnalyticsError(f"Failed to get performance trends: {str(e)}")
    
    async def get_performance_alerts(
        self, 
        workspace_id: str
    ) -> List[PerformanceAlerts]:
        """Get performance alerts for a workspace"""
        try:
            # This would typically query an alerts table
            # For now, we'll generate alerts based on current metrics
            alerts = await self._generate_alerts(workspace_id)
            
            return alerts
            
        except Exception as e:
            logger.error(
                "Failed to get performance alerts",
                error=str(e),
                workspace_id=workspace_id
            )
            raise AnalyticsError(f"Failed to get performance alerts: {str(e)}")
    
    async def get_real_time_metrics(
        self, 
        workspace_id: str
    ) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        try:
            # Get metrics from the last hour
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics = self.db.query(PerformanceMetricModel).filter(
                and_(
                    PerformanceMetricModel.workspace_id == workspace_id,
                    PerformanceMetricModel.timestamp >= start_time,
                    PerformanceMetricModel.timestamp <= end_time
                )
            ).all()
            
            # Calculate real-time statistics
            real_time_data = {
                "timestamp": end_time.isoformat(),
                "metrics": {},
                "active_users": len(set(m.user_id for m in metrics)),
                "total_requests": len(metrics)
            }
            
            # Group by metric type
            for metric in metrics:
                metric_type = metric.metric_type
                if metric_type not in real_time_data["metrics"]:
                    real_time_data["metrics"][metric_type] = []
                real_time_data["metrics"][metric_type].append(metric.value)
            
            # Calculate averages
            for metric_type, values in real_time_data["metrics"].items():
                if values:
                    real_time_data["metrics"][metric_type] = {
                        "current": values[-1] if values else 0,
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
            
            return real_time_data
            
        except Exception as e:
            logger.error(
                "Failed to get real-time metrics",
                error=str(e),
                workspace_id=workspace_id
            )
            raise AnalyticsError(f"Failed to get real-time metrics: {str(e)}")
    
    async def run_benchmark(
        self, 
        workspace_id: str, 
        benchmark_type: str = "full"
    ) -> BenchmarkResult:
        """Run performance benchmark for a workspace"""
        try:
            start_time = datetime.utcnow()
            
            # Simulate benchmark tests
            benchmark_results = await self._run_benchmark_tests(
                workspace_id, 
                benchmark_type
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            return BenchmarkResult(
                benchmark_type=benchmark_type,
                workspace_id=workspace_id,
                started_at=start_time,
                completed_at=end_time,
                duration_seconds=duration,
                **benchmark_results
            )
            
        except Exception as e:
            logger.error(
                "Failed to run performance benchmark",
                error=str(e),
                workspace_id=workspace_id
            )
            raise AnalyticsError(f"Failed to run performance benchmark: {str(e)}")
    
    async def get_health_status(
        self, 
        workspace_id: str
    ) -> HealthStatus:
        """Get overall performance health status"""
        try:
            # Get recent metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            metrics = self.db.query(PerformanceMetricModel).filter(
                and_(
                    PerformanceMetricModel.workspace_id == workspace_id,
                    PerformanceMetricModel.timestamp >= start_time,
                    PerformanceMetricModel.timestamp <= end_time
                )
            ).all()
            
            # Calculate health indicators
            health_status = await self._calculate_health_status(
                workspace_id, 
                metrics
            )
            
            return health_status
            
        except Exception as e:
            logger.error(
                "Failed to get performance health",
                error=str(e),
                workspace_id=workspace_id
            )
            raise AnalyticsError(f"Failed to get performance health: {str(e)}")
    
    async def _analyze_metrics(self, workspace_id: str) -> None:
        """Analyze metrics and generate alerts if needed"""
        try:
            # This would typically run in the background
            # For now, we'll just log the analysis
            logger.info(
                "Analyzing performance metrics",
                workspace_id=workspace_id
            )
            
        except Exception as e:
            logger.error(
                "Failed to analyze metrics",
                error=str(e),
                workspace_id=workspace_id
            )
    
    async def _calculate_summary(
        self, 
        workspace_id: str, 
        metrics: List[PerformanceMetricModel], 
        days: int
    ) -> PerformanceSummary:
        """Calculate performance summary from metrics"""
        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            metric_type = metric.metric_type
            if metric_type not in metrics_by_type:
                metrics_by_type[metric_type] = []
            metrics_by_type[metric_type].append(metric.value)
        
        # Calculate averages
        summary_data = {
            "workspace_id": workspace_id,
            "period_days": days,
            "is_healthy": True,
            "health_issues": []
        }
        
        # Core Web Vitals
        for vitals_type in ["lcp", "fid", "cls", "fcp", "ttfb"]:
            if vitals_type in metrics_by_type:
                values = metrics_by_type[vitals_type]
                summary_data[f"avg_{vitals_type}"] = sum(values) / len(values)
        
        # Custom metrics
        for custom_type in ["page_load", "api_response", "render", "memory"]:
            if custom_type in metrics_by_type:
                values = metrics_by_type[custom_type]
                summary_data[f"avg_{custom_type}_time"] = sum(values) / len(values)
        
        # User interaction metrics
        if "clicks" in metrics_by_type:
            summary_data["total_clicks"] = sum(metrics_by_type["clicks"])
        
        if "scroll" in metrics_by_type:
            scroll_values = metrics_by_type["scroll"]
            summary_data["avg_scroll_depth"] = sum(scroll_values) / len(scroll_values)
        
        if "time_on_page" in metrics_by_type:
            time_values = metrics_by_type["time_on_page"]
            summary_data["avg_time_on_page"] = sum(time_values) / len(time_values)
        
        # Error metrics
        if "errors" in metrics_by_type:
            summary_data["total_errors"] = sum(metrics_by_type["errors"])
        
        if "api_errors" in metrics_by_type:
            summary_data["total_api_errors"] = sum(metrics_by_type["api_errors"])
        
        # Calculate error rate
        total_requests = len(metrics)
        total_errors = summary_data.get("total_errors", 0)
        summary_data["error_rate"] = total_errors / total_requests if total_requests > 0 else 0
        
        # Calculate performance score
        summary_data["performance_score"] = await self._calculate_performance_score(
            summary_data
        )
        
        return PerformanceSummary(**summary_data)
    
    async def _calculate_trends_summary(self, trends: Dict[str, List[PerformanceTrendData]]) -> Dict[str, Any]:
        """Calculate trends summary"""
        summary = {}
        
        for metric_type, trend_data in trends.items():
            if not trend_data:
                continue
            
            values = [point.value for point in trend_data]
            summary[metric_type] = {
                "trend": "stable",
                "change_percent": 0.0,
                "current_value": values[-1] if values else 0,
                "average_value": sum(values) / len(values) if values else 0,
                "min_value": min(values) if values else 0,
                "max_value": max(values) if values else 0
            }
            
            # Calculate trend direction
            if len(values) >= 2:
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]
                
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                
                change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
                summary[metric_type]["change_percent"] = change_percent
                
                if change_percent > 5:
                    summary[metric_type]["trend"] = "improving"
                elif change_percent < -5:
                    summary[metric_type]["trend"] = "degrading"
        
        return summary
    
    async def _generate_alerts(self, workspace_id: str) -> List[PerformanceAlerts]:
        """Generate performance alerts based on current metrics"""
        alerts = []
        
        # This would typically query recent metrics and check against thresholds
        # For now, we'll return an empty list
        return alerts
    
    async def _run_benchmark_tests(
        self, 
        workspace_id: str, 
        benchmark_type: str
    ) -> Dict[str, Any]:
        """Run benchmark tests"""
        # This would typically run actual performance tests
        # For now, we'll return mock results
        return {
            "tests_run": 10,
            "tests_passed": 9,
            "tests_failed": 1,
            "avg_response_time": 150.0,
            "max_response_time": 300.0,
            "min_response_time": 50.0,
            "requests_per_second": 100.0,
            "cpu_usage_percent": 45.0,
            "memory_usage_mb": 512.0,
            "disk_io_mb": 1024.0,
            "recommendations": [
                "Consider optimizing database queries",
                "Enable caching for static assets"
            ],
            "score": 85.0
        }
    
    async def _calculate_health_status(
        self, 
        workspace_id: str, 
        metrics: List[PerformanceMetricModel]
    ) -> HealthStatus:
        """Calculate overall health status"""
        # This would typically analyze various health indicators
        # For now, we'll return a basic health status
        return HealthStatus(
            workspace_id=workspace_id,
            overall_health="healthy",
            health_score=85.0,
            database_health="healthy",
            api_health="healthy",
            frontend_health="healthy",
            cache_health="healthy",
            response_time_status="good",
            error_rate_status="low",
            resource_usage_status="normal",
            active_issues=[],
            recommendations=[],
            last_updated=datetime.utcnow()
        )
    
    async def _calculate_performance_score(self, summary_data: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        score = 100.0
        
        # LCP scoring (0-2.5s = 100, 2.5-4s = 50, >4s = 0)
        lcp = summary_data.get("avg_lcp", 0)
        if lcp > 4000:
            score -= 50
        elif lcp > 2500:
            score -= 25
        
        # FID scoring (0-100ms = 100, 100-300ms = 50, >300ms = 0)
        fid = summary_data.get("avg_fid", 0)
        if fid > 300:
            score -= 50
        elif fid > 100:
            score -= 25
        
        # CLS scoring (0-0.1 = 100, 0.1-0.25 = 50, >0.25 = 0)
        cls = summary_data.get("avg_cls", 0)
        if cls > 0.25:
            score -= 50
        elif cls > 0.1:
            score -= 25
        
        # Error rate penalty
        error_rate = summary_data.get("error_rate", 0)
        if error_rate > 0.05:
            score -= 30
        elif error_rate > 0.01:
            score -= 15
        
        return max(0.0, score)
