"""Update documents tables with UUID and workspace support

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing tables if they exist
    try:
        op.drop_table('document_chunks')
    except Exception:
        pass  # Table doesn't exist, continue
    
    try:
        op.drop_table('documents')
    except Exception:
        pass  # Table doesn't exist, continue
    
    # Create new documents table
    op.create_table('documents',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('workspace_id', sa.String(36), nullable=False),
        sa.Column('filename', sa.Text(), nullable=False),
        sa.Column('content_type', sa.Text(), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('path', sa.Text(), nullable=False),
        sa.Column('uploaded_by', sa.String(36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.CheckConstraint("status IN ('uploaded','processing','done','failed','deleted')", name='documents_status_check'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_workspace_id'), 'documents', ['workspace_id'], unique=False)
    
    # Create new document_chunks table
    op.create_table('document_chunks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('workspace_id', sa.String(36), nullable=False),
        sa.Column('chunk_index', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)
    op.create_index(op.f('ix_document_chunks_workspace_id'), 'document_chunks', ['workspace_id'], unique=False)


def downgrade() -> None:
    # Drop new tables
    op.drop_table('document_chunks')
    op.drop_table('documents')
    
    # Recreate old tables (simplified version)
    op.create_table('documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=10), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    
    op.create_table('document_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=64), nullable=False),
        sa.Column('embedding_id', sa.String(length=255), nullable=True),
        sa.Column('vector_dimension', sa.Integer(), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section_title', sa.String(length=255), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)
