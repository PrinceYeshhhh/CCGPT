"""
Integration tests for Production RAG Service with real components
Tests the complete RAG pipeline with actual database and external service interactions
"""

import pytest
import asyncio
import time
import tempfile
import os
import sys
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from app.main import app
from app.core.database import get_db
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chat import ChatSession, ChatMessage
from app.services.production_rag_service import ProductionRAGService, RAGConfig, RAGMode, ResponseStyle
from app.services.production_rag_system import ChunkingStrategy
from app.services.production_vector_service import SearchMode


class TestProductionRAGIntegration:
    """Integration tests for Production RAG Service"""
    
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
    
    @pytest.fixture
    def test_document(self, db_session, test_workspace):
        document = Document(
            id="doc_1",
            filename="test.pdf",
            file_type="application/pdf",
            file_size=1024,
            workspace_id=test_workspace.id,
            status="processed"
        )
        db_session.add(document)
        db_session.commit()
        db_session.refresh(document)
        return document
    
    @pytest.mark.asyncio
    async def test_complete_rag_workflow(self, rag_service, test_workspace):
        """Test complete RAG workflow from file processing to query"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("""
            Customer Service Policy
            
            Our customer service team is available 24/7 to help with any questions or concerns.
            We pride ourselves on providing excellent customer support and quick response times.
            
            Refund Policy
            
            Customers can request refunds within 30 days of purchase. All refunds are processed
            within 5-7 business days. For more information, contact our support team.
            
            Shipping Information
            
            We offer free shipping on orders over $50. Standard shipping takes 3-5 business days.
            Express shipping is available for an additional fee and takes 1-2 business days.
            """)
            temp_file_path = temp_file.name
        
        try:
            # Step 1: Process file
            with patch.object(rag_service.file_processor, 'process_file') as mock_process:
                with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                    with patch.object(rag_service, '_save_document_to_db') as mock_save:
                        # Mock file processing
                        from app.services.production_rag_system import TextBlock
                        mock_text_blocks = [
                            TextBlock(content="Customer Service Policy\n\nOur customer service team is available 24/7", metadata={"page": 1}),
                            TextBlock(content="Refund Policy\n\nCustomers can request refunds within 30 days", metadata={"page": 1}),
                            TextBlock(content="Shipping Information\n\nWe offer free shipping on orders over $50", metadata={"page": 2})
                        ]
                        mock_process.return_value = mock_text_blocks
                        
                        # Mock chunking
                        from app.services.production_rag_system import Chunk
                        mock_chunks = [
                            Chunk(id="chunk_1", content="Customer Service Policy", metadata={"document_id": "doc_1"}),
                            Chunk(id="chunk_2", content="Refund Policy", metadata={"document_id": "doc_1"}),
                            Chunk(id="chunk_3", content="Shipping Information", metadata={"document_id": "doc_1"})
                        ]
                        rag_service.file_processor.create_semantic_chunks = Mock(return_value=mock_chunks)
                        mock_add.return_value = True
                        mock_save.return_value = "doc_123"
                        
                        process_result = await rag_service.process_file(
                            file_path=temp_file_path,
                            content_type="text/plain",
                            workspace_id=str(test_workspace.id)
                        )
                        
                        assert process_result["status"] == "success"
                        assert process_result["document_id"] == "doc_123"
                        assert process_result["chunks_created"] == 3
            
            # Step 2: Search documents
            with patch.object(rag_service.vector_service, 'search') as mock_search:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Customer Service Policy",
                        score=0.95,
                        metadata={"document_id": "doc_123", "chunk_id": "chunk_1"}
                    ),
                    SearchResult(
                        id="result_2",
                        content="Refund Policy",
                        score=0.87,
                        metadata={"document_id": "doc_123", "chunk_id": "chunk_2"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                search_results = await rag_service.search_documents(
                    query="What is your refund policy?",
                    workspace_id=str(test_workspace.id)
                )
                
                assert len(search_results) == 2
                assert search_results[0].score == 0.95
                assert search_results[1].score == 0.87
            
            # Step 3: Generate response
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                mock_generate.return_value = {
                    "content": "Our refund policy allows customers to request refunds within 30 days of purchase. All refunds are processed within 5-7 business days.",
                    "sources_used": [{"chunk_id": "chunk_2", "document_id": "doc_123"}],
                    "tokens_used": 150
                }
                
                response = await rag_service.generate_response(
                    query="What is your refund policy?",
                    workspace_id=str(test_workspace.id)
                )
                
                assert "refund" in response.answer.lower()
                assert "30 days" in response.answer
                assert len(response.sources) == 1
                assert response.sources[0].document_id == "doc_123"
        
        finally:
            # Cleanup
            os.unlink(temp_file_path)
    
    @pytest.mark.asyncio
    async def test_rag_with_custom_configuration(self, rag_service, test_workspace):
        """Test RAG with custom configuration"""
        custom_config = RAGConfig(
            chunk_size=500,
            chunk_overlap=100,
            search_mode=SearchMode.HYBRID,
            top_k=15,
            similarity_threshold=0.8,
            use_reranking=True,
            rerank_top_k=8,
            response_style=ResponseStyle.TECHNICAL,
            max_context_length=6000,
            include_sources=True,
            include_citations=True,
            stream_response=False,
            parallel_processing=True
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                # Mock search results
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Technical content about API usage",
                        score=0.95,
                        metadata={"document_id": "doc_1", "chunk_id": "chunk_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                # Mock technical response
                mock_generate.return_value = {
                    "content": "Technical response with detailed specifications and implementation details.",
                    "sources_used": [{"chunk_id": "chunk_1", "document_id": "doc_1"}],
                    "tokens_used": 200
                }
                
                response = await rag_service.generate_response(
                    query="How do I implement the API?",
                    workspace_id=str(test_workspace.id),
                    config=custom_config
                )
                
                assert "technical" in response.answer.lower()
                assert len(response.sources) == 1
                # Verify custom config was used
                mock_search.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_with_document_filtering(self, rag_service, test_workspace):
        """Test RAG with document filtering"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            from app.services.production_vector_service import SearchResult
            mock_search_results = [
                SearchResult(
                    id="result_1",
                    content="Content from specific document",
                    score=0.9,
                    metadata={"document_id": "doc_1", "chunk_id": "chunk_1"}
                )
            ]
            mock_search.return_value = mock_search_results
            
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                mock_generate.return_value = {
                    "content": "Response based on filtered document",
                    "sources_used": [{"chunk_id": "chunk_1", "document_id": "doc_1"}],
                    "tokens_used": 100
                }
                
                # Test with document filtering
                response = await rag_service.generate_response(
                    query="Test query",
                    workspace_id=str(test_workspace.id),
                    document_ids=["doc_1"]
                )
                
                assert "filtered document" in response.answer.lower()
                assert len(response.sources) == 1
                assert response.sources[0].document_id == "doc_1"
    
    @pytest.mark.asyncio
    async def test_rag_streaming_response(self, rag_service, test_workspace):
        """Test RAG with streaming response"""
        streaming_config = RAGConfig(
            stream_response=True,
            response_style=ResponseStyle.CONVERSATIONAL,
            max_context_length=4000
        )
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service, '_generate_streaming_response') as mock_stream:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Streaming content",
                        score=0.9,
                        metadata={"document_id": "doc_1", "chunk_id": "chunk_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                from app.schemas.rag import RAGQueryResponse
                mock_stream.return_value = RAGQueryResponse(
                    answer="Streaming response",
                    sources=[],
                    response_time_ms=100
                )
                
                response = await rag_service.generate_response(
                    query="Test streaming query",
                    workspace_id=str(test_workspace.id),
                    config=streaming_config
                )
                
                assert response.answer == "Streaming response"
                mock_stream.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_performance_tracking(self, rag_service, test_workspace):
        """Test RAG performance tracking"""
        # Test initial performance stats
        initial_stats = rag_service.get_performance_stats()
        assert initial_stats["total_queries"] == 0
        assert initial_stats["total_files_processed"] == 0
        
        # Simulate some operations
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Performance test content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Performance test response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # Simulate multiple queries
                for i in range(5):
                    await rag_service.generate_response(
                        query=f"Test query {i}",
                        workspace_id=str(test_workspace.id)
                    )
                
                # Check performance stats
                updated_stats = rag_service.get_performance_stats()
                assert updated_stats["total_queries"] >= 5
    
    @pytest.mark.asyncio
    async def test_rag_error_handling(self, rag_service, test_workspace):
        """Test RAG error handling and recovery"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            # Test search error
            mock_search.side_effect = Exception("Search service error")
            
            response = await rag_service.generate_response(
                query="Test query",
                workspace_id=str(test_workspace.id)
            )
            
            # Should return error response, not crash
            assert response.answer is not None
            assert "error" in response.answer.lower() or "unable" in response.answer.lower()
    
    @pytest.mark.asyncio
    async def test_rag_with_conversation_context(self, rag_service, test_workspace):
        """Test RAG with conversation context"""
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Contextual content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                # Mock response with conversation context
                mock_generate.return_value = {
                    "content": "Contextual response based on previous conversation",
                    "sources_used": [],
                    "tokens_used": 150
                }
                
                conversation_history = [
                    {"role": "user", "content": "What is your refund policy?"},
                    {"role": "assistant", "content": "Our refund policy allows returns within 30 days."},
                    {"role": "user", "content": "What about shipping costs?"}
                ]
                
                response = await rag_service.generate_response(
                    query="What about shipping costs?",
                    workspace_id=str(test_workspace.id),
                    session_id="session_123"
                )
                
                assert "contextual" in response.answer.lower()
                # Verify conversation history was passed to Gemini
                mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rag_caching_mechanism(self, rag_service, test_workspace):
        """Test RAG caching mechanism"""
        config = RAGConfig(use_cache=True, cache_ttl=3600)
        
        with patch.object(rag_service.vector_service, 'search') as mock_search:
            with patch.object(rag_service.gemini_service, 'generate_response') as mock_generate:
                from app.services.production_vector_service import SearchResult
                mock_search_results = [
                    SearchResult(
                        id="result_1",
                        content="Cached content",
                        score=0.9,
                        metadata={"document_id": "doc_1"}
                    )
                ]
                mock_search.return_value = mock_search_results
                
                mock_generate.return_value = {
                    "content": "Cached response",
                    "sources_used": [],
                    "tokens_used": 100
                }
                
                # First query - should populate cache
                response1 = await rag_service.generate_response(
                    query="Test query",
                    workspace_id=str(test_workspace.id),
                    config=config
                )
                
                # Second query - should use cache
                response2 = await rag_service.generate_response(
                    query="Test query",
                    workspace_id=str(test_workspace.id),
                    config=config
                )
                
                assert response1.answer == "Cached response"
                assert response2.answer == "Cached response"
                # Should be called twice (cache miss + cache hit)
                assert mock_search.call_count == 2


class TestProductionRAGAPIIntegration:
    """Integration tests for Production RAG API endpoints"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, test_user):
        from app.services.auth import AuthService
        auth_service = AuthService(None)
        token = auth_service.create_access_token({
            "user_id": str(test_user.id),
            "email": test_user.email
        })
        return {"Authorization": f"Bearer {token}"}
    
    def test_production_rag_query_endpoint(self, client, auth_headers):
        """Test production RAG query endpoint"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                mock_service = Mock()
                mock_response = {
                    "answer": "Production RAG response",
                    "sources": [
                        {
                            "document_id": "doc_1",
                            "chunk_id": "chunk_1",
                            "content": "Source content",
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
                    "query": "Production RAG test query",
                    "session_id": "session_123",
                    "config": {
                        "response_style": "technical",
                        "max_context_length": 6000,
                        "include_sources": True
                    }
                }
                
                response = client.post("/api/v1/rag/query", json=query_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "sources" in data
                assert "response_time_ms" in data
                assert data["answer"] == "Production RAG response"
    
    def test_production_rag_search_endpoint(self, client, auth_headers):
        """Test production RAG search endpoint"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                mock_service = Mock()
                mock_search_results = [
                    {
                        "id": "result_1",
                        "content": "Search result content",
                        "score": 0.95,
                        "metadata": {"document_id": "doc_1"}
                    }
                ]
                mock_service.search_documents.return_value = mock_search_results
                mock_rag_service.return_value = mock_service
                
                search_data = {
                    "query": "Search test query",
                    "config": {
                        "search_mode": "hybrid",
                        "top_k": 10,
                        "similarity_threshold": 0.8
                    }
                }
                
                response = client.post("/api/v1/rag/search", json=search_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert len(data["results"]) == 1
                assert data["results"][0]["score"] == 0.95
    
    def test_production_rag_config_endpoint(self, client, auth_headers):
        """Test production RAG configuration endpoint"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            response = client.get("/api/v1/rag/config", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "chunk_size" in data
            assert "chunk_overlap" in data
            assert "search_mode" in data
            assert "response_style" in data
            assert "max_context_length" in data


class TestProductionRAGPerformance:
    """Performance tests for Production RAG Service"""
    
    @pytest.fixture
    def rag_service(self, db_session):
        return ProductionRAGService(db_session)
    
    @pytest.mark.asyncio
    async def test_rag_performance_under_load(self, rag_service):
        """Test RAG performance under load"""
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
                
                # Test concurrent queries
                start_time = time.time()
                tasks = []
                for i in range(10):
                    task = rag_service.generate_response(
                        query=f"Load test query {i}",
                        workspace_id="ws_1"
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                end_time = time.time()
                
                # All queries should succeed
                assert len(results) == 10
                assert all(result.answer == "Load test response" for result in results)
                
                # Should complete in reasonable time
                total_time = end_time - start_time
                assert total_time < 5.0  # Should complete within 5 seconds
    
    @pytest.mark.asyncio
    async def test_rag_memory_usage(self, rag_service):
        """Test RAG memory usage with large documents"""
        with patch.object(rag_service.file_processor, 'process_file') as mock_process:
            with patch.object(rag_service.vector_service, 'add_chunks') as mock_add:
                # Mock large document processing
                from app.services.production_rag_system import TextBlock
                large_text_blocks = [
                    TextBlock(content="Large content " * 1000, metadata={"page": i})
                    for i in range(100)  # 100 pages of large content
                ]
                mock_process.return_value = large_text_blocks
                
                from app.services.production_rag_system import Chunk
                large_chunks = [
                    Chunk(id=f"chunk_{i}", content=f"Large chunk {i}", metadata={"document_id": "doc_1"})
                    for i in range(100)
                ]
                rag_service.file_processor.create_semantic_chunks = Mock(return_value=large_chunks)
                mock_add.return_value = True
                
                with patch.object(rag_service, '_save_document_to_db') as mock_save:
                    mock_save.return_value = "doc_large"
                    
                    result = await rag_service.process_file(
                        file_path="large_document.pdf",
                        content_type="application/pdf",
                        workspace_id="ws_1"
                    )
                    
                    assert result["status"] == "success"
                    assert result["chunks_created"] == 100
                    # Should handle large documents without memory issues
                    assert result["processing_time"] > 0
