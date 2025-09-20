"""
Document and knowledge base models
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, BigInteger, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid


class Document(Base):
    """Document model for uploaded files"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    filename = Column(Text, nullable=False)
    content_type = Column(Text, nullable=False)
    size = Column(BigInteger, nullable=False)
    path = Column(Text, nullable=False)  # local path or s3 key
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    
    # Processing status
    status = Column(
        String(20), 
        CheckConstraint("status IN ('uploaded','processing','done','failed','deleted')"),
        default="uploaded",
        nullable=False
    )
    error = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"


class DocumentChunk(Base):
    """Document chunk model for vector embeddings"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    chunk_index = Column(BigInteger, nullable=False)
    text = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)  # {page: n, char_range: [s,e]}
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
