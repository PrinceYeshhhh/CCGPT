#!/usr/bin/env python3
"""
Configuration validation script for CustomerCareGPT
Validates environment configuration before deployment
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import Settings


class ConfigValidator:
    """Validates application configuration for different environments"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.errors = []
        self.warnings = []
        
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration and return (is_valid, errors, warnings)"""
        try:
            # Load settings
            settings = Settings()
            
            # Validate based on environment
            if self.environment.lower() == "production":
                self._validate_production(settings)
            elif self.environment.lower() == "staging":
                self._validate_staging(settings)
            else:
                self._validate_development(settings)
            
            # Common validations
            self._validate_common(settings)
            
            return len(self.errors) == 0, self.errors, self.warnings
            
        except Exception as e:
            self.errors.append(f"Failed to load configuration: {str(e)}")
            return False, self.errors, self.warnings
    
    def _validate_production(self, settings: Settings) -> None:
        """Validate production configuration"""
        # Critical secrets
        critical_secrets = [
            ("SECRET_KEY", settings.SECRET_KEY),
            ("JWT_SECRET", settings.JWT_SECRET),
            ("DATABASE_URL", settings.DATABASE_URL),
            ("REDIS_URL", settings.REDIS_URL),
            ("GEMINI_API_KEY", settings.GEMINI_API_KEY),
            ("PUBLIC_BASE_URL", settings.PUBLIC_BASE_URL),
            ("API_BASE_URL", settings.API_BASE_URL),
        ]
        
        for name, value in critical_secrets:
            if not value or value in ["", "your-secret-key-here-change-in-production"]:
                self.errors.append(f"Production requires {name} to be set")
        
        # Security validations
        if settings.DEBUG:
            self.errors.append("DEBUG must be False in production")
        
        if not settings.CORS_ORIGINS:
            self.errors.append("CORS_ORIGINS must be set in production")
        
        if not settings.ALLOWED_HOSTS:
            self.errors.append("ALLOWED_HOSTS must be set in production")
        
        # URL validations
        if settings.PUBLIC_BASE_URL and not settings.PUBLIC_BASE_URL.startswith("https://"):
            self.errors.append("PUBLIC_BASE_URL must use HTTPS in production")
        
        if settings.API_BASE_URL and not settings.API_BASE_URL.startswith("https://"):
            self.errors.append("API_BASE_URL must use HTTPS in production")
        
        # Database validation
        if "sqlite" in settings.DATABASE_URL.lower():
            self.errors.append("SQLite is not allowed in production")
        
        # Security features
        if not settings.ENABLE_SECURITY_HEADERS:
            self.warnings.append("Security headers should be enabled in production")
        
        if not settings.ENABLE_RATE_LIMITING:
            self.warnings.append("Rate limiting should be enabled in production")
        
        # Monitoring
        if not settings.SENTRY_DSN:
            self.warnings.append("Sentry DSN should be set for production monitoring")
    
    def _validate_staging(self, settings: Settings) -> None:
        """Validate staging configuration"""
        # Similar to production but with some relaxations
        critical_secrets = [
            ("SECRET_KEY", settings.SECRET_KEY),
            ("JWT_SECRET", settings.JWT_SECRET),
            ("DATABASE_URL", settings.DATABASE_URL),
            ("REDIS_URL", settings.REDIS_URL),
            ("GEMINI_API_KEY", settings.GEMINI_API_KEY),
        ]
        
        for name, value in critical_secrets:
            if not value or value in ["", "your-secret-key-here-change-in-production"]:
                self.errors.append(f"Staging requires {name} to be set")
        
        # Security validations
        if settings.DEBUG:
            self.warnings.append("DEBUG should be False in staging")
        
        if not settings.CORS_ORIGINS:
            self.errors.append("CORS_ORIGINS must be set in staging")
        
        if not settings.ALLOWED_HOSTS:
            self.errors.append("ALLOWED_HOSTS must be set in staging")
        
        # URL validations
        if settings.PUBLIC_BASE_URL and not settings.PUBLIC_BASE_URL.startswith("https://"):
            self.warnings.append("PUBLIC_BASE_URL should use HTTPS in staging")
        
        if settings.API_BASE_URL and not settings.API_BASE_URL.startswith("https://"):
            self.warnings.append("API_BASE_URL should use HTTPS in staging")
        
        # Database validation
        if "sqlite" in settings.DATABASE_URL.lower():
            self.warnings.append("SQLite is not recommended for staging")
    
    def _validate_development(self, settings: Settings) -> None:
        """Validate development configuration"""
        # Development is more lenient
        if not settings.SECRET_KEY or settings.SECRET_KEY == "":
            self.warnings.append("SECRET_KEY not set, using default")
        
        if not settings.JWT_SECRET or settings.JWT_SECRET == "":
            self.warnings.append("JWT_SECRET not set, using default")
        
        if not settings.GEMINI_API_KEY:
            self.warnings.append("GEMINI_API_KEY not set, AI features will not work")
        
        if not settings.REDIS_URL or settings.REDIS_URL == "":
            self.warnings.append("REDIS_URL not set, caching will not work")
    
    def _validate_common(self, settings: Settings) -> None:
        """Common validations for all environments"""
        # URL format validation
        if settings.PUBLIC_BASE_URL and not self._is_valid_url(settings.PUBLIC_BASE_URL):
            self.errors.append("PUBLIC_BASE_URL is not a valid URL")
        
        if settings.API_BASE_URL and not self._is_valid_url(settings.API_BASE_URL):
            self.errors.append("API_BASE_URL is not a valid URL")
        
        # Database URL validation
        if settings.DATABASE_URL and not self._is_valid_database_url(settings.DATABASE_URL):
            self.errors.append("DATABASE_URL is not a valid database URL")
        
        # Redis URL validation
        if settings.REDIS_URL and not self._is_valid_redis_url(settings.REDIS_URL):
            self.errors.append("REDIS_URL is not a valid Redis URL")
        
        # Numeric validations
        if settings.DB_POOL_SIZE <= 0:
            self.errors.append("DB_POOL_SIZE must be positive")
        
        if settings.RATE_LIMIT_REQUESTS <= 0:
            self.errors.append("RATE_LIMIT_REQUESTS must be positive")
        
        if settings.MAX_FILE_SIZE <= 0:
            self.errors.append("MAX_FILE_SIZE must be positive")
        
        # Email validation
        if settings.FROM_EMAIL and not self._is_valid_email(settings.FROM_EMAIL):
            self.errors.append("FROM_EMAIL is not a valid email address")
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _is_valid_database_url(self, url: str) -> bool:
        """Check if database URL is valid"""
        valid_schemes = ["sqlite", "postgresql", "mysql", "oracle"]
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return result.scheme in valid_schemes
        except:
            return False
    
    def _is_valid_redis_url(self, url: str) -> bool:
        """Check if Redis URL is valid"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return result.scheme in ["redis", "rediss"]
        except:
            return False
    
    def _is_valid_email(self, email: str) -> bool:
        """Check if email is valid"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def print_report(self) -> None:
        """Print validation report"""
        print(f"\n{'='*60}")
        print(f"Configuration Validation Report - {self.environment.upper()}")
        print(f"{'='*60}")
        
        if not self.errors and not self.warnings:
            print("✅ Configuration is valid!")
            return
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print(f"\n{'='*60}")
        
        if self.errors:
            print("❌ Configuration validation FAILED")
            sys.exit(1)
        else:
            print("✅ Configuration validation PASSED with warnings")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate CustomerCareGPT configuration")
    parser.add_argument(
        "--environment", 
        choices=["development", "staging", "production"],
        default=os.getenv("ENVIRONMENT", "development"),
        help="Environment to validate for"
    )
    parser.add_argument(
        "--env-file",
        help="Path to environment file to load"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Load environment file if specified
    if args.env_file:
        from dotenv import load_dotenv
        load_dotenv(args.env_file)
    
    # Set environment
    os.environ["ENVIRONMENT"] = args.environment
    
    # Validate configuration
    validator = ConfigValidator(args.environment)
    is_valid, errors, warnings = validator.validate()
    
    if args.json:
        result = {
            "environment": args.environment,
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }
        print(json.dumps(result, indent=2))
    else:
        validator.print_report()


if __name__ == "__main__":
    main()
