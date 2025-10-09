"""
Integration test for ingesting synthetic real-world analytics and verifying correlations via analytics endpoints.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_realworld_analytics.db"

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
    workspace = Workspace(id="ws_rw_1", name="RW WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="rw@example.com",
        hashed_password="hashed",
        full_name="RW User",
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


class TestRealWorldAnalyticsIntegration:
    def test_ingest_like_usage_and_fetch_correlations(self, client: TestClient, auth_headers):
        # Simulate usage: create a chat session and messages to generate analytics
        session_payload = {"workspace_id": "ws_rw_1", "user_label": "Visitor"}
        resp = client.post("/api/v1/chat/sessions", json=session_payload, headers=auth_headers)
        assert resp.status_code == 201
        session_id = resp.json()["session_id"]

        for _ in range(3):
            msg_payload = {"content": "How do refunds work?", "session_id": session_id}
            resp = client.post("/api/v1/chat/message", json=msg_payload, headers=auth_headers)
            assert resp.status_code == 200

        # Verify enhanced analytics endpoints respond with structured data
        resp = client.get("/api/v1/analytics/summary", headers=auth_headers)
        assert resp.status_code == 200

        resp = client.get("/api/v1/analytics/top-queries?limit=5&days=7", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

        resp = client.get("/api/v1/analytics/queries-over-time?days=7", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
