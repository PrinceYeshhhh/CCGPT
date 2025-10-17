"""
Unit tests for app.services.websocket_security websocket_security_service
"""

import pytest
from unittest.mock import Mock, patch

from app.services.websocket_security import websocket_security_service


class DummyRedis:
    def __init__(self):
        self.store = {}
    def get(self, k):
        v = self.store.get(k)
        return str(v) if isinstance(v, int) else v
    def incr(self, k):
        self.store[k] = int(self.store.get(k, 0) or 0) + 1
    def decr(self, k):
        self.store[k] = int(self.store.get(k, 0) or 0) - 1
    def expire(self, k, _ttl):
        return True


def test_validate_message_accepts_valid_chat():
    msg = {"type": "chat", "content": "hello"}
    assert websocket_security_service.validate_message(msg) is True


def test_validate_message_rejects_script():
    msg = {"type": "chat", "content": "<script>alert(1)</script>"}
    assert websocket_security_service.validate_message(msg) is False


@pytest.mark.asyncio
async def test_check_message_rate_limit_blocks_when_threshold_exceeded(monkeypatch):
    # Inject dummy redis
    svc = websocket_security_service
    svc.redis_client = DummyRedis()
    user_id = "u1"
    # Fill counters to limit
    for _ in range(svc.rate_limits["messages_per_minute"]):
        await svc.record_message(user_id)
    assert await svc.check_message_rate_limit(user_id) is False


@pytest.mark.asyncio
async def test_check_connection_limits_uses_in_memory_counts(monkeypatch):
    svc = websocket_security_service
    svc.redis_client = DummyRedis()
    uid = "u-limit"
    client_ip = "127.0.0.1"
    svc.connection_limits["per_user"] = 1
    # First connection ok
    assert await svc.check_connection_limits(uid, client_ip) is True
    svc.register_connection(uid, "conn-1", {"client_ip": client_ip})
    # Second should now fail
    assert await svc.check_connection_limits(uid, client_ip) is False


