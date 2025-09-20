"""Add subscriptions table

Revision ID: 003_add_subscriptions_table
Revises: 002_add_embed_codes_table
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_subscriptions_table'
down_revision = '002_add_embed_codes_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create workspaces table first
    op.create_table('workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('support_email', sa.String(length=255), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('plan', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add workspace_id to users table
    op.add_column('users', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_users_workspace_id', 'users', 'workspaces', ['workspace_id'], ['id'])
    
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=False),
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
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes
    op.create_index('ix_subscriptions_workspace_id', 'subscriptions', ['workspace_id'])
    op.create_index('ix_subscriptions_stripe_customer_id', 'subscriptions', ['stripe_customer_id'])
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'])
    op.create_index('ix_subscriptions_tier', 'subscriptions', ['tier'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])


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
