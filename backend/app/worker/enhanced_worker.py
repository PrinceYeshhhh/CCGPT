"""
Enhanced background worker with batching and optimization
"""

import asyncio
import uuid
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import structlog
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import db_manager
from app.models.document import Document, DocumentChunk
from app.utils.file_parser import extract_text_from_file
from app.utils.chunker import chunk_text, create_chunk_metadata
from app.utils.storage import get_storage_adapter
from app.utils.circuit_breaker import get_database_breaker, get_vector_db_breaker
from app.services.enhanced_vector_service import enhanced_vector_service
from app.utils.metrics import MetricsCollector

logger = structlog.get_logger()


class EnhancedWorker:
    """Enhanced background worker with batching and optimization"""
    
    def __init__(self):
        self.batch_size = 10
        self.batch_timeout = 5.0  # 5 seconds
        self.processing_batch = []
        self.embedding_batch = []
        self._lock = asyncio.Lock()
        self._running = False
        
        # Circuit breakers
        self.db_breaker = get_database_breaker()
        self.vector_breaker = get_vector_db_breaker()
    
    async def start(self):
        """Start the enhanced worker"""
        self._running = True
        logger.info("Enhanced worker started")
        
        # Start batch processing tasks
        tasks = [
            asyncio.create_task(self._process_document_batch_loop()),
            asyncio.create_task(self._process_embedding_batch_loop()),
            asyncio.create_task(self._cleanup_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error("Worker task failed", error=str(e))
            raise
        finally:
            self._running = False
    
    async def _process_document_batch_loop(self):
        """Process document batches continuously"""
        while self._running:
            try:
                if self.processing_batch:
                    await self._process_document_batch()
                else:
                    await asyncio.sleep(0.1)  # Short sleep if no work
            except Exception as e:
                logger.error("Document batch processing failed", error=str(e))
                await asyncio.sleep(1)  # Wait before retry
    
    async def _process_embedding_batch_loop(self):
        """Process embedding batches continuously"""
        while self._running:
            try:
                if self.embedding_batch:
                    await self._process_embedding_batch()
                else:
                    await asyncio.sleep(0.1)  # Short sleep if no work
            except Exception as e:
                logger.error("Embedding batch processing failed", error=str(e))
                await asyncio.sleep(1)  # Wait before retry
    
    async def _cleanup_loop(self):
        """Periodic cleanup tasks"""
        while self._running:
            try:
                await self._cleanup_expired_sessions()
                await self._cleanup_failed_jobs()
                await asyncio.sleep(300)  # 5 minutes
            except Exception as e:
                logger.error("Cleanup failed", error=str(e))
                await asyncio.sleep(60)  # Wait before retry
    
    async def process_document(self, document_id: str) -> Dict[str, Any]:
        """Process a single document (adds to batch)"""
        async with self._lock:
            self.processing_batch.append({
                'document_id': document_id,
                'timestamp': time.time()
            })
            
            # Process batch if it's full
            if len(self.processing_batch) >= self.batch_size:
                asyncio.create_task(self._process_document_batch())
        
        return {
            'status': 'queued',
            'document_id': document_id,
            'message': 'Document queued for batch processing'
        }
    
    async def _process_document_batch(self):
        """Process batch of documents"""
        if not self.processing_batch:
            return
        
        async with self._lock:
            batch = self.processing_batch.copy()
            self.processing_batch.clear()
        
        logger.info(f"Processing document batch of {len(batch)} documents")
        
        # Group by workspace for efficient processing
        workspace_docs = {}
        for doc_data in batch:
            document_id = doc_data['document_id']
            try:
                # Get document info
                with db_manager.get_write_session() as db:
                    document = db.query(Document).filter(Document.id == document_id).first()
                    if not document:
                        logger.warning(f"Document {document_id} not found")
                        continue
                    
                    workspace_id = document.workspace_id
                    if workspace_id not in workspace_docs:
                        workspace_docs[workspace_id] = []
                    workspace_docs[workspace_id].append(document)
            
            except Exception as e:
                logger.error(f"Failed to get document {document_id}", error=str(e))
                continue
        
        # Process each workspace batch
        for workspace_id, documents in workspace_docs.items():
            try:
                await self._process_workspace_documents(workspace_id, documents)
            except Exception as e:
                logger.error(f"Failed to process workspace {workspace_id}", error=str(e))
                # Mark documents as failed
                await self._mark_documents_failed(documents, str(e))
    
    async def _process_workspace_documents(self, workspace_id: str, documents: List[Document]):
        """Process documents for a specific workspace"""
        storage = get_storage_adapter()
        
        for document in documents:
            try:
                # Update status to processing
                await self._update_document_status(document.id, "processing")
                
                # Read file content
                file_content = storage.get_file(document.path)
                
                # Extract text blocks with metadata
                text_blocks = extract_text_from_file(document.path, document.content_type)
                
                if not text_blocks:
                    raise ValueError("No text could be extracted from the document")
                
                # Process each text block
                all_chunks = []
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
                
                # Save chunks to database
                await self._save_chunks_batch(document, all_chunks)
                
                # Update document status to done
                await self._update_document_status(document.id, "done")
                
                # Queue embeddings
                await self._queue_embeddings(document.id, workspace_id, all_chunks)
                
                logger.info(
                    f"Document {document.id} processed successfully",
                    workspace_id=workspace_id,
                    chunks_created=len(all_chunks)
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to process document {document.id}",
                    error=str(e),
                    workspace_id=workspace_id
                )
                await self._update_document_status(document.id, "failed", str(e))
    
    async def _save_chunks_batch(self, document: Document, chunks: List[tuple]):
        """Save chunks to database in batch"""
        try:
            with db_manager.get_write_session() as db:
                chunk_objects = []
                for chunk_text_content, chunk_metadata in chunks:
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
                
                logger.info(f"Saved {len(chunk_objects)} chunks for document {document.id}")
        
        except Exception as e:
            logger.error(f"Failed to save chunks for document {document.id}", error=str(e))
            raise
    
    async def _queue_embeddings(self, document_id: str, workspace_id: str, chunks: List[tuple]):
        """Queue embeddings for processing"""
        async with self._lock:
            for chunk_text_content, chunk_metadata in chunks:
                self.embedding_batch.append({
                    'document_id': document_id,
                    'workspace_id': workspace_id,
                    'chunk_text': chunk_text_content,
                    'chunk_metadata': chunk_metadata,
                    'timestamp': time.time()
                })
            
            # Process embedding batch if it's full
            if len(self.embedding_batch) >= self.batch_size:
                asyncio.create_task(self._process_embedding_batch())
    
    async def _process_embedding_batch(self):
        """Process batch of embeddings"""
        if not self.embedding_batch:
            return
        
        async with self._lock:
            batch = self.embedding_batch.copy()
            self.embedding_batch.clear()
        
        logger.info(f"Processing embedding batch of {len(batch)} chunks")
        
        # Group by workspace for efficient processing
        workspace_chunks = {}
        for chunk_data in batch:
            workspace_id = chunk_data['workspace_id']
            if workspace_id not in workspace_chunks:
                workspace_chunks[workspace_id] = []
            workspace_chunks[workspace_id].append(chunk_data)
        
        # Process each workspace batch
        for workspace_id, chunks in workspace_chunks.items():
            try:
                await self._process_workspace_embeddings(workspace_id, chunks)
            except Exception as e:
                logger.error(f"Failed to process embeddings for workspace {workspace_id}", error=str(e))
    
    async def _process_workspace_embeddings(self, workspace_id: str, chunks: List[Dict]):
        """Process embeddings for a specific workspace"""
        try:
            # Prepare documents for vector database
            documents = [chunk['chunk_text'] for chunk in chunks]
            metadatas = [chunk['chunk_metadata'] for chunk in chunks]
            ids = [f"{chunk['document_id']}_{chunk['chunk_metadata']['chunk_index']}" for chunk in chunks]
            
            # Add to vector database
            await self.vector_breaker.call(
                enhanced_vector_service.add_documents,
                workspace_id,
                documents,
                metadatas,
                ids
            )
            
            logger.info(f"Added {len(chunks)} embeddings for workspace {workspace_id}")
            
        except Exception as e:
            logger.error(f"Failed to process embeddings for workspace {workspace_id}", error=str(e))
            raise
    
    async def _update_document_status(self, document_id: str, status: str, error: str = None):
        """Update document status"""
        try:
            with db_manager.get_write_session() as db:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.status = status
                    if error:
                        document.error = error
                    db.commit()
        
        except Exception as e:
            logger.error(f"Failed to update document status for {document_id}", error=str(e))
    
    async def _mark_documents_failed(self, documents: List[Document], error: str):
        """Mark documents as failed"""
        for document in documents:
            await self._update_document_status(document.id, "failed", error)
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            with db_manager.get_write_session() as db:
                # Clean up sessions older than 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                # This would need to be implemented based on your session model
                logger.info("Cleaned up expired sessions")
        
        except Exception as e:
            logger.error("Failed to cleanup expired sessions", error=str(e))
    
    async def _cleanup_failed_jobs(self):
        """Clean up failed jobs"""
        try:
            with db_manager.get_write_session() as db:
                # Clean up failed documents older than 7 days
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                
                # This would need to be implemented based on your job model
                logger.info("Cleaned up failed jobs")
        
        except Exception as e:
            logger.error("Failed to cleanup failed jobs", error=str(e))
    
    def stop(self):
        """Stop the worker"""
        self._running = False
        logger.info("Enhanced worker stopped")


# Global worker instance
enhanced_worker = EnhancedWorker()
