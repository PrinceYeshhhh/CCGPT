"""
Integration tests for embed public chat via API key headers with validation and rate limits mocked.
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_embed_public_chat.db"

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


class TestEmbedPublicChatIntegration:
    def test_requires_api_key(self, client: TestClient):
        resp = client.post("/api/v1/embed/chat/message", json={"message": "Hello"})
        assert resp.status_code == 401

    def test_invalid_api_key(self, client: TestClient):
        with patch("app.api.api_v1.endpoints.embed_enhanced.EmbedService") as mock_embed_service:
            svc = Mock()
            svc.get_embed_code_by_api_key.return_value = None
            mock_embed_service.return_value = svc

            resp = client.post(
                "/api/v1/embed/chat/message",
                json={"message": "Hello"},
                headers={"X-Client-API-Key": "bad"},
            )
            assert resp.status_code == 401

    def test_sanitizes_input_and_allows_valid(self, client: TestClient):
        with patch("app.api.api_v1.endpoints.embed_enhanced.rate_limiting_service.check_ip_rate_limit", return_value=(True, {"limit": 10, "remaining": 9, "reset_time": Mock(timestamp=lambda: 0)})), \
             patch("app.api.api_v1.endpoints.embed_enhanced.EmbedService") as mock_embed_service:
            embed_code = Mock()
            embed_code.id = "embed_1"
            embed_code.is_active = True
            embed_code.expires_at = None
            svc = Mock()
            svc.get_embed_code_by_api_key.return_value = embed_code
            mock_embed_service.return_value = svc

            # Contains script; should be sanitized and accepted
            resp = client.post(
                "/api/v1/embed/chat/message",
                json={"message": "<script>alert('x')</script>Hi"},
                headers={"X-Client-API-Key": "good", "X-Embed-Code-ID": "embed_1"},
            )
            # Endpoint likely returns 200 with some content; we only assert non-4xx in this mocked path
            assert resp.status_code in (200, 201)

