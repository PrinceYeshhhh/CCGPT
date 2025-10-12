"""Add subscriptions table

Revision ID: 003_add_subscriptions_table
Revises: 002
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_subscriptions_table'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create workspaces table first (if it doesn't exist)
    try:
        op.create_table('workspaces',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('logo_url', sa.String(length=500), nullable=True),
            sa.Column('website_url', sa.String(length=500), nullable=True),
            sa.Column('support_email', sa.String(length=255), nullable=True),
            sa.Column('timezone', sa.String(length=50), nullable=True),
            sa.Column('plan', sa.String(length=50), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table already exists, continue
    
    # Add workspace_id to users table (if it doesn't exist)
    try:
        op.add_column('users', sa.Column('workspace_id', sa.String(36), nullable=True))
    except Exception:
        pass  # Column already exists, continue
    
    try:
        op.create_foreign_key('fk_users_workspace_id', 'users', 'workspaces', ['workspace_id'], ['id'])
    except Exception:
        pass  # Foreign key already exists, continue
    
    # Create subscriptions table (if it doesn't exist)
    try:
        op.create_table('subscriptions',
            sa.Column('id', sa.String(36), nullable=False),
            sa.Column('workspace_id', sa.String(36), nullable=False),
            sa.Column('stripe_customer_id', sa.String(), nullable=True),
            sa.Column('stripe_subscription_id', sa.String(), nullable=True),
            sa.Column('tier', sa.String(), nullable=False),
            sa.Column('status', sa.String(), nullable=False),
            sa.Column('seats', sa.Integer(), nullable=True),
            sa.Column('monthly_query_quota', sa.BigInteger(), nullable=True),
            sa.Column('queries_this_period', sa.BigInteger(), nullable=True),
            sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
            sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
            sa.Column('next_billing_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('metadata', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    except Exception:
        pass  # Table already exists, continue
    
    # Add indexes
    try:
        op.create_index('ix_subscriptions_workspace_id', 'subscriptions', ['workspace_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_subscriptions_tier', 'subscriptions', ['tier'])
    except Exception:
        pass
    try:
        op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    except Exception:
        pass


def downgrade():
    # Drop subscriptions table
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_tier', table_name='subscriptions')
    op.drop_index('ix_subscriptions_stripe_subscription_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_stripe_customer_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_workspace_id', table_name='subscriptions')
    op.drop_table('subscriptions')
    
    # Remove workspace_id from users table
    op.drop_constraint('fk_users_workspace_id', 'users', type_='foreignkey')
    op.drop_column('users', 'workspace_id')
    
    # Drop workspaces table
    op.drop_table('workspaces')
