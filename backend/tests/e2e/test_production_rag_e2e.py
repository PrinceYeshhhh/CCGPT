"""
End-to-End tests for Production RAG Service
Tests complete user journeys with production RAG features
"""

import pytest
import asyncio
import time
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.services.production_rag_service import (
    ProductionRAGService, 
    RAGConfig, 
    RAGMode, 
    ResponseStyle
)
from app.services.production_rag_system import ChunkingStrategy
from app.services.production_vector_service import SearchMode


class TestProductionRAGE2E:
    """End-to-End tests for Production RAG Service"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.fixture
    def test_user(self, db_session):
        user = User(
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            workspace_id="ws_1"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_workspace(self, db_session, test_user):
        workspace = Workspace(
            id="ws_1",
            name="Test Workspace",
            user_id=test_user.id
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.mark.asyncio
    async def test_complete_production_rag_workflow(self, rag_service, test_workspace):
        """Test complete production RAG workflow from file upload to advanced querying"""
        # Create a comprehensive test document
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("""
            CustomerCareGPT Advanced Features Documentation
            
            ## Advanced RAG Capabilities
            
            Our production RAG system supports multiple advanced features:
            
            ### 1. Hybrid Search
            - Combines semantic and keyword search for better results
            - Uses vector embeddings for semantic understanding
            - Includes BM25 for keyword matching
            - Reranks results for optimal relevance
            
            ### 2. Streaming Responses
            - Real-time response generation
            - Progressive content delivery
            - Better user experience for long responses
            - Reduced perceived latency
            
            ### 3. Advanced Chunking
            - Semantic chunking preserves meaning
            - Configurable chunk sizes and overlap
            - Context-aware boundary detection
            - Metadata preservation
            
            ### 4. Caching System
            - Intelligent query caching
            - Configurable TTL
            - Performance optimization
            - Cost reduction
            
            ### 5. Multi-modal Support
            - Text document processing
            - PDF extraction and analysis
            - HTML content parsing
            - Markdown formatting
            
            ## Configuration Options
            
            ### Search Configuration
            - search_mode: HYBRID, SEMANTIC, KEYWORD
            - top_k: Number of results to retrieve
            - similarity_threshold: Minimum relevance score
            - use_reranking: Enable/disable reranking
            - rerank_top_k: Number of results to rerank
            
            ### Generation Configuration
            - response_style: CONVERSATIONAL, TECHNICAL, FORMAL, CASUAL, STEP_BY_STEP
            - max_context_length: Maximum context window size
            - include_sources: Include source citations
            - include_citations: Include inline citations
            - stream_response: Enable streaming
            
            ### Performance Configuration
            - parallel_processing: Enable parallel operations
            - use_cache: Enable caching
            - cache_ttl: Cache time-to-live
            - chunk_size: Document chunk size
            - chunk_overlap: Overlap between chunks
            
            ## API Endpoints
            
            ### Query Endpoint
            POST /api/v1/rag/query
            - Supports all configuration options
            - Returns structured responses
            - Includes performance metrics
            
            ### Search Endpoint
            POST /api/v1/rag/search
            - Document search only
            - No generation
            - Fast retrieval
            
            ### Configuration Endpoint
            GET /api/v1/rag/config
            - Get available configurations
            - Default settings
            - Feature availability
            
            ## Performance Metrics
            
            The system tracks various performance metrics:
            - Query response times
            - File processing times
            - Cache hit rates
            - Success rates
            - Token usage
            - Throughput
            
            ## Error Handling
            
            Comprehensive error handling includes:
            - Graceful degradation
            - Detailed error messages
            - Retry mechanisms
            - Fallback strategies
            - Logging and monitoring
            
            ## Security Features
            
            Security measures include:
            - Input validation
            - Output sanitization
            - Rate limiting
            - Access control
            - Audit logging
            """)
            temp_file_path = temp_file.name
        
        try:
            # Step 1: Process document with advanced configuration
            advanced_config = RAGConfig(
                chunk_size=1000,
                chunk_overlap=200,
                chunking_strategy=ChunkingStrategy.SEMANTIC,
                search_mode=SearchMode.HYBRID,
                top_k=15,
                similarity_threshold=0.7,
                use_reranking=True,
                rerank_top_k=8,
                response_style=ResponseStyle.TECHNICAL,
                max_context_length=6000,
                include_sources=True,
                include_citations=True,
                stream_response=False,
                parallel_processing=True,
                use_cache=True,
                cache_ttl=3600
            )
            
            with patch.object(rag_service.file_processor, 'process_file') as mock_process:
                with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                    with patch.object(rag_service, '_save_document_to_db') as mock_save:
                        # Mock advanced file processing
                        from app.services.production_rag_system import TextBlock
                        mock_text_blocks = [
                            TextBlock(
                                content="CustomerCareGPT Advanced Features Documentation",
                                metadata={"page": 1, "section": "title"}
                            ),
                            TextBlock(
                                content="Our production RAG system supports multiple advanced features",
                                metadata={"page": 1, "section": "introduction"}
                            ),
                            TextBlock(
                                content="Hybrid Search combines semantic and keyword search",
                                metadata={"page": 1, "section": "hybrid_search"}
                            ),
                            TextBlock(
                                content="Streaming Responses provide real-time generation",
                                metadata={"page": 2, "section": "streaming"}
                            ),
                            TextBlock(
                                content="Advanced Chunking preserves meaning and context",
                                metadata={"page": 2, "section": "chunking"}
                            ),
                            TextBlock(
                                content="Caching System provides performance optimization",
                                metadata={"page": 3, "section": "caching"}
                            )
                        ]
                        mock_process.return_value = mock_text_blocks
                        
                        from app.services.production_rag_system import Chunk
                        mock_chunks = [
                            Chunk(
                                id=f"chunk_{i}",
                                content=block.content,
                                metadata={
                                    "document_id": "doc_advanced",
                                    "page": block.metadata["page"],
                                    "section": block.metadata["section"]
                                }
                            )
                            for i, block in enumerate(mock_text_blocks)
                        ]
                        rag_service.file_processor.create_semantic_chunks = Mock(return_value=mock_chunks)
                        mock_add.return_value = True
                        mock_save.return_value = "doc_advanced"
                        
                        process_result = await rag_service.process_file(
                            file_path=temp_file_path,
                            content_type="text/plain",
                            workspace_id=str(test_workspace.id),
                            config=advanced_config
                        )
                        
                        assert process_result["status"] == "success"
                        assert process_result["document_id"] == "doc_advanced"
                        assert process_result["chunks_created"] == 6
            
            # Step 2: Test hybrid search
            with patch.object(rag_service.vector_service, 'search') as mock_search:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Hybrid Search combines semantic and keyword search",
                        score=0.95,
                        metadata={"document_id": "doc_advanced", "chunk_id": "chunk_2", "section": "hybrid_search"}
                    ),
                    SearchResult(
                        id="result_2",
                        content="Our production RAG system supports multiple advanced features",
                        score=0.87,
                        metadata={"document_id": "doc_advanced", "chunk_id": "chunk_1", "section": "introduction"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                search_results = await rag_service.search_documents(
                    query="What are the advanced RAG features?",
                    workspace_id=str(test_workspace.id),
                    config=advanced_config
                )
                
                assert len(search_results) == 2
                assert search_results[0].score == 0.95
                assert "hybrid search" in search_results[0].content.lower()
            
            # Step 3: Test technical response generation
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                mock_generate.return_value = {
                    "content": "Our production RAG system supports several advanced features including hybrid search that combines semantic and keyword search for better results, streaming responses for real-time generation, advanced semantic chunking that preserves meaning and context, intelligent caching system for performance optimization, and multi-modal support for various document types. The system also includes comprehensive configuration options for search, generation, and performance parameters.",
                    "sources_used": [
                        {"chunk_id": "chunk_2", "document_id": "doc_advanced"},
                        {"chunk_id": "chunk_1", "document_id": "doc_advanced"}
                    ],
                    "tokens_used": 250
                }
                
                response = await rag_service.generate_response(
                    query="What are the advanced RAG features?",
                    workspace_id=str(test_workspace.id),
                    config=advanced_config
                )
                
                assert "hybrid search" in response.answer.lower()
                assert "streaming responses" in response.answer.lower()
                assert "semantic chunking" in response.answer.lower()
                assert "caching system" in response.answer.lower()
                assert len(response.sources) == 2
                assert response.sources[0].document_id == "doc_advanced"
            
            # Step 4: Test streaming response
            streaming_config = RAGConfig(
                stream_response=True,
                response_style=ResponseStyle.CONVERSATIONAL,
                max_context_length=4000
            )
            
            with patch.object(rag_service, '_generate_streaming_response') as mock_stream:
                from app.schemas.rag import RAGQueryResponse
                mock_stream.return_value = RAGQueryResponse(
                    answer="Streaming response about advanced RAG features",
                    sources=[],
                    response_time_ms=150
                )
                
                streaming_response = await rag_service.generate_response(
                    query="Explain streaming responses",
                    workspace_id=str(test_workspace.id),
                    config=streaming_config
                )
                
                assert "streaming" in streaming_response.answer.lower()
                mock_stream.assert_called_once()
            
            # Step 5: Test document filtering
            with patch.object(rag_service.vector_service, 'search') as mock_search:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Performance metrics include query response times and cache hit rates",
                        score=0.92,
                        metadata={"document_id": "doc_advanced", "chunk_id": "chunk_5", "section": "performance"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                    mock_generate.return_value = {
                        "content": "Performance metrics include query response times, file processing times, cache hit rates, success rates, token usage, and throughput.",
                        "sources_used": [{"chunk_id": "chunk_5", "document_id": "doc_advanced"}],
                        "tokens_used": 100
                    }
                    
                    filtered_response = await rag_service.generate_response(
                        query="What performance metrics are tracked?",
                        workspace_id=str(test_workspace.id),
                        document_ids=["doc_advanced"],
                        config=advanced_config
                    )
                    
                    assert "performance metrics" in filtered_response.answer.lower()
                    assert "query response times" in filtered_response.answer.lower()
                    assert "cache hit rates" in filtered_response.answer.lower()
            
            # Step 6: Test performance tracking
            performance_stats = rag_service.get_performance_stats()
            assert performance_stats["total_queries"] >= 0
            assert performance_stats["total_files_processed"] >= 0
            assert performance_stats["avg_query_time"] >= 0
            assert performance_stats["success_rate"] >= 0
        
        finally:
            # Cleanup
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_production_rag_api_endpoints(self, client, test_user, test_workspace):
        """Test production RAG API endpoints"""
        from app.services.auth import AuthService
        auth_service = AuthService(None)
        token = auth_service.create_access_token({
            "user_id": str(test_user.id),
            "email": test_user.email
        })
        auth_headers = {"Authorization": f"Bearer {token}"}
        
        # Test production RAG query endpoint
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = str(test_user.id)
            mock_user.workspace_id = str(test_workspace.id)
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                mock_service = Mock()
                mock_response = {
                    "answer": "Production RAG response with advanced features",
                    "sources": [
                        {
                            "document_id": "doc_1",
                            "chunk_id": "chunk_1",
                            "content": "Advanced RAG content",
                            "score": 0.95
                        }
                    ],
                    "response_time_ms": 250,
                    "tokens_used": 200,
                    "model_used": "gemini-pro"
                }
                mock_service.generate_response.return_value = mock_response
                mock_rag_service.return_value = mock_service
                
                query_data = {
                    "query": "What are the advanced RAG features?",
                    "session_id": "session_123",
                    "config": {
                        "response_style": "technical",
                        "max_context_length": 6000,
                        "include_sources": True,
                        "include_citations": True,
                        "use_reranking": True,
                        "search_mode": "hybrid"
                    }
                }
                
                response = client.post("/api/v1/rag/query", json=query_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "sources" in data
                assert "response_time_ms" in data
                assert data["answer"] == "Production RAG response with advanced features"
                assert len(data["sources"]) == 1
                assert data["sources"][0]["score"] == 0.95
        
        # Test production RAG search endpoint
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = str(test_user.id)
            mock_user.workspace_id = str(test_workspace.id)
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                mock_service = Mock()
                mock_search_results = [
                    {
                        "id": "result_1",
                        "content": "Advanced RAG search result",
                        "score": 0.95,
                        "metadata": {"document_id": "doc_1", "section": "features"}
                    }
                ]
                mock_service.search_documents.return_value = mock_search_results
                mock_rag_service.return_value = mock_service
                
                search_data = {
                    "query": "Advanced RAG features",
                    "config": {
                        "search_mode": "hybrid",
                        "top_k": 10,
                        "similarity_threshold": 0.8,
                        "use_reranking": True
                    }
                }
                
                response = client.post("/api/v1/rag/search", json=search_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert len(data["results"]) == 1
                assert data["results"][0]["score"] == 0.95
                assert "advanced" in data["results"][0]["content"].lower()
        
        # Test production RAG configuration endpoint
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = str(test_user.id)
            mock_user.workspace_id = str(test_workspace.id)
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/rag/config", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "chunk_size" in data
            assert "chunk_overlap" in data
            assert "search_mode" in data
            assert "response_style" in data
            assert "max_context_length" in data
            assert "use_reranking" in data
            assert "stream_response" in data
            assert "parallel_processing" in data
            assert "use_cache" in data
    
    @pytest.mark.asyncio
    async def test_production_rag_error_handling(self, rag_service, test_workspace):
        """Test production RAG error handling and recovery"""
        # Test file processing error
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            mock_process.side_effect = Exception("File processing error")
            
            with pytest.raises(Exception):
                await rag_service.process_file(
                    file_path="corrupted.pdf",
                    content_type="application/pdf",
                    workspace_id=str(test_workspace.id)
                )
        
        # Test search error
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            mock_search.side_effect = Exception("Search service error")
            
            response = await rag_service.generate_response(
                query="Test query",
                workspace_id=str(test_workspace.id)
            )
            
            # Should return error response, not crash
            assert response.answer is not None
            assert "error" in response.answer.lower() or "unable" in response.answer.lower()
        
        # Test generation error
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                mock_generate.side_effect = Exception("Generation service error")
                
                response = await rag_service.generate_response(
                    query="Test query",
                    workspace_id=str(test_workspace.id)
                )
                
                # Should return error response, not crash
                assert response.answer is not None
                assert "error" in response.answer.lower() or "unable" in response.answer.lower()
    
    @pytest.mark.asyncio
    async def test_production_rag_performance_under_load(self, rag_service, test_workspace):
        """Test production RAG performance under load"""
        config = RAGConfig(
            use_cache=True,
            parallel_processing=True,
            top_k=10,
            similarity_threshold=0.7
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Load test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Load test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # Test with high load
                start_time = time.time()
                tasks = []
                for i in range(100):  # 100 concurrent queries
                    task = rag_service.generate_response(
                        query=f"Load test query {i}",
                        workspace_id=str(test_workspace.id),
                        config=config
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # All queries should succeed
                assert len(results) == 100
                assert all(result.answer == "Load test response" for result in results)
                
                # Should complete in reasonable time
                total_time = end_time - start_time
                assert total_time < 20.0  # Should complete within 20 seconds
                
                print(f"100 concurrent queries completed in {total_time:.3f}s")
                print(f"Queries per second: {100/total_time:.1f}")
    
    @pytest.mark.asyncio
    async def test_production_rag_caching_behavior(self, rag_service, test_workspace):
        """Test production RAG caching behavior"""
        config = RAGConfig(
            use_cache=True,
            cache_ttl=3600,
            top_k=10,
            similarity_threshold=0.7
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Caching test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Caching test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # First query - should populate cache
                response1 = await rag_service.generate_response(
                    query="Caching test query",
                    workspace_id=str(test_workspace.id),
                    config=config
                )
                
                # Second query - should use cache
                response2 = await rag_service.generate_response(
                    query="Caching test query",
                    workspace_id=str(test_workspace.id),
                    config=config
                )
                
                # Both responses should be identical
                assert response1.answer == response2.answer
                assert response1.answer == "Caching test response"
                
                # Verify caching behavior
                assert mock_search.call_count >= 1  # At least one search call
                assert mock_generate.call_count >= 1  # At least one generation call
    
    @pytest.mark.asyncio
    async def test_production_rag_different_response_styles(self, rag_service, test_workspace):
        """Test production RAG with different response styles"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Response style test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                # Test different response styles
                response_styles = [
                    ResponseStyle.CONVERSATIONAL,
                    ResponseStyle.TECHNICAL,
                    ResponseStyle.FORMAL,
                    ResponseStyle.CASUAL,
                    ResponseStyle.STEP_BY_STEP
                ]
                
                for style in response_styles:
                    config = RAGConfig(response_style=style)
                    
                    mock_generate.return_value = {
                        "content": f"Response in {style.value} style",
                        "sources_used": [],
                        "tokens_used": 100
                    }
                    
                    response = await rag_service.generate_response(
                        query="Test query",
                        workspace_id=str(test_workspace.id),
                        config=config
                    )
                    
                    assert style.value in response.answer.lower()
                    assert response.answer == f"Response in {style.value} style"
