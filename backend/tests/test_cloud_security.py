"""
Cloud Security Tests
Tests the security of cloud backend from local machine
"""
import asyncio
import httpx
import os
import json
from typing import Dict, Any, List

# Cloud URLs
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_V1_URL = f"{BACKEND_URL}/api/v1"

class CloudSecurityTester:
    """Security tester for cloud backend"""
    
    def __init__(self, base_url: str = API_V1_URL):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=30.0)
        self.vulnerabilities: List[Dict[str, Any]] = []
        self.security_checks: List[Dict[str, Any]] = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()
    
    def add_vulnerability(self, severity: str, description: str, details: str = ""):
        """Add a security vulnerability"""
        self.vulnerabilities.append({
            "severity": severity,
            "description": description,
            "details": details
        })
    
    def add_security_check(self, check_name: str, passed: bool, details: str = ""):
        """Add a security check result"""
        self.security_checks.append({
            "check": check_name,
            "passed": passed,
            "details": details
        })
    
    async def test_https_enforcement(self):
        """Test HTTPS enforcement"""
        print("🔒 Testing HTTPS enforcement...")
        
        # Test if HTTP redirects to HTTPS
        try:
            http_url = self.base_url.replace("https://", "http://")
            response = await self.session.get(http_url, follow_redirects=False)
            
            if response.status_code in [301, 302, 307, 308]:
                self.add_security_check("HTTPS Redirect", True, f"HTTP redirects to HTTPS with status {response.status_code}")
            else:
                self.add_vulnerability("HIGH", "HTTP not redirecting to HTTPS", f"Status: {response.status_code}")
        except Exception as e:
            self.add_security_check("HTTPS Redirect", True, f"HTTP endpoint not accessible: {e}")
    
    async def test_security_headers(self):
        """Test security headers"""
        print("🛡️ Testing security headers...")
        
        response = await self.session.get(f"{self.base_url}/health")
        headers = response.headers
        
        # Check for security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=",
            "Content-Security-Policy": None,
            "Referrer-Policy": None
        }
        
        for header, expected in security_headers.items():
            if header in headers:
                if expected is None:
                    self.add_security_check(f"Header: {header}", True, f"Present: {headers[header]}")
                elif isinstance(expected, list):
                    if any(exp in headers[header] for exp in expected):
                        self.add_security_check(f"Header: {header}", True, f"Value: {headers[header]}")
                    else:
                        self.add_vulnerability("MEDIUM", f"Security header {header} has weak value", f"Value: {headers[header]}")
                elif expected in headers[header]:
                    self.add_security_check(f"Header: {header}", True, f"Value: {headers[header]}")
                else:
                    self.add_vulnerability("MEDIUM", f"Security header {header} has weak value", f"Value: {headers[header]}")
            else:
                self.add_vulnerability("MEDIUM", f"Missing security header: {header}")
    
    async def test_cors_configuration(self):
        """Test CORS configuration"""
        print("🌐 Testing CORS configuration...")
        
        # Test CORS preflight request
        cors_headers = {
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = await self.session.options(f"{self.base_url}/auth/login", headers=cors_headers)
        
        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]
            if allowed_origin == "*":
                self.add_vulnerability("HIGH", "CORS allows all origins (*)", "This allows any website to make requests")
            elif "malicious-site.com" in allowed_origin:
                self.add_vulnerability("HIGH", "CORS allows malicious origins", f"Allowed: {allowed_origin}")
            else:
                self.add_security_check("CORS Origin", True, f"Properly restricted: {allowed_origin}")
        else:
            self.add_security_check("CORS Origin", True, "No CORS headers present (good for API)")
    
    async def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        print("💉 Testing SQL injection...")
        
        # Test SQL injection in auth endpoints
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in sql_payloads:
            # Test login endpoint
            login_data = {
                "email": payload,
                "password": "password"
            }
            
            response = await self.session.post(f"{self.base_url}/auth/login", json=login_data)
            
            if response.status_code == 500:
                self.add_vulnerability("CRITICAL", f"SQL injection vulnerability detected", f"Payload: {payload}")
            elif response.status_code == 401:
                self.add_security_check("SQL Injection", True, f"Properly handled payload: {payload}")
    
    async def test_xss_protection(self):
        """Test XSS protection"""
        print("🛡️ Testing XSS protection...")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ]
        
        for payload in xss_payloads:
            # Test in registration
            user_data = {
                "email": f"test@example.com",
                "password": "password123",
                "full_name": payload
            }
            
            response = await self.session.post(f"{self.base_url}/auth/register", json=user_data)
            
            if response.status_code == 201:
                response_text = response.text
                if payload in response_text and "<script>" in response_text:
                    self.add_vulnerability("HIGH", "XSS vulnerability detected", f"Payload reflected: {payload}")
                else:
                    self.add_security_check("XSS Protection", True, f"Payload properly handled: {payload}")
    
    async def test_rate_limiting(self):
        """Test rate limiting"""
        print("⏱️ Testing rate limiting...")
        
        # Make rapid requests to test rate limiting
        for i in range(20):
            response = await self.session.get(f"{self.base_url}/health")
            if response.status_code == 429:
                self.add_security_check("Rate Limiting", True, f"Rate limit triggered after {i+1} requests")
                return
        
        self.add_vulnerability("MEDIUM", "No rate limiting detected", "Made 20 requests without rate limiting")
    
    async def test_authentication_bypass(self):
        """Test for authentication bypass vulnerabilities"""
        print("🔐 Testing authentication bypass...")
        
        # Test accessing protected endpoints without auth
        protected_endpoints = [
            "/workspaces/",
            "/documents/",
            "/chat/sessions/",
            "/billing/status"
        ]
        
        for endpoint in protected_endpoints:
            response = await self.session.get(f"{self.base_url}{endpoint}")
            
            if response.status_code == 200:
                self.add_vulnerability("CRITICAL", f"Authentication bypass on {endpoint}", "Endpoint accessible without authentication")
            elif response.status_code == 401:
                self.add_security_check("Authentication", True, f"Properly protected: {endpoint}")
            else:
                self.add_security_check("Authentication", True, f"Protected (status {response.status_code}): {endpoint}")
    
    async def test_input_validation(self):
        """Test input validation"""
        print("✅ Testing input validation...")
        
        # Test invalid email formats
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example..com"
        ]
        
        for email in invalid_emails:
            user_data = {
                "email": email,
                "password": "SecurePassword123!",
                "full_name": "Test User"
            }
            
            response = await self.session.post(f"{self.base_url}/auth/register", json=user_data)
            
            if response.status_code == 201:
                self.add_vulnerability("MEDIUM", f"Invalid email accepted: {email}")
            else:
                self.add_security_check("Input Validation", True, f"Invalid email rejected: {email}")
        
        # Test weak passwords
        weak_passwords = [
            "123",
            "password",
            "12345678",
            "Password",
            "password123"
        ]
        
        for password in weak_passwords:
            user_data = {
                "email": f"test{len(password)}@example.com",
                "password": password,
                "full_name": "Test User"
            }
            
            response = await self.session.post(f"{self.base_url}/auth/register", json=user_data)
            
            if response.status_code == 201:
                self.add_vulnerability("MEDIUM", f"Weak password accepted: {password}")
            else:
                self.add_security_check("Password Policy", True, f"Weak password rejected: {password}")
    
    async def test_file_upload_security(self):
        """Test file upload security"""
        print("📁 Testing file upload security...")
        
        # Test malicious file uploads
        malicious_files = [
            ("malicious.php", "<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("malicious.js", "<script>alert('xss')</script>", "application/javascript"),
            ("malicious.html", "<script>alert('xss')</script>", "text/html"),
            ("malicious.exe", b"MZ\x90\x00", "application/x-msdownload")
        ]
        
        for filename, content, content_type in malicious_files:
            files = {
                "file": (filename, content, content_type)
            }
            
            response = await self.session.post(f"{self.base_url}/documents/upload", files=files)
            
            if response.status_code == 201:
                self.add_vulnerability("HIGH", f"Malicious file uploaded: {filename}")
            else:
                self.add_security_check("File Upload Security", True, f"Malicious file rejected: {filename}")
    
    async def test_error_information_disclosure(self):
        """Test for error information disclosure"""
        print("🔍 Testing error information disclosure...")
        
        # Test for detailed error messages
        response = await self.session.get(f"{self.base_url}/nonexistent/endpoint")
        
        if response.status_code == 404:
            response_text = response.text.lower()
            sensitive_keywords = ["stack trace", "exception", "error", "database", "sql", "internal"]
            
            for keyword in sensitive_keywords:
                if keyword in response_text:
                    self.add_vulnerability("LOW", f"Error information disclosure: {keyword}")
                    break
            else:
                self.add_security_check("Error Handling", True, "No sensitive information in error messages")
    
    def generate_security_report(self) -> str:
        """Generate security report"""
        total_checks = len(self.security_checks)
        passed_checks = sum(1 for check in self.security_checks if check["passed"])
        failed_checks = total_checks - passed_checks
        
        critical_vulns = sum(1 for v in self.vulnerabilities if v["severity"] == "CRITICAL")
        high_vulns = sum(1 for v in self.vulnerabilities if v["severity"] == "HIGH")
        medium_vulns = sum(1 for v in self.vulnerabilities if v["severity"] == "MEDIUM")
        low_vulns = sum(1 for v in self.vulnerabilities if v["severity"] == "LOW")
        
        report = f"""
🔒 Cloud Security Test Report
============================
Backend URL: {BACKEND_URL}

Security Checks:
- Total: {total_checks}
- Passed: {passed_checks}
- Failed: {failed_checks}
- Pass Rate: {passed_checks/total_checks*100:.1f}%

Vulnerabilities:
- Critical: {critical_vulns}
- High: {high_vulns}
- Medium: {medium_vulns}
- Low: {low_vulns}
- Total: {len(self.vulnerabilities)}

Security Checks Results:
"""
        
        for check in self.security_checks:
            status = "✅" if check["passed"] else "❌"
            report += f"{status} {check['check']}: {check['details']}\n"
        
        if self.vulnerabilities:
            report += "\nVulnerabilities Found:\n"
            for vuln in self.vulnerabilities:
                severity_icon = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "🔶", "LOW": "🔸"}[vuln["severity"]]
                report += f"{severity_icon} [{vuln['severity']}] {vuln['description']}\n"
                if vuln["details"]:
                    report += f"   Details: {vuln['details']}\n"
        
        return report

async def main():
    """Run all security tests"""
    print("🔒 Cloud Security Testing Suite")
    print("=" * 50)
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 50)
    
    async with CloudSecurityTester() as tester:
        # Run security tests
        await tester.test_https_enforcement()
        await tester.test_security_headers()
        await tester.test_cors_configuration()
        await tester.test_sql_injection()
        await tester.test_xss_protection()
        await tester.test_rate_limiting()
        await tester.test_authentication_bypass()
        await tester.test_input_validation()
        await tester.test_file_upload_security()
        await tester.test_error_information_disclosure()
        
        # Generate and print report
        report = tester.generate_security_report()
        print(report)
        
        # Save report to file
        with open("cloud_security_report.txt", "w") as f:
            f.write(report)
        
        print("📊 Security report saved to cloud_security_report.txt")

if __name__ == "__main__":
    asyncio.run(main())
