"""
Integration test for full flow: document upload -> RAG query -> analytics fetch.
"""

from typing import Generator

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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_doc_rag_analytics.db"

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
    workspace = Workspace(id="ws_flow_1", name="Flow WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="flow@example.com",
        hashed_password="hashed",
        full_name="Flow User",
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


class TestDocRAGAnalyticsFlowIntegration:
    def test_flow(self, client: TestClient, auth_headers):
        headers, workspace = auth_headers

        # Upload document
        files = {"file": ("faq.txt", b"Q: Refund? A: 30 days.", "text/plain")}
        data = {"workspace_id": workspace.id}
        resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
        assert resp.status_code == 201
        doc_id = resp.json()["document_id"]

        # RAG query (mock RAG service to return known answer + source)
        with patch("app.api.api_v1.endpoints.rag_query.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_flow"
            mock_user.workspace_id = workspace.id
            mock_get_user.return_value = mock_user

            with patch("app.api.api_v1.endpoints.rag_query.RAGService") as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "Refund within 30 days.",
                    "sources": [{"document_id": doc_id, "chunk_id": "c1", "content": "Refund? 30 days"}],
                    "response_time_ms": 100,
                    "tokens_used": 50,
                    "model_used": "gemini-pro",
                }
                mock_rag_service.return_value = mock_service

                payload = {"query": "Refund policy?", "session_id": "sess_flow"}
                resp = client.post("/api/v1/rag/query", json=payload, headers=headers)
                assert resp.status_code == 200

        # Fetch analytics summary after the activity
        resp = client.get("/api/v1/analytics/summary", headers=headers)
        assert resp.status_code == 200

