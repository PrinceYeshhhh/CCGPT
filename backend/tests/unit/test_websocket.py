"""
Unit tests for WebSocket functionality
Tests chat WebSocket connections, message handling, and error scenarios
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import WebSocket, WebSocketDisconnect, FastAPI
from fastapi.websockets import WebSocketState

from app.api.websocket.chat_ws import router as websocket_router
from app.services.websocket_service import WebSocketService
from app.services.chat import ChatService
from app.models import ChatSession, ChatMessage

class TestWebSocketConnection:
    """Test WebSocket connection handling"""
    
    def test_websocket_connection_accepts_valid_token(self):
        """Test that WebSocket accepts connections with valid tokens"""
        app = FastAPI()
        app.include_router(websocket_router)
        
        with patch('app.api.websocket.chat_ws.verify_websocket_token') as mock_verify:
            mock_verify.return_value = {"user_id": "123", "workspace_id": "ws_123"}
            
            client = TestClient(app)
            with client.websocket_connect("/ws/chat?token=valid_token") as websocket:
                # Connection should be established
                assert websocket is not None
    
    def test_websocket_connection_rejects_invalid_token(self):
        """Test that WebSocket rejects connections with invalid tokens"""
        app = FastAPI()
        app.include_router(websocket_router)
        
        with patch('app.api.websocket.chat_ws.verify_websocket_token') as mock_verify:
            mock_verify.return_value = None
            
            client = TestClient(app)
            with pytest.raises(Exception):  # Should raise connection error
                with client.websocket_connect("/ws/chat?token=invalid_token") as websocket:
                    pass
    
    def test_websocket_connection_rejects_missing_token(self):
        """Test that WebSocket rejects connections without tokens"""
        app = FastAPI()
        app.include_router(websocket_router)
        
        client = TestClient(app)
        with pytest.raises(Exception):  # Should raise connection error
            with client.websocket_connect("/ws/chat") as websocket:
                pass

class TestWebSocketMessageHandling:
    """Test WebSocket message handling"""
    
    @pytest.mark.asyncio
    async def test_websocket_receives_text_message(self):
        """Test that WebSocket can receive text messages"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value='{"type": "message", "content": "Hello"}')
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock the message processing
        with patch.object(websocket_service, 'process_message') as mock_process:
            mock_process.return_value = {"response": "Hello back!"}
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            mock_websocket.receive_text.assert_called_once()
            mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_sends_response(self):
        """Test that WebSocket sends responses back to client"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value='{"type": "message", "content": "Hello"}')
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock the message processing
        with patch.object(websocket_service, 'process_message') as mock_process:
            mock_process.return_value = {"response": "Hello back!"}
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_websocket_handles_invalid_json(self):
        """Test that WebSocket handles invalid JSON gracefully"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value='invalid json')
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
        
        # Should send error message
        mock_websocket.send_text.assert_called()
        error_message = mock_websocket.send_text.call_args[0][0]
        assert "error" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_websocket_handles_disconnect(self):
        """Test that WebSocket handles client disconnection gracefully"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(side_effect=WebSocketDisconnect(1000, "Client disconnected"))
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Should not raise exception
        await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
        
        mock_websocket.close.assert_called_once()

class TestWebSocketChatFunctionality:
    """Test WebSocket chat-specific functionality"""
    
    @pytest.mark.asyncio
    async def test_chat_message_processing(self):
        """Test processing of chat messages through WebSocket"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
            "type": "chat_message",
            "content": "Hello, how can I help?",
            "session_id": "session_123"
        }))
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock chat service
        with patch('app.services.websocket_service.ChatService') as mock_chat_service:
            mock_chat_instance = Mock()
            mock_chat_instance.process_message.return_value = {
                "response": "I can help you with that!",
                "message_id": "msg_123"
            }
            mock_chat_service.return_value = mock_chat_instance
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            mock_chat_instance.process_message.assert_called_once()
            mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_chat_session_creation(self):
        """Test creating new chat sessions through WebSocket"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
            "type": "create_session",
            "user_label": "Customer Support"
        }))
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock chat service
        with patch('app.services.websocket_service.ChatService') as mock_chat_service:
            mock_chat_instance = Mock()
            mock_chat_instance.create_session.return_value = {
                "session_id": "session_123",
                "user_label": "Customer Support"
            }
            mock_chat_service.return_value = mock_chat_instance
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            mock_chat_instance.create_session.assert_called_once()
            mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_chat_message_with_rag(self):
        """Test chat messages that trigger RAG processing"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
            "type": "chat_message",
            "content": "What is your refund policy?",
            "session_id": "session_123"
        }))
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock RAG service
        with patch('app.services.websocket_service.RAGService') as mock_rag_service:
            mock_rag_instance = Mock()
            mock_rag_instance.process_query.return_value = {
                "answer": "Our refund policy allows returns within 30 days...",
                "sources": [{"document_id": "doc_123", "chunk_id": "chunk_456"}],
                "response_time_ms": 150
            }
            mock_rag_service.return_value = mock_rag_instance
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            mock_rag_instance.process_query.assert_called_once()
            mock_websocket.send_text.assert_called()

