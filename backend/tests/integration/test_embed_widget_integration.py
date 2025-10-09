"""
Integration test for embed widget generation API with service mocked and DB override.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_embed_widget.db"

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
    workspace = Workspace(id="ws_embed_1", name="Embed WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="embed@example.com",
        hashed_password="hashed",
        full_name="Embed User",
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


class TestEmbedWidgetIntegration:
    def test_generate_embed_widget(self, client: TestClient, auth_headers):
        with patch("app.api.api_v1.endpoints.embed_enhanced.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_embed"
            mock_user.workspace_id = "ws_embed_1"
            mock_get_user.return_value = mock_user

            with patch("app.api.api_v1.endpoints.embed_enhanced.EmbedService") as mock_embed_service:
                mock_service = Mock()
                mock_embed_code = Mock()
                mock_embed_code.id = "embed_123"
                mock_embed_code.client_api_key = "api_key_123"
                mock_embed_code.default_config = {"theme": {"primary": "#4f46e5"}}
                mock_service.generate_embed_code.return_value = mock_embed_code
                mock_service.get_embed_snippet.return_value = "<script>/* widget */</script>"
                mock_embed_service.return_value = mock_service

                payload = {
                    "workspace_id": "ws_embed_1",
                    "code_name": "Test Widget",
                    "config": {"theme": {"primary": "#4f46e5"}},
                }
                resp = client.post("/api/v1/embed/generate", json=payload, headers=auth_headers)
                assert resp.status_code == 201
                data = resp.json()
                assert "embed_code_id" in data
                assert "client_api_key" in data
                assert "embed_snippet" in data

