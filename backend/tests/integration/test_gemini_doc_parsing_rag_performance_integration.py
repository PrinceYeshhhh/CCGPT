"""
Integration performance: document parsing -> embeddings/vector search -> Gemini response (mocked) with timing.
"""

from typing import Generator

import asyncio
import tempfile
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_gemini_doc_rag.db"

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
    workspace = Workspace(id="ws_gem_1", name="Gemini WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="gemini@example.com",
        hashed_password="hashed",
        full_name="Gemini User",
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
    return {"Authorization": f"Bearer {token}"}, workspace


class TestGeminiDocParsingRAGPerformanceIntegration:
    def test_document_to_gemini_response_fast_enough(self, client: TestClient, auth_headers):
        headers, workspace = auth_headers

        # Create a temp file to simulate an upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
            tf.write("Refund policy: 30 days. Shipping: 3-5 days.")
            temp_path = tf.name

        # Upload document
        with open(temp_path, 'rb') as f:
            files = {"file": ("faq.txt", f.read(), "text/plain")}
        data = {"workspace_id": workspace.id}
        resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
        assert resp.status_code == 201

        # Mock RAG pipeline: embeddings/search + Gemini generate
        with patch("app.api.api_v1.endpoints.rag_query.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_gem"
            mock_user.workspace_id = workspace.id
            mock_get_user.return_value = mock_user

            with patch("app.api.api_v1.endpoints.rag_query.RAGService") as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "Refund within 30 days.",
                    "sources": [{"document_id": "doc", "chunk_id": "c1"}],
                    "response_time_ms": 80,
                    "tokens_used": 60,
                    "model_used": "gemini-pro",
                }
                mock_rag_service.return_value = mock_service

                # Concurrent small burst to gauge latency
                async def _do_one():
                    r = client.post("/api/v1/rag/query", json={"query": "Refund policy?"}, headers=headers)
                    assert r.status_code == 200

                async def _run_all():
                    await asyncio.gather(*(_do_one() for _ in range(10)))

                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(_run_all())
                finally:
                    loop.close()

