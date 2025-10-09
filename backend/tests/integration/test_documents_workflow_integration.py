"""
Integration tests for documents workflow: upload, status, and chunks, using real DB override.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, Document
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_documents_workflow.db"

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
    workspace = Workspace(id="ws_docs_1", name="Docs WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="docs@example.com",
        hashed_password="hashed",
        full_name="Docs User",
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


class TestDocumentsWorkflowIntegration:
    def test_upload_status_and_chunks(self, client: TestClient, db_session, auth_headers):
        headers, workspace = auth_headers

        files = {"file": ("test_document.txt", b"This is a test document content.", "text/plain")}
        data = {"workspace_id": workspace.id}

        # Upload
        resp = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
        assert resp.status_code == 201
        payload = resp.json()
        document_id = payload["document_id"]

        # Status
        resp = client.get(f"/api/v1/documents/{document_id}", headers=headers)
        assert resp.status_code == 200
        doc = resp.json()
        assert doc["filename"] == "test_document.txt"
        assert doc["status"] in ["processing", "processed"]

        # Chunks (may be empty depending on async processing)
        resp = client.get(f"/api/v1/documents/{document_id}/chunks", headers=headers)
        assert resp.status_code == 200
        chunks = resp.json()
        assert isinstance(chunks, list)

