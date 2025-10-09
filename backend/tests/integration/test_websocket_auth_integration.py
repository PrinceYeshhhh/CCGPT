"""
Integration-style tests for WebSocket auth matrix (JWT vs API key) via websocket_security_service.
"""

import types
import pytest
from unittest.mock import Mock, patch

from app.services.websocket_security import websocket_security_service


class DummyWebSocket:
    def __init__(self, client_host: str = "127.0.0.1"):
        self.client = types.SimpleNamespace(host=client_host)


@pytest.mark.asyncio
async def test_ws_auth_with_jwt_success():
    dummy_ws = DummyWebSocket()

    with patch("app.services.websocket_security.AuthService") as mock_auth, \
         patch("app.services.websocket_security.SessionLocal") as mock_session_local:
        # Mock JWT verification
        auth_instance = Mock()
        auth_instance.verify_token.return_value = {"sub": "user@example.com"}
        mock_auth.return_value = auth_instance

        # Mock DB user lookup
        db = Mock()
        user = Mock()
        user.id = "user_id_1"
        user.workspace_id = "ws_id_1"
        query = Mock()
        query.filter.return_value.first.return_value = user
        db.query.return_value = query
        mock_session_local.return_value = db

        result = await websocket_security_service.authenticate_connection(
            dummy_ws, token="valid.jwt", client_api_key=None
        )

        assert result is not None
        assert result["auth_type"] == "jwt"
        assert result["workspace_id"] == "ws_id_1"


@pytest.mark.asyncio
async def test_ws_auth_with_api_key_success():
    dummy_ws = DummyWebSocket()

    with patch("app.services.websocket_security.EmbedService") as mock_embed_service:
        db = Mock()
        embed_code = Mock()
        embed_code.id = "embed_123"
        embed_code.user_id = "user_id_2"
        embed_code.workspace_id = "ws_id_2"
        embed_code.is_active = True
        svc = Mock()
        svc.get_embed_code_by_api_key.return_value = embed_code
        mock_embed_service.return_value = svc

        result = await websocket_security_service.authenticate_connection(
            dummy_ws, token=None, client_api_key="good_key"
        )

        assert result is not None
        assert result["auth_type"] == "api_key"
        assert result["workspace_id"] == "ws_id_2"


@pytest.mark.asyncio
async def test_ws_auth_failure_invalid_credentials():
    dummy_ws = DummyWebSocket()

    # Invalid JWT
    with patch("app.services.websocket_security.AuthService") as mock_auth:
        auth_instance = Mock()
        auth_instance.verify_token.return_value = None
        mock_auth.return_value = auth_instance
        result = await websocket_security_service.authenticate_connection(
            dummy_ws, token="bad.jwt", client_api_key=None
        )
        assert result is None

    # Invalid API key
    with patch("app.services.websocket_security.EmbedService") as mock_embed_service:
        svc = Mock()
        svc.get_embed_code_by_api_key.return_value = None
        mock_embed_service.return_value = svc
        result = await websocket_security_service.authenticate_connection(
            dummy_ws, token=None, client_api_key="bad_key"
        )
        assert result is None

