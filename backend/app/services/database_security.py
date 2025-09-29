"""
Database security service for encryption and secure queries
"""

import hashlib
import secrets
import time
from typing import Any, Dict, List, Optional, Union
from sqlalchemy import text, MetaData, Table, Column, String, DateTime, Text
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select, Insert, Update, Delete
from cryptography.fernet import Fernet
from app.core.config import settings
from app.core.database import get_db
import structlog

logger = structlog.get_logger()


class DatabaseSecurityService:
    """Comprehensive database security service"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.sensitive_fields = {
            'users': ['email', 'mobile_phone', 'password_hash'],
            'documents': ['content', 'metadata'],
            'chat_messages': ['content'],
            'embeddings': ['text', 'metadata']
        }
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        try:
            # Try to get from environment
            key = settings.ENCRYPTION_KEY
            if key and len(key) == 44:  # Fernet key length
                return key.encode()
        except AttributeError:
            pass
        
        # Generate new key (in production, this should be stored securely)
        key = Fernet.generate_key()
        logger.warning("Generated new encryption key - store this securely in production")
        return key
    
    def encrypt_field(self, value: str) -> str:
        """Encrypt a sensitive field value"""
        if not value:
            return value
        
        try:
            encrypted_bytes = self.cipher.encrypt(value.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error("Failed to encrypt field", error=str(e))
            raise
    
    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt a sensitive field value"""
        if not encrypted_value:
            return encrypted_value
        
        try:
            decrypted_bytes = self.cipher.decrypt(encrypted_value.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error("Failed to decrypt field", error=str(e))
            raise
    
    def hash_sensitive_data(self, data: str, salt: Optional[str] = None) -> str:
        """Create a secure hash of sensitive data"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{data}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def sanitize_query_params(self, query: str, params: Dict[str, Any]) -> str:
        """Sanitize query parameters to prevent SQL injection"""
        # This is a basic implementation - in production, use parameterized queries
        sanitized_params = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = value.replace("'", "''").replace(";", "")
                sanitized_params[key] = sanitized_value
            else:
                sanitized_params[key] = value
        
        return query.format(**sanitized_params)
    
    def create_secure_query(self, base_query: str, filters: Dict[str, Any]) -> str:
        """Create a secure parameterized query"""
        # This is a simplified example - use SQLAlchemy's parameterized queries in practice
        where_clauses = []
        params = {}
        
        for field, value in filters.items():
            if value is not None:
                param_name = f"param_{field}"
                where_clauses.append(f"{field} = :{param_name}")
                params[param_name] = value
        
        if where_clauses:
            query = f"{base_query} WHERE {' AND '.join(where_clauses)}"
        else:
            query = base_query
        
        return query, params
    
    def audit_query(self, query: str, params: Dict[str, Any], user_id: Optional[str] = None):
        """Audit database queries for security monitoring"""
        try:
            # Log query for audit purposes
            audit_data = {
                "query": query,
                "params": params,
                "user_id": user_id,
                "timestamp": time.time()
            }
            
            # In production, store this in a secure audit log
            logger.info("Database query executed", **audit_data)
            
        except Exception as e:
            logger.error("Failed to audit query", error=str(e))
    
    def encrypt_sensitive_fields(self, data: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """Encrypt sensitive fields in data before database storage"""
        if table_name not in self.sensitive_fields:
            return data
        
        encrypted_data = data.copy()
        sensitive_fields = self.sensitive_fields[table_name]
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                try:
                    encrypted_data[field] = self.encrypt_field(encrypted_data[field])
                except Exception as e:
                    logger.error("Failed to encrypt field", field=field, error=str(e))
                    # Remove sensitive data if encryption fails
                    encrypted_data[field] = None
        
        return encrypted_data
    
    def decrypt_sensitive_fields(self, data: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """Decrypt sensitive fields in data after database retrieval"""
        if table_name not in self.sensitive_fields:
            return data
        
        decrypted_data = data.copy()
        sensitive_fields = self.sensitive_fields[table_name]
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt_field(decrypted_data[field])
                except Exception as e:
                    logger.error("Failed to decrypt field", field=field, error=str(e))
                    # Keep encrypted data if decryption fails
                    pass
        
        return decrypted_data
    
    def create_row_level_security_policy(self, table_name: str, user_id_field: str = "user_id"):
        """Create row-level security policy for a table"""
        # This is a PostgreSQL-specific implementation
        policy_sql = f"""
        CREATE POLICY IF NOT EXISTS {table_name}_user_policy ON {table_name}
        FOR ALL TO authenticated_users
        USING ({user_id_field} = current_setting('app.current_user_id')::int);
        """
        
        return policy_sql
    
    def enable_row_level_security(self, table_name: str):
        """Enable row-level security for a table"""
        rls_sql = f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;"
        return rls_sql
    
    def set_user_context(self, db: Session, user_id: str):
        """Set user context for row-level security"""
        try:
            # Set user context for the session
            db.execute(text(f"SET app.current_user_id = '{user_id}';"))
            db.commit()
        except Exception as e:
            logger.error("Failed to set user context", error=str(e))
    
    def validate_data_integrity(self, data: Dict[str, Any], table_name: str) -> bool:
        """Validate data integrity before database operations"""
        try:
            # Check for required fields
            required_fields = self._get_required_fields(table_name)
            for field in required_fields:
                if field not in data or data[field] is None:
                    logger.warning("Missing required field", field=field, table=table_name)
                    return False
            
            # Validate data types and constraints
            if not self._validate_data_types(data, table_name):
                return False
            
            # Check for suspicious patterns
            if not self._check_suspicious_patterns(data):
                return False
            
            return True
            
        except Exception as e:
            logger.error("Data integrity validation failed", error=str(e))
            return False
    
    def _get_required_fields(self, table_name: str) -> List[str]:
        """Get required fields for a table"""
        required_fields = {
            'users': ['email'],
            'documents': ['filename', 'workspace_id'],
            'chat_messages': ['content', 'session_id'],
            'embeddings': ['text', 'workspace_id']
        }
        return required_fields.get(table_name, [])
    
    def _validate_data_types(self, data: Dict[str, Any], table_name: str) -> bool:
        """Validate data types for fields"""
        # This is a simplified implementation
        # In production, use proper schema validation
        return True
    
    def _check_suspicious_patterns(self, data: Dict[str, Any]) -> bool:
        """Check for suspicious patterns in data"""
        suspicious_patterns = [
            '<script', 'javascript:', 'vbscript:', 'onload=',
            'eval(', 'document.cookie', 'document.write'
        ]
        
        for key, value in data.items():
            if isinstance(value, str):
                value_lower = value.lower()
                for pattern in suspicious_patterns:
                    if pattern in value_lower:
                        logger.warning("Suspicious pattern detected", 
                                     field=key, pattern=pattern)
                        return False
        
        return True
    
    def create_secure_connection_string(self, base_url: str) -> str:
        """Create a secure database connection string"""
        # Add security parameters to connection string
        security_params = [
            "sslmode=require",
            "sslcert=client-cert.pem",
            "sslkey=client-key.pem",
            "sslrootcert=ca-cert.pem"
        ]
        
        if '?' in base_url:
            return f"{base_url}&{'&'.join(security_params)}"
        else:
            return f"{base_url}?{'&'.join(security_params)}"


# Global instance
database_security_service = DatabaseSecurityService()
