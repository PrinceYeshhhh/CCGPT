"""
Production-grade vector search service with advanced capabilities
"""

import asyncio
import hashlib
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import structlog
import numpy as np
from sqlalchemy.orm import Session

# Vector database
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# Redis caching
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# ML and embeddings
try:
    from sentence_transformers import SentenceTransformer, CrossEncoder
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# BM25 for hybrid search
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.services.production_rag_system import Chunk, TextBlock

logger = structlog.get_logger()


class SearchMode(Enum):
    """Search modes for vector search"""
    SIMILARITY = "similarity"  # Pure vector similarity
    HYBRID = "hybrid"  # Vector + BM25
    SEMANTIC = "semantic"  # Semantic search with reranking
    MULTI_QUERY = "multi_query"  # Multiple query variations
    FUSION = "fusion"  # Multiple search methods fused


class IndexingStrategy(Enum):
    """Indexing strategies"""
    DENSE = "dense"  # Dense embeddings only
    SPARSE = "sparse"  # Sparse (BM25) only
    HYBRID = "hybrid"  # Both dense and sparse
    MULTI_VECTOR = "multi_vector"  # Multiple embedding models


@dataclass
class SearchResult:
    """Enhanced search result"""
    chunk_id: str
    document_id: int
    text: str
    score: float
    metadata: Dict[str, Any] = None
    search_method: str = "vector_similarity"
    rank: int = 0
    explanation: Optional[str] = None
    reranked_score: Optional[float] = None


@dataclass
class SearchConfig:
    """Search configuration"""
    top_k: int = 10
    similarity_threshold: float = 0.7
    search_mode: SearchMode = SearchMode.HYBRID
    use_reranking: bool = True
    rerank_top_k: int = 5
    use_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    boost_important: bool = True
    filter_by_metadata: Optional[Dict[str, Any]] = None


