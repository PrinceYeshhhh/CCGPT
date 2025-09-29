"""
Performance monitoring schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MetricType(str, Enum):
    """Performance metric types"""
    LCP = "lcp"  # Largest Contentful Paint
    FID = "fid"  # First Input Delay
    CLS = "cls"  # Cumulative Layout Shift
    FCP = "fcp"  # First Contentful Paint
    TTFB = "ttfb"  # Time to First Byte
    PAGE_LOAD = "page_load"
    API_RESPONSE = "api_response"
    RENDER = "render"
    MEMORY = "memory"
    CLICKS = "clicks"
    SCROLL = "scroll"
    TIME_ON_PAGE = "time_on_page"
    ERRORS = "errors"
    API_ERRORS = "api_errors"


class PerformanceMetric(BaseModel):
    """Individual performance metric"""
    type: MetricType
    value: float
    timestamp: datetime
    url: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


class PerformanceMetricsRequest(BaseModel):
    """Request to store performance metrics"""
    metrics: List[PerformanceMetric]
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class PerformanceMetricsResponse(BaseModel):
    """Response after storing performance metrics"""
    status: str
    message: str
    stored_count: int


class PerformanceSummary(BaseModel):
    """Performance summary for a workspace"""
    workspace_id: str
    period_days: int
    
    # Core Web Vitals
    avg_lcp: Optional[float] = None
    avg_fid: Optional[float] = None
    avg_cls: Optional[float] = None
    avg_fcp: Optional[float] = None
    avg_ttfb: Optional[float] = None
    
    # Custom metrics
    avg_page_load_time: Optional[float] = None
    avg_api_response_time: Optional[float] = None
    avg_render_time: Optional[float] = None
    avg_memory_usage: Optional[float] = None
    
    # User interaction metrics
    total_clicks: int = 0
    avg_scroll_depth: float = 0.0
    avg_time_on_page: float = 0.0
    
    # Error metrics
    total_errors: int = 0
    total_api_errors: int = 0
    error_rate: float = 0.0
    
    # Performance scores
    performance_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    best_practices_score: Optional[float] = None
    seo_score: Optional[float] = None
    
    # Health indicators
    is_healthy: bool = True
    health_issues: List[str] = Field(default_factory=list)
    
    # Comparison with previous period
    lcp_trend: Optional[str] = None  # "improving", "degrading", "stable"
    fid_trend: Optional[str] = None
    cls_trend: Optional[str] = None
    error_trend: Optional[str] = None


class PerformanceTrendData(BaseModel):
    """Performance trend data point"""
    date: datetime
    value: float
    metric_type: MetricType


class PerformanceTrends(BaseModel):
    """Performance trends over time"""
    workspace_id: str
    period_days: int
    trends: Dict[str, List[PerformanceTrendData]]
    summary: Dict[str, Any]


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PerformanceAlerts(BaseModel):
    """Performance alert"""
    id: str
    workspace_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    metric_type: MetricType
    threshold_value: float
    actual_value: float
    created_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool = False


class BenchmarkResult(BaseModel):
    """Performance benchmark result"""
    benchmark_type: str
    workspace_id: str
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    
    # Test results
    tests_run: int
    tests_passed: int
    tests_failed: int
    
    # Performance metrics
    avg_response_time: float
    max_response_time: float
    min_response_time: float
    requests_per_second: float
    
    # Resource usage
    cpu_usage_percent: float
    memory_usage_mb: float
    disk_io_mb: float
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    score: float  # 0-100


class HealthStatus(BaseModel):
    """Overall performance health status"""
    workspace_id: str
    overall_health: str  # "healthy", "warning", "critical"
    health_score: float  # 0-100
    
    # Component health
    database_health: str
    api_health: str
    frontend_health: str
    cache_health: str
    
    # Performance indicators
    response_time_status: str
    error_rate_status: str
    resource_usage_status: str
    
    # Issues
    active_issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    
    last_updated: datetime


class PerformanceConfig(BaseModel):
    """Performance monitoring configuration"""
    workspace_id: str
    
    # Monitoring settings
    enable_web_vitals: bool = True
    enable_custom_metrics: bool = True
    enable_user_tracking: bool = True
    enable_error_tracking: bool = True
    
    # Alerting thresholds
    lcp_threshold_ms: float = 2500
    fid_threshold_ms: float = 100
    cls_threshold: float = 0.1
    error_rate_threshold: float = 0.05
    response_time_threshold_ms: float = 2000
    
    # Reporting settings
    report_interval_minutes: int = 30
    batch_size: int = 100
    retention_days: int = 90
    
    # Notification settings
    enable_email_alerts: bool = True
    enable_webhook_alerts: bool = False
    alert_email: Optional[str] = None
    webhook_url: Optional[str] = None


class PerformanceReport(BaseModel):
    """Performance report for a period"""
    workspace_id: str
    report_period: str
    generated_at: datetime
    
    # Executive summary
    executive_summary: str
    key_metrics: Dict[str, Any]
    
    # Detailed analysis
    web_vitals_analysis: Dict[str, Any]
    custom_metrics_analysis: Dict[str, Any]
    user_behavior_analysis: Dict[str, Any]
    error_analysis: Dict[str, Any]
    
    # Trends and patterns
    trends: Dict[str, Any]
    patterns: List[str]
    
    # Recommendations
    recommendations: List[str]
    priority_actions: List[str]
    
    # Technical details
    technical_details: Dict[str, Any]
