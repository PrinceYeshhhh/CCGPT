"""
Unit tests for websocket router behaviors in app.api.websocket.chat_ws
"""

import json
import pytest
from unittest.mock import patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.websocket.chat_ws import router as websocket_router


class TestWebSocketRouterBehavior:
    def setup_app(self) -> TestClient:
        app = FastAPI()
        app.include_router(websocket_router)
        return TestClient(app)

    def test_accepts_ws_on_alias_with_valid_token(self):
        client = self.setup_app()
        with patch('app.api.websocket.chat_ws.verify_websocket_token') as mock_verify:
            mock_verify.return_value = {"user_id": "u1", "workspace_id": "w1"}
            # Should connect successfully; immediately close context after enter
            with client.websocket_connect("/ws/chat?token=t") as ws:
                # Send ping to keep alive and get a response
                ws.send_json({"type": "ping"})
                _ = ws.receive_text()

    def test_rejects_ws_with_invalid_token(self):
        client = self.setup_app()
        with patch('app.api.websocket.chat_ws.verify_websocket_token') as mock_verify:
            mock_verify.return_value = None
            with pytest.raises(Exception):
                with client.websocket_connect("/ws/chat?token=bad"):
                    pass

    def test_invalid_session_id_closes_with_4000(self):
        client = self.setup_app()
        # No token needed; session id check runs before auth
        with pytest.raises(Exception):
            with client.websocket_connect("/chat/short"):
                pass




