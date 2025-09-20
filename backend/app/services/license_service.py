"""
White-label license generation and management service
"""

import json
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

class LicenseService:
    """Service for generating and validating white-label licenses"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY.encode('utf-8')
    
    def generate_license(
        self,
        workspace_id: str,
        customer_name: str,
        customer_email: str,
        features: Dict[str, Any],
        expires_at: Optional[datetime] = None
    ) -> str:
        """Generate a signed license for white-label customers"""
        
        if not expires_at:
            expires_at = datetime.utcnow() + timedelta(days=365)  # 1 year default
        
        license_data = {
            "workspace_id": workspace_id,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "features": features,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "version": "1.0"
        }
        
        # Create signature
        license_json = json.dumps(license_data, sort_keys=True)
        signature = hmac.new(
            self.secret_key,
            license_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Combine license data and signature
        license_package = {
            "license": license_data,
            "signature": signature
        }
        
        # Encode as base64 for easy transmission
        license_b64 = base64.b64encode(
            json.dumps(license_package).encode('utf-8')
        ).decode('utf-8')
        
        logger.info(f"Generated license for workspace {workspace_id}")
        return license_b64
    
    def validate_license(self, license_b64: str) -> Optional[Dict[str, Any]]:
        """Validate a license and return license data if valid"""
        
        try:
            # Decode base64
            license_json = base64.b64decode(license_b64).decode('utf-8')
            license_package = json.loads(license_json)
            
            license_data = license_package["license"]
            signature = license_package["signature"]
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                json.dumps(license_data, sort_keys=True).encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning("Invalid license signature")
                return None
            
            # Check expiration
            expires_at = datetime.fromisoformat(license_data["expires_at"])
            if datetime.utcnow() > expires_at:
                logger.warning(f"License expired for workspace {license_data['workspace_id']}")
                return None
            
            logger.info(f"Valid license for workspace {license_data['workspace_id']}")
            return license_data
            
        except Exception as e:
            logger.error(f"Error validating license: {e}")
            return None
    
    def get_license_features(self, license_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from license data"""
        return license_data.get("features", {})
    
    def is_feature_enabled(self, license_data: Dict[str, Any], feature: str) -> bool:
        """Check if a specific feature is enabled in the license"""
        features = self.get_license_features(license_data)
        return features.get(feature, False)
    
    def generate_license_file_content(self, license_b64: str) -> str:
        """Generate a license file content for download"""
        
        license_data = self.validate_license(license_b64)
        if not license_data:
            return "Invalid license"
        
        content = f"""CustomerCareGPT White-Label License
=====================================

Customer: {license_data['customer_name']}
Email: {license_data['customer_email']}
Workspace ID: {license_data['workspace_id']}
Issued: {license_data['issued_at']}
Expires: {license_data['expires_at']}

Features:
"""
        
        for feature, enabled in license_data['features'].items():
            status = "✓" if enabled else "✗"
            content += f"  {status} {feature}\n"
        
        content += f"""
License Key:
{license_b64}

Instructions:
1. Save this license file securely
2. Use the license key to activate your white-label instance
3. Contact support if you need to renew or modify your license

Support: support@customercaregpt.com
"""
        
        return content

# Global instance
license_service = LicenseService()
