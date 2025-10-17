"""
Document and knowledge base models
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, BigInteger, CheckConstraint, Integer
from app.core.uuid_type import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Document(Base):
    """Document model for uploaded files"""
    __tablename__ = "documents"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(UUID(), ForeignKey("workspaces.id"), nullable=False, index=True)
    filename = Column(Text, nullable=False)
    content_type = Column(Text, nullable=False)
    size = Column(BigInteger, nullable=False)
    path = Column(Text, nullable=True)  # local path or s3 key (nullable in tests)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Processing status
    status = Column(
        String(20), 
        CheckConstraint("status IN ('uploaded','processing','done','failed','deleted','processed','error')"),
        default="uploaded",
        nullable=False
    )
    error = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="documents")
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"

    # Backwards-compat: some tests refer to file_path keyword/attr
    @property
    def file_path(self) -> str:
        return self.path or ""

    @file_path.setter
    def file_path(self, value: str) -> None:
        self.path = value

    # Compatibility attribute mappings for tests
    @property
    def file_size(self) -> int:
        return getattr(self, "size", 0)

    @file_size.setter
    def file_size(self, value: int) -> None:
        self.size = value

    @property
    def file_type(self) -> str:
        return getattr(self, "content_type", "")

    @file_type.setter
    def file_type(self, value: str) -> None:
        self.content_type = value

    @property
    def user_id(self) -> int:
        return getattr(self, "uploaded_by", None)

    @user_id.setter
    def user_id(self, value: int) -> None:
        self.uploaded_by = value


class DocumentChunk(Base):
    """Document chunk model for vector embeddings"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(), ForeignKey("documents.id"), nullable=False, index=True)
    workspace_id = Column(UUID(), nullable=False, index=True)
    chunk_index = Column(BigInteger, nullable=False)
    # Tests expect field name "text" in API, but our ORM uses content internally in service
    text = Column(Text, nullable=False)
    chunk_metadata = Column(JSON, nullable=True)  # {page: n, char_range: [s,e]}
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"
