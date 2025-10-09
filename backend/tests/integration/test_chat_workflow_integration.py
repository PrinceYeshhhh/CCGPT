"""
Integration tests for chat session workflow with a real test DB override.
Covers session creation and message processing end-to-end via API.
"""

import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, ChatSession, ChatMessage
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chat_workflow.db"

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
def user_and_workspace(db_session):
    workspace = Workspace(id="ws_chat_1", name="Chat WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="chat@example.com",
        hashed_password="hashed",
        full_name="Chat User",
        workspace_id=workspace.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user, workspace


@pytest.fixture
def auth_headers(user_and_workspace):
    user, _ = user_and_workspace
    token = AuthService(None).create_access_token({
        "user_id": str(user.id),
        "email": user.email,
    })
    return {"Authorization": f"Bearer {token}"}


class TestChatWorkflowIntegration:
    def test_create_session_and_send_message(self, client: TestClient, db_session, user_and_workspace, auth_headers):
        _, workspace = user_and_workspace

        # Create session
        session_payload = {
            "workspace_id": workspace.id,
            "user_label": "Customer"
        }
        resp = client.post("/api/v1/chat/sessions", json=session_payload, headers=auth_headers)
        assert resp.status_code == 201
        session_id = resp.json()["session_id"]

        # Send message
        message_payload = {
            "content": "Hello, I need help with my order",
            "session_id": session_id,
        }
        resp = client.post("/api/v1/chat/message", json=message_payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "message_id" in data

        # DB assertions
        session = db_session.query(ChatSession).filter(ChatSession.id == session_id).first()
        assert session is not None
        messages = db_session.query(ChatMessage).filter(ChatMessage.session_id == session_id).all()
        assert len(messages) >= 1

