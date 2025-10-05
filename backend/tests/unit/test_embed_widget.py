"""
Comprehensive unit tests for embed widget functionality
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.embed_service import EmbedService
from app.models import EmbedCode, User, Workspace
from app.schemas.embed import (
    EmbedCodeGenerateRequest,
    WidgetConfig,
    WidgetPreviewRequest
)


class TestEmbedService:
    """Comprehensive tests for EmbedService"""
    
    @pytest.fixture
    def embed_service(self, db_session):
        return EmbedService(db_session)
    
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
    
    def test_generate_embed_code_success(self, embed_service, test_user, test_workspace):
        """Test successful embed code generation"""
        config = {
            "theme": {"primary": "#4f46e5", "secondary": "#6366f1"},
            "welcomeMessage": "Hello! How can I help?",
            "placeholder": "Type your question...",
            "showSources": True
        }
        
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget",
            config=config
        )
        
        assert embed_code.workspace_id == str(test_workspace.id)
        assert embed_code.user_id == test_user.id
        assert embed_code.code_name == "Test Widget"
        assert embed_code.is_active is True
        assert embed_code.client_api_key is not None
        assert len(embed_code.client_api_key) > 20  # Should be a substantial API key
    
    def test_generate_embed_code_with_custom_template(self, embed_service, test_user, test_workspace):
        """Test embed code generation with custom snippet template"""
        config = {"theme": {"primary": "#10b981"}}
        custom_template = """
        <div id="customercaregpt-widget" 
             data-embed-id="{embed_id}" 
             data-api-key="{api_key}"
             data-theme="{theme}">
        </div>
        <script src="{widget_url}"></script>
        """
        
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Custom Widget",
            config=config,
            snippet_template=custom_template
        )
        
        snippet = embed_service.get_embed_snippet(embed_code)
        assert "customercaregpt-widget" in snippet
        assert str(embed_code.id) in snippet
        assert embed_code.client_api_key in snippet
    
    def test_get_embed_snippet_default_template(self, embed_service, test_user, test_workspace):
        """Test default embed snippet generation"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        snippet = embed_service.get_embed_snippet(embed_code)
        
        assert "<script" in snippet
        assert "data-embed-id" in snippet
        assert "data-api-key" in snippet
        assert str(embed_code.id) in snippet
        assert embed_code.client_api_key in snippet
    
    def test_get_embed_code_by_api_key(self, embed_service, test_user, test_workspace):
        """Test retrieving embed code by API key"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        retrieved_code = embed_service.get_embed_code_by_api_key(embed_code.client_api_key)
        
        assert retrieved_code is not None
        assert retrieved_code.id == embed_code.id
        assert retrieved_code.client_api_key == embed_code.client_api_key
    
    def test_get_embed_code_by_api_key_invalid(self, embed_service):
        """Test retrieving embed code with invalid API key"""
        retrieved_code = embed_service.get_embed_code_by_api_key("invalid_key")
        assert retrieved_code is None
    
    def test_get_embed_code_by_api_key_inactive(self, embed_service, test_user, test_workspace):
        """Test retrieving inactive embed code"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        # Deactivate the embed code
        embed_code.is_active = False
        embed_service.db.commit()
        
        retrieved_code = embed_service.get_embed_code_by_api_key(embed_code.client_api_key)
        assert retrieved_code is None
    
    def test_increment_usage(self, embed_service, test_user, test_workspace):
        """Test usage count increment"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        initial_usage = embed_code.usage_count
        embed_service.increment_usage(str(embed_code.id))
        
        # Refresh from database
        embed_service.db.refresh(embed_code)
        assert embed_code.usage_count == initial_usage + 1
    
    def test_update_embed_code_config(self, embed_service, test_user, test_workspace):
        """Test updating embed code configuration"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        new_config = {
            "theme": {"primary": "#10b981", "secondary": "#059669"},
            "welcomeMessage": "Updated welcome message",
            "showSources": False
        }
        
        updated_code = embed_service.update_embed_code(
            str(embed_code.id),
            config=new_config
        )
        
        assert updated_code is not None
        assert updated_code.default_config["theme"]["primary"] == "#10b981"
        assert updated_code.default_config["welcomeMessage"] == "Updated welcome message"
        assert updated_code.default_config["showSources"] is False
    
    def test_deactivate_embed_code(self, embed_service, test_user, test_workspace):
        """Test deactivating embed code"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        result = embed_service.deactivate_embed_code(str(embed_code.id))
        assert result is True
        
        # Verify it's deactivated
        embed_service.db.refresh(embed_code)
        assert embed_code.is_active is False
    
    def test_get_widget_script(self, embed_service, test_user, test_workspace):
        """Test getting widget script content"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        script_content = embed_service.get_widget_script(str(embed_code.id))
        
        assert script_content is not None
        assert "function" in script_content or "const" in script_content
        assert "CustomerCareGPT" in script_content or "customercaregpt" in script_content.lower()

    def test_widget_script_includes_rotating_greetings(self, embed_service, test_user, test_workspace):
        """Ensure the generated widget script supports rotating greeting messages on each open."""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Greeting Rotation Widget"
        )

        script_content = embed_service.get_widget_script(str(embed_code.id))

        # Script should expose a welcomeMessages array and rotation helpers
        assert "welcomeMessages:" in script_content
        assert "function getWelcomeMessage()" in script_content
        assert "localStorage.setItem(" in script_content

        # The chat toggle should append a greeting each time it opens
        assert "function toggleChat()" in script_content
        assert "const greet = getWelcomeMessage();" in script_content
        assert "addMessage(greet, 'bot')" in script_content

        # Default config should also retain single welcomeMessage fallback
        assert "welcomeMessage:" in script_content
    
    def test_get_widget_script_inactive(self, embed_service, test_user, test_workspace):
        """Test getting widget script for inactive embed code"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        # Deactivate the embed code
        embed_code.is_active = False
        embed_service.db.commit()
        
        script_content = embed_service.get_widget_script(str(embed_code.id))
        assert script_content is None
    
    def test_validate_origin_allowed(self, embed_service, test_user, test_workspace):
        """Test origin validation for allowed domains"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget",
            config={"allowedOrigins": ["https://example.com", "https://test.com"]}
        )
        
        # Test allowed origins
        assert embed_service.validate_origin(str(embed_code.id), "https://example.com") is True
        assert embed_service.validate_origin(str(embed_code.id), "https://test.com") is True
        
        # Test disallowed origin
        assert embed_service.validate_origin(str(embed_code.id), "https://malicious.com") is False
    
    def test_validate_origin_no_restrictions(self, embed_service, test_user, test_workspace):
        """Test origin validation when no restrictions are set"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        # Should allow any origin when no restrictions
        assert embed_service.validate_origin(str(embed_code.id), "https://any-domain.com") is True
        assert embed_service.validate_origin(str(embed_code.id), "http://localhost:3000") is True
    
    def test_get_embed_analytics(self, embed_service, test_user, test_workspace):
        """Test getting embed code analytics"""
        embed_code = embed_service.generate_embed_code(
            workspace_id=str(test_workspace.id),
            user_id=test_user.id,
            code_name="Test Widget"
        )
        
        # Simulate some usage
        embed_code.usage_count = 10
        embed_code.unique_visitors = 5
        embed_service.db.commit()
        
        analytics = embed_service.get_embed_analytics(str(embed_code.id))
        
        assert analytics is not None
        assert analytics["total_queries"] == 10
        assert analytics["unique_visitors"] == 5
        assert "last_used" in analytics
        assert "created_at" in analytics


class TestEmbedWidgetAPI:
    """Tests for embed widget API endpoints"""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self, test_user):
        from app.services.auth import AuthService
        auth_service = AuthService(None)
        token = auth_service.create_access_token({"user_id": str(test_user.id), "email": test_user.email})
        return {"Authorization": f"Bearer {token}"}
    
    def test_generate_embed_code_endpoint(self, client, auth_headers, test_workspace):
        """Test embed code generation endpoint"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_user.workspace_id = str(test_workspace.id)
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_embed_code = Mock()
                mock_embed_code.id = "embed_123"
                mock_embed_code.client_api_key = "api_key_123"
                mock_embed_code.default_config = {"theme": {"primary": "#4f46e5"}}
                mock_service.generate_embed_code.return_value = mock_embed_code
                mock_service.get_embed_snippet.return_value = "<script>console.log('test')</script>"
                mock_embed_service.return_value = mock_service
                
                embed_data = {
                    "workspace_id": str(test_workspace.id),
                    "code_name": "Test Widget",
                    "config": {
                        "theme": {"primary": "#4f46e5"},
                        "welcomeMessage": "Hello!"
                    }
                }
                
                response = client.post("/api/v1/embed/generate", json=embed_data, headers=auth_headers)
                
                assert response.status_code == 201
                data = response.json()
                assert "embed_code_id" in data
                assert "client_api_key" in data
                assert "embed_snippet" in data
                assert "widget_url" in data
    
    def test_widget_script_endpoint(self, client):
        """Test widget script serving endpoint"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_widget_script.return_value = "console.log('CustomerCareGPT Widget');"
            mock_service.increment_usage.return_value = None
            mock_embed_service.return_value = mock_service
            
            response = client.get("/api/v1/embed/widget/embed_123")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/javascript"
            assert "CustomerCareGPT" in response.text
    
    def test_widget_script_not_found(self, client):
        """Test widget script endpoint when embed code not found"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_service.get_widget_script.return_value = None
            mock_embed_service.return_value = mock_service
            
            response = client.get("/api/v1/embed/widget/nonexistent")
            
            assert response.status_code == 404
    
    def test_widget_chat_message_endpoint(self, client):
        """Test widget chat message endpoint"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
            with patch('app.api.api_v1.endpoints.embed_enhanced.ChatService') as mock_chat_service:
                mock_embed_service_instance = Mock()
                mock_embed_code = Mock()
                mock_embed_code.id = "embed_123"
                mock_embed_code.workspace_id = "ws_123"
                mock_embed_code.user_id = "user_123"
                mock_embed_code.is_active = True
                mock_embed_service_instance.get_embed_code_by_api_key.return_value = mock_embed_code
                mock_embed_service_instance.validate_origin.return_value = True
                mock_embed_service.return_value = mock_embed_service_instance
                
                mock_chat_service_instance = Mock()
                mock_chat_service_instance.process_message.return_value = {
                    "response": "Test response",
                    "message_id": "msg_123"
                }
                mock_chat_service.return_value = mock_chat_service_instance
                
                with patch('app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service') as mock_rate_limit:
                    mock_rate_limit.check_ip_rate_limit.return_value = (True, {})
                    
                    message_data = {
                        "message": "Hello, how can I help?",
                        "session_id": "session_123"
                    }
                    
                    headers = {
                        "X-Client-API-Key": "api_key_123",
                        "X-Embed-Code-ID": "embed_123",
                        "Origin": "https://example.com"
                    }
                    
                    response = client.post(
                        "/api/v1/embed/chat/message",
                        json=message_data,
                        headers=headers
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "response" in data
                    assert data["response"] == "Test response"
    
    def test_widget_chat_message_rate_limited(self, client):
        """Test widget chat message endpoint with rate limiting"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service') as mock_rate_limit:
            mock_rate_limit.check_ip_rate_limit.return_value = (False, {"retry_after": 60})
            
            message_data = {"message": "Hello"}
            headers = {"X-Client-API-Key": "api_key_123"}
            
            response = client.post(
                "/api/v1/embed/chat/message",
                json=message_data,
                headers=headers
            )
            
            assert response.status_code == 429
            assert "rate limit" in response.json()["detail"].lower()
    
    def test_widget_chat_message_invalid_origin(self, client):
        """Test widget chat message endpoint with invalid origin"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
            mock_service = Mock()
            mock_embed_code = Mock()
            mock_embed_code.is_active = True
            mock_service.get_embed_code_by_api_key.return_value = mock_embed_code
            mock_service.validate_origin.return_value = False
            mock_embed_service.return_value = mock_service
            
            with patch('app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service') as mock_rate_limit:
                mock_rate_limit.check_ip_rate_limit.return_value = (True, {})
                
                message_data = {"message": "Hello"}
                headers = {
                    "X-Client-API-Key": "api_key_123",
                    "Origin": "https://malicious.com"
                }
                
                response = client.post(
                    "/api/v1/embed/chat/message",
                    json=message_data,
                    headers=headers
                )
                
                assert response.status_code == 403
                assert "origin" in response.json()["detail"].lower()
    
    def test_widget_preview_endpoint(self, client, auth_headers):
        """Test widget preview endpoint"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "123"
            mock_get_user.return_value = mock_user
            
            with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
                mock_service = Mock()
                mock_service.generate_preview.return_value = {
                    "preview_html": "<div>Preview</div>",
                    "preview_css": "body { color: red; }"
                }
                mock_embed_service.return_value = mock_service
                
                preview_data = {
                    "config": {
                        "theme": {"primary": "#4f46e5"},
                        "welcomeMessage": "Preview message"
                    }
                }
                
                response = client.post("/api/v1/embed/preview", json=preview_data, headers=auth_headers)
                
                assert response.status_code == 200
                data = response.json()
                assert "preview_html" in data
                assert "preview_css" in data


