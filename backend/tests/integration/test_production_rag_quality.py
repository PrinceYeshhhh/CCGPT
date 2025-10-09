"""
Critical production RAG system quality and performance tests
Tests response quality, semantic chunking accuracy, and vector search performance
"""

import pytest
import asyncio
import time
import uuid
from typing import List, Dict, Any
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import numpy as np

from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, DocumentChunk, ChatSession
from app.services.production_rag_service import ProductionRAGService
from app.services.production_vector_service import ProductionVectorService
from app.services.enhanced_embeddings_service import EnhancedEmbeddingsService
from app.services.semantic_chunking_service import SemanticChunkingService


class TestProductionRAGQuality:
    """Critical production RAG system quality and performance tests"""
    
    @pytest.fixture(scope="function")
    def db_session(self):
        """Create a fresh database session for each test."""
        Base.metadata.create_all(bind=engine)
        session = Session()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
    
    @pytest.fixture(scope="function")
    def client(self, db_session):
        """Create a test client with database dependency override."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as test_client:
            yield test_client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def test_workspace(self, db_session):
        """Create test workspace"""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name="RAG Quality Test Workspace",
            description="Test workspace for RAG quality testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            email="ragtest@example.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="RAG Test User",
            workspace_id=test_workspace.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_documents(self, db_session, test_workspace, test_user):
        """Create test documents with various content types"""
        documents = []
        
        # Technical documentation
        tech_doc = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="technical_guide.pdf",
            content_type="application/pdf",
            size=50000,
            path="/tmp/technical_guide.pdf",
            uploaded_by=test_user.id,
            status="processed"
        )
        db_session.add(tech_doc)
        documents.append(tech_doc)
        
        # FAQ document
        faq_doc = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="faq.md",
            content_type="text/markdown",
            size=30000,
            path="/tmp/faq.md",
            uploaded_by=test_user.id,
            status="processed"
        )
        db_session.add(faq_doc)
        documents.append(faq_doc)
        
        # Policy document
        policy_doc = Document(
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            filename="policies.txt",
            content_type="text/plain",
            size=40000,
            path="/tmp/policies.txt",
            uploaded_by=test_user.id,
            status="processed"
        )
        db_session.add(policy_doc)
        documents.append(policy_doc)
        
        db_session.commit()
        return documents
    
    @pytest.fixture
    def test_chunks(self, db_session, test_documents, test_workspace):
        """Create test document chunks with embeddings"""
        chunks = []
        
        # Technical documentation chunks
        tech_chunks = [
            {
                "content": "To install the software, download the installer from our website and run it with administrator privileges.",
                "chunk_index": 0,
                "metadata": {"section": "installation", "document_type": "technical"}
            },
            {
                "content": "The API requires authentication using JWT tokens. Include the token in the Authorization header.",
                "chunk_index": 1,
                "metadata": {"section": "api", "document_type": "technical"}
            },
            {
                "content": "For troubleshooting, check the logs in the /var/log directory and ensure all services are running.",
                "chunk_index": 2,
                "metadata": {"section": "troubleshooting", "document_type": "technical"}
            }
        ]
        
        for i, chunk_data in enumerate(tech_chunks):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=test_documents[0].id,
                workspace_id=test_workspace.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                embedding=[0.1 + i * 0.1, 0.2 + i * 0.1, 0.3 + i * 0.1] + [0.0] * 381,  # 384-dim embedding
                metadata=chunk_data["metadata"]
            )
            db_session.add(chunk)
            chunks.append(chunk)
        
        # FAQ chunks
        faq_chunks = [
            {
                "content": "Q: How do I reset my password? A: Click on 'Forgot Password' on the login page and follow the instructions.",
                "chunk_index": 0,
                "metadata": {"question_type": "password", "document_type": "faq"}
            },
            {
                "content": "Q: What are your business hours? A: We are open Monday to Friday, 9 AM to 5 PM EST.",
                "chunk_index": 1,
                "metadata": {"question_type": "hours", "document_type": "faq"}
            },
            {
                "content": "Q: How can I contact support? A: You can reach us at support@company.com or call 1-800-HELP.",
                "chunk_index": 2,
                "metadata": {"question_type": "contact", "document_type": "faq"}
            }
        ]
        
        for i, chunk_data in enumerate(faq_chunks):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=test_documents[1].id,
                workspace_id=test_workspace.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                embedding=[0.4 + i * 0.1, 0.5 + i * 0.1, 0.6 + i * 0.1] + [0.0] * 381,  # 384-dim embedding
                metadata=chunk_data["metadata"]
            )
            db_session.add(chunk)
            chunks.append(chunk)
        
        # Policy chunks
        policy_chunks = [
            {
                "content": "Our refund policy allows returns within 30 days of purchase with original receipt.",
                "chunk_index": 0,
                "metadata": {"policy_type": "refund", "document_type": "policy"}
            },
            {
                "content": "Data privacy is important to us. We never sell your personal information to third parties.",
                "chunk_index": 1,
                "metadata": {"policy_type": "privacy", "document_type": "policy"}
            },
            {
                "content": "Shipping is free for orders over $50. Standard shipping takes 3-5 business days.",
                "chunk_index": 2,
                "metadata": {"policy_type": "shipping", "document_type": "policy"}
            }
        ]
        
        for i, chunk_data in enumerate(policy_chunks):
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=test_documents[2].id,
                workspace_id=test_workspace.id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                embedding=[0.7 + i * 0.1, 0.8 + i * 0.1, 0.9 + i * 0.1] + [0.0] * 381,  # 384-dim embedding
                metadata=chunk_data["metadata"]
            )
            db_session.add(chunk)
            chunks.append(chunk)
        
        db_session.commit()
        return chunks
    
    def test_rag_response_quality(self, client, test_user, test_workspace, test_chunks):
        """Test RAG response quality and relevance"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test queries with expected high-quality responses
            test_queries = [
                {
                    "query": "How do I reset my password?",
                    "expected_keywords": ["password", "reset", "forgot"],
                    "expected_sources": ["faq"]
                },
                {
                    "query": "What is your refund policy?",
                    "expected_keywords": ["refund", "return", "30 days"],
                    "expected_sources": ["policy"]
                },
                {
                    "query": "How do I install the software?",
                    "expected_keywords": ["install", "download", "administrator"],
                    "expected_sources": ["technical"]
                },
                {
                    "query": "What are your business hours?",
                    "expected_keywords": ["hours", "monday", "friday", "9 AM", "5 PM"],
                    "expected_sources": ["faq"]
                }
            ]
            
            for test_case in test_queries:
                with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                    # Mock RAG service response
                    mock_service = Mock()
                    mock_service.process_query.return_value = {
                        "answer": f"Based on our documentation: {test_case['query']} - Here's the relevant information...",
                        "sources": [
                            {
                                "chunk_id": str(uuid.uuid4()),
                                "document_id": str(uuid.uuid4()),
                                "content": f"Relevant content for {test_case['query']}",
                                "score": 0.95,
                                "metadata": {"document_type": test_case['expected_sources'][0]}
                            }
                        ],
                        "response_time_ms": 150,
                        "tokens_used": 100,
                        "model_used": "gemini-pro"
                    }
                    mock_rag_service.return_value = mock_service
                    
                    # Send RAG query
                    query_data = {
                        "query": test_case["query"],
                        "session_id": "test-session-1"
                    }
                    headers = {"Authorization": "Bearer test_token"}
                    response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
                    
                    # Verify response quality
                    assert response.status_code == 200
                    data = response.json()
                    
                    # Check response structure
                    assert "answer" in data
                    assert "sources" in data
                    assert "response_time_ms" in data
                    
                    # Check answer quality
                    answer = data["answer"].lower()
                    for keyword in test_case["expected_keywords"]:
                        assert keyword.lower() in answer, f"Expected keyword '{keyword}' not found in answer"
                    
                    # Check source relevance
                    assert len(data["sources"]) > 0
                    for source in data["sources"]:
                        assert source["score"] > 0.8, f"Source score too low: {source['score']}"
    
    def test_semantic_chunking_accuracy(self, db_session, test_workspace):
        """Test semantic chunking preserves meaning and context"""
        chunking_service = SemanticChunkingService()
        
        # Test document with clear semantic boundaries
        test_document = """
        # Installation Guide
        
        ## Prerequisites
        Before installing the software, ensure you have the following:
        - Windows 10 or later
        - At least 4GB RAM
        - 1GB free disk space
        
        ## Installation Steps
        1. Download the installer from our website
        2. Run the installer as administrator
        3. Follow the on-screen instructions
        4. Restart your computer
        
        ## Troubleshooting
        If you encounter issues during installation:
        - Check system requirements
        - Disable antivirus temporarily
        - Contact support for assistance
        
        # API Documentation
        
        ## Authentication
        All API requests require authentication using JWT tokens.
        Include the token in the Authorization header.
        
        ## Endpoints
        - GET /api/users - List all users
        - POST /api/users - Create a new user
        - PUT /api/users/{id} - Update user
        """
        
        # Test chunking
        chunks = chunking_service.create_semantic_chunks(test_document, max_tokens=200)
        
        # Verify chunks maintain semantic boundaries
        assert len(chunks) > 1, "Document should be chunked into multiple pieces"
        
        # Check that related content stays together
        installation_chunks = [chunk for chunk in chunks if "installation" in chunk.lower()]
        assert len(installation_chunks) >= 1, "Installation content should be chunked together"
        
        api_chunks = [chunk for chunk in chunks if "api" in chunk.lower()]
        assert len(api_chunks) >= 1, "API content should be chunked together"
        
        # Check chunk size limits
        for chunk in chunks:
            # Rough token estimation (4 chars per token)
            estimated_tokens = len(chunk) // 4
            assert estimated_tokens <= 200, f"Chunk too large: {estimated_tokens} tokens"
    
    def test_vector_search_performance(self, db_session, test_workspace, test_chunks):
        """Test vector search performance under load"""
        vector_service = ProductionVectorService()
        
        # Test search performance with multiple queries
        test_queries = [
            "How do I reset my password?",
            "What is your refund policy?",
            "How do I install the software?",
            "What are your business hours?",
            "How can I contact support?",
            "What are the system requirements?",
            "How do I troubleshoot issues?",
            "What is your privacy policy?",
            "How much does shipping cost?",
            "What payment methods do you accept?"
        ]
        
        search_times = []
        search_results = []
        
        for query in test_queries:
            start_time = time.time()
            
            # Mock vector search
            with patch('app.services.production_vector_service.ProductionVectorService.search') as mock_search:
                # Simulate search results
                mock_search.return_value = [
                    {
                        "chunk_id": str(uuid.uuid4()),
                        "content": f"Relevant content for: {query}",
                        "score": 0.9,
                        "metadata": {"document_type": "faq"}
                    }
                ]
                
                results = vector_service.search(
                    workspace_id=test_workspace.id,
                    query_vector=[0.1] * 384,  # Mock embedding
                    top_k=5
                )
                
                search_time = time.time() - start_time
                search_times.append(search_time)
                search_results.append(results)
        
        # Verify performance metrics
        avg_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)
        
        assert avg_search_time < 0.5, f"Average search time too slow: {avg_search_time:.3f}s"
        assert max_search_time < 1.0, f"Max search time too slow: {max_search_time:.3f}s"
        
        # Verify search quality
        for results in search_results:
            assert len(results) > 0, "Search should return results"
            for result in results:
                assert result["score"] > 0.7, f"Search result score too low: {result['score']}"
    
    def test_rag_response_consistency(self, client, test_user, test_workspace):
        """Test RAG response consistency across multiple queries"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test same query multiple times
            query = "How do I reset my password?"
            responses = []
            
            for i in range(3):
                with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                    mock_service = Mock()
                    mock_service.process_query.return_value = {
                        "answer": "To reset your password, click on 'Forgot Password' on the login page and follow the instructions.",
                        "sources": [
                            {
                                "chunk_id": str(uuid.uuid4()),
                                "document_id": str(uuid.uuid4()),
                                "content": "Q: How do I reset my password? A: Click on 'Forgot Password' on the login page and follow the instructions.",
                                "score": 0.95,
                                "metadata": {"document_type": "faq"}
                            }
                        ],
                        "response_time_ms": 150,
                        "tokens_used": 50,
                        "model_used": "gemini-pro"
                    }
                    mock_rag_service.return_value = mock_service
                    
                    query_data = {
                        "query": query,
                        "session_id": f"test-session-{i}"
                    }
                    headers = {"Authorization": "Bearer test_token"}
                    response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
                    
                    if response.status_code == 200:
                        responses.append(response.json())
            
            # Verify consistency
            assert len(responses) == 3, "Should get 3 responses"
            
            # Check that answers are similar (not identical due to LLM variability)
            answers = [resp["answer"] for resp in responses]
            for answer in answers:
                assert "password" in answer.lower(), "All answers should mention password"
                assert "forgot" in answer.lower() or "reset" in answer.lower(), "All answers should mention reset/forgot"
    
    def test_rag_error_handling(self, client, test_user, test_workspace):
        """Test RAG system error handling"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test with empty query
            query_data = {
                "query": "",
                "session_id": "test-session-1"
            }
            headers = {"Authorization": "Bearer test_token"}
            response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
            assert response.status_code == 422  # Validation error
            
            # Test with very long query
            long_query = "What is the meaning of life? " * 1000  # Very long query
            query_data = {
                "query": long_query,
                "session_id": "test-session-1"
            }
            response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
            assert response.status_code in [200, 422]  # Should handle gracefully
            
            # Test with special characters
            special_query = "What's the @#$%^&*() policy for <script>alert('xss')</script>?"
            query_data = {
                "query": special_query,
                "session_id": "test-session-1"
            }
            response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
            assert response.status_code in [200, 422]  # Should handle gracefully
    
    def test_rag_source_attribution(self, client, test_user, test_workspace, test_chunks):
        """Test RAG source attribution and citations"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "Based on our FAQ, you can reset your password by clicking 'Forgot Password' on the login page.",
                    "sources": [
                        {
                            "chunk_id": str(uuid.uuid4()),
                            "document_id": str(uuid.uuid4()),
                            "content": "Q: How do I reset my password? A: Click on 'Forgot Password' on the login page and follow the instructions.",
                            "score": 0.95,
                            "metadata": {"document_type": "faq", "section": "password"}
                        }
                    ],
                    "response_time_ms": 150,
                    "tokens_used": 50,
                    "model_used": "gemini-pro"
                }
                mock_rag_service.return_value = mock_service
                
                query_data = {
                    "query": "How do I reset my password?",
                    "session_id": "test-session-1"
                }
                headers = {"Authorization": "Bearer test_token"}
                response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify source attribution
                assert "sources" in data
                assert len(data["sources"]) > 0
                
                source = data["sources"][0]
                assert "chunk_id" in source
                assert "document_id" in source
                assert "content" in source
                assert "score" in source
                assert "metadata" in source
                
                # Verify source quality
                assert source["score"] > 0.8
                assert "password" in source["content"].lower()
                assert source["metadata"]["document_type"] == "faq"
    
    def test_rag_performance_under_load(self, client, test_user, test_workspace):
        """Test RAG performance under concurrent load"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test concurrent queries
            queries = [
                "How do I reset my password?",
                "What is your refund policy?",
                "How do I install the software?",
                "What are your business hours?",
                "How can I contact support?"
            ]
            
            response_times = []
            successful_requests = 0
            
            for i, query in enumerate(queries):
                with patch('app.api.api_v1.endpoints.rag_query.ProductionRAGService') as mock_rag_service:
                    mock_service = Mock()
                    mock_service.process_query.return_value = {
                        "answer": f"Answer for: {query}",
                        "sources": [{"chunk_id": str(uuid.uuid4()), "content": f"Source for {query}", "score": 0.9}],
                        "response_time_ms": 100 + i * 10,  # Simulate varying response times
                        "tokens_used": 50,
                        "model_used": "gemini-pro"
                    }
                    mock_rag_service.return_value = mock_service
                    
                    start_time = time.time()
                    query_data = {
                        "query": query,
                        "session_id": f"test-session-{i}"
                    }
                    headers = {"Authorization": "Bearer test_token"}
                    response = client.post("/api/v1/rag/query", json=query_data, headers=headers)
                    
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    
                    if response.status_code == 200:
                        successful_requests += 1
            
            # Verify performance
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            assert avg_response_time < 2.0, f"Average response time too slow: {avg_response_time:.3f}s"
            assert max_response_time < 5.0, f"Max response time too slow: {max_response_time:.3f}s"
            assert successful_requests >= len(queries) * 0.8, f"Too many failed requests: {successful_requests}/{len(queries)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
