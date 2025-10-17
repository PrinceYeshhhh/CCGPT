"""
Example test file showing how to use timeouts and debugging
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock
from tests.test_utils import timeout, async_timeout, debug_logging, log_test_progress

class TestExampleWithTimeouts:
    """Example tests with proper timeout handling"""
    
    # Example test; avoid custom timeouts in unit scope
    def test_simple_function_with_timeout(self):
        """Test a simple function with timeout"""
        with debug_logging("test_simple_function_with_timeout"):
            log_test_progress("Starting simple test")
            
            # Your test logic here
            result = 2 + 2
            assert result == 4
            
            log_test_progress("Test completed successfully")
    
    # Avoid custom async timeout in unit scope
    @pytest.mark.asyncio
    async def test_async_function_with_timeout(self):
        """Test an async function with timeout"""
        with debug_logging("test_async_function_with_timeout"):
            log_test_progress("Starting async test")
            
            # Simulate async work
            await asyncio.sleep(0.1)
            
            result = 3 * 3
            assert result == 9
            
            log_test_progress("Async test completed successfully")
    
    # Avoid custom timeouts and favor fast deterministic mocks
    def test_with_external_service_mock(self):
        """Test that mocks external services to prevent hanging"""
        with debug_logging("test_with_external_service_mock"):
            log_test_progress("Starting external service test")
            
            # Mock external service calls
            with patch('app.core.database.redis_manager') as mock_redis:
                mock_redis.get_client.return_value.ping.return_value = True
                
                # Your test logic that might call external services
                from app.core.database import redis_manager
                client = redis_manager.get_client()
                assert client.ping() is True
                
            log_test_progress("External service test completed")
    
    @pytest.mark.skip(reason="Out of scope for essential backend unit tests")
    def test_problematic_test(self):
        """Example of a test that should be skipped"""
        # This test would hang or fail
        pass
    
    # Keep this quick test without external timeout decorators
    def test_quick_operation(self):
        """Test that should complete quickly"""
        with debug_logging("test_quick_operation"):
            log_test_progress("Starting quick test")
            
            # Quick operation
            data = {"key": "value"}
            assert data["key"] == "value"
            
            log_test_progress("Quick test completed")
    
    def test_with_manual_timeout_handling(self):
        """Test showing manual timeout handling"""
        with debug_logging("test_with_manual_timeout_handling"):
            log_test_progress("Starting manual timeout test")
            
            start_time = time.time()
            timeout_seconds = 5
            
            try:
                # Simulate some work
                time.sleep(0.1)
                
                elapsed = time.time() - start_time
                assert elapsed < timeout_seconds
                
                log_test_progress("Manual timeout test completed")
            except Exception as e:
                log_test_progress(f"Manual timeout test failed: {e}")
                raise
