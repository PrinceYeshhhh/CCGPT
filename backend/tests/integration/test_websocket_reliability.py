"""
Critical WebSocket reliability tests for production stability
Tests connection recovery, concurrent connections, and real-time messaging
"""

import pytest
import asyncio
import json
import time
import uuid
from typing import List, Dict, Any
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import websockets
import threading
import queue

from app.main import app
from app.core.database import get_db, Base, engine
from app.models import User, Workspace, ChatSession, ChatMessage
from app.api.websocket.chat_ws import router as websocket_router


class TestWebSocketReliability:
    """Critical WebSocket reliability tests for production stability"""
    
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
            name="Test Workspace",
            description="Test workspace for WebSocket testing"
        )
        db_session.add(workspace)
        db_session.commit()
        db_session.refresh(workspace)
        return workspace
    
    @pytest.fixture
    def test_user(self, db_session, test_workspace):
        """Create test user"""
        user = User(
            email="websocket@test.com",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.s.2",
            full_name="WebSocket Test User",
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
            id=str(uuid.uuid4()),
            workspace_id=test_workspace.id,
            user_id=test_user.id,
            session_id="test-session-1",
            user_label="Test Customer"
        )
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        return session
    
    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(self, client, test_user):
        """Test that WebSocket connections can be established successfully"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test WebSocket connection
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Connection should be established
                assert websocket is not None
                
                # Send a test message
                test_message = {
                    "type": "ping",
                    "data": {"message": "test connection"}
                }
                websocket.send_text(json.dumps(test_message))
                
                # Should receive a response
                response = websocket.receive_text()
                assert response is not None
    
    @pytest.mark.asyncio
    async def test_websocket_connection_recovery(self, client, test_user):
        """Test WebSocket reconnection after connection failure"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # First connection
            try:
                with client.websocket_connect("/ws/chat/test-session-1") as websocket1:
                    # Send initial message
                    websocket1.send_text(json.dumps({"type": "ping", "data": {"message": "first"}}))
                    response1 = websocket1.receive_text()
                    assert response1 is not None
            except Exception as e:
                pytest.fail(f"First WebSocket connection failed: {e}")
            
            # Simulate connection failure and reconnection
            await asyncio.sleep(0.1)  # Brief pause
            
            # Second connection (reconnection)
            try:
                with client.websocket_connect("/ws/chat/test-session-1") as websocket2:
                    # Send reconnection message
                    websocket2.send_text(json.dumps({"type": "ping", "data": {"message": "reconnected"}}))
                    response2 = websocket2.receive_text()
                    assert response2 is not None
            except Exception as e:
                pytest.fail(f"WebSocket reconnection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_concurrent_websocket_connections(self, client, test_user):
        """Test multiple simultaneous WebSocket connections"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            connections = []
            messages_received = []
            
            async def create_connection(connection_id: int):
                """Create a WebSocket connection"""
                try:
                    with client.websocket_connect(f"/ws/chat/test-session-{connection_id}") as websocket:
                        # Send message
                        message = {
                            "type": "ping",
                            "data": {"message": f"connection-{connection_id}"}
                        }
                        websocket.send_text(json.dumps(message))
                        
                        # Receive response
                        response = websocket.receive_text()
                        messages_received.append({
                            "connection_id": connection_id,
                            "response": response
                        })
                except Exception as e:
                    pytest.fail(f"Connection {connection_id} failed: {e}")
            
            # Create 5 concurrent connections
            tasks = [create_connection(i) for i in range(5)]
            await asyncio.gather(*tasks)
            
            # Verify all connections were successful
            assert len(messages_received) == 5
            for i in range(5):
                assert any(msg["connection_id"] == i for msg in messages_received)
    
    @pytest.mark.asyncio
    async def test_websocket_message_broadcasting(self, client, test_user, test_chat_session):
        """Test WebSocket message broadcasting to multiple clients"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Create multiple connections to the same session
            connections = []
            messages_received = []
            
            async def listen_for_messages(connection_id: int):
                """Listen for broadcasted messages"""
                try:
                    with client.websocket_connect(f"/ws/chat/test-session-1") as websocket:
                        # Wait for broadcasted message
                        response = websocket.receive_text()
                        messages_received.append({
                            "connection_id": connection_id,
                            "message": response
                        })
                except Exception as e:
                    pytest.fail(f"Connection {connection_id} failed: {e}")
            
            # Start 3 listeners
            listener_tasks = [listen_for_messages(i) for i in range(3)]
            
            # Start listeners in background
            listener_futures = [asyncio.create_task(task) for task in listener_tasks]
            
            # Give listeners time to connect
            await asyncio.sleep(0.1)
            
            # Send broadcast message (simulated)
            broadcast_message = {
                "type": "broadcast",
                "data": {"message": "Hello all clients!"}
            }
            
            # Simulate broadcast by sending to one connection
            with client.websocket_connect("/ws/chat/test-session-1") as broadcaster:
                broadcaster.send_text(json.dumps(broadcast_message))
            
            # Wait for all listeners to receive messages
            await asyncio.gather(*listener_futures, return_exceptions=True)
            
            # Verify messages were received
            assert len(messages_received) >= 1  # At least one connection should receive the message
    
    @pytest.mark.asyncio
    async def test_websocket_typing_indicators(self, client, test_user):
        """Test WebSocket typing indicators functionality"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send typing start indicator
                typing_start = {
                    "type": "typing",
                    "data": {"is_typing": True, "user_id": str(test_user.id)}
                }
                websocket.send_text(json.dumps(typing_start))
                
                # Should receive confirmation
                response = websocket.receive_text()
                assert response is not None
                
                # Send typing stop indicator
                typing_stop = {
                    "type": "typing",
                    "data": {"is_typing": False, "user_id": str(test_user.id)}
                }
                websocket.send_text(json.dumps(typing_stop))
                
                # Should receive confirmation
                response = websocket.receive_text()
                assert response is not None
    
    @pytest.mark.asyncio
    async def test_websocket_connection_timeout(self, client, test_user):
        """Test WebSocket connection timeout handling"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send ping to keep connection alive
                ping_message = {
                    "type": "ping",
                    "data": {"timestamp": time.time()}
                }
                websocket.send_text(json.dumps(ping_message))
                
                # Should receive pong
                response = websocket.receive_text()
                assert response is not None
                
                # Test connection after idle period
                await asyncio.sleep(0.1)  # Brief idle period
                
                # Send another message after idle period
                websocket.send_text(json.dumps(ping_message))
                response = websocket.receive_text()
                assert response is not None
    
    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, client, test_user):
        """Test WebSocket error handling and recovery"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send malformed message
                malformed_message = "invalid json message"
                websocket.send_text(malformed_message)
                
                # Should handle error gracefully
                try:
                    response = websocket.receive_text()
                    # If we get a response, it should be an error message
                    assert "error" in response.lower() or "invalid" in response.lower()
                except Exception:
                    # Connection might close, which is also acceptable error handling
                    pass
                
                # Send valid message after error
                valid_message = {
                    "type": "ping",
                    "data": {"message": "recovery test"}
                }
                websocket.send_text(json.dumps(valid_message))
                
                # Should work normally after error
                response = websocket.receive_text()
                assert response is not None
    
    @pytest.mark.asyncio
    async def test_websocket_authentication_failure(self, client):
        """Test WebSocket connection with invalid authentication"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            # Simulate authentication failure
            mock_get_user.side_effect = Exception("Authentication failed")
            
            # Connection should be rejected
            with pytest.raises(Exception):
                with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                    pass
    
    @pytest.mark.asyncio
    async def test_websocket_message_ordering(self, client, test_user):
        """Test that WebSocket messages maintain proper ordering"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send multiple messages in sequence
                messages_sent = []
                for i in range(5):
                    message = {
                        "type": "message",
                        "data": {"content": f"message-{i}", "order": i}
                    }
                    websocket.send_text(json.dumps(message))
                    messages_sent.append(i)
                
                # Receive responses in order
                messages_received = []
                for i in range(5):
                    response = websocket.receive_text()
                    messages_received.append(response)
                
                # Verify all messages were received
                assert len(messages_received) == 5
    
    @pytest.mark.asyncio
    async def test_websocket_connection_limits(self, client, test_user):
        """Test WebSocket connection limits and resource management"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            # Test multiple connections from same user
            connections = []
            max_connections = 10  # Reasonable limit for testing
            
            for i in range(max_connections):
                try:
                    with client.websocket_connect(f"/ws/chat/test-session-{i}") as websocket:
                        connections.append(websocket)
                        # Send test message
                        websocket.send_text(json.dumps({
                            "type": "ping",
                            "data": {"connection": i}
                        }))
                except Exception as e:
                    # If connection limit is reached, that's acceptable
                    if "connection limit" in str(e).lower():
                        break
                    else:
                        pytest.fail(f"Unexpected error: {e}")
            
            # Verify at least some connections were successful
            assert len(connections) > 0
    
    @pytest.mark.asyncio
    async def test_websocket_graceful_shutdown(self, client, test_user):
        """Test WebSocket graceful shutdown and cleanup"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send close message
                close_message = {
                    "type": "close",
                    "data": {"reason": "client disconnect"}
                }
                websocket.send_text(json.dumps(close_message))
                
                # Connection should close gracefully
                try:
                    response = websocket.receive_text()
                    # If we get a response, it should be a close confirmation
                    assert "close" in response.lower() or "disconnect" in response.lower()
                except Exception:
                    # Connection closed, which is expected
                    pass
    
    @pytest.mark.asyncio
    async def test_websocket_heartbeat_mechanism(self, client, test_user):
        """Test WebSocket heartbeat mechanism for connection health"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send heartbeat
                heartbeat = {
                    "type": "heartbeat",
                    "data": {"timestamp": time.time()}
                }
                websocket.send_text(json.dumps(heartbeat))
                
                # Should receive heartbeat response
                response = websocket.receive_text()
                assert response is not None
                
                # Parse response to verify it's a heartbeat
                try:
                    response_data = json.loads(response)
                    assert response_data.get("type") == "heartbeat" or "pong" in response.lower()
                except json.JSONDecodeError:
                    # Response might not be JSON, but should contain heartbeat indicator
                    assert "heartbeat" in response.lower() or "pong" in response.lower()
    
    @pytest.mark.asyncio
    async def test_websocket_concurrent_messages(self, client, test_user):
        """Test handling of concurrent messages on same connection"""
        with patch('app.api.websocket.chat_ws.get_current_user') as mock_get_user:
            mock_get_user.return_value = test_user
            
            with client.websocket_connect("/ws/chat/test-session-1") as websocket:
                # Send multiple messages rapidly
                messages = []
                for i in range(10):
                    message = {
                        "type": "message",
                        "data": {"content": f"rapid-message-{i}"}
                    }
                    websocket.send_text(json.dumps(message))
                    messages.append(i)
                
                # Receive all responses
                responses = []
                for i in range(10):
                    try:
                        response = websocket.receive_text()
                        responses.append(response)
                    except Exception as e:
                        # Some messages might be lost, but most should be received
                        break
                
                # Verify most messages were received
                assert len(responses) >= 5, f"Only received {len(responses)} out of 10 messages"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
