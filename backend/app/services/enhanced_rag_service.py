import warnings
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")
"""
Enhanced RAG service with advanced retrieval, reranking, and generation capabilities
"""

import time
import uuid
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple
from sqlalchemy.orm import Session
import structlog
from dataclasses import dataclass
from enum import Enum

from app.services.vector_service import VectorService
from app.services.gemini_service import GeminiService
from app.services.enhanced_embeddings_service import enhanced_embeddings_service
from app.models.chat import ChatSession, ChatMessage
from app.schemas.rag import RAGQueryResponse, RAGQueryRequest

logger = structlog.get_logger()


class RetrievalStrategy(Enum):
    """Retrieval strategies for RAG"""
    VECTOR_ONLY = "vector_only"  # Only vector similarity search
    HYBRID = "hybrid"  # Vector + keyword search
    RERANKED = "reranked"  # Vector search + reranking
    MULTI_QUERY = "multi_query"  # Multiple query variations


class RerankingMethod(Enum):
    """Reranking methods for retrieved documents"""
    COSINE_SIMILARITY = "cosine_similarity"
    CROSS_ENCODER = "cross_encoder"
    BM25 = "bm25"
    COMBINED = "combined"


@dataclass
class RetrievalResult:
    """Result from document retrieval"""
    chunk_id: str
    document_id: int
    text: str
    score: float
    metadata: Dict[str, Any]
    retrieval_method: str
    rank: int


@dataclass
class RerankedResult:
    """Result after reranking"""
    chunk_id: str
    document_id: int
    text: str
    original_score: float
    reranked_score: float
    metadata: Dict[str, Any]
    rank: int


