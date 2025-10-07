import pytest


@pytest.mark.skip(reason="stub: implement analytics endpoints tests")
def test_analytics_overview_returns_kpis(authenticated_client):
    # Arrange
    # Act: GET /api/v1/analytics/overview
    # Assert: keys present: total_messages, active_sessions, avg_response_time, top_questions
    pass


@pytest.mark.skip(reason="stub: implement analytics error handling tests")
def test_analytics_usage_stats_handles_invalid_days(authenticated_client):
    # Arrange: invalid query param
    # Act: GET /api/v1/analytics/usage-stats?days=0
    # Assert: 422/400 validation error
    pass


