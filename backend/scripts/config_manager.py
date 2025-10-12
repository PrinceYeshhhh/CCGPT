#!/usr/bin/env python3
"""
Configuration management utility for CustomerCareGPT
Provides commands for configuration validation, environment setup, and deployment checks
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import Settings


class ConfigManager:
    """Manages application configuration for different environments"""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.project_root = self.backend_dir.parent
        
    def validate_environment(self, environment: str) -> Tuple[bool, List[str], List[str]]:
        """Validate configuration for a specific environment"""
        try:
            # Set environment
            os.environ["ENVIRONMENT"] = environment
            
            # Load settings
            settings = Settings()
            
            errors = []
            warnings = []
            
            # Environment-specific validations
            if environment.lower() == "production":
                errors, warnings = self._validate_production(settings, errors, warnings)
            elif environment.lower() == "staging":
                errors, warnings = self._validate_staging(settings, errors, warnings)
            else:
                errors, warnings = self._validate_development(settings, errors, warnings)
            
            # Common validations
            errors, warnings = self._validate_common(settings, errors, warnings)
            
            return len(errors) == 0, errors, warnings
            
        except Exception as e:
            return False, [f"Configuration validation failed: {str(e)}"], []
    
    def _validate_production(self, settings: Settings, errors: List[str], warnings: List[str]) -> Tuple[List[str], List[str]]:
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
                errors.append(f"Production requires {name} to be set")
        
        # Security validations
        if settings.DEBUG:
            errors.append("DEBUG must be False in production")
        
        if not settings.CORS_ORIGINS:
            errors.append("CORS_ORIGINS must be set in production")
        
        if not settings.ALLOWED_HOSTS:
            errors.append("ALLOWED_HOSTS must be set in production")
        
        # URL validations
        if settings.PUBLIC_BASE_URL and not settings.PUBLIC_BASE_URL.startswith("https://"):
            errors.append("PUBLIC_BASE_URL must use HTTPS in production")
        
        if settings.API_BASE_URL and not settings.API_BASE_URL.startswith("https://"):
            errors.append("API_BASE_URL must use HTTPS in production")
        
        # Database validation
        if "sqlite" in settings.DATABASE_URL.lower():
            errors.append("SQLite is not allowed in production")
        
        # Security features
        if not settings.ENABLE_SECURITY_HEADERS:
            warnings.append("Security headers should be enabled in production")
        
        if not settings.ENABLE_RATE_LIMITING:
            warnings.append("Rate limiting should be enabled in production")
        
        # Monitoring
        if not settings.SENTRY_DSN:
            warnings.append("Sentry DSN should be set for production monitoring")
        
        return errors, warnings
    
    def _validate_staging(self, settings: Settings, errors: List[str], warnings: List[str]) -> Tuple[List[str], List[str]]:
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
                errors.append(f"Staging requires {name} to be set")
        
        # Security validations
        if settings.DEBUG:
            warnings.append("DEBUG should be False in staging")
        
        if not settings.CORS_ORIGINS:
            errors.append("CORS_ORIGINS must be set in staging")
        
        if not settings.ALLOWED_HOSTS:
            errors.append("ALLOWED_HOSTS must be set in staging")
        
        # URL validations
        if settings.PUBLIC_BASE_URL and not settings.PUBLIC_BASE_URL.startswith("https://"):
            warnings.append("PUBLIC_BASE_URL should use HTTPS in staging")
        
        if settings.API_BASE_URL and not settings.API_BASE_URL.startswith("https://"):
            warnings.append("API_BASE_URL should use HTTPS in staging")
        
        # Database validation
        if "sqlite" in settings.DATABASE_URL.lower():
            warnings.append("SQLite is not recommended for staging")
        
        return errors, warnings
    
    def _validate_development(self, settings: Settings, errors: List[str], warnings: List[str]) -> Tuple[List[str], List[str]]:
        """Validate development configuration"""
        # Development is more lenient
        if not settings.SECRET_KEY or settings.SECRET_KEY == "":
            warnings.append("SECRET_KEY not set, using default")
        
        if not settings.JWT_SECRET or settings.JWT_SECRET == "":
            warnings.append("JWT_SECRET not set, using default")
        
        if not settings.GEMINI_API_KEY:
            warnings.append("GEMINI_API_KEY not set, AI features will not work")
        
        if not settings.REDIS_URL or settings.REDIS_URL == "":
            warnings.append("REDIS_URL not set, caching will not work")
        
        return errors, warnings
    
    def _validate_common(self, settings: Settings, errors: List[str], warnings: List[str]) -> Tuple[List[str], List[str]]:
        """Common validations for all environments"""
        # URL format validation
        if settings.PUBLIC_BASE_URL and not self._is_valid_url(settings.PUBLIC_BASE_URL):
            errors.append("PUBLIC_BASE_URL is not a valid URL")
        
        if settings.API_BASE_URL and not self._is_valid_url(settings.API_BASE_URL):
            errors.append("API_BASE_URL is not a valid URL")
        
        # Database URL validation
        if settings.DATABASE_URL and not self._is_valid_database_url(settings.DATABASE_URL):
            errors.append("DATABASE_URL is not a valid database URL")
        
        # Redis URL validation
        if settings.REDIS_URL and not self._is_valid_redis_url(settings.REDIS_URL):
            errors.append("REDIS_URL is not a valid Redis URL")
        
        # Numeric validations
        if settings.DB_POOL_SIZE <= 0:
            errors.append("DB_POOL_SIZE must be positive")
        
        if settings.RATE_LIMIT_REQUESTS <= 0:
            errors.append("RATE_LIMIT_REQUESTS must be positive")
        
        if settings.MAX_FILE_SIZE <= 0:
            errors.append("MAX_FILE_SIZE must be positive")
        
        # Email validation
        if settings.FROM_EMAIL and not self._is_valid_email(settings.FROM_EMAIL):
            errors.append("FROM_EMAIL is not a valid email address")
        
        return errors, warnings
    
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
    
    def generate_env_file(self, environment: str, output_file: str = None) -> str:
        """Generate environment file for a specific environment"""
        if not output_file:
            output_file = f".env.{environment}"
        
        # Load example file
        example_file = self.project_root / f"env.{environment}.example"
        if not example_file.exists():
            raise FileNotFoundError(f"Example file not found: {example_file}")
        
        # Copy example to output file
        import shutil
        shutil.copy2(example_file, output_file)
        
        return str(output_file)
    
    def check_dependencies(self) -> Tuple[bool, List[str]]:
        """Check if all required dependencies are installed"""
        try:
            import pkg_resources
            requirements_file = self.backend_dir / "requirements.txt"
            
            if not requirements_file.exists():
                return False, ["Requirements file not found"]
            
            with open(requirements_file, 'r') as f:
                requirements = f.read().splitlines()
            
            missing_packages = []
            for requirement in requirements:
                if requirement.strip() and not requirement.startswith('#'):
                    try:
                        pkg_resources.require(requirement)
                    except pkg_resources.DistributionNotFound:
                        missing_packages.append(requirement)
                    except pkg_resources.VersionConflict:
                        missing_packages.append(f"{requirement} (version conflict)")
            
            return len(missing_packages) == 0, missing_packages
            
        except Exception as e:
            return False, [f"Failed to check dependencies: {str(e)}"]
    
    def print_report(self, environment: str, is_valid: bool, errors: List[str], warnings: List[str]) -> None:
        """Print validation report"""
        print(f"\n{'='*60}")
        print(f"Configuration Validation Report - {environment.upper()}")
        print(f"{'='*60}")
        
        if not errors and not warnings:
            print("✅ Configuration is valid!")
            return
        
        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
        
        print(f"\n{'='*60}")
        
        if errors:
            print("❌ Configuration validation FAILED")
        else:
            print("✅ Configuration validation PASSED with warnings")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CustomerCareGPT Configuration Manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument(
        "--environment", 
        choices=["development", "staging", "production"],
        default=os.getenv("ENVIRONMENT", "development"),
        help="Environment to validate for"
    )
    validate_parser.add_argument(
        "--env-file",
        help="Path to environment file to load"
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate environment file")
    generate_parser.add_argument(
        "environment",
        choices=["development", "staging", "production"],
        help="Environment to generate file for"
    )
    generate_parser.add_argument(
        "--output",
        help="Output file path (default: .env.{environment})"
    )
    
    # Check dependencies command
    deps_parser = subparsers.add_parser("check-deps", help="Check dependencies")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = ConfigManager()
    
    if args.command == "validate":
        # Load environment file if specified
        if args.env_file:
            from dotenv import load_dotenv
            load_dotenv(args.env_file)
        
        # Set environment
        os.environ["ENVIRONMENT"] = args.environment
        
        # Validate configuration
        is_valid, errors, warnings = manager.validate_environment(args.environment)
        
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
            manager.print_report(args.environment, is_valid, errors, warnings)
        
        if not is_valid:
            sys.exit(1)
    
    elif args.command == "generate":
        try:
            output_file = manager.generate_env_file(args.environment, args.output)
            print(f"✅ Generated environment file: {output_file}")
            print(f"📝 Please edit the file and fill in your actual values")
        except Exception as e:
            print(f"❌ Failed to generate environment file: {e}")
            sys.exit(1)
    
    elif args.command == "check-deps":
        is_valid, missing = manager.check_dependencies()
        if is_valid:
            print("✅ All dependencies are installed")
        else:
            print("❌ Missing dependencies:")
            for pkg in missing:
                print(f"  - {pkg}")
            print("\n💡 Install missing packages with: pip install -r requirements.txt")
            sys.exit(1)


if __name__ == "__main__":
    main()
