"""
Integration tests for embed origin/referrer checks and per-embed rate limiting.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import get_db, Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_embed_origin_rl.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestEmbedOriginRateLimitIntegration:
    def test_origin_referer_headers_present(self, client: TestClient):
        with patch("app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service.check_ip_rate_limit", return_value=(True, {"limit": 10, "remaining": 9, "reset_time": Mock(timestamp=lambda: 0)})), \
             patch("app.api.api_v1.endpoints.embed_enhanced.EmbedService") as mock_embed_service:
            embed_code = Mock()
            embed_code.id = "embed_1"
            embed_code.is_active = True
            embed_code.expires_at = None
            svc = Mock()
            svc.get_embed_code_by_api_key.return_value = embed_code
            mock_embed_service.return_value = svc

            headers = {"X-Client-API-Key": "good", "X-Embed-Code-ID": "embed_1", "Origin": "https://customer.com", "Referer": "https://customer.com/page"}
            resp = client.post("/api/v1/embed/chat/message", json={"message": "Hi"}, headers=headers)
            assert resp.status_code in (200, 201)

    def test_per_embed_rate_limit_blocked(self, client: TestClient):
        with patch("app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service.check_ip_rate_limit", return_value=(True, {"limit": 10, "remaining": 9, "reset_time": Mock(timestamp=lambda: 0)})), \
             patch("app.api.api_v1.endpoints.embed_enhanced.EmbedService") as mock_embed_service, \
             patch("app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service.check_embed_rate_limit", return_value=(False, {"limit": 5, "remaining": 0, "reset_time": Mock(timestamp=lambda: 0)})):
            embed_code = Mock()
            embed_code.id = "embed_1"
            embed_code.is_active = True
            embed_code.expires_at = None
            svc = Mock()
            svc.get_embed_code_by_api_key.return_value = embed_code
            mock_embed_service.return_value = svc

            headers = {"X-Client-API-Key": "good", "X-Embed-Code-ID": "embed_1"}
            resp = client.post("/api/v1/embed/chat/message", json={"message": "Hi"}, headers=headers)
            assert resp.status_code == 429
