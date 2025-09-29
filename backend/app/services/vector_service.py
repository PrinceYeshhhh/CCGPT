"""
Vector service for handling embeddings and similarity search
"""

import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import structlog

from app.core.config import settings
from app.services.embeddings_service import embeddings_service
from app.services.vector_search_service import vector_search_service
from app.exceptions import VectorSearchError, DatabaseError, ConfigurationError

logger = structlog.get_logger()


class VectorService:
    """Vector service for managing embeddings and similarity search"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="customercaregpt_documents",
                metadata={"description": "CustomerCareGPT document embeddings"}
            )
            
            logger.info("Vector service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize vector service", error=str(e))
            raise ConfigurationError(
                message="Failed to initialize vector database",
                details={"error": str(e), "persist_directory": settings.CHROMA_PERSIST_DIRECTORY}
            )
    
    async def add_document_chunks(
        self, 
        document_id: int, 
        chunks: List[Dict[str, Any]], 
        workspace_id: str
    ):
        """Add document chunks to vector database with embeddings"""
        try:
            if not chunks:
                return
            
            # Generate embeddings for chunks
            embedded_chunks = await embeddings_service.embed_chunks(
                chunks=chunks,
                workspace_id=workspace_id,
                document_id=document_id
            )
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            embeddings = []
            
            for embedded_chunk in embedded_chunks:
                ids.append(embedded_chunk["chunk_id"])
                documents.append(embedded_chunk["text"])
                metadatas.append(embedded_chunk["metadata"])
                embeddings.append(embedded_chunk["embedding"])
            
            # Add to collection with embeddings
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(
                "Document chunks added to vector database with embeddings",
                document_id=document_id,
                workspace_id=workspace_id,
                chunks_count=len(chunks)
            )
            
        except Exception as e:
            logger.error(
                "Failed to add document chunks to vector database",
                error=str(e),
                document_id=document_id,
                workspace_id=workspace_id
            )
            raise VectorSearchError(
                message="Failed to add document chunks to vector database",
                details={
                    "document_id": document_id,
                    "workspace_id": workspace_id,
                    "chunks_count": len(chunks),
                    "error": str(e)
                }
            )
    
    async def search_similar_chunks(
        self, 
        query: str, 
        workspace_id: str, 
        limit: int = 5,
        document_ids: Optional[List[int]] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity with caching"""
        try:
            # Check cache first if enabled
            if use_cache:
                cache_key = vector_search_service._generate_cache_key(workspace_id, query, limit)
                cached_results = await vector_search_service._get_cached_results(cache_key)
                if cached_results is not None:
                    return cached_results
            
            # Perform the actual vector search
            results = await self._perform_vector_search(
                query=query,
                workspace_id=workspace_id,
                limit=limit,
                document_ids=document_ids
            )
            
            # Cache results if enabled
            if use_cache and results:
                cache_key = vector_search_service._generate_cache_key(workspace_id, query, limit)
                await vector_search_service._cache_results(cache_key, results)
            
            logger.info(
                "Similarity search completed",
                query=query[:100],
                workspace_id=workspace_id,
                results_count=len(results)
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Similarity search failed",
                error=str(e),
                query=query[:100],
                workspace_id=workspace_id
            )
            raise VectorSearchError(
                message="Similarity search failed",
                details={
                    "query": query[:100],
                    "workspace_id": workspace_id,
                    "limit": limit,
                    "error": str(e)
                }
            )
    
    async def _perform_vector_search(
        self,
        query: str,
        workspace_id: str,
        limit: int,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """Perform the actual vector search using ChromaDB"""
        try:
            # Generate query embedding
            query_embedding = await embeddings_service.generate_single_embedding(query)
            
            # Build where clause for workspace isolation
            where_clause = {"workspace_id": workspace_id}
            if document_ids:
                where_clause["document_id"] = {"$in": document_ids}
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            similar_chunks = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                )):
                    similar_chunks.append({
                        "chunk_id": metadata.get("chunk_id", ""),
                        "document_id": metadata.get("document_id"),
                        "text": doc,
                        "content": doc,  # For backward compatibility
                        "metadata": metadata,
                        "similarity_score": 1 - distance,  # Convert distance to similarity
                        "score": 1 - distance,  # Alias for consistency
                        "rank": i + 1
                    })
            
            return similar_chunks
            
        except Exception as e:
            logger.error(
                "Vector search execution failed",
                error=str(e),
                query=query[:100],
                workspace_id=workspace_id
            )
            raise
    
    def delete_document(self, document_id: int, workspace_id: str):
        """Delete all chunks for a document with workspace isolation"""
        try:
            # Get all chunks for this document in the workspace
            results = self.collection.get(
                where={
                    "document_id": document_id,
                    "workspace_id": workspace_id
                },
                include=["metadatas"]
            )
            
            if results["ids"]:
                # Delete chunks
                self.collection.delete(ids=results["ids"])
                
                # Clear related cache entries
                asyncio.create_task(
                    vector_search_service.clear_cache(workspace_id)
                )
                
                logger.info(
                    "Document chunks deleted from vector database",
                    document_id=document_id,
                    workspace_id=workspace_id,
                    chunks_deleted=len(results["ids"])
                )
            
        except Exception as e:
            logger.error(
                "Failed to delete document from vector database",
                error=str(e),
                document_id=document_id,
                workspace_id=workspace_id
            )
            raise
    
    async def vector_search(
        self,
        workspace_id: str,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Main vector search API function
        
        Args:
            workspace_id: Workspace identifier for isolation
            query: Search query text
            top_k: Number of top results to return
        
        Returns:
            List of search results with chunk_id, score, text, and metadata
        """
        try:
            results = await self.search_similar_chunks(
                query=query,
                workspace_id=workspace_id,
                limit=top_k,
                use_cache=True
            )
            
            # Format results for the API
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "chunk_id": result.get("chunk_id", ""),
                    "document_id": result.get("document_id"),
                    "text": result.get("text", ""),
                    "score": result.get("score", 0.0),
                    "metadata": result.get("metadata", {})
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(
                "Vector search API failed",
                error=str(e),
                workspace_id=workspace_id,
                query=query[:100]
            )
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            logger.error("Failed to get collection stats", error=str(e))
            return {"total_chunks": 0, "collection_name": "unknown"}
    
    def reset_collection(self):
        """Reset the entire collection (use with caution)"""
        try:
            self.client.delete_collection("customercaregpt_documents")
            self.collection = self.client.create_collection(
                name="customercaregpt_documents",
                metadata={"description": "CustomerCareGPT document embeddings"}
            )
            logger.info("Collection reset successfully")
        except Exception as e:
            logger.error("Failed to reset collection", error=str(e))
            raise
