"""
Enhanced vector search service with batching, caching, and optimization
"""

import asyncio
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
import structlog
from datetime import datetime, timedelta
import chromadb
from chromadb.config import Settings

from app.core.config import settings
from app.utils.cache import vector_search_cache, cache_manager
from app.utils.metrics import MetricsCollector

logger = structlog.get_logger()


class EnhancedVectorService:
    """Enhanced vector search service with batching and caching"""
    
    def __init__(self):
        self.client = None
        self.collections = {}
        self.query_batch = []
        self.batch_size = 10
        self.batch_timeout = 0.1  # 100ms
        self._batch_lock = asyncio.Lock()
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client (safe no-op if unavailable)."""
        try:
            # Allow disabling via environment for local/dev
            import os
            if os.getenv("CHROMA_DISABLED", "false").lower() == "true":
                logger.warning("ChromaDB disabled via CHROMA_DISABLED env var; vector search will be inactive")
                self.client = None
                return

            # Prefer HTTP client if a URL is provided; otherwise skip initialization
            chroma_host = settings.CHROMA_URL.replace("http://", "").replace("https://", "") if settings.CHROMA_URL else None
            if not chroma_host:
                logger.warning("CHROMA_URL not set; vector search will be inactive")
                self.client = None
                return

            self.client = chromadb.HttpClient(
                host=chroma_host,
                port=8001,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            # Do not crash app if Chroma is unavailable; degrade gracefully
            logger.error("Failed to initialize ChromaDB client; vector search disabled", error=str(e))
            self.client = None
    
    async def get_collection(self, workspace_id: str):
        """Get or create collection for workspace"""
        if self.client is None:
            logger.warning("Vector service inactive; returning empty collection for workspace", workspace_id=workspace_id)
            return None

        if workspace_id not in self.collections:
            try:
                collection_name = f"workspace_{workspace_id}"
                self.collections[workspace_id] = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"workspace_id": workspace_id}
                )
                logger.info(f"Collection created/retrieved for workspace {workspace_id}")
            except Exception as e:
                logger.error(f"Failed to get collection for workspace {workspace_id}", error=str(e))
                return None
        
        return self.collections[workspace_id]
    
    async def search_optimized(
        self, 
        workspace_id: str, 
        query: str, 
        top_k: int = 5,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """Optimized vector search with caching and batching"""
        
        # Check cache first
        if use_cache:
            cache_key = f"{workspace_id}:{hashlib.md5(query.encode()).hexdigest()}:{top_k}"
            cached_result = await vector_search_cache.get_search_results(
                workspace_id, query, top_k
            )
            if cached_result:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached_result
        
        # Add to batch for processing
        async with self._batch_lock:
            self.query_batch.append({
                'workspace_id': workspace_id,
                'query': query,
                'top_k': top_k,
                'timestamp': time.time()
            })
            
            # Process batch if it's full or timeout reached
            if len(self.query_batch) >= self.batch_size:
                results = await self._process_batch()
                return results[0]  # Return first result for single query
        
        # Process single query if batch not ready
        result = await self._search_single(workspace_id, query, top_k)
        
        # Cache result
        if use_cache:
            await vector_search_cache.set_search_results(workspace_id, query, top_k, result)
        
        return result
    
    async def _process_batch(self) -> List[List[Dict[str, Any]]]:
        """Process batch of queries"""
        if not self.query_batch:
            return []
        
        batch = self.query_batch.copy()
        self.query_batch.clear()
        
        # Group by workspace for efficient processing
        workspace_queries = {}
        for query_data in batch:
            workspace_id = query_data['workspace_id']
            if workspace_id not in workspace_queries:
                workspace_queries[workspace_id] = []
            workspace_queries[workspace_id].append(query_data)
        
        # Process each workspace batch
        all_results = []
        for workspace_id, queries in workspace_queries.items():
            try:
                collection = await self.get_collection(workspace_id)
                
                # Extract queries and top_k values
                query_texts = [q['query'] for q in queries]
                max_top_k = max(q['top_k'] for q in queries)
                
                # Batch search
                search_results = collection.query(
                    query_texts=query_texts,
                    n_results=max_top_k
                )
                
                # Process results for each query
                for i, query_data in enumerate(queries):
                    top_k = query_data['top_k']
                    result = self._format_search_results(
                        search_results, i, top_k, workspace_id
                    )
                    all_results.append(result)
                    
                    # Cache individual result
                    await vector_search_cache.set_search_results(
                        workspace_id, query_data['query'], top_k, result
                    )
                
            except Exception as e:
                logger.error(f"Batch processing failed for workspace {workspace_id}", error=str(e))
                # Return empty results for failed queries
                for _ in queries:
                    all_results.append([])
        
        return all_results
    
    async def _search_single(
        self, 
        workspace_id: str, 
        query: str, 
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Process single query"""
        start_time = time.time()
        
        try:
            collection = await self.get_collection(workspace_id)
            if collection is None:
                return []

            search_results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            result = self._format_search_results(search_results, 0, top_k, workspace_id)
            
            # Record metrics
            duration = time.time() - start_time
            MetricsCollector.record_vector_search(workspace_id, duration)
            
            return result
            
        except Exception as e:
            logger.error(f"Single search failed for workspace {workspace_id}", error=str(e))
            return []
    
    def _format_search_results(
        self, 
        search_results: Dict, 
        query_index: int, 
        top_k: int,
        workspace_id: str
    ) -> List[Dict[str, Any]]:
        """Format search results"""
        results = []
        
        if not search_results or not search_results.get('documents'):
            return results
        
        documents = search_results['documents'][query_index]
        metadatas = search_results.get('metadatas', [[]])[query_index]
        distances = search_results.get('distances', [[]])[query_index]
        ids = search_results.get('ids', [[]])[query_index]
        
        for i in range(min(len(documents), top_k)):
            result = {
                'id': ids[i] if i < len(ids) else f"chunk_{i}",
                'text': documents[i],
                'metadata': metadatas[i] if i < len(metadatas) else {},
                'similarity_score': 1 - distances[i] if i < len(distances) else 0.0,
                'workspace_id': workspace_id
            }
            results.append(result)
        
        return results
    
    async def add_documents(
        self, 
        workspace_id: str, 
        documents: List[str], 
        metadatas: List[Dict[str, Any]], 
        ids: List[str]
    ) -> bool:
        """Add documents to collection"""
        try:
            collection = await self.get_collection(workspace_id)
            if collection is None:
                return True
            
            # Batch add documents
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i + batch_size]
                batch_metadatas = metadatas[i:i + batch_size]
                batch_ids = ids[i:i + batch_size]
                
                collection.add(
                    documents=batch_docs,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
            
            # Invalidate cache for this workspace
            await vector_search_cache.invalidate_workspace(workspace_id)
            
            logger.info(f"Added {len(documents)} documents to workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add documents to workspace {workspace_id}", error=str(e))
            return False
    
    async def delete_documents(
        self, 
        workspace_id: str, 
        document_ids: List[str]
    ) -> bool:
        """Delete documents from collection"""
        try:
            collection = await self.get_collection(workspace_id)
            if collection is None:
                return True
            collection.delete(ids=document_ids)
            
            # Invalidate cache for this workspace
            await vector_search_cache.invalidate_workspace(workspace_id)
            
            logger.info(f"Deleted {len(document_ids)} documents from workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete documents from workspace {workspace_id}", error=str(e))
            return False
    
    async def get_collection_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            collection = await self.get_collection(workspace_id)
            if collection is None:
                return {'workspace_id': workspace_id, 'document_count': 0}
            count = collection.count()
            
            return {
                'workspace_id': workspace_id,
                'document_count': count,
                'collection_name': collection.name
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats for workspace {workspace_id}", error=str(e))
            return {'workspace_id': workspace_id, 'document_count': 0, 'error': str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check vector service health"""
        try:
            # Test connection
            if self.client is None:
                return {
                    'status': 'inactive',
                    'collections_count': 0,
                    'timestamp': datetime.utcnow().isoformat()
                }

            collections = self.client.list_collections()
            
            return {
                'status': 'healthy',
                'collections_count': len(collections),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Vector service health check failed", error=str(e))
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global instance
enhanced_vector_service = EnhancedVectorService()
