"""Add email verification fields to users

Revision ID: 005_add_email_verification_fields
Revises: 004_add_mobile_phone_unique
Create Date: 2025-09-24 00:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005_add_email_verification_fields'
down_revision = '004_add_mobile_phone_unique'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('email_verified', sa.Boolean(), nullable=True, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('email_verification_token', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('email_verification_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_users_email_verification_token', 'users', ['email_verification_token'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_users_email_verification_token', table_name='users')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('email_verification_sent_at')
        batch_op.drop_column('email_verification_token')
        batch_op.drop_column('email_verified')


