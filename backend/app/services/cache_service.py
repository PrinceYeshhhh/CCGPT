# Advanced Caching Service for CustomerCareGPT
# Multi-tier caching with intelligent invalidation and performance optimization

import json
import hashlib
import time
import asyncio
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from functools import wraps
from datetime import datetime, timedelta
import structlog
from app.core.database import redis_manager
from app.core.config import settings

logger = structlog.get_logger()

class CacheKey:
    """Cache key builder with namespace support"""
    
    @staticmethod
    def build(namespace: str, *parts: str, **kwargs) -> str:
        """Build a cache key with namespace and parts"""
        key_parts = [namespace] + list(parts)
        
        # Add sorted kwargs for consistent key generation
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        
        return ":".join(str(part) for part in key_parts)
    
    @staticmethod
    def hash_data(data: Any) -> str:
        """Generate hash for complex data structures"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()[:16]

class CacheStats:
    """Cache statistics tracking"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.total_requests = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary"""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate
        }

class CacheService:
    """Advanced caching service with multiple strategies"""
    
    def __init__(self):
        self.redis = redis_manager.get_client()
        self.stats = CacheStats()
        self.local_cache = {}  # L1 cache
        self.local_cache_ttl = {}  # TTL for local cache
        self.max_local_cache_size = 1000
        self.local_cache_cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()
    
    def _cleanup_local_cache(self):
        """Clean up expired local cache entries"""
        current_time = time.time()
        
        # Only cleanup if enough time has passed
        if current_time - self._last_cleanup < self.local_cache_cleanup_interval:
            return
        
        expired_keys = []
        for key, ttl in self.local_cache_ttl.items():
            if current_time > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.local_cache.pop(key, None)
            self.local_cache_ttl.pop(key, None)
        
        # Limit cache size
        if len(self.local_cache) > self.max_local_cache_size:
            # Remove oldest entries (simple FIFO)
            excess = len(self.local_cache) - self.max_local_cache_size
            keys_to_remove = list(self.local_cache.keys())[:excess]
            for key in keys_to_remove:
                self.local_cache.pop(key, None)
                self.local_cache_ttl.pop(key, None)
        
        self._last_cleanup = current_time
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (L1 -> L2)"""
        self.stats.total_requests += 1
        
        try:
            # Check L1 cache first
            current_time = time.time()
            if key in self.local_cache:
                ttl = self.local_cache_ttl.get(key, 0)
                if current_time < ttl:
                    self.stats.hits += 1
                    return self.local_cache[key]
                else:
                    # Expired, remove from L1
                    self.local_cache.pop(key, None)
                    self.local_cache_ttl.pop(key, None)
            
            # Check L2 cache (Redis)
            if self.redis.redis_available:
                cached_value = self.redis.get(key)
                if cached_value is not None:
                    try:
                        value = json.loads(cached_value)
                        # Store in L1 cache
                        self.local_cache[key] = value
                        self.local_cache_ttl[key] = current_time + 60  # 1 minute TTL for L1
                        self.stats.hits += 1
                        return value
                    except (json.JSONDecodeError, TypeError):
                        # Invalid cached data, remove it
                        self.redis.delete(key)
            
            self.stats.misses += 1
            return default
            
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            self.stats.errors += 1
            return default
        finally:
            self._cleanup_local_cache()
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """Set value in cache (L1 + L2)"""
        try:
            # Set in L1 cache
            current_time = time.time()
            self.local_cache[key] = value
            self.local_cache_ttl[key] = current_time + (ttl or 300)  # Default 5 minutes for L1
            
            # Set in L2 cache (Redis)
            if self.redis.redis_available:
                serialized_value = json.dumps(value, default=str)
                if ttl:
                    self.redis.setex(key, ttl, serialized_value)
                else:
                    self.redis.set(key, serialized_value)
            
            self.stats.sets += 1
            return True
            
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            self.stats.errors += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache (L1 + L2)"""
        try:
            # Remove from L1 cache
            self.local_cache.pop(key, None)
            self.local_cache_ttl.pop(key, None)
            
            # Remove from L2 cache
            if self.redis.redis_available:
                self.redis.delete(key)
            
            self.stats.deletes += 1
            return True
            
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            self.stats.errors += 1
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        try:
            deleted_count = 0
            
            # Delete from L1 cache
            keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
            for key in keys_to_delete:
                self.local_cache.pop(key, None)
                self.local_cache_ttl.pop(key, None)
                deleted_count += 1
            
            # Delete from L2 cache
            if self.redis.redis_available:
                keys = self.redis.keys(pattern)
                if keys:
                    deleted_count += self.redis.delete(*keys)
            
            return deleted_count
            
        except Exception as e:
            logger.error("Cache delete pattern error", pattern=pattern, error=str(e))
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            # Check L1 cache
            current_time = time.time()
            if key in self.local_cache:
                ttl = self.local_cache_ttl.get(key, 0)
                if current_time < ttl:
                    return True
                else:
                    # Expired, remove
                    self.local_cache.pop(key, None)
                    self.local_cache_ttl.pop(key, None)
            
            # Check L2 cache
            if self.redis.redis_available:
                return bool(self.redis.exists(key))
            
            return False
            
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
    
    async def get_or_set(
        self, 
        key: str, 
        factory: Callable, 
        ttl: Optional[int] = None,
        *args, 
        **kwargs
    ) -> Any:
        """Get value from cache or set using factory function"""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Generate value using factory
        if asyncio.iscoroutinefunction(factory):
            value = await factory(*args, **kwargs)
        else:
            value = factory(*args, **kwargs)
        
        # Cache the value
        await self.set(key, value, ttl)
        return value
    
    async def invalidate_namespace(self, namespace: str) -> int:
        """Invalidate all keys in a namespace"""
        pattern = f"{namespace}:*"
        return await self.delete_pattern(pattern)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.stats.to_dict()
    
    async def clear(self) -> bool:
        """Clear all cache data"""
        try:
            # Clear L1 cache
            self.local_cache.clear()
            self.local_cache_ttl.clear()
            
            # Clear L2 cache
            if self.redis.redis_available:
                self.redis.flushdb()
            
            return True
            
        except Exception as e:
            logger.error("Cache clear error", error=str(e))
            return False

