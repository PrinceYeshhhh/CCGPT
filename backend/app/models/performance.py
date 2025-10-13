"""
Performance monitoring database models
"""

from sqlalchemy import Column, String, Float, DateTime, Text, Index
from app.core.uuid_type import UUID
from app.db.base import Base
import uuid


class PerformanceMetric(Base):
    """Performance metrics storage model"""
    
    __tablename__ = "performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    url = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    metric_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_workspace_timestamp', 'workspace_id', 'timestamp'),
        Index('idx_workspace_metric_type', 'workspace_id', 'metric_type'),
        Index('idx_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_metric_type_timestamp', 'metric_type', 'timestamp'),
    )


class PerformanceAlert(Base):
    """Performance alerts model"""
    
    __tablename__ = "performance_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String(255), nullable=False, index=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    metric_type = Column(String(50), nullable=False)
    threshold_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    is_resolved = Column(String(10), nullable=False, default='false')
    
    # Indexes
    __table_args__ = (
        Index('idx_workspace_created', 'workspace_id', 'created_at'),
        Index('idx_severity_resolved', 'severity', 'is_resolved'),
    )


class PerformanceConfig(Base):
    """Performance monitoring configuration model"""
    
    __tablename__ = "performance_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Monitoring settings
    enable_web_vitals = Column(String(10), nullable=False, default='true')
    enable_custom_metrics = Column(String(10), nullable=False, default='true')
    enable_user_tracking = Column(String(10), nullable=False, default='true')
    enable_error_tracking = Column(String(10), nullable=False, default='true')
    
    # Alerting thresholds
    lcp_threshold_ms = Column(Float, nullable=False, default=2500.0)
    fid_threshold_ms = Column(Float, nullable=False, default=100.0)
    cls_threshold = Column(Float, nullable=False, default=0.1)
    error_rate_threshold = Column(Float, nullable=False, default=0.05)
    response_time_threshold_ms = Column(Float, nullable=False, default=2000.0)
    
    # Reporting settings
    report_interval_minutes = Column(String(10), nullable=False, default='30')
    batch_size = Column(String(10), nullable=False, default='100')
    retention_days = Column(String(10), nullable=False, default='90')
    
    # Notification settings
    enable_email_alerts = Column(String(10), nullable=False, default='true')
    enable_webhook_alerts = Column(String(10), nullable=False, default='false')
    alert_email = Column(String(255), nullable=True)
    webhook_url = Column(Text, nullable=True)
    
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class PerformanceReport(Base):
    """Performance reports model"""
    
    __tablename__ = "performance_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String(255), nullable=False, index=True)
    report_period = Column(String(50), nullable=False)
    report_type = Column(String(50), nullable=False, default='standard')
    
    # Report data
    executive_summary = Column(Text, nullable=True)
    key_metrics = Column(Text, nullable=True)  # JSON
    detailed_analysis = Column(Text, nullable=True)  # JSON
    trends = Column(Text, nullable=True)  # JSON
    recommendations = Column(Text, nullable=True)  # JSON
    technical_details = Column(Text, nullable=True)  # JSON
    
    # Metadata
    generated_at = Column(DateTime, nullable=False, index=True)
    generated_by = Column(String(255), nullable=True)
    file_path = Column(Text, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_workspace_generated', 'workspace_id', 'generated_at'),
        Index('idx_report_period', 'report_period'),
    )


class PerformanceBenchmark(Base):
    """Performance benchmark results model"""
    
    __tablename__ = "performance_benchmarks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(String(255), nullable=False, index=True)
    benchmark_type = Column(String(50), nullable=False)
    
    # Test results
    tests_run = Column(String(10), nullable=False)
    tests_passed = Column(String(10), nullable=False)
    tests_failed = Column(String(10), nullable=False)
    
    # Performance metrics
    avg_response_time = Column(Float, nullable=False)
    max_response_time = Column(Float, nullable=False)
    min_response_time = Column(Float, nullable=False)
    requests_per_second = Column(Float, nullable=False)
    
    # Resource usage
    cpu_usage_percent = Column(Float, nullable=False)
    memory_usage_mb = Column(Float, nullable=False)
    disk_io_mb = Column(Float, nullable=False)
    
    # Results
    score = Column(Float, nullable=False)
    recommendations = Column(Text, nullable=True)  # JSON array
    
    # Metadata
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_workspace_benchmark', 'workspace_id', 'benchmark_type'),
        Index('idx_benchmark_started', 'started_at'),
    )