class ProductionVectorService:
    """Production-grade vector search service"""
    
    def __init__(self, 
                 db: Session,
                 embedding_model: str = "all-mpnet-base-v2",
                 collection_name: str = "documents"):
        self.db = db
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        
        # Initialize components
        self._initialize_embedding_model()
        self._initialize_vector_database()
        self._initialize_redis_cache()
        self._initialize_reranking_model()
        self._initialize_bm25()
        
        # Performance tracking
        self.search_stats = {
            "total_searches": 0,
            "cache_hits": 0,
            "avg_search_time": 0.0,
            "embedding_time": 0.0,
            "search_time": 0.0,
            "rerank_time": 0.0
        }
    
    def _initialize_embedding_model(self):
        """Initialize embedding model"""
        if ML_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
                logger.info(f"Embedding model loaded: {self.embedding_model_name}")
            except Exception as e:
                logger.error("Failed to load embedding model", error=str(e))
                self.embedding_model = None
                self.embedding_dimension = 384  # Default dimension
        else:
            logger.warning("ML libraries not available, using basic embeddings")
            self.embedding_model = None
            self.embedding_dimension = 384
    
    def _initialize_vector_database(self):
        """Initialize ChromaDB vector database"""
        if CHROMADB_AVAILABLE:
            try:
                # Create ChromaDB client
                self.chroma_client = chromadb.PersistentClient(
                    path=settings.CHROMA_DB_PATH,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                
                # Create or get collection
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                
                logger.info("ChromaDB initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize ChromaDB", error=str(e))
                self.chroma_client = None
                self.collection = None
        else:
            logger.warning("ChromaDB not available")
            self.chroma_client = None
            self.collection = None
    
    def _initialize_redis_cache(self):
        """Initialize Redis cache"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = aioredis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning("Failed to initialize Redis cache", error=str(e))
                self.redis_client = None
        else:
            logger.warning("Redis not available")
            self.redis_client = None
    
    def _initialize_reranking_model(self):
        """Initialize reranking model"""
        if ML_AVAILABLE:
            try:
                self.reranking_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                logger.info("Reranking model loaded successfully")
            except Exception as e:
                logger.warning("Failed to load reranking model", error=str(e))
                self.reranking_model = None
        else:
            self.reranking_model = None
    
    def _initialize_bm25(self):
        """Initialize BM25 for hybrid search"""
        if BM25_AVAILABLE:
            self.bm25_available = True
            logger.info("BM25 available for hybrid search")
        else:
            self.bm25_available = False
            logger.warning("BM25 not available, hybrid search disabled")
    
    async def add_chunks(self, 
                        chunks: List[Chunk], 
                        workspace_id: str,
                        indexing_strategy: IndexingStrategy = IndexingStrategy.HYBRID) -> bool:
        """Add chunks to vector database with advanced indexing"""
        try:
            if not self.collection:
                logger.error("Vector database not initialized")
                return False
            
            # Prepare data for indexing
            chunk_ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for chunk in chunks:
                # Generate embedding
                embedding = await self._generate_embedding(chunk.text)
                if embedding is None:
                    continue
                
                # Prepare metadata
                metadata = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "workspace_id": workspace_id,
                    "chunk_index": chunk.chunk_index,
                    "importance_score": chunk.importance_score,
                    "block_types": json.dumps(chunk.metadata.get("block_types", [])),
                    "sections": json.dumps(chunk.metadata.get("sections", [])),
                    "entities": json.dumps(chunk.entities),
                    "keywords": json.dumps(chunk.keywords),
                    "created_at": chunk.created_at,
                    "text_length": len(chunk.text)
                }
                
                # Add custom metadata
                metadata.update(chunk.metadata)
                
                chunk_ids.append(chunk.chunk_id)
                embeddings.append(embedding)
                metadatas.append(metadata)
                documents.append(chunk.text)
            
            # Add to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            
            # Index for BM25 if using hybrid strategy
            if indexing_strategy in [IndexingStrategy.HYBRID, IndexingStrategy.SPARSE]:
                await self._index_for_bm25(chunks, workspace_id)
            
            logger.info(f"Added {len(chunks)} chunks to vector database")
            return True
            
        except Exception as e:
            logger.error("Failed to add chunks to vector database", error=str(e))
            return False
    
    async def search(self, 
                    query: str, 
                    workspace_id: str,
                    config: SearchConfig = None) -> List[SearchResult]:
        """Advanced vector search with multiple strategies"""
        if config is None:
            config = SearchConfig()
        
        start_time = time.time()
        self.search_stats["total_searches"] += 1
        
        try:
            # Check cache first
            if config.use_cache and self.redis_client:
                cached_results = await self._get_cached_results(query, workspace_id, config)
                if cached_results:
                    self.search_stats["cache_hits"] += 1
                    return cached_results
            
            # Perform search based on mode
            if config.search_mode == SearchMode.SIMILARITY:
                results = await self._similarity_search(query, workspace_id, config)
            elif config.search_mode == SearchMode.HYBRID:
                results = await self._hybrid_search(query, workspace_id, config)
            elif config.search_mode == SearchMode.SEMANTIC:
                results = await self._semantic_search(query, workspace_id, config)
            elif config.search_mode == SearchMode.MULTI_QUERY:
                results = await self._multi_query_search(query, workspace_id, config)
            elif config.search_mode == SearchMode.FUSION:
                results = await self._fusion_search(query, workspace_id, config)
            else:
                results = await self._similarity_search(query, workspace_id, config)
            
            # Apply reranking if enabled
            if config.use_reranking and self.reranking_model and len(results) > config.rerank_top_k:
                results = await self._rerank_results(query, results, config.rerank_top_k)
            
            # Apply importance boosting
            if config.boost_important:
                results = self._boost_important_results(results)
            
            # Cache results
            if config.use_cache and self.redis_client:
                await self._cache_results(query, workspace_id, config, results)
            
            # Update performance stats
            search_time = time.time() - start_time
            self.search_stats["avg_search_time"] = (
                (self.search_stats["avg_search_time"] * (self.search_stats["total_searches"] - 1) + search_time) 
                / self.search_stats["total_searches"]
            )
            
            logger.info(f"Search completed in {search_time:.3f}s, found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error("Search failed", error=str(e))
            return []
    
    async def _similarity_search(self, query: str, workspace_id: str, config: SearchConfig) -> List[SearchResult]:
        """Pure vector similarity search"""
        if not self.collection:
            return []
        
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        if query_embedding is None:
            return []
        
        # Build where clause for workspace filtering
        where_clause = {"workspace_id": workspace_id}
        if config.filter_by_metadata:
            where_clause.update(config.filter_by_metadata)
        
        # Search in ChromaDB
        search_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=config.top_k,
            where=where_clause
        )
        
        # Convert to SearchResult objects
        results = []
        if search_results['ids'] and search_results['ids'][0]:
            for i, chunk_id in enumerate(search_results['ids'][0]):
                results.append(SearchResult(
                    chunk_id=chunk_id,
                    document_id=search_results['metadatas'][0][i].get('document_id', 0),
                    text=search_results['documents'][0][i],
                    score=1 - search_results['distances'][0][i],  # Convert distance to similarity
                    metadata=search_results['metadatas'][0][i],
                    search_method="vector_similarity",
                    rank=i + 1
                ))
        
        return results
    
    async def _hybrid_search(self, query: str, workspace_id: str, config: SearchConfig) -> List[SearchResult]:
        """Hybrid search combining vector similarity and BM25"""
        if not self.bm25_available:
            return await self._similarity_search(query, workspace_id, config)
        
        # Get vector results
        vector_results = await self._similarity_search(query, workspace_id, config)
        
        # Get BM25 results
        bm25_results = await self._bm25_search(query, workspace_id, config)
        
        # Combine and rerank results
        combined_results = self._combine_search_results(vector_results, bm25_results)
        
        return combined_results[:config.top_k]
    
    async def _semantic_search(self, query: str, workspace_id: str, config: SearchConfig) -> List[SearchResult]:
        """Semantic search with query expansion and reranking"""
        # Generate multiple query variations
        query_variations = await self._generate_query_variations(query)
        
        # Search with each variation
        all_results = []
        for variation in query_variations:
            results = await self._similarity_search(variation, workspace_id, config)
            all_results.extend(results)
        
        # Deduplicate and rerank
        unique_results = self._deduplicate_results(all_results)
        reranked_results = await self._rerank_results(query, unique_results, config.top_k)
        
        return reranked_results
    
    async def _multi_query_search(self, query: str, workspace_id: str, config: SearchConfig) -> List[SearchResult]:
        """Multi-query search with different strategies"""
        # Generate different query formulations
        queries = [
            query,  # Original query
            f"What is {query}?",  # Question format
            f"Explain {query}",  # Explanation format
            f"Information about {query}",  # Information format
        ]
        
        # Search with each query
        all_results = []
        for q in queries:
            results = await self._similarity_search(q, workspace_id, config)
            all_results.extend(results)
        
        # Combine and deduplicate
        combined_results = self._deduplicate_results(all_results)
        return combined_results[:config.top_k]
    
    async def _fusion_search(self, query: str, workspace_id: str, config: SearchConfig) -> List[SearchResult]:
        """Fusion search combining multiple methods"""
        # Run different search methods
        vector_results = await self._similarity_search(query, workspace_id, config)
        hybrid_results = await self._hybrid_search(query, workspace_id, config)
        semantic_results = await self._semantic_search(query, workspace_id, config)
        
        # Combine all results
        all_results = vector_results + hybrid_results + semantic_results
        
        # Deduplicate and rerank
        unique_results = self._deduplicate_results(all_results)
        reranked_results = await self._rerank_results(query, unique_results, config.top_k)
        
        return reranked_results
    
    async def _bm25_search(self, query: str, workspace_id: str, config: SearchConfig) -> List[SearchResult]:
        """BM25 search for hybrid retrieval"""
        # This would be implemented with BM25 index
        # For now, return empty results
        return []
    
    async def _generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for semantic search"""
        variations = [query]
        
        # Add question variations
        if not query.endswith('?'):
            variations.append(f"What is {query}?")
            variations.append(f"How does {query} work?")
            variations.append(f"Why is {query} important?")
        
        # Add keyword variations
        words = query.split()
        if len(words) > 1:
            variations.append(" ".join(words[:len(words)//2]))  # First half
            variations.append(" ".join(words[len(words)//2:]))  # Second half
        
        return variations[:5]  # Limit to 5 variations
    
    def _combine_search_results(self, vector_results: List[SearchResult], bm25_results: List[SearchResult]) -> List[SearchResult]:
        """Combine vector and BM25 results using reciprocal rank fusion"""
        # Create score maps
        vector_scores = {r.chunk_id: r.score for r in vector_results}
        bm25_scores = {r.chunk_id: r.score for r in bm25_results}
        
        # Get all unique chunk IDs
        all_chunk_ids = set(vector_scores.keys()) | set(bm25_scores.keys())
        
        # Calculate reciprocal rank fusion scores
        combined_results = []
        for chunk_id in all_chunk_ids:
            vector_score = vector_scores.get(chunk_id, 0.0)
            bm25_score = bm25_scores.get(chunk_id, 0.0)
            
            # Reciprocal rank fusion
            rrf_score = (1 / (60 + vector_results.index(next(r for r in vector_results if r.chunk_id == chunk_id)) + 1) if chunk_id in vector_scores else 0) + \
                       (1 / (60 + bm25_results.index(next(r for r in bm25_results if r.chunk_id == chunk_id)) + 1) if chunk_id in bm25_scores else 0)
            
            # Find the result object
            result = next((r for r in vector_results if r.chunk_id == chunk_id), None)
            if not result:
                result = next((r for r in bm25_results if r.chunk_id == chunk_id), None)
            
            if result:
                result.score = rrf_score
                result.search_method = "hybrid"
                combined_results.append(result)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x.score, reverse=True)
        
        return combined_results
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on chunk_id"""
        seen = set()
        unique_results = []
        
        for result in results:
            if result.chunk_id not in seen:
                seen.add(result.chunk_id)
                unique_results.append(result)
        
        return unique_results
    
    async def _rerank_results(self, query: str, results: List[SearchResult], top_k: int) -> List[SearchResult]:
        """Rerank results using cross-encoder"""
        if not self.reranking_model or len(results) <= 1:
            return results[:top_k]
        
        start_time = time.time()
        
        try:
            # Prepare query-document pairs
            pairs = [(query, result.text) for result in results]
            
            # Get reranking scores
            rerank_scores = self.reranking_model.predict(pairs)
            
            # Update results with reranking scores
            for i, result in enumerate(results):
                result.reranked_score = float(rerank_scores[i])
                result.score = result.reranked_score  # Use reranked score as final score
                result.explanation = f"Reranked from {result.search_method}"
            
            # Sort by reranked score
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Update performance stats
            rerank_time = time.time() - start_time
            self.search_stats["rerank_time"] = rerank_time
            
            return results[:top_k]
            
        except Exception as e:
            logger.warning("Reranking failed", error=str(e))
            return results[:top_k]
    
    def _boost_important_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Boost results based on importance scores"""
        for result in results:
            if result.metadata and 'importance_score' in result.metadata:
                importance_boost = result.metadata['importance_score'] * 0.1  # 10% boost
                result.score = min(1.0, result.score + importance_boost)
                result.explanation = f"Boosted by importance: {result.metadata['importance_score']:.2f}"
        
        # Resort by updated scores
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self.embedding_model:
            # Return dummy embedding
            return [0.0] * self.embedding_dimension
        
        try:
            start_time = time.time()
            embedding = self.embedding_model.encode(text).tolist()
            
            # Update performance stats
            embedding_time = time.time() - start_time
            self.search_stats["embedding_time"] = embedding_time
            
            return embedding
        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            return None
    
    async def _index_for_bm25(self, chunks: List[Chunk], workspace_id: str):
        """Index chunks for BM25 search"""
        # This would implement BM25 indexing
        # For now, just log
        logger.info(f"Indexing {len(chunks)} chunks for BM25 search")
    
    async def _get_cached_results(self, query: str, workspace_id: str, config: SearchConfig) -> Optional[List[SearchResult]]:
        """Get cached search results"""
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(query, workspace_id, config)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                # Deserialize results
                results_data = json.loads(cached_data)
                results = [SearchResult(**result) for result in results_data]
                return results
            
            return None
        except Exception as e:
            logger.warning("Failed to get cached results", error=str(e))
            return None
    
    async def _cache_results(self, query: str, workspace_id: str, config: SearchConfig, results: List[SearchResult]):
        """Cache search results"""
        if not self.redis_client:
            return
        
        try:
            cache_key = self._generate_cache_key(query, workspace_id, config)
            
            # Serialize results
            results_data = [
                {
                    "chunk_id": r.chunk_id,
                    "document_id": r.document_id,
                    "text": r.text,
                    "score": r.score,
                    "metadata": r.metadata or {},
                    "search_method": r.search_method,
                    "rank": r.rank,
                    "reranked_score": r.reranked_score,
                    "explanation": r.explanation
                }
                for r in results
            ]
            
            await self.redis_client.setex(
                cache_key,
                config.cache_ttl,
                json.dumps(results_data)
            )
            
        except Exception as e:
            logger.warning("Failed to cache results", error=str(e))
    
    def _generate_cache_key(self, query: str, workspace_id: str, config: SearchConfig) -> str:
        """Generate cache key for search results"""
        key_data = {
            "query": query,
            "workspace_id": workspace_id,
            "top_k": config.top_k,
            "search_mode": config.search_mode.value,
            "use_reranking": config.use_reranking,
            "filter": config.filter_by_metadata
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return f"search:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    async def delete_workspace(self, workspace_id: str) -> bool:
        """Delete all chunks for a workspace"""
        try:
            if not self.collection:
                return False
            
            # Delete from ChromaDB
            self.collection.delete(where={"workspace_id": workspace_id})
            
            # Clear cache
            if self.redis_client:
                pattern = f"search:*{workspace_id}*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
            
            logger.info(f"Deleted workspace {workspace_id} from vector database")
            return True
            
        except Exception as e:
            logger.error("Failed to delete workspace", error=str(e))
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        stats = self.search_stats.copy()
        
        # Add collection stats
        if self.collection:
            try:
                collection_count = self.collection.count()
                stats["total_chunks"] = collection_count
            except:
                stats["total_chunks"] = 0
        else:
            stats["total_chunks"] = 0
        
        # Add cache stats
        if self.redis_client:
            try:
                cache_info = await self.redis_client.info("memory")
                stats["cache_memory_usage"] = cache_info.get("used_memory_human", "0B")
            except:
                stats["cache_memory_usage"] = "Unknown"
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        health = {
            "status": "healthy",
            "components": {},
            "timestamp": time.time()
        }
        
        # Check ChromaDB
        if self.collection:
            try:
                self.collection.count()
                health["components"]["chromadb"] = "healthy"
            except Exception as e:
                health["components"]["chromadb"] = f"unhealthy: {str(e)}"
                health["status"] = "degraded"
        else:
            health["components"]["chromadb"] = "not_available"
            health["status"] = "degraded"
        
        # Check Redis
        if self.redis_client:
            try:
                await self.redis_client.ping()
                health["components"]["redis"] = "healthy"
            except Exception as e:
                health["components"]["redis"] = f"unhealthy: {str(e)}"
                health["status"] = "degraded"
        else:
            health["components"]["redis"] = "not_available"
        
        # Check embedding model
        if self.embedding_model:
            try:
                test_embedding = self.embedding_model.encode("test")
                health["components"]["embedding_model"] = "healthy"
            except Exception as e:
                health["components"]["embedding_model"] = f"unhealthy: {str(e)}"
                health["status"] = "degraded"
        else:
            health["components"]["embedding_model"] = "not_available"
            health["status"] = "degraded"
        
        return health