# Global cache service instance
cache_service = CacheService()

# Cache decorators
def cached(
    ttl: int = 300,
    namespace: str = "default",
    key_func: Optional[Callable] = None
):
    """Cache decorator for functions"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                key_hash = CacheKey.hash_data(key_data)
                cache_key = CacheKey.build(namespace, func.__name__, key_hash)
            
            # Try to get from cache
            result = await cache_service.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await cache_service.set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_data = {
                    "func": func.__name__,
                    "args": args,
                    "kwargs": kwargs
                }
                key_hash = CacheKey.hash_data(key_data)
                cache_key = CacheKey.build(namespace, func.__name__, key_hash)
            
            # Try to get from cache (sync)
            import asyncio
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(cache_service.get(cache_key))
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            loop.run_until_complete(cache_service.set(cache_key, result, ttl))
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def cache_invalidate(namespace: str, key_pattern: Optional[str] = None):
    """Cache invalidation decorator"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidate cache
            if key_pattern:
                await cache_service.delete_pattern(key_pattern)
            else:
                await cache_service.invalidate_namespace(namespace)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache (sync)
            import asyncio
            loop = asyncio.get_event_loop()
            if key_pattern:
                loop.run_until_complete(cache_service.delete_pattern(key_pattern))
            else:
                loop.run_until_complete(cache_service.invalidate_namespace(namespace))
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Specialized cache functions
class QueryCache:
    """Database query caching"""
    
    @staticmethod
    async def cache_query(
        query_key: str,
        query_func: Callable,
        ttl: int = 300,
        workspace_id: Optional[str] = None
    ) -> Any:
        """Cache database query results"""
        cache_key = CacheKey.build(
            "query",
            query_key,
            workspace_id=workspace_id
        )
        
        return await cache_service.get_or_set(
            cache_key,
            query_func,
            ttl
        )
    
    @staticmethod
    async def invalidate_workspace(workspace_id: str):
        """Invalidate all queries for a workspace"""
        pattern = f"query:*:workspace_id:{workspace_id}"
        await cache_service.delete_pattern(pattern)

class APICache:
    """API response caching"""
    
    @staticmethod
    async def cache_response(
        endpoint: str,
        params: Dict[str, Any],
        response_func: Callable,
        ttl: int = 600,
        workspace_id: Optional[str] = None
    ) -> Any:
        """Cache API response"""
        # Generate cache key from endpoint and params
        params_hash = CacheKey.hash_data(params)
        cache_key = CacheKey.build(
            "api",
            endpoint,
            params_hash,
            workspace_id=workspace_id
        )
        
        return await cache_service.get_or_set(
            cache_key,
            response_func,
            ttl
        )
    
    @staticmethod
    async def invalidate_endpoint(endpoint: str, workspace_id: Optional[str] = None):
        """Invalidate all responses for an endpoint"""
        if workspace_id:
            pattern = f"api:{endpoint}:*:workspace_id:{workspace_id}"
        else:
            pattern = f"api:{endpoint}:*"
        
        await cache_service.delete_pattern(pattern)

class VectorCache:
    """Vector search result caching"""
    
    @staticmethod
    async def cache_search(
        query: str,
        workspace_id: str,
        search_func: Callable,
        ttl: int = 600
    ) -> Any:
        """Cache vector search results"""
        query_hash = CacheKey.hash_data(query)
        cache_key = CacheKey.build(
            "vector_search",
            workspace_id,
            query_hash
        )
        
        return await cache_service.get_or_set(
            cache_key,
            search_func,
            ttl
        )
    
    @staticmethod
    async def invalidate_workspace(workspace_id: str):
        """Invalidate all vector searches for a workspace"""
        pattern = f"vector_search:{workspace_id}:*"
        await cache_service.delete_pattern(pattern)
