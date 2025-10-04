"""
Configuration for skipping problematic tests that cause hangs
"""

import pytest
import os

# Environment variable to control test skipping
SKIP_PROBLEMATIC_TESTS = os.getenv('SKIP_PROBLEMATIC_TESTS', 'false').lower() == 'true'

def skip_if_problematic(reason: str = "Test is known to cause hangs"):
    """Skip test if SKIP_PROBLEMATIC_TESTS is enabled"""
    return pytest.mark.skipif(
        SKIP_PROBLEMATIC_TESTS,
        reason=reason
    )

def skip_if_slow(reason: str = "Test is too slow for CI"):
    """Skip test if it's too slow for CI"""
    return pytest.mark.skipif(
        os.getenv('CI') == 'true',
        reason=reason
    )

def skip_if_external_services_unavailable(reason: str = "External services not available"):
    """Skip test if external services are not available"""
    return pytest.mark.skipif(
        os.getenv('SKIP_EXTERNAL_TESTS', 'false').lower() == 'true',
        reason=reason
    )

# Example usage in test files:
# @skip_if_problematic("This test hangs on Redis connection")
# def test_redis_connection():
#     pass

# @skip_if_slow("This test takes too long for CI")
# def test_large_data_processing():
#     pass

# @skip_if_external_services_unavailable("ChromaDB not available in test environment")
# def test_chromadb_integration():
#     pass
