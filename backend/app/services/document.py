"""
Document service for file processing and management
"""

import os
import hashlib
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import UploadFile
import structlog

from sqlalchemy.sql import func
from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.services.file_processor import FileProcessor
from app.services.vector_service import VectorService
from app.services.semantic_chunking_service import semantic_chunking_service, ChunkingStrategy

logger = structlog.get_logger()


class DocumentService:
    """Document service for database operations and file processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_processor = FileProcessor()
        self.vector_service = VectorService()
    
    async def upload_document(
        self,
        file: UploadFile,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Document:
        """Upload and process a document"""
        
        # Validate file
        if not self._validate_file(file):
            raise ValueError("Invalid file type or size")
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        # Ensure upload directory exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create document record
        document = Document(
            user_id=user_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_type=file_extension,
            file_size=len(content),
            file_path=file_path,
            title=title or file.filename,
            description=description,
            tags=tags or [],
            status="uploaded"
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Process document asynchronously
        try:
            await self._process_document(document)
        except Exception as e:
            logger.error(
                "Document processing failed",
                error=str(e),
                document_id=document.id,
                filename=document.filename
            )
            document.status = "error"
            document.processing_error = str(e)
            self.db.commit()
        
        return document
    
    async def _process_document(self, document: Document):
        """Process document and create chunks"""
        try:
            document.status = "processing"
            self.db.commit()
            
            # Extract text from file
            text_content = await self.file_processor.extract_text(document.file_path, document.file_type)
            
            # Create chunks using semantic chunking
            chunking_strategy = ChunkingStrategy.SEMANTIC  # Default to semantic chunking
            chunks = semantic_chunking_service.chunk_text(
                text=text_content,
                strategy=chunking_strategy,
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # Convert Chunk objects to dict format expected by the rest of the system
            chunk_dicts = []
            for chunk in chunks:
                chunk_dicts.append({
                    "index": chunk.chunk_index,
                    "content": chunk.content,
                    "hash": chunk.metadata.get("content_hash", ""),
                    "word_count": chunk.metadata.get("word_count", 0),
                    "section_title": chunk.metadata.get("section_title", ""),
                    "importance_score": chunk.importance_score,
                    "metadata": chunk.metadata
                })
            
            chunks = chunk_dicts
            
            # Save chunks to database
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_data["index"],
                    content=chunk_data["content"],
                    content_hash=chunk_data["hash"],
                    page_number=chunk_data.get("page_number"),
                    section_title=chunk_data.get("section_title"),
                    word_count=chunk_data.get("word_count")
                )
                self.db.add(chunk)
            
            self.db.commit()
            
            # Generate embeddings and store in vector database
            await self.vector_service.add_document_chunks(
                document_id=document.id, 
                chunks=chunks, 
                workspace_id=str(document.workspace_id)
            )
            
            # Update document status
            document.status = "processed"
            document.processed_at = func.now()
            self.db.commit()
            
            logger.info(
                "Document processed successfully",
                document_id=document.id,
                chunks_created=len(chunks)
            )
            
        except Exception as e:
            logger.error(
                "Document processing failed",
                error=str(e),
                document_id=document.id
            )
            document.status = "error"
            document.processing_error = str(e)
            self.db.commit()
            raise
    
    def _validate_file(self, file: UploadFile) -> bool:
        """Validate uploaded file"""
        if not file.filename:
            return False
        
        # Check file extension
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_EXTENSIONS:
            return False
        
        # Check file size (will be validated when reading content)
        return True
    
    def get_user_documents(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[Document]:
        """Get user's documents"""
        query = self.db.query(Document).filter(Document.user_id == user_id)
        
        if status:
            query = query.filter(Document.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def get_document_by_id(self, document_id: int, user_id: int) -> Optional[Document]:
        """Get document by ID for specific user"""
        return self.db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == user_id
        ).first()
    
    def update_document(
        self,
        document_id: int,
        user_id: int,
        update_data: dict
    ) -> Optional[Document]:
        """Update document metadata"""
        document = self.get_document_by_id(document_id, user_id)
        if not document:
            return None
        
        for field, value in update_data.items():
            if hasattr(document, field) and value is not None:
                setattr(document, field, value)
        
        self.db.commit()
        self.db.refresh(document)
        return document
    
    def delete_document(self, document_id: int, user_id: int) -> bool:
        """Delete document and associated data"""
        document = self.get_document_by_id(document_id, user_id)
        if not document:
            return False
        
        try:
            # Delete from vector database
            self.vector_service.delete_document(document_id)
            
            # Delete file from filesystem
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete from database (cascade will handle chunks)
            self.db.delete(document)
            self.db.commit()
            
            logger.info(
                "Document deleted successfully",
                document_id=document_id,
                user_id=user_id
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to delete document",
                error=str(e),
                document_id=document_id,
                user_id=user_id
            )
            self.db.rollback()
            return False
    
    def reprocess_document(self, document_id: int, user_id: int) -> bool:
        """Reprocess a document"""
        document = self.get_document_by_id(document_id, user_id)
        if not document:
            return False
        
        try:
            # Delete existing chunks
            self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id
            ).delete()
            
            # Delete from vector database
            self.vector_service.delete_document(document_id)
            
            # Reset document status
            document.status = "uploaded"
            document.processing_error = None
            self.db.commit()
            
            # Process document again
            import asyncio
            asyncio.create_task(self._process_document(document))
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to reprocess document",
                error=str(e),
                document_id=document_id,
                user_id=user_id
            )
            return False
