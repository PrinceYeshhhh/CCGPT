"""
Unit tests for RealtimeChatService typing/ping and filtering
"""

import pytest
from unittest.mock import Mock, AsyncMock

from app.services.websocket_service import RealtimeChatService


@pytest.mark.asyncio
async def test_typing_start_and_stop_broadcasts():
    svc = RealtimeChatService()
    svc.websocket_manager.broadcast_to_session = AsyncMock()
    await svc._handle_typing_start("s1", "u1")
    await svc._handle_typing_stop("s1", "u1")
    assert svc.websocket_manager.broadcast_to_session.await_count == 2


@pytest.mark.asyncio
async def test_ping_sends_pong():
    svc = RealtimeChatService()
    svc.websocket_manager.send_message = AsyncMock()
    await svc._handle_ping("s1", "u1")
    svc.websocket_manager.send_message.assert_awaited()


def test_filter_content_removes_common_vectors():
    svc = RealtimeChatService()
    msg = {"type": "chat_message", "content": "<script>javascript:alert('x')</script>", "session_id": "s"}
    filtered = svc.filter_content(msg)
    assert "<script>" not in filtered["content"].lower()
    assert "javascript:" not in filtered["content"].lower()
    assert "alert" not in filtered["content"].lower()


