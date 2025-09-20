"""
Vector search schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class VectorSearchRequest(BaseModel):
    """Request schema for vector search"""
    query: str = Field(..., description="Search query text", min_length=1, max_length=1000)
    top_k: Optional[int] = Field(5, description="Number of results to return", ge=1, le=50)
    document_ids: Optional[List[int]] = Field(None, description="Filter by specific document IDs")


class VectorSearchResult(BaseModel):
    """Individual search result"""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: Optional[int] = Field(None, description="Document ID")
    text: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Similarity score", ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class VectorSearchResponse(BaseModel):
    """Response schema for vector search"""
    query: str = Field(..., description="Original search query")
    results: List[VectorSearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")


class VectorCacheStats(BaseModel):
    """Vector cache statistics"""
    cache_enabled: bool = Field(..., description="Whether caching is enabled")
    total_cached_queries: int = Field(0, description="Number of cached queries")
    cache_ttl_seconds: int = Field(900, description="Cache TTL in seconds")


class VectorCollectionStats(BaseModel):
    """Vector collection statistics"""
    total_chunks: int = Field(..., description="Total number of chunks in collection")
    collection_name: str = Field(..., description="Collection name")


class VectorEmbeddingStats(BaseModel):
    """Embedding service statistics"""
    model_name: str = Field(..., description="Embedding model name")
    embedding_dimension: int = Field(..., description="Embedding dimension")
    model_loaded: bool = Field(..., description="Whether model is loaded")


class VectorStatsResponse(BaseModel):
    """Complete vector statistics response"""
    collection: VectorCollectionStats = Field(..., description="Collection statistics")
    cache: VectorCacheStats = Field(..., description="Cache statistics")
    embeddings: VectorEmbeddingStats = Field(..., description="Embedding statistics")
