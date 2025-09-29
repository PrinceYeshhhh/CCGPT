"""
JWT Token revocation service for security
"""

import redis
import json
from datetime import datetime, timedelta
from typing import Set, Optional
from app.core.config import settings
from app.core.database import redis_manager
import structlog

logger = structlog.get_logger()


class TokenRevocationService:
    """Service for managing JWT token revocation"""
    
    def __init__(self):
        self.redis_client = redis_manager.get_client()
        self.revoked_tokens_key = "revoked_tokens"
        self.user_tokens_key = "user_tokens"
    
    def revoke_token(self, token_jti: str, user_id: int, expires_at: datetime) -> bool:
        """Revoke a specific token by its JTI (JWT ID)"""
        try:
            # Store revoked token with expiration
            token_data = {
                "jti": token_jti,
                "user_id": user_id,
                "revoked_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat()
            }
            
            # Calculate TTL (time to live) for Redis
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            if ttl > 0:
                self.redis_client.setex(
                    f"{self.revoked_tokens_key}:{token_jti}",
                    ttl,
                    json.dumps(token_data)
                )
                
                # Add to user's revoked tokens set
                self.redis_client.sadd(f"{self.user_tokens_key}:{user_id}", token_jti)
                
                logger.info("Token revoked", jti=token_jti, user_id=user_id)
                return True
            else:
                logger.warning("Token already expired", jti=token_jti)
                return False
                
        except Exception as e:
            logger.error("Failed to revoke token", error=str(e), jti=token_jti)
            return False
    
    def is_token_revoked(self, token_jti: str) -> bool:
        """Check if a token is revoked"""
        try:
            return self.redis_client.exists(f"{self.revoked_tokens_key}:{token_jti}") > 0
        except Exception as e:
            logger.error("Failed to check token revocation", error=str(e), jti=token_jti)
            return False
    
    def revoke_all_user_tokens(self, user_id: int) -> int:
        """Revoke all tokens for a specific user"""
        try:
            # Get all user tokens
            user_tokens = self.redis_client.smembers(f"{self.user_tokens_key}:{user_id}")
            revoked_count = 0
            
            for token_jti in user_tokens:
                if self.is_token_revoked(token_jti):
                    revoked_count += 1
            
            # Clear user's token set
            self.redis_client.delete(f"{self.user_tokens_key}:{user_id}")
            
            logger.info("All user tokens revoked", user_id=user_id, count=revoked_count)
            return revoked_count
            
        except Exception as e:
            logger.error("Failed to revoke user tokens", error=str(e), user_id=user_id)
            return 0
    
    def cleanup_expired_tokens(self) -> int:
        """Clean up expired revoked tokens"""
        try:
            # Get all revoked token keys
            pattern = f"{self.revoked_tokens_key}:*"
            keys = self.redis_client.keys(pattern)
            cleaned_count = 0
            
            for key in keys:
                token_data = self.redis_client.get(key)
                if token_data:
                    data = json.loads(token_data)
                    expires_at = datetime.fromisoformat(data["expires_at"])
                    
                    if expires_at < datetime.utcnow():
                        self.redis_client.delete(key)
                        cleaned_count += 1
            
            logger.info("Expired tokens cleaned up", count=cleaned_count)
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired tokens", error=str(e))
            return 0
    
    def get_revoked_tokens_for_user(self, user_id: int) -> Set[str]:
        """Get all revoked tokens for a user"""
        try:
            tokens = self.redis_client.smembers(f"{self.user_tokens_key}:{user_id}")
            return {token.decode() if isinstance(token, bytes) else token for token in tokens}
        except Exception as e:
            logger.error("Failed to get user revoked tokens", error=str(e), user_id=user_id)
            return set()


# Global instance
token_revocation_service = TokenRevocationService()
