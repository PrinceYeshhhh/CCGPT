#!/usr/bin/env python3
"""
Local Testing Setup
Tests your local backend (if running) or helps you deploy to cloud
"""
import asyncio
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Import test modules
from backend.tests.test_cloud_integration import CloudTestClient

class LocalTestRunner:
    """Local test runner"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.api_url = f"{self.backend_url}/api/v1"
        self.results: Dict[str, Any] = {}
        
    def print_banner(self):
        """Print test banner"""
        print("🏠 CustomerCareGPT Local Testing Suite")
        print("=" * 50)
        print(f"Backend URL: {self.backend_url}")
        print("=" * 50)
    
    async def test_local_backend(self) -> bool:
        """Test if local backend is running"""
        print("\n🔗 Testing Local Backend...")
        print("-" * 30)
        
        try:
            async with CloudTestClient(base_url=self.api_url) as client:
                result, status = await client.get_health()
                
                if status == 200:
                    print("✅ Local backend is running and healthy")
                    print(f"   Status: {result['status']}")
                    return True
                else:
                    print(f"❌ Local backend returned status {status}")
                    print(f"   Response: {result}")
                    return False
                    
        except Exception as e:
            print(f"❌ Local backend is not running: {e}")
            print("   Make sure to start your backend with: python backend/main.py")
            return False
    
    async def test_cloud_deployment_status(self) -> bool:
        """Check if cloud deployment is ready"""
        print("\n🌐 Checking Cloud Deployment Status...")
        print("-" * 30)
        
        # Check if we have a real backend URL
        cloud_url = "https://customercaregpt-backend-xxxxx-uc.a.run.app"
        
        if "xxxxx" in cloud_url:
            print("❌ Cloud backend not deployed yet")
            print("   Your backend URL still has placeholder 'xxxxx'")
            print("   You need to deploy to Google Cloud Run first")
            print("\n   To deploy:")
            print("   1. Run: source gcp/production.env")
            print("   2. Run: ./gcp/deploy-gcp-complete.sh")
            print("   3. Then run: python test_cloud_setup.py --quick")
            return False
        else:
            print("✅ Cloud backend URL looks valid")
            return True
    
    def print_deployment_instructions(self):
        """Print deployment instructions"""
        print("\n🚀 Deployment Instructions")
        print("=" * 50)
        print("To test your cloud backend, you need to deploy it first:")
        print()
        print("1. Deploy to Google Cloud Run:")
        print("   source gcp/production.env")
        print("   ./gcp/deploy-gcp-complete.sh")
        print()
        print("2. Or test locally (if backend is running):")
        print("   python backend/main.py")
        print("   python test_local_setup.py")
        print()
        print("3. After deployment, test cloud backend:")
        print("   python test_cloud_setup.py --quick")
        print()
        print("Current Status:")
        print(f"   Local Backend: {'Running' if self.results.get('Local Backend', False) else 'Not Running'}")
        print(f"   Cloud Backend: {'Deployed' if self.results.get('Cloud Deployment', False) else 'Not Deployed'}")
    
    async def run_tests(self):
        """Run all tests"""
        self.print_banner()
        
        # Test local backend
        self.results["Local Backend"] = await self.test_local_backend()
        
        # Check cloud deployment status
        self.results["Cloud Deployment"] = await self.test_cloud_deployment_status()
        
        # Print instructions
        self.print_deployment_instructions()
        
        return any(self.results.values())

async def main():
    """Main function"""
    runner = LocalTestRunner()
    success = await runner.run_tests()
    
    if success:
        print("\n✅ You can proceed with testing!")
    else:
        print("\n🔧 Please deploy your backend first, then run the tests.")

if __name__ == "__main__":
    asyncio.run(main())
