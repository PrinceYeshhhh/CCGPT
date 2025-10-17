from unittest.mock import patch, MagicMock
import stripe

from app.services.stripe_service import stripe_service


def test_verify_webhook_signature_invalid_returns_false():
    with patch("stripe.Webhook.construct_event") as construct:
        construct.side_effect = stripe.error.SignatureVerificationError(
            message="bad sig", sig_header="hdr", http_body=b"{}"
        )
        ok = stripe_service.verify_webhook_signature(b"{}", "bad")
        assert ok is False


def test_verify_webhook_signature_valid_returns_true():
    with patch("stripe.Webhook.construct_event") as construct:
        construct.return_value = {"type": "dummy"}
        ok = stripe_service.verify_webhook_signature(b"{}", "good")
        assert ok is True


async def test_create_checkout_session_happy_path_builds_session_and_returns_url():
    # Mock customer list empty then create
    with patch("stripe.Customer.list", return_value=MagicMock(data=[])):
        with patch("stripe.Customer.create", return_value=MagicMock(id="cus_123")):
            # Mock checkout session
            fake_session = MagicMock(id="cs_test", url="https://stripe.test/session")
            with patch("stripe.checkout.Session.create", return_value=fake_session):
                result = await stripe_service.create_checkout_session(
                    workspace_id="ws_1",
                    plan_tier="starter",
                    customer_email="user@example.com",
                    customer_name="User",
                )
                # create_checkout_session is async; call underlying function via __wrapped__ only if decorated
                # Otherwise, call through event loop
                if hasattr(result, "__await__"):
                    import asyncio
                    result = asyncio.get_event_loop().run_until_complete(result)  # type: ignore
                assert result["url"] == "https://stripe.test/session"
                assert result["plan_tier"] == "starter"