class EnhancedRAGService:
    """Enhanced RAG service with advanced retrieval and generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_service = VectorService()
        self.gemini_service = GeminiService()
        self.embeddings_service = enhanced_embeddings_service
        
        # Configuration
        self.default_top_k = 10
        self.rerank_top_k = 5
        self.retrieval_strategy = RetrievalStrategy.RERANKED
        self.reranking_method = RerankingMethod.CROSS_ENCODER
        
        # Initialize reranking model if available
        self._initialize_reranking_model()
    
    def _initialize_reranking_model(self):
        """Initialize reranking model for better relevance scoring"""
        try:
            # Try to load a cross-encoder model for reranking
            from sentence_transformers import CrossEncoder
            self.reranking_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("Cross-encoder reranking model loaded")
        except ImportError:
            logger.warning("Cross-encoder not available, using cosine similarity for reranking")
            self.reranking_model = None
        except Exception as e:
            logger.warning("Failed to load reranking model", error=str(e))
            self.reranking_model = None
    
    async def process_query(
        self,
        workspace_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 6,
        retrieval_strategy: Optional[RetrievalStrategy] = None,
        use_streaming: bool = False
    ) -> RAGQueryResponse:
        """
        Process a RAG query with enhanced retrieval and generation
        
        Args:
            workspace_id: Workspace identifier
            query: User query
            session_id: Optional session ID for continuity
            top_k: Number of chunks to retrieve
            retrieval_strategy: Strategy for document retrieval
            use_streaming: Whether to use streaming response
        
        Returns:
            RAGQueryResponse with answer, sources, and metadata
        """
        start_time = time.time()
        
        try:
            # Get or create session
            session = await self._get_or_create_session(workspace_id, session_id)
            
            # Step 1: Enhanced retrieval
            retrieval_strategy = retrieval_strategy or self.retrieval_strategy
            retrieved_chunks = await self._enhanced_retrieval(
                query=query,
                workspace_id=workspace_id,
                top_k=top_k,
                strategy=retrieval_strategy
            )
            
            if not retrieved_chunks:
                return self._create_no_results_response(query, start_time)
            
            # Step 2: Rerank results for better relevance
            reranked_chunks = await self._rerank_results(query, retrieved_chunks)
            
            # Step 3: Build enhanced context
            context_text = self._build_enhanced_context(reranked_chunks, query)
            
            # Step 4: Generate response with advanced prompting
            if use_streaming:
                # This would return a streaming response
                return await self._generate_streaming_response(
                    query, context_text, reranked_chunks, session
                )
            else:
                return await self._generate_standard_response(
                    query, context_text, reranked_chunks, session, start_time
                )
                
        except Exception as e:
            logger.error("Enhanced RAG query processing failed", error=str(e))
            return self._create_error_response(str(e), start_time)
    
    async def _enhanced_retrieval(
        self,
        query: str,
        workspace_id: str,
        top_k: int,
        strategy: RetrievalStrategy
    ) -> List[RetrievalResult]:
        """Enhanced document retrieval with multiple strategies"""
        
        if strategy == RetrievalStrategy.VECTOR_ONLY:
            return await self._vector_only_retrieval(query, workspace_id, top_k)
        elif strategy == RetrievalStrategy.HYBRID:
            return await self._hybrid_retrieval(query, workspace_id, top_k)
        elif strategy == RetrievalStrategy.MULTI_QUERY:
            return await self._multi_query_retrieval(query, workspace_id, top_k)
        else:  # RERANKED
            return await self._vector_only_retrieval(query, workspace_id, top_k * 2)  # Get more for reranking
    
    async def _vector_only_retrieval(
        self,
        query: str,
        workspace_id: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """Vector similarity search only"""
        try:
            similar_chunks = await self.vector_service.search_similar_chunks(
                query=query,
                workspace_id=workspace_id,
                limit=top_k
            )
            
            results = []
            for i, chunk in enumerate(similar_chunks):
                results.append(RetrievalResult(
                    chunk_id=chunk.get("chunk_id", ""),
                    document_id=chunk.get("document_id", 0),
                    text=chunk.get("text", ""),
                    score=chunk.get("similarity_score", 0.0),
                    metadata=chunk.get("metadata", {}),
                    retrieval_method="vector_similarity",
                    rank=i + 1
                ))
            
            return results
            
        except Exception as e:
            logger.error("Vector retrieval failed", error=str(e))
            return []
    
    async def _hybrid_retrieval(
        self,
        query: str,
        workspace_id: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """Hybrid retrieval combining vector and keyword search"""
        try:
            # Vector search
            vector_results = await self._vector_only_retrieval(query, workspace_id, top_k)
            
            # Keyword search (simplified BM25-like approach)
            keyword_results = await self._keyword_search(query, workspace_id, top_k)
            
            # Combine and deduplicate results
            combined_results = self._combine_retrieval_results(vector_results, keyword_results)
            
            # Sort by combined score
            combined_results.sort(key=lambda x: x.score, reverse=True)
            
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error("Hybrid retrieval failed", error=str(e))
            return await self._vector_only_retrieval(query, workspace_id, top_k)
    
    async def _multi_query_retrieval(
        self,
        query: str,
        workspace_id: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """Multi-query retrieval with query expansion"""
        try:
            # Generate query variations
            query_variations = await self._generate_query_variations(query)
            
            all_results = []
            
            # Search with each query variation
            for i, variation in enumerate(query_variations):
                variation_results = await self._vector_only_retrieval(
                    variation, workspace_id, top_k // len(query_variations) + 1
                )
                
                # Adjust scores based on variation quality
                for result in variation_results:
                    result.score *= (1.0 - i * 0.1)  # Reduce score for later variations
                    result.retrieval_method = f"multi_query_{i}"
                
                all_results.extend(variation_results)
            
            # Deduplicate and rerank
            unique_results = self._deduplicate_results(all_results)
            unique_results.sort(key=lambda x: x.score, reverse=True)
            
            return unique_results[:top_k]
            
        except Exception as e:
            logger.error("Multi-query retrieval failed", error=str(e))
            return await self._vector_only_retrieval(query, workspace_id, top_k)
    
    async def _keyword_search(
        self,
        query: str,
        workspace_id: str,
        top_k: int
    ) -> List[RetrievalResult]:
        """Simple keyword-based search (placeholder for BM25 implementation)"""
        # This is a simplified implementation
        # In production, you'd use a proper BM25 implementation
        
        try:
            # For now, use vector search as a proxy for keyword search
            # In a real implementation, you'd have a separate keyword index
            vector_results = await self._vector_only_retrieval(query, workspace_id, top_k)
            
            # Convert to keyword results with adjusted scoring
            keyword_results = []
            for result in vector_results:
                keyword_results.append(RetrievalResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    text=result.text,
                    score=result.score * 0.8,  # Slightly lower score for keyword search
                    metadata=result.metadata,
                    retrieval_method="keyword_search",
                    rank=result.rank
                ))
            
            return keyword_results
            
        except Exception as e:
            logger.error("Keyword search failed", error=str(e))
            return []
    
    async def _generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for multi-query retrieval"""
        variations = [query]  # Original query
        
        # Simple variations (in production, use more sophisticated methods)
        if len(query.split()) > 1:
            # Add query without stop words
            words = query.split()
            stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
            filtered_words = [w for w in words if w.lower() not in stop_words]
            if filtered_words:
                variations.append(" ".join(filtered_words))
        
        # Add query with synonyms (simplified)
        synonym_map = {
            "how": ["what", "why", "when", "where"],
            "what": ["how", "why", "when", "where"],
            "best": ["good", "great", "excellent", "top"],
            "good": ["best", "great", "excellent", "top"]
        }
        
        for word in query.split():
            if word.lower() in synonym_map:
                for synonym in synonym_map[word.lower()][:2]:  # Limit to 2 synonyms
                    variation = query.replace(word, synonym)
                    if variation not in variations:
                        variations.append(variation)
        
        return variations[:3]  # Limit to 3 variations total
    
    def _combine_retrieval_results(
        self,
        vector_results: List[RetrievalResult],
        keyword_results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Combine results from different retrieval methods"""
        # Create a map of chunk_id to best result
        result_map = {}
        
        # Add vector results
        for result in vector_results:
            key = result.chunk_id
            if key not in result_map or result.score > result_map[key].score:
                result_map[key] = result
        
        # Add keyword results with score combination
        for result in keyword_results:
            key = result.chunk_id
            if key in result_map:
                # Combine scores (weighted average)
                vector_score = result_map[key].score
                keyword_score = result.score
                combined_score = 0.7 * vector_score + 0.3 * keyword_score
                
                result_map[key] = RetrievalResult(
                    chunk_id=result.chunk_id,
                    document_id=result.document_id,
                    text=result.text,
                    score=combined_score,
                    metadata=result.metadata,
                    retrieval_method="hybrid",
                    rank=result.rank
                )
            else:
                result_map[key] = result
        
        return list(result_map.values())
    
    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Remove duplicate results based on chunk_id"""
        seen = set()
        unique_results = []
        
        for result in results:
            if result.chunk_id not in seen:
                seen.add(result.chunk_id)
                unique_results.append(result)
        
        return unique_results
    
    async def _rerank_results(
        self,
        query: str,
        retrieved_chunks: List[RetrievalResult]
    ) -> List[RerankedResult]:
        """Rerank retrieved chunks for better relevance"""
        if not retrieved_chunks:
            return []
        
        try:
            if self.reranking_model and self.reranking_method == RerankingMethod.CROSS_ENCODER:
                return await self._cross_encoder_rerank(query, retrieved_chunks)
            else:
                return await self._cosine_similarity_rerank(query, retrieved_chunks)
                
        except Exception as e:
            logger.error("Reranking failed", error=str(e))
            # Return original results with reranked scores
            return [
                RerankedResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    original_score=chunk.score,
                    reranked_score=chunk.score,
                    metadata=chunk.metadata,
                    rank=i + 1
                )
                for i, chunk in enumerate(retrieved_chunks)
            ]
    
    async def _cross_encoder_rerank(
        self,
        query: str,
        retrieved_chunks: List[RetrievalResult]
    ) -> List[RerankedResult]:
        """Rerank using cross-encoder model"""
        try:
            # Prepare query-document pairs
            pairs = [(query, chunk.text) for chunk in retrieved_chunks]
            
            # Get reranking scores
            loop = asyncio.get_event_loop()
            scores = await loop.run_in_executor(
                None, 
                lambda: self.reranking_model.predict(pairs)
            )
            
            # Create reranked results
            reranked_results = []
            for i, (chunk, score) in enumerate(zip(retrieved_chunks, scores)):
                reranked_results.append(RerankedResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    original_score=chunk.score,
                    reranked_score=float(score),
                    metadata=chunk.metadata,
                    rank=i + 1
                ))
            
            # Sort by reranked score
            reranked_results.sort(key=lambda x: x.reranked_score, reverse=True)
            
            # Update ranks
            for i, result in enumerate(reranked_results):
                result.rank = i + 1
            
            return reranked_results[:self.rerank_top_k]
            
        except Exception as e:
            logger.error("Cross-encoder reranking failed", error=str(e))
            return await self._cosine_similarity_rerank(query, retrieved_chunks)
    
    async def _cosine_similarity_rerank(
        self,
        query: str,
        retrieved_chunks: List[RetrievalResult]
    ) -> List[RerankedResult]:
        """Rerank using cosine similarity"""
        try:
            # Generate query embedding
            query_embedding = await self.embeddings_service.generate_single_embedding(query)
            
            # Generate document embeddings
            doc_texts = [chunk.text for chunk in retrieved_chunks]
            doc_embeddings = await self.embeddings_service.generate_embeddings(doc_texts)
            
            # Calculate similarities
            similarities = []
            for i, doc_embedding in enumerate(doc_embeddings):
                similarity = self.embeddings_service._cosine_similarity(query_embedding, doc_embedding)
                similarities.append(similarity)
            
            # Create reranked results
            reranked_results = []
            for i, (chunk, similarity) in enumerate(zip(retrieved_chunks, similarities)):
                reranked_results.append(RerankedResult(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    text=chunk.text,
                    original_score=chunk.score,
                    reranked_score=similarity,
                    metadata=chunk.metadata,
                    rank=i + 1
                ))
            
            # Sort by reranked score
            reranked_results.sort(key=lambda x: x.reranked_score, reverse=True)
            
            # Update ranks
            for i, result in enumerate(reranked_results):
                result.rank = i + 1
            
            return reranked_results[:self.rerank_top_k]
            
        except Exception as e:
            logger.error("Cosine similarity reranking failed", error=str(e))
            return []
    
    def _build_enhanced_context(
        self,
        reranked_chunks: List[RerankedResult],
        query: str
    ) -> str:
        """Build enhanced context with better formatting and metadata"""
        if not reranked_chunks:
            return ""
        
        context_parts = []
        
        for i, chunk in enumerate(reranked_chunks):
            # Add chunk with metadata
            chunk_text = f"[Source {i+1}] {chunk.text}"
            
            # Add metadata if available
            if chunk.metadata:
                metadata_info = []
                if "page_number" in chunk.metadata:
                    metadata_info.append(f"Page {chunk.metadata['page_number']}")
                if "section" in chunk.metadata:
                    metadata_info.append(f"Section: {chunk.metadata['section']}")
                if "document_id" in chunk.metadata:
                    metadata_info.append(f"Document ID: {chunk.metadata['document_id']}")
                
                if metadata_info:
                    chunk_text += f" ({', '.join(metadata_info)})"
            
            context_parts.append(chunk_text)
        
        return "\n\n".join(context_parts)
    
    async def _generate_standard_response(
        self,
        query: str,
        context: str,
        reranked_chunks: List[RerankedResult],
        session: ChatSession,
        start_time: float
    ) -> RAGQueryResponse:
        """Generate standard (non-streaming) response"""
        try:
            # Generate response with Gemini
            gemini_response = await self.gemini_service.generate_response(
                user_message=query,
                context=context,
                sources=reranked_chunks
            )
            
            # Format sources
            sources = self._format_enhanced_sources(reranked_chunks)
            
            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)
            
            # Save interaction
            await self._save_interaction(session, query, gemini_response, sources)
            
            return RAGQueryResponse(
                answer=gemini_response.get("content", ""),
                sources=sources,
                response_time_ms=response_time,
                tokens_used=gemini_response.get("tokens_used", 0),
                model_used=gemini_response.get("model_used", "gemini"),
                session_id=session.session_id,
                metadata={
                    "retrieval_strategy": self.retrieval_strategy.value,
                    "reranking_method": self.reranking_method.value,
                    "chunks_retrieved": len(reranked_chunks),
                    "context_length": len(context)
                }
            )
            
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return self._create_error_response(str(e), start_time)
    
    async def _generate_streaming_response(
        self,
        query: str,
        context: str,
        reranked_chunks: List[RerankedResult],
        session: ChatSession
    ) -> RAGQueryResponse:
        """Generate streaming response (placeholder for future implementation)"""
        # This would implement streaming response generation
        # For now, return standard response
        return await self._generate_standard_response(
            query, context, reranked_chunks, session, time.time()
        )
    
    def _format_enhanced_sources(self, reranked_chunks: List[RerankedResult]) -> List[Dict[str, Any]]:
        """Format sources with enhanced metadata"""
        sources = []
        
        for i, chunk in enumerate(reranked_chunks):
            source = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "text": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                "score": chunk.reranked_score,
                "rank": chunk.rank,
                "metadata": chunk.metadata
            }
            sources.append(source)
        
        return sources
    
    async def _get_or_create_session(self, workspace_id: str, session_id: Optional[str]) -> ChatSession:
        """Get or create chat session"""
        if session_id:
            session = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.workspace_id == workspace_id
            ).first()
            
            if session:
                return session
        
        # Create new session
        new_session_id = str(uuid.uuid4())
        session = ChatSession(
            workspace_id=workspace_id,
            user_id=int(workspace_id),  # Using workspace_id as user_id for now
            session_id=new_session_id,
            is_active=True
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    async def _save_interaction(
        self,
        session: ChatSession,
        query: str,
        response: Dict[str, Any],
        sources: List[Dict[str, Any]]
    ):
        """Save interaction to database"""
        try:
            # Save user message
            user_message = ChatMessage(
                session_id=session.session_id,
                role="user",
                content=query,
                metadata={"timestamp": time.time()}
            )
            self.db.add(user_message)
            
            # Save assistant response
            assistant_message = ChatMessage(
                session_id=session.session_id,
                role="assistant",
                content=response.get("content", ""),
                metadata={
                    "sources": sources,
                    "tokens_used": response.get("tokens_used", 0),
                    "model_used": response.get("model_used", "gemini"),
                    "timestamp": time.time()
                }
            )
            self.db.add(assistant_message)
            
            # Update session
            from datetime import datetime
            session.updated_at = datetime.now()
            
            self.db.commit()
            
        except Exception as e:
            logger.error("Failed to save interaction", error=str(e))
            self.db.rollback()
    
    def _create_no_results_response(self, query: str, start_time: float) -> RAGQueryResponse:
        """Create response when no results are found"""
        response_time = int((time.time() - start_time) * 1000)
        
        return RAGQueryResponse(
            answer="I couldn't find any relevant information to answer your question. Please try rephrasing your query or check if the relevant documents have been uploaded.",
            sources=[],
            response_time_ms=response_time,
            tokens_used=0,
            model_used="none",
            session_id=None,
            metadata={"no_results": True}
        )
    
    def _create_error_response(self, error: str, start_time: float) -> RAGQueryResponse:
        """Create error response"""
        response_time = int((time.time() - start_time) * 1000)
        
        return RAGQueryResponse(
            answer=f"I encountered an error while processing your query: {error}. Please try again.",
            sources=[],
            response_time_ms=response_time,
            tokens_used=0,
            model_used="error",
            session_id=None,
            metadata={"error": error}
        )
