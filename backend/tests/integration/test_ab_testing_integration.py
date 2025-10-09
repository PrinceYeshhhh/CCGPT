"""
Integration tests for A/B testing endpoints.
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ab_testing.db"

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
    workspace = Workspace(id="ws_ab_1", name="AB WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="ab@example.com",
        hashed_password="hashed",
        full_name="AB User",
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


class TestABTestingIntegration:
    def test_create_get_stop_and_conversion(self, client: TestClient, auth_headers):
        with patch("app.api.api_v1.endpoints.ab_testing.ABTestingService") as mock_service_cls:
            mock_service = Mock()
            mock_service_cls.return_value = mock_service

            # Create test
            mock_service.create_test.return_value = True
            payload = {
                "test_id": "test_btn_color",
                "name": "Button Color",
                "variants": [{"id": "A", "config": {"color": "blue"}}, {"id": "B", "config": {"color": "green"}}],
                "traffic_split": 0.5
            }
            resp = client.post("/api/v1/ab-testing/tests", params=payload, headers=auth_headers)
            assert resp.status_code == 200

            # Get all tests
            mock_service.get_all_tests.return_value = [
                {"id": "test_btn_color", "name": "Button Color"}
            ]
            resp = client.get("/api/v1/ab-testing/tests", headers=auth_headers)
            assert resp.status_code == 200

            # Get test details
            mock_service.get_test_results.return_value = {"id": "test_btn_color", "conversions": {"A": 10, "B": 12}}
            resp = client.get("/api/v1/ab-testing/tests/test_btn_color", headers=auth_headers)
            assert resp.status_code == 200

            # Track conversion
            mock_service.track_conversion.return_value = True
            resp = client.post("/api/v1/ab-testing/tests/test_btn_color/conversion", params={"conversion_type": "signup"}, headers=auth_headers)
            assert resp.status_code == 200

            # Stop test
            mock_service.stop_test.return_value = True
            resp = client.post("/api/v1/ab-testing/tests/test_btn_color/stop", headers=auth_headers)
            assert resp.status_code == 200

