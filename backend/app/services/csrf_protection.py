"""
CSRF (Cross-Site Request Forgery) protection service
"""

import secrets
import hashlib
import hmac
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from app.core.database import redis_manager
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class CSRFProtectionService:
    """Comprehensive CSRF protection service"""
    
    def __init__(self):
        self.redis_client = redis_manager.get_client()
        self.token_length = 32
        self.token_expiry = 3600  # 1 hour
        self.secret_key = settings.SECRET_KEY.encode()
    
    def generate_csrf_token(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Generate a CSRF token for a user session"""
        try:
            # Generate random token
            token = secrets.token_urlsafe(self.token_length)
            
            # Create token data
            token_data = {
                "user_id": user_id,
                "session_id": session_id,
                "created_at": time.time(),
                "token": token
            }
            
            # Store token in Redis
            token_key = f"csrf_token:{token}"
            self.redis_client.setex(
                token_key,
                self.token_expiry,
                str(token_data)
            )
            
            # Add token to user's active tokens
            user_tokens_key = f"csrf_user_tokens:{user_id}"
            self.redis_client.sadd(user_tokens_key, token)
            self.redis_client.expire(user_tokens_key, self.token_expiry)
            
            logger.info("CSRF token generated", user_id=user_id, token=token[:8])
            return token
            
        except Exception as e:
            logger.error("Failed to generate CSRF token", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate CSRF token"
            )
    
    def validate_csrf_token(self, token: str, user_id: str) -> bool:
        """Validate a CSRF token"""
        try:
            if not token or not user_id:
                return False
            
            # Check if token exists
            token_key = f"csrf_token:{token}"
            token_data = self.redis_client.get(token_key)
            
            if not token_data:
                logger.warning("CSRF token not found", token=token[:8])
                return False
            
            # Parse token data
            import json
            try:
                data = json.loads(token_data)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Invalid CSRF token data", token=token[:8])
                return False
            
            # Validate user ID
            if data.get("user_id") != user_id:
                logger.warning("CSRF token user mismatch", 
                             token=token[:8], expected=user_id, actual=data.get("user_id"))
                return False
            
            # Check token age
            created_at = data.get("created_at", 0)
            if time.time() - created_at > self.token_expiry:
                logger.warning("CSRF token expired", token=token[:8])
                self.redis_client.delete(token_key)
                return False
            
            return True
            
        except Exception as e:
            logger.error("CSRF token validation failed", error=str(e), token=token[:8])
            return False
    
    def revoke_csrf_token(self, token: str) -> bool:
        """Revoke a specific CSRF token"""
        try:
            token_key = f"csrf_token:{token}"
            token_data = self.redis_client.get(token_key)
            
            if token_data:
                import json
                data = json.loads(token_data)
                user_id = data.get("user_id")
                
                # Remove from user's tokens
                if user_id:
                    user_tokens_key = f"csrf_user_tokens:{user_id}"
                    self.redis_client.srem(user_tokens_key, token)
                
                # Delete token
                self.redis_client.delete(token_key)
                
                logger.info("CSRF token revoked", token=token[:8], user_id=user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Failed to revoke CSRF token", error=str(e), token=token[:8])
            return False
    
    def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all CSRF tokens for a user"""
        try:
            user_tokens_key = f"csrf_user_tokens:{user_id}"
            tokens = self.redis_client.smembers(user_tokens_key)
            
            revoked_count = 0
            for token in tokens:
                if self.revoke_csrf_token(token):
                    revoked_count += 1
            
            # Clear user's token set
            self.redis_client.delete(user_tokens_key)
            
            logger.info("All CSRF tokens revoked for user", user_id=user_id, count=revoked_count)
            return revoked_count
            
        except Exception as e:
            logger.error("Failed to revoke user CSRF tokens", error=str(e), user_id=user_id)
            return 0
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up expired CSRF tokens"""
        try:
            pattern = "csrf_token:*"
            keys = self.redis_client.keys(pattern)
            cleaned_count = 0
            
            for key in keys:
                token_data = self.redis_client.get(key)
                if token_data:
                    import json
                    try:
                        data = json.loads(token_data)
                        created_at = data.get("created_at", 0)
                        
                        if time.time() - created_at > self.token_expiry:
                            self.redis_client.delete(key)
                            cleaned_count += 1
                    except (json.JSONDecodeError, TypeError):
                        # Invalid data, delete it
                        self.redis_client.delete(key)
                        cleaned_count += 1
            
            logger.info("Expired CSRF tokens cleaned up", count=cleaned_count)
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired CSRF tokens", error=str(e))
            return 0
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get information about a CSRF token"""
        try:
            token_key = f"csrf_token:{token}"
            token_data = self.redis_client.get(token_key)
            
            if not token_data:
                return None
            
            import json
            data = json.loads(token_data)
            
            return {
                "user_id": data.get("user_id"),
                "session_id": data.get("session_id"),
                "created_at": data.get("created_at"),
                "expires_at": data.get("created_at", 0) + self.token_expiry,
                "is_valid": time.time() - data.get("created_at", 0) < self.token_expiry
            }
            
        except Exception as e:
            logger.error("Failed to get CSRF token info", error=str(e), token=token[:8])
            return None
    
    def generate_secure_token(self, data: str) -> str:
        """Generate a secure token using HMAC"""
        return hmac.new(
            self.secret_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_secure_token(self, data: str, token: str) -> bool:
        """Verify a secure token"""
        expected_token = self.generate_secure_token(data)
        return hmac.compare_digest(expected_token, token)


# Global instance
csrf_protection_service = CSRFProtectionService()
