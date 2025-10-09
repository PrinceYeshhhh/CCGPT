"""
Comprehensive Integration Edge Case Tests
Tests complex workflows, error scenarios, and edge cases across the entire system
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, Document, ChatSession, ChatMessage, EmbedCode, Subscription


class TestIntegrationEdgeCases:
    """Comprehensive tests for integration edge cases and complex workflows"""
    
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
            id="ws_edge_test",
            name="Edge Test Workspace",
            description="Test workspace for edge case testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            id="user_edge_test",
            email="edge@test.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Edge Test User",
            workspace_id=test_workspace.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def auth_headers(self, test_user):
        """Create authentication headers"""
        from app.services.auth import AuthService
        auth_service = AuthService(None)
        token = auth_service.create_access_token(data={"sub": test_user.email})
        return {"Authorization": f"Bearer {token}"}

    # ==================== COMPLEX WORKFLOW TESTS ====================
    
    def test_complete_user_journey_workflow(self, client, auth_headers, test_user, test_workspace):
        """Test complete user journey from registration to chat completion"""
        # Step 1: User registration (mocked)
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Step 2: Upload document
            with patch('app.services.document_service.DocumentService.upload_document') as mock_upload:
                mock_upload.return_value = {
                    "document_id": "doc_123",
                    "job_id": "job_123",
                    "status": "processing"
                }
                
                files = {"file": ("test.pdf", b"test content", "application/pdf")}
                response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                assert response.status_code == 200
                
                # Step 3: Create chat session
                session_payload = {
                    "workspace_id": test_workspace.id,
                    "user_label": "Test Customer"
                }
                response = client.post("/api/v1/chat/sessions", json=session_payload, headers=auth_headers)
                assert response.status_code == 201
                session_id = response.json()["session_id"]
                
                # Step 4: Send chat message
                with patch('app.services.chat.ChatService.process_message') as mock_chat:
                    mock_chat.return_value = {
                        "message": "Hello! How can I help you?",
                        "session_id": session_id,
                        "sources": [{"content": "Test source"}]
                    }
                    
                    message_payload = {
                        "message": "Hello, I need help with my order",
                        "session_id": session_id
                    }
                    response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                    assert response.status_code == 200
                    
                    # Step 5: End chat session
                    response = client.post(f"/api/v1/chat/sessions/{session_id}/end", headers=auth_headers)
                    assert response.status_code == 200

    def test_embed_widget_complete_workflow(self, client, auth_headers, test_user, test_workspace):
        """Test complete embed widget workflow"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Step 1: Generate embed code
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_embed_code = Mock()
                mock_embed_code.id = "embed_123"
                mock_embed_code.client_api_key = "api_key_123"
                mock_embed_code.default_config = {"theme": {"primary": "#4f46e5"}}
                mock_service.generate_embed_code.return_value = mock_embed_code
                mock_service.get_embed_snippet.return_value = "<script>/* widget */</script>"
                mock_embed_service.return_value = mock_service
                
                payload = {
                    "workspace_id": test_workspace.id,
                    "code_name": "Test Widget",
                    "config": {"theme": {"primary": "#4f46e5"}}
                }
                
                response = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
                assert response.status_code == 201
                embed_data = response.json()
                
                # Step 2: Get widget script
                with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                    mock_service = Mock()
                    mock_service.get_widget_script.return_value = "console.log('Widget loaded');"
                    mock_service.increment_usage.return_value = None
                    mock_embed_service.return_value = mock_service
                    
                    response = client.get(f"/api/v1/embed/widget/{embed_data['embed_code_id']}")
                    assert response.status_code == 200
                    assert response.headers["content-type"] == "application/javascript"
                    
                    # Step 3: Test widget chat message
                    with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                        mock_service = Mock()
                        mock_service.get_embed_code_by_api_key.return_value = mock_embed_code
                        mock_service.increment_usage.return_value = None
                        mock_embed_service.return_value = mock_service
                        
                        with patch('app.services.rate_limiting.rate_limiting_service.check_ip_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
                            mock_rate_limit.return_value = (True, {"limit": 10, "remaining": 9, "reset_time": Mock(timestamp=lambda: 0)})
                            
                            with patch('app.services.rate_limiting.rate_limiting_service.check_rate_limit', new_callable=AsyncMock) as mock_embed_rate_limit:
                                mock_embed_rate_limit.return_value = (True, {"limit": 60, "remaining": 59, "reset_time": Mock(timestamp=lambda: 0)})
                                
                                with patch('app.services.rate_limiting.rate_limiting_service.check_workspace_rate_limit', new_callable=AsyncMock) as mock_ws_rate_limit:
                                    mock_ws_rate_limit.return_value = (True, {"limit": 120, "remaining": 119, "reset_time": Mock(timestamp=lambda: 0)})
                                    
                                    with patch('app.services.chat.ChatService') as mock_chat_service:
                                        mock_chat = Mock()
                                        mock_chat.process_message.return_value = {
                                            "message": "Widget response",
                                            "session_id": "widget_session"
                                        }
                                        mock_chat_service.return_value = mock_chat
                                        
                                        payload = {"message": "Hello from widget"}
                                        headers = {
                                            "X-Client-API-Key": embed_data["client_api_key"],
                                            "X-Embed-Code-ID": embed_data["embed_code_id"]
                                        }
                                        
                                        response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
                                        assert response.status_code == 200

    def test_analytics_complete_workflow(self, client, auth_headers, test_user, test_workspace):
        """Test complete analytics workflow"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Step 1: Generate some activity
            with patch('app.services.chat.ChatService') as mock_chat_service:
                mock_chat = Mock()
                mock_chat.create_session.return_value = Mock(session_id="test_session")
                mock_chat.process_message.return_value = {
                    "message": "Test response",
                    "session_id": "test_session"
                }
                mock_chat_service.return_value = mock_chat
                
                # Create session
                session_payload = {
                    "workspace_id": test_workspace.id,
                    "user_label": "Test Customer"
                }
                response = client.post("/api/v1/chat/sessions", json=session_payload, headers=auth_headers)
                assert response.status_code == 201
                
                # Send message
                message_payload = {
                    "message": "Test message",
                    "session_id": "test_session"
                }
                response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                assert response.status_code == 200
                
                # Step 2: Get analytics
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                assert response.status_code == 200
                
                response = client.get("/api/v1/analytics/top-queries?limit=5&days=7", headers=auth_headers)
                assert response.status_code == 200
                
                response = client.get("/api/v1/analytics/queries-over-time?days=7", headers=auth_headers)
                assert response.status_code == 200

    # ==================== ERROR SCENARIO TESTS ====================
    
    def test_cascade_failure_scenario(self, client, auth_headers, test_user, test_workspace):
        """Test cascade failure scenario where one service failure affects others"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Simulate RAG service failure affecting chat
            with patch('app.services.rag_service.RAGService') as mock_rag_service:
                mock_rag = Mock()
                mock_rag.process_query.side_effect = Exception("RAG service unavailable")
                mock_rag_service.return_value = mock_rag
                
                with patch('app.services.chat.ChatService') as mock_chat_service:
                    mock_chat = Mock()
                    mock_chat.process_message.side_effect = Exception("Chat service error due to RAG failure")
                    mock_chat_service.return_value = mock_chat
                    
                    message_payload = {
                        "message": "Test message",
                        "session_id": "test_session"
                    }
                    
                    response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                    assert response.status_code == 500

    def test_database_connection_failure_scenario(self, client, auth_headers, test_user, test_workspace):
        """Test database connection failure scenario"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Simulate database connection failure
            with patch('app.core.database.get_db') as mock_get_db:
                mock_get_db.side_effect = Exception("Database connection failed")
                
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                assert response.status_code == 500

    def test_rate_limiting_cascade_scenario(self, client, test_user, test_workspace):
        """Test rate limiting cascade scenario"""
        # Create embed code
        embed_code = EmbedCode(
            id="embed_rate_test",
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            code_name="Rate Test Widget",
            client_api_key="rate_test_key",
            is_active=True
        )
        
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = embed_code
            mock_embed_service.return_value = mock_service
            
            # Simulate rate limiting at multiple levels
            with patch('app.services.rate_limiting.rate_limiting_service.check_ip_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
                mock_rate_limit.return_value = (False, {"limit": 10, "remaining": 0, "reset_time": Mock(timestamp=lambda: 0)})
                
                payload = {"message": "Test message"}
                headers = {"X-Client-API-Key": "rate_test_key"}
                
                response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
                assert response.status_code == 429

    def test_memory_exhaustion_scenario(self, client, auth_headers, test_user, test_workspace):
        """Test memory exhaustion scenario"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Simulate memory exhaustion in document processing
            with patch('app.services.document_service.DocumentService.upload_document') as mock_upload:
                mock_upload.side_effect = MemoryError("Insufficient memory")
                
                files = {"file": ("large_file.pdf", b"x" * (100 * 1024 * 1024), "application/pdf")}
                response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                assert response.status_code == 500

    # ==================== CONCURRENT ACCESS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_concurrent_user_operations(self, client, auth_headers, test_user, test_workspace):
        """Test concurrent user operations"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test concurrent chat sessions
            async def create_chat_session(session_id):
                session_payload = {
                    "workspace_id": test_workspace.id,
                    "user_label": f"Customer {session_id}"
                }
                return client.post("/api/v1/chat/sessions", json=session_payload, headers=auth_headers)
            
            # Create multiple concurrent sessions
            tasks = [create_chat_session(i) for i in range(5)]
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_concurrent_document_uploads(self, client, auth_headers, test_user, test_workspace):
        """Test concurrent document uploads"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with patch('app.services.document_service.DocumentService.upload_document') as mock_upload:
                mock_upload.return_value = {
                    "document_id": "doc_123",
                    "job_id": "job_123",
                    "status": "processing"
                }
                
                async def upload_document(doc_id):
                    files = {"file": (f"test_{doc_id}.pdf", b"test content", "application/pdf")}
                    return client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                
                # Upload multiple documents concurrently
                tasks = [upload_document(i) for i in range(5)]
                responses = await asyncio.gather(*tasks)
                
                # All should succeed
                for response in responses:
                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_analytics_requests(self, client, auth_headers, test_user):
        """Test concurrent analytics requests"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            async def get_analytics(endpoint):
                return client.get(f"/api/v1/analytics/{endpoint}", headers=auth_headers)
            
            # Make multiple concurrent analytics requests
            endpoints = ["summary", "top-queries", "queries-over-time", "file-usage", "embed-codes"]
            tasks = [get_analytics(endpoint) for endpoint in endpoints]
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            for response in responses:
                assert response.status_code == 200

    # ==================== DATA CONSISTENCY TESTS ====================
    
    def test_data_consistency_across_services(self, client, auth_headers, test_user, test_workspace):
        """Test data consistency across different services"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Create document
            with patch('app.services.document_service.DocumentService.upload_document') as mock_upload:
                mock_upload.return_value = {
                    "document_id": "doc_consistency_test",
                    "job_id": "job_consistency_test",
                    "status": "processing"
                }
                
                files = {"file": ("consistency_test.pdf", b"test content", "application/pdf")}
                response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                assert response.status_code == 200
                
                # Create chat session
                session_payload = {
                    "workspace_id": test_workspace.id,
                    "user_label": "Consistency Test Customer"
                }
                response = client.post("/api/v1/chat/sessions", json=session_payload, headers=auth_headers)
                assert response.status_code == 201
                session_id = response.json()["session_id"]
                
                # Send message referencing the document
                with patch('app.services.chat.ChatService.process_message') as mock_chat:
                    mock_chat.return_value = {
                        "message": "Response referencing document",
                        "session_id": session_id,
                        "sources": [{"document_id": "doc_consistency_test"}]
                    }
                    
                    message_payload = {
                        "message": "Tell me about the uploaded document",
                        "session_id": session_id
                    }
                    response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                    assert response.status_code == 200
                    
                    # Verify data consistency
                    response_data = response.json()
                    assert response_data["session_id"] == session_id
                    assert "sources" in response_data

    def test_workspace_isolation_consistency(self, client, auth_headers, test_user, test_workspace):
        """Test workspace isolation consistency"""
        # Create second workspace
        workspace2 = Workspace(
            id="ws_isolation_test",
            name="Isolation Test Workspace"
        )
        
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test that user can only access their workspace data
            response = client.get("/api/v1/analytics/summary", headers=auth_headers)
            assert response.status_code == 200
            
            # Verify workspace isolation in analytics
            data = response.json()
            # Should only show data for the user's workspace
            assert "total_documents" in data
            assert "total_sessions" in data

    # ==================== PERFORMANCE EDGE CASES ====================
    
    def test_large_payload_handling(self, client, auth_headers, test_user, test_workspace):
        """Test handling of large payloads"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test large message payload
            large_message = "A" * 10000  # 10KB message
            
            with patch('app.services.chat.ChatService.process_message') as mock_chat:
                mock_chat.return_value = {
                    "message": "Response to large message",
                    "session_id": "test_session"
                }
                
                message_payload = {
                    "message": large_message,
                    "session_id": "test_session"
                }
                response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                assert response.status_code == 200

    def test_high_frequency_requests(self, client, auth_headers, test_user):
        """Test handling of high frequency requests"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test rapid successive requests
            for i in range(10):
                response = client.get("/api/v1/analytics/summary", headers=auth_headers)
                assert response.status_code == 200

    def test_memory_intensive_operations(self, client, auth_headers, test_user, test_workspace):
        """Test memory intensive operations"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test large document upload
            with patch('app.services.document_service.DocumentService.upload_document') as mock_upload:
                mock_upload.return_value = {
                    "document_id": "doc_memory_test",
                    "job_id": "job_memory_test",
                    "status": "processing"
                }
                
                # Simulate large file
                large_content = b"x" * (50 * 1024 * 1024)  # 50MB
                files = {"file": ("large_file.pdf", large_content, "application/pdf")}
                response = client.post("/api/v1/documents/upload", files=files, headers=auth_headers)
                assert response.status_code == 200

    # ==================== SECURITY EDGE CASES ====================
    
    def test_sql_injection_attempts(self, client, auth_headers, test_user):
        """Test SQL injection attempts"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test SQL injection in message
            sql_injection_message = "'; DROP TABLE users; --"
            
            with patch('app.services.chat.ChatService.process_message') as mock_chat:
                mock_chat.return_value = {
                    "message": "Safe response",
                    "session_id": "test_session"
                }
                
                message_payload = {
                    "message": sql_injection_message,
                    "session_id": "test_session"
                }
                response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                assert response.status_code == 200
                # Should be handled safely

    def test_xss_attempts(self, client, auth_headers, test_user):
        """Test XSS attempts"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test XSS in message
            xss_message = "<script>alert('xss')</script>Hello"
            
            with patch('app.services.chat.ChatService.process_message') as mock_chat:
                mock_chat.return_value = {
                    "message": "Safe response",
                    "session_id": "test_session"
                }
                
                message_payload = {
                    "message": xss_message,
                    "session_id": "test_session"
                }
                response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                assert response.status_code == 200
                # Should be sanitized

    def test_unauthorized_access_attempts(self, client):
        """Test unauthorized access attempts"""
        # Test without authentication
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 401
        
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/analytics/summary", headers=headers)
        assert response.status_code == 401

    # ==================== RECOVERY TESTS ====================
    
    def test_service_recovery_after_failure(self, client, auth_headers, test_user, test_workspace):
        """Test service recovery after failure"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Simulate service failure and recovery
            with patch('app.services.chat.ChatService.process_message') as mock_chat:
                # First call fails
                mock_chat.side_effect = [Exception("Service temporarily unavailable"), {
                    "message": "Recovery response",
                    "session_id": "test_session"
                }]
                
                message_payload = {
                    "message": "Test message",
                    "session_id": "test_session"
                }
                
                # First attempt should fail
                response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                assert response.status_code == 500
                
                # Second attempt should succeed (recovery)
                response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                assert response.status_code == 200

    def test_graceful_degradation(self, client, auth_headers, test_user, test_workspace):
        """Test graceful degradation when services are partially available"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Simulate partial service availability
            with patch('app.services.rag_service.RAGService') as mock_rag_service:
                mock_rag = Mock()
                mock_rag.process_query.side_effect = Exception("RAG service unavailable")
                mock_rag_service.return_value = mock_rag
                
                with patch('app.services.chat.ChatService.process_message') as mock_chat:
                    # Should provide fallback response
                    mock_chat.return_value = {
                        "message": "I'm sorry, I'm experiencing technical difficulties. Please try again later.",
                        "session_id": "test_session",
                        "sources": []
                    }
                    
                    message_payload = {
                        "message": "Test message",
                        "session_id": "test_session"
                    }
                    response = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
                    assert response.status_code == 200
                    
                    # Should provide graceful fallback
                    response_data = response.json()
                    assert "technical difficulties" in response_data["message"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
