import pytest


@pytest.mark.skip(reason="stub: implement websocket auth and connection limit tests")
def test_websocket_rejects_invalid_token():
    # Arrange: invalid token query
    # Act: connect to /api/websocket/chat/{session_id}
    # Assert: connection closed with 4401 code
    pass


@pytest.mark.skip(reason="stub: implement connection rate limiting tests")
def test_websocket_connection_limits_per_user():
    # Arrange: exceed allowed concurrent connections
    # Act: open N connections
    # Assert: subsequent connection closed with 4403
    pass


