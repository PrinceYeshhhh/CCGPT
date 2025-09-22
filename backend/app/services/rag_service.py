"""
RAG (Retrieval-Augmented Generation) service for enhanced query processing
"""

import time
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
import structlog

from app.services.vector_service import VectorService
from app.services.gemini_service import GeminiService
from app.services.embeddings_service import embeddings_service
from app.models.chat import ChatSession, ChatMessage
from app.schemas.rag import RAGQueryResponse, RAGSource, RAGStreamChunk

logger = structlog.get_logger()


class RAGService:
    """Enhanced RAG service with proper citations and streaming support"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vector_service = VectorService()
        self.gemini_service = GeminiService()
    
    async def process_query(
        self,
        workspace_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 6
    ) -> RAGQueryResponse:
        """
        Process a RAG query with enhanced prompting and citations
        
        Args:
            workspace_id: Workspace identifier
            query: User query
            session_id: Optional session ID for continuity
            top_k: Number of chunks to retrieve
        
        Returns:
            RAGQueryResponse with answer, sources, and metadata
        """
        start_time = time.time()
        
        try:
            # Get or create session
            session = await self._get_or_create_session(workspace_id, session_id)
            
            # Step 1: Vector search for relevant chunks
            similar_chunks = await self.vector_service.search_similar_chunks(
                query=query,
                workspace_id=workspace_id,
                limit=top_k
            )
            
            # Step 2: Build enhanced RAG prompt with citations
            context_text = self._build_context_with_citations(similar_chunks)
            prompt = self._build_rag_prompt(query, context_text, similar_chunks)
            
            # Step 3: Generate response with Gemini
            gemini_response = await self.gemini_service.generate_response(
                user_message=query,
                context=context_text,
                sources=similar_chunks
            )
            
            # Step 4: Extract and format sources
            sources = self._format_sources(similar_chunks)
            
            # Step 5: Save interaction to database
            await self._save_interaction(
                session=session,
                query=query,
                answer=gemini_response["content"],
                sources=sources,
                response_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=gemini_response.get("tokens_used"),
                model_used=gemini_response.get("model_used", "gemini-pro")
            )
            
            # Step 6: Build response
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return RAGQueryResponse(
                answer=gemini_response["content"],
                sources=sources,
                response_time_ms=response_time_ms,
                session_id=session.session_id,
                tokens_used=gemini_response.get("tokens_used"),
                confidence_score=gemini_response.get("confidence_score", "medium"),
                model_used=gemini_response.get("model_used", "gemini-pro")
            )
            
        except Exception as e:
            logger.error(
                "RAG query processing failed",
                error=str(e),
                workspace_id=workspace_id,
                query=query[:100]
            )
            
            # Return fallback response
            return RAGQueryResponse(
                answer="I apologize, but I'm having trouble processing your request right now. Please try again later.",
                sources=[],
                response_time_ms=int((time.time() - start_time) * 1000),
                session_id=session_id or str(uuid.uuid4()),
                tokens_used=0,
                confidence_score="low",
                model_used="fallback"
            )
    
    async def process_query_stream(
        self,
        workspace_id: str,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 6
    ) -> AsyncGenerator[RAGStreamChunk, None]:
        """
        Process a RAG query with streaming response
        
        Args:
            workspace_id: Workspace identifier
            query: User query
            session_id: Optional session ID for continuity
            top_k: Number of chunks to retrieve
        
        Yields:
            RAGStreamChunk objects for streaming response
        """
        try:
            # Send start chunk
            yield RAGStreamChunk(
                type="start",
                content="Starting query processing...",
                metadata={"workspace_id": workspace_id, "query": query[:100]}
            )
            
            # Get or create session
            session = await self._get_or_create_session(workspace_id, session_id)
            
            # Step 1: Vector search
            yield RAGStreamChunk(
                type="searching",
                content="Searching knowledge base...",
                metadata={"step": "vector_search"}
            )
            
            similar_chunks = await self.vector_service.search_similar_chunks(
                query=query,
                workspace_id=workspace_id,
                limit=top_k
            )
            
            # Step 2: Build context
            context_text = self._build_context_with_citations(similar_chunks)
            sources = self._format_sources(similar_chunks)
            
            # Send sources chunk
            yield RAGStreamChunk(
                type="sources",
                sources=sources,
                metadata={"sources_count": len(sources)}
            )
            
            # Step 3: Generate response
            yield RAGStreamChunk(
                type="generating",
                content="Generating response...",
                metadata={"step": "llm_generation"}
            )
            
            gemini_response = await self.gemini_service.generate_response(
                user_message=query,
                context=context_text,
                sources=similar_chunks
            )
            
            # Send answer chunk
            yield RAGStreamChunk(
                type="answer",
                content=gemini_response["content"],
                metadata={
                    "model_used": gemini_response.get("model_used", "gemini-pro"),
                    "confidence_score": gemini_response.get("confidence_score", "medium"),
                    "tokens_used": gemini_response.get("tokens_used")
                }
            )
            
            # Send end chunk
            yield RAGStreamChunk(
                type="end",
                content="Query processing complete",
                metadata={
                    "session_id": session.session_id,
                    "sources_count": len(sources)
                }
            )
            
        except Exception as e:
            logger.error(
                "RAG streaming query failed",
                error=str(e),
                workspace_id=workspace_id,
                query=query[:100]
            )
            
            # Send error chunk
            yield RAGStreamChunk(
                type="error",
                content="I apologize, but I'm having trouble processing your request right now. Please try again later.",
                metadata={"error": str(e)}
            )
    
    def _build_context_with_citations(self, similar_chunks: List[Dict[str, Any]]) -> str:
        """Build context text with proper chunk citations"""
        if not similar_chunks:
            return ""
        
        context_parts = []
        for i, chunk in enumerate(similar_chunks, 1):
            chunk_id = chunk.get("chunk_id", f"chunk_{i}")
            content = chunk.get("content", chunk.get("text", ""))
            metadata = chunk.get("metadata", {})
            
            # Build citation
            citation = f"[chunk_id:{chunk_id}]"
            if metadata.get("document_id"):
                citation += f" [doc:{metadata['document_id']}]"
            if metadata.get("section_title"):
                citation += f" [section:{metadata['section_title']}]"
            
            context_parts.append(f"{citation} {content}")
        
        return "\n\n".join(context_parts)
    
    def _build_rag_prompt(
        self, 
        query: str, 
        context: str, 
        sources: List[Dict[str, Any]]
    ) -> str:
        """Build enhanced RAG prompt with proper instructions"""
        prompt_parts = [
            "System: You are CustomerCareGPT, a helpful support AI. Only answer using the provided context.\n\n",
            
            "Context (with metadata):\n",
            context,
            "\n\n",
            
            f"User Query: \"{query}\"\n\n",
            
            "Instruction: Answer in a helpful, professional tone. If unsure, say \"I don't know\". ",
            "Always cite sources using chunk_ids in your response. ",
            "Format citations as [chunk_id:123] when referencing specific information.\n\n",
            
            "Response:"
        ]
        
        return "".join(prompt_parts)
    
    def _format_sources(self, similar_chunks: List[Dict[str, Any]]) -> List[RAGSource]:
        """Format sources for response"""
        sources = []
        
        for chunk in similar_chunks:
            metadata = chunk.get("metadata", {})
            sources.append(RAGSource(
                chunk_id=chunk.get("chunk_id", ""),
                document_id=str(metadata.get("document_id", "")),
                chunk_index=metadata.get("chunk_index", 0),
                text=chunk.get("content", chunk.get("text", ""))[:200] + "..." if len(chunk.get("content", chunk.get("text", ""))) > 200 else chunk.get("content", chunk.get("text", "")),
                similarity_score=chunk.get("similarity_score", chunk.get("score", 0.0))
            ))
        
        return sources
    
    async def _get_or_create_session(
        self, 
        workspace_id: str, 
        session_id: Optional[str] = None
    ) -> ChatSession:
        """Get existing session or create new one"""
        if session_id:
            session = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.workspace_id == workspace_id
            ).first()
            
            if session:
                return session
        
        # Create new session
        new_session_id = str(uuid.uuid4())
        # For testing, we'll use a default user_id since workspace_id is a UUID
        session = ChatSession(
            workspace_id=workspace_id,
            user_id=1,  # Default user_id for testing
            session_id=new_session_id,
            is_active=True
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        logger.info(
            "New RAG session created",
            workspace_id=workspace_id,
            session_id=new_session_id
        )
        
        return session
    
    async def _save_interaction(
        self,
        session: ChatSession,
        query: str,
        answer: str,
        sources: List[RAGSource],
        response_time_ms: int,
        tokens_used: Optional[int] = None,
        model_used: str = "gemini-pro"
    ):
        """Save interaction to database"""
        try:
            # Save user message
            user_message = ChatMessage(
                session_id=session.id,
                role="user",
                content=query
            )
            self.db.add(user_message)
            
            # Save assistant response
            assistant_message = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=answer,
                model_used=model_used,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                sources_used=[source.dict() for source in sources],
                confidence_score="high" if len(sources) > 0 else "low"
            )
            self.db.add(assistant_message)
            
            # Update session
            from datetime import datetime
            session.updated_at = datetime.now()
            
            self.db.commit()
            
            logger.info(
                "RAG interaction saved",
                session_id=session.session_id,
                response_time_ms=response_time_ms,
                sources_count=len(sources)
            )
            
        except Exception as e:
            logger.error(
                "Failed to save RAG interaction",
                error=str(e),
                session_id=session.session_id
            )
            self.db.rollback()
            raise
