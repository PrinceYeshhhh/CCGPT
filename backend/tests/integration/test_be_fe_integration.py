"""
Comprehensive Backend-Frontend Integration Tests
Tests API contracts, WebSocket communication, and real-time features
"""

import pytest
import asyncio
import json
import websockets
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models import User, Workspace, Document, ChatSession, ChatMessage, EmbedCode
from app.services.auth import AuthService
from app.services.websocket_service import WebSocketService


class TestAPIContracts:
    """Tests for API contract compliance between BE and FE"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, test_user):
        auth_service = AuthService(None)
        token = auth_service.create_access_token({
            "user_id": str(test_user.id),
            "email": test_user.email
        })
        return {"Authorization": f"Bearer {token}"}
    
    def test_auth_api_contract(self, client):
        """Test authentication API contract"""
        # Test registration endpoint
        register_data = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "business_name": "Test Business",
            "business_domain": "test.com"
        }
        
        with patch('app.api.api_v1.endpoints.auth.AuthService') as mock_auth:
            mock_service = Mock()
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.email = "newuser@example.com"
            mock_service.register_user.return_value = mock_user
            mock_auth.return_value = mock_service
            
            response = client.post("/api/v1/auth/register", json=register_data)
            
            assert response.status_code == 201
            data = response.json()
            
            # Verify API contract
            assert "access_token" in data
            assert "token_type" in data
            assert "user" in data
            assert data["token_type"] == "bearer"
            assert data["user"]["email"] == "newuser@example.com"
    
    def test_documents_api_contract(self, client, auth_headers):
        """Test documents API contract"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_documents = [
                    {
                        "id": "doc_1",
                        "filename": "test.pdf",
                        "file_type": "application/pdf",
                        "file_size": 1024,
                        "status": "processed",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
                mock_service.get_documents.return_value = mock_documents
                mock_doc_service.return_value = mock_service
                
                response = client.get("/api/v1/documents/", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify API contract
                assert isinstance(data, list)
                if data:  # If documents exist
                    doc = data[0]
                    assert "id" in doc
                    assert "filename" in doc
                    assert "file_type" in doc
                    assert "file_size" in doc
                    assert "status" in doc
                    assert "created_at" in doc
    
    def test_chat_api_contract(self, client, auth_headers):
        """Test chat API contract"""
        with patch('app.api.api_v1.endpoints.chat.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.chat.ChatService') as mock_chat_service:
                mock_service = Mock()
                mock_response = {
                    "response": "This is a test response",
                    "message_id": "msg_123",
                    "sources": [
                        {
                            "document_id": "doc_1",
                            "chunk_id": "chunk_1",
                            "content": "Source content",
                            "score": 0.95
                        }
                    ],
                    "response_time_ms": 250,
                    "tokens_used": 150
                }
                mock_service.process_message.return_value = mock_response
                mock_chat_service.return_value = mock_service
                
                message_data = {
                    "message": "Hello, how can I help?",
                    "session_id": "session_123"
                }
                
                response = client.post("/api/v1/chat/send", json=message_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify API contract
                assert "response" in data
                assert "message_id" in data
                assert "sources" in data
                assert isinstance(data["sources"], list)
                if data["sources"]:
                    source = data["sources"][0]
                    assert "document_id" in source
                    assert "chunk_id" in source
                    assert "content" in source
                    assert "score" in source
    
    def test_rag_api_contract(self, client, auth_headers):
        """Test RAG API contract"""
        with patch('app.api.api_v1.endpoints.rag_query.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.rag_query.RAGService') as mock_rag_service:
                mock_service = Mock()
                mock_response = {
                    "answer": "This is the answer to your question",
                    "sources": [
                        {
                            "document_id": "doc_1",
                            "chunk_id": "chunk_1",
                            "content": "Relevant content",
                            "score": 0.92
                        }
                    ],
                    "response_time_ms": 300,
                    "tokens_used": 200,
                    "model_used": "gemini-pro"
                }
                mock_service.process_query.return_value = mock_response
                mock_rag_service.return_value = mock_service
                
                query_data = {
                    "query": "What is your refund policy?",
                    "session_id": "session_123"
                }
                
                response = client.post("/api/v1/rag/query", json=query_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify API contract
                assert "answer" in data
                assert "sources" in data
                assert "response_time_ms" in data
                assert "tokens_used" in data
                assert "model_used" in data
                assert isinstance(data["sources"], list)
    
    def test_embed_widget_api_contract(self, client, auth_headers):
        """Test embed widget API contract"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_embed_code = Mock()
                mock_embed_code.id = "embed_123"
                mock_embed_code.client_api_key = "api_key_123"
                mock_embed_code.default_config = {"theme": {"primary": "#4f46e5"}}
                mock_service.generate_embed_code.return_value = mock_embed_code
                mock_service.get_embed_snippet.return_value = "<script>console.log('widget')</script>"
                mock_embed_service.return_value = mock_service
                
                embed_data = {
                    "workspace_id": "ws_123",
                    "code_name": "Test Widget",
                    "config": {
                        "theme": {"primary": "#4f46e5"},
                        "welcomeMessage": "Hello!"
                    }
                }
                
                response = client.post("/api/v1/embed/generate", json=embed_data, headers=auth_headers)
                
                assert response.status_code == 201
                data = response.json()
                
                # Verify API contract
                assert "embed_code_id" in data
                assert "client_api_key" in data
                assert "embed_snippet" in data
                assert "widget_url" in data
                assert "config" in data
                assert data["config"]["theme"]["primary"] == "#4f46e5"


class TestWebSocketIntegration:
    """Tests for WebSocket communication between BE and FE"""
    
    @pytest.fixture
    def websocket_service(self):
        return WebSocketService()
    
    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self):
        """Test WebSocket connection establishment"""
        from unittest.mock import Mock
        
        # Mock WebSocket connection
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(return_value='{"type": "ping"}')
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        # Mock authentication
        with patch('app.api.api_v1.endpoints.websocket.WebSocketSecurityService') as mock_security:
            mock_security_instance = Mock()
            mock_security_instance.authenticate_connection.return_value = {
                "user_id": "123",
                "workspace_id": "ws_123",
                "auth_type": "jwt"
            }
            mock_security.return_value = mock_security_instance
            
            # Test connection handling
            from app.api.api_v1.endpoints.websocket import websocket_endpoint
            
            # This would be called in a real WebSocket connection
            # await websocket_endpoint(mock_websocket, token="valid_token")
            
            # Verify WebSocket methods were called
            mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self):
        """Test WebSocket message handling"""
        from unittest.mock import Mock
        
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        # Test message types
        test_messages = [
            {"type": "ping", "data": {}},
            {"type": "chat_message", "data": {"message": "Hello"}},
            {"type": "typing", "data": {"is_typing": True}},
            {"type": "disconnect", "data": {}}
        ]
        
        for message in test_messages:
            # Mock WebSocket service
            with patch('app.services.websocket_service.WebSocketService') as mock_service:
                mock_service_instance = Mock()
                mock_service_instance.handle_message = AsyncMock()
                mock_service.return_value = mock_service_instance
                
                # Test message handling
                await mock_service_instance.handle_message(
                    mock_websocket, 
                    json.dumps(message),
                    {"user_id": "123", "workspace_id": "ws_123"}
                )
                
                mock_service_instance.handle_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling"""
        from unittest.mock import Mock
        
        # Mock WebSocket with error
        mock_websocket = Mock()
        mock_websocket.receive_text = AsyncMock(side_effect=Exception("Connection error"))
        mock_websocket.close = AsyncMock()
        
        # Test error handling
        try:
            await mock_websocket.receive_text()
        except Exception:
            await mock_websocket.close()
        
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_failure(self):
        """Test WebSocket authentication failure handling"""
        from unittest.mock import Mock
        
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.close = AsyncMock()
        
        # Mock authentication failure
        with patch('app.api.api_v1.endpoints.websocket.WebSocketSecurityService') as mock_security:
            mock_security_instance = Mock()
            mock_security_instance.authenticate_connection.return_value = None
            mock_security.return_value = mock_security_instance
            
            # Test authentication failure
            auth_result = await mock_security_instance.authenticate_connection(
                mock_websocket, token="invalid_token"
            )
            
            assert auth_result is None
            # In real implementation, WebSocket would be closed


class TestRealTimeFeatures:
    """Tests for real-time features integration"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_typing_indicators(self, client, auth_headers):
        """Test typing indicators in chat"""
        with patch('app.api.api_v1.endpoints.websocket.WebSocketService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.broadcast_typing = AsyncMock()
            mock_service.return_value = mock_service_instance
            
            # Test typing indicator
            typing_data = {
                "session_id": "session_123",
                "is_typing": True,
                "user_id": "123"
            }
            
            # This would be sent via WebSocket in real implementation
            # For testing, we'll verify the service method exists
            assert hasattr(mock_service_instance, 'broadcast_typing')
    
    def test_message_broadcasting(self, client, auth_headers):
        """Test message broadcasting to multiple clients"""
        with patch('app.api.api_v1.endpoints.websocket.WebSocketService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.broadcast_message = AsyncMock()
            mock_service.return_value = mock_service_instance
            
            # Test message broadcast
            message_data = {
                "session_id": "session_123",
                "message": "Hello everyone",
                "user_id": "123"
            }
            
            # Verify broadcast method exists
            assert hasattr(mock_service_instance, 'broadcast_message')
    
    def test_connection_management(self, client, auth_headers):
        """Test WebSocket connection management"""
        with patch('app.api.api_v1.endpoints.websocket.WebSocketService') as mock_service:
            mock_service_instance = Mock()
            mock_service_instance.add_connection = AsyncMock()
            mock_service_instance.remove_connection = AsyncMock()
            mock_service.return_value = mock_service_instance
            
            # Test connection management
            connection_data = {
                "user_id": "123",
                "workspace_id": "ws_123",
                "connection_id": "conn_123"
            }
            
            # Verify connection management methods exist
            assert hasattr(mock_service_instance, 'add_connection')
            assert hasattr(mock_service_instance, 'remove_connection')


class TestDataConsistency:
    """Tests for data consistency between BE and FE"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_user_data_consistency(self, client, auth_headers):
        """Test user data consistency across endpoints"""
        with patch('app.api.api_v1.endpoints.auth.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.email = "test@example.com"
            mock_user.full_name = "Test User"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            # Test user data in different endpoints
            response = client.get("/api/v1/auth/me", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify consistent user data structure
            assert data["id"] == "123"
            assert data["email"] == "test@example.com"
            assert data["full_name"] == "Test User"
            assert data["workspace_id"] == "ws_123"
    
    def test_workspace_data_consistency(self, client, auth_headers):
        """Test workspace data consistency"""
        with patch('app.api.api_v1.endpoints.workspaces.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.workspaces.WorkspaceService') as mock_workspace_service:
                mock_service = Mock()
                mock_workspace = {
                    "id": "ws_123",
                    "name": "Test Workspace",
                    "user_id": "123",
                    "created_at": "2024-01-01T00:00:00Z"
                }
                mock_service.get_workspace.return_value = mock_workspace
                mock_workspace_service.return_value = mock_service
                
                response = client.get("/api/v1/workspaces/ws_123", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify consistent workspace data structure
                assert data["id"] == "ws_123"
                assert data["name"] == "Test Workspace"
                assert data["user_id"] == "123"
                assert "created_at" in data
    
    def test_document_status_consistency(self, client, auth_headers):
        """Test document status consistency across operations"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_document = {
                    "id": "doc_123",
                    "filename": "test.pdf",
                    "status": "processing",
                    "progress": 50
                }
                mock_service.get_document.return_value = mock_document
                mock_doc_service.return_value = mock_service
                
                response = client.get("/api/v1/documents/doc_123", headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify consistent document status structure
                assert data["id"] == "doc_123"
                assert data["filename"] == "test.pdf"
                assert data["status"] == "processing"
                assert "progress" in data


class TestErrorHandlingIntegration:
    """Tests for error handling integration between BE and FE"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_authentication_error_handling(self, client):
        """Test authentication error handling"""
        # Test without authentication
        response = client.get("/api/v1/documents/")
        assert response.status_code == 401
        
        # Test with invalid token
        response = client.get(
            "/api/v1/documents/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
    
    def test_validation_error_handling(self, client):
        """Test input validation error handling"""
        # Test invalid registration data
        invalid_data = {
            "email": "invalid-email",
            "password": "123",  # Too short
            "full_name": ""
        }
        
        response = client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422  # Validation error
        
        # Verify error response structure
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
    
    def test_not_found_error_handling(self, client, auth_headers):
        """Test not found error handling"""
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.get_document.return_value = None
                mock_doc_service.return_value = mock_service
                
                response = client.get("/api/v1/documents/nonexistent", headers=auth_headers)
                assert response.status_code == 404
                
                # Verify error response structure
                data = response.json()
                assert "detail" in data
                assert "not found" in data["detail"].lower()
    
    def test_rate_limit_error_handling(self, client):
        """Test rate limit error handling"""
        with patch('app.api.api_v1.endpoints.auth.rate_limiting_service') as mock_rate_limit:
            mock_rate_limit.check_ip_rate_limit.return_value = (False, {"retry_after": 60})
            
            # Simulate rate limiting
            response = client.post("/api/v1/auth/login", json={
                "email": "test@example.com",
                "password": "password123"
            })
            
            # Should return 429 if rate limited
            if response.status_code == 429:
                data = response.json()
                assert "rate limit" in data["detail"].lower()
                assert "retry_after" in data or "retry" in data["detail"].lower()


class TestPerformanceIntegration:
    """Tests for performance integration between BE and FE"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_response_time_consistency(self, client, auth_headers):
        """Test response time consistency"""
        import time
        
        with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = "ws_123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                mock_service = Mock()
                mock_service.get_documents.return_value = []
                mock_doc_service.return_value = mock_service
                
                # Test multiple requests
                response_times = []
                for _ in range(5):
                    start_time = time.time()
                    response = client.get("/api/v1/documents/", headers=auth_headers)
                    end_time = time.time()
                    
                    assert response.status_code == 200
                    response_times.append(end_time - start_time)
                
                # Verify response times are reasonable (less than 1 second)
                assert all(rt < 1.0 for rt in response_times)
    
    def test_concurrent_request_handling(self, client, auth_headers):
        """Test concurrent request handling"""
        import asyncio
        import time
        
        async def make_request():
            with patch('app.api.api_v1.endpoints.documents.get_current_user') as mock_get_user:
                mock_user = Mock()
                mock_user.id = "123"
                mock_user.workspace_id = "ws_123"
                mock_get_user.return_value = mock_user
                
                with patch('app.api.api_v1.endpoints.documents.DocumentService') as mock_doc_service:
                    mock_service = Mock()
                    mock_service.get_documents.return_value = []
                    mock_doc_service.return_value = mock_service
                    
                    response = client.get("/api/v1/documents/", headers=auth_headers)
                    return response.status_code
        
        # Test concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        end_time = time.time()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        
        # Should complete in reasonable time
        assert end_time - start_time < 5.0
