"""
Health check and readiness probe implementation
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class HealthChecker:
    """Health check implementation"""
    
    def __init__(self):
        self.checks = {
            'database': self.check_database,
            'redis': self.check_redis,
            'chromadb': self.check_chromadb,
            'gemini_api': self.check_gemini_api,
            'vector_search': self.check_vector_search
        }
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        start_time = time.time()
        try:
            db = next(get_db())
            result = db.execute(text("SELECT 1")).scalar()
            duration = time.time() - start_time
            
            if result == 1:
                return {
                    'status': 'healthy',
                    'duration_ms': round(duration * 1000, 2),
                    'details': 'Database connection successful'
                }
            else:
                return {
                    'status': 'unhealthy',
                    'duration_ms': round(duration * 1000, 2),
                    'details': 'Database query returned unexpected result'
                }
        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': 'unhealthy',
                'duration_ms': round(duration * 1000, 2),
                'details': f'Database connection failed: {str(e)}'
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        start_time = time.time()
        try:
            r = redis.from_url(settings.REDIS_URL)
            r.ping()
            duration = time.time() - start_time
            
            return {
                'status': 'healthy',
                'duration_ms': round(duration * 1000, 2),
                'details': 'Redis connection successful'
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': 'unhealthy',
                'duration_ms': round(duration * 1000, 2),
                'details': f'Redis connection failed: {str(e)}'
            }
    
    async def check_chromadb(self) -> Dict[str, Any]:
        """Check ChromaDB connectivity"""
        start_time = time.time()
        try:
            # Import here to avoid circular imports
            from app.services.vector_search import vector_search_service
            
            # Try to get collection info
            collections = vector_search_service.list_collections()
            duration = time.time() - start_time
            
            return {
                'status': 'healthy',
                'duration_ms': round(duration * 1000, 2),
                'details': f'ChromaDB accessible, {len(collections)} collections found'
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': 'unhealthy',
                'duration_ms': round(duration * 1000, 2),
                'details': f'ChromaDB connection failed: {str(e)}'
            }
    
    async def check_gemini_api(self) -> Dict[str, Any]:
        """Check Gemini API connectivity (optional)"""
        start_time = time.time()
        try:
            if not settings.GEMINI_API_KEY:
                return {
                    'status': 'skipped',
                    'duration_ms': 0,
                    'details': 'Gemini API key not configured'
                }
            
            # Simple API test
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": settings.GEMINI_API_KEY}
                )
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    return {
                        'status': 'healthy',
                        'duration_ms': round(duration * 1000, 2),
                        'details': 'Gemini API accessible'
                    }
                else:
                    return {
                        'status': 'unhealthy',
                        'duration_ms': round(duration * 1000, 2),
                        'details': f'Gemini API returned status {response.status_code}'
                    }
        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': 'unhealthy',
                'duration_ms': round(duration * 1000, 2),
                'details': f'Gemini API check failed: {str(e)}'
            }
    
    async def check_vector_search(self) -> Dict[str, Any]:
        """Check vector search functionality"""
        start_time = time.time()
        try:
            from app.services.vector_search import vector_search_service
            
            # Try a simple search
            results = await vector_search_service.search(
                workspace_id="health_check",
                query="test query",
                top_k=1
            )
            duration = time.time() - start_time
            
            return {
                'status': 'healthy',
                'duration_ms': round(duration * 1000, 2),
                'details': f'Vector search functional, returned {len(results)} results'
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                'status': 'unhealthy',
                'duration_ms': round(duration * 1000, 2),
                'details': f'Vector search failed: {str(e)}'
            }
    
    async def run_health_checks(self, components: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run health checks for specified components"""
        if components is None:
            components = list(self.checks.keys())
        
        results = {}
        overall_status = 'healthy'
        
        # Run checks concurrently
        tasks = []
        for component in components:
            if component in self.checks:
                tasks.append(self._run_single_check(component))
        
        check_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, component in enumerate(components):
            if i < len(check_results):
                result = check_results[i]
                if isinstance(result, Exception):
                    results[component] = {
                        'status': 'unhealthy',
                        'duration_ms': 0,
                        'details': f'Check failed with exception: {str(result)}'
                    }
                    overall_status = 'unhealthy'
                else:
                    results[component] = result
                    if result['status'] != 'healthy':
                        overall_status = 'unhealthy'
            else:
                results[component] = {
                    'status': 'unhealthy',
                    'duration_ms': 0,
                    'details': 'Check not found'
                }
                overall_status = 'unhealthy'
        
        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'components': results
        }
    
    async def _run_single_check(self, component: str) -> Dict[str, Any]:
        """Run a single health check"""
        try:
            return await self.checks[component]()
        except Exception as e:
            return {
                'status': 'unhealthy',
                'duration_ms': 0,
                'details': f'Check failed: {str(e)}'
            }

