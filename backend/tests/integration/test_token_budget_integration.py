"""
Integration tests for token budget info and reset endpoints.
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_token_budget.db"

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
    workspace = Workspace(id="ws_tb_1", name="TB WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="tb@example.com",
        hashed_password="hashed",
        full_name="TB User",
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


class TestTokenBudgetIntegration:
    def test_token_budget_info_and_reset(self, client: TestClient, auth_headers):
        # Get token budget info
        resp = client.get("/api/v1/rag/token-budget", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "daily_limit" in data
        assert "monthly_limit" in data

        # Reset token budget
        resp = client.post("/api/v1/rag/reset-budget", headers=auth_headers)
        assert resp.status_code == 200
        assert "reset" in resp.json().get("message", "").lower()

