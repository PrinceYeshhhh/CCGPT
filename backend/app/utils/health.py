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
from app.utils.metrics import metrics_collector

logger = structlog.get_logger()


class HealthChecker:
    """Comprehensive health check system"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "chromadb": self._check_chromadb,
            "security": self._check_security,
            "performance": self._check_performance,
            "dependencies": self._check_dependencies
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            from app.core.database import db_manager
            
            # Use enhanced database health check
            health_status = await db_manager.health_check()
            
            if health_status['overall']:
                # Get response times
                response_times = health_status.get('response_times', {})
                avg_response_time = sum(response_times.values()) / len(response_times) if response_times else 0
                
                # Get connection stats
                connection_stats = health_status.get('connection_stats', {})
                write_stats = connection_stats.get('write_db', {})
                
                return {
                    "status": "healthy",
                    "response_time_ms": round(avg_response_time, 2),
                    "write_db_healthy": health_status['write_db'],
                    "read_dbs_healthy": health_status['read_dbs'],
                    "connection_pool_size": write_stats.get('size', 0),
                    "active_connections": write_stats.get('checked_out', 0),
                    "idle_connections": write_stats.get('checked_in', 0),
                    "invalid_connections": write_stats.get('invalid', 0),
                    "message": "Database connection successful"
                }
            else:
                return {
                    "status": "unhealthy",
                    "write_db_healthy": health_status['write_db'],
                    "read_dbs_healthy": health_status['read_dbs'],
                    "message": "Database connection failed"
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
    
    async def _check_chromadb(self) -> Dict[str, Any]:
        """Check ChromaDB connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test ChromaDB connection
            import chromadb
            from chromadb.config import Settings
            
            # Initialize ChromaDB client
            client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Test basic operations
            collection_name = "health_check_test"
            try:
                # Try to get or create a test collection
                collection = client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Health check test collection"}
                )
                
                # Test adding a document
                test_id = "health_check_doc"
                test_doc = "This is a health check test document"
                collection.add(
                    documents=[test_doc],
                    ids=[test_id]
                )
                
                # Test querying
                results = collection.query(
                    query_texts=["health check"],
                    n_results=1
                )
                
                # Clean up test data
                collection.delete(ids=[test_id])
                
                if not results['documents'] or len(results['documents'][0]) == 0:
                    raise Exception("ChromaDB query returned no results")
                
            except Exception as e:
                # Clean up test collection if it exists
                try:
                    client.delete_collection(collection_name)
                except:
                    pass
                raise e
            
            response_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "message": "ChromaDB connection successful"
            }
            
        except Exception as e:
            logger.error("ChromaDB health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "message": "ChromaDB connection failed"
            }
    
    async def _check_security(self) -> Dict[str, Any]:
        """Check security system status"""
        try:
            # Check if security headers are enabled
            security_headers_enabled = settings.ENABLE_SECURITY_HEADERS
            rate_limiting_enabled = settings.ENABLE_RATE_LIMITING
            input_validation_enabled = settings.ENABLE_INPUT_VALIDATION
            
            # Check if we're in production mode
            is_production = settings.ENVIRONMENT.lower() == "production"
            
            # Basic security configuration check
            security_issues = []
            if not security_headers_enabled:
                security_issues.append("Security headers disabled")
            if not rate_limiting_enabled:
                security_issues.append("Rate limiting disabled")
            if not input_validation_enabled:
                security_issues.append("Input validation disabled")
            
            # Check if critical secrets are set
            if is_production:
                if not settings.SECRET_KEY or settings.SECRET_KEY == "":
                    security_issues.append("SECRET_KEY not set")
                if not settings.JWT_SECRET or settings.JWT_SECRET == "":
                    security_issues.append("JWT_SECRET not set")
                if not settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL:
                    security_issues.append("Using SQLite in production")
            
            # Determine security status
            if security_issues:
                status = "warning" if len(security_issues) < 3 else "unhealthy"
                message = f"Security issues detected: {', '.join(security_issues)}"
            else:
                status = "healthy"
                message = "Security configuration looks good"
            
            return {
                "status": status,
                "security_headers_enabled": security_headers_enabled,
                "rate_limiting_enabled": rate_limiting_enabled,
                "input_validation_enabled": input_validation_enabled,
                "is_production": is_production,
                "issues": security_issues,
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
            
            # Try to get system metrics if psutil is available
            memory_percent = None
            cpu_percent = None
            
            try:
                import psutil
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                cpu_percent = psutil.cpu_percent(interval=1)
            except ImportError:
                logger.warning("psutil not available, skipping system metrics")
            except Exception as e:
                logger.warning(f"Failed to get system metrics: {e}")
            
            # Determine performance status
            status = "healthy"
            message = "Performance metrics within normal range"
            
            if memory_percent is not None and memory_percent > 90:
                status = "warning"
                message = f"High memory usage: {memory_percent}%"
            elif cpu_percent is not None and cpu_percent > 80:
                status = "warning"
                message = f"High CPU usage: {cpu_percent}%"
            
            return {
                "status": status,
                "uptime_seconds": uptime_seconds,
                "memory_percent": memory_percent,
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
    critical_checks = ["database", "redis", "chromadb"]
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
            # Basic security configuration check
            security_ok = (
                settings.ENABLE_SECURITY_HEADERS and
                settings.ENABLE_RATE_LIMITING and
                settings.ENABLE_INPUT_VALIDATION
            )
            if security_ok:
                results["security"] = {"status": "healthy", "message": "Security systems operational"}
            else:
                results["security"] = {"status": "warning", "message": "Some security features disabled"}
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


async def get_external_services_status() -> Dict[str, Any]:
    """Check external services like Gemini API, Stripe, etc."""
    try:
        results = {}
        
        # Gemini API check
        try:
            if settings.GEMINI_API_KEY:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                # Test API with a simple request
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content("Hello")
                
                if response and response.text:
                    results["gemini_api"] = {
                        "status": "healthy", 
                        "message": "Gemini API accessible"
                    }
                else:
                    results["gemini_api"] = {
                        "status": "warning", 
                        "message": "Gemini API responded but no content"
                    }
            else:
                results["gemini_api"] = {
                    "status": "warning", 
                    "message": "Gemini API key not configured"
                }
        except Exception as e:
            results["gemini_api"] = {
                "status": "unhealthy", 
                "message": f"Gemini API error: {str(e)}"
            }
        
        # Stripe API check (if configured)
        try:
            if settings.STRIPE_API_KEY:
                import stripe
                stripe.api_key = settings.STRIPE_API_KEY
                
                # Test API with a simple request
                stripe.Account.retrieve()
                
                results["stripe_api"] = {
                    "status": "healthy", 
                    "message": "Stripe API accessible"
                }
            else:
                results["stripe_api"] = {
                    "status": "warning", 
                    "message": "Stripe API key not configured"
                }
        except Exception as e:
            results["stripe_api"] = {
                "status": "unhealthy", 
                "message": f"Stripe API error: {str(e)}"
            }
        
        # Determine overall status
        unhealthy_services = [name for name, result in results.items() if result["status"] == "unhealthy"]
        warning_services = [name for name, result in results.items() if result["status"] == "warning"]
        
        if unhealthy_services:
            overall_status = "unhealthy"
        elif warning_services:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "services": results,
            "unhealthy_services": unhealthy_services,
            "warning_services": warning_services
        }
        
    except Exception as e:
        logger.error("External services check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }