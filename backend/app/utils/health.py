"""
Comprehensive health check system for CustomerCareGPT
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import structlog

from app.core.config import settings
from app.core.database import redis_manager, write_engine
from app.utils.security_monitor import get_security_monitor

logger = structlog.get_logger()


class HealthChecker:
    """Comprehensive health check system"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "security": self._check_security,
            "performance": self._check_performance,
            "dependencies": self._check_dependencies
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            from sqlalchemy import text
            with write_engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).fetchone()
                if not result:
                    raise Exception("Database query returned no results")
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "message": "Database connection successful"
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Database connection failed"
            }
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test Redis connection
            redis_client = redis_manager.get_client()
            redis_client.ping()
            
            # Test basic operations
            test_key = "health_check_test"
            redis_client.set(test_key, "test_value", ex=10)
            value = redis_client.get(test_key)
            redis_client.delete(test_key)
            
            if value != "test_value":
                raise Exception("Redis read/write test failed")
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "message": "Redis connection successful"
            }
            
        except Exception as e:
            logger.error("Redis health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Redis connection failed"
            }
    
    async def _check_security(self) -> Dict[str, Any]:
        """Check security system status"""
        try:
            security_monitor = get_security_monitor()
            summary = security_monitor.get_security_summary()
            anomalies = security_monitor.detect_anomalies()
            
            # Determine security status
            if summary["blocked_ips"] > 100:  # High number of blocked IPs
                status = "warning"
                message = f"High number of blocked IPs: {summary['blocked_ips']}"
            elif len(anomalies) > 5:  # Many anomalies detected
                status = "warning"
                message = f"Multiple security anomalies detected: {len(anomalies)}"
            else:
                status = "healthy"
                message = "Security system operating normally"
            
            return {
                "status": status,
                "blocked_ips": summary["blocked_ips"],
                "recent_events": summary["recent_events"],
                "anomalies": len(anomalies),
                "message": message
            }
            
        except Exception as e:
            logger.error("Security health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Security system check failed"
            }
    
    async def _check_performance(self) -> Dict[str, Any]:
        """Check system performance metrics"""
        try:
            # Get system uptime
            uptime = datetime.utcnow() - self.start_time
            uptime_seconds = uptime.total_seconds()
            
            # Check memory usage (simplified)
            import psutil
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Determine performance status
            if memory.percent > 90:
                status = "warning"
                message = f"High memory usage: {memory.percent}%"
            elif cpu_percent > 80:
                status = "warning"
                message = f"High CPU usage: {cpu_percent}%"
            else:
                status = "healthy"
                message = "Performance metrics within normal range"
            
            return {
                "status": status,
                "uptime_seconds": uptime_seconds,
                "memory_percent": memory.percent,
                "cpu_percent": cpu_percent,
                "message": message
            }
            
        except Exception as e:
            logger.error("Performance health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Performance check failed"
            }
    
    async def _check_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies"""
        try:
            dependencies = {}
            
            # Check if we can import required modules
            try:
                import redis
                dependencies["redis"] = "available"
            except ImportError:
                dependencies["redis"] = "missing"
            
            try:
                import psutil
                dependencies["psutil"] = "available"
            except ImportError:
                dependencies["psutil"] = "missing"
            
            # Check if all critical dependencies are available
            missing_deps = [dep for dep, status in dependencies.items() if status == "missing"]
            
            if missing_deps:
                status = "warning"
                message = f"Missing dependencies: {', '.join(missing_deps)}"
            else:
                status = "healthy"
                message = "All dependencies available"
            
            return {
                "status": status,
                "dependencies": dependencies,
                "message": message
            }
            
        except Exception as e:
            logger.error("Dependencies health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "Dependencies check failed"
            }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        start_time = time.time()
        results = {}
        
        # Run all checks concurrently
        check_tasks = []
        for check_name, check_func in self.checks.items():
            task = asyncio.create_task(check_func())
            check_tasks.append((check_name, task))
        
        # Wait for all checks to complete
        for check_name, task in check_tasks:
            try:
                results[check_name] = await task
            except Exception as e:
                logger.error(f"Health check {check_name} failed", error=str(e))
                results[check_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "message": f"Health check {check_name} failed"
                }
        
        # Determine overall status
        overall_status = "healthy"
        if any(result["status"] == "unhealthy" for result in results.values()):
            overall_status = "unhealthy"
        elif any(result["status"] == "warning" for result in results.values()):
            overall_status = "warning"
        
        total_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": round(total_time, 2),
            "checks": results
        }


# Global health checker instance
health_checker = HealthChecker()


async def get_health_status() -> Dict[str, Any]:
    """Get basic health status"""
    return await health_checker.run_all_checks()


async def get_readiness_status() -> Dict[str, Any]:
    """Get readiness status for Kubernetes"""
    # Only check critical services for readiness
    critical_checks = ["database", "redis"]
    results = {}
    
    for check_name in critical_checks:
        if check_name in health_checker.checks:
            results[check_name] = await health_checker.checks[check_name]()
    
    # Determine readiness
    is_ready = all(
        result["status"] == "healthy" 
        for result in results.values()
    )
    
    return {
        "ready": is_ready,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": results
    }


async def get_detailed_health_status() -> Dict[str, Any]:
    """Get detailed health status with performance metrics"""
    return await health_checker.run_all_checks()


async def get_startup_checks() -> Dict[str, Any]:
    """Get startup health checks for application initialization"""
    try:
        # Basic connectivity checks
        results = {}
        
        # Database check
        try:
            from sqlalchemy import text
            with write_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results["database"] = {"status": "healthy", "message": "Database accessible"}
        except Exception as e:
            results["database"] = {"status": "unhealthy", "message": f"Database error: {str(e)}"}
        
        # Redis check
        try:
            redis_client = redis_manager.get_client()
            redis_client.ping()
            results["redis"] = {"status": "healthy", "message": "Redis accessible"}
        except Exception as e:
            results["redis"] = {"status": "unhealthy", "message": f"Redis error: {str(e)}"}
        
        # Security check
        try:
            security_monitor = get_security_monitor()
            results["security"] = {"status": "healthy", "message": "Security systems operational"}
        except Exception as e:
            results["security"] = {"status": "unhealthy", "message": f"Security error: {str(e)}"}
        
        return {
            "startup_ready": all(check["status"] == "healthy" for check in results.values()),
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }
        
    except Exception as e:
        logger.error("Startup checks failed", error=str(e))
        return {
            "startup_ready": False,
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }