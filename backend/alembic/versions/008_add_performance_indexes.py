"""Add performance indexes for database optimization

Revision ID: 008_add_performance_indexes
Revises: 007_create_missing_tables
Create Date: 2024-01-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '008_add_performance_indexes'
down_revision = '007_create_missing_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add composite indexes for common query patterns
    
    # Documents table indexes
    try:
        op.create_index('idx_documents_workspace_status', 'documents', ['workspace_id', 'status'])
    except Exception:
        pass
    try:
        op.create_index('idx_documents_workspace_uploaded_by', 'documents', ['workspace_id', 'uploaded_by'])
    except Exception:
        pass
    try:
        op.create_index('idx_documents_status_uploaded_at', 'documents', ['status', 'uploaded_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_documents_workspace_uploaded_at', 'documents', ['workspace_id', 'uploaded_at'])
    except Exception:
        pass
    
    # Document chunks table indexes
    try:
        op.create_index('idx_document_chunks_workspace_chunk_index', 'document_chunks', ['workspace_id', 'chunk_index'])
    except Exception:
        pass
    try:
        op.create_index('idx_document_chunks_document_chunk_index', 'document_chunks', ['document_id', 'chunk_index'])
    except Exception:
        pass
    
    # Chat sessions table indexes
    try:
        op.create_index('idx_chat_sessions_workspace_is_active', 'chat_sessions', ['workspace_id', 'is_active'])
    except Exception:
        pass
    try:
        op.create_index('idx_chat_sessions_workspace_created_at', 'chat_sessions', ['workspace_id', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_chat_sessions_user_created_at', 'chat_sessions', ['user_id', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_chat_sessions_last_activity', 'chat_sessions', ['last_activity_at'])
    except Exception:
        pass
    
    # Chat messages table indexes
    try:
        op.create_index('idx_chat_messages_session_created_at', 'chat_messages', ['session_id', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_chat_messages_role_created_at', 'chat_messages', ['role', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_chat_messages_is_flagged_created_at', 'chat_messages', ['is_flagged', 'created_at'])
    except Exception:
        pass
    
    # Embed codes table indexes
    try:
        op.create_index('idx_embed_codes_workspace_is_active', 'embed_codes', ['workspace_id', 'is_active'])
    except Exception:
        pass
    try:
        op.create_index('idx_embed_codes_workspace_created_at', 'embed_codes', ['workspace_id', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_embed_codes_last_used', 'embed_codes', ['last_used'])
    except Exception:
        pass
    
    # Subscriptions table indexes
    try:
        op.create_index('idx_subscriptions_plan_status', 'subscriptions', ['plan', 'status'])
    except Exception:
        pass
    try:
        op.create_index('idx_subscriptions_status_created_at', 'subscriptions', ['status', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_subscriptions_current_period_end', 'subscriptions', ['current_period_end'])
    except Exception:
        pass
    
    # Team members table indexes
    try:
        op.create_index('idx_team_members_workspace_user', 'team_members', ['workspace_id', 'user_id'])
    except Exception:
        pass
    try:
        op.create_index('idx_team_members_workspace_role', 'team_members', ['workspace_id', 'role'])
    except Exception:
        pass
    try:
        op.create_index('idx_team_members_workspace_is_active', 'team_members', ['workspace_id', 'is_active'])
    except Exception:
        pass
    try:
        op.create_index('idx_team_members_user_is_active', 'team_members', ['user_id', 'is_active'])
    except Exception:
        pass
    
    # Users table indexes
    try:
        op.create_index('idx_users_workspace_is_active', 'users', ['workspace_id', 'is_active'])
    except Exception:
        pass
    try:
        op.create_index('idx_users_workspace_created_at', 'users', ['workspace_id', 'created_at'])
    except Exception:
        pass
    try:
        op.create_index('idx_users_email_verified_is_active', 'users', ['email_verified', 'is_active'])
    except Exception:
        pass
    try:
        op.create_index('idx_users_last_login_at', 'users', ['last_login_at'])
    except Exception:
        pass
    
    # Workspaces table indexes
    try:
        op.create_index('idx_workspaces_plan_is_active', 'workspaces', ['plan', 'is_active'])
    except Exception:
        pass
    try:
        op.create_index('idx_workspaces_created_at', 'workspaces', ['created_at'])
    except Exception:
        pass
    
    # Performance metrics table indexes (if they don't exist)
    try:
        op.create_index('idx_performance_metrics_workspace_metric_timestamp', 'performance_metrics', ['workspace_id', 'metric_type', 'timestamp'])
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
    
    # Performance alerts table indexes (if they don't exist)
    try:
        op.create_index('idx_performance_alerts_workspace_severity', 'performance_alerts', ['workspace_id', 'severity'])
    except Exception:
        pass
    try:
        op.create_index('idx_performance_alerts_workspace_created_resolved', 'performance_alerts', ['workspace_id', 'created_at', 'is_resolved'])
    except Exception:
        pass


def downgrade():
    # Drop composite indexes
    
    # Performance alerts indexes
    try:
        op.drop_index('idx_performance_alerts_workspace_created_resolved', table_name='performance_alerts')
        op.drop_index('idx_performance_alerts_workspace_severity', table_name='performance_alerts')
    except Exception:
        pass
    
    # Performance metrics indexes
    try:
        op.drop_index('idx_performance_metrics_metric_type_timestamp', table_name='performance_metrics')
        op.drop_index('idx_performance_metrics_user_timestamp', table_name='performance_metrics')
        op.drop_index('idx_performance_metrics_workspace_metric_timestamp', table_name='performance_metrics')
    except Exception:
        pass
    
    # Workspaces indexes
    op.drop_index('idx_workspaces_created_at', table_name='workspaces')
    op.drop_index('idx_workspaces_plan_is_active', table_name='workspaces')
    
    # Users indexes
    op.drop_index('idx_users_last_login_at', table_name='users')
    op.drop_index('idx_users_email_verified_is_active', table_name='users')
    op.drop_index('idx_users_workspace_created_at', table_name='users')
    op.drop_index('idx_users_workspace_is_active', table_name='users')
    
    # Team members indexes
    op.drop_index('idx_team_members_user_is_active', table_name='team_members')
    op.drop_index('idx_team_members_workspace_is_active', table_name='team_members')
    op.drop_index('idx_team_members_workspace_role', table_name='team_members')
    op.drop_index('idx_team_members_workspace_user', table_name='team_members')
    
    # Subscriptions indexes
    op.drop_index('idx_subscriptions_current_period_end', table_name='subscriptions')
    op.drop_index('idx_subscriptions_status_created_at', table_name='subscriptions')
    op.drop_index('idx_subscriptions_plan_status', table_name='subscriptions')
    
    # Embed codes indexes
    op.drop_index('idx_embed_codes_last_used', table_name='embed_codes')
    op.drop_index('idx_embed_codes_workspace_created_at', table_name='embed_codes')
    op.drop_index('idx_embed_codes_workspace_is_active', table_name='embed_codes')
    
    # Chat messages indexes
    op.drop_index('idx_chat_messages_is_flagged_created_at', table_name='chat_messages')
    op.drop_index('idx_chat_messages_role_created_at', table_name='chat_messages')
    op.drop_index('idx_chat_messages_session_created_at', table_name='chat_messages')
    
    # Chat sessions indexes
    op.drop_index('idx_chat_sessions_last_activity', table_name='chat_sessions')
    op.drop_index('idx_chat_sessions_user_created_at', table_name='chat_sessions')
    op.drop_index('idx_chat_sessions_workspace_created_at', table_name='chat_sessions')
    op.drop_index('idx_chat_sessions_workspace_is_active', table_name='chat_sessions')
    
    # Document chunks indexes
    op.drop_index('idx_document_chunks_document_chunk_index', table_name='document_chunks')
    op.drop_index('idx_document_chunks_workspace_chunk_index', table_name='document_chunks')
    
    # Documents indexes
    op.drop_index('idx_documents_workspace_uploaded_at', table_name='documents')
    op.drop_index('idx_documents_status_uploaded_at', table_name='documents')
    op.drop_index('idx_documents_workspace_uploaded_by', table_name='documents')
    op.drop_index('idx_documents_workspace_status', table_name='documents')
