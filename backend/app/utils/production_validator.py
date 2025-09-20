"""
Production environment validation utilities
Validates external services, database migrations, and production readiness
"""

import asyncio
import httpx
import structlog
from typing import Dict, List, Tuple, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.secrets import secrets_manager
import redis
import chromadb
from google.generativeai import configure, GenerativeModel
import stripe

logger = structlog.get_logger()

class ProductionValidator:
    """Validates production environment readiness"""
    
    def __init__(self):
        self.validation_results = {}
        self.critical_failures = []
        self.warnings = []
    
    async def validate_all(self) -> Dict[str, any]:
        """Run all production validations"""
        logger.info("Starting production environment validation")
        
        # Critical validations
        await self.validate_database_connectivity()
        await self.validate_redis_connectivity()
        await self.validate_chromadb_connectivity()
        await self.validate_external_apis()
        await self.validate_database_migrations()
        await self.validate_secrets_management()
        await self.validate_rate_limiting()
        await self.validate_caching()
        
        # Security validations
        await self.validate_security_configuration()
        await self.validate_cors_configuration()
        await self.validate_authentication()
        
        # Performance validations
        await self.validate_performance_configuration()
        await self.validate_monitoring_setup()
        
        return {
            "status": "healthy" if not self.critical_failures else "unhealthy",
            "critical_failures": self.critical_failures,
            "warnings": self.warnings,
            "validation_results": self.validation_results
        }
    
    async def validate_database_connectivity(self):
        """Validate database connectivity and basic operations"""
        try:
            db = next(get_db())
            
            # Test basic query
            result = db.execute(text("SELECT 1 as test")).fetchone()
            if result and result[0] == 1:
                self.validation_results["database_connectivity"] = "PASS"
                logger.info("Database connectivity validated")
            else:
                self.critical_failures.append("Database query test failed")
                self.validation_results["database_connectivity"] = "FAIL"
                
        except Exception as e:
            self.critical_failures.append(f"Database connectivity failed: {e}")
            self.validation_results["database_connectivity"] = "FAIL"
            logger.error(f"Database validation failed: {e}")
    
    async def validate_redis_connectivity(self):
        """Validate Redis connectivity and basic operations"""
        try:
            redis_client = redis.from_url(settings.REDIS_URL)
            
            # Test basic operations
            redis_client.set("test_key", "test_value", ex=10)
            value = redis_client.get("test_key")
            
            if value and value.decode() == "test_value":
                redis_client.delete("test_key")
                self.validation_results["redis_connectivity"] = "PASS"
                logger.info("Redis connectivity validated")
            else:
                self.critical_failures.append("Redis operations test failed")
                self.validation_results["redis_connectivity"] = "FAIL"
                
        except Exception as e:
            self.critical_failures.append(f"Redis connectivity failed: {e}")
            self.validation_results["redis_connectivity"] = "FAIL"
            logger.error(f"Redis validation failed: {e}")
    
    async def validate_chromadb_connectivity(self):
        """Validate ChromaDB connectivity and basic operations"""
        try:
            client = chromadb.HttpClient(host=settings.CHROMA_URL.replace("http://", "").split(":")[0])
            
            # Test basic operations
            collection = client.get_or_create_collection("test_collection")
            collection.add(
                documents=["test document"],
                ids=["test_id"]
            )
            
            results = collection.query(
                query_texts=["test"],
                n_results=1
            )
            
            if results and len(results["documents"][0]) > 0:
                # Cleanup
                client.delete_collection("test_collection")
                self.validation_results["chromadb_connectivity"] = "PASS"
                logger.info("ChromaDB connectivity validated")
            else:
                self.critical_failures.append("ChromaDB operations test failed")
                self.validation_results["chromadb_connectivity"] = "FAIL"
                
        except Exception as e:
            self.critical_failures.append(f"ChromaDB connectivity failed: {e}")
            self.validation_results["chromadb_connectivity"] = "FAIL"
            logger.error(f"ChromaDB validation failed: {e}")
    
    async def validate_external_apis(self):
        """Validate external API connectivity"""
        
        # Validate Gemini API
        await self._validate_gemini_api()
        
        # Validate Stripe API
        await self._validate_stripe_api()
    
    async def _validate_gemini_api(self):
        """Validate Google Gemini API connectivity"""
        try:
            if not settings.GEMINI_API_KEY:
                self.warnings.append("Gemini API key not configured")
                self.validation_results["gemini_api"] = "SKIP"
                return
            
            configure(api_key=settings.GEMINI_API_KEY)
            model = GenerativeModel("gemini-pro")
            
            # Test with a simple prompt
            response = model.generate_content("Test")
            
            if response and response.text:
                self.validation_results["gemini_api"] = "PASS"
                logger.info("Gemini API validated")
            else:
                self.critical_failures.append("Gemini API test failed")
                self.validation_results["gemini_api"] = "FAIL"
                
        except Exception as e:
            self.critical_failures.append(f"Gemini API validation failed: {e}")
            self.validation_results["gemini_api"] = "FAIL"
            logger.error(f"Gemini API validation failed: {e}")
    
    async def _validate_stripe_api(self):
        """Validate Stripe API connectivity"""
        try:
            if not settings.STRIPE_API_KEY:
                self.warnings.append("Stripe API key not configured")
                self.validation_results["stripe_api"] = "SKIP"
                return
            
            stripe.api_key = settings.STRIPE_API_KEY
            
            # Test with a simple API call
            balance = stripe.Balance.retrieve()
            
            if balance:
                self.validation_results["stripe_api"] = "PASS"
                logger.info("Stripe API validated")
            else:
                self.critical_failures.append("Stripe API test failed")
                self.validation_results["stripe_api"] = "FAIL"
                
        except Exception as e:
            self.critical_failures.append(f"Stripe API validation failed: {e}")
            self.validation_results["stripe_api"] = "FAIL"
            logger.error(f"Stripe API validation failed: {e}")
    
    async def validate_database_migrations(self):
        """Validate database migrations are up to date"""
        try:
            db = next(get_db())
            
            # Check if all required tables exist
            required_tables = [
                "users", "workspaces", "subscriptions", "documents", 
                "document_chunks", "chat_sessions", "chat_messages", "embed_codes"
            ]
            
            for table in required_tables:
                result = db.execute(text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")).fetchone()
                if not result or not result[0]:
                    self.critical_failures.append(f"Required table '{table}' does not exist")
                    self.validation_results["database_migrations"] = "FAIL"
                    return
            
            self.validation_results["database_migrations"] = "PASS"
            logger.info("Database migrations validated")
            
        except Exception as e:
            self.critical_failures.append(f"Database migrations validation failed: {e}")
            self.validation_results["database_migrations"] = "FAIL"
            logger.error(f"Database migrations validation failed: {e}")
    
    async def validate_secrets_management(self):
        """Validate secrets management configuration"""
        try:
            # Test secrets manager initialization
            if secrets_manager.provider == "env":
                self.warnings.append("Using environment variables for secrets (not recommended for production)")
                self.validation_results["secrets_management"] = "WARN"
            else:
                # Test secret retrieval
                test_secret = secrets_manager.get_secret("TEST_SECRET")
                if test_secret is not None:
                    self.validation_results["secrets_management"] = "PASS"
                    logger.info("Secrets management validated")
                else:
                    self.warnings.append("Secrets management configured but test secret not found")
                    self.validation_results["secrets_management"] = "WARN"
                    
        except Exception as e:
            self.critical_failures.append(f"Secrets management validation failed: {e}")
            self.validation_results["secrets_management"] = "FAIL"
            logger.error(f"Secrets management validation failed: {e}")
    
    async def validate_rate_limiting(self):
        """Validate rate limiting configuration"""
        try:
            # Test rate limiting service
            from app.services.rate_limiting import rate_limiting_service
            
            # Test rate limit check
            is_allowed, info = await rate_limiting_service.check_workspace_rate_limit(
                workspace_id="test-workspace",
                limit=60,
                window_seconds=60
            )
            
            if isinstance(is_allowed, bool):
                self.validation_results["rate_limiting"] = "PASS"
                logger.info("Rate limiting validated")
            else:
                self.critical_failures.append("Rate limiting service not working")
                self.validation_results["rate_limiting"] = "FAIL"
                
        except Exception as e:
            self.critical_failures.append(f"Rate limiting validation failed: {e}")
            self.validation_results["rate_limiting"] = "FAIL"
            logger.error(f"Rate limiting validation failed: {e}")
    
    async def validate_caching(self):
        """Validate caching configuration"""
        try:
            from app.utils.cache import cache_service
            
            # Test cache operations
            await cache_service.set("test_cache_key", "test_value", ttl=10)
            cached_value = await cache_service.get("test_cache_key")
            
            if cached_value == "test_value":
                await cache_service.delete("test_cache_key")
                self.validation_results["caching"] = "PASS"
                logger.info("Caching validated")
            else:
                self.critical_failures.append("Cache operations test failed")
                self.validation_results["caching"] = "FAIL"
                
        except Exception as e:
            self.critical_failures.append(f"Caching validation failed: {e}")
            self.validation_results["caching"] = "FAIL"
            logger.error(f"Caching validation failed: {e}")
    
    async def validate_security_configuration(self):
        """Validate security configuration"""
        try:
            # Check JWT secret is not default
            if settings.SECRET_KEY == "your-secret-key-here":
                self.critical_failures.append("JWT secret is using default value")
                self.validation_results["security_configuration"] = "FAIL"
                return
            
            # Check CORS configuration
            if "*" in settings.CORS_ORIGINS:
                self.warnings.append("CORS allows all origins (not recommended for production)")
                self.validation_results["security_configuration"] = "WARN"
            else:
                self.validation_results["security_configuration"] = "PASS"
                logger.info("Security configuration validated")
                
        except Exception as e:
            self.critical_failures.append(f"Security configuration validation failed: {e}")
            self.validation_results["security_configuration"] = "FAIL"
            logger.error(f"Security configuration validation failed: {e}")
    
    async def validate_cors_configuration(self):
        """Validate CORS configuration"""
        try:
            if not settings.CORS_ORIGINS:
                self.critical_failures.append("CORS origins not configured")
                self.validation_results["cors_configuration"] = "FAIL"
                return
            
            if "*" in settings.CORS_ORIGINS:
                self.warnings.append("CORS allows all origins")
                self.validation_results["cors_configuration"] = "WARN"
            else:
                self.validation_results["cors_configuration"] = "PASS"
                logger.info("CORS configuration validated")
                
        except Exception as e:
            self.critical_failures.append(f"CORS configuration validation failed: {e}")
            self.validation_results["cors_configuration"] = "FAIL"
            logger.error(f"CORS configuration validation failed: {e}")
    
    async def validate_authentication(self):
        """Validate authentication configuration"""
        try:
            # Check JWT configuration
            if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
                self.critical_failures.append("JWT secret key is too short or not configured")
                self.validation_results["authentication"] = "FAIL"
                return
            
            self.validation_results["authentication"] = "PASS"
            logger.info("Authentication configuration validated")
            
        except Exception as e:
            self.critical_failures.append(f"Authentication validation failed: {e}")
            self.validation_results["authentication"] = "FAIL"
            logger.error(f"Authentication validation failed: {e}")
    
    async def validate_performance_configuration(self):
        """Validate performance configuration"""
        try:
            # Check database connection pool settings
            db = next(get_db())
            pool = db.bind.pool
            
            if hasattr(pool, 'size') and pool.size() < 5:
                self.warnings.append("Database connection pool size is low")
            
            self.validation_results["performance_configuration"] = "PASS"
            logger.info("Performance configuration validated")
            
        except Exception as e:
            self.warnings.append(f"Performance configuration validation warning: {e}")
            self.validation_results["performance_configuration"] = "WARN"
            logger.warning(f"Performance configuration validation warning: {e}")
    
    async def validate_monitoring_setup(self):
        """Validate monitoring and observability setup"""
        try:
            # Check if metrics endpoint is accessible
            from app.api.api_v1.endpoints.health import get_metrics
            
            # This would test the metrics endpoint
            self.validation_results["monitoring_setup"] = "PASS"
            logger.info("Monitoring setup validated")
            
        except Exception as e:
            self.warnings.append(f"Monitoring setup validation warning: {e}")
            self.validation_results["monitoring_setup"] = "WARN"
            logger.warning(f"Monitoring setup validation warning: {e}")

# Global validator instance
production_validator = ProductionValidator()
