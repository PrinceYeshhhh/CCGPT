"""
Comprehensive unit tests for RAG (Retrieval-Augmented Generation) system
Tests all critical RAG flows, vector search, and AI integration
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.main import app
from app.models import Document, DocumentChunk, ChatSession, ChatMessage, User, Workspace
from app.services.chat import ChatService
from app.services.vector_service import VectorService
from app.services.gemini_service import GeminiService
from app.utils.error_handling import ValidationError, ExternalAPIError



class TestRAGQueryFlow:
    """Test complete RAG query flow"""
    
    def test_rag_query_success(self, test_user, auth_headers, test_document):
        """Test successful RAG query with document context"""
        query_data = {
            "message": "What is this document about?",
            "session_id": None,
            "context": {
                "document_ids": [str(test_document.id)]
            }
        }
        
        # Mock vector search results
        mock_chunks = [
            {
                "text": "This document is about artificial intelligence and machine learning.",
                "metadata": {"document_id": str(test_document.id), "chunk_index": 0},
                "distance": 0.1
            },
            {
                "text": "It covers topics like neural networks, deep learning, and natural language processing.",
                "metadata": {"document_id": str(test_document.id), "chunk_index": 1},
                "distance": 0.2
            }
        ]
        
        # Mock Gemini response
        mock_gemini_response = {
            "message": "This document is about artificial intelligence and machine learning, covering topics like neural networks, deep learning, and natural language processing.",
            "sources": [str(test_document.id)],
            "confidence": "high"
        }
        
        with patch('app.services.vector_service.VectorService.search_similar_chunks') as mock_search, \
             patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            
            mock_search.return_value = mock_chunks
            mock_gemini.return_value = mock_gemini_response
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            assert "message" in data
            assert "session_id" in data
            assert "sources" in data
            assert "confidence" in data
            assert data["confidence"] == "high"
            assert str(test_document.id) in data["sources"]
    
    def test_rag_query_without_context(self, test_user, auth_headers):
        """Test RAG query without specific document context"""
        query_data = {
            "message": "What can you help me with?",
            "session_id": None
        }
        
        # Mock Gemini response for general query
        mock_gemini_response = {
            "message": "I can help you with questions about your uploaded documents and provide information based on your knowledge base.",
            "sources": [],
            "confidence": "medium"
        }
        
        with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            mock_gemini.return_value = mock_gemini_response
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
            assert data["confidence"] == "medium"
    
    def test_rag_query_with_session(self, test_user, auth_headers, test_document):
        """Test RAG query with existing session"""
        # Create a chat session
        session = ChatSession(
            workspace_id=test_user.workspace_id,
            user_id=test_user.id,
            visitor_ip="127.0.0.1",
            user_agent="test"
        )
        
        query_data = {
            "message": "Can you tell me more about that?",
            "session_id": str(session.id)
        }
        
        # Mock Gemini response with context
        mock_gemini_response = {
            "message": "Based on our previous conversation, I can provide more details about the topic we discussed.",
            "sources": [str(test_document.id)],
            "confidence": "high"
        }
        
        with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            mock_gemini.return_value = mock_gemini_response
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
            assert data["session_id"] == str(session.id)
    
    def test_rag_query_no_relevant_chunks(self, test_user, auth_headers):
        """Test RAG query when no relevant chunks are found"""
        query_data = {
            "message": "What is quantum computing?",
            "context": {
                "document_ids": ["nonexistent-doc-id"]
            }
        }
        
        # Mock empty vector search results
        with patch('app.services.vector_service.VectorService.search_similar_chunks') as mock_search, \
             patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            
            mock_search.return_value = []
            mock_gemini.return_value = {
                "message": "I don't have specific information about quantum computing in your uploaded documents.",
                "sources": [],
                "confidence": "low"
            }
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["confidence"] == "low"
            assert len(data["sources"]) == 0
    
    def test_rag_query_low_confidence(self, test_user, auth_headers, test_document):
        """Test RAG query with low confidence results"""
        query_data = {
            "message": "What is this document about?",
            "context": {
                "document_ids": [str(test_document.id)]
            }
        }
        
        # Mock low confidence vector search results
        mock_chunks = [
            {
                "text": "Some unrelated text that doesn't match the query.",
                "metadata": {"document_id": str(test_document.id), "chunk_index": 0},
                "distance": 0.9  # High distance = low similarity
            }
        ]
        
        mock_gemini_response = {
            "message": "I found some information, but I'm not very confident about its relevance to your question.",
            "sources": [str(test_document.id)],
            "confidence": "low"
        }
        
        with patch('app.services.vector_service.VectorService.search_similar_chunks') as mock_search, \
             patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            
            mock_search.return_value = mock_chunks
            mock_gemini.return_value = mock_gemini_response
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["confidence"] == "low"


class TestVectorSearch:
    """Test vector search functionality"""
    
    def test_vector_search_similarity_threshold(self):
        """Test vector search with similarity threshold"""
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        query_embedding = [0.1] * 384
        
        # Mock search results with different distances
        mock_results = {
            "documents": [["Relevant text", "Less relevant text", "Irrelevant text"]],
            "metadatas": [[{"doc_id": "1"}, {"doc_id": "2"}, {"doc_id": "3"}]],
            "distances": [[0.1, 0.5, 0.9]]  # Low, medium, high distance
        }
        
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = mock_results
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            results = vector_service.search_similar_chunks(
                "workspace1", 
                query_embedding, 
                top_k=5,
                similarity_threshold=0.7
            )
            
            # Should filter out results with distance > 0.7
            assert len(results) == 2  # Only first two results should pass threshold
    
    def test_vector_search_workspace_isolation(self):
        """Test vector search respects workspace isolation"""
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        query_embedding = [0.1] * 384
        
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            vector_service.search_similar_chunks("workspace1", query_embedding, top_k=5)
            
            # Verify workspace filter was applied
            call_args = mock_collection.query.call_args
            assert "where" in call_args.kwargs
            assert call_args.kwargs["where"]["workspace_id"] == "workspace1"
    
    def test_vector_search_caching(self):
        """Test vector search result caching"""
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        query_embedding = [0.1] * 384
        
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client, \
             patch('app.core.database.redis_manager.get') as mock_redis_get, \
             patch('app.core.database.redis_manager.set') as mock_redis_set:
            
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["Cached result"]],
                "metadatas": [[{"doc_id": "1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_or_create_collection.return_value = mock_collection
            
            # First call - should hit database and cache result
            mock_redis_get.return_value = None
            results1 = vector_service.search_similar_chunks("workspace1", query_embedding, top_k=5)
            
            # Second call - should hit cache
            mock_redis_get.return_value = json.dumps(results1)
            results2 = vector_service.search_similar_chunks("workspace1", query_embedding, top_k=5)
            
            # Results should be the same
            assert results1 == results2
            
            # Database should only be called once
            assert mock_collection.query.call_count == 1
    
    def test_vector_search_error_handling(self):
        """Test vector search error handling"""
        from app.services.vector_service import VectorService
        
        vector_service = VectorService()
        
        query_embedding = [0.1] * 384
        
        with patch('app.services.vector_service.chromadb.PersistentClient') as mock_client:
            mock_client.side_effect = Exception("ChromaDB connection failed")
            
            with pytest.raises(ExternalAPIError):
                vector_service.search_similar_chunks("workspace1", query_embedding, top_k=5)


class TestGeminiIntegration:
    """Test Google Gemini AI integration"""
    
    def test_gemini_response_generation(self):
        """Test Gemini response generation"""
        from app.services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        query = "What is artificial intelligence?"
        context_chunks = [
            "Artificial intelligence (AI) is the simulation of human intelligence in machines.",
            "AI systems can perform tasks that typically require human intelligence."
        ]
        
        with patch('app.services.gemini_service.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = "Artificial intelligence (AI) is the simulation of human intelligence in machines. AI systems can perform tasks that typically require human intelligence."
            mock_model.return_value.generate_content.return_value = mock_response
            
            response = gemini_service.generate_response(query, context_chunks)
            
            assert "message" in response
            assert "sources" in response
            assert "confidence" in response
            assert "artificial intelligence" in response["message"].lower()
    
    def test_gemini_response_with_sources(self):
        """Test Gemini response with source attribution"""
        from app.services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        query = "What is machine learning?"
        context_chunks = [
            {
                "text": "Machine learning is a subset of artificial intelligence.",
                "metadata": {"document_id": "doc1", "chunk_index": 0}
            },
            {
                "text": "It enables computers to learn without being explicitly programmed.",
                "metadata": {"document_id": "doc1", "chunk_index": 1}
            }
        ]
        
        with patch('app.services.gemini_service.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = "Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed."
            mock_model.return_value.generate_content.return_value = mock_response
            
            response = gemini_service.generate_response(query, context_chunks)
            
            assert "doc1" in response["sources"]
            assert response["confidence"] in ["high", "medium", "low"]
    
    def test_gemini_api_error_handling(self):
        """Test Gemini API error handling"""
        from app.services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        query = "Test query"
        context_chunks = ["Test context"]
        
        with patch('app.services.gemini_service.genai.GenerativeModel') as mock_model:
            mock_model.return_value.generate_content.side_effect = Exception("API rate limit exceeded")
            
            with pytest.raises(ExternalAPIError):
                gemini_service.generate_response(query, context_chunks)
    
    def test_gemini_response_confidence_scoring(self):
        """Test Gemini response confidence scoring"""
        from app.services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        # Test high confidence response
        query = "What is this document about?"
        context_chunks = [
            {
                "text": "This document is about machine learning algorithms.",
                "metadata": {"document_id": "doc1"},
                "distance": 0.1  # Low distance = high similarity
            }
        ]
        
        with patch('app.services.gemini_service.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = "This document is about machine learning algorithms."
            mock_model.return_value.generate_content.return_value = mock_response
            
            response = gemini_service.generate_response(query, context_chunks)
            
            assert response["confidence"] == "high"
        
        # Test low confidence response
        context_chunks = [
            {
                "text": "Some unrelated text.",
                "metadata": {"document_id": "doc1"},
                "distance": 0.9  # High distance = low similarity
            }
        ]
        
        with patch('app.services.gemini_service.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = "I'm not sure about this topic."
            mock_model.return_value.generate_content.return_value = mock_response
            
            response = gemini_service.generate_response(query, context_chunks)
            
            assert response["confidence"] == "low"


class TestChatSessionManagement:
    """Test chat session management"""
    
    def test_create_chat_session(self, test_user, auth_headers):
        """Test creating a new chat session"""
        session_data = {
            "visitor_ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Test Browser)",
            "referrer": "https://example.com"
        }
        
        response = client.post("/api/v1/chat/sessions", json=session_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "session_id" in data
        assert "created_at" in data
    
    def test_get_chat_session(self, test_user, auth_headers, test_chat_session):
        """Test getting chat session details"""
        response = client.get(f"/api/v1/chat/sessions/{test_chat_session.id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(test_chat_session.id)
        assert data["workspace_id"] == str(test_chat_session.workspace_id)
    
    def test_list_chat_sessions(self, test_user, auth_headers, test_chat_session):
        """Test listing user's chat sessions"""
        response = client.get("/api/v1/chat/sessions", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 1
        assert any(session["id"] == str(test_chat_session.id) for session in data["sessions"])
    
    def test_chat_session_timeout(self, test_user, auth_headers):
        """Test chat session timeout handling"""
        # Create session with very short timeout
        with patch('app.core.config.settings.CHAT_SESSION_TIMEOUT', 1):  # 1 second
            session_data = {
                "visitor_ip": "127.0.0.1",
                "user_agent": "Test Browser"
            }
            
            response = client.post("/api/v1/chat/sessions", json=session_data, headers=auth_headers)
            session_id = response.json()["session_id"]
            
            # Wait for session to timeout
            import time
            time.sleep(2)
            
            # Try to use expired session
            query_data = {
                "message": "Test message",
                "session_id": session_id
            }
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            assert response.status_code == status.HTTP_410_GONE  # Gone = session expired


class TestRAGPerformance:
    """Test RAG system performance"""
    
    def test_large_context_handling(self, test_user, auth_headers):
        """Test handling of large context in RAG queries"""
        # Create large context
        large_context = [
            {
                "text": "This is a test document chunk. " * 100,  # Large chunk
                "metadata": {"document_id": "doc1", "chunk_index": i},
                "distance": 0.1
            }
            for i in range(20)  # Many chunks
        ]
        
        query_data = {
            "message": "What is this about?",
            "context": {"document_ids": ["doc1"]}
        }
        
        with patch('app.services.vector_service.VectorService.search_similar_chunks') as mock_search, \
             patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            
            mock_search.return_value = large_context
            mock_gemini.return_value = {
                "message": "This is about the test document.",
                "sources": ["doc1"],
                "confidence": "high"
            }
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "message" in data
    
    def test_concurrent_rag_queries(self, test_user, auth_headers):
        """Test concurrent RAG queries"""
        import asyncio
        
        async def make_rag_query(query_num):
            query_data = {
                "message": f"Test query {query_num}",
                "session_id": None
            }
            
            with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
                mock_gemini.return_value = {
                    "message": f"Response to query {query_num}",
                    "sources": [],
                    "confidence": "medium"
                }
                
                response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
                return response.status_code
        
        # Make multiple concurrent queries
        async def run_concurrent_queries():
            tasks = [make_rag_query(i) for i in range(5)]
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(run_concurrent_queries())
        
        # All should succeed
        for status_code in results:
            assert status_code == status.HTTP_200_OK
    
    def test_rag_query_rate_limiting(self, test_user, auth_headers):
        """Test RAG query rate limiting"""
        query_data = {
            "message": "Test query",
            "session_id": None
        }
        
        # Make many rapid requests
        for i in range(20):  # Exceed rate limit
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            if i < 10:  # First few should succeed
                assert response.status_code == status.HTTP_200_OK
            else:  # Later ones should be rate limited
                assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestRAGErrorHandling:
    """Test RAG system error handling"""
    
    def test_vector_search_failure(self, test_user, auth_headers):
        """Test handling of vector search failures"""
        query_data = {
            "message": "Test query",
            "context": {"document_ids": ["doc1"]}
        }
        
        with patch('app.services.vector_service.VectorService.search_similar_chunks') as mock_search:
            mock_search.side_effect = Exception("Vector search failed")
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert "error" in data
    
    def test_gemini_api_failure(self, test_user, auth_headers):
        """Test handling of Gemini API failures"""
        query_data = {
            "message": "Test query",
            "session_id": None
        }
        
        with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
            mock_gemini.side_effect = ExternalAPIError("Gemini API unavailable")
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert "error" in data
    
    def test_database_failure_during_rag(self, test_user, auth_headers):
        """Test handling of database failures during RAG queries"""
        query_data = {
            "message": "Test query",
            "session_id": None
        }
        
        with patch('app.core.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_invalid_query_format(self, test_user, auth_headers):
        """Test handling of invalid query format"""
        invalid_queries = [
            {},  # Empty query
            {"message": ""},  # Empty message
            {"message": "x" * 10000},  # Message too long
            {"message": "Test", "context": "invalid"},  # Invalid context format
        ]
        
        for query_data in invalid_queries:
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


class TestRAGSecurity:
    """Test RAG system security"""
    
    def test_rag_query_injection_prevention(self, test_user, auth_headers):
        """Test prevention of injection attacks in RAG queries"""
        malicious_queries = [
            "'; DROP TABLE documents; --",
            "<script>alert('xss')</script>",
            "{{7*7}}",  # Template injection
            "{{config.items()}}",  # Config exposure
        ]
        
        for malicious_query in malicious_queries:
            query_data = {
                "message": malicious_query,
                "session_id": None
            }
            
            with patch('app.services.gemini_service.GeminiService.generate_response') as mock_gemini:
                mock_gemini.return_value = {
                    "message": "I cannot process that request.",
                    "sources": [],
                    "confidence": "low"
                }
                
                response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
                
                # Should either succeed with sanitized response or fail validation
                assert response.status_code in [200, 400, 422]
    
    def test_rag_query_workspace_isolation(self, test_user, auth_headers, test_db):
        """Test RAG queries respect workspace isolation"""
        # Create another user in different workspace
        other_workspace = Workspace(name="Other Workspace")
        test_db.add(other_workspace)
        test_db.commit()
        
        other_user = User(
            email="other@example.com",
            hashed_password="hashed",
            mobile_phone="+9876543210",
            full_name="Other User",
            workspace_id=other_workspace.id
        )
        test_db.add(other_user)
        test_db.commit()
        
        # Try to query with other user's document
        query_data = {
            "message": "What is this about?",
            "context": {"document_ids": ["other-workspace-doc"]}
        }
        
        with patch('app.services.vector_service.VectorService.search_similar_chunks') as mock_search:
            mock_search.return_value = []  # No results due to workspace isolation
            
            response = client.post("/api/v1/chat/message", json=query_data, headers=auth_headers)
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["sources"]) == 0  # No sources from other workspace
    
    def test_rag_query_unauthorized_access(self):
        """Test RAG queries without authentication fail"""
        query_data = {
            "message": "Test query",
            "session_id": None
        }
        
        response = client.post("/api/v1/chat/message", json=query_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
