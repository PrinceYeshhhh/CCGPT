"""
Essential auth endpoint unit tests focused on backend contract only.
Uses existing shared fixtures from tests/conftest.py.
"""

import pytest
from fastapi import status


class TestAuthCoreEndpoints:
    """Happy-path and core error cases for auth endpoints"""

    def test_login_wrong_password(self, client, test_user):
        """Wrong password yields 401 with 'Invalid credentials' detail."""
        payload = {"identifier": test_user.email, "password": "wrong_password"}
        response = client.post("/api/v1/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_refresh_requires_valid_token(self, client, test_user):
        """Refresh with invalid token yields 401."""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()


