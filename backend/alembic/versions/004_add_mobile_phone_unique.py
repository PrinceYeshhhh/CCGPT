"""Add mobile_phone and phone_verified to users, unique index on mobile_phone

Revision ID: 004_add_mobile_phone_unique
Revises: 003_add_subscriptions_table
Create Date: 2025-09-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_mobile_phone_unique'
down_revision = '003_add_subscriptions_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns if not present
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('mobile_phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('phone_verified', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    # Create unique index on mobile_phone (exclude nulls where supported)
    # For broad compatibility, create a unique index and rely on app-level checks to prevent null duplicates
    op.create_index('ix_users_mobile_phone_unique', 'users', ['mobile_phone'], unique=True)


def downgrade() -> None:
    # Drop index and columns
    op.drop_index('ix_users_mobile_phone_unique', table_name='users')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('phone_verified')
        batch_op.drop_column('mobile_phone')


