#!/usr/bin/env python3
"""
Deployment readiness check for CustomerCareGPT
Comprehensive checks before production deployment
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


class DeploymentChecker:
    """Comprehensive deployment readiness checker"""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.project_root = self.backend_dir.parent
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = []
        self.errors = []
    
    def run_all_checks(self, environment: str = "production") -> Dict[str, Any]:
        """Run all deployment checks"""
        print(f"🚀 Running deployment readiness checks for {environment.upper()}")
        print("=" * 60)
        
        # Set environment
        os.environ["ENVIRONMENT"] = environment
        
        # Run all checks
        self._check_configuration(environment)
        self._check_dependencies()
        self._check_database_migrations()
        self._check_security_settings()
        self._check_environment_variables()
        self._check_file_permissions()
        self._check_disk_space()
        self._check_network_connectivity()
        self._check_health_endpoints()
        
        # Summary
        total_checks = self.checks_passed + self.checks_failed
        success_rate = (self.checks_passed / total_checks * 100) if total_checks > 0 else 0
        
        result = {
            "environment": environment,
            "total_checks": total_checks,
            "checks_passed": self.checks_passed,
            "checks_failed": self.checks_failed,
            "success_rate": success_rate,
            "warnings": self.warnings,
            "errors": self.errors,
            "ready_for_deployment": self.checks_failed == 0
        }
        
        self._print_summary(result)
        return result
    
    def _check_configuration(self, environment: str) -> None:
        """Check configuration validity"""
        print("🔧 Checking configuration...")
        try:
            settings = Settings()
            
            # Check critical settings
            critical_settings = [
                ("SECRET_KEY", settings.SECRET_KEY),
                ("JWT_SECRET", settings.JWT_SECRET),
                ("DATABASE_URL", settings.DATABASE_URL),
                ("REDIS_URL", settings.REDIS_URL),
                ("GEMINI_API_KEY", settings.GEMINI_API_KEY),
            ]
            
            missing_settings = []
            for name, value in critical_settings:
                if not value or value in ["", "your-secret-key-here-change-in-production"]:
                    missing_settings.append(name)
            
            if missing_settings:
                self.errors.append(f"Missing critical settings: {', '.join(missing_settings)}")
                self.checks_failed += 1
            else:
                print("  ✅ Configuration is valid")
                self.checks_passed += 1
                
        except Exception as e:
            self.errors.append(f"Configuration check failed: {str(e)}")
            self.checks_failed += 1
    
    def _check_dependencies(self) -> None:
        """Check if all dependencies are installed"""
        print("📦 Checking dependencies...")
        try:
            import pkg_resources
            requirements_file = self.backend_dir / "requirements.txt"
            
            if not requirements_file.exists():
                self.errors.append("Requirements file not found")
                self.checks_failed += 1
                return
            
            with open(requirements_file, 'r') as f:
                requirements = f.read().splitlines()
            
            missing_packages = []
            for requirement in requirements:
                if requirement.strip() and not requirement.startswith('#'):
                    try:
                        pkg_resources.require(requirement)
                    except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
                        missing_packages.append(requirement)
            
            if missing_packages:
                self.errors.append(f"Missing packages: {', '.join(missing_packages)}")
                self.checks_failed += 1
            else:
                print("  ✅ All dependencies are installed")
                self.checks_passed += 1
                
        except Exception as e:
            self.errors.append(f"Dependency check failed: {str(e)}")
            self.checks_failed += 1
    
    def _check_database_migrations(self) -> None:
        """Check database migrations"""
        print("🗄️  Checking database migrations...")
        try:
            # Check if alembic is available
            import alembic
            from alembic.config import Config
            from alembic import command
            
            # Check if migrations directory exists
            migrations_dir = self.backend_dir / "alembic" / "versions"
            if not migrations_dir.exists():
                self.errors.append("Migrations directory not found")
                self.checks_failed += 1
                return
            
            # Check if there are migration files
            migration_files = list(migrations_dir.glob("*.py"))
            if not migration_files:
                self.warnings.append("No migration files found")
            else:
                print(f"  ✅ Found {len(migration_files)} migration files")
                self.checks_passed += 1
                
        except ImportError:
            self.errors.append("Alembic not installed")
            self.checks_failed += 1
        except Exception as e:
            self.errors.append(f"Migration check failed: {str(e)}")
            self.checks_failed += 1
    
    def _check_security_settings(self) -> None:
        """Check security settings"""
        print("🔒 Checking security settings...")
        try:
            settings = Settings()
            
            security_checks = []
            
            # Check if DEBUG is disabled in production
            if settings.ENVIRONMENT.lower() == "production" and settings.DEBUG:
                security_checks.append("DEBUG should be False in production")
            
            # Check if security headers are enabled
            if not settings.ENABLE_SECURITY_HEADERS:
                security_checks.append("Security headers should be enabled")
            
            # Check if rate limiting is enabled
            if not settings.ENABLE_RATE_LIMITING:
                security_checks.append("Rate limiting should be enabled")
            
            # Check if input validation is enabled
            if not settings.ENABLE_INPUT_VALIDATION:
                security_checks.append("Input validation should be enabled")
            
            # Check if CORS origins are set
            if not settings.CORS_ORIGINS:
                security_checks.append("CORS origins should be set")
            
            # Check if allowed hosts are set
            if not settings.ALLOWED_HOSTS:
                security_checks.append("Allowed hosts should be set")
            
            if security_checks:
                self.warnings.extend(security_checks)
                print(f"  ⚠️  {len(security_checks)} security warnings")
            else:
                print("  ✅ Security settings are properly configured")
            
            self.checks_passed += 1
            
        except Exception as e:
            self.errors.append(f"Security check failed: {str(e)}")
            self.checks_failed += 1
    
    def _check_environment_variables(self) -> None:
        """Check environment variables"""
        print("🌍 Checking environment variables...")
        try:
            settings = Settings()
            
            # Check if environment is set
            if not settings.ENVIRONMENT:
                self.errors.append("ENVIRONMENT variable not set")
                self.checks_failed += 1
                return
            
            # Check if URLs are valid
            if settings.PUBLIC_BASE_URL and not settings.PUBLIC_BASE_URL.startswith(("http://", "https://")):
                self.errors.append("PUBLIC_BASE_URL must be a valid URL")
                self.checks_failed += 1
                return
            
            if settings.API_BASE_URL and not settings.API_BASE_URL.startswith(("http://", "https://")):
                self.errors.append("API_BASE_URL must be a valid URL")
                self.checks_failed += 1
                return
            
            print("  ✅ Environment variables are properly configured")
            self.checks_passed += 1
            
        except Exception as e:
            self.errors.append(f"Environment check failed: {str(e)}")
            self.checks_failed += 1
    
    def _check_file_permissions(self) -> None:
        """Check file permissions"""
        print("📁 Checking file permissions...")
        try:
            # Check if logs directory is writable
            logs_dir = self.backend_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            if not os.access(logs_dir, os.W_OK):
                self.errors.append("Logs directory is not writable")
                self.checks_failed += 1
                return
            
            # Check if uploads directory is writable
            uploads_dir = self.backend_dir / "uploads"
            uploads_dir.mkdir(exist_ok=True)
            
            if not os.access(uploads_dir, os.W_OK):
                self.errors.append("Uploads directory is not writable")
                self.checks_failed += 1
                return
            
            print("  ✅ File permissions are correct")
            self.checks_passed += 1
            
        except Exception as e:
            self.errors.append(f"File permission check failed: {str(e)}")
            self.checks_failed += 1
    
    def _check_disk_space(self) -> None:
        """Check available disk space"""
        print("💾 Checking disk space...")
        try:
            import shutil
            
            # Check available space in the project directory
            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free / (1024**3)
            
            if free_gb < 1:  # Less than 1GB free
                self.warnings.append(f"Low disk space: {free_gb:.2f}GB available")
            else:
                print(f"  ✅ Disk space OK: {free_gb:.2f}GB available")
            
            self.checks_passed += 1
            
        except Exception as e:
            self.warnings.append(f"Disk space check failed: {str(e)}")
            self.checks_passed += 1
    
    def _check_network_connectivity(self) -> None:
        """Check network connectivity to external services"""
        print("🌐 Checking network connectivity...")
        try:
            settings = Settings()
            
            # Check Redis connectivity
            if settings.REDIS_URL:
                try:
                    import redis
                    r = redis.from_url(settings.REDIS_URL)
                    r.ping()
                    print("  ✅ Redis connection successful")
                except Exception as e:
                    self.errors.append(f"Redis connection failed: {str(e)}")
                    self.checks_failed += 1
                    return
            
            # Check database connectivity
            if settings.DATABASE_URL and not settings.DATABASE_URL.startswith("sqlite"):
                try:
                    from sqlalchemy import create_engine
                    engine = create_engine(settings.DATABASE_URL)
                    with engine.connect() as conn:
                        conn.execute("SELECT 1")
                    print("  ✅ Database connection successful")
                except Exception as e:
                    self.errors.append(f"Database connection failed: {str(e)}")
                    self.checks_failed += 1
                    return
            
            self.checks_passed += 1
            
        except Exception as e:
            self.warnings.append(f"Network connectivity check failed: {str(e)}")
            self.checks_passed += 1
    
    def _check_health_endpoints(self) -> None:
        """Check if health endpoints are accessible"""
        print("🏥 Checking health endpoints...")
        try:
            # This would require the application to be running
            # For now, just check if the health module exists
            health_module = self.backend_dir / "app" / "utils" / "health.py"
            if not health_module.exists():
                self.errors.append("Health module not found")
                self.checks_failed += 1
                return
            
            print("  ✅ Health module exists")
            self.checks_passed += 1
            
        except Exception as e:
            self.errors.append(f"Health endpoint check failed: {str(e)}")
            self.checks_failed += 1
    
    def _print_summary(self, result: Dict[str, Any]) -> None:
        """Print deployment readiness summary"""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT READINESS SUMMARY")
        print("=" * 60)
        
        print(f"Environment: {result['environment'].upper()}")
        print(f"Total Checks: {result['total_checks']}")
        print(f"Passed: {result['checks_passed']} ✅")
        print(f"Failed: {result['checks_failed']} ❌")
        print(f"Success Rate: {result['success_rate']:.1f}%")
        
        if result['warnings']:
            print(f"\n⚠️  WARNINGS ({len(result['warnings'])}):")
            for i, warning in enumerate(result['warnings'], 1):
                print(f"  {i}. {warning}")
        
        if result['errors']:
            print(f"\n❌ ERRORS ({len(result['errors'])}):")
            for i, error in enumerate(result['errors'], 1):
                print(f"  {i}. {error}")
        
        print("\n" + "=" * 60)
        
        if result['ready_for_deployment']:
            print("🚀 READY FOR DEPLOYMENT!")
        else:
            print("❌ NOT READY FOR DEPLOYMENT")
            print("Please fix the errors above before deploying.")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CustomerCareGPT Deployment Readiness Check")
    parser.add_argument(
        "--environment",
        choices=["development", "staging", "production"],
        default="production",
        help="Environment to check for deployment"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    checker = DeploymentChecker()
    result = checker.run_all_checks(args.environment)
    
    if args.json:
        print(json.dumps(result, indent=2))
    
    if not result['ready_for_deployment']:
        sys.exit(1)


if __name__ == "__main__":
    main()
