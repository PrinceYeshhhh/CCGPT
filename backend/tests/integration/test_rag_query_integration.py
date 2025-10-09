"""
Integration tests for RAG query endpoint with externals mocked and real DB override.
"""

import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, Mock

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, Document
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rag_query.db"

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
def user_workspace_and_doc(db_session):
    workspace = Workspace(id="ws_rag_1", name="RAG WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="rag@example.com",
        hashed_password="hashed",
        full_name="RAG User",
        workspace_id=workspace.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    document = Document(
        id="doc_rag_1",
        filename="faq.txt",
        file_type="text/plain",
        file_size=100,
        workspace_id=workspace.id,
        status="processed",
    )
    db_session.add(document)
    db_session.commit()

    return user, workspace, document


@pytest.fixture
def auth_headers(user_workspace_and_doc):
    user, _, _ = user_workspace_and_doc
    token = AuthService(None).create_access_token({
        "user_id": str(user.id),
        "email": user.email,
    })
    return {"Authorization": f"Bearer {token}"}


class TestRAGQueryIntegration:
    def test_rag_query_returns_answer_and_sources(self, client: TestClient, auth_headers, user_workspace_and_doc):
        _, workspace, document = user_workspace_and_doc

        with patch("app.api.api_v1.endpoints.rag_query.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_rag"
            mock_user.workspace_id = workspace.id
            mock_get_user.return_value = mock_user

            with patch("app.api.api_v1.endpoints.rag_query.RAGService") as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "You can request a refund within 30 days.",
                    "sources": [
                        {
                            "document_id": document.id,
                            "chunk_id": "chunk_1",
                            "content": "Refund policy within 30 days",
                            "score": 0.95,
                        }
                    ],
                    "response_time_ms": 120,
                    "tokens_used": 80,
                    "model_used": "gemini-pro",
                }
                mock_rag_service.return_value = mock_service

                payload = {
                    "query": "What is your refund policy?",
                    "session_id": "sess_rag_1",
                }
                resp = client.post("/api/v1/rag/query", json=payload, headers=auth_headers)
                assert resp.status_code == 200
                data = resp.json()
                assert "answer" in data and "sources" in data
                assert data["sources"][0]["document_id"] == document.id

    def test_rag_query_enforces_auth(self, client: TestClient):
        resp = client.post("/api/v1/rag/query", json={"query": "hi"})
        # Should be 401 without auth
        assert resp.status_code == 401