# Global health checker instance
health_checker = HealthChecker()

async def get_health_status() -> Dict[str, Any]:
    """Get basic health status (liveness probe)"""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'customercaregpt-api',
        'version': '1.0.0'
    }

async def get_readiness_status(components: Optional[List[str]] = None) -> Dict[str, Any]:
    """Get readiness status (readiness probe)"""
    return await health_checker.run_health_checks(components)

async def get_startup_checks() -> Dict[str, Any]:
    """Run startup checks (all components)"""
    return await health_checker.run_health_checks()

async def get_detailed_health_status() -> Dict[str, Any]:
    """Get detailed health status with performance metrics"""
    try:
        # Run all health checks
        health_results = await health_checker.run_health_checks()
        
        # Get additional metrics
        from app.core.database import db_manager, redis_manager
        from app.services.enhanced_vector_service import enhanced_vector_service
        from app.core.queue import queue_manager
        
        # Database health
        db_health = await db_manager.health_check()
        
        # Redis health
        redis_health = await redis_manager.health_check()
        
        # Vector DB health
        vector_health = await enhanced_vector_service.health_check()
        
        # Queue stats
        queue_stats = queue_manager.get_queue_stats()
        
        # Circuit breaker stats
        from app.utils.circuit_breaker import circuit_breaker_manager
        circuit_breaker_stats = circuit_breaker_manager.get_all_stats()
        
        # Performance metrics
        performance_metrics = {
            'database_connections': {
                'write_pool_size': db_health.get('write_pool_size', 0),
                'read_pool_size': db_health.get('read_pool_size', 0),
                'active_connections': db_health.get('active_connections', 0)
            },
            'redis_connections': {
                'connection_pool_size': redis_health.get('connection_pool_size', 0),
                'active_connections': redis_health.get('active_connections', 0)
            },
            'queue_lengths': queue_stats,
            'circuit_breakers': circuit_breaker_stats
        }
        
        # Overall health assessment
        overall_healthy = (
            health_results['status'] == 'healthy' and
            db_health.get('overall', False) and
            redis_health and
            vector_health.get('status') == 'healthy'
        )
        
        return {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': health_results['components'],
            'database': db_health,
            'redis': redis_health,
            'vector_db': vector_health,
            'performance': performance_metrics,
            'overall_healthy': overall_healthy
        }
        
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        return {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e),
            'overall_healthy': False
        }

# Kubernetes probe examples
KUBERNETES_LIVENESS_PROBE = {
    "httpGet": {
        "path": "/health",
        "port": 8000
    },
    "initialDelaySeconds": 30,
    "periodSeconds": 10,
    "timeoutSeconds": 5,
    "failureThreshold": 3
}

KUBERNETES_READINESS_PROBE = {
    "httpGet": {
        "path": "/ready",
        "port": 8000
    },
    "initialDelaySeconds": 5,
    "periodSeconds": 5,
    "timeoutSeconds": 3,
    "failureThreshold": 3
}
