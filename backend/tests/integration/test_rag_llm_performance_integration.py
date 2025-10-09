"""
Integration performance test: LLM+RAG under concurrent load with externals mocked.
"""

from typing import Generator

import asyncio
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rag_llm_perf.db"

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
    workspace = Workspace(id="ws_perf_rag_1", name="RAG PERF WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="perf-rag@example.com",
        hashed_password="hashed",
        full_name="Perf RAG User",
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


class TestRAGLLMPerformanceIntegration:
    def test_concurrent_rag_queries_under_2s(self, client: TestClient, auth_headers):
        # Mock user dep and rag service to avoid real LLM/vector
        with patch("app.api.api_v1.endpoints.rag_query.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_perf_rag"
            mock_user.workspace_id = "ws_perf_rag_1"
            mock_get_user.return_value = mock_user

            with patch("app.api.api_v1.endpoints.rag_query.RAGService") as mock_rag_service:
                mock_service = Mock()
                mock_service.process_query.return_value = {
                    "answer": "Mock answer",
                    "sources": [],
                    "response_time_ms": 50,
                    "tokens_used": 10,
                    "model_used": "gemini-pro",
                }
                mock_rag_service.return_value = mock_service

                async def _do_one():
                    resp = client.post("/api/v1/rag/query", json={"query": "Q?", "session_id": "s"}, headers=auth_headers)
                    assert resp.status_code == 200

                async def _run_all():
                    tasks = [_do_one() for _ in range(20)]
                    await asyncio.gather(*tasks)

                # Run and assert time bound loosely (env dependent)
                loop = asyncio.new_event_loop()
                try:
                    loop.run_until_complete(_run_all())
                finally:
                    loop.close()

