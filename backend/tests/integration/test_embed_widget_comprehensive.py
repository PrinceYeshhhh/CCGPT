"""
Comprehensive Embed Widget Integration Tests
Tests all embed widget functionality including security, rate limiting, and edge cases
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
from app.models import User, Workspace, EmbedCode, Subscription
from app.services.auth import AuthService
from app.services.embed_service import EmbedService
from app.services.rate_limiting import rate_limiting_service


class TestEmbedWidgetComprehensive:
    """Comprehensive tests for embed widget functionality"""
    
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
            id="ws_embed_test",
            name="Embed Test Workspace",
            description="Test workspace for embed widget testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            id="user_embed_test",
            email="embed@test.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Embed Test User",
            workspace_id=test_workspace.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_subscription(self, db_session, test_workspace):
        """Create test subscription"""
        subscription = Subscription(
            workspace_id=test_workspace.id,
            tier="pro",
            status="active",
            monthly_query_quota=1000,
            document_limit=100
        )
        db_session.add(subscription)
        db_session.commit()
        db_session.refresh(subscription)
        return subscription
    
    @pytest.fixture
    def auth_headers(self, test_user):
        """Create authentication headers"""
        auth_service = AuthService(None)
        token = auth_service.create_access_token(data={"sub": test_user.email})
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def test_embed_code(self, db_session, test_user, test_workspace):
        """Create test embed code"""
        embed_code = EmbedCode(
            id="embed_test_123",
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            code_name="Test Widget",
            client_api_key="test_api_key_123",
            is_active=True,
            default_config={"theme": {"primary": "#4f46e5"}},
            usage_count=0
        )
        db_session.add(embed_code)
        db_session.commit()
        db_session.refresh(embed_code)
        return embed_code

    # ==================== EMBED CODE GENERATION TESTS ====================
    
    def test_generate_embed_code_success(self, client, auth_headers, test_workspace):
        """Test successful embed code generation"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test", workspace_id=test_workspace.id)
            
            payload = {
                "workspace_id": test_workspace.id,
                "code_name": "Test Widget",
                "config": {"theme": {"primary": "#4f46e5"}},
                "snippet_template": "default"
            }
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_embed_code = Mock()
                mock_embed_code.id = "embed_123"
                mock_embed_code.client_api_key = "api_key_123"
                mock_embed_code.default_config = {"theme": {"primary": "#4f46e5"}}
                mock_service.generate_embed_code.return_value = mock_embed_code
                mock_service.get_embed_snippet.return_value = "<script>/* widget */</script>"
                mock_embed_service.return_value = mock_service
                
                response = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
                
                assert response.status_code == 201
                data = response.json()
                assert "embed_code_id" in data
                assert "client_api_key" in data
                assert "embed_snippet" in data
                assert "widget_url" in data
                assert "config" in data

    def test_generate_embed_code_validation_errors(self, client, auth_headers):
        """Test embed code generation with validation errors"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test", workspace_id="ws_test")
            
            # Test missing required fields
            payload = {"code_name": "Test Widget"}
            response = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
            assert response.status_code == 422  # Validation error
            
            # Test invalid config format
            payload = {
                "workspace_id": "ws_test",
                "code_name": "Test Widget",
                "config": "invalid_config"
            }
            response = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
            assert response.status_code == 422

    def test_generate_embed_code_service_failure(self, client, auth_headers, test_workspace):
        """Test embed code generation when service fails"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test", workspace_id=test_workspace.id)
            
            payload = {
                "workspace_id": test_workspace.id,
                "code_name": "Test Widget",
                "config": {"theme": {"primary": "#4f46e5"}}
            }
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.generate_embed_code.side_effect = Exception("Service error")
                mock_embed_service.return_value = mock_service
                
                response = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
                assert response.status_code == 500
                assert "Failed to generate embed code" in response.json()["detail"]

    # ==================== EMBED CODE MANAGEMENT TESTS ====================
    
    def test_get_embed_codes_success(self, client, auth_headers, test_embed_code):
        """Test successful retrieval of embed codes"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test")
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.get_user_embed_codes.return_value = [test_embed_code]
                mock_embed_service.return_value = mock_service
                
                response = client.get("/api/v1/embed/codes", headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) == 1
                assert data[0]["id"] == str(test_embed_code.id)

    def test_get_embed_code_by_id_success(self, client, auth_headers, test_embed_code):
        """Test successful retrieval of specific embed code"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test")
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.get_embed_code_by_id.return_value = test_embed_code
                mock_embed_service.return_value = mock_service
                
                response = client.get(f"/api/v1/embed/codes/{test_embed_code.id}", headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert data["id"] == str(test_embed_code.id)

    def test_get_embed_code_by_id_not_found(self, client, auth_headers):
        """Test retrieval of non-existent embed code"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test")
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.get_embed_code_by_id.return_value = None
                mock_embed_service.return_value = mock_service
                
                response = client.get("/api/v1/embed/codes/non_existent", headers=auth_headers)
                assert response.status_code == 404
                assert "Embed code not found" in response.json()["detail"]

    def test_update_embed_code_success(self, client, auth_headers, test_embed_code):
        """Test successful embed code update"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test")
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                updated_embed_code = test_embed_code
                updated_embed_code.code_name = "Updated Widget"
                mock_service.update_embed_code.return_value = updated_embed_code
                mock_embed_service.return_value = mock_service
                
                payload = {
                    "code_name": "Updated Widget",
                    "widget_config": {"theme": {"primary": "#ff0000"}}
                }
                
                response = client.put(f"/api/v1/embed/codes/{test_embed_code.id}", json=payload, headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert data["code_name"] == "Updated Widget"

    def test_delete_embed_code_success(self, client, auth_headers, test_embed_code):
        """Test successful embed code deletion"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test")
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.delete_embed_code.return_value = True
                mock_embed_service.return_value = mock_service
                
                response = client.delete(f"/api/v1/embed/codes/{test_embed_code.id}", headers=auth_headers)
                assert response.status_code == 200
                assert "deleted successfully" in response.json()["message"]

    def test_regenerate_embed_code_success(self, client, auth_headers, test_embed_code):
        """Test successful embed code regeneration"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test")
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.regenerate_embed_code.return_value = test_embed_code
                mock_embed_service.return_value = mock_service
                
                response = client.post(f"/api/v1/embed/codes/{test_embed_code.id}/regenerate", headers=auth_headers)
                assert response.status_code == 200
                assert "regenerated successfully" in response.json()["message"]

    # ==================== WIDGET SCRIPT TESTS ====================
    
    def test_get_widget_script_success(self, client, test_embed_code):
        """Test successful widget script retrieval"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_widget_script.return_value = "console.log('Widget loaded');"
            mock_service.increment_usage.return_value = None
            mock_embed_service.return_value = mock_service
            
            response = client.get(f"/api/v1/embed/widget/{test_embed_code.id}")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/javascript"
            assert "console.log('Widget loaded');" in response.text

    def test_get_widget_script_not_found(self, client):
        """Test widget script retrieval for non-existent embed code"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_widget_script.return_value = None
            mock_embed_service.return_value = mock_service
            
            response = client.get("/api/v1/embed/widget/non_existent")
            assert response.status_code == 404
            assert "Embed code not found or inactive" in response.json()["detail"]

    # ==================== WIDGET PREVIEW TESTS ====================
    
    def test_preview_widget_success(self, client, auth_headers):
        """Test successful widget preview generation"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test")
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service._generate_embed_script.return_value = "console.log('Preview');"
                mock_service._generate_embed_html.return_value = "<div>Preview HTML</div>"
                mock_embed_service.return_value = mock_service
                
                payload = {
                    "config": {
                        "primary_color": "#ff0000",
                        "secondary_color": "#00ff00",
                        "text_color": "#000000"
                    }
                }
                
                response = client.post("/api/v1/embed/preview", json=payload, headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert "preview_html" in data
                assert "preview_css" in data
                assert "preview_js" in data

    # ==================== WIDGET CHAT MESSAGE TESTS ====================
    
    def test_widget_chat_message_success(self, client, test_embed_code):
        """Test successful widget chat message processing"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
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
                                "message": "Test response",
                                "session_id": "test_session"
                            }
                            mock_chat_service.return_value = mock_chat
                            
                            payload = {"message": "Hello, how can I help?"}
                            headers = {
                                "X-Client-API-Key": test_embed_code.client_api_key,
                                "X-Embed-Code-ID": str(test_embed_code.id)
                            }
                            
                            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
                            assert response.status_code == 200

    def test_widget_chat_message_missing_api_key(self, client):
        """Test widget chat message without API key"""
        payload = {"message": "Hello"}
        response = client.post("/api/v1/embed/chat/message", json=payload)
        assert response.status_code == 401
        assert "Client API key required" in response.json()["detail"]

    def test_widget_chat_message_invalid_api_key(self, client):
        """Test widget chat message with invalid API key"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = None
            mock_embed_service.return_value = mock_service
            
            payload = {"message": "Hello"}
            headers = {"X-Client-API-Key": "invalid_key"}
            
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 401
            assert "Invalid client API key" in response.json()["detail"]

    def test_widget_chat_message_inactive_embed_code(self, client, test_embed_code):
        """Test widget chat message with inactive embed code"""
        test_embed_code.is_active = False
        
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
            mock_embed_service.return_value = mock_service
            
            payload = {"message": "Hello"}
            headers = {"X-Client-API-Key": test_embed_code.client_api_key}
            
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 401
            assert "Embed code is inactive" in response.json()["detail"]

    def test_widget_chat_message_expired_embed_code(self, client, test_embed_code):
        """Test widget chat message with expired embed code"""
        test_embed_code.expires_at = datetime.utcnow() - timedelta(days=1)
        
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
            mock_embed_service.return_value = mock_service
            
            payload = {"message": "Hello"}
            headers = {"X-Client-API-Key": test_embed_code.client_api_key}
            
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 401
            assert "Embed code has expired" in response.json()["detail"]

    def test_widget_chat_message_rate_limit_exceeded(self, client, test_embed_code):
        """Test widget chat message when rate limit is exceeded"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
            mock_embed_service.return_value = mock_service
            
            with patch('app.services.rate_limiting.rate_limiting_service.check_ip_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
                mock_rate_limit.return_value = (False, {"limit": 10, "remaining": 0, "reset_time": Mock(timestamp=lambda: 0)})
                
                payload = {"message": "Hello"}
                headers = {"X-Client-API-Key": test_embed_code.client_api_key}
                
                response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
                assert response.status_code == 429
                assert "Rate limit exceeded" in response.json()["detail"]

    def test_widget_chat_message_invalid_message_format(self, client, test_embed_code):
        """Test widget chat message with invalid message format"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
            mock_embed_service.return_value = mock_service
            
            # Test missing message
            payload = {}
            headers = {"X-Client-API-Key": test_embed_code.client_api_key}
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 400
            assert "Message is required" in response.json()["detail"]
            
            # Test non-string message
            payload = {"message": 123}
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 400
            assert "must be a string" in response.json()["detail"]
            
            # Test empty message
            payload = {"message": ""}
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 400
            assert "Message is required" in response.json()["detail"]

    def test_widget_chat_message_message_too_long(self, client, test_embed_code):
        """Test widget chat message with message too long"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
            mock_embed_service.return_value = mock_service
            
            payload = {"message": "x" * 1001}  # Exceeds 1000 character limit
            headers = {"X-Client-API-Key": test_embed_code.client_api_key}
            
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 400
            assert "Message too long" in response.json()["detail"]

    def test_widget_chat_message_xss_protection(self, client, test_embed_code):
        """Test widget chat message XSS protection"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
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
                            mock_chat.process_message.return_value = {"message": "Safe response"}
                            mock_chat_service.return_value = mock_chat
                            
                            # Test script injection
                            payload = {"message": "<script>alert('xss')</script>Hello"}
                            headers = {"X-Client-API-Key": test_embed_code.client_api_key}
                            
                            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
                            assert response.status_code == 200
                            # Verify that the script tag was removed from the message sent to chat service
                            mock_chat.process_message.assert_called_once()
                            call_args = mock_chat.process_message.call_args
                            assert "<script>" not in call_args[1]["message"]
                            assert "Hello" in call_args[1]["message"]

    def test_widget_chat_message_cors_origin_validation(self, client, test_embed_code):
        """Test widget chat message CORS origin validation"""
        test_embed_code.allowed_origins = "https://example.com,https://test.com"
        
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
            mock_embed_service.return_value = mock_service
            
            payload = {"message": "Hello"}
            headers = {
                "X-Client-API-Key": test_embed_code.client_api_key,
                "Origin": "https://malicious.com"
            }
            
            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
            assert response.status_code == 403
            assert "Origin not allowed" in response.json()["detail"]

    def test_widget_chat_message_allowed_origin(self, client, test_embed_code):
        """Test widget chat message with allowed origin"""
        test_embed_code.allowed_origins = "https://example.com,https://test.com"
        
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
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
                            mock_chat.process_message.return_value = {"message": "Test response"}
                            mock_chat_service.return_value = mock_chat
                            
                            payload = {"message": "Hello"}
                            headers = {
                                "X-Client-API-Key": test_embed_code.client_api_key,
                                "Origin": "https://example.com"
                            }
                            
                            response = client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
                            assert response.status_code == 200

    # ==================== CONCURRENT ACCESS TESTS ====================
    
    @pytest.mark.asyncio
    async def test_concurrent_embed_code_generation(self, client, auth_headers, test_workspace):
        """Test concurrent embed code generation"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test", workspace_id=test_workspace.id)
            
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
                
                # Send multiple concurrent requests
                tasks = []
                for i in range(5):
                    task = asyncio.create_task(
                        client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks)
                
                # All requests should succeed
                for response in responses:
                    assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_concurrent_widget_chat_messages(self, client, test_embed_code):
        """Test concurrent widget chat messages"""
        with patch('app.services.embed_service.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_embed_code_by_api_key.return_value = test_embed_code
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
                            mock_chat.process_message.return_value = {"message": "Test response"}
                            mock_chat_service.return_value = mock_chat
                            
                            payload = {"message": "Hello"}
                            headers = {"X-Client-API-Key": test_embed_code.client_api_key}
                            
                            # Send multiple concurrent requests
                            tasks = []
                            for i in range(10):
                                task = asyncio.create_task(
                                    client.post("/api/v1/embed/chat/message", json=payload, headers=headers)
                                )
                                tasks.append(task)
                            
                            responses = await asyncio.gather(*tasks)
                            
                            # All requests should succeed
                            for response in responses:
                                assert response.status_code == 200

    # ==================== ERROR HANDLING TESTS ====================
    
    def test_embed_service_database_error(self, client, auth_headers, test_workspace):
        """Test embed service database error handling"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test", workspace_id=test_workspace.id)
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.generate_embed_code.side_effect = Exception("Database connection failed")
                mock_embed_service.return_value = mock_service
                
                payload = {
                    "workspace_id": test_workspace.id,
                    "code_name": "Test Widget",
                    "config": {"theme": {"primary": "#4f46e5"}}
                }
                
                response = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
                assert response.status_code == 500
                assert "Failed to generate embed code" in response.json()["detail"]

    def test_embed_service_validation_error(self, client, auth_headers, test_workspace):
        """Test embed service validation error handling"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id="user_embed_test", workspace_id=test_workspace.id)
            
            with patch('app.services.embed_service.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.generate_embed_code.side_effect = ValueError("Invalid configuration")
                mock_embed_service.return_value = mock_service
                
                payload = {
                    "workspace_id": test_workspace.id,
                    "code_name": "Test Widget",
                    "config": {"theme": {"primary": "invalid_color"}}
                }
                
                response = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
                assert response.status_code == 500
                assert "Failed to generate embed code" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
