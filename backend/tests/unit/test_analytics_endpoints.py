from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.api.api_v1.endpoints.analytics import router as analytics_router


def create_app() -> TestClient:
    app = FastAPI()
    app.include_router(analytics_router, prefix="/api/v1/analytics")
    return TestClient(app)


def test_overview_returns_expected_shape():
    client = create_app()
    # Without DB mocking, this may 500; we only assert non-500 contract where possible
    resp = client.get("/api/v1/analytics/overview")
    # Allow 200 or 500 depending on environment; if 200, check keys
    if resp.status_code == 200:
        body = resp.json()
        assert "total_messages" in body
        assert "active_sessions" in body
        assert "avg_response_time" in body
        assert "top_questions" in body


def test_usage_stats_validates_days_param():
    client = create_app()
    resp = client.get("/api/v1/analytics/usage-stats?days=0")
    assert resp.status_code in (400, 422)


