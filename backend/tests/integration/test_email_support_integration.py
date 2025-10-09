"""
Integration tests for email support endpoints with EmailService mocked.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.main import app
from app.core.database import get_db, Base


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_email_support.db"

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


class TestEmailSupportIntegration:
    def test_contact_support_success(self, client: TestClient):
        payload = {
            "name": "Jane Doe",
            "organization": "Acme",
            "email": "jane@example.com",
            "question": "I need help with onboarding setup."
        }

        with patch("app.services.email_service.EmailService.send_contact_support_email", return_value=True), \
             patch("app.services.email_service.EmailService.send_confirmation_email", return_value=True):
            resp = client.post("/api/v1/support/contact", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("success") is True

    def test_contact_support_failure(self, client: TestClient):
        payload = {
            "name": "Jane Doe",
            "organization": "Acme",
            "email": "jane@example.com",
            "question": "I need help with onboarding setup."
        }

        with patch("app.services.email_service.EmailService.send_contact_support_email", return_value=False), \
             patch("app.services.email_service.EmailService.send_confirmation_email", return_value=False):
            resp = client.post("/api/v1/support/contact", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("success") is False

    def test_schedule_demo_success(self, client: TestClient):
        payload = {
            "name": "John Smith",
            "organization": "Beta Inc",
            "email": "john@example.com",
            "preferred_date": "2025-10-10T10:00:00Z",
            "notes": "We want to see analytics dashboard."
        }

        with patch("app.services.email_service.EmailService.send_demo_request_email", return_value=True), \
             patch("app.services.email_service.EmailService.send_confirmation_email", return_value=True):
            resp = client.post("/api/v1/support/schedule-demo", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("success") is True

