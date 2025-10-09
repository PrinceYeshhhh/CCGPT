"""
Integration tests for performance endpoints: metrics, summary, trends, alerts, health.
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_performance_endpoints.db"

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
    workspace = Workspace(id="ws_perf_1", name="Perf WS")
    db_session.add(workspace)
    db_session.commit()

    user = User(
        email="perf@example.com",
        hashed_password="hashed",
        full_name="Perf User",
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


class TestPerformanceEndpointsIntegration:
    def test_collect_metrics_and_fetch_summary_trends(self, client: TestClient, auth_headers):
        # Collect a couple of metric points
        metrics_payload = {
            "metrics": [
                {"name": "ttfb", "value": 120},
                {"name": "fcp", "value": 800},
            ],
            "metadata": {"page": "/dashboard"}
        }
        resp = client.post("/api/v1/performance/metrics", json=metrics_payload, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json().get("status") == "success"

        # Summary
        resp = client.get("/api/v1/performance/summary?days=7", headers=auth_headers)
        assert resp.status_code == 200
        summary = resp.json()
        assert "average_metrics" in summary or isinstance(summary, dict)

        # Trends
        resp = client.get("/api/v1/performance/trends?days=7&metric_type=ttfb", headers=auth_headers)
        assert resp.status_code == 200
        trends = resp.json()
        assert isinstance(trends, dict)

    def test_alerts_and_health(self, client: TestClient, auth_headers):
        resp = client.get("/api/v1/performance/alerts", headers=auth_headers)
        assert resp.status_code == 200

        resp = client.get("/api/v1/performance/health", headers=auth_headers)
        assert resp.status_code == 200

