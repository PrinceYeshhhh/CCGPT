import pytest


@pytest.mark.skip(reason="stub: implement rate limiting and token budget tests for rag_query")
def test_rag_query_rate_limited(authenticated_client):
    # Arrange: exceed 60 req/min window
    # Act: POST /api/v1/rag/query repeatedly
    # Assert: 429 with X-RateLimit headers
    pass


@pytest.mark.skip(reason="stub: implement token budget enforcement tests")
def test_rag_query_token_budget_exceeded(authenticated_client):
    # Arrange: simulate token usage reaching daily limit
    # Act: POST /api/v1/rag/query
    # Assert: 429 with budget headers
    pass


