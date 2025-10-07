import pytest


@pytest.mark.skip(reason="stub: implement Stripe webhook signature verification and flows")
def test_stripe_webhook_signature_verification(client):
    # Arrange: craft payload and signature header
    # Act: POST to /api/v1/billing/webhook
    # Assert: 200 on valid signature, 400 on invalid
    pass


@pytest.mark.skip(reason="stub: implement checkout session creation happy/error path")
def test_checkout_session_creation_requires_valid_plan(authenticated_client):
    # Arrange: invalid plan value
    # Act: POST /api/v1/billing/checkout
    # Assert: 400 with validation error
    pass


