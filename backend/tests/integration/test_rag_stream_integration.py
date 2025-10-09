"""
Integration tests for RAG streaming endpoint (/api/v1/rag/query/stream)
with DB override and streaming chunks mocked.
"""

from typing import Generator, AsyncGenerator

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, Mock

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rag_stream.db"

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


@pytest.fixture
def auth_headers(db_session):
    workspace = Workspace(id="ws_stream_1", name="Stream WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="stream@example.com",
        hashed_password="hashed",
        full_name="Stream User",
        workspace_id=workspace.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = AuthService(None).create_access_token({
        "user_id": str(user.id),
        "email": user.email,
    })
    return {"Authorization": f"Bearer {token}"}


async def _fake_stream_chunks() -> AsyncGenerator:
    # Simplified chunk format compatible with RAGStreamChunk
    chunks = [
        {"type": "start", "content": "start"},
        {"type": "sources", "content": "source list"},
        {"type": "answer", "content": "partial"},
        {"type": "final", "content": "final answer"},
    ]
    for ch in chunks:
        await asyncio.sleep(0)
        # Provide a minimal object exposing .json()
        yield Mock(json=lambda ch=ch: json.dumps(ch))


class TestRAGStreamingIntegration:
    def test_stream_returns_event_stream(self, client: TestClient, auth_headers):
        # Mock current user dependency inside endpoint and rag service streaming generator
        with patch("app.api.api_v1.endpoints.rag_query.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_stream"
            mock_user.workspace_id = "ws_stream_1"
            mock_get_user.return_value = mock_user

            with patch("app.api.api_v1.endpoints.rag_query.RAGService") as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query_stream = Mock(return_value=_fake_stream_chunks())
                mock_rag_service.return_value = mock_service

                payload = {"query": "Test streaming?", "session_id": "sess_stream_1"}
                resp = client.post("/api/v1/rag/query/stream", json=payload, headers=auth_headers)
                assert resp.status_code == 200
                # Response is a stream; accumulate text
                text = resp.text
                # Validate that our chunks came through as SSE-like lines
                assert "data: {\"type\": \"start\"" in text
                assert "data: {\"type\": \"final\"" in text

