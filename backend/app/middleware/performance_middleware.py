# Performance Monitoring Middleware
# Request-level performance tracking and optimization

import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog
from app.services.performance_service import performance_service
from app.services.cache_service import cache_service, cached
from app.core.config import settings

logger = structlog.get_logger()

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for monitoring request performance"""
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        self.request_count = 0
        self.total_response_time = 0.0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with performance monitoring"""
        start_time = time.time()
        self.request_count += 1
        
        # Skip monitoring for certain paths
        if self._should_skip_monitoring(request):
            return await call_next(request)
        
        # Get request context
        request_id = f"req_{int(start_time * 1000)}_{self.request_count}"
        client_ip = request.client.host if request.client else "unknown"
        
        # Add request ID to request state
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate metrics
            duration = time.time() - start_time
            self.total_response_time += duration
            
            # Record performance metrics
            performance_service.record_request(duration, response.status_code)
            
            # Log slow requests
            if duration > self.slow_request_threshold:
                logger.warning(
                    "Slow request detected",
                    request_id=request_id,
                    path=request.url.path,
                    method=request.method,
                    duration=duration,
                    status_code=response.status_code,
                    client_ip=client_ip
                )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = request_id
            
            # Log request completion
            logger.info(
                "Request completed",
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                duration=duration,
                status_code=response.status_code,
                client_ip=client_ip
            )
            
            return response
            
        except Exception as e:
            # Calculate duration even for failed requests
            duration = time.time() - start_time
            performance_service.record_request(duration, 500)
            
            logger.error(
                "Request failed",
                request_id=request_id,
                path=request.url.path,
                method=request.method,
                duration=duration,
                error=str(e),
                client_ip=client_ip,
                exc_info=True
            )
            
            raise
    
    def _should_skip_monitoring(self, request: Request) -> bool:
        """Check if request should be skipped from monitoring"""
        skip_paths = [
            "/health",
            "/ready",
            "/metrics",
            "/health/detailed",
            "/health/external",
            "/favicon.ico"
        ]
        
        return request.url.path in skip_paths

class CacheOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic cache optimization"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.cacheable_paths = {
            "/api/v1/analytics/overview": 300,  # 5 minutes
            "/api/v1/analytics/usage-stats": 600,  # 10 minutes
            "/api/v1/analytics/kpis": 900,  # 15 minutes
            "/api/v1/documents": 60,  # 1 minute
            "/api/v1/workspace": 300,  # 5 minutes
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with cache optimization"""
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if path is cacheable
        cache_ttl = self.cacheable_paths.get(request.url.path)
        if not cache_ttl:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        try:
            # Try to get from cache
            cached_response = await cache_service.get(cache_key)
            if cached_response:
                # Return cached response
                response = Response(
                    content=cached_response["content"],
                    status_code=cached_response["status_code"],
                    headers=cached_response["headers"],
                    media_type=cached_response["media_type"]
                )
                
                # Add cache headers
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key
                
                logger.debug(
                    "Cache hit",
                    path=request.url.path,
                    cache_key=cache_key
                )
                
                return response
            
            # Process request
            response = await call_next(request)
            
            # Cache successful responses
            if response.status_code == 200:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                # Store in cache
                cache_data = {
                    "content": response_body.decode(),
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "media_type": response.media_type
                }
                
                await cache_service.set(cache_key, cache_data, cache_ttl)
                
                # Recreate response
                response = Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type
                )
                
                # Add cache headers
                response.headers["X-Cache"] = "MISS"
                response.headers["X-Cache-Key"] = cache_key
                response.headers["X-Cache-TTL"] = str(cache_ttl)
            
            return response
            
        except Exception as e:
            logger.error(
                "Cache optimization error",
                path=request.url.path,
                cache_key=cache_key,
                error=str(e)
            )
            
            # Fallback to normal processing
            return await call_next(request)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        # Include path, query parameters, and user context
        key_parts = [request.url.path]
        
        # Add query parameters
        if request.query_params:
            sorted_params = sorted(request.query_params.items())
            key_parts.append("?" + "&".join(f"{k}={v}" for k, v in sorted_params))
        
        # Add user context if available
        if hasattr(request.state, "user_id"):
            key_parts.append(f"user:{request.state.user_id}")
        elif hasattr(request.state, "workspace_id"):
            key_parts.append(f"workspace:{request.state.workspace_id}")
        
        return ":".join(key_parts)

class DatabaseQueryOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware for database query optimization"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.query_count = 0
        self.slow_query_threshold = 0.5  # 500ms
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with database query optimization"""
        # Track database queries for this request
        request.state.db_query_count = 0
        request.state.db_query_time = 0.0
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate database performance
            duration = time.time() - start_time
            query_count = getattr(request.state, "db_query_count", 0)
            query_time = getattr(request.state, "db_query_time", 0.0)
            
            # Log slow database operations
            if query_time > self.slow_query_threshold:
                logger.warning(
                    "Slow database operation",
                    path=request.url.path,
                    method=request.method,
                    query_count=query_count,
                    query_time=query_time,
                    total_time=duration
                )
            
            # Add database performance headers
            response.headers["X-DB-Queries"] = str(query_count)
            response.headers["X-DB-Time"] = f"{query_time:.3f}s"
            
            return response
            
        except Exception as e:
            logger.error(
                "Database optimization error",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            raise

class MemoryOptimizationMiddleware(BaseHTTPMiddleware):
    """Middleware for memory usage optimization"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.memory_threshold = 0.8  # 80% memory usage
        self.last_gc_time = 0
        self.gc_interval = 300  # 5 minutes
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with memory optimization"""
        import gc
        import psutil
        
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent / 100.0
        
        # Force garbage collection if memory usage is high
        if memory_percent > self.memory_threshold:
            current_time = time.time()
            if current_time - self.last_gc_time > self.gc_interval:
                logger.warning(
                    "High memory usage detected, forcing garbage collection",
                    memory_percent=memory_percent
                )
                
                # Force garbage collection
                collected = gc.collect()
                self.last_gc_time = current_time
                
                logger.info(
                    "Garbage collection completed",
                    collected_objects=collected,
                    memory_percent=psutil.virtual_memory().percent
                )
        
        try:
            response = await call_next(request)
            
            # Add memory usage headers
            response.headers["X-Memory-Usage"] = f"{memory_percent:.1%}"
            
            return response
            
        except Exception as e:
            logger.error(
                "Memory optimization error",
                path=request.url.path,
                method=request.method,
                error=str(e)
            )
            raise

# Performance decorators for endpoints
def optimize_performance(cache_ttl: int = 300, cache_key_func: Callable = None):
    """Decorator for optimizing endpoint performance"""
    def decorator(func):
        @cached(ttl=cache_ttl, key_func=cache_key_func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def monitor_database_queries(func):
    """Decorator for monitoring database query performance"""
    async def wrapper(*args, **kwargs):
        # This would be implemented with database query monitoring
        # For now, we'll just call the function
        return await func(*args, **kwargs)
    return wrapper
