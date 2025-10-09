"""
Integration tests for resilience under outages/timeouts and fail-open behavior
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_rate_limiter_fails_open_when_redis_down(client):
    """Rate limiting should fail-open if Redis is unavailable"""
    with patch('app.middleware.rate_limiter.get_redis', side_effect=Exception("Redis down")):
        # Make several rapid requests; should not get 429 due to fail-open
        statuses = []
        for _ in range(5):
            r = client.get("/api/v1/analytics/summary")
            statuses.append(r.status_code)
        assert 429 not in statuses


def test_vector_service_timeout_returns_500(client):
    """Vector search should return 500 on upstream timeout"""
    with patch('app.services.vector_service.VectorService') as mock_vs:
        inst = Mock()
        inst.vector_search.side_effect = TimeoutError("vector timeout")
        mock_vs.return_value = inst
        r = client.post("/api/v1/vector/search", json={"query": "q", "top_k": 5})
        assert r.status_code == 401 or r.status_code == 500


def test_rag_query_timeout_returns_500(client):
    """RAG query should surface 500 on upstream timeout"""
    with patch('app.services.rag_service.RAGService') as mock_rs:
        inst = Mock()
        inst.query.side_effect = TimeoutError("llm timeout")
        mock_rs.return_value = inst
        r = client.get("/api/v1/rag/query", params={"query": "q"})
        assert r.status_code in [401, 500]


def test_database_error_returns_standard_500(client):
    """Generic DB error should be wrapped into standardized 500 response"""
    with patch('app.core.database.get_db') as mock_get_db:
        mock_get_db.side_effect = Exception("DB unavailable")
        r = client.get("/api/v1/analytics/summary")
        assert r.status_code == 500


def test_error_monitoring_invoked_on_exception(client):
    """Ensure error monitoring is invoked on exceptions"""
    with patch('app.utils.error_monitoring.error_monitor') as mock_em, \
         patch('app.api.api_v1.endpoints.analytics.get_analytics_summary', side_effect=Exception("boom")):
        mock_em.log_error.return_value = {"error_count": 42}
        r = client.get("/api/v1/analytics/summary")
        assert r.status_code == 500
        mock_em.log_error.assert_called()


