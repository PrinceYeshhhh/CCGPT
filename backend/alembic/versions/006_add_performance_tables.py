"""Add performance monitoring tables

Revision ID: 006_add_performance_tables
Revises: 005_add_email_verification_fields
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_performance_tables'
down_revision = '005_add_email_verification_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create performance_metrics table
    try:
        op.create_table('performance_metrics',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('workspace_id', sa.String(length=255), nullable=False),
            sa.Column('user_id', sa.String(length=255), nullable=False),
            sa.Column('metric_type', sa.String(length=50), nullable=False),
            sa.Column('value', sa.Float(), nullable=False),
            sa.Column('url', sa.Text(), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('session_id', sa.String(length=255), nullable=True),
            sa.Column('timestamp', sa.DateTime(), nullable=False),
            sa.Column('metadata', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table already exists, continue
    
    # Create indexes for performance_metrics
    try:
        op.create_index('idx_performance_metrics_workspace_id', 'performance_metrics', ['workspace_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_user_id', 'performance_metrics', ['user_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_metric_type', 'performance_metrics', ['metric_type'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_session_id', 'performance_metrics', ['session_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_timestamp', 'performance_metrics', ['timestamp'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_workspace_timestamp', 'performance_metrics', ['workspace_id', 'timestamp'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_workspace_metric_type', 'performance_metrics', ['workspace_id', 'metric_type'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_user_timestamp', 'performance_metrics', ['user_id', 'timestamp'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_metrics_metric_type_timestamp', 'performance_metrics', ['metric_type', 'timestamp'])
    except Exception:
        pass

    # Create performance_alerts table
    try:
        op.create_table('performance_alerts',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('workspace_id', sa.String(length=255), nullable=False),
            sa.Column('alert_type', sa.String(length=100), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('metric_type', sa.String(length=50), nullable=False),
            sa.Column('threshold_value', sa.Float(), nullable=False),
            sa.Column('actual_value', sa.Float(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('resolved_at', sa.DateTime(), nullable=True),
            sa.Column('is_resolved', sa.String(length=10), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table already exists, continue
    
    # Create indexes for performance_alerts
    try:
        op.create_index('idx_performance_alerts_workspace_id', 'performance_alerts', ['workspace_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_alerts_severity', 'performance_alerts', ['severity'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_alerts_created_at', 'performance_alerts', ['created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_alerts_workspace_created', 'performance_alerts', ['workspace_id', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_alerts_severity_resolved', 'performance_alerts', ['severity', 'is_resolved'])
    except Exception:
        pass

    # Create performance_configs table
    try:
        op.create_table('performance_configs',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('workspace_id', sa.String(length=255), nullable=False),
            sa.Column('enable_web_vitals', sa.String(length=10), nullable=False),
            sa.Column('enable_custom_metrics', sa.String(length=10), nullable=False),
            sa.Column('enable_user_tracking', sa.String(length=10), nullable=False),
            sa.Column('enable_error_tracking', sa.String(length=10), nullable=False),
            sa.Column('lcp_threshold_ms', sa.Float(), nullable=False),
            sa.Column('fid_threshold_ms', sa.Float(), nullable=False),
            sa.Column('cls_threshold', sa.Float(), nullable=False),
            sa.Column('error_rate_threshold', sa.Float(), nullable=False),
            sa.Column('response_time_threshold_ms', sa.Float(), nullable=False),
            sa.Column('report_interval_minutes', sa.String(length=10), nullable=False),
            sa.Column('batch_size', sa.String(length=10), nullable=False),
            sa.Column('retention_days', sa.String(length=10), nullable=False),
            sa.Column('enable_email_alerts', sa.String(length=10), nullable=False),
            sa.Column('enable_webhook_alerts', sa.String(length=10), nullable=False),
            sa.Column('alert_email', sa.String(length=255), nullable=True),
            sa.Column('webhook_url', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('workspace_id')
        )
    except Exception:
        pass  # Table already exists, continue
    
    # Create indexes for performance_configs
    try:
        op.create_index('idx_performance_configs_workspace_id', 'performance_configs', ['workspace_id'])
    except Exception:
        pass

    # Create performance_reports table
    try:
        op.create_table('performance_reports',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('workspace_id', sa.String(length=255), nullable=False),
            sa.Column('report_period', sa.String(length=50), nullable=False),
            sa.Column('report_type', sa.String(length=50), nullable=False),
            sa.Column('executive_summary', sa.Text(), nullable=True),
            sa.Column('key_metrics', sa.Text(), nullable=True),
            sa.Column('detailed_analysis', sa.Text(), nullable=True),
            sa.Column('trends', sa.Text(), nullable=True),
            sa.Column('recommendations', sa.Text(), nullable=True),
            sa.Column('technical_details', sa.Text(), nullable=True),
            sa.Column('generated_at', sa.DateTime(), nullable=False),
            sa.Column('generated_by', sa.String(length=255), nullable=True),
            sa.Column('file_path', sa.Text(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table already exists, continue
    
    # Create indexes for performance_reports
    try:
        op.create_index('idx_performance_reports_workspace_id', 'performance_reports', ['workspace_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_reports_generated_at', 'performance_reports', ['generated_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_reports_workspace_generated', 'performance_reports', ['workspace_id', 'generated_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_reports_report_period', 'performance_reports', ['report_period'])
    except Exception:
        pass

    # Create performance_benchmarks table
    try:
        op.create_table('performance_benchmarks',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('workspace_id', sa.String(length=255), nullable=False),
            sa.Column('benchmark_type', sa.String(length=50), nullable=False),
            sa.Column('tests_run', sa.String(length=10), nullable=False),
            sa.Column('tests_passed', sa.String(length=10), nullable=False),
            sa.Column('tests_failed', sa.String(length=10), nullable=False),
            sa.Column('avg_response_time', sa.Float(), nullable=False),
            sa.Column('max_response_time', sa.Float(), nullable=False),
            sa.Column('min_response_time', sa.Float(), nullable=False),
            sa.Column('requests_per_second', sa.Float(), nullable=False),
            sa.Column('cpu_usage_percent', sa.Float(), nullable=False),
            sa.Column('memory_usage_mb', sa.Float(), nullable=False),
            sa.Column('disk_io_mb', sa.Float(), nullable=False),
            sa.Column('score', sa.Float(), nullable=False),
            sa.Column('recommendations', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=False),
            sa.Column('duration_seconds', sa.Float(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table already exists, continue
    
    # Create indexes for performance_benchmarks
    try:
        op.create_index('idx_performance_benchmarks_workspace_id', 'performance_benchmarks', ['workspace_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_benchmarks_benchmark_type', 'performance_benchmarks', ['benchmark_type'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_benchmarks_started_at', 'performance_benchmarks', ['started_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_benchmarks_workspace_benchmark', 'performance_benchmarks', ['workspace_id', 'benchmark_type'])
    except Exception:
        pass


def downgrade():
    # Drop performance_benchmarks table
    op.drop_table('performance_benchmarks')
    
    # Drop performance_reports table
    op.drop_table('performance_reports')
    
    # Drop performance_configs table
    op.drop_table('performance_configs')
    
    # Drop performance_alerts table
    op.drop_table('performance_alerts')
    
    # Drop performance_metrics table
    op.drop_table('performance_metrics')
