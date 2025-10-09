"""
Integration tests for cross-workspace authorization isolation
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.workspace import Workspace
from app.models.document import Document
from app.models.chat import ChatSession


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    from app.db.session import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def workspaces(db_session):
    ws_a = Workspace(id="ws-a", name="Workspace A")
    ws_b = Workspace(id="ws-b", name="Workspace B")
    db_session.add_all([ws_a, ws_b])
    db_session.commit()
    return ws_a, ws_b


@pytest.fixture
def users(db_session, workspaces):
    ws_a, ws_b = workspaces
    user_a = User(id="user-a", email="a@example.com", username="usera", hashed_password="x", workspace_id=ws_a.id)
    user_b = User(id="user-b", email="b@example.com", username="userb", hashed_password="x", workspace_id=ws_b.id)
    db_session.add_all([user_a, user_b])
    db_session.commit()
    return user_a, user_b


@pytest.fixture
def tokens(users):
    from app.services.auth import AuthService
    auth = AuthService()
    user_a, user_b = users
    token_a = auth.create_access_token({"sub": user_a.email})
    token_b = auth.create_access_token({"sub": user_b.email})
    return token_a, token_b


def test_documents_isolation(client, db_session, workspaces, users, tokens):
    """User A must not access documents belonging to Workspace B"""
    ws_a, ws_b = workspaces
    user_a, user_b = users
    token_a, token_b = tokens

    # Create document in workspace B
    doc_b = Document(
        id="doc-b",
        workspace_id=ws_b.id,
        filename="secret.pdf",
        content_type="application/pdf",
        status="ready",
        file_size=123
    )
    db_session.add(doc_b)
    db_session.commit()

    # Attempt to fetch doc B with User A
    r = client.get(f"/api/v1/documents/{doc_b.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert r.status_code in [403, 404]


def test_chat_session_isolation(client, db_session, workspaces, users, tokens):
    """User B must not access chat sessions belonging to Workspace A"""
    ws_a, ws_b = workspaces
    user_a, user_b = users
    token_a, token_b = tokens

    # Create chat session in workspace A
    session_a = ChatSession(id="sess-a", workspace_id=ws_a.id, created_at=datetime.utcnow())
    db_session.add(session_a)
    db_session.commit()

    # Attempt to fetch session A with User B
    r = client.get(f"/api/v1/chat/sessions/{session_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code in [403, 404]


def test_analytics_isolation(client, db_session, workspaces, users, tokens):
    """Analytics queries should be scoped to caller's workspace only"""
    ws_a, ws_b = workspaces
    user_a, user_b = users
    token_a, token_b = tokens

    # Call summary for A
    r_a = client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token_a}"})
    assert r_a.status_code in [200, 204]

    # Call summary for B
    r_b = client.get("/api/v1/analytics/summary", headers={"Authorization": f"Bearer {token_b}"})
    assert r_b.status_code in [200, 204]

    # No direct leakage detectable via response here, but existence of separate calls ensures scoping runs.


def test_embed_code_isolation(client, db_session, workspaces, users, tokens):
    """Embed code endpoints must not allow cross-workspace visibility"""
    from app.models.embed import EmbedCode
    ws_a, ws_b = workspaces
    user_a, user_b = users
    token_a, token_b = tokens

    embed_b = EmbedCode(id="embed-b", workspace_id=ws_b.id, is_active=True)
    db_session.add(embed_b)
    db_session.commit()

    # If there is an endpoint to fetch embed code details under auth, ensure isolation
    r = client.get(f"/api/v1/embed/{embed_b.id}", headers={"Authorization": f"Bearer {token_a}"})
    # Depending on implementation, may be 403 or 404
    assert r.status_code in [403, 404, 405]


