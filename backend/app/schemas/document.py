"""
Document Pydantic schemas
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class DocumentStatus(str, Enum):
    """Document processing status"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    DELETED = "deleted"


class DocumentResponse(BaseModel):
    """Document response schema"""
    id: uuid.UUID
    workspace_id: uuid.UUID
    filename: str
    content_type: str
    size: int
    path: str
    uploaded_by: uuid.UUID
    status: str
    error: Optional[str] = None
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    """Document chunk response schema"""
    id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    chunk_index: int
    text: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentWithChunks(DocumentResponse):
    """Document with chunks schema"""
    chunks: List[DocumentChunkResponse] = []


class FileUploadResponse(BaseModel):
    """File upload response schema"""
    document_id: uuid.UUID
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Job status response schema"""
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
