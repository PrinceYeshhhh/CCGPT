from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security import CSRFProtectionMiddleware


def create_test_app() -> TestClient:
    app = FastAPI()
    app.add_middleware(CSRFProtectionMiddleware)

    @app.post("/submit")
    async def submit():  # pragma: no cover - trivial endpoint for middleware test
        return {"ok": True}

    return TestClient(app)


def test_post_without_csrf_header_is_forbidden():
    client = create_test_app()
    res = client.post("/submit", json={})
    assert res.status_code == 403
    assert res.json().get("detail") in {"CSRF token required", "Invalid CSRF token"}


def test_post_with_bearer_auth_is_allowed():
    client = create_test_app()
    res = client.post("/submit", json={}, headers={"Authorization": "Bearer testtoken"})
    assert res.status_code == 200
    assert res.json() == {"ok": True}


