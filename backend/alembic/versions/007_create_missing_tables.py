"""Create missing tables for complete schema

Revision ID: 007_create_missing_tables
Revises: 006_add_performance_tables
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_create_missing_tables'
down_revision = '006_add_performance_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create workspaces table
    op.create_table('workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('support_email', sa.String(length=255), nullable=True),
        sa.Column('custom_domain', sa.String(length=255), nullable=True),
        sa.Column('widget_domain', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_workspaces_id'), 'workspaces', ['id'], unique=False)
    op.create_index('idx_workspaces_plan', 'workspaces', ['plan'])
    op.create_index('idx_workspaces_is_active', 'workspaces', ['is_active'])

    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('user_label', sa.String(length=255), nullable=True),
        sa.Column('visitor_ip', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_chat_sessions_id'), 'chat_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_session_id'), 'chat_sessions', ['session_id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_workspace_id'), 'chat_sessions', ['workspace_id'], unique=False)
    op.create_index('idx_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    op.create_index('idx_chat_sessions_is_active', 'chat_sessions', ['is_active'])
    op.create_index('idx_chat_sessions_created_at', 'chat_sessions', ['created_at'])

    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('sources_used', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('confidence_score', sa.String(length=10), nullable=True),
        sa.Column('is_flagged', sa.Boolean(), nullable=True),
        sa.Column('flag_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_id'), 'chat_messages', ['id'], unique=False)
    op.create_index('idx_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('idx_chat_messages_role', 'chat_messages', ['role'])
    op.create_index('idx_chat_messages_created_at', 'chat_messages', ['created_at'])
    op.create_index('idx_chat_messages_is_flagged', 'chat_messages', ['is_flagged'])

    # Create embed_codes table
    op.create_table('embed_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('client_api_key', sa.String(length=255), nullable=False),
        sa.Column('default_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('custom_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('embed_script', sa.Text(), nullable=True),
        sa.Column('embed_html', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_api_key')
    )
    op.create_index(op.f('ix_embed_codes_id'), 'embed_codes', ['id'], unique=False)
    op.create_index(op.f('ix_embed_codes_workspace_id'), 'embed_codes', ['workspace_id'], unique=False)
    op.create_index('idx_embed_codes_client_api_key', 'embed_codes', ['client_api_key'])
    op.create_index('idx_embed_codes_is_active', 'embed_codes', ['is_active'])

    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('current_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=True),
        sa.Column('canceled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_id')
    )
    op.create_index(op.f('ix_subscriptions_id'), 'subscriptions', ['id'], unique=False)
    op.create_index(op.f('ix_subscriptions_workspace_id'), 'subscriptions', ['workspace_id'], unique=False)
    op.create_index('idx_subscriptions_plan', 'subscriptions', ['plan'])
    op.create_index('idx_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('idx_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])

    # Create team_members table
    op.create_table('team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('invited_by', sa.Integer(), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_team_members_id'), 'team_members', ['id'], unique=False)
    op.create_index(op.f('ix_team_members_workspace_id'), 'team_members', ['workspace_id'], unique=False)
    op.create_index('idx_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('idx_team_members_role', 'team_members', ['role'])
    op.create_index('idx_team_members_is_active', 'team_members', ['is_active'])

    # Update users table to add workspace_id and other missing fields
    op.add_column('users', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('users', sa.Column('mobile_phone', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('username', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('two_factor_secret', sa.String(length=32), nullable=True))
    op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('email_verification_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), nullable=True))
    op.add_column('users', sa.Column('phone_verification_token', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('phone_verification_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('password_reset_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('password_reset_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('login_attempts', sa.Integer(), nullable=True))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    op.add_column('users', sa.Column('theme', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('language', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('timezone', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('notification_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True))

    # Create indexes for users table
    op.create_index('idx_users_workspace_id', 'users', ['workspace_id'])
    op.create_index('idx_users_mobile_phone', 'users', ['mobile_phone'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_email_verified', 'users', ['email_verified'])
    op.create_index('idx_users_phone_verified', 'users', ['phone_verified'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])

    # Add foreign key constraint for users.workspace_id
    op.create_foreign_key('fk_users_workspace_id', 'users', 'workspaces', ['workspace_id'], ['id'])

    # Create widget_assets table
    op.create_table('widget_assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('embed_code_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('asset_url', sa.String(length=500), nullable=False),
        sa.Column('asset_data', sa.LargeBinary(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['embed_code_id'], ['embed_codes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_widget_assets_id'), 'widget_assets', ['id'], unique=False)
    op.create_index('idx_widget_assets_embed_code_id', 'widget_assets', ['embed_code_id'])
    op.create_index('idx_widget_assets_asset_type', 'widget_assets', ['asset_type'])


def downgrade():
    # Drop widget_assets table
    op.drop_table('widget_assets')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_users_workspace_id', 'users', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_users_timezone', table_name='users')
    op.drop_index('idx_users_language', table_name='users')
    op.drop_index('idx_users_theme', table_name='users')
    op.drop_index('idx_users_notification_settings', table_name='users')
    op.drop_index('idx_users_preferences', table_name='users')
    op.drop_index('idx_users_locked_until', table_name='users')
    op.drop_index('idx_users_login_attempts', table_name='users')
    op.drop_index('idx_users_last_login_at', table_name='users')
    op.drop_index('idx_users_password_reset_sent_at', table_name='users')
    op.drop_index('idx_users_password_reset_token', table_name='users')
    op.drop_index('idx_users_phone_verification_sent_at', table_name='users')
    op.drop_index('idx_users_phone_verification_token', table_name='users')
    op.drop_index('idx_users_phone_verified', table_name='users')
    op.drop_index('idx_users_email_verification_sent_at', table_name='users')
    op.drop_index('idx_users_email_verification_token', table_name='users')
    op.drop_index('idx_users_email_verified', table_name='users')
    op.drop_index('idx_users_two_factor_enabled', table_name='users')
    op.drop_index('idx_users_two_factor_secret', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_users_mobile_phone', table_name='users')
    op.drop_index('idx_users_workspace_id', table_name='users')
    
    # Drop columns from users table
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'language')
    op.drop_column('users', 'theme')
    op.drop_column('users', 'notification_settings')
    op.drop_column('users', 'preferences')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'login_attempts')
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'password_reset_sent_at')
    op.drop_column('users', 'password_reset_token')
    op.drop_column('users', 'phone_verification_sent_at')
    op.drop_column('users', 'phone_verification_token')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'email_verification_sent_at')
    op.drop_column('users', 'email_verification_token')
    op.drop_column('users', 'email_verified')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'two_factor_secret')
    op.drop_column('users', 'username')
    op.drop_column('users', 'mobile_phone')
    op.drop_column('users', 'workspace_id')
    
    # Drop team_members table
    op.drop_table('team_members')
    
    # Drop subscriptions table
    op.drop_table('subscriptions')
    
    # Drop embed_codes table
    op.drop_table('embed_codes')
    
    # Drop chat_messages table
    op.drop_table('chat_messages')
    
    # Drop chat_sessions table
    op.drop_table('chat_sessions')
    
    # Drop workspaces table
    op.drop_table('workspaces')
