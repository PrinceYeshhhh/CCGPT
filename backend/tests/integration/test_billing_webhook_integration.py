"""
Integration tests for Stripe billing webhook handling.
Validates signature verification and DB side effects on checkout completion.
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


#
# Test database (SQLite) with StaticPool so the same in-memory DB is reused within a test
#
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_billing_webhook.db"

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
def client(db_session: sessionmaker) -> Generator[TestClient, None, None]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _build_checkout_completed_event(workspace_id: str = "ws_123", plan_tier: str = "starter") -> dict:
    return {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "customer": "cus_test_123",
                "metadata": {
                    "workspace_id": workspace_id,
                    "plan_tier": plan_tier,
                },
            }
        },
    }


class TestBillingWebhookIntegration:
    def test_invalid_signature_returns_400(self, client: TestClient):
        payload = {"dummy": True}
        body = json.dumps(payload).encode()

        # No signature header
        response = client.post(
            "/api/v1/billing/webhook",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        # Invalid signature (parser returns None)
        with patch("app.services.stripe_service.stripe_service.parse_webhook_event", return_value=None):
            response = client.post(
                "/api/v1/billing/webhook",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "bad_sig",
                },
            )
            assert response.status_code == 400

    def test_checkout_completed_updates_subscription_and_workspace(self, client: TestClient, db_session):
        # Arrange: create workspace to be upgraded
        workspace = Workspace(id="ws_123", name="Test WS")
        db_session.add(workspace)
        db_session.commit()

        event = _build_checkout_completed_event(workspace_id="ws_123", plan_tier="pro")
        body = json.dumps({}).encode()

        # Patch the parser to return our event for any body/signature
        with patch(
            "app.services.stripe_service.stripe_service.parse_webhook_event",
            return_value=event,
        ):
            response = client.post(
                "/api/v1/billing/webhook",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "whsec_test",
                },
            )

        assert response.status_code == 200
        assert response.json().get("status") == "success"

        # Assert DB updates
        updated_workspace = db_session.query(Workspace).filter(Workspace.id == "ws_123").first()
        assert updated_workspace is not None
        assert getattr(updated_workspace, "plan", None) == "pro"

        subscription = (
            db_session.query(Subscription)
            .filter(Subscription.workspace_id == "ws_123")
            .first()
        )
        assert subscription is not None
        assert subscription.status == "active"
        assert subscription.tier == "pro"

