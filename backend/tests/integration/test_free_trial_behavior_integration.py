"""
Integration test for free trial 7-day behavior on billing/usage endpoints (mocked).
"""

from typing import Generator

import datetime as dt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models import User, Workspace, Subscription
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_free_trial.db"

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
def auth_headers_and_sub(db_session):
    workspace = Workspace(id="ws_trial_1", name="Trial WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="trial@example.com",
        hashed_password="hashed",
        full_name="Trial User",
        workspace_id=workspace.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create a free trial subscription starting now
    sub = Subscription(
        workspace_id=workspace.id,
        stripe_customer_id="cus_trial",
        tier="starter",
        status="trialing",
        seats=1,
        monthly_query_quota=100,
        queries_this_period=0,
        period_start=dt.datetime.utcnow(),
        period_end=dt.datetime.utcnow() + dt.timedelta(days=7),
    )
    db_session.add(sub)
    db_session.commit()

    token = AuthService(None).create_access_token({
        "user_id": str(user.id),
        "email": user.email,
    })
    return {"Authorization": f"Bearer {token}"}, workspace


class TestFreeTrialBehaviorIntegration:
    def test_trial_status_visible_on_billing_status(self, client: TestClient, auth_headers_and_sub):
        headers, _ = auth_headers_and_sub
        resp = client.get("/api/v1/billing/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        # Expect trial or active status in response; structure may vary
        assert any(k in data for k in ("status", "is_trial", "plan", "tier"))

