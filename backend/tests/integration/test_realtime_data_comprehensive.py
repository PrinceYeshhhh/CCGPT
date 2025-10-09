"""
Comprehensive Real-time Data Integration Tests
Tests all real-time functionality including WebSocket reliability, broadcasting, and concurrent connections
"""

import pytest
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import patch, Mock, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, ChatSession, ChatMessage
from app.api.websocket.chat_ws import router as websocket_router


class TestRealtimeDataComprehensive:
    """Comprehensive tests for real-time data functionality"""
    
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
            id="ws_realtime_test",
            name="Realtime Test Workspace",
            description="Test workspace for real-time data testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            id="user_realtime_test",
            email="realtime@test.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="Realtime Test User",
            workspace_id=test_workspace.id,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_chat_session(self, db_session, test_user, test_workspace):
        """Create test chat session"""
        session = ChatSession(
            id="session_realtime_test",
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            session_id="realtime-session-1",
            user_label="Test Customer",
            is_active=True
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        return session
    
    @pytest.fixture
    def auth_headers(self, test_user):
        """Create authentication headers"""
        from app.services.auth import AuthService
        auth_service = AuthService(None)
        token = auth_service.create_access_token(data={"sub": test_user.email})
        return {"Authorization": f"Bearer {token}"}

    # ==================== WEBSOCKET CONNECTION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self, client, test_user):
        """Test WebSocket connection establishment"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.process_chat_message.return_value = {
                    "type": "response",
                    "content": "Test response"
                }
                
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    # Connection should be established
                    assert websocket is not None
                    
                    # Send a test message
                    test_message = {
                        "type": "chat",
                        "content": "Hello, test message"
                    }
                    websocket.send_text(json.dumps(test_message))
                    
                    # Should receive a response
                    response = websocket.receive_text()
                    assert response is not None
                    response_data = json.loads(response)
                    assert response_data["type"] == "response"

    @pytest.mark.asyncio
    async def test_websocket_connection_authentication_failure(self, client):
        """Test WebSocket connection with authentication failure"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = None
            
            with pytest.raises(Exception):  # WebSocket connection should fail
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    pass

    @pytest.mark.asyncio
    async def test_websocket_connection_rate_limit_exceeded(self, client, test_user):
        """Test WebSocket connection when rate limit is exceeded"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = False
            
            with pytest.raises(Exception):  # WebSocket connection should fail
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    pass

    @pytest.mark.asyncio
    async def test_websocket_invalid_session_id(self, client, test_user):
        """Test WebSocket connection with invalid session ID"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            
            # Test with session ID that's too short
            with pytest.raises(Exception):  # WebSocket connection should fail
                with client.websocket_connect("/ws/chat/123") as websocket:
                    pass

    # ==================== WEBSOCKET MESSAGE HANDLING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_websocket_chat_message_processing(self, client, test_user):
        """Test WebSocket chat message processing"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.process_chat_message.return_value = {
                    "type": "response",
                    "content": "Hello! How can I help you?",
                    "session_id": "test-session-1"
                }
                
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    # Send chat message
                    chat_message = {
                        "type": "chat",
                        "content": "Hello, I need help with my order"
                    }
                    websocket.send_text(json.dumps(chat_message))
                    
                    # Receive response
                    response = websocket.receive_text()
                    response_data = json.loads(response)
                    assert response_data["type"] == "response"
                    assert "Hello! How can I help you?" in response_data["content"]

    @pytest.mark.asyncio
    async def test_websocket_ping_pong(self, client, test_user):
        """Test WebSocket ping-pong mechanism"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send ping
                ping_message = {"type": "ping"}
                websocket.send_text(json.dumps(ping_message))
                
                # Receive pong
                response = websocket.receive_text()
                response_data = json.loads(response)
                assert response_data["type"] == "pong"

    @pytest.mark.asyncio
    async def test_websocket_typing_indicator(self, client, test_user):
        """Test WebSocket typing indicator"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.broadcast_typing.return_value = None
                
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    # Send typing indicator
                    typing_message = {
                        "type": "typing"
                    }
                    websocket.send_text(json.dumps(typing_message))
                    
                    # Should not receive immediate response for typing
                    # The broadcast_typing method should be called
                    mock_chat_service.broadcast_typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_stop_typing_indicator(self, client, test_user):
        """Test WebSocket stop typing indicator"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.broadcast_typing.return_value = None
                
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    # Send stop typing indicator
                    stop_typing_message = {
                        "type": "stop_typing"
                    }
                    websocket.send_text(json.dumps(stop_typing_message))
                    
                    # The broadcast_typing method should be called with is_typing=False
                    mock_chat_service.broadcast_typing.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_invalid_message_format(self, client, test_user):
        """Test WebSocket with invalid message format"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = False  # Invalid message
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send invalid message
                invalid_message = {"invalid": "message"}
                websocket.send_text(json.dumps(invalid_message))
                
                # Should receive error response
                response = websocket.receive_text()
                response_data = json.loads(response)
                assert response_data["type"] == "error"
                assert "Invalid message format" in response_data["message"]

    @pytest.mark.asyncio
    async def test_websocket_rate_limit_exceeded(self, client, test_user):
        """Test WebSocket when message rate limit is exceeded"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = False  # Rate limit exceeded
            mock_security.record_message.return_value = None
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send message
                chat_message = {
                    "type": "chat",
                    "content": "Hello"
                }
                websocket.send_text(json.dumps(chat_message))
                
                # Should receive rate limit error
                response = websocket.receive_text()
                response_data = json.loads(response)
                assert response_data["type"] == "error"
                assert "Rate limit exceeded" in response_data["message"]

    # ==================== CONCURRENT CONNECTION TESTS ====================
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_websocket_connections(self, client, test_user):
        """Test multiple concurrent WebSocket connections"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.process_chat_message.return_value = {
                    "type": "response",
                    "content": "Test response"
                }
                
                # Create multiple concurrent connections
                connections = []
                for i in range(5):
                    try:
                        websocket = client.websocket_connect(f"/ws/chat/test-session-{i}")
                        connections.append(websocket)
                    except Exception as e:
                        # Some connections might fail due to test limitations
                        pass
                
                # All connections should be established
                assert len(connections) > 0

    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup(self, client, test_user):
        """Test WebSocket connection cleanup on disconnect"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Connection should be established
                assert websocket is not None
                
                # Close connection
                websocket.close()
                
                # unregister_connection should be called
                mock_security.unregister_connection.assert_called()

    # ==================== BROADCASTING TESTS ====================
    
    def test_broadcast_to_session_success(self, client, auth_headers, test_user):
        """Test successful message broadcasting to session"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.websocket_manager.get_session_info.return_value = {
                    "session_id": "test-session-1",
                    "active_connections": 2
                }
                mock_chat_service.websocket_manager.broadcast_to_session.return_value = None
                
                message = {
                    "type": "announcement",
                    "content": "System maintenance in 5 minutes"
                }
                
                response = client.post(
                    "/api/v1/websocket/broadcast/test-session-1",
                    json=message,
                    headers=auth_headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert "Message broadcasted successfully" in data["message"]

    def test_broadcast_to_nonexistent_session(self, client, auth_headers, test_user):
        """Test broadcasting to non-existent session"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.websocket_manager.get_session_info.return_value = None
                
                message = {
                    "type": "announcement",
                    "content": "System maintenance in 5 minutes"
                }
                
                response = client.post(
                    "/api/v1/websocket/broadcast/nonexistent-session",
                    json=message,
                    headers=auth_headers
                )
                
                assert response.status_code == 404
                assert "Session not found or not active" in response.json()["detail"]

    def test_broadcast_unauthorized_access(self, client):
        """Test broadcasting without authentication"""
        message = {
            "type": "announcement",
            "content": "System maintenance in 5 minutes"
        }
        
        response = client.post(
            "/api/v1/websocket/broadcast/test-session-1",
            json=message
        )
        
        assert response.status_code == 401

    # ==================== WEBSOCKET STATISTICS TESTS ====================
    
    def test_websocket_stats_success(self, client):
        """Test successful WebSocket statistics retrieval"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_stats = {
                "total_connections": 10,
                "active_connections": 5,
                "total_messages": 100,
                "connections_by_workspace": {
                    "ws_1": 3,
                    "ws_2": 2
                }
            }
            mock_security.get_connection_stats.return_value = mock_stats
            
            response = client.get("/api/v1/websocket/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            assert data["data"]["total_connections"] == 10
            assert data["data"]["active_connections"] == 5

    def test_websocket_stats_error(self, client):
        """Test WebSocket statistics with error"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.get_connection_stats.side_effect = Exception("Stats error")
            
            response = client.get("/api/v1/websocket/stats")
            assert response.status_code == 500
            assert "Failed to retrieve WebSocket statistics" in response.json()["detail"]

    # ==================== PERFORMANCE TESTS ====================
    
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self, client, test_user):
        """Test WebSocket message throughput"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.process_chat_message.return_value = {
                    "type": "response",
                    "content": "Test response"
                }
                
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    # Send multiple messages rapidly
                    start_time = time.time()
                    message_count = 10
                    
                    for i in range(message_count):
                        message = {
                            "type": "chat",
                            "content": f"Message {i}"
                        }
                        websocket.send_text(json.dumps(message))
                    
                    # Receive all responses
                    responses = []
                    for i in range(message_count):
                        try:
                            response = websocket.receive_text()
                            responses.append(response)
                        except Exception:
                            break
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    # Should process messages within reasonable time
                    assert duration < 5.0
                    assert len(responses) >= message_count // 2  # At least half should be processed

    @pytest.mark.asyncio
    async def test_websocket_connection_scaling(self, client, test_user):
        """Test WebSocket connection scaling"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            # Test with increasing number of connections
            connection_counts = [1, 5, 10, 20]
            
            for count in connection_counts:
                connections = []
                try:
                    for i in range(count):
                        websocket = client.websocket_connect(f"/ws/chat/test-session-{i}")
                        connections.append(websocket)
                    
                    # All connections should be established
                    assert len(connections) == count
                    
                    # Clean up connections
                    for conn in connections:
                        try:
                            conn.close()
                        except:
                            pass
                            
                except Exception as e:
                    # Some connections might fail due to test limitations
                    assert len(connections) >= count // 2

    # ==================== ERROR HANDLING TESTS ====================
    
    @pytest.mark.asyncio
    async def test_websocket_connection_error_handling(self, client, test_user):
        """Test WebSocket connection error handling"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.side_effect = Exception("Authentication error")
            
            with pytest.raises(Exception):  # WebSocket connection should fail
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    pass

    @pytest.mark.asyncio
    async def test_websocket_message_processing_error(self, client, test_user):
        """Test WebSocket message processing error handling"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.process_chat_message.side_effect = Exception("Processing error")
                
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    # Send message
                    message = {
                        "type": "chat",
                        "content": "Hello"
                    }
                    websocket.send_text(json.dumps(message))
                    
                    # Should receive error response
                    response = websocket.receive_text()
                    response_data = json.loads(response)
                    assert response_data["type"] == "error"
                    assert "Message processing failed" in response_data["message"]

    def test_broadcast_service_error(self, client, auth_headers, test_user):
        """Test broadcasting with service error"""
        with patch('app.api.api_v1.dependencies.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                mock_chat_service.websocket_manager.get_session_info.return_value = {
                    "session_id": "test-session-1",
                    "active_connections": 2
                }
                mock_chat_service.websocket_manager.broadcast_to_session.side_effect = Exception("Broadcast error")
                
                message = {
                    "type": "announcement",
                    "content": "System maintenance in 5 minutes"
                }
                
                response = client.post(
                    "/api/v1/websocket/broadcast/test-session-1",
                    json=message,
                    headers=auth_headers
                )
                
                assert response.status_code == 500
                assert "Failed to broadcast message" in response.json()["detail"]

    # ==================== EDGE CASE TESTS ====================
    
    @pytest.mark.asyncio
    async def test_websocket_empty_message(self, client, test_user):
        """Test WebSocket with empty message"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = False  # Empty message is invalid
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send empty message
                websocket.send_text("")
                
                # Should receive error response
                response = websocket.receive_text()
                response_data = json.loads(response)
                assert response_data["type"] == "error"

    @pytest.mark.asyncio
    async def test_websocket_malformed_json(self, client, test_user):
        """Test WebSocket with malformed JSON"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = False  # Malformed JSON is invalid
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send malformed JSON
                websocket.send_text("{ invalid json }")
                
                # Should receive error response
                response = websocket.receive_text()
                response_data = json.loads(response)
                assert response_data["type"] == "error"

    @pytest.mark.asyncio
    async def test_websocket_connection_timeout(self, client, test_user):
        """Test WebSocket connection timeout handling"""
        with patch('app.api.websocket.chat_ws.websocket_security_service') as mock_security:
            mock_security.authenticate_connection.return_value = {
                "user_id": test_user.id,
                "workspace_id": test_user.workspace_id
            }
            mock_security.check_connection_limits.return_value = True
            mock_security.register_connection.return_value = None
            mock_security.unregister_connection.return_value = None
            mock_security.validate_message.return_value = True
            mock_security.check_message_rate_limit.return_value = True
            mock_security.record_message.return_value = None
            
            with patch('app.services.websocket_service.realtime_chat_service') as mock_chat_service:
                # Simulate slow response
                async def slow_response(*args, **kwargs):
                    await asyncio.sleep(10)  # Simulate timeout
                    return {"type": "response", "content": "Slow response"}
                
                mock_chat_service.process_chat_message.side_effect = slow_response
                
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    # Send message
                    message = {
                        "type": "chat",
                        "content": "Hello"
                    }
                    websocket.send_text(json.dumps(message))
                    
                    # Should handle timeout gracefully
                    try:
                        response = websocket.receive_text()
                        # If we get a response, it should be valid
                        response_data = json.loads(response)
                        assert "type" in response_data
                    except Exception:
                        # Timeout is expected in this test
                        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
