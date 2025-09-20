"""
Redis caching layer with TTL and invalidation
"""

import redis
import json
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import asyncio

from app.core.config import settings
from app.utils.logger import get_logger, log_performance
from app.utils.metrics import MetricsCollector

logger = get_logger(__name__)

class CacheManager:
    """Redis-based cache manager with TTL and invalidation"""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.default_ttl = 600  # 10 minutes
        self.cache_prefixes = {
            'vector_search': 'vs',
            'analytics': 'analytics',
            'embed_code': 'embed',
            'subscription': 'sub',
            'workspace': 'ws'
        }
    
    def _get_cache_key(self, prefix: str, key: str) -> str:
        """Generate cache key with prefix"""
        return f"cache:{self.cache_prefixes.get(prefix, prefix)}:{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize value for storage"""
        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str)
        return str(value)
    
    def _deserialize_value(self, value: str, default_type: type = str) -> Any:
        """Deserialize value from storage"""
        try:
            if default_type in (dict, list):
                return json.loads(value)
            return default_type(value)
        except (json.JSONDecodeError, ValueError):
            return value
    
    async def get(
        self, 
        prefix: str, 
        key: str, 
        default: Any = None,
        deserialize_type: type = str
    ) -> Any:
        """Get value from cache"""
        cache_key = self._get_cache_key(prefix, key)
        
        try:
            value = self.redis_client.get(cache_key)
            if value is None:
                MetricsCollector.record_cache_miss(prefix)
                return default
            
            MetricsCollector.record_cache_hit(prefix)
            return self._deserialize_value(value.decode('utf-8'), deserialize_type)
            
        except Exception as e:
            logger.error(f"Cache get failed for {cache_key}: {e}")
            return default
    
    async def set(
        self, 
        prefix: str, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL"""
        cache_key = self._get_cache_key(prefix, key)
        
        try:
            serialized_value = self._serialize_value(value)
            ttl = ttl or self.default_ttl
            
            result = self.redis_client.setex(cache_key, ttl, serialized_value)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache set failed for {cache_key}: {e}")
            return False
    
    async def delete(self, prefix: str, key: str) -> bool:
        """Delete value from cache"""
        cache_key = self._get_cache_key(prefix, key)
        
        try:
            result = self.redis_client.delete(cache_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Cache delete failed for {cache_key}: {e}")
            return False
    
    async def delete_pattern(self, prefix: str, pattern: str) -> int:
        """Delete all keys matching pattern"""
        cache_prefix = self._get_cache_key(prefix, "")
        full_pattern = f"{cache_prefix}*{pattern}*"
        
        try:
            keys = self.redis_client.keys(full_pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Cache delete pattern failed for {full_pattern}: {e}")
            return 0
    
    async def exists(self, prefix: str, key: str) -> bool:
        """Check if key exists in cache"""
        cache_key = self._get_cache_key(prefix, key)
        
        try:
            return bool(self.redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"Cache exists check failed for {cache_key}: {e}")
            return False
    
    async def get_ttl(self, prefix: str, key: str) -> int:
        """Get TTL for key"""
        cache_key = self._get_cache_key(prefix, key)
        
        try:
            return self.redis_client.ttl(cache_key)
        except Exception as e:
            logger.error(f"Cache TTL check failed for {cache_key}: {e}")
            return -1
    
    async def extend_ttl(self, prefix: str, key: str, ttl: int) -> bool:
        """Extend TTL for key"""
        cache_key = self._get_cache_key(prefix, key)
        
        try:
            return bool(self.redis_client.expire(cache_key, ttl))
        except Exception as e:
            logger.error(f"Cache TTL extension failed for {cache_key}: {e}")
            return False

class VectorSearchCache:
    """Specialized cache for vector search results"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.ttl = int(settings.VECTOR_CACHE_TTL) if hasattr(settings, 'VECTOR_CACHE_TTL') else 600
    
    def _generate_query_hash(self, workspace_id: str, query: str, top_k: int) -> str:
        """Generate hash for query parameters"""
        query_data = f"{workspace_id}:{query}:{top_k}"
        return hashlib.md5(query_data.encode('utf-8')).hexdigest()
    
    async def get_search_results(
        self, 
        workspace_id: str, 
        query: str, 
        top_k: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached vector search results"""
        query_hash = self._generate_query_hash(workspace_id, query, top_k)
        return await self.cache.get(
            'vector_search', 
            query_hash, 
            deserialize_type=list
        )
    
    async def set_search_results(
        self, 
        workspace_id: str, 
        query: str, 
        top_k: int, 
        results: List[Dict[str, Any]]
    ) -> bool:
        """Cache vector search results"""
        query_hash = self._generate_query_hash(workspace_id, query, top_k)
        return await self.cache.set(
            'vector_search', 
            query_hash, 
            results, 
            ttl=self.ttl
        )
    
    async def invalidate_workspace(self, workspace_id: str) -> int:
        """Invalidate all vector search cache for workspace"""
        return await self.cache.delete_pattern('vector_search', f"*{workspace_id}*")

class AnalyticsCache:
    """Specialized cache for analytics data"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.ttl = 300  # 5 minutes for analytics
    
    async def get_analytics_summary(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analytics summary"""
        return await self.cache.get(
            'analytics', 
            f"summary:{workspace_id}", 
            deserialize_type=dict
        )
    
    async def set_analytics_summary(
        self, 
        workspace_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Cache analytics summary"""
        return await self.cache.set(
            'analytics', 
            f"summary:{workspace_id}", 
            data, 
            ttl=self.ttl
        )
    
    async def get_queries_over_time(
        self, 
        workspace_id: str, 
        period: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached queries over time data"""
        return await self.cache.get(
            'analytics', 
            f"queries_over_time:{workspace_id}:{period}", 
            deserialize_type=list
        )
    
    async def set_queries_over_time(
        self, 
        workspace_id: str, 
        period: str, 
        data: List[Dict[str, Any]]
    ) -> bool:
        """Cache queries over time data"""
        return await self.cache.set(
            'analytics', 
            f"queries_over_time:{workspace_id}:{period}", 
            data, 
            ttl=self.ttl
        )
    
    async def invalidate_workspace(self, workspace_id: str) -> int:
        """Invalidate all analytics cache for workspace"""
        return await self.cache.delete_pattern('analytics', f"*{workspace_id}*")

class EmbedCodeCache:
    """Specialized cache for embed codes"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.ttl = 3600  # 1 hour for embed codes
    
    async def get_embed_code(self, embed_id: str) -> Optional[Dict[str, Any]]:
        """Get cached embed code"""
        return await self.cache.get(
            'embed_code', 
            embed_id, 
            deserialize_type=dict
        )
    
    async def set_embed_code(
        self, 
        embed_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Cache embed code"""
        return await self.cache.set(
            'embed_code', 
            embed_id, 
            data, 
            ttl=self.ttl
        )
    
    async def invalidate_embed_code(self, embed_id: str) -> bool:
        """Invalidate embed code cache"""
        return await self.cache.delete('embed_code', embed_id)

# Global cache instances
cache_manager = CacheManager()
vector_search_cache = VectorSearchCache(cache_manager)
analytics_cache = AnalyticsCache(cache_manager)
embed_code_cache = EmbedCodeCache(cache_manager)

# Cache decorator
def cache_result(prefix: str, ttl: int = 600, key_func: Optional[callable] = None):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [str(arg) for arg in args[1:]]  # Skip self
                key_parts.extend([f"{k}:{v}" for k, v in kwargs.items()])
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = await cache_manager.get(prefix, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(prefix, cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Cache invalidation helpers
async def invalidate_workspace_cache(workspace_id: str):
    """Invalidate all cache entries for a workspace"""
    tasks = [
        vector_search_cache.invalidate_workspace(workspace_id),
        analytics_cache.invalidate_workspace(workspace_id)
    ]
    await asyncio.gather(*tasks)

async def invalidate_embed_cache(embed_id: str):
    """Invalidate embed code cache"""
    await embed_code_cache.invalidate_embed_code(embed_id)
