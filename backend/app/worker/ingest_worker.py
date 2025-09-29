"""
Background worker for document processing
"""

import uuid
from typing import List, Dict, Any
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import structlog

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.utils.file_parser import extract_text_from_file
from app.utils.chunker import chunk_text, create_chunk_metadata
from app.utils.storage import get_storage_adapter
from app.services.vector_service import VectorService

logger = structlog.get_logger()

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def process_document(document_id: str) -> Dict[str, Any]:
    """
    Process a document: extract text, chunk it, and save chunks to database
    
    Args:
        document_id: UUID of the document to process
        
    Returns:
        Dict with processing results
    """
    db = SessionLocal()
    storage = get_storage_adapter()
    vector = VectorService()
    
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        logger.info(
            "Starting document processing",
            document_id=document_id,
            workspace_id=document.workspace_id,
            filename=document.filename
        )
        
        # Update status to processing
        document.status = "processing"
        document.error = None
        db.commit()
        
        # Read file content
        file_content = storage.get_file(document.path)
        
        # Extract text blocks with metadata
        text_blocks = extract_text_from_file(document.path, document.content_type)
        
        if not text_blocks:
            raise ValueError("No text could be extracted from the document")
        
        # Process each text block
        all_chunks = []
        processed = 0
        total_blocks = len(text_blocks)
        for block_text, block_metadata in text_blocks:
            # Chunk the text block
            chunks = chunk_text(block_text)
            
            # Create chunk metadata
            for i, chunk_text_content in enumerate(chunks):
                chunk_metadata = create_chunk_metadata(
                    chunk_text_content, 
                    len(all_chunks) + i, 
                    block_metadata
                )
                all_chunks.append((chunk_text_content, chunk_metadata))
            processed += 1
            # Optional: store progress in document.error as JSON or in a side-channel (skipping DB writes for perf)
        
        # Save chunks to database
        chunk_objects = []
        for chunk_text_content, chunk_metadata in all_chunks:
            chunk = DocumentChunk(
                document_id=document.id,
                workspace_id=document.workspace_id,
                chunk_index=chunk_metadata["chunk_index"],
                text=chunk_text_content,
                metadata=chunk_metadata
            )
            chunk_objects.append(chunk)
        
        # Bulk insert chunks
        db.bulk_save_objects(chunk_objects)
        db.commit()
        
        # Index embeddings in vector database
        try:
            raw_chunks = []
            for c in chunk_objects:
                raw_chunks.append({
                    "chunk_id": str(c.id),
                    "text": c.text,
                    "metadata": {
                        "document_id": str(document.id),
                        "workspace_id": str(document.workspace_id),
                        "chunk_index": c.chunk_index,
                        **(c.metadata or {})
                    }
                })
            # Note: VectorService.add_document_chunks expects document_id and workspace_id as strings
            import asyncio
            asyncio.run(vector.add_document_chunks(document_id=str(document.id), chunks=raw_chunks, workspace_id=str(document.workspace_id)))
        except Exception as e:
            logger.error("Vector indexing failed", error=str(e), document_id=document_id)
        
        # Update document status to done
        document.status = "done"
        db.commit()
        
        logger.info(
            "Document processing completed successfully",
            document_id=document_id,
            workspace_id=document.workspace_id,
            chunks_created=len(all_chunks)
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_created": len(all_chunks),
            "message": "Document processed successfully",
            "progress": 100,
            "phase": "complete"
        }
        
    except Exception as e:
        logger.error(
            "Document processing failed",
            error=str(e),
            document_id=document_id,
            workspace_id=getattr(document, 'workspace_id', None) if 'document' in locals() else None
        )
        
        # Update document status to failed
        if 'document' in locals():
            document.status = "failed"
            document.error = str(e)
            db.commit()
        
        return {
            "status": "failed",
            "document_id": document_id,
            "error": str(e),
            "message": "Document processing failed",
            "progress": 0,
            "phase": "error"
        }
        
    finally:
        db.close()


def enqueue_embedding_jobs(document_id: str, chunk_ids: List[str]) -> None:
    """
    Enqueue embedding jobs for document chunks
    
    Args:
        document_id: UUID of the document
        chunk_ids: List of chunk UUIDs to embed
    """
    # This will be implemented when embedding service is ready
    logger.info(
        "Embedding jobs would be enqueued here",
        document_id=document_id,
        chunk_count=len(chunk_ids)
    )
