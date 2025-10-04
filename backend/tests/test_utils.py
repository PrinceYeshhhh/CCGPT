"""
Test utilities for debugging and timeout management
"""

import asyncio
import time
import logging
import signal
from contextlib import contextmanager
from typing import Any, Callable, Optional
import functools

# Set up debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TestTimeoutError(Exception):
    """Raised when a test exceeds its timeout"""
    pass

def timeout(seconds: int = 30):
    """Decorator to add timeout to test functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def timeout_handler(signum, frame):
                raise TestTimeoutError(f"Test {func.__name__} timed out after {seconds} seconds")
            
            # Set up timeout signal
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                logger.debug(f"Starting test: {func.__name__}")
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                logger.debug(f"Completed test: {func.__name__} in {end_time - start_time:.2f}s")
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

def async_timeout(seconds: int = 30):
    """Decorator to add timeout to async test functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger.debug(f"Starting async test: {func.__name__}")
            start_time = time.time()
            
            try:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
                end_time = time.time()
                logger.debug(f"Completed async test: {func.__name__} in {end_time - start_time:.2f}s")
                return result
            except asyncio.TimeoutError:
                raise TestTimeoutError(f"Async test {func.__name__} timed out after {seconds} seconds")
        
        return wrapper
    return decorator

@contextmanager
def debug_logging(test_name: str):
    """Context manager for debug logging during tests"""
    logger.debug(f"=== Starting test: {test_name} ===")
    start_time = time.time()
    
    try:
        yield
    except Exception as e:
        logger.error(f"Test {test_name} failed: {e}")
        raise
    finally:
        end_time = time.time()
        logger.debug(f"=== Completed test: {test_name} in {end_time - start_time:.2f}s ===")

def log_test_progress(step: str, test_name: str = ""):
    """Log test progress for debugging"""
    logger.debug(f"[{test_name}] {step}")

def check_external_services():
    """Check if external services are available"""
    import os
    from app.core.config import settings
    
    services = {
        "Redis": settings.REDIS_URL,
        "Database": settings.DATABASE_URL,
        "ChromaDB": settings.CHROMA_URL,
    }
    
    for service, url in services.items():
        try:
            if "redis" in url.lower():
                import redis
                r = redis.from_url(url)
                r.ping(timeout=1)
            elif "sqlite" in url.lower():
                # SQLite is always available
                pass
            elif "postgres" in url.lower():
                # Skip PostgreSQL check in tests
                pass
            else:
                # Skip other services
                pass
            logger.debug(f"{service} is available")
        except Exception as e:
            logger.warning(f"{service} is not available: {e}")

# Mark slow tests
def slow_test(func):
    """Mark a test as slow"""
    func._slow_test = True
    return func

# Mark integration tests
def integration_test(func):
    """Mark a test as integration test"""
    func._integration_test = True
    return func
