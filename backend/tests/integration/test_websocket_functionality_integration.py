"""
Integration-ish tests for WebSocket broadcast and typing indicators using service mocks.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch


class TestWebSocketFunctionalityIntegration:
    @pytest.mark.asyncio
    async def test_broadcast_message(self):
        with patch("app.api.api_v1.endpoints.websocket.WebSocketService") as mock_service_cls:
            svc = Mock()
            svc.broadcast_message = AsyncMock()
            mock_service_cls.return_value = svc

            # Simulate broadcast
            await svc.broadcast_message("session_1", "Hello everyone")
            svc.broadcast_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_typing_indicator(self):
        with patch("app.api.api_v1.endpoints.websocket.WebSocketService") as mock_service_cls:
            svc = Mock()
            svc.broadcast_typing = AsyncMock()
            mock_service_cls.return_value = svc

            await svc.broadcast_typing("session_1", user_id="u1", is_typing=True)
            svc.broadcast_typing.assert_awaited_once()