class TestWebSocketErrorHandling:
    """Test WebSocket error handling"""
    
    @pytest.mark.asyncio
    async def test_websocket_handles_service_errors(self):
        """Test that WebSocket handles service errors gracefully"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
            "type": "chat_message",
            "content": "Hello",
            "session_id": "session_123"
        }))
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock chat service to raise an error
        with patch('app.services.websocket_service.ChatService') as mock_chat_service:
            mock_chat_instance = Mock()
            mock_chat_instance.process_message.side_effect = Exception("Service error")
            mock_chat_service.return_value = mock_chat_instance
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            # Should send error message
            mock_websocket.send_text.assert_called()
            error_message = mock_websocket.send_text.call_args[0][0]
            assert "error" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_websocket_handles_database_errors(self):
        """Test that WebSocket handles database errors gracefully"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
            "type": "create_session",
            "user_label": "Customer"
        }))
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock database error
        with patch('app.services.websocket_service.ChatService') as mock_chat_service:
            mock_chat_instance = Mock()
            mock_chat_instance.create_session.side_effect = Exception("Database connection failed")
            mock_chat_service.return_value = mock_chat_instance
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            # Should send error message
            mock_websocket.send_text.assert_called()
            error_message = mock_websocket.send_text.call_args[0][0]
            assert "error" in error_message.lower()
    
    @pytest.mark.asyncio
    async def test_websocket_handles_rate_limiting(self):
        """Test that WebSocket handles rate limiting"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
            "type": "chat_message",
            "content": "Hello",
            "session_id": "session_123"
        }))
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock rate limiting
        with patch('app.services.websocket_service.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.is_allowed.return_value = False
            
            await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            # Should send rate limit message
            mock_websocket.send_text.assert_called()
            rate_limit_message = mock_websocket.send_text.call_args[0][0]
            assert "rate limit" in rate_limit_message.lower() or "too many" in rate_limit_message.lower()

class TestWebSocketSecurity:
    """Test WebSocket security measures"""
    
    def test_websocket_token_validation(self):
        """Test WebSocket token validation"""
        from app.api.websocket.chat_ws import verify_websocket_token
        
        # Test valid token
        with patch('app.api.websocket.chat_ws.jwt.decode') as mock_decode:
            mock_decode.return_value = {"user_id": "123", "workspace_id": "ws_123"}
            
            result = verify_websocket_token("valid_token")
            assert result == {"user_id": "123", "workspace_id": "ws_123"}
    
    def test_websocket_invalid_token_rejection(self):
        """Test that invalid tokens are rejected"""
        from app.api.websocket.chat_ws import verify_websocket_token
        
        # Test invalid token
        with patch('app.api.websocket.chat_ws.jwt.decode') as mock_decode:
            mock_decode.side_effect = Exception("Invalid token")
            
            result = verify_websocket_token("invalid_token")
            assert result is None
    
    def test_websocket_message_validation(self):
        """Test WebSocket message validation"""
        websocket_service = WebSocketService()
        
        # Test valid message
        valid_message = {
            "type": "chat_message",
            "content": "Hello",
            "session_id": "session_123"
        }
        
        is_valid = websocket_service.validate_message(valid_message)
        assert is_valid is True
        
        # Test invalid message (missing required fields)
        invalid_message = {
            "type": "chat_message",
            "content": "Hello"
            # Missing session_id
        }
        
        is_valid = websocket_service.validate_message(invalid_message)
        assert is_valid is False
    
    def test_websocket_content_filtering(self):
        """Test WebSocket content filtering for malicious input"""
        websocket_service = WebSocketService()
        
        # Test malicious content
        malicious_message = {
            "type": "chat_message",
            "content": "<script>alert('xss')</script>",
            "session_id": "session_123"
        }
        
        filtered_message = websocket_service.filter_content(malicious_message)
        assert "<script>" not in filtered_message["content"]
        assert "alert" not in filtered_message["content"]

class TestWebSocketPerformance:
    """Test WebSocket performance and scalability"""
    
    @pytest.mark.asyncio
    async def test_websocket_concurrent_connections(self):
        """Test handling multiple concurrent WebSocket connections"""
        websocket_service = WebSocketService()
        
        # Mock multiple WebSocket connections
        mock_websockets = []
        for i in range(10):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.receive_text = AsyncMock(return_value=json.dumps({
                "type": "chat_message",
                "content": f"Message {i}",
                "session_id": f"session_{i}"
            }))
            mock_ws.send_text = AsyncMock()
            mock_ws.close = AsyncMock()
            mock_websockets.append(mock_ws)
        
        # Mock chat service
        with patch('app.services.websocket_service.ChatService') as mock_chat_service:
            mock_chat_instance = Mock()
            mock_chat_instance.process_message.return_value = {"response": "Processed"}
            mock_chat_service.return_value = mock_chat_instance
            
            # Handle all connections concurrently
            tasks = []
            for i, mock_ws in enumerate(mock_websockets):
                task = websocket_service.handle_websocket(mock_ws, f"user_{i}", f"ws_{i}")
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # Verify all connections were handled
            for mock_ws in mock_websockets:
                mock_ws.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self):
        """Test WebSocket message throughput"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()
        
        websocket_service = WebSocketService()
        
        # Mock chat service
        with patch('app.services.websocket_service.ChatService') as mock_chat_service:
            mock_chat_instance = Mock()
            mock_chat_instance.process_message.return_value = {"response": "Processed"}
            mock_chat_service.return_value = mock_chat_instance
            
            # Send multiple messages quickly
            for i in range(100):
                mock_websocket.receive_text = AsyncMock(return_value=json.dumps({
                    "type": "chat_message",
                    "content": f"Message {i}",
                    "session_id": "session_123"
                }))
                
                await websocket_service.handle_websocket(mock_websocket, "123", "ws_123")
            
            # Verify all messages were processed
            assert mock_websocket.send_text.call_count == 100

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
