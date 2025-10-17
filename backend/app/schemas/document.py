"""
Document Pydantic schemas
"""

from pydantic import BaseModel, ConfigDict, Field
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
    path: Optional[str] = ""
    uploaded_by: Optional[str | int] = None
    status: str
    error: Optional[str] = None
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    """Document chunk response schema"""
    id: uuid.UUID
    document_id: uuid.UUID
    workspace_id: uuid.UUID
    chunk_index: int
    text: str
    # Map model's chunk_metadata field to "metadata" in API responses
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="chunk_metadata")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentWithChunks(DocumentResponse):
    """Document with chunks schema"""
    chunks: List[DocumentChunkResponse] = []


class DocumentListResponse(BaseModel):
    """Envelope for documents list used by endpoints"""
    documents: List[DocumentResponse]
    
    model_config = ConfigDict(from_attributes=True)


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
    progress: Optional[int] = None
    phase: Optional[str] = None
