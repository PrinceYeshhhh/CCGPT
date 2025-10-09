"""
Unit tests for Utility Services
Tests all utility classes and helper functions
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import tempfile
import os

from app.utils.cache import CacheManager, VectorSearchCache, AnalyticsCache, EmbedCodeCache
from app.utils.storage import StorageAdapter, LocalStorageAdapter, S3StorageAdapter, GCSStorageAdapter
from app.utils.health import HealthChecker
from app.utils.file_validation import FileValidator
from app.utils.plan_limits import PlanTier, PlanLimits
from app.utils.metrics import MetricsCollector
from app.utils.security_monitor import SecurityMonitor
from app.utils.validators import DashboardQueryValidator, AnalyticsFilterValidator, PerformanceMetricsValidator
from app.utils.circuit_breaker import CircuitState, CircuitBreaker, CircuitBreakerOpenException, CircuitBreakerManager
from app.utils.logger import RequestLogger
from app.utils.production_validator import ProductionValidator
from app.utils.error_monitoring import ErrorMonitor

class TestCacheManager:
    """Unit tests for CacheManager"""
    
    @pytest.fixture
    def cache_manager(self):
        return CacheManager()
    
    def test_initialization(self, cache_manager):
        """Test cache manager initialization"""
        assert cache_manager is not None
        assert hasattr(cache_manager, 'redis_client')
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_manager):
        """Test cache set and get operations"""
        key = "test_key"
        value = {"data": "test_value"}
        ttl = 3600
        
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.set.return_value = True
            mock_redis.get.return_value = '{"data": "test_value"}'
            
            # Test set
            result = await cache_manager.set(key, value, ttl)
            assert result is True
            mock_redis.set.assert_called_once()
            
            # Test get
            cached_value = await cache_manager.get(key)
            assert cached_value == value
            mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_manager):
        """Test cache delete operation"""
        key = "test_key"
        
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.delete.return_value = True
            
            result = await cache_manager.delete(key)
            assert result is True
            mock_redis.delete.assert_called_once_with(key)
    
    @pytest.mark.asyncio
    async def test_exists(self, cache_manager):
        """Test cache exists check"""
        key = "test_key"
        
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.exists.return_value = True
            
            exists = await cache_manager.exists(key)
            assert exists is True
            mock_redis.exists.assert_called_once_with(key)
    
    @pytest.mark.asyncio
    async def test_clear(self, cache_manager):
        """Test cache clear operation"""
        with patch.object(cache_manager, 'redis_client') as mock_redis:
            mock_redis.flushdb.return_value = True
            
            result = await cache_manager.clear()
            assert result is True
            mock_redis.flushdb.assert_called_once()

class TestVectorSearchCache:
    """Unit tests for VectorSearchCache"""
    
    @pytest.fixture
    def vector_cache(self):
        return VectorSearchCache()
    
    def test_initialization(self, vector_cache):
        """Test vector cache initialization"""
        assert vector_cache is not None
        assert hasattr(vector_cache, 'cache_manager')
    
    @pytest.mark.asyncio
    async def test_cache_search_results(self, vector_cache):
        """Test caching search results"""
        workspace_id = "ws_123"
        query = "test query"
        results = [{"content": "result 1", "score": 0.9}]
        
        with patch.object(vector_cache, 'cache_manager') as mock_cache:
            mock_cache.set.return_value = True
            
            result = await vector_cache.cache_search_results(workspace_id, query, results)
            assert result is True
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cached_results(self, vector_cache):
        """Test getting cached search results"""
        workspace_id = "ws_123"
        query = "test query"
        cached_results = [{"content": "result 1", "score": 0.9}]
        
        with patch.object(vector_cache, 'cache_manager') as mock_cache:
            mock_cache.get.return_value = cached_results
            
            results = await vector_cache.get_cached_results(workspace_id, query)
            assert results == cached_results
            mock_cache.get.assert_called_once()
    
    def test_generate_cache_key(self, vector_cache):
        """Test cache key generation"""
        workspace_id = "ws_123"
        query = "test query"
        
        key = vector_cache.generate_cache_key(workspace_id, query)
        
        assert isinstance(key, str)
        assert workspace_id in key
        assert "query" in key.lower()

class TestStorageAdapter:
    """Unit tests for StorageAdapter"""
    
    def test_abstract_methods(self):
        """Test that StorageAdapter is abstract"""
        with pytest.raises(TypeError):
            StorageAdapter()

class TestLocalStorageAdapter:
    """Unit tests for LocalStorageAdapter"""
    
    @pytest.fixture
    def local_storage(self):
        return LocalStorageAdapter("/tmp/test_storage")
    
    def test_initialization(self, local_storage):
        """Test local storage initialization"""
        assert local_storage is not None
        assert hasattr(local_storage, 'base_path')
    
    @pytest.mark.asyncio
    async def test_upload_file(self, local_storage):
        """Test file upload"""
        file_path = "test_file.txt"
        content = b"test content"
        
        with patch('aiofiles.open', create=True) as mock_open:
            mock_file = AsyncMock()
            mock_file.write = AsyncMock()
            mock_file.__aenter__ = AsyncMock(return_value=mock_file)
            mock_file.__aexit__ = AsyncMock(return_value=None)
            mock_open.return_value = mock_file
            
            result = await local_storage.upload_file(file_path, content)
            assert result is True
            mock_open.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_file(self, local_storage):
        """Test file download"""
        file_path = "test_file.txt"
        expected_content = b"test content"
        
        with patch('aiofiles.open', create=True) as mock_open:
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=expected_content)
            mock_file.__aenter__ = AsyncMock(return_value=mock_file)
            mock_file.__aexit__ = AsyncMock(return_value=None)
            mock_open.return_value = mock_file
            
            content = await local_storage.download_file(file_path)
            assert content == expected_content
            mock_open.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file(self, local_storage):
        """Test file deletion"""
        file_path = "test_file.txt"
        
        with patch('aiofiles.os.remove') as mock_remove:
            mock_remove.return_value = None
            
            result = await local_storage.delete_file(file_path)
            assert result is True
            mock_remove.assert_called_once()

class TestS3StorageAdapter:
    """Unit tests for S3StorageAdapter"""
    
    @pytest.fixture
    def s3_storage(self):
        return S3StorageAdapter("test-bucket", "us-east-1")
    
    def test_initialization(self, s3_storage):
        """Test S3 storage initialization"""
        assert s3_storage is not None
        assert hasattr(s3_storage, 'bucket_name')
        assert hasattr(s3_storage, 'region')
    
    @pytest.mark.asyncio
    async def test_upload_file(self, s3_storage):
        """Test S3 file upload"""
        file_path = "test_file.txt"
        content = b"test content"
        
        with patch.object(s3_storage, 's3_client') as mock_s3:
            mock_s3.put_object.return_value = {"ETag": "test-etag"}
            
            result = await s3_storage.upload_file(file_path, content)
            assert result is True
            mock_s3.put_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_file(self, s3_storage):
        """Test S3 file download"""
        file_path = "test_file.txt"
        expected_content = b"test content"
        
        with patch.object(s3_storage, 's3_client') as mock_s3:
            mock_response = {"Body": {"read": AsyncMock(return_value=expected_content)}}
            mock_s3.get_object.return_value = mock_response
            
            content = await s3_storage.download_file(file_path)
            assert content == expected_content
            mock_s3.get_object.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file(self, s3_storage):
        """Test S3 file deletion"""
        file_path = "test_file.txt"
        
        with patch.object(s3_storage, 's3_client') as mock_s3:
            mock_s3.delete_object.return_value = {}
            
            result = await s3_storage.delete_file(file_path)
            assert result is True
            mock_s3.delete_object.assert_called_once()

class TestHealthChecker:
    """Unit tests for HealthChecker"""
    
    @pytest.fixture
    def health_checker(self):
        return HealthChecker()
    
    def test_initialization(self, health_checker):
        """Test health checker initialization"""
        assert health_checker is not None
        assert hasattr(health_checker, 'checks')
    
    @pytest.mark.asyncio
    async def test_check_database_health(self, health_checker):
        """Test database health check"""
        with patch.object(health_checker, 'db') as mock_db:
            mock_db.execute.return_value = True
            
            result = await health_checker.check_database_health()
            assert result is True
            mock_db.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_redis_health(self, health_checker):
        """Test Redis health check"""
        with patch.object(health_checker, 'redis_client') as mock_redis:
            mock_redis.ping.return_value = True
            
            result = await health_checker.check_redis_health()
            assert result is True
            mock_redis.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_external_apis(self, health_checker):
        """Test external API health check"""
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_httpx.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await health_checker.check_external_apis()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_run_all_checks(self, health_checker):
        """Test running all health checks"""
        with patch.object(health_checker, 'check_database_health', return_value=True):
            with patch.object(health_checker, 'check_redis_health', return_value=True):
                with patch.object(health_checker, 'check_external_apis', return_value=True):
                    
                    result = await health_checker.run_all_checks()
                    
                    assert isinstance(result, dict)
                    assert "database" in result
                    assert "redis" in result
                    assert "external_apis" in result
                    assert all(result.values())

class TestFileValidator:
    """Unit tests for FileValidator"""
    
    @pytest.fixture
    def file_validator(self):
        return FileValidator()
    
    def test_initialization(self, file_validator):
        """Test file validator initialization"""
        assert file_validator is not None
        assert hasattr(file_validator, 'allowed_types')
        assert hasattr(file_validator, 'max_size')
    
    def test_validate_file_type(self, file_validator):
        """Test file type validation"""
        # Test valid types
        assert file_validator.validate_file_type("application/pdf") is True
        assert file_validator.validate_file_type("text/plain") is True
        
        # Test invalid types
        assert file_validator.validate_file_type("application/octet-stream") is False
        assert file_validator.validate_file_type("image/jpeg") is False
    
    def test_validate_file_size(self, file_validator):
        """Test file size validation"""
        # Test valid sizes
        assert file_validator.validate_file_size(1024 * 1024) is True  # 1MB
        assert file_validator.validate_file_size(10 * 1024 * 1024) is True  # 10MB
        
        # Test invalid sizes
        assert file_validator.validate_file_size(100 * 1024 * 1024) is False  # 100MB
        assert file_validator.validate_file_size(0) is False  # Empty file
    
    def test_validate_file_extension(self, file_validator):
        """Test file extension validation"""
        # Test valid extensions
        assert file_validator.validate_file_extension("test.pdf") is True
        assert file_validator.validate_file_extension("test.txt") is True
        assert file_validator.validate_file_extension("test.docx") is True
        
        # Test invalid extensions
        assert file_validator.validate_file_extension("test.exe") is False
        assert file_validator.validate_file_extension("test.bat") is False
    
    def test_scan_for_malware(self, file_validator):
        """Test malware scanning"""
        # Test clean content
        clean_content = b"This is clean content"
        is_clean = file_validator.scan_for_malware(clean_content)
        assert is_clean is True
        
        # Test suspicious content
        suspicious_content = b"eval(base64_decode('malicious'))"
        is_clean = file_validator.scan_for_malware(suspicious_content)
        assert is_clean is False

class TestPlanLimits:
    """Unit tests for PlanLimits"""
    
    def test_plan_tier_enum(self):
        """Test PlanTier enum values"""
        assert PlanTier.FREE.value == "free"
        assert PlanTier.PRO.value == "pro"
        assert PlanTier.ENTERPRISE.value == "enterprise"
    
    def test_plan_limits_initialization(self):
        """Test PlanLimits initialization"""
        limits = PlanLimits()
        assert limits is not None
        assert hasattr(limits, 'get_limits')
    
    def test_get_limits_free_tier(self):
        """Test getting limits for free tier"""
        limits = PlanLimits()
        free_limits = limits.get_limits(PlanTier.FREE)
        
        assert isinstance(free_limits, dict)
        assert "max_documents" in free_limits
        assert "max_queries_per_month" in free_limits
        assert "max_file_size" in free_limits
        assert free_limits["max_documents"] < 100  # Free tier should have low limits
    
    def test_get_limits_pro_tier(self):
        """Test getting limits for pro tier"""
        limits = PlanLimits()
        pro_limits = limits.get_limits(PlanTier.PRO)
        
        assert isinstance(pro_limits, dict)
        assert pro_limits["max_documents"] > 100  # Pro tier should have higher limits
        assert pro_limits["max_queries_per_month"] > 1000
    
    def test_get_limits_enterprise_tier(self):
        """Test getting limits for enterprise tier"""
        limits = PlanLimits()
        enterprise_limits = limits.get_limits(PlanTier.ENTERPRISE)
        
        assert isinstance(enterprise_limits, dict)
        assert enterprise_limits["max_documents"] > 1000  # Enterprise should have highest limits
        assert enterprise_limits["max_queries_per_month"] > 10000

class TestMetricsCollector:
    """Unit tests for MetricsCollector"""
    
    @pytest.fixture
    def metrics_collector(self):
        return MetricsCollector()
    
    def test_initialization(self, metrics_collector):
        """Test metrics collector initialization"""
        assert metrics_collector is not None
        assert hasattr(metrics_collector, 'metrics')
    
    def test_increment_counter(self, metrics_collector):
        """Test counter increment"""
        counter_name = "test_counter"
        
        metrics_collector.increment_counter(counter_name)
        
        assert counter_name in metrics_collector.metrics
        assert metrics_collector.metrics[counter_name] == 1
        
        # Increment again
        metrics_collector.increment_counter(counter_name)
        assert metrics_collector.metrics[counter_name] == 2
    
    def test_record_histogram(self, metrics_collector):
        """Test histogram recording"""
        histogram_name = "test_histogram"
        value = 100.5
        
        metrics_collector.record_histogram(histogram_name, value)
        
        assert histogram_name in metrics_collector.metrics
        assert value in metrics_collector.metrics[histogram_name]
    
    def test_record_gauge(self, metrics_collector):
        """Test gauge recording"""
        gauge_name = "test_gauge"
        value = 42
        
        metrics_collector.record_gauge(gauge_name, value)
        
        assert gauge_name in metrics_collector.metrics
        assert metrics_collector.metrics[gauge_name] == value
    
    def test_get_metrics(self, metrics_collector):
        """Test getting all metrics"""
        metrics_collector.increment_counter("test_counter")
        metrics_collector.record_gauge("test_gauge", 42)
        
        all_metrics = metrics_collector.get_metrics()
        
        assert isinstance(all_metrics, dict)
        assert "test_counter" in all_metrics
        assert "test_gauge" in all_metrics

class TestSecurityMonitor:
    """Unit tests for SecurityMonitor"""
    
    @pytest.fixture
    def security_monitor(self):
        return SecurityMonitor()
    
    def test_initialization(self, security_monitor):
        """Test security monitor initialization"""
        assert security_monitor is not None
        assert hasattr(security_monitor, 'alerts')
    
    def test_detect_anomaly(self, security_monitor):
        """Test anomaly detection"""
        # Test normal behavior
        is_anomaly = security_monitor.detect_anomaly("normal_request", "user_123")
        assert is_anomaly is False
        
        # Test suspicious behavior
        is_anomaly = security_monitor.detect_anomaly("'; DROP TABLE users; --", "user_123")
        assert is_anomaly is True
    
    def test_log_security_event(self, security_monitor):
        """Test security event logging"""
        event_type = "suspicious_login"
        user_id = "user_123"
        details = {"ip": "192.168.1.1", "user_agent": "suspicious"}
        
        security_monitor.log_security_event(event_type, user_id, details)
        
        assert len(security_monitor.alerts) == 1
        assert security_monitor.alerts[0]["type"] == event_type
        assert security_monitor.alerts[0]["user_id"] == user_id
    
    def test_get_security_alerts(self, security_monitor):
        """Test getting security alerts"""
        security_monitor.log_security_event("test_event", "user_123", {})
        
        alerts = security_monitor.get_security_alerts()
        
        assert isinstance(alerts, list)
        assert len(alerts) == 1
        assert alerts[0]["type"] == "test_event"

class TestCircuitBreaker:
    """Unit tests for CircuitBreaker"""
    
    def test_initialization(self):
        """Test circuit breaker initialization"""
        cb = CircuitBreaker(failure_threshold=5, timeout=60)
        
        assert cb.failure_threshold == 5
        assert cb.timeout == 60
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_successful_call(self):
        """Test successful circuit breaker call"""
        cb = CircuitBreaker(failure_threshold=5, timeout=60)
        
        @cb
        def test_function():
            return "success"
        
        result = test_function()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
    
    def test_failure_counting(self):
        """Test failure counting"""
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        
        @cb
        def failing_function():
            raise Exception("Test failure")
        
        # First few failures should not open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                failing_function()
        
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 2
        
        # Third failure should open circuit
        with pytest.raises(Exception):
            failing_function()
        
        assert cb.state == CircuitState.OPEN
        assert cb.failure_count == 3
    
    def test_circuit_breaker_open_exception(self):
        """Test circuit breaker open exception"""
        cb = CircuitBreaker(failure_threshold=1, timeout=60)
        
        @cb
        def failing_function():
            raise Exception("Test failure")
        
        # First failure opens circuit
        with pytest.raises(Exception):
            failing_function()
        
        # Subsequent calls should raise CircuitBreakerOpenException
        with pytest.raises(CircuitBreakerOpenException):
            failing_function()
    
    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset after timeout"""
        cb = CircuitBreaker(failure_threshold=1, timeout=0.1)  # Very short timeout
        
        @cb
        def failing_function():
            raise Exception("Test failure")
        
        # Open the circuit
        with pytest.raises(Exception):
            failing_function()
        
        assert cb.state == CircuitState.OPEN
        
        # Wait for timeout and test reset
        import time
        time.sleep(0.2)
        
        # Should be reset to half-open
        assert cb.state == CircuitState.HALF_OPEN

