"""
Comprehensive input validation service for security
"""

import re
import html
from typing import Any, Dict, List, Optional, Union, Tuple
from fastapi import HTTPException, status
import structlog

logger = structlog.get_logger()


class InputValidationService:
    """Comprehensive input validation and sanitization service"""
    
    def __init__(self):
        self.max_string_length = 1000
        self.max_text_length = 10000
        self.max_array_length = 100
        
        # Dangerous patterns
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'eval\s*\(',
            r'document\.cookie',
            r'document\.write',
            r'window\.location',
            r'alert\s*\(',
            r'confirm\s*\(',
            r'prompt\s*\(',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>',
            r'expression\s*\(',
            r'url\s*\(',
            r'@import',
            r'behavior\s*:',
            r'-moz-binding',
            r'data:text/html',
            r'data:application/javascript'
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            r'union\s+select',
            r'drop\s+table',
            r'delete\s+from',
            r'insert\s+into',
            r'update\s+set',
            r'alter\s+table',
            r'create\s+table',
            r'exec\s*\(',
            r'execute\s*\(',
            r'sp_',
            r'xp_',
            r'--',
            r'/\*.*?\*/',
            r';\s*drop',
            r';\s*delete',
            r';\s*insert',
            r';\s*update',
            r';\s*alter',
            r';\s*create',
            r';\s*exec',
            r';\s*execute'
        ]
        
        # Path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'\.\.%2f',
            r'\.\.%5c',
            r'%252e%252e%252f',
            r'%252e%252e%255c'
        ]
    
    def validate_string(self, value: Any, field_name: str, max_length: Optional[int] = None) -> str:
        """Validate and sanitize a string input"""
        if value is None:
            return ""
        
        if not isinstance(value, str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be a string"
            )
        
        # Check length
        max_len = max_length or self.max_string_length
        if len(value) > max_len:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} too long (max {max_len} characters)"
            )
        
        # Sanitize HTML
        sanitized = html.escape(value, quote=True)
        
        # Check for dangerous patterns
        if self._contains_dangerous_patterns(sanitized):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} contains potentially dangerous content"
            )
        
        return sanitized.strip()
    
    def validate_email(self, email: Any, field_name: str = "email") -> str:
        """Validate email address"""
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required"
            )
        
        email_str = self.validate_string(email, field_name, 254)
        
        # Email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email_str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format"
            )
        
        return email_str.lower()
    
    def validate_phone(self, phone: Any, field_name: str = "phone") -> str:
        """Validate phone number"""
        if not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required"
            )
        
        phone_str = self.validate_string(phone, field_name, 20)
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone_str)
        
        # Check if it's a valid length (7-15 digits)
        if len(digits_only) < 7 or len(digits_only) > 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format"
            )
        
        return digits_only
    
    def validate_password(self, password: Any, field_name: str = "password") -> str:
        """Validate password strength"""
        if not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required"
            )
        
        password_str = self.validate_string(password, field_name, 128)
        
        # Check minimum length
        if len(password_str) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be at least 8 characters long"
            )
        
        # Check for common weak passwords
        weak_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password_str.lower() in weak_passwords:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is too weak"
            )
        
        return password_str
    
    def validate_url(self, url: Any, field_name: str = "url") -> str:
        """Validate URL"""
        if not url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required"
            )
        
        url_str = self.validate_string(url, field_name, 2048)
        
        # URL regex pattern
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        if not re.match(url_pattern, url_str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format"
            )
        
        return url_str
    
    def validate_uuid(self, uuid_value: Any, field_name: str = "id") -> str:
        """Validate UUID format"""
        if not uuid_value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} is required"
            )
        
        uuid_str = self.validate_string(uuid_value, field_name, 36)
        
        # UUID regex pattern
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, uuid_str.lower()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid {field_name} format"
            )
        
        return uuid_str.lower()
    
    def validate_array(self, array: Any, field_name: str, max_length: Optional[int] = None) -> List[str]:
        """Validate array of strings"""
        if not array:
            return []
        
        if not isinstance(array, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be an array"
            )
        
        max_len = max_length or self.max_array_length
        if len(array) > max_len:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} too long (max {max_len} items)"
            )
        
        validated_array = []
        for i, item in enumerate(array):
            validated_item = self.validate_string(item, f"{field_name}[{i}]")
            validated_array.append(validated_item)
        
        return validated_array
    
    def validate_json(self, json_data: Any, field_name: str = "data") -> Dict[str, Any]:
        """Validate JSON data"""
        if not json_data:
            return {}
        
        if not isinstance(json_data, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{field_name} must be a JSON object"
            )
        
        # Validate each field in the JSON
        validated_data = {}
        for key, value in json_data.items():
            if not isinstance(key, str):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid key type in {field_name}"
                )
            
            validated_key = self.validate_string(key, f"{field_name}.key")
            
            if isinstance(value, str):
                validated_value = self.validate_string(value, f"{field_name}.{validated_key}")
            elif isinstance(value, list):
                validated_value = self.validate_array(value, f"{field_name}.{validated_key}")
            elif isinstance(value, dict):
                validated_value = self.validate_json(value, f"{field_name}.{validated_key}")
            else:
                validated_value = value
            
            validated_data[validated_key] = validated_value
        
        return validated_data
    
    def validate_file_upload(self, filename: str, content_type: str, size: int) -> Tuple[str, str, int]:
        """Validate file upload parameters"""
        # Validate filename
        validated_filename = self.validate_string(filename, "filename", 255)
        
        # Check for path traversal
        if self._contains_path_traversal(validated_filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Validate content type
        validated_content_type = self.validate_string(content_type, "content_type", 100)
        
        # Validate size
        if size < 0 or size > 10 * 1024 * 1024:  # 10MB max
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file size"
            )
        
        return validated_filename, validated_content_type, size
    
    def _contains_dangerous_patterns(self, text: str) -> bool:
        """Check if text contains dangerous patterns"""
        text_lower = text.lower()
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning("Dangerous pattern detected", pattern=pattern)
                return True
        
        return False
    
    def _contains_sql_patterns(self, text: str) -> bool:
        """Check if text contains SQL injection patterns"""
        text_lower = text.lower()
        
        for pattern in self.sql_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning("SQL injection pattern detected", pattern=pattern)
                return True
        
        return False
    
    def _contains_path_traversal(self, text: str) -> bool:
        """Check if text contains path traversal patterns"""
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("Path traversal pattern detected", pattern=pattern)
                return True
        
        return False
    
    def sanitize_for_database(self, value: str) -> str:
        """Sanitize value for database storage"""
        if not value:
            return value
        
        # Remove null bytes
        sanitized = value.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
        
        # Limit length
        if len(sanitized) > self.max_text_length:
            sanitized = sanitized[:self.max_text_length]
        
        return sanitized.strip()


# Global instance
input_validation_service = InputValidationService()