class TestEmbedWidgetSecurity:
    """Security tests for embed widget functionality"""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_xss_prevention_in_widget_message(self, client):
        """Test XSS prevention in widget messages"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.EmbedService') as mock_embed_service:
            with patch('app.api.api_v1.endpoints.embed_enhanced.ChatService') as mock_chat_service:
                mock_embed_service_instance = Mock()
                mock_embed_code = Mock()
                mock_embed_code.id = "embed_123"
                mock_embed_code.workspace_id = "ws_123"
                mock_embed_code.user_id = "user_123"
                mock_embed_code.is_active = True
                mock_embed_service_instance.get_embed_code_by_api_key.return_value = mock_embed_code
                mock_embed_service_instance.validate_origin.return_value = True
                mock_embed_service.return_value = mock_embed_service_instance
                
                mock_chat_service_instance = Mock()
                mock_chat_service_instance.process_message.return_value = {
                    "response": "Safe response",
                    "message_id": "msg_123"
                }
                mock_chat_service.return_value = mock_chat_service_instance
                
                with patch('app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service') as mock_rate_limit:
                    mock_rate_limit.check_ip_rate_limit.return_value = (True, {})
                    
                    # Test XSS attempt
                    malicious_message = "<script>alert('XSS')</script>Hello"
                    message_data = {"message": malicious_message}
                    headers = {"X-Client-API-Key": "api_key_123"}
                    
                    response = client.post(
                        "/api/v1/embed/chat/message",
                        json=message_data,
                        headers=headers
                    )
                    
                    # Should process the message but sanitize it
                    assert response.status_code == 200
                    # Verify the sanitized message was passed to chat service
                    call_args = mock_chat_service_instance.process_message.call_args
                    sanitized_message = call_args[1]["message"]
                    assert "<script>" not in sanitized_message
                    assert "Hello" in sanitized_message
    
    def test_message_length_limitation(self, client):
        """Test message length limitation"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service') as mock_rate_limit:
            mock_rate_limit.check_ip_rate_limit.return_value = (True, {})
            
            # Test very long message
            long_message = "A" * 2000  # Exceeds 1000 character limit
            message_data = {"message": long_message}
            headers = {"X-Client-API-Key": "api_key_123"}
            
            response = client.post(
                "/api/v1/embed/chat/message",
                json=message_data,
                headers=headers
            )
            
            assert response.status_code == 400
            assert "too long" in response.json()["detail"].lower()
    
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in widget messages"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service') as mock_rate_limit:
            mock_rate_limit.check_ip_rate_limit.return_value = (True, {})
            
            # Test invalid JSON
            response = client.post(
                "/api/v1/embed/chat/message",
                data="invalid json",
                headers={"X-Client-API-Key": "api_key_123", "Content-Type": "application/json"}
            )
            
            assert response.status_code == 400
            assert "invalid" in response.json()["detail"].lower()
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        with patch('app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service') as mock_rate_limit:
            mock_rate_limit.check_ip_rate_limit.return_value = (True, {})
            
            # Test missing message field
            message_data = {"session_id": "session_123"}
            headers = {"X-Client-API-Key": "api_key_123"}
            
            response = client.post(
                "/api/v1/embed/chat/message",
                json=message_data,
                headers=headers
            )
            
            assert response.status_code == 400
            assert "message" in response.json()["detail"].lower()