class TestRequestLogger:
    """Unit tests for RequestLogger"""
    
    @pytest.fixture
    def request_logger(self):
        return RequestLogger()
    
    def test_initialization(self, request_logger):
        """Test request logger initialization"""
        assert request_logger is not None
        assert hasattr(request_logger, 'logger')
    
    def test_log_request(self, request_logger):
        """Test request logging"""
        with patch.object(request_logger, 'logger') as mock_logger:
            request_logger.log_request("GET", "/api/test", "user_123", 200, 150)
            
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0]
            assert "GET" in call_args
            assert "/api/test" in call_args
            assert "user_123" in call_args
            assert "200" in call_args
            assert "150" in call_args
    
    def test_log_error(self, request_logger):
        """Test error logging"""
        with patch.object(request_logger, 'logger') as mock_logger:
            request_logger.log_error("Test error", "user_123", {"details": "error details"})
            
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0][0]
            assert "Test error" in call_args
            assert "user_123" in call_args

class TestProductionValidator:
    """Unit tests for ProductionValidator"""
    
    @pytest.fixture
    def production_validator(self):
        return ProductionValidator()
    
    def test_initialization(self, production_validator):
        """Test production validator initialization"""
        assert production_validator is not None
        assert hasattr(production_validator, 'checks')
    
    def test_validate_environment(self, production_validator):
        """Test environment validation"""
        with patch.dict('os.environ', {
            'DATABASE_URL': 'postgresql://test',
            'REDIS_URL': 'redis://test',
            'SECRET_KEY': 'test_secret',
            'GEMINI_API_KEY': 'test_key'
        }):
            result = production_validator.validate_environment()
            assert result is True
    
    def test_validate_environment_missing_vars(self, production_validator):
        """Test environment validation with missing variables"""
        with patch.dict('os.environ', {}, clear=True):
            result = production_validator.validate_environment()
            assert result is False
    
    def test_validate_database_connection(self, production_validator):
        """Test database connection validation"""
        with patch.object(production_validator, 'db') as mock_db:
            mock_db.execute.return_value = True
            
            result = production_validator.validate_database_connection()
            assert result is True
            mock_db.execute.assert_called_once()
    
    def test_validate_redis_connection(self, production_validator):
        """Test Redis connection validation"""
        with patch.object(production_validator, 'redis_client') as mock_redis:
            mock_redis.ping.return_value = True
            
            result = production_validator.validate_redis_connection()
            assert result is True
            mock_redis.ping.assert_called_once()
    
    def test_run_all_checks(self, production_validator):
        """Test running all production checks"""
        with patch.object(production_validator, 'validate_environment', return_value=True):
            with patch.object(production_validator, 'validate_database_connection', return_value=True):
                with patch.object(production_validator, 'validate_redis_connection', return_value=True):
                    
                    result = production_validator.run_all_checks()
                    
                    assert isinstance(result, dict)
                    assert "environment" in result
                    assert "database" in result
                    assert "redis" in result
                    assert all(result.values())

