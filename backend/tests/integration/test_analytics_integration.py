"""
Integration tests for analytics after user activity using DB override.
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_analytics.db"

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
    workspace = Workspace(id="ws_analytics_1", name="Analytics WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="analytics@example.com",
        hashed_password="hashed",
        full_name="Analytics User",
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


class TestAnalyticsIntegration:
    def test_analytics_after_chat_activity(self, client: TestClient, auth_headers):
        headers, workspace = auth_headers

        # Create a chat session and send a message to generate activity
        session_payload = {
            "workspace_id": workspace.id,
            "user_label": "Customer"
        }
        resp = client.post("/api/v1/chat/sessions", json=session_payload, headers=headers)
        assert resp.status_code == 201
        session_id = resp.json()["session_id"]

        message_payload = {"content": "Hello", "session_id": session_id}
        resp = client.post("/api/v1/chat/message", json=message_payload, headers=headers)
        assert resp.status_code == 200

        # Fetch analytics
        resp = client.get("/api/v1/analytics/workspace", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # Validate basic structure
        assert "total_queries" in data
        assert "total_documents" in data

