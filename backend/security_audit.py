"""
Security audit script for production readiness
"""

import asyncio
import sys
from typing import Dict, List, Any
import structlog
from app.core.config import settings
from app.core.database import redis_manager, db_manager
from app.services.token_revocation import token_revocation_service
from app.services.csrf_protection import csrf_protection_service
from app.services.file_security import file_security_service
from app.services.websocket_security import websocket_security_service
from app.services.database_security import database_security_service
from app.services.input_validation import input_validation_service

logger = structlog.get_logger()


class SecurityAuditor:
    """Comprehensive security audit for production readiness"""
    
    def __init__(self):
        self.audit_results = {
            "critical_issues": [],
            "high_issues": [],
            "medium_issues": [],
            "low_issues": [],
            "passed_checks": []
        }
    
    async def run_full_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        logger.info("Starting comprehensive security audit")
        
        # Critical security checks
        await self._check_critical_security()
        
        # Authentication and authorization
        await self._check_authentication_security()
        
        # Data protection
        await self._check_data_protection()
        
        # Network security
        await self._check_network_security()
        
        # Input validation
        await self._check_input_validation()
        
        # File upload security
        await self._check_file_upload_security()
        
        # WebSocket security
        await self._check_websocket_security()
        
        # Database security
        await self._check_database_security()
        
        # Configuration security
        await self._check_configuration_security()
        
        # Generate report
        return self._generate_report()
    
    async def _check_critical_security(self):
        """Check critical security issues"""
        logger.info("Checking critical security issues")
        
        # Check if default secrets are being used
        if settings.SECRET_KEY == "your-secret-key-here-change-in-production":
            self.audit_results["critical_issues"].append({
                "issue": "Default SECRET_KEY in use",
                "description": "SECRET_KEY must be changed in production",
                "fix": "Set a strong, unique SECRET_KEY"
            })
        else:
            self.audit_results["passed_checks"].append("SECRET_KEY is configured")
        
        if settings.JWT_SECRET == "your-jwt-secret-key-here-change-in-production":
            self.audit_results["critical_issues"].append({
                "issue": "Default JWT_SECRET in use",
                "description": "JWT_SECRET must be changed in production",
                "fix": "Set a strong, unique JWT_SECRET"
            })
        else:
            self.audit_results["passed_checks"].append("JWT_SECRET is configured")
        
        # Check if encryption key is set
        if not settings.ENCRYPTION_KEY:
            self.audit_results["critical_issues"].append({
                "issue": "ENCRYPTION_KEY not set",
                "description": "Sensitive data encryption requires ENCRYPTION_KEY",
                "fix": "Generate and set a secure ENCRYPTION_KEY"
            })
        else:
            self.audit_results["passed_checks"].append("ENCRYPTION_KEY is configured")
    
    async def _check_authentication_security(self):
        """Check authentication and authorization security"""
        logger.info("Checking authentication security")
        
        # Check token expiration times
        if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
            self.audit_results["high_issues"].append({
                "issue": "Long token expiration time",
                "description": f"Access tokens expire in {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes",
                "fix": "Reduce ACCESS_TOKEN_EXPIRE_MINUTES to 15-30 minutes"
            })
        else:
            self.audit_results["passed_checks"].append("Token expiration time is secure")
        
        # Check password requirements
        if settings.PASSWORD_MIN_LENGTH < 12:
            self.audit_results["high_issues"].append({
                "issue": "Weak password requirements",
                "description": f"Minimum password length is {settings.PASSWORD_MIN_LENGTH}",
                "fix": "Increase PASSWORD_MIN_LENGTH to at least 12"
            })
        else:
            self.audit_results["passed_checks"].append("Password requirements are strong")
    
    async def _check_data_protection(self):
        """Check data protection measures"""
        logger.info("Checking data protection")
        
        # Check if Redis is configured for token revocation
        try:
            redis_client = redis_manager.get_client()
            redis_client.ping()
            self.audit_results["passed_checks"].append("Redis is available for token revocation")
        except Exception as e:
            self.audit_results["critical_issues"].append({
                "issue": "Redis not available",
                "description": "Token revocation requires Redis",
                "fix": "Configure Redis connection"
            })
    
    async def _check_network_security(self):
        """Check network security configuration"""
        logger.info("Checking network security")
        
        # Check CORS configuration
        if isinstance(settings.CORS_ORIGINS, list) and "*" in settings.CORS_ORIGINS:
            self.audit_results["high_issues"].append({
                "issue": "Overly permissive CORS",
                "description": "CORS allows all origins (*)",
                "fix": "Restrict CORS_ORIGINS to specific domains"
            })
        else:
            self.audit_results["passed_checks"].append("CORS is properly configured")
        
        # Check allowed hosts
        if isinstance(settings.ALLOWED_HOSTS, list) and "*" in settings.ALLOWED_HOSTS:
            self.audit_results["medium_issues"].append({
                "issue": "Overly permissive ALLOWED_HOSTS",
                "description": "ALLOWED_HOSTS allows all hosts (*)",
                "fix": "Restrict ALLOWED_HOSTS to specific domains"
            })
        else:
            self.audit_results["passed_checks"].append("ALLOWED_HOSTS is properly configured")
    
    async def _check_input_validation(self):
        """Check input validation security"""
        logger.info("Checking input validation")
        
        # Test input validation service
        try:
            validation_service = input_validation_service
            
            # Test dangerous input
            test_inputs = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE users; --",
                "../../../etc/passwd",
                "javascript:alert('xss')"
            ]
            
            for test_input in test_inputs:
                try:
                    validation_service.validate_string(test_input, "test")
                    self.audit_results["high_issues"].append({
                        "issue": "Input validation bypassed",
                        "description": f"Dangerous input passed validation: {test_input[:20]}...",
                        "fix": "Strengthen input validation patterns"
                    })
                except HTTPException:
                    pass  # Good - validation caught the dangerous input
            
            self.audit_results["passed_checks"].append("Input validation is working")
            
        except Exception as e:
            self.audit_results["critical_issues"].append({
                "issue": "Input validation service error",
                "description": f"Input validation service failed: {str(e)}",
                "fix": "Fix input validation service"
            })
    
    async def _check_file_upload_security(self):
        """Check file upload security"""
        logger.info("Checking file upload security")
        
        try:
            file_security = file_security_service
            
            # Check if dangerous extensions are blocked
            dangerous_extensions = ['.exe', '.bat', '.php', '.js']
            for ext in dangerous_extensions:
                if ext in file_security.dangerous_extensions:
                    self.audit_results["passed_checks"].append(f"Dangerous extension {ext} is blocked")
                else:
                    self.audit_results["high_issues"].append({
                        "issue": f"Dangerous extension {ext} not blocked",
                        "description": f"File upload allows {ext} files",
                        "fix": f"Add {ext} to dangerous_extensions list"
                    })
            
        except Exception as e:
            self.audit_results["critical_issues"].append({
                "issue": "File security service error",
                "description": f"File security service failed: {str(e)}",
                "fix": "Fix file security service"
            })
    
    async def _check_websocket_security(self):
        """Check WebSocket security"""
        logger.info("Checking WebSocket security")
        
        try:
            ws_security = websocket_security_service
            
            # Check connection limits
            if ws_security.connection_limits["per_user"] > 10:
                self.audit_results["medium_issues"].append({
                    "issue": "High WebSocket connection limit per user",
                    "description": f"Users can have {ws_security.connection_limits['per_user']} WebSocket connections",
                    "fix": "Reduce per-user connection limit"
                })
            else:
                self.audit_results["passed_checks"].append("WebSocket connection limits are reasonable")
            
        except Exception as e:
            self.audit_results["critical_issues"].append({
                "issue": "WebSocket security service error",
                "description": f"WebSocket security service failed: {str(e)}",
                "fix": "Fix WebSocket security service"
            })
    
    async def _check_database_security(self):
        """Check database security"""
        logger.info("Checking database security")
        
        try:
            db_security = database_security_service
            
            # Check if encryption is available
            if db_security.encryption_key:
                self.audit_results["passed_checks"].append("Database encryption is available")
            else:
                self.audit_results["high_issues"].append({
                    "issue": "Database encryption not available",
                    "description": "Sensitive data may not be encrypted",
                    "fix": "Configure database encryption"
                })
            
        except Exception as e:
            self.audit_results["critical_issues"].append({
                "issue": "Database security service error",
                "description": f"Database security service failed: {str(e)}",
                "fix": "Fix database security service"
            })
    
    async def _check_configuration_security(self):
        """Check configuration security"""
        logger.info("Checking configuration security")
        
        # Check if debug mode is enabled
        if settings.DEBUG:
            self.audit_results["high_issues"].append({
                "issue": "Debug mode enabled",
                "description": "DEBUG=True in production is dangerous",
                "fix": "Set DEBUG=False in production"
            })
        else:
            self.audit_results["passed_checks"].append("Debug mode is disabled")
        
        # Check environment
        if settings.ENVIRONMENT == "development":
            self.audit_results["medium_issues"].append({
                "issue": "Development environment",
                "description": "ENVIRONMENT=development in production",
                "fix": "Set ENVIRONMENT=production"
            })
        else:
            self.audit_results["passed_checks"].append("Environment is set to production")
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate security audit report"""
        total_issues = (
            len(self.audit_results["critical_issues"]) +
            len(self.audit_results["high_issues"]) +
            len(self.audit_results["medium_issues"]) +
            len(self.audit_results["low_issues"])
        )
        
        total_checks = total_issues + len(self.audit_results["passed_checks"])
        
        report = {
            "summary": {
                "total_checks": total_checks,
                "total_issues": total_issues,
                "critical_issues": len(self.audit_results["critical_issues"]),
                "high_issues": len(self.audit_results["high_issues"]),
                "medium_issues": len(self.audit_results["medium_issues"]),
                "low_issues": len(self.audit_results["low_issues"]),
                "passed_checks": len(self.audit_results["passed_checks"]),
                "security_score": max(0, 100 - (total_issues * 10))
            },
            "issues": self.audit_results,
            "recommendations": self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        if self.audit_results["critical_issues"]:
            recommendations.append("🚨 CRITICAL: Fix all critical issues before production deployment")
        
        if self.audit_results["high_issues"]:
            recommendations.append("⚠️ HIGH: Address high-priority security issues")
        
        if not settings.ENCRYPTION_KEY:
            recommendations.append("🔐 Generate and configure ENCRYPTION_KEY for data encryption")
        
        if settings.DEBUG:
            recommendations.append("🐛 Disable DEBUG mode in production")
        
        if isinstance(settings.CORS_ORIGINS, list) and "*" in settings.CORS_ORIGINS:
            recommendations.append("🌐 Restrict CORS origins to specific domains")
        
        recommendations.extend([
            "🔒 Enable HTTPS in production",
            "🛡️ Set up proper monitoring and alerting",
            "📊 Regular security audits and penetration testing",
            "👥 Security training for development team",
            "📋 Implement security incident response plan"
        ])
        
        return recommendations


async def main():
    """Run security audit"""
    auditor = SecurityAuditor()
    report = await auditor.run_full_audit()
    
    print("\n" + "="*80)
    print("🔒 CUSTOMERCAREGPT SECURITY AUDIT REPORT")
    print("="*80)
    
    summary = report["summary"]
    print(f"\n📊 SUMMARY:")
    print(f"   Total Checks: {summary['total_checks']}")
    print(f"   Issues Found: {summary['total_issues']}")
    print(f"   Critical: {summary['critical_issues']}")
    print(f"   High: {summary['high_issues']}")
    print(f"   Medium: {summary['medium_issues']}")
    print(f"   Low: {summary['low_issues']}")
    print(f"   Security Score: {summary['security_score']}/100")
    
    if summary['critical_issues'] > 0:
        print(f"\n🚨 CRITICAL ISSUES ({summary['critical_issues']}):")
        for issue in report["issues"]["critical_issues"]:
            print(f"   • {issue['issue']}: {issue['description']}")
            print(f"     Fix: {issue['fix']}")
    
    if summary['high_issues'] > 0:
        print(f"\n⚠️ HIGH PRIORITY ISSUES ({summary['high_issues']}):")
        for issue in report["issues"]["high_issues"]:
            print(f"   • {issue['issue']}: {issue['description']}")
            print(f"     Fix: {issue['fix']}")
    
    print(f"\n✅ PASSED CHECKS ({summary['passed_checks']}):")
    for check in report["issues"]["passed_checks"]:
        print(f"   ✓ {check}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in report["recommendations"]:
        print(f"   {rec}")
    
    print("\n" + "="*80)
    
    # Exit with error code if critical issues found
    if summary['critical_issues'] > 0:
        print("❌ PRODUCTION DEPLOYMENT NOT RECOMMENDED")
        sys.exit(1)
    elif summary['high_issues'] > 0:
        print("⚠️ PRODUCTION DEPLOYMENT WITH CAUTION")
        sys.exit(2)
    else:
        print("✅ PRODUCTION READY")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
