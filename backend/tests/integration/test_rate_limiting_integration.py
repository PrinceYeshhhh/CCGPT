"""
Integration tests for rate-limiting behavior with deterministic env flags.
"""

from typing import Generator

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rate_limit.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def set_deterministic_rate_limit_env():
    # Ensure rate limiting is enabled and thresholds are low for tests
    prev_enabled = os.environ.get("RATE_LIMITS_ENABLED")
    prev_requests = os.environ.get("RATE_LIMIT_MAX_REQUESTS_PER_MINUTE")
    os.environ["RATE_LIMITS_ENABLED"] = "true"
    os.environ["RATE_LIMIT_MAX_REQUESTS_PER_MINUTE"] = "5"
    try:
        yield
    finally:
        if prev_enabled is None:
            os.environ.pop("RATE_LIMITS_ENABLED", None)
        else:
            os.environ["RATE_LIMITS_ENABLED"] = prev_enabled
        if prev_requests is None:
            os.environ.pop("RATE_LIMIT_MAX_REQUESTS_PER_MINUTE", None)
        else:
            os.environ["RATE_LIMIT_MAX_REQUESTS_PER_MINUTE"] = prev_requests


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
    workspace = Workspace(id="ws_rl_1", name="RL WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="rl@example.com",
        hashed_password="hashed",
        full_name="RL User",
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


class TestRateLimitingIntegration:
    def test_rate_limit_kicks_in(self, client: TestClient, auth_headers):
        # Make repeated requests to a protected endpoint
        last_status = None
        for _ in range(20):
            resp = client.get("/api/v1/documents/", headers=auth_headers)
            last_status = resp.status_code
            if last_status == 429:
                break

        assert last_status == 429

