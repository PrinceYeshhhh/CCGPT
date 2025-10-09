"""
Integration test for subscription tiers and query quota enforcement.
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
from app.models import User, Workspace, Subscription
from app.services.auth import AuthService


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_subscription_quota.db"

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
def auth_headers_and_workspace(db_session):
    workspace = Workspace(id="ws_quota_1", name="Quota WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="quota@example.com",
        hashed_password="hashed",
        full_name="Quota User",
        workspace_id=workspace.id,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create a starter subscription with a low monthly quota
    sub = Subscription(
        workspace_id=workspace.id,
        stripe_customer_id="cus_quota",
        tier="starter",
        status="active",
        seats=1,
        monthly_query_quota=3,
        queries_this_period=3,  # Already used up
    )
    db_session.add(sub)
    db_session.commit()

    token = AuthService(None).create_access_token({
        "user_id": str(user.id),
        "email": user.email,
    })
    return {"Authorization": f"Bearer {token}"}, workspace


class TestSubscriptionQuotaEnforcementIntegration:
    def test_quota_exceeded_blocks_rag_query(self, client: TestClient, auth_headers_and_workspace):
        headers, _ = auth_headers_and_workspace

        with patch("app.api.api_v1.endpoints.rag_query.get_current_user") as mock_get_user:
            mock_user = Mock()
            mock_user.id = "user_quota"
            mock_user.workspace_id = "ws_quota_1"
            mock_get_user.return_value = mock_user

            # The endpoint should detect quota exceeded and return 402
            resp = client.post(
                "/api/v1/rag/query",
                json={"query": "Test?", "session_id": "s"},
                headers=headers,
            )
            assert resp.status_code in (402, 429)

