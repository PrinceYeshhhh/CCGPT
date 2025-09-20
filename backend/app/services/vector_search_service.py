"""
Vector search service with Redis caching for similarity search
"""

import json
import hashlib
import asyncio
from typing import List, Dict, Any, Optional
import redis.asyncio as aioredis
import structlog

from app.core.config import settings
from app.services.embeddings_service import embeddings_service

logger = structlog.get_logger()


class VectorSearchService:
    """Vector search service with Redis caching"""
    
    def __init__(self):
        self.redis_client = None
        self.cache_ttl = 900  # 15 minutes default TTL
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client"""
        try:
            self.redis_client = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
            logger.info("Vector search service initialized with Redis caching")
        except Exception as e:
            logger.error("Failed to initialize Redis client", error=str(e))
            # Continue without caching
            self.redis_client = None
    
    def _generate_cache_key(self, workspace_id: str, query: str, limit: int) -> str:
        """Generate cache key for vector search query"""
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()[:16]
        return f"vector_search:{workspace_id}:{query_hash}:{limit}"
    
    async def _get_cached_results(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results from Redis"""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                results = json.loads(cached_data)
                logger.info("Cache hit for vector search", cache_key=cache_key)
                return results
        except Exception as e:
            logger.warning("Failed to get cached results", error=str(e))
        
        return None
    
    async def _cache_results(
        self, 
        cache_key: str, 
        results: List[Dict[str, Any]]
    ) -> None:
        """Cache search results in Redis"""
        if not self.redis_client:
            return
        
        try:
            await self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(results, default=str)
            )
            logger.info("Results cached successfully", cache_key=cache_key)
        except Exception as e:
            logger.warning("Failed to cache results", error=str(e))
    
    async def vector_search(
        self,
        workspace_id: str,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[int]] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search with Redis caching
        
        Args:
            workspace_id: Workspace identifier for isolation
            query: Search query text
            top_k: Number of top results to return
            document_ids: Optional list of document IDs to filter by
            use_cache: Whether to use Redis caching
        
        Returns:
            List of search results with chunk_id, score, text, and metadata
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(workspace_id, query, top_k)
            
            # Check cache first
            if use_cache:
                cached_results = await self._get_cached_results(cache_key)
                if cached_results is not None:
                    return cached_results
            
            # Generate query embedding
            query_embedding = await embeddings_service.generate_single_embedding(query)
            
            # Perform vector search (this would be implemented by the vector service)
            # For now, we'll return a placeholder that the vector service will implement
            search_results = await self._perform_vector_search(
                workspace_id=workspace_id,
                query_embedding=query_embedding,
                top_k=top_k,
                document_ids=document_ids
            )
            
            # Cache results
            if use_cache and search_results:
                await self._cache_results(cache_key, search_results)
            
            logger.info(
                "Vector search completed",
                workspace_id=workspace_id,
                query=query[:100],
                results_count=len(search_results),
                cached=use_cache
            )
            
            return search_results
            
        except Exception as e:
            logger.error(
                "Vector search failed",
                error=str(e),
                workspace_id=workspace_id,
                query=query[:100]
            )
            raise
    
    async def _perform_vector_search(
        self,
        workspace_id: str,
        query_embedding: List[float],
        top_k: int,
        document_ids: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform the actual vector search using ChromaDB
        This method will be called by the updated vector service
        """
        # This method is called by the vector service when performing actual searches
        # The vector service handles the ChromaDB interaction
        return []
    
    async def clear_cache(self, workspace_id: Optional[str] = None) -> bool:
        """Clear vector search cache for a workspace or all workspaces"""
        if not self.redis_client:
            return False
        
        try:
            if workspace_id:
                pattern = f"vector_search:{workspace_id}:*"
            else:
                pattern = "vector_search:*"
            
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(
                    "Cache cleared",
                    workspace_id=workspace_id,
                    keys_deleted=len(keys)
                )
            
            return True
            
        except Exception as e:
            logger.error("Failed to clear cache", error=str(e))
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.redis_client:
            return {"cache_enabled": False}
        
        try:
            keys = await self.redis_client.keys("vector_search:*")
            return {
                "cache_enabled": True,
                "total_cached_queries": len(keys),
                "cache_ttl_seconds": self.cache_ttl
            }
        except Exception as e:
            logger.error("Failed to get cache stats", error=str(e))
            return {"cache_enabled": False, "error": str(e)}
    
    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL in seconds"""
        self.cache_ttl = ttl_seconds
        logger.info("Cache TTL updated", ttl_seconds=ttl_seconds)
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Vector search service closed")


# Global instance
vector_search_service = VectorSearchService()

