import pytest


@pytest.mark.skip(reason="stub: implement CSRF middleware tests for non-Bearer POSTs")
def test_post_without_csrf_header_is_forbidden(client):
    # Arrange: pick a non-exempt POST endpoint
    # Act: send POST without X-CSRF-Token and without Bearer auth
    # Assert: 403 with {detail: 'CSRF token required'}
    pass


@pytest.mark.skip(reason="stub: implement CSRF header acceptance")
def test_post_with_valid_csrf_header_is_allowed(client):
    # Arrange: set X-CSRF-Token header
    # Act: POST
    # Assert: not 403
    pass


