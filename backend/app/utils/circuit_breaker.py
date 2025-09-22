"""
Circuit breaker pattern implementation for fault tolerance
"""

import asyncio
import time
from typing import Callable, Any, Optional
from enum import Enum
import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests are blocked
    - HALF_OPEN: Testing if service is back online
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 3,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.name = name
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} entering HALF_OPEN state")
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker {self.name} is OPEN"
                    )
        
        try:
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - update state
            await self._record_success()
            return result
            
        except Exception as e:
            # Failure - update state
            await self._record_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.timeout
    
    async def _record_success(self):
        """Record successful call"""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} reset to CLOSED state")
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.failure_count = 0
    
    async def _record_failure(self):
        """Record failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")
            elif self.state == CircuitState.HALF_OPEN:
                # Any failure in HALF_OPEN state goes back to OPEN
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning(f"Circuit breaker {self.name} reopened due to failure in HALF_OPEN state")
    
    def get_state(self) -> CircuitState:
        """Get current circuit breaker state"""
        return self.state
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time,
            'is_open': self.state == CircuitState.OPEN
        }
    
    def reset(self):
        """Manually reset circuit breaker"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info(f"Circuit breaker {self.name} manually reset")


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass


class CircuitBreakerManager:
    """Manager for multiple circuit breakers"""
    
    def __init__(self):
        self.breakers = {}
        self._lock = asyncio.Lock()
    
    def get_breaker(
        self, 
        name: str, 
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 3
    ) -> CircuitBreaker:
        """Get or create circuit breaker"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                timeout=timeout,
                success_threshold=success_threshold,
                name=name
            )
        return self.breakers[name]
    
    async def call_with_breaker(
        self, 
        breaker_name: str, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """Call function with circuit breaker"""
        breaker = self.get_breaker(breaker_name)
        return await breaker.call(func, *args, **kwargs)
    
    def get_all_stats(self) -> dict:
        """Get statistics for all circuit breakers"""
        return {
            name: breaker.get_stats() 
            for name, breaker in self.breakers.items()
        }
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()

# Pre-configured circuit breakers
def get_database_breaker() -> CircuitBreaker:
    """Get circuit breaker for database operations"""
    return circuit_breaker_manager.get_breaker(
        "database",
        failure_threshold=3,
        timeout=30,
        success_threshold=2
    )

def get_redis_breaker() -> CircuitBreaker:
    """Get circuit breaker for Redis operations"""
    return circuit_breaker_manager.get_breaker(
        "redis",
        failure_threshold=5,
        timeout=60,
        success_threshold=3
    )

def get_vector_db_breaker() -> CircuitBreaker:
    """Get circuit breaker for vector database operations"""
    return circuit_breaker_manager.get_breaker(
        "vector_db",
        failure_threshold=3,
        timeout=45,
        success_threshold=2
    )

def get_gemini_api_breaker() -> CircuitBreaker:
    """Get circuit breaker for Gemini API operations"""
    return circuit_breaker_manager.get_breaker(
        "gemini_api",
        failure_threshold=5,
        timeout=120,
        success_threshold=3
    )


# Decorator for easy circuit breaker usage
def circuit_breaker(breaker_name: str, **breaker_kwargs):
    """Decorator to add circuit breaker to functions"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            breaker = circuit_breaker_manager.get_breaker(breaker_name, **breaker_kwargs)
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
