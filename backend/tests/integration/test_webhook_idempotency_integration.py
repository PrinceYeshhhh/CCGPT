"""
Integration tests for webhook idempotency (billing and white-label).
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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_webhook_idempotency.db"

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


def _billing_event(workspace_id: str = "ws_idem_1") -> dict:
    return {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_idem", "customer": "cus_idem", "metadata": {"workspace_id": workspace_id, "plan_tier": "starter"}}},
    }


def _white_label_event(workspace_id: str = "ws_idem_1") -> dict:
    return {
        "type": "checkout.session.completed",
        "data": {"object": {"id": "cs_idem_wl", "customer": "cus_idem_wl", "metadata": {"workspace_id": workspace_id}}},
    }


class TestWebhookIdempotencyIntegration:
    def test_billing_checkout_idempotent(self, client: TestClient, db_session):
        ws = Workspace(id="ws_idem_1", name="Idem WS")
        db_session.add(ws)
        db_session.commit()

        event = _billing_event()
        body = json.dumps({}).encode()

        with patch("app.services.stripe_service.stripe_service.parse_webhook_event", return_value=event):
            # First call
            r1 = client.post("/api/v1/billing/webhook", data=body, headers={"Stripe-Signature": "whsec"})
            assert r1.status_code == 200
            # Second call (duplicate)
            r2 = client.post("/api/v1/billing/webhook", data=body, headers={"Stripe-Signature": "whsec"})
            # Should still be 200 and not duplicate subscription entries
            assert r2.status_code == 200

        subs = db_session.query(Subscription).filter(Subscription.workspace_id == "ws_idem_1").all()
        assert len(subs) == 1

    def test_white_label_checkout_idempotent(self, client: TestClient, db_session):
        ws = Workspace(id="ws_idem_1", name="Idem WS")
        db_session.add(ws)
        db_session.commit()

        event = _white_label_event()
        body = json.dumps({}).encode()

        with patch("app.services.stripe_service.stripe_service.parse_webhook_event", return_value=event):
            r1 = client.post("/api/v1/white-label/webhook", data=body, headers={"Stripe-Signature": "whsec"})
            assert r1.status_code == 200
            r2 = client.post("/api/v1/white-label/webhook", data=body, headers={"Stripe-Signature": "whsec"})
            assert r2.status_code == 200

        subs = db_session.query(Subscription).filter(Subscription.workspace_id == "ws_idem_1", Subscription.tier == "white_label").all()
        assert len(subs) == 1

