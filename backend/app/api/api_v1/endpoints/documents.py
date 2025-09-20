"""
Document management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import structlog
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document, DocumentChunk
from app.schemas.document import (
    DocumentResponse, 
    DocumentWithChunks, 
    DocumentChunkResponse,
    FileUploadResponse,
    JobStatusResponse
)
from app.services.document_service import DocumentService
from app.core.queue import get_ingest_queue

logger = structlog.get_logger()
router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new document"""
    try:
        document_service = DocumentService(db)
        
        # For now, use user ID as workspace ID (can be enhanced later)
        workspace_id = str(current_user.id)
        uploaded_by = str(current_user.id)
        
        # Upload document and enqueue processing
        document, job_id = await document_service.upload_document(
            file=file,
            workspace_id=workspace_id,
            uploaded_by=uploaded_by
        )
        
        logger.info(
            "Document uploaded successfully",
            user_id=current_user.id,
            document_id=document.id,
            filename=document.filename,
            job_id=job_id
        )
        
        return FileUploadResponse(
            document_id=document.id,
            job_id=job_id,
            status=document.status,
            message="Document uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Document upload failed",
            error=str(e),
            user_id=current_user.id,
            filename=file.filename
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's documents"""
    try:
        document_service = DocumentService(db)
        workspace_id = str(current_user.id)
        
        documents = document_service.get_workspace_documents(
            workspace_id=workspace_id,
            limit=limit,
            offset=offset,
            status_filter=status_filter
        )
        
        return [DocumentResponse.from_orm(doc) for doc in documents]
        
    except Exception as e:
        logger.error("Failed to get documents", error=str(e), user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@router.get("/{document_id}", response_model=DocumentWithChunks)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document with its chunks"""
    try:
        document_service = DocumentService(db)
        workspace_id = str(current_user.id)
        
        document = document_service.get_document(
            document_id=document_id,
            workspace_id=workspace_id
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get first few chunks for preview
        chunks = document_service.get_document_chunks(
            document_id=document_id,
            workspace_id=workspace_id,
            limit=5,
            offset=0
        )
        
        document_data = DocumentResponse.from_orm(document)
        chunk_data = [DocumentChunkResponse.from_orm(chunk) for chunk in chunks]
        
        return DocumentWithChunks(
            **document_data.dict(),
            chunks=chunk_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get document",
            error=str(e),
            user_id=current_user.id,
            document_id=document_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
async def get_document_chunks(
    document_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get document chunks with pagination"""
    try:
        document_service = DocumentService(db)
        workspace_id = str(current_user.id)
        
        # Check if document exists and belongs to user
        document = document_service.get_document(document_id, workspace_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        chunks = document_service.get_document_chunks(
            document_id=document_id,
            workspace_id=workspace_id,
            limit=limit,
            offset=offset
        )
        
        return [DocumentChunkResponse.from_orm(chunk) for chunk in chunks]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get document chunks",
            error=str(e),
            user_id=current_user.id,
            document_id=document_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document chunks"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete a document"""
    try:
        document_service = DocumentService(db)
        workspace_id = str(current_user.id)
        
        success = document_service.soft_delete_document(
            document_id=document_id,
            workspace_id=workspace_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        logger.info(
            "Document deleted successfully",
            user_id=current_user.id,
            document_id=document_id
        )
        
        return {"message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete document",
            error=str(e),
            user_id=current_user.id,
            document_id=document_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get job status"""
    try:
        queue = get_ingest_queue()
        job = queue.fetch_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        return JobStatusResponse(
            job_id=job_id,
            status=job.get_status(),
            result=job.result,
            error=str(job.exc_info) if job.exc_info else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get job status",
            error=str(e),
            user_id=current_user.id,
            job_id=job_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )