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
    # Check if columns already exist before adding them
    connection = op.get_bind()
    
    # Check if mobile_phone column exists
    if "postgresql" in connection.dialect.name:
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'mobile_phone'
            );
        """))
        mobile_phone_exists = result.scalar()
    else:  # SQLite
        result = connection.execute(sa.text("PRAGMA table_info(users);"))
        mobile_phone_exists = any(row[1] == 'mobile_phone' for row in result.fetchall())
    
    # Check if phone_verified column exists
    if "postgresql" in connection.dialect.name:
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'phone_verified'
            );
        """))
        phone_verified_exists = result.scalar()
    else:  # SQLite
        result = connection.execute(sa.text("PRAGMA table_info(users);"))
        phone_verified_exists = any(row[1] == 'phone_verified' for row in result.fetchall())
    
    # Only add columns if they don't exist
    if not mobile_phone_exists or not phone_verified_exists:
        with op.batch_alter_table('users') as batch_op:
            if not mobile_phone_exists:
                batch_op.add_column(sa.Column('mobile_phone', sa.String(length=20), nullable=True))
            if not phone_verified_exists:
                batch_op.add_column(sa.Column('phone_verified', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    
    # Check if index already exists before creating it
    if "postgresql" in connection.dialect.name:
        result = connection.execute(sa.text("""
            SELECT EXISTS (
                SELECT FROM pg_indexes 
                WHERE tablename = 'users' 
                AND indexname = 'ix_users_mobile_phone_unique'
            );
        """))
        index_exists = result.scalar()
    else:  # SQLite
        result = connection.execute(sa.text("PRAGMA index_list(users);"))
        index_exists = any(row[1] == 'ix_users_mobile_phone_unique' for row in result.fetchall())
    
    # Only create index if it doesn't exist
    if not index_exists:
        op.create_index('ix_users_mobile_phone_unique', 'users', ['mobile_phone'], unique=True)


def downgrade() -> None:
    # Drop index and columns
    op.drop_index('ix_users_mobile_phone_unique', table_name='users')
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('phone_verified')
        batch_op.drop_column('mobile_phone')


