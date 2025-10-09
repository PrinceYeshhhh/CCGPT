"""
Integration test for dashboard access after login (protected analytics/dashboard endpoints).
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dashboard_access.db"

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
    workspace = Workspace(id="ws_dash_1", name="Dash WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="dash@example.com",
        hashed_password="hashed",
        full_name="Dash User",
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


class TestDashboardAccessIntegration:
    def test_dashboard_endpoints_require_auth(self, client: TestClient):
        resp = client.get("/api/v1/analytics/summary")
        assert resp.status_code == 401

    def test_dashboard_endpoints_after_login(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/analytics/summary", headers=auth_headers)
        assert resp.status_code == 200
        resp = client.get("/api/v1/analytics/queries-over-time?days=7", headers=auth_headers)
        assert resp.status_code == 200

