import asyncio
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel
from unittest.mock import AsyncMock, patch

from app.api.api_v1.endpoints.rag_query import router as rag_router


def create_app() -> TestClient:
    app = FastAPI()
    app.include_router(rag_router, prefix="/api/v1/rag")
    return TestClient(app)


def test_rag_query_rate_limited_returns_429_with_headers():
    client = create_app()
    async def fake_check(*args, **kwargs):
        return False, {"limit": 60, "remaining": 0, "reset_time": asyncio.get_event_loop().time()}

    with patch("app.api.api_v1.endpoints.rag_query.rate_limiting_service.check_workspace_rate_limit", new=AsyncMock(side_effect=fake_check)):
        res = client.post("/api/v1/rag/query", json={"workspace_id": "1", "query": "hi"})
        assert res.status_code == 429
        # Headers should be present per endpoint contract
        assert "X-RateLimit-Limit" in res.headers
        assert "X-RateLimit-Remaining" in res.headers
        assert "X-RateLimit-Reset" in res.headers


def test_rag_query_token_budget_exceeded_returns_429():
    client = create_app()

    async def fake_rate_ok(*args, **kwargs):
        return True, {"limit": 60, "remaining": 10, "reset_time": asyncio.get_event_loop().time()}

    class FakeBudget:
        async def check_budget(self, *_, **__):
            return False, {
                "daily_limit": 100,
                "daily_used": 100,
                "monthly_limit": 1000,
                "monthly_used": 1000,
            }

    with patch("app.api.api_v1.endpoints.rag_query.rate_limiting_service.check_workspace_rate_limit", new=AsyncMock(side_effect=fake_rate_ok)):
        with patch("app.api.api_v1.endpoints.rag_query.TokenBudgetService", return_value=FakeBudget()):
            res = client.post("/api/v1/rag/query", json={"workspace_id": "1", "query": "hi"})
            assert res.status_code == 429
            assert res.json().get("detail")


