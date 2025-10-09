"""
Integration tests for white-label webhook flow.
"""

import json
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import app
from app.core.database import get_db, Base
from app.models import Workspace, Subscription


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_white_label_webhook.db"

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


def _white_label_checkout_event(workspace_id: str = "ws_wl_1") -> dict:
    return {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_wl",
                "customer": "cus_test_wl",
                "metadata": {"workspace_id": workspace_id},
                "customer_email": "buyer@example.com",
            }
        },
    }


class TestWhiteLabelWebhookIntegration:
    def test_invalid_signature_returns_400(self, client: TestClient):
        body = json.dumps({}).encode()
        # Missing signature
        resp = client.post("/api/v1/white-label/webhook", data=body, headers={"Content-Type": "application/json"})
        assert resp.status_code == 400

        with patch("app.services.stripe_service.stripe_service.parse_webhook_event", return_value=None):
            resp = client.post(
                "/api/v1/white-label/webhook",
                data=body,
                headers={"Content-Type": "application/json", "Stripe-Signature": "bad"},
            )
            assert resp.status_code == 400

    def test_checkout_completed_creates_subscription_and_updates_plan(self, client: TestClient, db_session):
        # Arrange: workspace exists
        workspace = Workspace(id="ws_wl_1", name="WL WS")
        db_session.add(workspace)
        db_session.commit()

        event = _white_label_checkout_event(workspace_id="ws_wl_1")
        body = json.dumps({}).encode()

        with patch("app.services.stripe_service.stripe_service.parse_webhook_event", return_value=event):
            resp = client.post(
                "/api/v1/white-label/webhook",
                data=body,
                headers={"Content-Type": "application/json", "Stripe-Signature": "whsec_test"},
            )
        assert resp.status_code == 200

        # Verify DB updates
        updated_ws = db_session.query(Workspace).filter(Workspace.id == "ws_wl_1").first()
        assert updated_ws.plan == "white_label"
        sub = (
            db_session.query(Subscription)
            .filter(Subscription.workspace_id == "ws_wl_1", Subscription.tier == "white_label")
            .first()
        )
        assert sub is not None
        assert sub.status == "active"