class TestErrorMonitor:
    """Unit tests for ErrorMonitor"""
    
    @pytest.fixture
    def error_monitor(self):
        return ErrorMonitor()
    
    def test_initialization(self, error_monitor):
        """Test error monitor initialization"""
        assert error_monitor is not None
        assert hasattr(error_monitor, 'errors')
    
    def test_capture_exception(self, error_monitor):
        """Test exception capture"""
        try:
            raise ValueError("Test error")
        except Exception as e:
            error_monitor.capture_exception(e, {"user_id": "user_123"})
        
        assert len(error_monitor.errors) == 1
        assert error_monitor.errors[0]["type"] == "ValueError"
        assert error_monitor.errors[0]["message"] == "Test error"
    
    def test_get_error_summary(self, error_monitor):
        """Test getting error summary"""
        # Capture some errors
        try:
            raise ValueError("Error 1")
        except Exception as e:
            error_monitor.capture_exception(e)
        
        try:
            raise RuntimeError("Error 2")
        except Exception as e:
            error_monitor.capture_exception(e)
        
        summary = error_monitor.get_error_summary()
        
        assert isinstance(summary, dict)
        assert "total_errors" in summary
        assert "error_types" in summary
        assert summary["total_errors"] == 2
        assert "ValueError" in summary["error_types"]
        assert "RuntimeError" in summary["error_types"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

