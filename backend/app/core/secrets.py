"""
Secrets management for production environments
Supports AWS Secrets Manager, Azure Key Vault, and HashiCorp Vault
"""

import os
import json
from typing import Optional, Dict, Any
import structlog

# Optional imports for secrets management
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

# Removed circular import - settings will be passed as parameter

logger = structlog.get_logger()

class SecretsManager:
    """Unified secrets management interface"""
    
    def __init__(self):
        self.provider = os.getenv("SECRETS_PROVIDER", "env")  # env, aws, azure, vault
        self._client = None
        self._cache = {}
        
    def _get_aws_client(self):
        """Initialize AWS Secrets Manager client"""
        if not AWS_AVAILABLE:
            raise ImportError("boto3 is not installed. Install with: pip install boto3")
        if not self._client:
            region = os.getenv("AWS_REGION", "us-east-1")
            self._client = boto3.client('secretsmanager', region_name=region)
        return self._client
    
    def _get_azure_client(self):
        """Initialize Azure Key Vault client"""
        if not AZURE_AVAILABLE:
            raise ImportError("azure-keyvault-secrets is not installed. Install with: pip install azure-keyvault-secrets azure-identity")
        if not self._client:
            vault_url = os.getenv("AZURE_KEY_VAULT_URL")
            if not vault_url:
                raise ValueError("AZURE_KEY_VAULT_URL environment variable is required")
            credential = DefaultAzureCredential()
            self._client = SecretClient(vault_url=vault_url, credential=credential)
        return self._client
    
    def _get_vault_client(self):
        """Initialize HashiCorp Vault client"""
        if not VAULT_AVAILABLE:
            raise ImportError("hvac is not installed. Install with: pip install hvac")
        if not self._client:
            vault_url = os.getenv("VAULT_URL", "")
            vault_token = os.getenv("VAULT_TOKEN")
            if not vault_token:
                raise ValueError("VAULT_TOKEN environment variable is required")
            
            self._client = hvac.Client(url=vault_url, token=vault_token)
            if not self._client.is_authenticated():
                raise ValueError("Failed to authenticate with Vault")
        return self._client
    
    def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[str]:
        """Get secret value from configured provider"""
        
        # Check cache first
        if use_cache and secret_name in self._cache:
            return self._cache[secret_name]
        
        try:
            if self.provider == "aws":
                secret_value = self._get_aws_secret(secret_name)
            elif self.provider == "azure":
                secret_value = self._get_azure_secret(secret_name)
            elif self.provider == "vault":
                secret_value = self._get_vault_secret(secret_name)
            else:  # env
                secret_value = os.getenv(secret_name)
            
            if secret_value:
                self._cache[secret_name] = secret_value
                logger.info(f"Retrieved secret: {secret_name}", provider=self.provider)
            
            return secret_value
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}", provider=self.provider)
            return None
    
    def _get_aws_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        client = self._get_aws_client()
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret_string = response['SecretString']
            
            # Try to parse as JSON for structured secrets
            try:
                secret_data = json.loads(secret_string)
                return secret_data.get('value', secret_string)
            except json.JSONDecodeError:
                return secret_string
                
        except client.exceptions.ResourceNotFoundException:
            logger.warning(f"Secret {secret_name} not found in AWS Secrets Manager")
            return None
    
    def _get_azure_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        client = self._get_azure_client()
        try:
            secret = client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            logger.warning(f"Secret {secret_name} not found in Azure Key Vault: {e}")
            return None
    
    def _get_vault_secret(self, secret_name: str) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        client = self._get_vault_client()
        try:
            secret_path = os.getenv("VAULT_SECRET_PATH", "secret")
            response = client.secrets.kv.v2.read_secret_version(
                path=f"{secret_path}/{secret_name}"
            )
            return response['data']['data'].get('value')
        except Exception as e:
            logger.warning(f"Secret {secret_name} not found in Vault: {e}")
            return None
    
    def get_database_url(self) -> str:
        """Get database URL from secrets or environment"""
        if self.provider != "env":
            db_url = self.get_secret("DATABASE_URL")
            if db_url:
                return db_url
        # Lazy import to avoid circular dependency; fall back safely
        default_val = None
        try:
            from app.core.config import settings as _settings
            default_val = getattr(_settings, 'DATABASE_URL', None)
        except Exception:
            default_val = None
        return os.getenv("DATABASE_URL", default_val or "")
    
    def get_redis_url(self) -> str:
        """Get Redis URL from secrets or environment"""
        if self.provider != "env":
            redis_url = self.get_secret("REDIS_URL")
            if redis_url:
                return redis_url
        # Lazy import to avoid circular dependency; fall back safely
        default_val = None
        try:
            from app.core.config import settings as _settings
            default_val = getattr(_settings, 'REDIS_URL', None)
        except Exception:
            default_val = None
        return os.getenv("REDIS_URL", default_val or "redis://localhost:6379/0")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for specific service"""
        key_name = f"{service.upper()}_API_KEY"
        return self.get_secret(key_name)
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret from secrets or environment"""
        if self.provider != "env":
            jwt_secret = self.get_secret("JWT_SECRET")
            if jwt_secret:
                return jwt_secret
        # Lazy import to avoid circular dependency; fall back safely
        default_val = None
        try:
            from app.core.config import settings as _settings
            default_val = getattr(_settings, 'SECRET_KEY', None)
        except Exception:
            default_val = None
        return os.getenv("JWT_SECRET", default_val or "change-me")
    
    def get_stripe_config(self) -> Dict[str, str]:
        """Get Stripe configuration from secrets"""
        config = {}
        
        if self.provider != "env":
            config["api_key"] = self.get_secret("STRIPE_API_KEY") or os.getenv("STRIPE_API_KEY", "")
            config["webhook_secret"] = self.get_secret("STRIPE_WEBHOOK_SECRET") or os.getenv("STRIPE_WEBHOOK_SECRET", "")
        else:
            config["api_key"] = os.getenv("STRIPE_API_KEY", "")
            config["webhook_secret"] = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        
        return config
    
    def rotate_secret(self, secret_name: str, new_value: str) -> bool:
        """Rotate secret value (if supported by provider)"""
        try:
            if self.provider == "aws":
                return self._rotate_aws_secret(secret_name, new_value)
            elif self.provider == "azure":
                return self._rotate_azure_secret(secret_name, new_value)
            elif self.provider == "vault":
                return self._rotate_vault_secret(secret_name, new_value)
            else:
                logger.warning("Secret rotation not supported for env provider")
                return False
        except Exception as e:
            logger.error(f"Failed to rotate secret {secret_name}: {e}")
            return False
    
    def _rotate_aws_secret(self, secret_name: str, new_value: str) -> bool:
        """Rotate secret in AWS Secrets Manager"""
        client = self._get_aws_client()
        try:
            client.update_secret(
                SecretId=secret_name,
                SecretString=new_value
            )
            # Clear cache
            if secret_name in self._cache:
                del self._cache[secret_name]
            return True
        except Exception as e:
            logger.error(f"Failed to rotate AWS secret {secret_name}: {e}")
            return False
    
    def _rotate_azure_secret(self, secret_name: str, new_value: str) -> bool:
        """Rotate secret in Azure Key Vault"""
        client = self._get_azure_client()
        try:
            client.set_secret(secret_name, new_value)
            # Clear cache
            if secret_name in self._cache:
                del self._cache[secret_name]
            return True
        except Exception as e:
            logger.error(f"Failed to rotate Azure secret {secret_name}: {e}")
            return False
    
    def _rotate_vault_secret(self, secret_name: str, new_value: str) -> bool:
        """Rotate secret in HashiCorp Vault"""
        client = self._get_vault_client()
        try:
            secret_path = os.getenv("VAULT_SECRET_PATH", "secret")
            client.secrets.kv.v2.create_or_update_secret(
                path=f"{secret_path}/{secret_name}",
                secret={"value": new_value}
            )
            # Clear cache
            if secret_name in self._cache:
                del self._cache[secret_name]
            return True
        except Exception as e:
            logger.error(f"Failed to rotate Vault secret {secret_name}: {e}")
            return False

# Global secrets manager instance
secrets_manager = SecretsManager()
