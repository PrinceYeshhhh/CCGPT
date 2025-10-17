"""
Production environment validation utilities
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx
import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db, get_redis
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class ProductionValidator:
    """Comprehensive production environment validation
    Test-friendly shim methods are provided to satisfy unit tests that expect
    simple synchronous validators and attributes like `checks`, `db`, and `redis_client`.
    """
    
    def __init__(self):
        self.validation_results = {}
        self.critical_failures = []
        self.warnings = []
        # Test-friendly attributes expected by unit tests
        try:
            self.db: Optional[Session] = next(get_db())
        except Exception:
            self.db = None
        try:
            self.redis_client = get_redis()
        except Exception:
            self.redis_client = None
        self.checks = {
            "environment": False,
            "database": False,
            "redis": False,
        }
    
    async def validate_all(self) -> Dict[str, Any]:
        """Run all production validations"""
        logger.info("Starting comprehensive production validation")
        
        # Reset validation state
        self.validation_results = {}
        self.critical_failures = []
        self.warnings = []
        
        # Run all validations
        await self.validate_environment_variables()
        await self.validate_database_connectivity()
        await self.validate_redis_connectivity()
        await self.validate_chromadb_connectivity()
        await self.validate_gemini_api()
        await self.validate_security_configuration()
        await self.validate_performance_settings()
        await self.validate_monitoring_setup()
        await self.validate_ssl_certificates()
        await self.validate_backup_configuration()
        await self.validate_logging_configuration()
        await self.validate_rate_limiting()
        await self.validate_cors_configuration()
        await self.validate_file_upload_limits()
        await self.validate_memory_usage()
        await self.validate_disk_space()
        await self.validate_network_connectivity()
        await self.validate_dependencies()
        await self.validate_health_checks()
        
        # Determine overall status
        overall_status = "healthy" if not self.critical_failures else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "critical_failures": self.critical_failures,
            "warnings": self.warnings,
            "validation_results": self.validation_results,
            "summary": {
                "total_checks": len(self.validation_results),
                "passed": len([r for r in self.validation_results.values() if r.get("status") == "passed"]),
                "failed": len([r for r in self.validation_results.values() if r.get("status") == "failed"]),
                "warnings": len(self.warnings)
            }
        }
    
    # ---------------- Test-friendly sync API below -----------------
    def validate_environment(self) -> bool:
        """Synchronous environment validation expected by unit tests."""
        required = ["DATABASE_URL", "REDIS_URL", "SECRET_KEY", "GEMINI_API_KEY"]
        missing = []
        for var in required:
            if not getattr(settings, var, None):
                missing.append(var)
        ok = len(missing) == 0
        self.checks["environment"] = ok
        return ok
    
    def validate_database_connection(self) -> bool:
        """Synchronous DB validation expected by unit tests."""
        try:
            if self.db is None:
                self.db = next(get_db())
            # Basic connectivity check
            self.db.execute(text("SELECT 1"))
            self.checks["database"] = True
            return True
        except Exception:
            self.checks["database"] = False
            return False
    
    def validate_redis_connection(self) -> bool:
        """Synchronous Redis validation expected by unit tests."""
        try:
            if self.redis_client is None:
                self.redis_client = get_redis()
            self.redis_client.ping()
            self.checks["redis"] = True
            return True
        except Exception:
            self.checks["redis"] = False
            return False
    
    def run_all_checks(self) -> Dict[str, bool]:
        """Run environment, database, and redis checks and return a simple map."""
        env_ok = self.validate_environment()
        db_ok = self.validate_database_connection()
        redis_ok = self.validate_redis_connection()
        return {
            "environment": env_ok,
            "database": db_ok,
            "redis": redis_ok,
        }
    
    async def validate_environment_variables(self):
        """Validate all required environment variables"""
        required_vars = [
            "DATABASE_URL", "REDIS_URL", "CHROMA_URL", "GEMINI_API_KEY",
            "SECRET_KEY", "STRIPE_API_KEY", "STRIPE_WEBHOOK_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(settings, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            self.critical_failures.append(f"Missing required environment variables: {', '.join(missing_vars)}")
            self.validation_results["environment_variables"] = {
                "status": "failed",
                "message": f"Missing variables: {', '.join(missing_vars)}"
            }
        else:
            self.validation_results["environment_variables"] = {
                "status": "passed",
                "message": "All required environment variables are set"
        }
    
    async def validate_database_connectivity(self):
        """Validate database connectivity and performance"""
        try:
            start_time = time.time()
            db = next(get_db())
            
            # Test basic connectivity
            result = db.execute(text("SELECT 1")).scalar()
            basic_latency = (time.time() - start_time) * 1000
            
            # Test connection pool
            start_time = time.time()
            db.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            query_latency = (time.time() - start_time) * 1000
            
            # Check database size
            size_result = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
            db_size_mb = size_result / (1024 * 1024)
            
            if basic_latency > 1000:  # More than 1 second
                self.warnings.append(f"Database basic connectivity is slow: {basic_latency:.2f}ms")
            
            if query_latency > 2000:  # More than 2 seconds
                self.warnings.append(f"Database queries are slow: {query_latency:.2f}ms")
            
            if db_size_mb > 1000:  # More than 1GB
                self.warnings.append(f"Database size is large: {db_size_mb:.2f}MB")
            
            self.validation_results["database_connectivity"] = {
                "status": "passed",
                "message": "Database connectivity successful",
                "metrics": {
                    "basic_latency_ms": round(basic_latency, 2),
                    "query_latency_ms": round(query_latency, 2),
                    "database_size_mb": round(db_size_mb, 2)
                }
            }
                
        except Exception as e:
            self.critical_failures.append(f"Database connectivity failed: {str(e)}")
            self.validation_results["database_connectivity"] = {
                "status": "failed",
                "message": f"Database connection failed: {str(e)}"
            }
    
    async def validate_redis_connectivity(self):
        """Validate Redis connectivity and performance"""
        try:
            start_time = time.time()
            redis_client = get_redis()
            redis_client.ping()
            latency = (time.time() - start_time) * 1000
            
            # Test Redis operations
            start_time = time.time()
            redis_client.set("test_key", "test_value", ex=10)
            redis_client.get("test_key")
            redis_client.delete("test_key")
            operation_latency = (time.time() - start_time) * 1000
            
            if latency > 100:  # More than 100ms
                self.warnings.append(f"Redis ping is slow: {latency:.2f}ms")
            
            if operation_latency > 500:  # More than 500ms
                self.warnings.append(f"Redis operations are slow: {operation_latency:.2f}ms")
            
            self.validation_results["redis_connectivity"] = {
                "status": "passed",
                "message": "Redis connectivity successful",
                "metrics": {
                    "ping_latency_ms": round(latency, 2),
                    "operation_latency_ms": round(operation_latency, 2)
                }
            }
                
        except Exception as e:
            self.critical_failures.append(f"Redis connectivity failed: {str(e)}")
            self.validation_results["redis_connectivity"] = {
                "status": "failed",
                "message": f"Redis connection failed: {str(e)}"
            }
    
    async def validate_chromadb_connectivity(self):
        """Validate ChromaDB connectivity"""
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.CHROMA_URL}/api/v1/heartbeat")
                latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if latency > 1000:  # More than 1 second
                    self.warnings.append(f"ChromaDB response is slow: {latency:.2f}ms")
                
                self.validation_results["chromadb_connectivity"] = {
                    "status": "passed",
                    "message": "ChromaDB connectivity successful",
                    "metrics": {
                        "response_latency_ms": round(latency, 2)
                    }
                }
            else:
                self.critical_failures.append(f"ChromaDB returned status {response.status_code}")
                self.validation_results["chromadb_connectivity"] = {
                    "status": "failed",
                    "message": f"ChromaDB returned status {response.status_code}"
                }
                
        except Exception as e:
            self.critical_failures.append(f"ChromaDB connectivity failed: {str(e)}")
            self.validation_results["chromadb_connectivity"] = {
                "status": "failed",
                "message": f"ChromaDB connection failed: {str(e)}"
            }
    
    async def validate_gemini_api(self):
        """Validate Gemini API connectivity"""
        try:
            if not settings.GEMINI_API_KEY:
                self.warnings.append("Gemini API key not configured")
                self.validation_results["gemini_api"] = {
                    "status": "skipped",
                    "message": "Gemini API key not configured"
                }
                return
            
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://generativelanguage.googleapis.com/v1beta/models",
                    params={"key": settings.GEMINI_API_KEY}
                )
                latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                if latency > 5000:  # More than 5 seconds
                    self.warnings.append(f"Gemini API response is slow: {latency:.2f}ms")
                
                self.validation_results["gemini_api"] = {
                    "status": "passed",
                    "message": "Gemini API connectivity successful",
                    "metrics": {
                        "response_latency_ms": round(latency, 2)
                    }
                }
            else:
                self.critical_failures.append(f"Gemini API returned status {response.status_code}")
                self.validation_results["gemini_api"] = {
                    "status": "failed",
                    "message": f"Gemini API returned status {response.status_code}"
                }
                
        except Exception as e:
            self.critical_failures.append(f"Gemini API connectivity failed: {str(e)}")
            self.validation_results["gemini_api"] = {
                "status": "failed",
                "message": f"Gemini API connection failed: {str(e)}"
            }
    
    async def validate_security_configuration(self):
        """Validate security configuration"""
        security_issues = []
        
        # Check if running in production mode
        if settings.DEBUG:
            security_issues.append("Debug mode is enabled in production")
        
        # Check secret key strength
        if len(settings.SECRET_KEY) < 32:
            security_issues.append("SECRET_KEY is too short (minimum 32 characters)")
        
        # Check if default secret key is being used
        if settings.SECRET_KEY == "your-secret-key-here":
            security_issues.append("Default SECRET_KEY is being used")
        
        # Check CORS configuration
        if "*" in settings.CORS_ORIGINS:
            security_issues.append("CORS is configured to allow all origins")
        
        if security_issues:
            self.critical_failures.extend(security_issues)
            self.validation_results["security_configuration"] = {
                "status": "failed",
                "message": f"Security issues found: {len(security_issues)}",
                "issues": security_issues
            }
        else:
            self.validation_results["security_configuration"] = {
                "status": "passed",
                "message": "Security configuration is appropriate"
            }
    
    async def validate_performance_settings(self):
        """Validate performance-related settings"""
        performance_issues = []
        
        # Check database pool settings
        if settings.DB_POOL_SIZE < 10:
            performance_issues.append("Database pool size is too small")
        
        if settings.DB_MAX_OVERFLOW < 5:
            performance_issues.append("Database max overflow is too small")
        
        # Check rate limiting settings
        if not settings.ENABLE_RATE_LIMITING:
            performance_issues.append("Rate limiting is disabled")
        
        if performance_issues:
            self.warnings.extend(performance_issues)
            self.validation_results["performance_settings"] = {
                "status": "warning",
                "message": f"Performance issues found: {len(performance_issues)}",
                "issues": performance_issues
            }
        else:
            self.validation_results["performance_settings"] = {
                "status": "passed",
                "message": "Performance settings are appropriate"
            }
    
    async def validate_monitoring_setup(self):
        """Validate monitoring and metrics setup"""
        monitoring_issues = []
        
        if not settings.PROMETHEUS_ENABLED:
            monitoring_issues.append("Prometheus metrics are disabled")
        
        if not settings.METRICS_ENABLED:
            monitoring_issues.append("Metrics collection is disabled")
        
        if not settings.HEALTH_CHECK_ENABLED:
            monitoring_issues.append("Health checks are disabled")
        
        if monitoring_issues:
            self.warnings.extend(monitoring_issues)
            self.validation_results["monitoring_setup"] = {
                "status": "warning",
                "message": f"Monitoring issues found: {len(monitoring_issues)}",
                "issues": monitoring_issues
            }
        else:
            self.validation_results["monitoring_setup"] = {
                "status": "passed",
                "message": "Monitoring setup is appropriate"
            }
    
    async def validate_ssl_certificates(self):
        """Validate SSL certificate configuration"""
        # This would check SSL certificates in production
        self.validation_results["ssl_certificates"] = {
            "status": "skipped",
            "message": "SSL certificate validation not implemented"
        }
    
    async def validate_backup_configuration(self):
        """Validate backup configuration"""
        # This would check backup configuration
        self.validation_results["backup_configuration"] = {
            "status": "skipped",
            "message": "Backup configuration validation not implemented"
        }
    
    async def validate_logging_configuration(self):
        """Validate logging configuration"""
        logging_issues = []
        
        if settings.LOG_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            logging_issues.append("Invalid log level")
        
        if settings.ENVIRONMENT == "production" and settings.LOG_LEVEL == "DEBUG":
            logging_issues.append("Debug logging enabled in production")
        
        if logging_issues:
            self.warnings.extend(logging_issues)
            self.validation_results["logging_configuration"] = {
                "status": "warning",
                "message": f"Logging issues found: {len(logging_issues)}",
                "issues": logging_issues
            }
        else:
            self.validation_results["logging_configuration"] = {
                "status": "passed",
                "message": "Logging configuration is appropriate"
            }
    
    async def validate_rate_limiting(self):
        """Validate rate limiting configuration"""
        if not settings.ENABLE_RATE_LIMITING:
            self.warnings.append("Rate limiting is disabled")
            self.validation_results["rate_limiting"] = {
                "status": "warning",
                "message": "Rate limiting is disabled"
            }
        else:
            self.validation_results["rate_limiting"] = {
                "status": "passed",
                "message": "Rate limiting is enabled"
            }
    
    async def validate_cors_configuration(self):
        """Validate CORS configuration"""
        if not settings.ENABLE_CORS:
            self.warnings.append("CORS is disabled")
            self.validation_results["cors_configuration"] = {
                "status": "warning",
                "message": "CORS is disabled"
            }
        else:
            self.validation_results["cors_configuration"] = {
                "status": "passed",
                "message": "CORS is properly configured"
            }
    
    async def validate_file_upload_limits(self):
        """Validate file upload limits"""
        if settings.MAX_FILE_SIZE > 50 * 1024 * 1024:  # 50MB
            self.warnings.append("File upload limit is very high")
            self.validation_results["file_upload_limits"] = {
                "status": "warning",
                "message": "File upload limit is very high"
            }
        else:
            self.validation_results["file_upload_limits"] = {
                "status": "passed",
                "message": "File upload limits are appropriate"
            }
    
    async def validate_memory_usage(self):
        """Validate memory usage"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.percent > 80:
                self.warnings.append(f"High memory usage: {memory.percent}%")
                self.validation_results["memory_usage"] = {
                    "status": "warning",
                    "message": f"High memory usage: {memory.percent}%"
                }
            else:
                self.validation_results["memory_usage"] = {
                    "status": "passed",
                    "message": f"Memory usage is normal: {memory.percent}%"
                }
        except ImportError:
            self.validation_results["memory_usage"] = {
                "status": "skipped",
                "message": "psutil not available for memory monitoring"
            }
    
    async def validate_disk_space(self):
        """Validate disk space"""
        try:
            import psutil
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.warnings.append(f"Low disk space: {disk.percent}% used")
                self.validation_results["disk_space"] = {
                    "status": "warning",
                    "message": f"Low disk space: {disk.percent}% used"
                }
            else:
                self.validation_results["disk_space"] = {
                    "status": "passed",
                    "message": f"Disk space is adequate: {disk.percent}% used"
                }
        except ImportError:
            self.validation_results["disk_space"] = {
                "status": "skipped",
                "message": "psutil not available for disk monitoring"
            }
    
    async def validate_network_connectivity(self):
        """Validate network connectivity"""
        # This would test network connectivity to external services
        self.validation_results["network_connectivity"] = {
            "status": "skipped",
            "message": "Network connectivity validation not implemented"
        }
    
    async def validate_dependencies(self):
        """Validate all dependencies are available"""
        try:
            # Test critical imports
            import fastapi
            import sqlalchemy
            import redis
            import httpx
            import pydantic
            
            self.validation_results["dependencies"] = {
                "status": "passed",
                "message": "All critical dependencies are available"
            }
        except ImportError as e:
            self.critical_failures.append(f"Missing dependency: {str(e)}")
            self.validation_results["dependencies"] = {
                "status": "failed",
                "message": f"Missing dependency: {str(e)}"
            }
    
    async def validate_health_checks(self):
        """Validate health check endpoints"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                base = getattr(settings, 'API_BASE_URL', None) or getattr(settings, 'PUBLIC_BASE_URL', None) or ""
                url = f"{base}/health" if base else "/health"
                response = await client.get(url)
                if response.status_code == 200:
                    self.validation_results["health_checks"] = {
                        "status": "passed",
                        "message": "Health check endpoint is working"
                    }
                else:
                    self.critical_failures.append(f"Health check returned status {response.status_code}")
                    self.validation_results["health_checks"] = {
                        "status": "failed",
                        "message": f"Health check returned status {response.status_code}"
                    }
        except Exception as e:
            self.critical_failures.append(f"Health check failed: {str(e)}")
            self.validation_results["health_checks"] = {
                "status": "failed",
                "message": f"Health check failed: {str(e)}"
            }

# Global validator instance
production_validator = ProductionValidator()
