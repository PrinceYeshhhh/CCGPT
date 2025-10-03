"""
Document service for file processing and management
"""

import uuid
import os
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
import structlog

from app.core.config import settings
from app.core.queue import get_ingest_queue
from app.models.document import Document, DocumentChunk
from app.utils.storage import get_storage_adapter
from app.services.file_security import file_security_service
from app.utils.file_parser import extract_text_from_file

logger = structlog.get_logger()


class DocumentService:
    """Document service for database operations and file processing"""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage = get_storage_adapter()
        self.queue = get_ingest_queue()
    
    async def upload_document(
        self,
        file: UploadFile,
        workspace_id: str,
        uploaded_by: str
    ) -> Document:
        """Upload a document and enqueue processing job"""
        
        # Comprehensive file security validation
        is_valid, error_message = await file_security_service.validate_file(file)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed: {error_message}"
            )
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Get file content
        file_content = await file.read()
        
        # Save file to storage
        file_path, file_size = await self.storage.save_file(
            file_content=file_content,
            workspace_id=workspace_id,
            document_id=document_id,
            filename=file.filename
        )
        
        # Create document record
        document = Document(
            id=document_id,
            workspace_id=workspace_id,
            filename=file.filename,
            content_type=file.content_type,
            size=file_size,
            path=file_path,
            uploaded_by=uploaded_by,
            status="uploaded"
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        # Enqueue processing job
        job = self.queue.enqueue(
            'app.worker.ingest_worker.process_document',
            document_id,
            job_timeout='10m'
        )
        
        logger.info(
            "Document uploaded and job enqueued",
            document_id=document_id,
            workspace_id=workspace_id,
            job_id=job.id,
            filename=file.filename
        )
        
        return document, job.id
    
    def get_document(
        self, 
        document_id: str, 
        workspace_id: str
    ) -> Optional[Document]:
        """Get document by ID within workspace"""
        return self.db.query(Document).filter(
            Document.id == document_id,
            Document.workspace_id == workspace_id
        ).first()
    
    def get_document_chunks(
        self,
        document_id: str,
        workspace_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[DocumentChunk]:
        """Get document chunks with pagination"""
        return self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.workspace_id == workspace_id
        ).offset(offset).limit(limit).all()
    
    def reprocess_document(
        self,
        document_id: str,
        workspace_id: str
    ) -> Optional[str]:
        """Reprocess a document: clear existing chunks and enqueue processing again.
        Returns job_id if enqueued successfully, otherwise None.
        """
        document = self.get_document(document_id, workspace_id)
        if not document:
            return None
        try:
            # Clear previous chunks
            self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.workspace_id == workspace_id
            ).delete(synchronize_session=False)
            self.db.commit()

            # Reset status
            document.status = "uploaded"
            document.error = None
            self.db.commit()

            # Enqueue processing job
            job = self.queue.enqueue(
                'app.worker.ingest_worker.process_document',
                document_id,
                job_timeout='10m'
            )

            logger.info(
                "Document reprocess enqueued",
                document_id=document_id,
                workspace_id=workspace_id,
                job_id=job.id,
                filename=document.filename
            )
            return job.id
        except Exception as e:
            logger.error("Failed to reprocess document", error=str(e), document_id=document_id, workspace_id=workspace_id)
            self.db.rollback()
            return None
    
    def soft_delete_document(
        self, 
        document_id: str, 
        workspace_id: str
    ) -> bool:
        """Soft delete and clean up a document: mark deleted, remove chunks, delete file, and schedule vector cleanup."""
        document = self.get_document(document_id, workspace_id)
        if not document:
            return False
        try:
            # Mark deleted
            document.status = "deleted"
            self.db.commit()

            # Delete chunks from DB
            self.db.query(DocumentChunk).filter(
                DocumentChunk.document_id == document_id,
                DocumentChunk.workspace_id == workspace_id
            ).delete(synchronize_session=False)
            self.db.commit()

            # Delete file from storage using adapter
            try:
                await self.storage.delete_file(document.path)
            except Exception:
                pass

            # Vector deletion (if using vector DB)
            try:
                from app.services.vector_service import VectorService
                VectorService().delete_document(document_id=document_id, workspace_id=workspace_id)
            except Exception:
                pass

            logger.info(
                "Document soft deleted and cleaned",
                document_id=document_id,
                workspace_id=workspace_id
            )
            return True
        except Exception as e:
            logger.error("Failed to delete document", error=str(e), document_id=document_id, workspace_id=workspace_id)
            self.db.rollback()
            return False
    
    def get_workspace_documents(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0,
        status_filter: Optional[str] = None
    ) -> List[Document]:
        """Get documents for a workspace"""
        query = self.db.query(Document).filter(
            Document.workspace_id == workspace_id
        )
        
        if status_filter:
            query = query.filter(Document.status == status_filter)
        
        return query.offset(offset).limit(limit).all()
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        # Check file size
        file_content = file.file.read()
        file.file.seek(0)  # Reset file pointer
        
        max_size = getattr(settings, 'MAX_FILE_SIZE', None) or getattr(settings, 'MAX_UPLOAD_SIZE_BYTES', 10 * 1024 * 1024)
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {max_size} bytes"
            )
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_FILE_TYPES)}"
            )
        
        # Check content type
        if file.content_type not in self._get_allowed_content_types():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid content type"
            )
    
    def _get_allowed_content_types(self) -> List[str]:
        """Get allowed content types"""
        return [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/markdown",
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ]
